# ============================================================
# data/stats.py
# Definición de estadísticas base del personaje.
#
# Para agregar una stat nueva:
#   1. Añadir una entrada al diccionario STATS
#   2. Opcionalmente referenciarla en data/skills.py
#   Nada más. El engine la leerá automáticamente.
# ============================================================

STATS = {
    "fuerza": {
        "nombre":      "Fuerza",
        "abrev":       "FUE",
        "descripcion": "Capacidad física bruta. Afecta el daño cuerpo a cuerpo, "
                       "la carga máxima y forzar obstáculos.",
        "min":   1,
        "max":  10,
        "icono": "💪",
        # Efecto pasivo automático sobre atributos derivados
        "efectos_pasivos": {
            "carga_max":  2.0,   # +2 kg por punto
        },
    },
    "destreza": {
        "nombre":      "Destreza",
        "abrev":       "DES",
        "descripcion": "Agilidad, coordinación y precisión. Sirve para esquivar, "
                       "usar armas a distancia y moverse en silencio.",
        "min":   1,
        "max":  10,
        "icono": "🏃",
        "efectos_pasivos": {},
    },
    "resistencia": {
        "nombre":      "Resistencia",
        "abrev":       "RES",
        "descripcion": "Aguante físico. Determina los puntos de salud máximos "
                       "y cuánto tarda el hambre/sed en volverse críticos.",
        "min":   1,
        "max":  10,
        "icono": "🛡️",
        "efectos_pasivos": {
            "salud_max":   5.0,   # +5 HP por punto
            "energia_max": 3.0,   # +3 energía por punto
        },
    },
    "percepcion": {
        "nombre":      "Percepción",
        "abrev":       "PER",
        "descripcion": "Atención al entorno. Permite detectar trampas, "
                       "encontrar loot oculto y anticiparse a emboscadas.",
        "min":   1,
        "max":  10,
        "icono": "👁️",
        "efectos_pasivos": {},
    },
    "inteligencia": {
        "nombre":      "Inteligencia",
        "abrev":       "INT",
        "descripcion": "Capacidad analítica. Mejora el uso de medicina, "
                       "mecánica y la toma de decisiones bajo presión.",
        "min":   1,
        "max":  10,
        "icono": "🧠",
        "efectos_pasivos": {},
    },
    "suerte": {
        "nombre":      "Suerte",
        "abrev":       "SRT",
        "descripcion": "Factor impredecible. Influye en el loot encontrado, "
                       "los golpes críticos y los eventos aleatorios.",
        "min":   1,
        "max":  10,
        "icono": "🍀",
        "efectos_pasivos": {
            "loot_bonus":  0.05,  # +5% multiplicador de loot por punto
        },
    },

    # ── EJEMPLO: cómo agregar una stat nueva ─────────────────
    # "carisma": {
    #     "nombre":      "Carisma",
    #     "abrev":       "CAR",
    #     "descripcion": "Capacidad de influir en otros sobrevivientes.",
    #     "min":   1,
    #     "max":  10,
    #     "icono": "🗣️",
    #     "efectos_pasivos": {},
    # },
}


# Atributos vitales del personaje
# Estos no son stats (no se tiran dados contra ellos),
# sino medidores que fluctúan durante el juego.
VITALES = {
    "salud": {
        "nombre":   "Salud",
        "abrev":    "SAL",
        "icono":    "❤️",
        "base":      50,          # antes de aplicar bonus de Resistencia
        "critico":   20,          # % por debajo del cual hay penalizaciones
        "min":        0,
        "max_base": 100,
        "deterioro_por_turno": 0,  # natural (hambre/sed lo manejan ellos)
    },
    "hambre": {
        "nombre":      "Hambre",
        "abrev":       "HAM",
        "icono":       "🍖",
        "base":          0,
        "critico":      80,        # % a partir del cual hay daño por turno
        "subida_hora":  (5, 9),    # rango aleatorio por hora activa
        "daño_critico":  3,        # HP por hora cuando hambre >= critico
        "max_base":    100,
    },
    "sed": {
        "nombre":      "Sed",
        "abrev":       "SED",
        "icono":       "💧",
        "base":          0,
        "critico":      80,
        "subida_hora":  (8, 13),   # sube más rápido que el hambre
        "daño_critico":  8,
        "max_base":    100,
    },
    "fatiga": {
        "nombre":      "Fatiga",
        "abrev":       "FAT",
        "icono":       "😴",
        "base":         20,
        "critico":      80,
        "subida_hora":  (4, 8),
        "recuperacion_descanso": 40,  # fatiga reducida por turno de descanso
        "max_base":    100,
    },
    "moral": {
        "nombre":      "Moral",
        "abrev":       "MOR",
        "icono":       "🧭",
        "base":         70,
        "critico":      25,        # por debajo hay penalizaciones a skills
        "max_base":    100,
    },
    "radiacion": {
        "nombre":      "Radiación",
        "abrev":       "RAD",
        "icono":       "☢️",
        "base":          0,
        "critico":      70,
        "daño_critico":  5,
        "max_base":    100,
        "decae":      False,       # no se cura sola, necesita tratamiento
    },
}
