# ============================================================
# data/skills.py
# Habilidades del personaje y sus fórmulas de derivación.
#
# Para agregar una skill nueva:
#   1. Añadir una entrada al diccionario SKILLS
#   2. Definir qué stats la componen y con qué peso
#   3. Definir xp_base y xp_incremento para la curva de progreso
#   El engine la calculará y progresará automáticamente.
#
# CURVA DE XP:
#   xp_necesaria = xp_base + (nivel_actual // 10) * xp_incremento
#   Ejemplo con xp_base=10, xp_incremento=5:
#     Nivel 20 → 20 XP para +1   |   Nivel 50 → 35 XP   |   Nivel 80 → 50 XP
# ============================================================

SKILLS = {
    # ── COMBATE ───────────────────────────────────────────────
    "combate_cac": {
        "nombre":        "Combate C.A.C.",
        "abrev":         "CAC",
        "descripcion":   "Efectividad con armas de mano: cuchillos, bates, hachas.",
        "icono":         "⚔️",
        "derivacion":    [("fuerza", 5), ("destreza", 5)],
        "max":           100,
        "categoria":     "combate",
        "xp_por_uso":    2,     # XP ganada por cada acción exitosa con esta skill
        "xp_base":       8,     # XP mínima para +1 punto (niveles bajos)
        "xp_incremento": 4,     # XP adicional cada 10 niveles
    },
    "combate_distancia": {
        "nombre":        "Combate a distancia",
        "abrev":         "CDI",
        "descripcion":   "Puntería con armas de fuego, arcos e improvisadas.",
        "icono":         "🎯",
        "derivacion":    [("destreza", 5), ("percepcion", 4), ("suerte", 1)],
        "max":           100,
        "categoria":     "combate",
        "xp_por_uso":    2,
        "xp_base":       8,
        "xp_incremento": 4,
    },
    "sigilo": {
        "nombre":        "Sigilo",
        "abrev":         "SIG",
        "descripcion":   "Moverse sin ser detectado. Evitar emboscadas y patrullas.",
        "icono":         "🌑",
        "derivacion":    [("destreza", 5), ("percepcion", 5)],
        "max":           100,
        "categoria":     "supervivencia",
        "xp_por_uso":    2,
        "xp_base":       8,
        "xp_incremento": 4,
    },
    "medicina": {
        "nombre":        "Medicina",
        "abrev":         "MED",
        "descripcion":   "Tratar heridas, enfermedades e infecciones correctamente.",
        "icono":         "🩺",
        "derivacion":    [("inteligencia", 6), ("suerte", 2), ("percepcion", 2)],
        "max":           100,
        "categoria":     "conocimiento",
        "xp_por_uso":    3,
        "xp_base":       12,    # Más difícil de subir: conocimiento especializado
        "xp_incremento": 6,
    },
    "saqueo": {
        "nombre":        "Saqueo / Forrajeo",
        "abrev":         "SAQ",
        "descripcion":   "Eficiencia para encontrar recursos en zonas exploradas.",
        "icono":         "🎒",
        "derivacion":    [("percepcion", 5), ("inteligencia", 3), ("suerte", 2)],
        "max":           100,
        "categoria":     "supervivencia",
        "xp_por_uso":    1,
        "xp_base":       6,     # Más fácil de subir: se practica en cada expedición
        "xp_incremento": 3,
    },
    "supervivencia": {
        "nombre":        "Supervivencia",
        "abrev":         "SUP",
        "descripcion":   "Orientación, refugio improvisado, señales, trampas de caza.",
        "icono":         "🏕️",
        "derivacion":    [("resistencia", 4), ("inteligencia", 4), ("percepcion", 2)],
        "max":           100,
        "categoria":     "supervivencia",
        "xp_por_uso":    2,
        "xp_base":       10,
        "xp_incremento": 5,
    },
    "persuasion": {
        "nombre":        "Persuasión",
        "abrev":         "PER",
        "descripcion":   "Negociar, convencer y calmar situaciones con NPCs.",
        "icono":         "🗣️",
        "derivacion":    [("inteligencia", 5), ("suerte", 3), ("percepcion", 2)],
        "max":           100,
        "categoria":     "social",
        "xp_por_uso":    3,
        "xp_base":       12,    # Raro de practicar — cada uso cuenta más
        "xp_incremento": 6,
    },
    "mecanica": {
        "nombre":        "Mecánica",
        "abrev":         "MEC",
        "descripcion":   "Reparar, fabricar y forzar mecanismos.",
        "icono":         "🔧",
        "derivacion":    [("inteligencia", 5), ("fuerza", 2), ("destreza", 3)],
        "max":           100,
        "categoria":     "conocimiento",
        "xp_por_uso":    3,
        "xp_base":       12,
        "xp_incremento": 6,
    },

    # ── EJEMPLO: cómo agregar una skill nueva ─────────────────
    # "electronica": {
    #     "nombre":        "Electrónica",
    #     "abrev":         "ELE",
    #     "descripcion":   "Hackear sistemas, reparar radios, fabricar trampas.",
    #     "icono":         "⚡",
    #     "derivacion":    [("inteligencia", 7), ("destreza", 3)],
    #     "max":           100,
    #     "categoria":     "conocimiento",
    #     "xp_por_uso":    3,
    #     "xp_base":       12,
    #     "xp_incremento": 6,
    # },
}

# Categorías de skills (para mostrar en UI agrupadas)
CATEGORIAS_SKILLS = {
    "combate":       "⚔️  Combate",
    "supervivencia": "🏕️  Supervivencia",
    "conocimiento":  "📚  Conocimiento",
    "social":        "🤝  Social",
}
