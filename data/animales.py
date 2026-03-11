# ============================================================
# data/animales.py
# Catálogo data-driven de animales domésticos del refugio.
#
# Estructura de cada tipo:
#   nombre, icono, desc
#   necesidades_dia: {comida, agua} — unidades por día de juego
#   produce: {comida?, moral?} — genera por día si está sano
#   defensa: int — bonus de defensa del refugio
#   puede_reproducirse: bool
#   zona_encuentro: list[str] — tags de zona donde puede aparecer
#   prob_encuentro: float — probabilidad base por expedición en esa zona
#   eventos_posibles: list[str] — claves de EVENTOS_ANIMALES
#   salud_max: int
# ============================================================

TIPOS_ANIMALES: dict[str, dict] = {
    "perro": {
        "nombre":             "Perro",
        "icono":              "🐕",
        "desc":               "Leal compañero. Avisa de peligros y defiende a los más débiles.",
        "necesidades_dia":    {"comida": 15, "agua": 8},
        "produce":            {},
        "defensa":            2,
        "puede_reproducirse": True,
        "zona_encuentro":     ["residencial", "urbano", "civil"],
        "prob_encuentro":     0.07,
        "eventos_posibles":   ["alerta_intruso", "encuentra_restos", "protege_nino", "herido", "se_enferma", "cria"],
        "salud_max":          80,
    },
    "gato": {
        "nombre":             "Gato",
        "icono":              "🐈",
        "desc":               "Independiente, caza ratas y pequeñas plagas que mermarían la comida.",
        "necesidades_dia":    {"comida": 8, "agua": 4},
        "produce":            {"comida": 3},    # caza pequeñas presas
        "defensa":            0,
        "puede_reproducirse": True,
        "zona_encuentro":     ["residencial", "civil", "interior"],
        "prob_encuentro":     0.06,
        "eventos_posibles":   ["caza_exitosa", "se_enferma", "cria", "desaparece_vuelve"],
        "salud_max":          60,
    },
    "gallina": {
        "nombre":             "Gallina",
        "icono":              "🐔",
        "desc":               "Produce huevos regularmente. Fuente de proteínas estable.",
        "necesidades_dia":    {"comida": 5, "agua": 3},
        "produce":            {"comida": 8},    # huevos diarios
        "defensa":            0,
        "puede_reproducirse": True,
        "zona_encuentro":     ["residencial", "rural", "civil"],
        "prob_encuentro":     0.05,
        "eventos_posibles":   ["pone_huevo", "se_enferma", "cria", "depredador"],
        "salud_max":          40,
    },
    "cabra": {
        "nombre":             "Cabra",
        "icono":              "🐐",
        "desc":               "Da leche a diario. Puede sobrevivir con pastos escasos.",
        "necesidades_dia":    {"comida": 12, "agua": 6},
        "produce":            {"comida": 12, "agua": 5},   # leche → alivia sed también
        "defensa":            1,
        "puede_reproducirse": True,
        "zona_encuentro":     ["rural", "residencial"],
        "prob_encuentro":     0.04,
        "eventos_posibles":   ["produce_leche", "se_enferma", "cria", "huye_asustada"],
        "salud_max":          70,
    },
    "conejo": {
        "nombre":             "Conejo",
        "icono":              "🐇",
        "desc":               "Silencioso y rápido. Se reproduce velozmente; buena fuente de carne.",
        "necesidades_dia":    {"comida": 4, "agua": 2},
        "produce":            {"comida": 5},
        "defensa":            0,
        "puede_reproducirse": True,
        "zona_encuentro":     ["rural", "residencial", "campo"],
        "prob_encuentro":     0.06,
        "eventos_posibles":   ["cria", "se_enferma", "huye_asustada"],
        "salud_max":          35,
    },
}

# Eventos narrativos posibles para los animales
EVENTOS_ANIMALES: dict[str, dict] = {
    "alerta_intruso": {
        "texto": "{nombre} ladra furiosamente ante algo que se acercaba al refugio. Amenaza disuadida.",
        "efecto": {"moral": 3},
    },
    "encuentra_restos": {
        "texto": "{nombre} regresa con algo entre los dientes: restos de comida encontrados cerca.",
        "efecto": {"comida": 8},
    },
    "protege_nino": {
        "texto": "{nombre} interpuso su cuerpo entre un peligro menor y los más jóvenes. Sin heridos.",
        "efecto": {"moral": 5},
    },
    "herido": {
        "texto": "{nombre} tiene una herida. Necesita cuidados o perderá salud rápidamente.",
        "efecto": {"salud_animal": -20},
    },
    "se_enferma": {
        "texto": "{nombre} no come bien y tiene fiebre. Puede contagiar si no se trata.",
        "efecto": {"salud_animal": -15, "hambre_animal": 10},
    },
    "cria": {
        "texto": "{nombre} ha dado a luz. Hay crías en el refugio.",
        "efecto": {"nueva_cria": True},
    },
    "caza_exitosa": {
        "texto": "{nombre} volvió con una presa pequeña. Proteínas extra para hoy.",
        "efecto": {"comida": 6},
    },
    "desaparece_vuelve": {
        "texto": "{nombre} desapareció dos días. Volvió delgado pero vivo.",
        "efecto": {"moral": 2},
    },
    "pone_huevo": {
        "texto": "{nombre} puso huevos extra hoy.",
        "efecto": {"comida": 5},
    },
    "depredador": {
        "texto": "Algo atacó a {nombre} durante la noche. Señales de lucha pero sobrevivió.",
        "efecto": {"salud_animal": -25},
    },
    "produce_leche": {
        "texto": "{nombre} produjo leche abundante hoy.",
        "efecto": {"comida": 8, "agua": 4},
    },
    "huye_asustada": {
        "texto": "{nombre} huyó asustado por un ruido fuerte. Tardó horas en volver.",
        "efecto": {"moral": -2},
    },
}

# Nombres posibles para animales (mascota → más afecto, generic → más neutro)
NOMBRES_ANIMALES: dict[str, list[str]] = {
    "perro":   ["Rex", "Luna", "Thor", "Sombra", "Parche", "Lobo", "Rayo", "Nube"],
    "gato":    ["Michi", "Sombra", "Gris", "Ceniza", "Noche", "Polvo", "Niebla"],
    "gallina": ["Pinta", "Rubia", "Negra", "Moñuda", "Clara", "Pela"],
    "cabra":   ["Blanca", "Terca", "Manchas", "Vieja", "Cornuda"],
    "conejo":  ["Pelusa", "Rápido", "Gris", "Blanco", "Manchado"],
}
