# ============================================================
# data/skills.py
# Habilidades del personaje y sus fórmulas de derivación.
#
# Para agregar una skill nueva:
#   1. Añadir una entrada al diccionario SKILLS
#   2. Definir qué stats la componen y con qué peso
#   3. Opcionalmente añadir usos en data/eventos.py o data/areas.py
#   El engine la calculará automáticamente en la creación del personaje.
# ============================================================

SKILLS = {
    # ── COMBATE ───────────────────────────────────────────────
    "combate_cac": {
        "nombre":      "Combate C.A.C.",
        "abrev":       "CAC",
        "descripcion": "Efectividad con armas de mano: cuchillos, bates, hachas.",
        "icono":       "⚔️",
        # Cada tupla: (nombre_stat, multiplicador)
        # Resultado: sum(stat * mult) → clampeado a [0, max]
        "derivacion":  [("fuerza", 5), ("destreza", 5)],
        "max":         100,
        "categoria":   "combate",
        # Cómo mejora con uso (XP ganada por acción relevante)
        "xp_por_uso":  2,
    },
    "combate_distancia": {
        "nombre":      "Combate a distancia",
        "abrev":       "CDI",
        "descripcion": "Puntería con armas de fuego, arcos e improvisadas.",
        "icono":       "🎯",
        "derivacion":  [("destreza", 5), ("percepcion", 4), ("suerte", 1)],
        "max":         100,
        "categoria":   "combate",
        "xp_por_uso":  2,
    },
    "sigilo": {
        "nombre":      "Sigilo",
        "abrev":       "SIG",
        "descripcion": "Moverse sin ser detectado. Evitar emboscadas y patrullas.",
        "icono":       "🌑",
        "derivacion":  [("destreza", 5), ("percepcion", 5)],
        "max":         100,
        "categoria":   "supervivencia",
        "xp_por_uso":  2,
    },
    "medicina": {
        "nombre":      "Medicina",
        "abrev":       "MED",
        "descripcion": "Tratar heridas, enfermedades e infecciones correctamente.",
        "icono":       "🩺",
        "derivacion":  [("inteligencia", 6), ("suerte", 2), ("percepcion", 2)],
        "max":         100,
        "categoria":   "conocimiento",
        "xp_por_uso":  3,
    },
    "saqueo": {
        "nombre":      "Saqueo / Forrajeo",
        "abrev":       "SAQ",
        "descripcion": "Eficiencia para encontrar recursos en zonas exploradas.",
        "icono":       "🎒",
        "derivacion":  [("percepcion", 5), ("inteligencia", 3), ("suerte", 2)],
        "max":         100,
        "categoria":   "supervivencia",
        "xp_por_uso":  1,
    },
    "supervivencia": {
        "nombre":      "Supervivencia",
        "abrev":       "SUP",
        "descripcion": "Orientación, refugio improvisado, señales, trampas de caza.",
        "icono":       "🏕️",
        "derivacion":  [("resistencia", 4), ("inteligencia", 4), ("percepcion", 2)],
        "max":         100,
        "categoria":   "supervivencia",
        "xp_por_uso":  2,
    },
    "persuasion": {
        "nombre":      "Persuasión",
        "abrev":       "PER",
        "descripcion": "Negociar, convencer y calmar situaciones con NPCs.",
        "icono":       "🗣️",
        "derivacion":  [("inteligencia", 5), ("suerte", 3), ("percepcion", 2)],
        "max":         100,
        "categoria":   "social",
        "xp_por_uso":  3,
    },
    "mecanica": {
        "nombre":      "Mecánica",
        "abrev":       "MEC",
        "descripcion": "Reparar, fabricar y forzar mecanismos.",
        "icono":       "🔧",
        "derivacion":  [("inteligencia", 5), ("fuerza", 2), ("destreza", 3)],
        "max":         100,
        "categoria":   "conocimiento",
        "xp_por_uso":  3,
    },

    # ── EJEMPLO: cómo agregar una skill nueva ─────────────────
    # "electronica": {
    #     "nombre":      "Electrónica",
    #     "abrev":       "ELE",
    #     "descripcion": "Hackear sistemas, reparar radios, fabricar trampas eléctricas.",
    #     "icono":       "⚡",
    #     "derivacion":  [("inteligencia", 7), ("destreza", 3)],
    #     "max":         100,
    #     "categoria":   "conocimiento",
    #     "xp_por_uso":  3,
    # },
    # "navegacion": {
    #     "nombre":      "Navegación",
    #     "abrev":       "NAV",
    #     "descripcion": "Leer mapas, orientarse, evitar zonas peligrosas.",
    #     "icono":       "🧭",
    #     "derivacion":  [("percepcion", 6), ("inteligencia", 4)],
    #     "max":         100,
    #     "categoria":   "supervivencia",
    #     "xp_por_uso":  1,
    # },
}

# Categorías de skills (para mostrar en UI agrupadas)
CATEGORIAS_SKILLS = {
    "combate":      "⚔️  Combate",
    "supervivencia": "🏕️  Supervivencia",
    "conocimiento": "📚  Conocimiento",
    "social":       "🤝  Social",
}
