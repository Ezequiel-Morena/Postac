# ============================================================
# engine/temperatura.py — Motor de temperatura corporal
#
# Calcula la temperatura corporal del personaje en función de:
#   - Temperatura ambiente (del clima)
#   - Viento y humedad (wind chill / heat index)
#   - Ropa equipada (aislamiento efectivo, mojado)
#   - Fuego activo y refugio
#   - Rasgos del personaje
#
# Produce efectos graduales: hipotermia, hipertermia, congelación.
# ============================================================

from __future__ import annotations

from data.vestimenta import MATERIALES, PRENDAS, SLOTS_ROPA
from engine.constants import clamp

# ── Constantes ───────────────────────────────────────────────

TEMP_CORPORAL_NORMAL = 36.5
TEMP_CORPORAL_MIN = 28.0   # muerte por hipotermia
TEMP_CORPORAL_MAX = 42.0   # muerte por hipertermia

# Umbrales de hipotermia (grados corporales)
HIPOTERMIA_LEVE = 35.0     # temblores, confusión leve
HIPOTERMIA_MODERADA = 33.0 # somnolencia, rigidez muscular
HIPOTERMIA_SEVERA = 30.0   # pérdida de consciencia
HIPOTERMIA_CRITICA = 28.0  # paro cardíaco

# Umbrales de hipertermia
HIPERTERMIA_LEVE = 38.0    # sudoración excesiva, sed
HIPERTERMIA_MODERADA = 39.5  # mareo, náuseas
HIPERTERMIA_SEVERA = 40.5  # golpe de calor, delirio
HIPERTERMIA_CRITICA = 42.0 # fallo orgánico

# Umbrales de congelación en extremidades (horas de exposición bajo 0°C sin protección)
CONGELACION_HORAS_INICIO = 2.0

# Velocidad de regulación corporal (°C por hora hacia 36.5)
REGULACION_BASE = 0.8

# Factor de aislamiento máximo teórico (100 en todos los slots)
_AISLAMIENTO_MAX_TEORICO = 100.0 * len(SLOTS_ROPA)


# ── Cálculo de aislamiento efectivo ─────────────────────────

def aislamiento_efectivo(
    ropa_equipada: dict[str, dict],
    humedad_ropa: float,
    es_frio: bool,
) -> float:
    """Calcula el aislamiento total de la ropa equipada (0-100 normalizado).

    Si es_frio=True usa aislamiento_frio; si False, aislamiento_calor.
    La humedad_ropa (0-100) degrada el aislamiento según el material.
    """
    total = 0.0
    campo = "aislamiento_frio" if es_frio else "aislamiento_calor"

    for slot in SLOTS_ROPA:
        prenda = ropa_equipada.get(slot)
        if not prenda:
            continue

        valor_base = float(prenda.get(campo, 0))
        if humedad_ropa > 0:
            material_key = prenda.get("material", "algodon")
            mat = MATERIALES.get(material_key, MATERIALES["algodon"])
            factor = mat["factor_mojado"]
            # Interpolar: a 100% humedad se aplica factor completo
            degradacion = 1.0 - (1.0 - factor) * (humedad_ropa / 100.0)
            valor_base *= degradacion

        total += valor_base

    # Normalizar a 0-100
    return min(100.0, total * 100.0 / _AISLAMIENTO_MAX_TEORICO)


def impermeabilidad_total(ropa_equipada: dict[str, dict]) -> float:
    """Impermeabilidad media ponderada de la ropa (0-100).

    La capa exterior tiene peso doble porque es la primera barrera.
    """
    if not ropa_equipada:
        return 0.0

    total = 0.0
    peso_total = 0.0
    for slot in SLOTS_ROPA:
        prenda = ropa_equipada.get(slot)
        if not prenda:
            continue
        peso_slot = 2.0 if slot == "capa_exterior" else 1.0
        total += float(prenda.get("impermeabilidad", 0)) * peso_slot
        peso_total += peso_slot

    return total / max(1.0, peso_total)


def proteccion_radiacion_total(ropa_equipada: dict[str, dict]) -> float:
    """Protección total contra radiación (suma directa, 0-100 cap)."""
    return min(100.0, sum(
        float(p.get("radiacion_prot", 0))
        for p in ropa_equipada.values()
        if p
    ))


# ── Sensación térmica ────────────────────────────────────────

def temperatura_sensacion(temp_c: float, viento_kmh: float, humedad_rel: float) -> float:
    """Calcula la temperatura de sensación (wind chill o heat index simplificado).

    Wind chill: aplica cuando temp < 10°C y hay viento.
    Heat index: aplica cuando temp > 27°C y hay humedad alta.
    """
    if temp_c <= 10.0 and viento_kmh > 5.0:
        # Fórmula de wind chill simplificada (NWS)
        wc = (
            13.12
            + 0.6215 * temp_c
            - 11.37 * (viento_kmh ** 0.16)
            + 0.3965 * temp_c * (viento_kmh ** 0.16)
        )
        return round(min(temp_c, wc), 1)

    if temp_c >= 27.0 and humedad_rel > 40.0:
        # Heat index simplificado (NOAA)
        hi = temp_c + 0.5 * (humedad_rel - 40.0) * 0.05
        return round(max(temp_c, hi), 1)

    return round(temp_c, 1)


# ── Motor principal ──────────────────────────────────────────

def calcular_temp_corporal(
    temp_actual: float,
    temp_ambiente: float,
    viento_kmh: float,
    humedad_rel: float,
    ropa_equipada: dict[str, dict],
    humedad_ropa: float,
    fuego_activo: bool,
    en_refugio: bool,
    horas: float,
    mult_resistencia: float = 1.0,
) -> tuple[float, list[str]]:
    """Calcula la nueva temperatura corporal tras un período de tiempo.

    Returns:
        (nueva_temp_corporal, lista_mensajes)
    """
    msgs: list[str] = []

    # Sensación térmica efectiva
    t_sensacion = temperatura_sensacion(temp_ambiente, viento_kmh, humedad_rel)

    # El refugio reduce la exposición
    if en_refugio:
        # Interior: la temperatura se modera hacia 15-25°C
        t_sensacion = t_sensacion * 0.3 + 18.0 * 0.7
        if fuego_activo:
            t_sensacion = max(t_sensacion, 22.0)

    # Diferencia entre ambiente y temperatura corporal ideal
    diff = t_sensacion - TEMP_CORPORAL_NORMAL  # negativo=frío, positivo=calor

    # Aislamiento de la ropa (mitiga la diferencia)
    es_frio = diff < 0
    aisl = aislamiento_efectivo(ropa_equipada, humedad_ropa, es_frio)

    # Factor de protección: 0% aislamiento = exposición total, 100% = 80% reducción
    factor_proteccion = 1.0 - (aisl / 100.0) * 0.80

    # Exposición efectiva: cuánto le afecta el ambiente
    exposicion = diff * factor_proteccion * (horas / 6.0)

    # Resistencia del personaje (rasgos)
    exposicion *= (2.0 - mult_resistencia)  # mult > 1 reduce exposición

    # Regulación natural del cuerpo (tiende a volver a 36.5)
    regulacion = (TEMP_CORPORAL_NORMAL - temp_actual) * REGULACION_BASE * (horas / 6.0)

    # Si está en hipotermia severa, la regulación se reduce
    if temp_actual < HIPOTERMIA_MODERADA:
        regulacion *= 0.3
    elif temp_actual < HIPOTERMIA_LEVE:
        regulacion *= 0.7

    # Nueva temperatura
    nueva_temp = temp_actual + exposicion * 0.15 + regulacion
    nueva_temp = round(max(TEMP_CORPORAL_MIN, min(TEMP_CORPORAL_MAX, nueva_temp)), 1)

    # Mensajes de estado
    if nueva_temp < HIPOTERMIA_CRITICA:
        msgs.append("☠ Hipotermia crítica. El cuerpo está al borde del paro cardíaco.")
    elif nueva_temp < HIPOTERMIA_SEVERA:
        msgs.append("🥶 Hipotermia severa. Perdiendo consciencia. Necesita calor urgente.")
    elif nueva_temp < HIPOTERMIA_MODERADA:
        msgs.append("🥶 Hipotermia moderada. Somnolencia y rigidez muscular.")
    elif nueva_temp < HIPOTERMIA_LEVE:
        msgs.append("❄ Hipotermia leve. Temblores y confusión.")
    elif nueva_temp > HIPERTERMIA_CRITICA:
        msgs.append("☠ Hipertermia crítica. Fallo orgánico inminente.")
    elif nueva_temp > HIPERTERMIA_SEVERA:
        msgs.append("🔥 Golpe de calor. Delirio y convulsiones.")
    elif nueva_temp > HIPERTERMIA_MODERADA:
        msgs.append("🌡 Hipertermia moderada. Mareo y náuseas severas.")
    elif nueva_temp > HIPERTERMIA_LEVE:
        msgs.append("🌡 Calor corporal elevado. Sudoración excesiva.")

    return nueva_temp, msgs


# ── Efectos de temperatura sobre stats ───────────────────────

def efectos_temperatura(
    temp_corporal: float,
    horas: float,
) -> dict[str, int]:
    """Calcula los cambios en stats del personaje por temperatura corporal.

    Returns dict con deltas: salud, fatiga, sed, moral, velocidad (para combate).
    """
    efectos: dict[str, int] = {}

    if temp_corporal < HIPOTERMIA_LEVE:
        # Frío: más hambre (el cuerpo quema calorías), más fatiga
        severidad = (HIPOTERMIA_LEVE - temp_corporal) / (HIPOTERMIA_LEVE - TEMP_CORPORAL_MIN)
        factor = min(1.0, severidad) * (horas / 6.0)

        efectos["salud"] = -int(round(factor * 12))
        efectos["fatiga"] = int(round(factor * 15))
        efectos["hambre"] = int(round(factor * 10))
        efectos["moral"] = -int(round(factor * 8))

    elif temp_corporal > HIPERTERMIA_LEVE:
        # Calor: más sed, más fatiga
        severidad = (temp_corporal - HIPERTERMIA_LEVE) / (HIPERTERMIA_CRITICA - HIPERTERMIA_LEVE)
        factor = min(1.0, severidad) * (horas / 6.0)

        efectos["salud"] = -int(round(factor * 10))
        efectos["fatiga"] = int(round(factor * 12))
        efectos["sed"] = int(round(factor * 15))
        efectos["moral"] = -int(round(factor * 6))

    return efectos


# ── Congelación localizada ───────────────────────────────────

def evaluar_congelacion(
    temp_sensacion: float,
    ropa_equipada: dict[str, dict],
    horas: float,
    horas_exposicion_frio_acum: float,
) -> tuple[float, list[str]]:
    """Evalúa riesgo de congelación en extremidades sin protección.

    Returns:
        (nuevas_horas_acumuladas, mensajes)
    """
    msgs: list[str] = []

    if temp_sensacion >= 0:
        # Sin riesgo, reducir acumulación
        return max(0.0, horas_exposicion_frio_acum - horas * 0.5), msgs

    # Extremidades vulnerables: pies, manos, cabeza (nariz/orejas)
    extremidades_expuestas: list[str] = []
    for slot in ("pies", "manos", "cabeza"):
        prenda = ropa_equipada.get(slot)
        if not prenda or float(prenda.get("aislamiento_frio", 0)) < 20:
            extremidades_expuestas.append(slot)

    if not extremidades_expuestas:
        return max(0.0, horas_exposicion_frio_acum - horas * 0.3), msgs

    # Acumular horas de exposición
    nueva_acum = horas_exposicion_frio_acum + horas

    if nueva_acum >= CONGELACION_HORAS_INICIO * 3:
        partes = ", ".join(extremidades_expuestas)
        msgs.append(
            f"☠ Congelación severa en {partes}. "
            "Riesgo de daño permanente."
        )
    elif nueva_acum >= CONGELACION_HORAS_INICIO * 2:
        partes = ", ".join(extremidades_expuestas)
        msgs.append(
            f"🥶 Congelación progresando en {partes}. "
            "Entumecimiento y pérdida de sensibilidad."
        )
    elif nueva_acum >= CONGELACION_HORAS_INICIO:
        partes = ", ".join(extremidades_expuestas)
        msgs.append(
            f"❄ Principio de congelación en {partes}. "
            "Dolor intenso y coloración azulada."
        )

    return nueva_acum, msgs


# ── Mojado y secado ──────────────────────────────────────────

def actualizar_humedad_ropa(
    humedad_actual: float,
    clima_id: str,
    impermeabilidad: float,
    en_refugio: bool,
    fuego_activo: bool,
    horas: float,
) -> float:
    """Actualiza la humedad de la ropa según clima y condiciones.

    Returns nueva humedad (0-100).
    """
    climas_mojados = {"lluvia", "tormenta", "lluvia_acida", "granizo_acido"}
    climas_nieve = {"ventisca_polar", "helada"}

    mojado_por_hora = 0.0
    if clima_id in climas_mojados and not en_refugio:
        # Lluvia moja la ropa según impermeabilidad
        mojado_por_hora = 15.0 * (1.0 - impermeabilidad / 100.0)
    elif clima_id in climas_nieve and not en_refugio:
        # Nieve moja menos rápido
        mojado_por_hora = 8.0 * (1.0 - impermeabilidad / 100.0)

    # Secado
    secado_por_hora = 2.0  # secado base
    if en_refugio:
        secado_por_hora = 5.0
    if fuego_activo:
        secado_por_hora = 12.0
    if clima_id == "calor_extremo" and not en_refugio:
        secado_por_hora = 8.0
    if clima_id == "sequedad":
        secado_por_hora += 3.0

    delta = (mojado_por_hora - secado_por_hora) * horas
    nueva = humedad_actual + delta
    return round(max(0.0, min(100.0, nueva)), 1)


# ── Desgaste de ropa ────────────────────────────────────────

def desgastar_ropa(
    ropa_equipada: dict[str, dict],
    horas: float,
    en_expedicion: bool,
    clima_id: str,
) -> list[str]:
    """Reduce la durabilidad de la ropa equipada. Retorna mensajes de alerta.

    La ropa se desgasta más en expedición y con climas agresivos.
    Items con durabilidad <= 0 se marcan para remoción.
    """
    msgs: list[str] = []
    climas_agresivos = {"lluvia_acida", "granizo_acido", "polvo_toxico", "tormenta"}

    desgaste_base = horas * (0.5 if en_expedicion else 0.2)
    if clima_id in climas_agresivos:
        desgaste_base *= 2.0

    for slot, prenda in list(ropa_equipada.items()):
        if not prenda:
            continue

        dur_max = float(prenda.get("durabilidad_max", 100))
        dur_actual = float(prenda.get("durabilidad", dur_max))
        dur_nueva = max(0.0, dur_actual - desgaste_base)
        prenda["durabilidad"] = round(dur_nueva, 1)

        nombre = prenda.get("nombre", slot)
        pct = dur_nueva / max(1.0, dur_max) * 100

        if dur_nueva <= 0:
            msgs.append(f"💔 {nombre} se ha destruido por el desgaste.")
            ropa_equipada[slot] = {}
        elif pct < 15:
            msgs.append(f"⚠ {nombre} a punto de romperse ({int(pct)}%).")
        elif pct < 30:
            msgs.append(f"🔧 {nombre} muy desgastada ({int(pct)}%).")

    return msgs
