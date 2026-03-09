# ============================================================
# data/eventos.py — Plantillas de eventos narrativos
#
# Tipos de evento válidos:
#   combate            — combate directo sin opciones
#   combate_evadible   — combate con opción de sigilo/huida
#   hallazgo           — loot bonus
#   hallazgo_especial  — loot especial con narrativa
#   interaccion        — caja fuerte, mecanismo, etc.
#   npc_amigable       — encuentro con sobreviviente amistoso
#   npc_dilema         — encuentro con decisión moral
#   npc_especial       — comerciante u otro NPC único
#   peligro_ambiental  — trampas, pisos, incendios
#   ambiental_forzado  — lluvia ácida, tormenta
#   ambiental_acumulativo — radiación
#   narrativo          — solo historia, sin mecánica
#   narrativo_especial — historia con efecto moral/info
#   peligro_oculto     — trampa que puede evitarse con percepción
# ============================================================

EVENTOS = {

    # ══════════════════════════════════════════════════════════
    #  COMBATE
    # ══════════════════════════════════════════════════════════
    "emboscada_infectado": {
        "tipo":        "combate",
        "titulo":      "¡Emboscada!",
        "descripcion": "Un infectado estaba oculto detrás de una estantería. "
                       "Te lanza antes de que puedas reaccionar.",
        "enemigo":     "infectado_rapido",
        "iniciativa":  "enemigo",
    },
    "patrulla_bandidos": {
        "tipo":        "combate_evadible",
        "titulo":      "Patrulla de bandidos",
        "descripcion": "Escuchas voces. Una patrulla de dos bandidos "
                       "recorre el pasillo principal.",
        "enemigo":     "bandido",
        "opciones": {
            "sigilo": {
                "texto":      "Ocultarte y esperar",
                "skill":      "sigilo",
                "dificultad": 40,
            },
            "combate": {
                "texto":      "Atacar por sorpresa (+15 primer golpe)",
                "skill":      "combate_cac",
                "dificultad": 50,
                "bonus_ataque": 15,
            },
            "huida": {
                "texto":      "Retirarte en silencio",
                "stat":       "destreza",
                "dificultad": 4,
                "moral_costo": -3,
            },
        },
    },
    "trampa_bandidos": {
        "tipo":        "combate",
        "titulo":      "Trampa de bandidos",
        "descripcion": "Era una trampa. Dos bandidos te estaban esperando.",
        "enemigo":     "bandido_armado",
        "iniciativa":  "enemigo",
    },

    # ══════════════════════════════════════════════════════════
    #  HALLAZGOS
    # ══════════════════════════════════════════════════════════
    "cadaver_con_loot": {
        "tipo":        "hallazgo",
        "titulo":      "Cadáver con equipo",
        "descripcion": "Encuentras el cuerpo de un sobreviviente. "
                       "Murió hace días, pero lleva equipo.",
        "loot_bonus":   1.5,
        "moral_costo": -5,
    },
    "deposito_oculto": {
        "tipo":        "hallazgo_especial",
        "titulo":      "Depósito oculto",
        "descripcion": "Detrás de una pared falsa encuentras un pequeño depósito. "
                       "Alguien lo preparó con cuidado y nunca volvió.",
        "loot_bonus":   2.0,
        "loot_extra":  ["botiquin", "lata_atun", "botella_agua"],
    },
    "caja_fuerte": {
        "tipo":        "interaccion",
        "titulo":      "Caja fuerte cerrada",
        "descripcion": "Una caja fuerte empotrada. El dial está bloqueado pero parece antiguo.",
        "opciones": {
            "mecanica": {
                "texto":       "Abrirla con mecánica",
                "skill":       "mecanica",
                "dificultad":  60,
                "loot_exito":  ["botiquin", "pistola_9mm", "balas_9mm", "morfina"],
            },
            "fuerza": {
                "texto":       "Forzarla (Fuerza)",
                "stat":        "fuerza",
                "dificultad":  8,
                "loot_exito":  ["botiquin", "balas_9mm", "lata_atun"],
                "ruido_fallo": True,
            },
            "ignorar": {
                "texto":       "Ignorarla y seguir",
                "resultado":   "nada",
            },
        },
    },
    "carta_familiar": {
        "tipo":        "narrativo",
        "titulo":      "Carta encontrada",
        "descripcion": "Un sobre pegado a la pared con un post-it que dice 'Para quien la encuentre'. "
                       "La lees. El último dueño de esta casa escribió hasta el final.",
        "moral_bonus":  -5,
        "loot":        ["diario_sobreviviente"],
    },

    # ══════════════════════════════════════════════════════════
    #  NPCs
    # ══════════════════════════════════════════════════════════
    "sobreviviente_amigable": {
        "tipo":        "npc_amigable",
        "titulo":      "Sobreviviente encontrado",
        "descripcion": "Una figura emerge de la penumbra con las manos en alto. "
                       "'No dispares. Solo busco comida.'",
        "opciones": {
            "ayudar": {
                "texto":    "Compartir recursos",
                "costo":    {"comida": 1},
                "moral_bonus": 10,
                "recompensa": {"info_zona": True},
            },
            "intercambio": {
                "texto":    "Intercambiar información",
                "moral_bonus": 5,
                "recompensa": {"loot_key": "mapa_zona", "prob": 0.5},
            },
            "ignorar": {
                "texto":    "Rechazarlo con frialdad",
                "moral_costo": -8,
            },
        },
    },
    "comerciante_nomada": {
        "tipo":        "npc_especial",
        "titulo":      "Comerciante nómada",
        "descripcion": "Un anciano con una carreta llena de curiosidades. "
                       "'Tengo de todo, si tienes con qué pagar.'",
        "comercio":    True,
        "inventario_comerciante": ["botiquin", "balas_9mm", "lata_atun",
                                    "filtro_agua", "cuchillo", "linterna"],
    },
    "nino_perdido": {
        "tipo":        "npc_dilema",
        "titulo":      "Niño perdido",
        "descripcion": "Un niño de no más de 8 años, sucio y asustado, "
                       "se aferra a una mochila roja.",
        "opciones": {
            "llevar": {
                "texto":    "Llevarlo al refugio",
                "costo":    {"comida": 2, "agua": 1},
                "moral_bonus": 25,
                "loot":    ["mochila_roja"],
            },
            "recursos": {
                "texto":    "Darle suministros y separar caminos",
                "costo":    {"comida": 1},
                "moral_bonus": 10,
            },
            "ignorar": {
                "texto":    "Seguir adelante",
                "moral_costo": -20,
            },
        },
    },

    # ══════════════════════════════════════════════════════════
    #  PELIGROS AMBIENTALES
    # ══════════════════════════════════════════════════════════
    "piso_inestable": {
        "tipo":        "peligro_ambiental",
        "titulo":      "Piso inestable",
        "descripcion": "El suelo cruje bajo tus pies. "
                       "Tienes un segundo para decidir.",
        "opciones": {
            "rapido": {
                "texto":      "Cruzar rápido (Destreza)",
                "stat":       "destreza",
                "dificultad": 5,
                "fallo_daño": (10, 25),
                "fallo_ruido": True,
            },
            "cuidadoso": {
                "texto":    "Rodear con cuidado",
                "fatiga_costo": 10,
            },
        },
    },
    "tormenta_acida": {
        "tipo":        "ambiental_forzado",
        "titulo":      "Tormenta ácida",
        "descripcion": "El cielo se tiñe de amarillo. Lluvia ácida. "
                       "Necesitas refugio inmediatamente.",
        "daño_sin_proteccion": 15,
        "proteccion_item":    "mascarilla",
        "daño_con_proteccion": 0,
        "consume_proteccion":  True,
    },
    "incendio_estructural": {
        "tipo":        "peligro_ambiental",
        "titulo":      "Incendio",
        "descripcion": "Humo y llamas bloquean la salida principal. "
                       "Hay que buscar otra ruta.",
        "opciones": {
            "atravesar": {
                "texto":    "Atravesar las llamas",
                "daño":     (15, 30),
            },
            "buscar_ruta": {
                "texto":      "Buscar salida alternativa (Percepción)",
                "stat":       "percepcion",
                "dificultad": 4,
                "fatiga_costo": 15,
            },
        },
    },
    "zona_radiactiva": {
        "tipo":        "ambiental_acumulativo",
        "titulo":      "Zona contaminada",
        "descripcion": "El aire sabe a metal. "
                       "La radiación es palpable aquí.",
        "radiacion_normal":   15,
        "radiacion_protegido": 5,
        "proteccion_item":    "mascarilla",
    },
    "trampa_cazador": {
        "tipo":        "peligro_oculto",
        "titulo":      "Trampa de cazador",
        "descripcion": "¡Clic! Una trampa para animales se cierra sobre tu pierna.",
        "percepcion_evitar":   5,
        "daño":               (8, 20),
        "condicion_aplica":   "herida_pierna",
    },

    # ══════════════════════════════════════════════════════════
    #  NARRATIVOS
    # ══════════════════════════════════════════════════════════
    "mensaje_radio": {
        "tipo":        "narrativo_especial",
        "titulo":      "Señal de radio",
        "descripcion": "Una frecuencia débil. Alguien repite coordenadas "
                       "y la palabra 'seguro'. ¿Será real o una trampa?",
        "moral_bonus":  15,
        "info_zona":    True,
    },
    "diario_anterior": {
        "tipo":        "narrativo",
        "titulo":      "Diario encontrado",
        "descripcion": "Un cuaderno. El último dueño de este lugar "
                       "escribió hasta el final. Sus palabras pesan.",
        "moral_costo": -5,
        "loot":        ["diario_sobreviviente"],
    },

    # ── EJEMPLO: cómo agregar un evento nuevo ─────────────────
    # "generador_averiado": {
    #     "tipo":        "interaccion",
    #     "titulo":      "Generador averiado",
    #     "descripcion": "Un generador enorme está apagado. "
    #                    "Si lo enciendes, iluminarás toda la zona.",
    #     "opciones": {
    #         "mecanica": {
    #             "texto":      "Reparar el generador (Mecánica)",
    #             "skill":      "mecanica",
    #             "dificultad": 50,
    #             "loot_exito": ["linterna", "pilas", "gasolina"],
    #             "bonus_exito": {"percepcion": 3},  # área iluminada
    #         },
    #         "ignorar": {
    #             "texto":    "Dejarlo y seguir",
    #             "resultado": "nada",
    #         },
    #     },
    # },
}
