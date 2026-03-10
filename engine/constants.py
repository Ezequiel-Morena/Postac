# ============================================================
# engine/constants.py — Constantes nombradas del simulador
#
# Centraliza todos los valores numéricos y umbrales que gobiernan
# la simulación. Ningún módulo debe contener números mágicos;
# cualquier valor que necesite justificación narrativa o de balance
# vive aquí, con un comentario que explica el "por qué".
# ============================================================

# ── PELIGRO DE ZONAS ─────────────────────────────────────────
PELIGRO_MIN = 1
PELIGRO_MAX = 5
# Variación aleatoria ±1 sobre el peligro base de cada área.
PELIGRO_VARIACION = 1

# ── GENERACIÓN DE ZONA (mundo.py) ────────────────────────────
# Probabilidad de que una zona tenga loot excepcional ese día.
PROB_LOOT_ALTO = 0.25
# Probabilidad de que el peligro suba un punto extra al generar.
PROB_RIESGO_ALTO = 0.20
# Al tener loot alto, la expedición dura más (hay más que explorar).
DURACION_MULT_LOOT_ALTO = 1.2
# Las expediciones en invierno son más lentas por el terreno y el frío.
DURACION_MULT_INVIERNO = 1.10
# El verano alarga ligeramente la expedición (calor, descansos extra).
DURACION_MULT_VERANO = 1.05
# Lluvia y niebla reducen la velocidad de movimiento.
DURACION_MULT_MAL_CLIMA = 1.05
# Factores de distancia en km respecto a la duración estimada en horas.
DISTANCIA_FACTOR_MIN = 1.4
DISTANCIA_FACTOR_MAX = 2.5
DISTANCIA_MIN_KM = 0.5
# Las tormentas degradan la calidad del loot encontrado.
LOOT_SCORE_MULT_TORMENTA = 0.92
# Bonus de loot cuando la zona tiene bandera de alto loot.
LOOT_SCORE_MULT_ALTO = 1.25

# ── UMBRALES VITALES (hambre, sed, salud) ────────────────────
# Por encima de estos valores se genera alerta de estado crítico.
HAMBRE_UMBRAL_CRITICO = 70
SED_UMBRAL_CRITICO = 70
# A este % de salud máxima se aborta automáticamente la expedición.
SALUD_PCT_ABORT_EXPEDICION = 0.15
# Por debajo de este % se avisa al inicio de la expedición.
SALUD_PCT_ALERTA_INICIO = 0.40
# Auto-consumo de medicina durante la expedición si la salud cae aquí.
SALUD_PCT_AUTOCONSUMO = 0.30
# Límite de salud para tomar medicina durante el descanso.
SALUD_PCT_DESCANSO_MEDICINA = 0.70
# Umbrales de hambre/sed para consumo durante descanso.
HAMBRE_UMBRAL_DESCANSO = 40
SED_UMBRAL_DESCANSO = 30
# Avisos críticos al final del ciclo de descanso.
HAMBRE_UMBRAL_AVISO_DESCANSO = 75
SED_UMBRAL_AVISO_DESCANSO = 75
# Sed de emergencia durante expedición.
SED_UMBRAL_EMERGENCIA = 85
# Hambre de emergencia durante expedición.
HAMBRE_UMBRAL_EMERGENCIA = 90

# ── MORAL ────────────────────────────────────────────────────
# Bonus de moral por completar una expedición o descansar.
MORAL_BONUS_EXPEDICION = 5
MORAL_BONUS_DESCANSO = 5
MORAL_MIN = 0
MORAL_MAX = 100

# ── COMBATE ──────────────────────────────────────────────────
# Número máximo de turnos antes de que el combate se resuelva por derrota.
MAX_TURNOS_COMBATE = 12
# Si la salud cae por debajo de este porcentaje, el personaje intenta huir.
SALUD_PCT_HUIDA_CRITICA = 0.25
# El turno mínimo antes de que la huida automática sea posible.
TURNO_MIN_HUIDA = 2
# Probabilidad de golpe crítico cuando la suerte es ≥8.
PROB_CRITICO = 0.15
# Multiplicador de daño en golpe crítico.
MULT_DAÑO_CRITICO = 1.8
# Dificultad base del check de golpe del jugador (ajustada por velocidad del enemigo).
DIFICULTAD_GOLPE_BASE = 40
DIFICULTAD_GOLPE_POR_VELOCIDAD = 5
# Probabilidad de que un enemigo deje su loot al ser neutralizado.
PROB_LOOT_ENEMIGO = 0.60
# Multiplicador de daño por emboscada en primer turno.
MULT_DAÑO_EMBOSCADA = 1.5
# Probabilidad de ataque de ácido del mutante.
PROB_ATAQUE_ACIDO = 0.30
# Daño extra del ácido (además del daño base del enemigo).
DAÑO_EXTRA_ACIDO = 8
# Probabilidad de que una mordida infectada contagie condición.
PROB_MORDIDA_INFECTADA = 0.30
# Daño de huida exitosa ante una horda (mínimo-máximo).
DAÑO_HORDA_HUIDA_MIN = 5
DAÑO_HORDA_HUIDA_MAX = 15
# Daño de horda que te atrapa.
DAÑO_HORDA_ATRAPADO_MIN = 25
DAÑO_HORDA_ATRAPADO_MAX = 50
# Daño base de combate sin arma equipada.
DAÑO_MANOS_MIN = 2
DAÑO_MANOS_MAX = 5
# Umbral mínimo de suerte para que el crítico sea posible.
SUERTE_MIN_CRITICO = 8

# ── RELACIONES / REFUGIO ─────────────────────────────────────
# Probabilidad base de que un NPC salga de expedición en un tick.
NPC_PROB_EXPEDICION_BASE = 0.30
# Umbral de tensión grupal a partir del cual se activan eventos.
NPC_TENSION_UMBRAL = 0.50
# Probabilidades de resultado de expedición de NPC.
NPC_EXPEDICION_PROB_RETORNO_BASE = 0.50
NPC_EXPEDICION_PROB_RETORNO_POR_DIA = 0.30
NPC_EXPEDICION_PROB_LESION = 0.12
NPC_EXPEDICION_PROB_MUERTE = 0.04
NPC_EXPEDICION_PROB_EXITO = 0.80
# Modificadores de probabilidad según lealtad del NPC.
NPC_EXPEDICION_BONUS_LEALTAD_ALTA = 0.05
NPC_EXPEDICION_REDUCCION_LESION_LEALTAD = 0.04
NPC_EXPEDICION_REDUCCION_MUERTE_LEALTAD = 0.01
# Probabilidad de que un NPC emigre cuando la tensión es muy alta.
NPC_PROB_EMIGRACION = 0.65
# Recuperación de hambre de un NPC cuando recibe comida del refugio.
NPC_RECUPERACION_HAMBRE_BASE = 0.5  # (hambre -= horas * este_factor)
# Umbral de confianza para que un NPC reaccione emocionalmente.
NPC_CONFIANZA_REACCION = 55
# Porcentaje de salud del jugador que activa el miedo del NPC.
SALUD_PCT_ACTIVA_MIEDO_NPC = 0.25
NPC_PROB_REACCION_MIEDO = 0.4
# Umbral de moral del jugador que genera alertas de NPC.
MORAL_UMBRAL_BAJA = 20
NPC_PROB_ALERTA_MORAL = 0.3
# Salud y moral mínima a la que el miedo del NPC se reduce.
SALUD_PCT_REDUCE_MIEDO = 0.7
MORAL_MINIMA_REDUCE_MIEDO = 60

# ── ENVEJECIMIENTO ───────────────────────────────────────────
# A partir de esta edad empieza la probabilidad de muerte natural.
EDAD_MUERTE_NATURAL_INICIO = 70
# Incremento de probabilidad de muerte natural por año extra.
PROB_MUERTE_NATURAL_POR_ANIO = 0.012

# ── ANIMALES ─────────────────────────────────────────────────
# Número máximo de animales en el refugio.
MAX_ANIMALES_REFUGIO = 6


# ── UTILIDADES ───────────────────────────────────────────────
def clamp(valor: int | float, lo: int = 0, hi: int = 100) -> int:
    """Restringe un valor numérico al rango [lo, hi] y lo convierte a int."""
    return max(lo, min(hi, int(valor)))


# ── COLORES ANSI BASE ────────────────────────────────────────
# Fuente canónica para toda secuencia ANSI del proyecto.
# Los módulos de engine/ y ui/ importan desde aquí.
ANSI_RESET  = "\033[0m"
ANSI_VERDE  = "\033[92m"
ANSI_ROJO   = "\033[91m"
ANSI_AMARILLO = "\033[93m"
ANSI_CYAN   = "\033[96m"
ANSI_GRIS   = "\033[90m"
ANSI_BLANCO = "\033[97m"
ANSI_NEGRITA = "\033[1m"
ANSI_DIM    = "\033[2m"
