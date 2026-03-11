# ============================================================
# engine/medical_system.py
# Núcleo médico modular: cuerpo por partes + farmacología básica.
# ============================================================

from __future__ import annotations

from copy import deepcopy

PARTES_CUERPO = (
    "cabeza",
    "torso",
    "brazo_izquierdo",
    "brazo_derecho",
    "pierna_izquierda",
    "pierna_derecha",
)

TIPOS_FARMACO = {"medicina", "medicina_fuerte"}


def estado_cuerpo_base() -> dict[str, dict]:
    base = {
        "integridad": 100,
        "dolor": 0,
        "infeccion": 0,
        "cronico": False,
        "perdida": False,
    }
    return {parte: deepcopy(base) for parte in PARTES_CUERPO}


def asegurar_estado_cuerpo(cuerpo: dict | None) -> dict[str, dict]:
    data = deepcopy(cuerpo) if isinstance(cuerpo, dict) else {}
    base = estado_cuerpo_base()
    for parte, valores in base.items():
        if parte not in data or not isinstance(data[parte], dict):
            data[parte] = deepcopy(valores)
            continue
        for campo, default in valores.items():
            data[parte].setdefault(campo, default)
    return data


def aplicar_condicion_a_cuerpo(personaje, condicion) -> list[str]:
    """Mapea una condición a una parte del cuerpo de forma data-driven."""
    personaje.cuerpo = asegurar_estado_cuerpo(getattr(personaje, "cuerpo", None))
    efectos = condicion.efectos or {}

    zona = efectos.get("zona_cuerpo")
    if not zona:
        texto = f"{condicion.clave} {condicion.nombre}".lower()
        if "brazo" in texto:
            zona = "brazo_derecho"
        elif "pierna" in texto:
            zona = "pierna_derecha"

    if zona not in personaje.cuerpo:
        return []

    p = personaje.cuerpo[zona]
    p["dolor"] = _clip(p["dolor"] + int(efectos.get("dolor_delta", 10)), 0, 100)
    p["infeccion"] = _clip(p["infeccion"] + int(efectos.get("infeccion_delta", 0)), 0, 100)
    p["integridad"] = _clip(p["integridad"] + int(efectos.get("integridad_delta", -5)), 0, 100)

    if efectos.get("perdida_miembro", False):
        p["perdida"] = True
        p["integridad"] = 0

    if p["infeccion"] >= 70:
        p["cronico"] = True

    return [f"Estado corporal actualizado en {zona.replace('_', ' ')}."]


def procesar_uso_farmaco(
    personaje,
    item: dict,
    uso_terapeutico: bool,
    forzar_supervivencia: bool = False,
) -> tuple[bool, list[str]]:
    """
    Decide si se consume y aplica carga farmacológica.
    - Con conocimiento médico alto y sin necesidad terapéutica: evita consumo.
    - Con poco conocimiento: puede consumir de más y acercarse a sobredosis.
    """
    tipo = item.get("tipo", "")
    if tipo not in TIPOS_FARMACO:
        return True, []

    meta = _farmacologia_item(item)
    personaje.historial_farmacos = list(getattr(personaje, "historial_farmacos", []))
    ahora_h = _hora_absoluta(personaje)
    _limpiar_historial_farmacos(personaje, ahora_h)

    principio = meta["principio_activo"]
    clase = meta["clase"]
    ventana_h = int(meta["ventana_horas"])
    dosis_actual = float(meta["dosis"])

    recientes_mismo = [
        h for h in personaje.historial_farmacos
        if h.get("principio_activo") == principio and (ahora_h - float(h.get("hora_abs", -9999))) <= ventana_h
    ]
    clases_activas = {
        h.get("clase")
        for h in personaje.historial_farmacos
        if (ahora_h - float(h.get("hora_abs", -9999))) <= float(h.get("ventana_horas", 6))
    }
    dosis_prev = sum(float(h.get("dosis", 0.0)) for h in recientes_mismo)
    dosis_total = dosis_prev + dosis_actual

    skill_med = personaje.skills.get("medicina", 0)
    skill_far = personaje.skills.get("farmacologia", max(0, skill_med - 15))
    skill_farma_total = int((skill_med * 0.65) + (skill_far * 0.35))
    salud_pct = personaje.salud / max(1, personaje.salud_max)
    emergencia_vital = forzar_supervivencia or salud_pct <= 0.35
    contra = _contraindicaciones_presentes(personaje, meta.get("contraindicaciones", []))
    mezcla_riesgo = any(c in clases_activas for c in meta.get("no_combinar_con", []))

    if not uso_terapeutico and tipo == "medicina":
        return False, ["No hay necesidad médica inmediata para ese fármaco."]

    if dosis_prev > 0 and skill_farma_total >= 50 and not emergencia_vital:
        return False, [f"Conocimiento médico: ya hay {principio} activo, mejor esperar."]

    if contra and skill_farma_total >= 45 and not emergencia_vital:
        return False, [f"Conocimiento médico: evitas usarlo por contraindicación ({', '.join(contra)})."]

    if not uso_terapeutico and skill_farma_total >= 55 and not emergencia_vital:
        return False, ["Conocimiento médico: evitas consumir un fármaco innecesario."]

    potencia = _potencia_farmaco(item)
    factor_skill = max(0.65, 1.25 - (skill_farma_total / 120.0))
    if not uso_terapeutico and skill_farma_total < 25:
        factor_skill *= 1.35

    delta = round(potencia * factor_skill, 1)
    if mezcla_riesgo:
        delta = round(delta * 1.25, 1)
    if contra:
        delta = round(delta * 1.15, 1)

    personaje.farmaco_carga = min(200.0, float(getattr(personaje, "farmaco_carga", 0.0)) + delta)

    msgs = [f"Carga farmacológica +{delta:.1f}."]
    if emergencia_vital:
        msgs.append("Protocolo de emergencia: se prioriza supervivencia inmediata sobre prudencia farmacológica.")
    if mezcla_riesgo:
        msgs.append("Mezcla de compuestos activa: riesgo aumentado.")
    if contra:
        msgs.append(f"Contraindicación presente ({', '.join(contra)}).")

    if dosis_total > float(meta.get("dosis_toxica", 2.0)):
        daño = 10 if skill_farma_total < 45 else 6
        personaje.salud = max(0, personaje.salud - daño)
        personaje.moral = max(0, personaje.moral - 6)
        msgs.append(f"Sobredosis de {principio}: -{daño} salud, -6 moral.")

    personaje.historial_farmacos.append(
        {
            "principio_activo": principio,
            "clase": clase,
            "dosis": dosis_actual,
            "hora_abs": ahora_h,
            "ventana_horas": ventana_h,
        }
    )

    if personaje.farmaco_carga >= 120:
        daño = 6
        personaje.salud = max(0, personaje.salud - daño)
        personaje.moral = max(0, personaje.moral - 4)
        msgs.append(f"Sobrecarga farmacológica: -{daño} salud, -4 moral.")
    elif personaje.farmaco_carga >= 90:
        personaje.moral = max(0, personaje.moral - 2)
        msgs.append("Malestar por mezcla de fármacos (-2 moral).")

    return True, msgs


def tick_medico(personaje, horas: float) -> list[str]:
    """Evolución médica por tick global: infección local, cronicidad y metabolismo."""
    if horas <= 0:
        return []

    personaje.cuerpo = asegurar_estado_cuerpo(getattr(personaje, "cuerpo", None))
    personaje.historial_farmacos = list(getattr(personaje, "historial_farmacos", []))
    msgs: list[str] = []
    _limpiar_historial_farmacos(personaje, _hora_absoluta(personaje))

    # Metabolismo farmacológico
    skill_med = personaje.skills.get("medicina", 0)
    carga_antes = float(getattr(personaje, "farmaco_carga", 0.0))
    depuracion = (7.0 + skill_med / 20.0) * horas
    personaje.farmaco_carga = max(0.0, carga_antes - depuracion)

    # Efectos sistémicos de carga elevada sostenida
    if personaje.farmaco_carga >= 100:
        daño = max(1, int(2 * horas))
        personaje.salud = max(0, personaje.salud - daño)
        msgs.append(f"El cuerpo acusa exceso de fármacos (-{daño} salud).")

    # Evolución por parte del cuerpo
    for parte, estado in personaje.cuerpo.items():
        if estado.get("perdida", False):
            estado["integridad"] = 0
            estado["cronico"] = True
            continue

        infeccion = int(estado.get("infeccion", 0))
        if infeccion > 0:
            crecimiento = max(1, int(horas))
            estado["infeccion"] = _clip(infeccion + crecimiento, 0, 100)

            if estado["infeccion"] >= 80:
                daño = max(1, int(1 * horas))
                personaje.salud = max(0, personaje.salud - daño)
                msgs.append(f"Infección grave en {parte.replace('_', ' ')} (-{daño} salud).")

            if estado["infeccion"] >= 70:
                estado["cronico"] = True

        # Recuperación de dolor lento si no hay infección activa severa
        dolor = int(estado.get("dolor", 0))
        if dolor > 0 and estado.get("infeccion", 0) < 40:
            estado["dolor"] = _clip(dolor - max(1, int(horas)), 0, 100)

    return msgs


def aplicar_condiciones_cronicas_tick(personaje, horas: float) -> list[str]:
    """Aplica efectos pasivos de condiciones cronicas por tick global."""
    if horas <= 0:
        return []

    cronicas = list(getattr(personaje, "condiciones_cronicas", []))
    if not cronicas:
        return []

    msgs: list[str] = []
    recuperacion_mult = float(personaje.obtener_efecto_rasgo("recuperacion_condicion_mult", 1.0))
    a_remover: list[dict] = []

    for cond in cronicas:
        nombre = str(cond.get("nombre", cond.get("clave", "Condición crónica")))
        sev = max(1, int(cond.get("severidad", 1)))
        ef = cond.get("efectos", {}) if isinstance(cond.get("efectos", {}), dict) else {}

        fatiga_extra = float(ef.get("fatiga_extra_hora", 0.0)) * horas * sev
        if fatiga_extra > 0:
            delta_f = max(1, int(round(fatiga_extra)))
            personaje.fatiga = min(100, personaje.fatiga + delta_f)

        moral_pen = int(ef.get("moral_penalidad_tick", 0)) * max(1, int(horas))
        if moral_pen > 0:
            personaje.moral = max(0, personaje.moral - moral_pen)

        # Sed extra (ej. deshidratación crónica, intoxicación alimentaria).
        sed_extra = float(ef.get("sed_extra_hora", 0.0)) * horas * sev
        if sed_extra > 0:
            personaje.sed = min(100, personaje.sed + max(1, int(round(sed_extra))))

        # Daño por hora (sepsis, hipotermia, envenenamiento, desnutrición).
        daño_hora = float(ef.get("daño_hora", 0.0)) * horas * sev
        if daño_hora > 0:
            personaje.salud = max(0, personaje.salud - max(1, int(round(daño_hora))))

        infeccion_mult = float(ef.get("riesgo_infeccion_mult", 1.0))
        if infeccion_mult > 1.0:
            for parte in getattr(personaje, "cuerpo", {}).values():
                inf = int(parte.get("infeccion", 0))
                if inf > 0:
                    parte["infeccion"] = _clip(inf + int((infeccion_mult - 1.0) * sev), 0, 100)

        # Recuperación natural de condiciones adquiridas (rasgo metabolismo_rapido).
        es_adquirida = cond.get("origen", "hereditario") != "hereditario"
        if es_adquirida and recuperacion_mult > 1.0:
            recuperacion_tick = (recuperacion_mult - 1.0) * horas * 0.5
            nueva_sev = cond.get("severidad", 1) - recuperacion_tick
            if nueva_sev <= 0:
                a_remover.append(cond)
                msgs.append(f"✓ Condición {nombre} superada gracias a recuperación acelerada.")
                continue
            cond["severidad"] = round(nueva_sev, 2)

        tiene_efecto = fatiga_extra > 0 or moral_pen > 0 or sed_extra > 0 or daño_hora > 0
        if tiene_efecto:
            msgs.append(f"Condición crónica activa: {nombre}.")

    for cond in a_remover:
        if cond in personaje.condiciones_cronicas:
            personaje.condiciones_cronicas.remove(cond)

    return msgs


def _potencia_farmaco(item: dict) -> float:
    tipo = item.get("tipo", "")
    base = 14.0 if tipo == "medicina" else 24.0
    salud = item.get("efectos", {}).get("salud", 0)
    return base + max(0.0, salud * 0.25)


def _farmacologia_item(item: dict) -> dict:
    base = {
        "principio_activo": item.get("nombre", "compuesto").lower().replace(" ", "_"),
        "clase": "analgesico",
        "dosis": 1.0,
        "dosis_toxica": 2.2,
        "ventana_horas": 6,
        "contraindicaciones": [],
        "no_combinar_con": [],
    }
    extra = item.get("farmacologia", {}) if isinstance(item.get("farmacologia", {}), dict) else {}
    base.update(extra)
    return base


def _hora_absoluta(personaje) -> float:
    return float(getattr(personaje, "dia", 1) * 24 + getattr(personaje, "hora", 0))


def _limpiar_historial_farmacos(personaje, ahora_h: float) -> None:
    personaje.historial_farmacos = [
        h for h in personaje.historial_farmacos
        if (ahora_h - float(h.get("hora_abs", -9999))) <= float(h.get("ventana_horas", 6))
    ]


def _contraindicaciones_presentes(personaje, contra: list[str]) -> list[str]:
    presentes: list[str] = []
    for c in contra:
        if c == "deshidratacion" and getattr(personaje, "sed", 0) >= 75:
            presentes.append(c)
        elif c == "hambre_critica" and getattr(personaje, "hambre", 0) >= 85:
            presentes.append(c)
        elif c == "radiacion_alta" and getattr(personaje, "radiacion", 0) >= 60:
            presentes.append(c)
    return presentes


def _clip(valor: int | float, low: int, high: int) -> int:
    return int(max(low, min(high, valor)))


# ──────────────────────────────────────────────────────────────────────────────
#  ADQUISICIÓN DINÁMICA DE CONDICIONES CRÓNICAS
# ──────────────────────────────────────────────────────────────────────────────

def evaluar_adquisicion_condiciones(
    personaje,
    clima_id: str,
    horas: float,
    en_refugio: bool = False,
) -> list[str]:
    """
    Evalúa si el personaje adquiere alguna condición crónica a partir del
    estado actual y el clima. Solo condiciones adquiribles (adquirible=True).
    No añade condiciones que el personaje ya tiene.
    Devuelve lista de mensajes para la bitácora.
    """
    from data.condiciones_medicas import CONDICIONES_CRONICAS
    import random

    if horas <= 0:
        return []

    msgs: list[str] = []
    ya_tiene = {c.get("clave") for c in getattr(personaje, "condiciones_cronicas", [])}
    rng = random.Random(f"{personaje.partida_id}:{personaje.dia}:{personaje.hora}:{clima_id}")

    # ── Condiciones activadas por clima peligroso ─────────────────────────────
    if not en_refugio:
        clima_riesgo_map: dict[str, str] = {
            "lluvia_acida":      "quemaduras_acidas",
            "granizo_acido":     "quemaduras_acidas",
            "polvo_toxico":      "envenenamiento_quimico",
            "ventisca_polar":    "hipotermia",
            "tormenta_radiacion":"envenenamiento_radiacion",
        }
        clave_clima = clima_riesgo_map.get(clima_id)
        if clave_clima and clave_clima not in ya_tiene:
            defn = CONDICIONES_CRONICAS.get(clave_clima, {})
            from data.clima import CLIMAS
            prob_base = float(CLIMAS.get(clima_id, {}).get("prob_condicion", 0.0))

            # La resistencia ambiental del personaje reduce la probabilidad.
            resist_mult = personaje.obtener_efecto_rasgo("resistencia_ambiental_mult", 1.0)
            prob = prob_base * max(0.2, resist_mult)

            if rng.random() < prob * (horas / 3.0):
                msgs.extend(_adquirir_condicion_cronica(personaje, clave_clima, defn, origen=f"exposicion_{clima_id}"))

    # ── Hipotermia por temperatura corporal baja ────────────────────────────
    if "hipotermia" not in ya_tiene:
        tc = getattr(personaje, "temp_corporal", 36.5)
        if tc < 35.0:
            severidad = 35.0 - tc
            prob = min(0.9, 0.15 * severidad) * (horas / 3.0)
            if rng.random() < prob:
                msgs.extend(_adquirir_condicion_cronica(
                    personaje, "hipotermia",
                    CONDICIONES_CRONICAS.get("hipotermia", {}),
                    "temperatura_corporal_baja",
                ))

    # ── Hipertermia / golpe de calor ──────────────────────────────────────
    if "hipertermia" not in ya_tiene:
        tc = getattr(personaje, "temp_corporal", 36.5)
        if tc > 38.5:
            severidad = tc - 38.5
            prob = min(0.9, 0.15 * severidad) * (horas / 3.0)
            if rng.random() < prob:
                msgs.extend(_adquirir_condicion_cronica(
                    personaje, "hipertermia",
                    CONDICIONES_CRONICAS.get("hipertermia", {}),
                    "temperatura_corporal_alta",
                ))

    # ── Sepsis: infección en alguna parte del cuerpo >= 80% ──────────────────
    if "sepsis" not in ya_tiene:
        tiene_infeccion_severa = any(
            int(p.get("infeccion", 0)) >= 80
            for p in getattr(personaje, "cuerpo", {}).values()
            if not p.get("perdida", False)
        )
        if tiene_infeccion_severa and rng.random() < 0.25 * (horas / 6.0):
            msgs.extend(_adquirir_condicion_cronica(personaje, "sepsis", CONDICIONES_CRONICAS.get("sepsis", {}), "infeccion_severa"))

    # ── Envenenamiento por radiación: radiacion > 70 ──────────────────────────
    if "envenenamiento_radiacion" not in ya_tiene and personaje.radiacion >= 70:
        prob = 0.30 * (horas / 6.0)
        if rng.random() < prob:
            msgs.extend(_adquirir_condicion_cronica(personaje, "envenenamiento_radiacion", CONDICIONES_CRONICAS.get("envenenamiento_radiacion", {}), "radiacion_acumulada"))

    # ── Agotamiento profundo: fatiga crítica sostenida ────────────────────────
    if "agotamiento_profundo" not in ya_tiene and personaje.fatiga >= 90:
        prob = 0.12 * (horas / 6.0)
        if rng.random() < prob:
            msgs.extend(_adquirir_condicion_cronica(personaje, "agotamiento_profundo", CONDICIONES_CRONICAS.get("agotamiento_profundo", {}), "fatiga_critica_sostenida"))

    # ── Deshidratación crónica: sed muy alta sostenida ────────────────────────
    if "deshidratacion_cronica" not in ya_tiene and personaje.sed >= 85:
        if rng.random() < 0.10 * (horas / 6.0):
            msgs.extend(_adquirir_condicion_cronica(personaje, "deshidratacion_cronica", CONDICIONES_CRONICAS.get("deshidratacion_cronica", {}), "sed_critica_sostenida"))

    # ── Desnutrición crónica: hambre muy alta sostenida ──────────────────────
    if "desnutricion_cronica" not in ya_tiene and personaje.hambre >= 80:
        if rng.random() < 0.08 * (horas / 6.0):
            msgs.extend(_adquirir_condicion_cronica(personaje, "desnutricion_cronica", CONDICIONES_CRONICAS.get("desnutricion_cronica", {}), "hambre_critica_sostenida"))

    # ── Neumonía: frío+humedad con alta fatiga ────────────────────────────────
    if "neumonia" not in ya_tiene and not en_refugio:
        climas_frio_humedo = {"lluvia", "tormenta", "niebla", "frente_frio", "helada", "ventisca_polar"}
        if clima_id in climas_frio_humedo and personaje.fatiga > 75:
            resist_pulmon = personaje.obtener_efecto_rasgo("riesgo_neumonia_mult", 1.0)
            prob = 0.08 * (horas / 6.0) * resist_pulmon
            if rng.random() < prob:
                msgs.extend(_adquirir_condicion_cronica(personaje, "neumonia", CONDICIONES_CRONICAS.get("neumonia", {}), "frio_humedo_y_fatiga"))

    # ── Trauma psicológico: moral crítica + muertes vistas ───────────────────
    if "trauma_psicologico" not in ya_tiene:
        if personaje.moral <= 15 and personaje.muertes_vistas >= 3:
            if rng.random() < 0.10 * (horas / 6.0):
                msgs.extend(_adquirir_condicion_cronica(personaje, "trauma_psicologico", CONDICIONES_CRONICAS.get("trauma_psicologico", {}), "muerte_vista_o_moral_critica"))

    # ── Síndrome de abstinencia: carga farmacológica alta ────────────────────
    if "sindrome_abstinencia" not in ya_tiene:
        carga = float(getattr(personaje, "farmaco_carga", 0.0))
        if carga >= 100 and rng.random() < 0.20 * (horas / 6.0):
            msgs.extend(_adquirir_condicion_cronica(personaje, "sindrome_abstinencia", CONDICIONES_CRONICAS.get("sindrome_abstinencia", {}), "dependencia_farmacos"))

    return msgs


def _adquirir_condicion_cronica(personaje, clave: str, defn: dict, origen: str) -> list[str]:
    """Añade una condición crónica al personaje y devuelve el mensaje de bitácora."""
    if not defn:
        return []
    personaje.condiciones_cronicas = list(getattr(personaje, "condiciones_cronicas", []))
    personaje.condiciones_cronicas.append({
        "clave":     clave,
        "nombre":    defn.get("nombre", clave),
        "origen":    origen,
        "severidad": int(defn.get("severidad_base", 1)),
        "efectos":   dict(defn.get("efectos", {})),
    })
    nombre = defn.get("nombre", clave)
    return [f"⚠ Nueva condición crónica adquirida: {nombre} (origen: {origen.replace('_', ' ')})."]


def adquirir_condicion_por_consumo(personaje, clave: str, origen: str = "consumo") -> list[str]:
    """Punto de entrada público para forzar la adquisición de una condición crónica por ítem consumido."""
    from data.condiciones_medicas import CONDICIONES_CRONICAS
    existentes = {c["clave"] for c in getattr(personaje, "condiciones_cronicas", [])}
    if clave in existentes:
        return []
    defn = CONDICIONES_CRONICAS.get(clave, {})
    return _adquirir_condicion_cronica(personaje, clave, defn, origen)


# ──────────────────────────────────────────────────────────────
#  TRATAMIENTOS INTERACTIVOS (F3)
# ──────────────────────────────────────────────────────────────

# Items que pueden usarse para tratar condiciones, con su eficacia base.
_ITEMS_TRATAMIENTO: dict[str, dict] = {
    "Botiquín":          {"eficacia": 0.65, "skill_mult": True,  "desc": "tratamiento básico"},
    "Medicina":          {"eficacia": 0.50, "skill_mult": True,  "desc": "medicamento genérico"},
    "Medicina fuerte":   {"eficacia": 0.75, "skill_mult": True,  "desc": "medicamento potente"},
    "Antibióticos":      {"eficacia": 0.80, "skill_mult": False, "desc": "antibiótico específico"},
    "Jeringa morfina":   {"eficacia": 0.30, "skill_mult": False, "desc": "alivio temporal del dolor"},
}

# Condiciones que no se pueden curar, solo reducir severidad.
_CONDICIONES_INCURABLES = frozenset({
    "amputacion_pierna", "amputacion_brazo", "ceguera_parcial",
    "sordera_parcial", "trauma_cerebral_leve", "asma_cronica", "hipertension",
})


def intentar_tratamiento(personaje, clave_condicion: str, nombre_item: str) -> dict:
    """
    Intenta tratar una condición crónica usando un ítem médico.

    Retorna:
        {
          "exito": bool,
          "curado": bool,        # True si la condición desapareció
          "severidad_reducida": bool,
          "mensaje": str,
        }
    """
    import random
    from data.condiciones_medicas import CONDICIONES_CRONICAS

    # Verificar que el ítem existe en el inventario
    if not personaje.tiene_item(nombre_item):
        return {"exito": False, "curado": False, "severidad_reducida": False,
                "mensaje": f"No tienes {nombre_item} en el inventario."}

    # Verificar que la condición está activa
    condicion_activa = next(
        (c for c in getattr(personaje, "condiciones_cronicas", [])
         if c.get("clave") == clave_condicion),
        None
    )
    if not condicion_activa:
        return {"exito": False, "curado": False, "severidad_reducida": False,
                "mensaje": "Esa condición no está activa."}

    config_item = _ITEMS_TRATAMIENTO.get(nombre_item)
    if not config_item:
        return {"exito": False, "curado": False, "severidad_reducida": False,
                "mensaje": f"{nombre_item} no es un ítem de tratamiento válido."}

    # Calcular probabilidad de éxito
    eficacia = config_item["eficacia"]
    if config_item["skill_mult"]:
        skill_medicina = personaje.skills.get("medicina", 0)
        bonus = skill_medicina * 0.003     # máximo +30% con skill 100
        eficacia = min(0.95, eficacia + bonus)

    # La severidad alta reduce las probabilidades de éxito
    severidad = int(condicion_activa.get("severidad", 1))
    eficacia = max(0.10, eficacia - (severidad - 1) * 0.15)

    # Consumir el ítem siempre (se usa aunque falle)
    personaje.remover_item(nombre_item)
    personaje.skills["medicina"] = min(100, personaje.skills.get("medicina", 0) + 2)

    rng = random.Random()
    nombre_condicion = condicion_activa.get("nombre", clave_condicion)
    incurable = clave_condicion in _CONDICIONES_INCURABLES

    if rng.random() < eficacia:
        if incurable or severidad > 1:
            # Reducir severidad
            condicion_activa["severidad"] = max(1, severidad - 1)
            return {
                "exito": True, "curado": False, "severidad_reducida": True,
                "mensaje": (
                    f"✓ Tratamiento parcialmente exitoso. "
                    f"La severidad de {nombre_condicion} se redujo."
                ),
            }
        else:
            # Curar completamente
            personaje.condiciones_cronicas = [
                c for c in personaje.condiciones_cronicas
                if c.get("clave") != clave_condicion
            ]
            return {
                "exito": True, "curado": True, "severidad_reducida": False,
                "mensaje": f"✓ {nombre_condicion} tratada con éxito. Te sientes mejor.",
            }
    else:
        return {
            "exito": False, "curado": False, "severidad_reducida": False,
            "mensaje": (
                f"✗ El tratamiento no surtió efecto en {nombre_condicion}. "
                "El ítem fue usado de todas formas."
            ),
        }


def items_tratamiento_disponibles(personaje) -> list[str]:
    """Retorna los nombres de ítems de tratamiento que el personaje tiene en inventario."""
    disponibles = []
    for nombre in _ITEMS_TRATAMIENTO:
        if personaje.tiene_item(nombre):
            disponibles.append(nombre)
    return disponibles
