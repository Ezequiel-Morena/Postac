# ============================================================
# data/rasgos.py
# Sistema de Rasgos (Traits/Perks).
#
# Para agregar un rasgo nuevo:
#   1. Añadir una entrada al diccionario RASGOS con su clave única
#   2. Definir los efectos según la categoría que corresponda (ver abajo)
#   3. Definir cuándo se puede adquirir en "adquisicion"
#   Nada más. El engine lo aplicará automáticamente.
#
# ── CATEGORÍAS DE EFECTOS ─────────────────────────────────────
#
#   A — AL ADQUIRIR (se aplican una sola vez en _aplicar_rasgo):
#       "skills": {"nombre_skill": bonus_int}
#       "salud_max": int
#       "carga_max": float
#
#   B — PASIVOS ESCALARES (se consultan con obtener_efecto_rasgo):
#       "daño_cac_mult": float
#       "dificultad_esquive": int
#       "multiplicador_medicina": float
#       "multiplicador_consumo_hambre": float
#       "multiplicador_consumo_sed": float
#       "penalizacion_presion_mult": float
#       "recuperacion_descanso_mult": float
#       "xp_mult_global": float          ← multiplica toda XP ganada
#       "xp_mult_libro": float           ← multiplica XP de libros
#       "bonus_check_experto": int        ← bonus a checks cuando skill > 70
#
#   C — CONTEXTUALES (se consultan con modificador_skill_en_contexto):
#       "skills_en_interior": {"nombre_skill": mod_int}
#       "skills_en_noche":    {"nombre_skill": mod_int}  (futuro)
#
#   D — DEPENDENCIAS (se procesan en tick_dependencias):
#       "dependencia_item": "key_item"
#       "penalizacion_sin_item": {"stats_global": int}
#
#   E — INMUNIDADES (se consultan con tiene_inmunidad):
#       "inmune_envenenamiento_comida": True
#       "inmune_panico": True             (reservado — sistema de pánico futuro)
#
#   F — CAPACIDADES (flags para sistemas futuros):
#       "puede_fabricar": True            (reservado — sistema de fabricación)
# ============================================================

RASGOS = {

    # ══════════════════════════════════════════════════════════
    #  RASGOS POSITIVOS — COMBATE
    # ══════════════════════════════════════════════════════════

    "golpe_brutal": {
        "nombre":      "Golpe Brutal",
        "icono":       "💥",
        "descripcion": "Tus ataques cuerpo a cuerpo hacen un 20% más de daño.",
        "tipo":        "positivo",
        "categoria":   "combate",
        "efectos": {
            "daño_cac_mult": 1.20,                  # Categoría B
        },
        "adquisicion": {
            "tipo":   "acumulacion",
            "skill":  "combate_cac",
            "umbral": 60,
        },
        "incompatible_con": [],
    },

    "mano_firme": {
        "nombre":      "Mano Firme",
        "icono":       "🎯",
        "descripcion": "El temblor no te afecta. +15 a Combate a Distancia.",
        "tipo":        "positivo",
        "categoria":   "combate",
        "efectos": {
            "skills": {"combate_distancia": 15},    # Categoría A
        },
        "adquisicion": {
            "tipo":   "acumulacion",
            "skill":  "combate_distancia",
            "umbral": 50,
        },
        "incompatible_con": [],
    },

    "esquivador": {
        "nombre":      "Esquivador",
        "icono":       "💨",
        "descripcion": "Cuerpo entrenado. La dificultad de esquivar ataques baja en 1.",
        "tipo":        "positivo",
        "categoria":   "combate",
        "efectos": {
            "dificultad_esquive": -1,               # Categoría B
        },
        "adquisicion": {
            "tipo":   "acumulacion",
            "stat":   "destreza",
            "umbral": 8,
        },
        "incompatible_con": [],
    },

    # ══════════════════════════════════════════════════════════
    #  RASGOS POSITIVOS — SUPERVIVENCIA
    # ══════════════════════════════════════════════════════════

    "estomago_de_hierro": {
        "nombre":      "Estómago de Hierro",
        "icono":       "🫀",
        "descripcion": "Puedes comer comida en mal estado sin consecuencias.",
        "tipo":        "positivo",
        "categoria":   "supervivencia",
        "efectos": {
            "inmune_envenenamiento_comida": True,   # Categoría E
        },
        "adquisicion": {
            "tipo":   "acumulacion",
            "skill":  "supervivencia",
            "umbral": 50,
        },
        "incompatible_con": [],
    },

    # ══════════════════════════════════════════════════════════
    #  RASGOS POSITIVOS — CONOCIMIENTO
    # ══════════════════════════════════════════════════════════

    "medico_nato": {
        "nombre":      "Médico Nato",
        "icono":       "🩺",
        "descripcion": "Años de práctica. La medicina surte un 50% más de efecto.",
        "tipo":        "positivo",
        "categoria":   "conocimiento",
        "efectos": {
            "multiplicador_medicina": 1.50,         # Categoría B
        },
        "adquisicion": {
            "tipo":   "acumulacion",
            "skill":  "medicina",
            "umbral": 65,
        },
        "incompatible_con": [],
    },

    "mecanico_improvisado": {
        "nombre":      "Mecánico Improvisado",
        "icono":       "⚙️",
        "descripcion": "Puedes fabricar items básicos con chatarra. +15 Mecánica.",
        "tipo":        "positivo",
        "categoria":   "conocimiento",
        "efectos": {
            "skills":         {"mecanica": 15},     # Categoría A
            "puede_fabricar": True,                  # Categoría F (reservado)
        },
        "adquisicion": {
            "tipo":   "acumulacion",
            "skill":  "mecanica",
            "umbral": 60,
        },
        "incompatible_con": [],
    },

    # ── NUEVOS — SISTEMA DE XP ────────────────────────────────

    "aprendiz_rapido": {
        "nombre":      "Aprendiz Rápido",
        "icono":       "📖",
        "descripcion": "Tu mente absorbe experiencias con facilidad. "
                       "Ganas un 25% más de XP en todas las habilidades.",
        "tipo":        "positivo",
        "categoria":   "conocimiento",
        "efectos": {
            "xp_mult_global": 1.25,                 # Categoría B
        },
        "adquisicion": {
            "tipo":     "acumulacion",
            "contador": "expediciones_completadas",
            "umbral":   15,                         # 15 expediciones sobrevividas
        },
        "incompatible_con": [],
    },

    "memoria_fotografica": {
        "nombre":      "Memoria Fotográfica",
        "icono":       "🧠",
        "descripcion": "Lo que lees se graba. Los libros y manuales te enseñan "
                       "un 50% más.",
        "tipo":        "positivo",
        "categoria":   "conocimiento",
        "efectos": {
            "xp_mult_libro": 1.50,                  # Categoría B
        },
        "adquisicion": {
            "tipo":     "acumulacion",
            "contador": "libros_leidos",
            "umbral":   3,                          # leer 3 libros/manuales
        },
        "incompatible_con": [],
    },

    "especialista": {
        "nombre":      "Especialista",
        "icono":       "🏅",
        "descripcion": "Cuando dominas algo de verdad, los resultados mejoran. "
                       "Los checks de skills por encima de 70 se facilitan.",
        "tipo":        "positivo",
        "categoria":   "combate",
        "efectos": {
            "bonus_check_experto": 8,               # Categoría B (+8 al valor en checks)
        },
        "adquisicion": {
            "tipo":   "acumulacion",
            "skill":  "combate_cac",                # cualquier skill que llegue a 75
            "umbral": 75,
        },
        "incompatible_con": [],
    },

    "curtido": {
        "nombre":      "Curtido",
        "icono":       "🪨",
        "descripcion": "Lo que no te mata te endurece. "
                       "+5 Salud máxima permanente.",
        "tipo":        "positivo",
        "categoria":   "supervivencia",
        "efectos": {
            "salud_max": 5,                         # Categoría A
        },
        "adquisicion": {
            "tipo":     "acumulacion",
            "contador": "veces_condicion_grave",    # condiciones de severidad 3
            "umbral":   3,
        },
        "incompatible_con": [],
    },

    # ── RESISTENCIA TÉRMICA ──────────────────────────────────

    "sangre_fria": {
        "nombre":      "Sangre fría",
        "icono":       "🧊",
        "descripcion": "El frío te afecta menos. Tu cuerpo regula mejor en bajas temperaturas.",
        "tipo":        "positivo",
        "categoria":   "supervivencia",
        "efectos": {
            "resistencia_termica_mult": 0.7,
        },
        "adquisicion": {
            "tipo":     "acumulacion",
            "contador": "horas_bajo_cero",
            "umbral":   48,
        },
        "incompatible_con": ["intolerancia_frio"],
    },
    "piel_curtida_sol": {
        "nombre":      "Piel curtida al sol",
        "icono":       "☀️",
        "descripcion": "Años bajo el sol te dieron tolerancia al calor. Hipertermia menos probable.",
        "tipo":        "positivo",
        "categoria":   "supervivencia",
        "efectos": {
            "resistencia_termica_mult": 0.7,
        },
        "adquisicion": {
            "tipo":     "acumulacion",
            "contador": "horas_calor_extremo",
            "umbral":   48,
        },
        "incompatible_con": ["intolerancia_calor"],
    },
    "intolerancia_frio": {
        "nombre":      "Intolerancia al frío",
        "icono":       "🥶",
        "descripcion": "Tu cuerpo pierde calor rápido. La hipotermia acecha antes.",
        "tipo":        "negativo",
        "categoria":   "supervivencia",
        "efectos": {
            "resistencia_termica_mult": 1.4,
        },
        "adquisicion": {
            "tipo":     "condicion",
            "condicion": "hipotermia",
        },
        "incompatible_con": ["sangre_fria"],
    },
    "intolerancia_calor": {
        "nombre":      "Intolerancia al calor",
        "icono":       "🥵",
        "descripcion": "Sudas en exceso y te deshidratas rápido con calor.",
        "tipo":        "negativo",
        "categoria":   "supervivencia",
        "efectos": {
            "resistencia_termica_mult": 1.4,
        },
        "adquisicion": {
            "tipo":     "condicion",
            "condicion": "hipertermia",
        },
        "incompatible_con": ["piel_curtida_sol"],
    },

    # ══════════════════════════════════════════════════════════
    #  RASGOS POSITIVOS — SOCIAL
    # ══════════════════════════════════════════════════════════

    "cara_de_poker": {
        "nombre":      "Cara de Póker",
        "icono":       "🃏",
        "descripcion": "En negociaciones, tus intenciones son ilegibles. +20 Persuasión.",
        "tipo":        "positivo",
        "categoria":   "social",
        "efectos": {
            "skills": {"persuasion": 20},           # Categoría A
        },
        "adquisicion": {
            "tipo":   "acumulacion",
            "skill":  "persuasion",
            "umbral": 50,
        },
        "incompatible_con": [],
    },

    "sangre_fria": {
        "nombre":      "Sangre Fría",
        "icono":       "🧊",
        "descripcion": "Bajo presión funcionas mejor. Las penalizaciones por "
                       "salud/moral bajas se reducen a la mitad.",
        "tipo":        "positivo",
        "categoria":   "mente",
        "efectos": {
            "penalizacion_presion_mult": 0.5,       # Categoría B
        },
        "adquisicion": {
            "tipo":     "acumulacion",
            "contador": "veces_en_peligro_critico",
            "umbral":   5,
        },
        "incompatible_con": [],
    },

    # ══════════════════════════════════════════════════════════
    #  RASGOS NEGATIVOS (adquiridos por trauma o daño acumulado)
    # ══════════════════════════════════════════════════════════

    "cicatrices_de_guerra": {
        "nombre":      "Cicatrices de Guerra",
        "icono":       "🩹",
        "descripcion": "Heridas graves previas. La salud máxima se reduce en 10.",
        "tipo":        "negativo",
        "categoria":   "fisico",
        "efectos": {
            "salud_max": -10,                       # Categoría A
        },
        "adquisicion": {
            "tipo":     "acumulacion",
            "contador": "veces_en_peligro_critico",
            "umbral":   8,
        },
        "incompatible_con": [],
    },

    "claustrofobia": {
        "nombre":      "Claustrofobia",
        "icono":       "😰",
        "descripcion": "Los espacios cerrados te alteran. -15 Sigilo en interiores.",
        "tipo":        "negativo",
        "categoria":   "mente",
        "efectos": {
            "skills_en_interior": {"sigilo": -15},  # Categoría C
        },
        "adquisicion": {
            "tipo":   "evento",
            "evento": "quedar_atrapado",
        },
        "incompatible_con": [],
    },

    "adiccion_morfina": {
        "nombre":      "Adicción (Morfina)",
        "icono":       "💉",
        "descripcion": "Tu cuerpo la necesita. Sin ella, -2 a todas las stats cada turno.",
        "tipo":        "negativo",
        "categoria":   "fisico",
        "efectos": {
            "dependencia_item":     "morfina",      # Categoría D — key de ITEMS
            "penalizacion_sin_item": {"stats_global": -2},
        },
        "adquisicion": {
            "tipo":       "acumulacion",
            "item_usado": "morfina",
            "umbral":     5,
        },
        "incompatible_con": [],
    },

    "pesadillas": {
        "nombre":      "Pesadillas",
        "icono":       "💀",
        "descripcion": "El descanso no te restaura del todo. La fatiga baja un 30% menos.",
        "tipo":        "negativo",
        "categoria":   "mente",
        "efectos": {
            "recuperacion_descanso_mult": 0.70,     # Categoría B
        },
        "adquisicion": {
            "tipo":     "acumulacion",
            "contador": "muertes_vistas",
            "umbral":   3,
        },
        "incompatible_con": [],
    },

    # ══════════════════════════════════════════════════════════
    #  RASGOS DE BACKGROUND (asignados al crear personaje)
    # ══════════════════════════════════════════════════════════

    "instinto_medico": {
        "nombre":      "Instinto Médico",
        "icono":       "🩺",
        "descripcion": "Reconoces síntomas al instante. La medicina tiene efecto adicional.",
        "tipo":        "background",
        "categoria":   "conocimiento",
        "efectos": {
            "multiplicador_medicina": 1.25,         # Categoría B
            "skills": {"medicina": 10},             # Categoría A
        },
        "adquisicion": {
            "tipo":       "background",
            "background": "Médico/a de emergencias",
        },
        "incompatible_con": [],
    },

    "ingenio_mecanico": {
        "nombre":      "Ingenio Mecánico",
        "icono":       "🔧",
        "descripcion": "Puedes improvisar reparaciones con lo que encuentres.",
        "tipo":        "background",
        "categoria":   "conocimiento",
        "efectos": {
            "puede_fabricar": True,                  # Categoría F (reservado)
            "skills": {"mecanica": 10},             # Categoría A
        },
        "adquisicion": {
            "tipo":       "background",
            "background": "Mecánico/a automotriz",
        },
        "incompatible_con": [],
    },

    "disciplina_combate": {
        "nombre":      "Disciplina de Combate",
        "icono":       "🎖️",
        "descripcion": "Entrenamiento militar. No entras en pánico en combate.",
        "tipo":        "background",
        "categoria":   "combate",
        "efectos": {
            "inmune_panico": True,                   # Categoría E (reservado)
            "skills": {"combate_cac": 10, "combate_distancia": 10},  # A
        },
        "adquisicion": {
            "tipo":       "background",
            "background": "Militar/ex-policía",
        },
        "incompatible_con": [],
    },

    "hijo_de_la_tierra": {
        "nombre":      "Hijo de la Tierra",
        "icono":       "🌱",
        "descripcion": "Sabes qué es comestible en la naturaleza. El cuerpo aprovecha mejor la comida.",
        "tipo":        "background",
        "categoria":   "supervivencia",
        "efectos": {
            "multiplicador_consumo_hambre": 0.90,   # Categoría B
            "skills": {"supervivencia": 10},        # Categoría A
        },
        "adquisicion": {
            "tipo":       "background",
            "background": "Granjero/a",
        },
        "incompatible_con": [],
    },

    "mente_analitica": {
        "nombre":      "Mente Analítica",
        "icono":       "🔬",
        "descripcion": "Ves patrones donde otros ven caos. +10 Medicina y Mecánica.",
        "tipo":        "background",
        "categoria":   "conocimiento",
        "efectos": {
            "skills": {"medicina": 10, "mecanica": 10},  # Categoría A
        },
        "adquisicion": {
            "tipo":       "background",
            "background": "Científico/a",
        },
        "incompatible_con": [],
    },

    "dedos_ligeros": {
        "nombre":      "Dedos Ligeros",
        "icono":       "🖐️",
        "descripcion": "El viejo oficio no se olvida. +15 Sigilo y Saqueo.",
        "tipo":        "background",
        "categoria":   "supervivencia",
        "efectos": {
            "skills": {"sigilo": 15, "saqueo": 5},  # Categoría A
        },
        "adquisicion": {
            "tipo":       "background",
            "background": "Ladrón/Carterista",
        },
        "incompatible_con": [],
    },

    # ══════════════════════════════════════════════════════════
    #  NUEVOS RASGOS — SUPERVIVENCIA AMBIENTAL Y RESILIENCIA
    # ══════════════════════════════════════════════════════════

    "piel_curtida": {
        "nombre":      "Piel Curtida",
        "icono":       "🛡️",
        "descripcion": "Años de exposición endurecieron tu piel. Los efectos ambientales te afectan menos.",
        "tipo":        "positivo",
        "categoria":   "supervivencia",
        "efectos": {
            "resistencia_ambiental_mult": 0.70,     # Categoría B — nuevo efecto
            "multiplicador_consumo_sed":   0.92,
        },
        "adquisicion": {
            "tipo":    "acumulacion",
            "contador": "expediciones_completadas",
            "umbral":  20,
        },
        "incompatible_con": [],
    },

    "voluntad_de_hierro": {
        "nombre":      "Voluntad de Hierro",
        "icono":       "⚙️",
        "descripcion": "El horror no te paraliza. Penalizaciones de moral y trauma reducidas.",
        "tipo":        "positivo",
        "categoria":   "mental",
        "efectos": {
            "penalizacion_presion_mult":   0.75,    # Categoría B
            "xp_mult_global":              1.05,
        },
        "adquisicion": {
            "tipo":    "acumulacion",
            "contador": "veces_en_peligro_critico",
            "umbral":  10,
        },
        "incompatible_con": [],
    },

    "metabolismo_rapido": {
        "nombre":      "Metabolismo Rápido",
        "icono":       "⚡",
        "descripcion": "Las condiciones negativas duran menos. Tu cuerpo combate mejor las enfermedades.",
        "tipo":        "positivo",
        "categoria":   "medico",
        "efectos": {
            "recuperacion_condicion_mult": 1.30,    # Categoría B — nuevo
            "multiplicador_medicina":      1.10,
        },
        "adquisicion": {
            "tipo":   "acumulacion",
            "stat":   "resistencia",
            "umbral": 8,
        },
        "incompatible_con": [],
    },

    "temple_explorador": {
        "nombre":      "Temple del Explorador",
        "icono":       "🧊",
        "descripcion": "La presión no te mueve. Fatiga y hambre suben más despacio en expedición.",
        "tipo":        "positivo",
        "categoria":   "supervivencia",
        "efectos": {
            "multiplicador_consumo_hambre": 0.88,   # Categoría B
            "recuperacion_descanso_mult":   1.10,
        },
        "adquisicion": {
            "tipo":   "acumulacion",
            "skill":  "sigilo",
            "umbral": 55,
        },
        "incompatible_con": [],
    },

    "pulmones_acero": {
        "nombre":      "Pulmones de Acero",
        "icono":       "💨",
        "descripcion": "Polvo, gases, frío. Nada detiene tu respiración. Resistencia a climas peligrosos.",
        "tipo":        "positivo",
        "categoria":   "supervivencia",
        "efectos": {
            "resistencia_ambiental_mult": 0.60,     # Categoría B
            "riesgo_neumonia_mult":       0.40,     # Categoría B — nuevo
        },
        "adquisicion": {
            "tipo":    "acumulacion",
            "contador": "expediciones_completadas",
            "umbral":  30,
        },
        "incompatible_con": ["asma_cronica"],
    },

    "sombra": {
        "nombre":      "Sombra",
        "icono":       "🌑",
        "descripcion": "La oscuridad es tu aliada. Tus habilidades de sigilo aumentan de noche.",
        "tipo":        "positivo",
        "categoria":   "combate",
        "efectos": {
            "skills_en_noche": {"sigilo": 15, "combate_cac": 5},  # Categoría C
        },
        "adquisicion": {
            "tipo":    "acumulacion",
            "contador": "expediciones_nocturnas",
            "umbral":  10,
        },
        "incompatible_con": [],
    },
}
