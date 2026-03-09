# ============================================================
# data/rasgos.py
# Sistema de Rasgos (Traits/Perks).
#
# Los rasgos son modificadores permanentes que el personaje
# puede tener desde el inicio (background) o adquirir
# durante el juego (por eventos, decisiones, acumulación de XP).
#
# Para agregar un rasgo nuevo:
#   1. Añadir una entrada al diccionario RASGOS
#   2. Definir cuándo se puede adquirir en "adquisicion"
#   Nada más. El engine lo aplicará automáticamente.
# ============================================================

RASGOS = {

    # ══════════════════════════════════════════════════════════
    #  RASGOS POSITIVOS
    # ══════════════════════════════════════════════════════════

    # ── COMBATE ───────────────────────────────────────────────
    "golpe_brutal": {
        "nombre":      "Golpe Brutal",
        "icono":       "💥",
        "descripcion": "Tus ataques cuerpo a cuerpo hacen un 20% más de daño.",
        "tipo":        "positivo",
        "categoria":   "combate",
        "efectos": {
            "daño_cac_mult": 1.20,
        },
        "adquisicion": {
            "tipo":    "acumulacion",   # se gana con uso repetido
            "skill":   "combate_cac",
            "umbral":  60,             # cuando la skill llega a 60
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
            "skills": {"combate_distancia": 15},
        },
        "adquisicion": {
            "tipo":    "acumulacion",
            "skill":   "combate_distancia",
            "umbral":  50,
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
            "dificultad_esquive": -1,
        },
        "adquisicion": {
            "tipo":    "acumulacion",
            "stat":    "destreza",
            "umbral":  8,             # cuando destreza >= 8
        },
        "incompatible_con": [],
    },

    # ── SUPERVIVENCIA ─────────────────────────────────────────
    "estomago_de_hierro": {
        "nombre":      "Estómago de Hierro",
        "icono":       "🫀",
        "descripcion": "Puedes comer comida en mal estado sin consecuencias.",
        "tipo":        "positivo",
        "categoria":   "supervivencia",
        "efectos": {
            "inmune_envenenamiento_comida": True,
        },
        "adquisicion": {
            "tipo":    "evento",       # se gana tras sobrevivir un evento específico
            "evento":  "sobrevivir_envenenamiento",
        },
        "incompatible_con": [],
    },
    "metabolismo_lento": {
        "nombre":      "Metabolismo Lento",
        "icono":       "🐢",
        "descripcion": "Consumes recursos un 25% más lento.",
        "tipo":        "positivo",
        "categoria":   "supervivencia",
        "efectos": {
            "multiplicador_consumo_hambre": 0.75,
            "multiplicador_consumo_sed":    0.75,
        },
        "adquisicion": {
            "tipo":    "acumulacion",
            "stat":    "resistencia",
            "umbral":  9,
        },
        "incompatible_con": ["metabolismo_rapido"],
    },
    "ojos_de_aguila": {
        "nombre":      "Ojos de Águila",
        "icono":       "🦅",
        "descripcion": "Percibes detalles que otros ignoran. +20 a Saqueo.",
        "tipo":        "positivo",
        "categoria":   "supervivencia",
        "efectos": {
            "skills": {"saqueo": 20},
        },
        "adquisicion": {
            "tipo":    "acumulacion",
            "skill":   "saqueo",
            "umbral":  55,
        },
        "incompatible_con": [],
    },
    "curandero_nato": {
        "nombre":      "Curandero Nato",
        "icono":       "💊",
        "descripcion": "Los consumibles médicos tienen un 50% más de efecto.",
        "tipo":        "positivo",
        "categoria":   "conocimiento",
        "efectos": {
            "multiplicador_medicina": 1.50,
        },
        "adquisicion": {
            "tipo":    "acumulacion",
            "skill":   "medicina",
            "umbral":  65,
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
            "penalizacion_presion_mult": 0.5,
        },
        "adquisicion": {
            "tipo":    "acumulacion",
            "contador": "veces_en_peligro_critico",
            "umbral":   5,
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
            "skills": {"mecanica": 15},
            "puede_fabricar": True,
        },
        "adquisicion": {
            "tipo":    "acumulacion",
            "skill":   "mecanica",
            "umbral":  60,
        },
        "incompatible_con": [],
    },

    # ── SOCIAL ────────────────────────────────────────────────
    "cara_de_poker": {
        "nombre":      "Cara de Póker",
        "icono":       "🃏",
        "descripcion": "En negociaciones, tus intenciones son ilegibles. +20 Persuasión.",
        "tipo":        "positivo",
        "categoria":   "social",
        "efectos": {
            "skills": {"persuasion": 20},
        },
        "adquisicion": {
            "tipo":    "acumulacion",
            "skill":   "persuasion",
            "umbral":  50,
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
            "salud_max": -10,
        },
        "adquisicion": {
            "tipo":    "acumulacion",
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
            "skills_en_interior": {"sigilo": -15},
        },
        "adquisicion": {
            "tipo":    "evento",
            "evento":  "quedar_atrapado",
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
            "dependencia_item": "morfina",
            "penalizacion_sin_item": {"stats_global": -2},
        },
        "adquisicion": {
            "tipo":    "acumulacion",
            "item_usado": "morfina",
            "umbral":     5,         # usar morfina 5 veces
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
            "recuperacion_descanso_mult": 0.70,
        },
        "adquisicion": {
            "tipo":    "acumulacion",
            "contador": "muertes_vistas",   # testigo de muertes de NPCs
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
            "multiplicador_medicina": 1.25,
            "skills": {"medicina": 10},
        },
        "adquisicion": {
            "tipo":    "background",
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
            "puede_fabricar": True,
            "skills": {"mecanica": 10},
        },
        "adquisicion": {
            "tipo":    "background",
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
            "inmune_panico": True,
            "skills": {"combate_cac": 10, "combate_distancia": 10},
        },
        "adquisicion": {
            "tipo":    "background",
            "background": "Militar/ex-policía",
        },
        "incompatible_con": [],
    },
    "hijo_de_la_tierra": {
        "nombre":      "Hijo de la Tierra",
        "icono":       "🌱",
        "descripcion": "Sabes qué es comestible en la naturaleza. Reducción de hambre +10%.",
        "tipo":        "background",
        "categoria":   "supervivencia",
        "efectos": {
            "multiplicador_consumo_hambre": 0.90,
            "skills": {"supervivencia": 10},
        },
        "adquisicion": {
            "tipo":    "background",
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
            "skills": {"medicina": 10, "mecanica": 10},
        },
        "adquisicion": {
            "tipo":    "background",
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
            "skills": {"sigilo": 15, "saqueo": 5},
        },
        "adquisicion": {
            "tipo":    "background",
            "background": "Ladrón/Carterista",
        },
        "incompatible_con": [],
    },

    # ── EJEMPLO: cómo agregar un rasgo nuevo ──────────────────
    # "visión_nocturna": {
    #     "nombre":      "Visión Nocturna",
    #     "icono":       "🌙",
    #     "descripcion": "Adaptado a la oscuridad. Sin penalizaciones de noche.",
    #     "tipo":        "positivo",
    #     "categoria":   "supervivencia",
    #     "efectos": {
    #         "sin_penalizacion_noche": True,
    #         "skills": {"sigilo": 10},
    #     },
    #     "adquisicion": {
    #         "tipo":    "acumulacion",
    #         "contador": "expediciones_nocturnas",
    #         "umbral":   10,
    #     },
    #     "incompatible_con": [],
    # },
}
