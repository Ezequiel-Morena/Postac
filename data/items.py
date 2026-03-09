# ============================================================
# data/items.py
# Catálogo completo de ítems del mundo.
#
# Para agregar un ítem nuevo:
#   1. Añadir una entrada al diccionario ITEMS
#   2. Opcionalmente añadir su clave a data/loot.py
#   Nada más.
#
# Tipos válidos de ítem:
#   medicina | medicina_fuerte | comida | agua | agua_sucia
#   arma_contundente | arma_cortante | arma_fuego | arma_arrojadiza
#   municion | armadura | casco | equipo | equipo_especial
#   herramienta | herramienta_medica | material | material_especial
#   combustible | libro | mapa | especial
# ============================================================

ITEMS = {

    # ══════════════════════════════════════════════════════════
    #  MEDICINA
    # ══════════════════════════════════════════════════════════
    "venda": {
        "nombre": "Venda",
        "tipo":   "medicina",
        "peso":    0.1,
        "usos":    1,
        "efectos": {"salud": 8},
        "desc":    "Detiene hemorragias menores. Esencial en el kit básico.",
    },
    "botiquin": {
        "nombre": "Botiquín básico",
        "tipo":   "medicina",
        "peso":    0.5,
        "usos":    3,
        "efectos": {"salud": 20},
        "desc":    "Vendas, antiséptico y analgésicos. El estándar mínimo de supervivencia.",
    },
    "antibiotico": {
        "nombre": "Antibióticos",
        "tipo":   "medicina",
        "peso":    0.1,
        "usos":    4,
        "efectos": {"condicion_remove": "infeccion"},
        "desc":    "Combaten infecciones bacterianas. No sirven para virus.",
    },
    "morfina": {
        "nombre": "Morfina",
        "tipo":   "medicina_fuerte",
        "peso":    0.1,
        "usos":    2,
        "efectos": {"salud": 40, "fatiga": -20},
        "riesgo":  "adiccion_morfina_acum",
        "desc":    "Analgésico potente. Funciona, pero el cuerpo la recuerda.",
    },
    "antiseptico": {
        "nombre": "Antiséptico",
        "tipo":   "medicina",
        "peso":    0.2,
        "usos":    3,
        "efectos": {"condicion_prevent": "infeccion"},
        "desc":    "Previene infecciones al limpiar heridas abiertas.",
    },
    "sutura": {
        "nombre": "Kit de sutura",
        "tipo":   "medicina",
        "peso":    0.2,
        "usos":    2,
        "efectos": {"salud": 30, "condicion_remove": "hemorragia"},
        "skill_req": {"medicina": 30},
        "desc":    "Para heridas profundas. Requiere pulso firme.",
    },
    "yodo": {
        "nombre": "Yodo medicinal",
        "tipo":   "medicina",
        "peso":    0.1,
        "usos":    5,
        "efectos": {"condicion_prevent": "infeccion", "radiacion": -5},
        "desc":    "Antiséptico y algo de protección contra radiación.",
    },
    "pastilla_purificadora": {
        "nombre": "Pastillas purificadoras",
        "tipo":   "herramienta",
        "peso":    0.05,
        "usos":   10,
        "efectos": {"purifica_agua": True},
        "desc":    "Convierte agua contaminada en agua potable.",
    },

    # ── LIBROS DE HABILIDAD ───────────────────────────────────
    "cuaderno_medico": {
        "nombre": "Cuaderno médico",
        "tipo":   "libro",
        "peso":    0.2,
        "usos":    1,
        "efectos": {"skill_xp": {"medicina": 8}},
        "desc":    "Notas de campo de un médico. +8 Medicina al leerlo.",
    },
    "manual_mecanica": {
        "nombre": "Manual de mecánica",
        "tipo":   "libro",
        "peso":    0.3,
        "usos":    1,
        "efectos": {"skill_xp": {"mecanica": 8}},
        "desc":    "Manual técnico de reparación. +8 Mecánica.",
    },
    "guia_supervivencia": {
        "nombre": "Guía de supervivencia",
        "tipo":   "libro",
        "peso":    0.2,
        "usos":    1,
        "efectos": {"skill_xp": {"supervivencia": 8}},
        "desc":    "Técnicas de forrajeo y orientación. +8 Supervivencia.",
    },
    "tratado_combate": {
        "nombre": "Tratado de combate",
        "tipo":   "libro",
        "peso":    0.2,
        "usos":    1,
        "efectos": {"skill_xp": {"combate_cac": 8}},
        "desc":    "Tácticas militares básicas. +8 Combate CAC.",
    },
    "cuaderno_notas": {
        "nombre": "Cuaderno de notas",
        "tipo":   "especial",
        "peso":    0.3,
        "desc":    "Tus apuntes del colapso. Podría ser valioso para otros.",
    },

    # ══════════════════════════════════════════════════════════
    #  COMIDA
    # ══════════════════════════════════════════════════════════
    "lata_frijoles": {
        "nombre":   "Lata de frijoles",
        "tipo":     "comida",
        "peso":      0.4,
        "efectos":  {"hambre": -35},
        "desc":     "Frijoles enlatados. No es gourmet, pero alimenta.",
    },
    "lata_atun": {
        "nombre":   "Lata de atún",
        "tipo":     "comida",
        "peso":      0.3,
        "efectos":  {"hambre": -30},
        "desc":     "Alto en proteínas. Sabor tolerable.",
    },
    "lata_sopa": {
        "nombre":   "Lata de sopa",
        "tipo":     "comida",
        "peso":      0.4,
        "efectos":  {"hambre": -25, "sed": -10},
        "desc":     "Mejor caliente, pero funciona fría también.",
    },
    "barritas_energia": {
        "nombre":   "Barrita energética",
        "tipo":     "comida",
        "peso":      0.1,
        "efectos":  {"hambre": -20, "fatiga": -15},
        "desc":     "Compacta y calórica. Ideal para llevar en expedición.",
    },
    "comida_militar": {
        "nombre":   "Ración militar (MRE)",
        "tipo":     "comida",
        "peso":      0.8,
        "efectos":  {"hambre": -60, "fatiga": -10},
        "desc":     "Ración completa de combate. Dura décadas sin abrir.",
    },
    "frutos_silvestres": {
        "nombre":   "Frutos silvestres",
        "tipo":     "comida",
        "peso":      0.2,
        "efectos":  {"hambre": -15},
        "riesgo":   "envenenamiento_10",
        "desc":     "Algunos son venenosos. 10% de probabilidad de intoxicación.",
    },
    "carne_ahumada": {
        "nombre":   "Carne ahumada",
        "tipo":     "comida",
        "peso":      0.5,
        "efectos":  {"hambre": -45},
        "desc":     "Bien conservada mediante ahumado.",
    },
    "semillas": {
        "nombre":   "Semillas variadas",
        "tipo":     "material_especial",
        "peso":      0.1,
        "desc":     "Podrían cultivarse en un refugio con tierra y agua.",
    },

    # ══════════════════════════════════════════════════════════
    #  AGUA
    # ══════════════════════════════════════════════════════════
    "botella_agua": {
        "nombre":   "Botella de agua",
        "tipo":     "agua",
        "peso":      0.5,
        "efectos":  {"sed": -40},
        "desc":     "500ml de agua purificada.",
    },
    "garrafa_agua": {
        "nombre":   "Garrafa de agua",
        "tipo":     "agua",
        "peso":      2.0,
        "efectos":  {"sed": -100},
        "desc":     "5 litros. Pesada, pero valen la pena.",
    },
    "agua_contaminada": {
        "nombre":   "Agua contaminada",
        "tipo":     "agua_sucia",
        "peso":      0.5,
        "efectos":  {"sed": -30},
        "riesgo":   "enfermedad_50",
        "desc":     "Parece agua. Probablemente no lo sea.",
    },
    "filtro_agua": {
        "nombre":   "Filtro de agua portátil",
        "tipo":     "herramienta",
        "peso":      0.3,
        "usos":     20,
        "efectos":  {"purifica_agua": True},
        "desc":     "Purifica agua contaminada. 20 usos.",
    },

    # ══════════════════════════════════════════════════════════
    #  ARMAS
    # ══════════════════════════════════════════════════════════
    "pipa_metal": {
        "nombre":      "Pipa de metal",
        "tipo":        "arma_contundente",
        "peso":         1.2,
        "daño":        (3, 7),
        "durabilidad": 40,
        "desc":        "Improvisada pero efectiva.",
    },
    "bate_beisbol": {
        "nombre":      "Bate de béisbol",
        "tipo":        "arma_contundente",
        "peso":         0.9,
        "daño":        (5, 10),
        "durabilidad": 60,
        "desc":        "Resistente. El post-apocalipsis necesita sus clásicos.",
    },
    "llave_inglesa": {
        "nombre":      "Llave inglesa",
        "tipo":        "arma_contundente",
        "peso":         0.8,
        "daño":        (4, 8),
        "durabilidad": 80,
        "desc":        "Herramienta y arma. Doble utilidad.",
    },
    "cuchillo": {
        "nombre":      "Cuchillo",
        "tipo":        "arma_cortante",
        "peso":         0.2,
        "daño":        (4, 8),
        "durabilidad": 50,
        "silencioso":  True,
        "desc":        "Versátil y silencioso. El arma definitiva del superviviente.",
    },
    "cuchillo_tactico": {
        "nombre":      "Cuchillo táctico",
        "tipo":        "arma_cortante",
        "peso":         0.3,
        "daño":        (5, 10),
        "durabilidad": 70,
        "silencioso":  True,
        "desc":        "Hoja de acero de 20cm. Confiable y silenciosa.",
    },
    "navaja": {
        "nombre":      "Navaja plegable",
        "tipo":        "arma_cortante",
        "peso":         0.1,
        "daño":        (3, 6),
        "durabilidad": 40,
        "silencioso":  True,
        "desc":        "Pequeña, discreta. Fácil de ocultar.",
    },
    "machete": {
        "nombre":      "Machete",
        "tipo":        "arma_cortante",
        "peso":         0.6,
        "daño":        (6, 12),
        "durabilidad": 65,
        "silencioso":  True,
        "desc":        "Corta vegetación y todo lo demás.",
    },
    "hacha": {
        "nombre":      "Hacha de mano",
        "tipo":        "arma_cortante",
        "peso":         1.5,
        "daño":        (7, 14),
        "durabilidad": 55,
        "desc":        "Letal. También corta madera.",
    },
    "lanza_improvisada": {
        "nombre":      "Lanza improvisada",
        "tipo":        "arma_cortante",
        "peso":         1.0,
        "daño":        (5, 11),
        "durabilidad": 30,
        "desc":        "Palo con cuchillo atado. Alcance medio.",
    },
    "pistola_9mm": {
        "nombre":      "Pistola 9mm",
        "tipo":        "arma_fuego",
        "peso":         0.8,
        "daño":        (15, 25),
        "durabilidad": 80,
        "municion_tipo": "balas_9mm",
        "cargador":     12,
        "ruidosa":      True,
        "desc":        "Confiable y precisa. El ruido atrae infectados.",
    },
    "escopeta": {
        "nombre":      "Escopeta recortada",
        "tipo":        "arma_fuego",
        "peso":         2.5,
        "daño":        (25, 45),
        "durabilidad": 70,
        "municion_tipo": "cartuchos_escopeta",
        "cargador":      4,
        "ruidosa":       True,
        "desc":        "Devastadora a corta distancia. Muy ruidosa.",
    },
    "molotov": {
        "nombre":      "Cóctel Molotov",
        "tipo":        "arma_arrojadiza",
        "peso":         0.5,
        "daño":        (20, 40),
        "area":         True,
        "cantidad":     1,
        "desc":        "Daño en área. Úsalo lejos de donde estás.",
    },

    # ══════════════════════════════════════════════════════════
    #  MUNICIÓN
    # ══════════════════════════════════════════════════════════
    "balas_9mm": {
        "nombre":   "Balas 9mm",
        "tipo":     "municion",
        "peso":      0.2,
        "cantidad":  15,
        "para":      "pistola_9mm",
        "desc":     "Munición estándar para pistola 9mm.",
    },
    "cartuchos_escopeta": {
        "nombre":   "Cartuchos escopeta",
        "tipo":     "municion",
        "peso":      0.4,
        "cantidad":  8,
        "para":      "escopeta",
        "desc":     "Para escopeta de 12 calibres.",
    },

    # ══════════════════════════════════════════════════════════
    #  ARMADURA / EQUIPO
    # ══════════════════════════════════════════════════════════
    "chaleco_cuero": {
        "nombre":   "Chaleco de cuero",
        "tipo":     "armadura",
        "peso":      1.5,
        "defensa":   2,
        "slot":     "torso",
        "desc":     "Protección básica contra cortes y rozaduras.",
    },
    "chaleco_tactico": {
        "nombre":   "Chaqueta táctica",
        "tipo":     "armadura",
        "peso":      2.0,
        "defensa":   4,
        "slot":     "torso",
        "bonus":    {"carga_max": 2},
        "desc":     "Buena protección. Los bolsillos extra ayudan.",
    },
    "casco_moto": {
        "nombre":   "Casco de moto",
        "tipo":     "casco",
        "peso":      1.2,
        "defensa":   3,
        "slot":     "cabeza",
        "desc":     "Protege la cabeza de golpes y mordidas.",
    },
    "mascarilla": {
        "nombre":   "Mascarilla N95",
        "tipo":     "equipo",
        "peso":      0.1,
        "usos":     10,
        "efectos":  {"proteccion_radiacion": 0.5, "proteccion_gas": 0.5},
        "desc":     "Reduce la exposición a contaminantes en un 50%.",
    },
    "linterna": {
        "nombre":   "Linterna",
        "tipo":     "equipo",
        "peso":      0.3,
        "usos":     30,
        "bonus":    {"percepcion": 2},
        "desc":     "+2 Percepción en ambientes oscuros.",
    },
    "mochila_tactica": {
        "nombre":   "Mochila táctica",
        "tipo":     "equipo_especial",
        "peso":      0.8,
        "bonus":    {"carga_max": 10},
        "desc":     "+10 kg de capacidad de carga.",
    },

    # ══════════════════════════════════════════════════════════
    #  HERRAMIENTAS
    # ══════════════════════════════════════════════════════════
    "palanca": {
        "nombre":   "Palanca",
        "tipo":     "herramienta",
        "peso":      1.5,
        "usos":     20,
        "efectos":  {"fuerza_puertas": True},
        "desc":     "Abre puertas y cajones sin hacer demasiado ruido.",
    },
    "cuerda": {
        "nombre":   "Cuerda (10m)",
        "tipo":     "material",
        "peso":      0.8,
        "desc":     "Múltiples usos: escalar, atar, trampas de caza.",
    },
    "encendedor": {
        "nombre":   "Encendedor",
        "tipo":     "herramienta",
        "peso":      0.05,
        "usos":     15,
        "efectos":  {"genera_fuego": True},
        "desc":     "Fuego cuando más lo necesitas.",
    },
    "radio_comunicacion": {
        "nombre":   "Walkie-talkie",
        "tipo":     "equipo_especial",
        "peso":      0.4,
        "efectos":  {"escuchar_frecuencias": True},
        "desc":     "Permite escuchar frecuencias. A veces hay sobrevivientes.",
    },
    "brujula": {
        "nombre":   "Brújula",
        "tipo":     "herramienta",
        "peso":      0.05,
        "efectos":  {"no_perderse": True},
        "desc":     "No te pierdes en áreas desconocidas.",
    },
    "ganzuas": {
        "nombre":   "Ganzúas",
        "tipo":     "herramienta",
        "peso":      0.1,
        "usos":     10,
        "efectos":  {"abrir_cerraduras": True},
        "skill_req": {"sigilo": 20},
        "desc":     "Abren la mayoría de cerraduras sin hacer ruido.",
    },
    "kit_herramientas": {
        "nombre":   "Kit de herramientas",
        "tipo":     "herramienta",
        "peso":      1.5,
        "usos":      5,
        "efectos":  {"forzar_cerraduras": True, "reparar": True},
        "desc":     "Para reparar objetos y forzar cerraduras simples.",
    },
    "cinta_aislante": {
        "nombre":   "Cinta aislante",
        "tipo":     "material",
        "peso":      0.1,
        "cantidad":  2,
        "desc":     "Material de reparación esencial. Mantiene unido lo roto.",
    },

    # ══════════════════════════════════════════════════════════
    #  MATERIALES
    # ══════════════════════════════════════════════════════════
    "chatarra_metal": {
        "nombre":   "Chatarra metálica",
        "tipo":     "material",
        "peso":      0.5,
        "cantidad":  1,
        "desc":     "Para fabricar armas improvisadas y refuerzos.",
    },
    "madera": {
        "nombre":   "Madera",
        "tipo":     "material",
        "peso":      1.0,
        "cantidad":  1,
        "desc":     "Construcción y combustible.",
    },
    "trapos": {
        "nombre":   "Tiras de tela",
        "tipo":     "material",
        "peso":      0.1,
        "cantidad":  1,
        "desc":     "Vendas improvisadas. +3 Salud si se usan como medicina básica.",
    },
    "alcohol_industrial": {
        "nombre":   "Alcohol industrial",
        "tipo":     "material_especial",
        "peso":      0.5,
        "desc":     "Antiséptico, combustible o componente de Molotov.",
    },
    "pilas": {
        "nombre":   "Pilas AA",
        "tipo":     "material",
        "peso":      0.1,
        "cantidad":  4,
        "desc":     "Para linternas y equipos electrónicos.",
    },
    "gasolina": {
        "nombre":   "Gasolina (1L)",
        "tipo":     "combustible",
        "peso":      0.8,
        "desc":     "Combustible. Altamente inflamable.",
    },
    "cable_electrico": {
        "nombre":   "Cable eléctrico",
        "tipo":     "material",
        "peso":      0.3,
        "desc":     "Para fabricar trampas eléctricas o reparaciones.",
    },

    # ══════════════════════════════════════════════════════════
    #  MAPAS / ESPECIALES
    # ══════════════════════════════════════════════════════════
    "mapa_zona": {
        "nombre":   "Mapa de zona",
        "tipo":     "mapa",
        "peso":      0.05,
        "efectos":  {"revela_area": True},
        "desc":     "Revela puntos de interés en el área.",
    },
    "plano_edificio": {
        "nombre":   "Planos de edificio",
        "tipo":     "mapa",
        "peso":      0.05,
        "efectos":  {"revela_salidas": True},
        "desc":     "Muestra salidas de emergencia y zonas de almacén.",
    },
    "diario_sobreviviente": {
        "nombre":   "Diario de sobreviviente",
        "tipo":     "especial",
        "peso":      0.2,
        "efectos":  {"info_zona": True},
        "desc":     "Contiene rutas y advertencias de otro superviviente.",
    },

    # ── EJEMPLO: cómo agregar un ítem nuevo ───────────────────
    # "arco_improvisado": {
    #     "nombre":      "Arco improvisado",
    #     "tipo":        "arma_distancia",
    #     "peso":         1.2,
    #     "daño":        (8, 16),
    #     "durabilidad":  35,
    #     "silencioso":   True,
    #     "municion_tipo": "flechas",
    #     "cargador":      1,
    #     "desc":        "Silencioso y reutilizable. Difícil de fabricar.",
    # },
}
