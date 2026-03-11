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
#   combustible | libro | mapa | especial | vestimenta
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
        "farmacologia": {
            "principio_activo": "antisepsia_local",
            "clase": "topico",
            "dosis": 0.4,
            "dosis_toxica": 3.5,
            "ventana_horas": 2,
            "contraindicaciones": [],
            "no_combinar_con": [],
        },
        "desc":    "Detiene hemorragias menores. Esencial en el kit básico.",
    },
    "botiquin": {
        "nombre": "Botiquín básico",
        "tipo":   "medicina",
        "peso":    0.5,
        "usos":    3,
        "efectos": {"salud": 20},
        "farmacologia": {
            "principio_activo": "analgesico_generico",
            "clase": "analgesico",
            "dosis": 1.0,
            "dosis_toxica": 2.4,
            "ventana_horas": 6,
            "contraindicaciones": ["deshidratacion"],
            "no_combinar_con": ["opioide"],
        },
        "desc":    "Vendas, antiséptico y analgésicos. El estándar mínimo de supervivencia.",
    },
    "antibiotico": {
        "nombre": "Antibióticos",
        "tipo":   "medicina",
        "peso":    0.1,
        "usos":    4,
        "efectos": {"condicion_remove": "infeccion"},
        "farmacologia": {
            "principio_activo": "amoxicilina",
            "clase": "antibiotico",
            "dosis": 1.0,
            "dosis_toxica": 2.6,
            "ventana_horas": 8,
            "contraindicaciones": ["hambre_critica"],
            "no_combinar_con": ["opioide"],
        },
        "desc":    "Combaten infecciones bacterianas. No sirven para virus.",
    },
    "morfina": {
        "nombre": "Morfina",
        "tipo":   "medicina_fuerte",
        "peso":    0.1,
        "usos":    2,
        "efectos": {"salud": 40, "fatiga": -20},
        "riesgo":  "adiccion_morfina_acum",
        "farmacologia": {
            "principio_activo": "morfina",
            "clase": "opioide",
            "dosis": 1.4,
            "dosis_toxica": 2.1,
            "ventana_horas": 10,
            "contraindicaciones": ["deshidratacion", "radiacion_alta"],
            "no_combinar_con": ["analgesico", "sedante"],
        },
        "desc":    "Analgésico potente. Funciona, pero el cuerpo la recuerda.",
    },
    "antiseptico": {
        "nombre": "Antiséptico",
        "tipo":   "medicina",
        "peso":    0.2,
        "usos":    3,
        "efectos": {"condicion_prevent": "infeccion"},
        "farmacologia": {
            "principio_activo": "clorhexidina",
            "clase": "topico",
            "dosis": 0.5,
            "dosis_toxica": 4.0,
            "ventana_horas": 2,
            "contraindicaciones": [],
            "no_combinar_con": [],
        },
        "desc":    "Previene infecciones al limpiar heridas abiertas.",
    },
    "sutura": {
        "nombre": "Kit de sutura",
        "tipo":   "medicina",
        "peso":    0.2,
        "usos":    2,
        "efectos": {"salud": 30, "condicion_remove": "hemorragia"},
        "skill_req": {"medicina": 30},
        "farmacologia": {
            "principio_activo": "lidocaina_local",
            "clase": "analgesico",
            "dosis": 0.8,
            "dosis_toxica": 2.2,
            "ventana_horas": 5,
            "contraindicaciones": ["deshidratacion"],
            "no_combinar_con": ["opioide"],
        },
        "desc":    "Para heridas profundas. Requiere pulso firme.",
    },
    "yodo": {
        "nombre": "Yodo medicinal",
        "tipo":   "medicina",
        "peso":    0.1,
        "usos":    5,
        "efectos": {"condicion_prevent": "infeccion", "radiacion": -5},
        "farmacologia": {
            "principio_activo": "yoduro",
            "clase": "protector_radiologico",
            "dosis": 0.7,
            "dosis_toxica": 2.8,
            "ventana_horas": 6,
            "contraindicaciones": [],
            "no_combinar_con": [],
        },
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
    "racion_deshidratada": {
        "nombre":   "Ración deshidratada",
        "tipo":     "comida",
        "peso":      0.25,
        "efectos":  {"hambre": -28, "sed": 8},
        "desc":     "Liviana y estable por años; da energía pero exige hidratarse luego.",
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
    "manta_termica": {
        "nombre":   "Manta térmica",
        "tipo":     "equipo",
        "peso":      0.2,
        "usos":      6,
        "efectos":  {"fatiga": -8, "moral": 3},
        "desc":     "Reduce pérdida de calor y mejora descanso en clima hostil.",
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
    "detector_radiacion": {
        "nombre":   "Detector Geiger",
        "tipo":     "herramienta",
        "peso":      0.4,
        "usos":     30,
        "efectos":  {"alerta_radiacion": True},
        "desc":     "Permite anticipar zonas con radiación peligrosa.",
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
    "filtro_hepa": {
        "nombre":   "Filtro HEPA",
        "tipo":     "material_especial",
        "peso":      0.3,
        "cantidad":  1,
        "desc":     "Componente para mejorar purificación de aire/agua en refugio.",
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

    # ══════════════════════════════════════════════════════════
    #  NUEVOS ÍTEMS MÉDICOS Y DE PROTECCIÓN AMBIENTAL
    # ══════════════════════════════════════════════════════════

    "pastillas_yodo": {
        "nombre": "Pastillas de yodo",
        "tipo":   "medicina",
        "peso":    0.05,
        "usos":    6,
        "efectos": {"radiacion": -15},
        "farmacologia": {
            "principio_activo": "yoduro_potasico",
            "clase": "radioprotector",
            "dosis": 0.8,
            "dosis_toxica": 4.0,
            "ventana_horas": 24,
            "contraindicaciones": ["hipertiroidismo"],
            "no_combinar_con": [],
        },
        "desc": "Bloquean la absorción de yodo radiactivo por la tiroides. Uso preventivo.",
    },
    "antidoto_universal": {
        "nombre": "Antídoto universal",
        "tipo":   "medicina_fuerte",
        "peso":    0.15,
        "usos":    1,
        "efectos": {"condicion_remove": "envenenamiento_quimico", "salud": 10},
        "farmacologia": {
            "principio_activo": "carbono_activado",
            "clase": "antidoto",
            "dosis": 1.2,
            "dosis_toxica": 3.0,
            "ventana_horas": 4,
            "contraindicaciones": [],
            "no_combinar_con": [],
        },
        "desc": "Absorbe toxinas activas. Eficaz solo si se administra rápido.",
    },
    "purgante_medico": {
        "nombre": "Purgante médico",
        "tipo":   "medicina",
        "peso":    0.1,
        "usos":    2,
        "efectos": {"condicion_remove": "intoxicacion_alimentaria", "salud": 5, "sed": 8},
        "farmacologia": {
            "principio_activo": "bisacodilo",
            "clase": "purgante",
            "dosis": 0.9,
            "dosis_toxica": 2.5,
            "ventana_horas": 6,
            "contraindicaciones": ["deshidratacion"],
            "no_combinar_con": ["opioide"],
        },
        "desc": "Elimina toxinas digestivas. Provoca deshidratación: beber agua después.",
    },
    "mascara_gas": {
        "nombre": "Máscara de gas",
        "tipo":   "equipo_especial",
        "peso":    0.8,
        "usos":   -1,
        "efectos": {"proteccion_quimica": True},
        "durabilidad": 70,
        "desc": "Filtra partículas químicas y polvo tóxico. Esencial en zonas contaminadas.",
    },
    "suero_rehidratacion": {
        "nombre": "Suero de rehidratación",
        "tipo":   "medicina",
        "peso":    0.3,
        "usos":    2,
        "efectos": {"sed": -35, "salud": 6},
        "farmacologia": {
            "principio_activo": "electrolitos_orales",
            "clase": "rehidratante",
            "dosis": 0.6,
            "dosis_toxica": 5.0,
            "ventana_horas": 3,
            "contraindicaciones": [],
            "no_combinar_con": [],
        },
        "desc": "Rehidratación rápida con electrolitos. Más efectivo que agua sola.",
    },
    "vitaminas_c": {
        "nombre": "Vitamina C (comprimidos)",
        "tipo":   "medicina",
        "peso":    0.05,
        "usos":    8,
        "efectos": {"salud": 3, "moral": 2},
        "farmacologia": {
            "principio_activo": "acido_ascorbico",
            "clase": "vitamina",
            "dosis": 0.3,
            "dosis_toxica": 6.0,
            "ventana_horas": 12,
            "contraindicaciones": [],
            "no_combinar_con": [],
        },
        "desc": "Refuerza el sistema inmune y sube el ánimo levemente. Útil en periodos largos.",
    },
    "calmante_nervioso": {
        "nombre": "Calmante nervioso",
        "tipo":   "medicina",
        "peso":    0.08,
        "usos":    3,
        "efectos": {"moral": 20, "fatiga": 10},
        "farmacologia": {
            "principio_activo": "diazepam",
            "clase": "sedante",
            "dosis": 1.0,
            "dosis_toxica": 2.2,
            "ventana_horas": 8,
            "contraindicaciones": ["radiacion_alta"],
            "no_combinar_con": ["opioide", "analgesico"],
        },
        "desc": "Reduce la ansiedad y el pánico. La mente también puede romperse.",
    },
    "linimento_muscular": {
        "nombre": "Linimento muscular",
        "tipo":   "medicina",
        "peso":    0.2,
        "usos":    4,
        "efectos": {"fatiga": -15},
        "farmacologia": {
            "principio_activo": "salicilato_metilo",
            "clase": "topico",
            "dosis": 0.4,
            "dosis_toxica": 3.5,
            "ventana_horas": 4,
            "contraindicaciones": [],
            "no_combinar_con": [],
        },
        "desc": "Alivia contracturas y dolor muscular. Básico tras jornadas largas.",
    },
    "agua_contaminada": {
        "nombre": "Agua contaminada",
        "tipo":   "agua_sucia",
        "peso":    0.5,
        "usos":    1,
        "efectos": {"sed": -20, "condicion_riesgo": "intoxicacion_alimentaria", "prob_condicion": 0.25},
        "desc": "Sacias la sed, pero las bacterias cobran su precio. Purificar antes de beber.",
    },
    "racion_militar": {
        "nombre": "Ración militar (MRE)",
        "tipo":   "comida",
        "peso":    0.6,
        "usos":    1,
        "efectos": {"hambre": -55, "moral": 5},
        "desc": "Comida calórica y estable. Diseñada para situaciones de combate sostenido.",
    },
    "carne_cruda": {
        "nombre": "Carne cruda",
        "tipo":   "comida",
        "peso":    0.4,
        "usos":    1,
        "efectos": {"hambre": -30, "condicion_riesgo": "intoxicacion_alimentaria", "prob_condicion": 0.35},
        "desc": "Proteínas, sí. Pero sin cocinar, el riesgo de infección es real.",
    },

    # ── HERRAMIENTAS DE PESCA Y CAZA ──────────────────────────
    "cana_pesca": {
        "nombre": "Caña de pesca improvisada",
        "tipo": "herramienta",
        "peso": 0.8,
        "usos": 15,
        "durabilidad_max": 15,
        "desc": "Ramas y hilo resistente. Funciona si sabes usarla.",
    },
    "trampa_caza": {
        "nombre": "Trampa de lazo",
        "tipo": "herramienta",
        "peso": 0.3,
        "usos": 20,
        "durabilidad_max": 20,
        "desc": "Lazo de alambre. Lo que pasa por ahí, no sale.",
    },
    "pedernal": {
        "nombre": "Pedernal y acero",
        "tipo": "herramienta",
        "peso": 0.15,
        "usos": 50,
        "durabilidad_max": 50,
        "desc": "El método más antiguo de encender fuego. Lento pero inagotable.",
    },
    "olla_campo": {
        "nombre": "Olla de campo",
        "tipo": "herramienta",
        "peso": 0.9,
        "usos": 100,
        "durabilidad_max": 100,
        "desc": "Imprescindible para hervir agua y hacer caldos.",
    },

    # ── COMBUSTIBLES ──────────────────────────────────────────
    "lena": {
        "nombre": "Leña seca",
        "tipo": "combustible",
        "peso": 1.0,
        "valor_calorico": 40,
        "desc": "Madera seca lista para quemar. Dura más que la madera húmeda.",
    },
    "carbon_vegetal": {
        "nombre": "Carbón vegetal",
        "tipo": "combustible",
        "peso": 0.5,
        "valor_calorico": 70,
        "desc": "Más eficiente que la leña. Menos humo, más calor.",
    },

    # ── ALIMENTOS CRUDOS (PESCA / CAZA) ───────────────────────
    "pez_pequeno": {
        "nombre": "Pez pequeño",
        "tipo": "comida",
        "peso": 0.15,
        "efectos": {"hambre": 12, "posible_parasitos": True},
        "desc": "Crudo tiene parásitos. Hay que cocinarlo.",
        "crudo": True,
    },
    "pez_mediano": {
        "nombre": "Pez mediano",
        "tipo": "comida",
        "peso": 0.35,
        "efectos": {"hambre": 22, "posible_parasitos": True},
        "desc": "Buen tamaño. Cocinado, alimenta bien.",
        "crudo": True,
    },
    "carne_animal_cruda": {
        "nombre": "Carne de animal",
        "tipo": "comida",
        "peso": 0.5,
        "efectos": {"hambre": 30, "posible_parasitos": True},
        "desc": "Carne de caza. Sin cocinar es un riesgo.",
        "crudo": True,
    },
    "piel_animal": {
        "nombre": "Piel de animal",
        "tipo": "material",
        "peso": 0.4,
        "desc": "Puede curtirse para hacer ropa o cuero.",
    },

    # ── ALIMENTOS COCINADOS ───────────────────────────────────
    "pez_cocido": {
        "nombre": "Pez cocido",
        "tipo": "comida",
        "peso": 0.2,
        "efectos": {"hambre": 28},
        "desc": "El fuego mata los parásitos. Mucho más seguro.",
    },
    "carne_asada": {
        "nombre": "Carne asada",
        "tipo": "comida",
        "peso": 0.45,
        "efectos": {"hambre": 45},
        "desc": "Proteína de alta calidad. Vale la leña que costó.",
    },
    "agua_hervida": {
        "nombre": "Agua hervida",
        "tipo": "agua",
        "peso": 0.5,
        "efectos": {"sed": 60},
        "desc": "El fuego mata bacterias. No elimina metales pesados.",
    },
    "caldo_huesos": {
        "nombre": "Caldo de huesos",
        "tipo": "comida",
        "peso": 0.4,
        "efectos": {"hambre": 20, "salud": 5},
        "desc": "Reconstituyente. Huesos hervidos durante horas.",
    },

    # ── SEMILLAS Y PLANTAS ────────────────────────────────────
    "semillas_tomate": {
        "nombre": "Semillas de tomate",
        "tipo": "material_especial",
        "peso": 0.05,
        "ciclo_dias": 30,
        "rendimiento": 8,
        "desc": "30 días para cosechar. Necesita agua regular.",
    },
    "semillas_papa": {
        "nombre": "Semillas de papa",
        "tipo": "material_especial",
        "peso": 0.1,
        "ciclo_dias": 60,
        "rendimiento": 12,
        "desc": "Alta densidad calórica. Resiste mejor el frío.",
    },
    "hierba_medicinal": {
        "nombre": "Hierba medicinal",
        "tipo": "medicina",
        "peso": 0.1,
        "usos": 2,
        "efectos": {"salud": 6, "condicion_prevent": "infeccion_leve"},
        "desc": "Propiedades antisépticas. No reemplaza antibióticos.",
    },
    "hongo_comestible": {
        "nombre": "Hongo comestible",
        "tipo": "comida",
        "peso": 0.1,
        "efectos": {"hambre": 10},
        "desc": "Alta proteína. Identificarlos correctamente salva la vida.",
    },

    # ── ÍTEMS DE CRAFTEO AVANZADO ─────────────────────────────
    "explosivo_casero": {
        "nombre":   "Explosivo casero",
        "tipo":     "arma_arrojadiza",
        "peso":      0.8,
        "daño":     (30, 55),
        "area":      True,
        "cantidad":  1,
        "desc":     "Inestable y potente. Manéjalo con extremo cuidado.",
    },
    "chaleco_improvisado": {
        "nombre":   "Chaleco improvisado",
        "tipo":     "armadura",
        "peso":      2.5,
        "defensa":   3,
        "slot":     "torso",
        "desc":     "Cuero y tela reforzados con madera. Protección rudimentaria pero funcional.",
    },
    "senal_fuego": {
        "nombre":   "Señal de fuego",
        "tipo":     "equipo_especial",
        "peso":      1.0,
        "cantidad":  1,
        "efectos":  {"evento_especial": "senal_socorro"},
        "desc":     "Fuego de señalización. Puede atraer ayuda... o amenazas.",
    },
}

# ── Auto-registro de prendas de vestimenta ────────────────────
# Las prendas definidas en data/vestimenta.py se incorporan como
# ítems de tipo "vestimenta" para que participen en loot, crafteo,
# inventario y serialización sin duplicar datos.

from data.vestimenta import PRENDAS as _PRENDAS

for _clave, _prenda in _PRENDAS.items():
    if _clave not in ITEMS:
        ITEMS[_clave] = {
            "nombre":     _prenda["nombre"],
            "tipo":       "vestimenta",
            "peso":       _prenda.get("peso", 0.5),
            "slot":       _prenda["slot"],
            "material":   _prenda.get("material", "algodon"),
            "aislamiento_frio":  _prenda.get("aislamiento_frio", 0),
            "aislamiento_calor": _prenda.get("aislamiento_calor", 0),
            "impermeabilidad":   _prenda.get("impermeabilidad", 0),
            "defensa":    _prenda.get("defensa", 0),
            "radiacion_prot":    _prenda.get("radiacion_prot", 0),
            "durabilidad_max":   _prenda.get("durabilidad_max", 100),
            "desc":       _prenda.get("desc", ""),
        }
