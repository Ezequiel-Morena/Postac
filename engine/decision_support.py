# ============================================================
# engine/decision_support.py
# Soporte de decisiones tácticas para supervivencia.
# Mantiene la lógica fuera de main.py para mejorar testabilidad.
# ============================================================

from dataclasses import dataclass
from typing import Callable


SALUD_CRITICA_PCT = 0.35
SALUD_TENSION_PCT = 0.55
SED_CRITICA = 80
SED_TENSION = 65
HAMBRE_CRITICA = 82
HAMBRE_TENSION = 70
FATIGA_CRITICA = 85
FATIGA_TENSION = 70

AUTO_SED_MIN = 55
AUTO_HAMBRE_MIN = 60
AUTO_SALUD_MIN_PCT = 0.60
AUTO_SALUD_EMERGENCIA_PCT = 0.35


@dataclass(frozen=True)
class DiagnosticoSupervivencia:
    nivel: str
    recomendacion: str
    presion: int


@dataclass(frozen=True)
class AutoSupervivenciaPolicy:
    sed_min: int = AUTO_SED_MIN
    hambre_min: int = AUTO_HAMBRE_MIN
    salud_min_pct: float = AUTO_SALUD_MIN_PCT
    salud_emergencia_pct: float = AUTO_SALUD_EMERGENCIA_PCT
    salud_objetivo_pct: float = 0.70
    max_intentos_normal: int = 1
    max_intentos_emergencia: int = 3


def diagnosticar_supervivencia(personaje) -> DiagnosticoSupervivencia:
    """Evalua el estado general y devuelve un diagnostico compacto."""
    salud_pct = personaje.salud / max(1, personaje.salud_max)
    presion = 0

    if salud_pct < SALUD_CRITICA_PCT:
        presion += 2
    elif salud_pct < SALUD_TENSION_PCT:
        presion += 1

    if personaje.sed > SED_CRITICA:
        presion += 2
    elif personaje.sed > SED_TENSION:
        presion += 1

    if personaje.hambre > HAMBRE_CRITICA:
        presion += 2
    elif personaje.hambre > HAMBRE_TENSION:
        presion += 1

    if personaje.fatiga > FATIGA_CRITICA:
        presion += 2
    elif personaje.fatiga > FATIGA_TENSION:
        presion += 1

    if presion >= 5:
        return DiagnosticoSupervivencia(
            nivel="critico",
            recomendacion="prioriza descanso/consumo antes de exponerte",
            presion=presion,
        )
    if presion >= 3:
        return DiagnosticoSupervivencia(
            nivel="tension",
            recomendacion="elige zonas de peligro bajo y duracion corta",
            presion=presion,
        )
    return DiagnosticoSupervivencia(
        nivel="estable",
        recomendacion="puedes asumir riesgo moderado",
        presion=presion,
    )


def generar_alertas_supervivencia(personaje, diagnostico: DiagnosticoSupervivencia | None = None) -> list[tuple[str, str]]:
    """
    Retorna alertas en formato (nivel, mensaje).
    nivel: info | warning | critical
    """
    d = diagnostico or diagnosticar_supervivencia(personaje)
    alertas: list[tuple[str, str]] = []

    alertas.append(("info", f"Diagnostico: {d.nivel.upper()} - {d.recomendacion}"))

    if personaje.hambre > HAMBRE_CRITICA:
        alertas.append(("critical", "HAMBRE CRITICA - necesitas comer"))
    if personaje.sed > SED_CRITICA:
        alertas.append(("critical", "SED CRITICA - necesitas agua"))
    if personaje.salud < personaje.salud_max * 0.25:
        alertas.append(("critical", "SALUD CRITICA - al borde de la muerte"))
    if personaje.fatiga > FATIGA_CRITICA:
        alertas.append(("warning", "Agotamiento extremo - descansa"))

    if d.nivel != "estable":
        alertas.append(("warning", "Sugerencia: usa [a] Auto-supervivencia antes de salir."))

    return alertas


def confirmar_salida_expedicion(
    personaje,
    area: dict,
    es_interactivo_fn: Callable[[], bool],
    confirmar_fn: Callable[[str, bool], bool],
) -> bool:
    """Aplica politica de confirmacion segun el estado tactico."""
    if not es_interactivo_fn():
        return True

    d = diagnosticar_supervivencia(personaje)
    if d.nivel == "critico" and area.get("peligro", 3) >= 3:
        return confirmar_fn("Estado critico: aun asi deseas salir?", default_no=True)
    return confirmar_fn("Salir de expedicion ahora?", default_no=False)


def aplicar_auto_supervivencia(
    personaje,
    policy: AutoSupervivenciaPolicy | None = None,
) -> list[str]:
    """Consume recursos de forma automatica y devuelve un log de acciones."""
    politica = policy or AutoSupervivenciaPolicy()
    acciones: list[str] = []
    salud_pct = personaje.salud / max(1, personaje.salud_max)
    en_emergencia = salud_pct <= politica.salud_emergencia_pct

    if personaje.sed >= politica.sed_min:
        agua = _primer_item_por_tipo(personaje, "agua")
        if agua:
            ok, msg = personaje.usar_item(agua["nombre"])
            if ok:
                acciones.append(f"Bebiste {agua['nombre']}: {msg}")

    if personaje.hambre >= politica.hambre_min:
        comida = _primer_item_por_tipo(personaje, "comida")
        if comida:
            ok, msg = personaje.usar_item(comida["nombre"])
            if ok:
                acciones.append(f"Comiste {comida['nombre']}: {msg}")

    if _debe_iniciar_tratamiento(personaje, politica):
        pool = _items_por_tipos(personaje, ["medicina", "medicina_fuerte"])
        intentos = 0
        max_intentos = (
            politica.max_intentos_emergencia
            if en_emergencia
            else politica.max_intentos_normal
        )

        while pool and intentos < max_intentos and _necesita_mas_tratamiento(personaje, politica):
            medicina = pool.pop(0)
            ok, msg = personaje.usar_item(medicina["nombre"], forzar_supervivencia=en_emergencia)
            intentos += 1

            if ok:
                acciones.append(f"Tratamiento con {medicina['nombre']}: {msg}")
            elif en_emergencia:
                # En emergencia seguimos intentando con alternativas disponibles.
                acciones.append(f"Intento médico con {medicina['nombre']}: {msg}")

            if personaje.salud <= 0:
                break

        if en_emergencia and intentos > 0 and personaje.salud < personaje.salud_max * politica.salud_emergencia_pct:
            acciones.append("Estado crítico persistente: se prioriza tratamiento agresivo para evitar muerte en reposo.")

    return acciones


def _debe_iniciar_tratamiento(personaje, politica: AutoSupervivenciaPolicy) -> bool:
    return personaje.salud < personaje.salud_max * politica.salud_min_pct


def _necesita_mas_tratamiento(personaje, politica: AutoSupervivenciaPolicy) -> bool:
    return personaje.salud < personaje.salud_max * politica.salud_objetivo_pct


def _primer_item_por_tipo(personaje, tipo: str):
    # Priorizamos lo ultimo agregado para respetar decisiones tacticas recientes
    # (loot inmediato o item recien crafteado) y volver la IA mas predecible.
    return next((it for it in reversed(personaje.inventario) if it.get("tipo") == tipo), None)


def _items_por_tipos(personaje, tipos: list[str]) -> list[dict]:
    set_tipos = set(tipos)
    items = [it for it in personaje.inventario if it.get("tipo") in set_tipos]
    return sorted(items, key=lambda it: (0 if it.get("tipo") == "medicina" else 1, it.get("nombre", "")))
