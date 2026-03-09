# ============================================================
# data/personajes.py
# Nombres, apellidos y trasfondos de personaje.
#
# Para agregar un trasfondo nuevo:
#   1. Añadir una entrada a BACKGROUNDS
#   2. Referenciar el rasgo de background en data/rasgos.py
#   El engine leerá todo automáticamente.
# ============================================================

NOMBRES = {
    "masculino": [
        "Marcos", "Elías", "Iván", "León", "Damián", "Sebastián",
        "Rafael", "Tomás", "Bruno", "Hugo", "Emilio", "Nicolás",
        "Axel", "Mateo", "Santiago", "Víctor", "Rodrigo", "Abel",
        "Dante", "Ezra", "Ciro", "René", "Omar", "Héctor",
        "Fabio", "Leandro", "Ignacio", "Joel", "Ariel", "Saúl",
    ],
    "femenino": [
        "Mara", "Sofía", "Elena", "Zoe", "Nadia", "Valeria",
        "Carmen", "Iris", "Luna", "Dana", "Vera", "Claudia",
        "Alina", "Renata", "Miriam", "Jade", "Camila", "Leila",
        "Ara", "Nora", "Sasha", "Elia", "Talia", "Rhea",
        "Deva", "Inés", "Fiona", "Nyx", "Petra", "Selene",
    ],
    "apellidos": [
        "Vega", "Ramos", "Cruz", "Morales", "Torres", "Reyes",
        "Castillo", "Mendoza", "Silva", "Ríos", "Guerrero", "Salinas",
        "Vargas", "Flores", "Navarro", "Ibáñez", "Herrera", "Palma",
        "Rojas", "Núñez", "Peña", "Aguilar", "Fuentes", "Ortega",
        "Medina", "Lara", "Soto", "Delgado", "Romero", "Campos",
    ],
}

# ──────────────────────────────────────────────────────────────
#  TRASFONDOS
#  Cada background define:
#   - bonus_stats:  modificadores sobre las stats base
#   - bonus_skills: modificadores sobre las skills derivadas
#   - rasgos:       lista de claves en data/rasgos.py
#   - items_inicio: items con los que empieza el personaje
# ──────────────────────────────────────────────────────────────
BACKGROUNDS = {
    "medico": {
        "nombre":      "Médico/a de emergencias",
        "descripcion": "Antes del colapso trabajabas en urgencias. "
                       "Sabes leer síntomas, suturar heridas y mantener la calma.",
        "bonus_stats": {"inteligencia": 2, "resistencia": 1},
        "bonus_skills": {"medicina": 25, "supervivencia": 10},
        "rasgos":       ["instinto_medico"],
        "items_inicio": [
            {
                "ref": "botiquin",
                "desc_override": None,
            },
            {
                "ref": "bisturi",
                "nombre": "Bisturí",
                "tipo": "herramienta_medica",
                "peso": 0.1,
                "desc": "Útil para cirugías de campo o como arma improvisada.",
            },
            {
                "ref": "cuaderno_medico",
            },
        ],
    },
    "mecanico": {
        "nombre":      "Mecánico/a automotriz",
        "descripcion": "Entiendes cómo funcionan las máquinas. "
                       "Puedes fabricar herramientas y reparar casi cualquier cosa.",
        "bonus_stats": {"fuerza": 1, "inteligencia": 1, "destreza": 1},
        "bonus_skills": {"mecanica": 25, "saqueo": 10},
        "rasgos":       ["ingenio_mecanico"],
        "items_inicio": [
            {"ref": "llave_inglesa"},
            {"ref": "kit_herramientas"},
            {"ref": "cinta_aislante"},
        ],
    },
    "militar": {
        "nombre":      "Militar / ex-policía",
        "descripcion": "Entrenamiento en combate y trabajo bajo presión. "
                       "Conoces tácticas de supervivencia y no te derrumbas en crisis.",
        "bonus_stats": {"fuerza": 2, "destreza": 1},
        "bonus_skills": {"combate_cac": 20, "combate_distancia": 15, "sigilo": 10},
        "rasgos":       ["disciplina_combate"],
        "items_inicio": [
            {"ref": "cuchillo_tactico"},
            {"ref": "chaleco_cuero"},
            {"ref": "venda", "cantidad_override": 2},
        ],
    },
    "granjero": {
        "nombre":      "Granjero/a",
        "descripcion": "Viviste de la tierra. Sabes cultivar, criar animales "
                       "y sobrevivir semanas con muy poco.",
        "bonus_stats": {"resistencia": 2, "fuerza": 1, "suerte": 1},
        "bonus_skills": {"supervivencia": 25, "saqueo": 10},
        "rasgos":       ["hijo_de_la_tierra"],
        "items_inicio": [
            {"ref": "machete"},
            {"ref": "lata_frijoles", "cantidad_override": 3},
            {"ref": "semillas"},
        ],
    },
    "cientifico": {
        "nombre":      "Científico/a",
        "descripcion": "Mente analítica. Entiendes la biología del virus "
                       "y cómo sintetizar compuestos con recursos básicos.",
        "bonus_stats": {"inteligencia": 3, "percepcion": 1},
        "bonus_skills": {"medicina": 15, "mecanica": 15, "supervivencia": 10},
        "rasgos":       ["mente_analitica"],
        "items_inicio": [
            {"ref": "cuaderno_notas"},
            {"ref": "antibiotico"},
            {"ref": "mascarilla"},
        ],
    },
    "ladron": {
        "nombre":      "Ladrón / Carterista",
        "descripcion": "Viviste al margen de la ley. "
                       "La habilidad de pasar desapercibido ahora vale más que cualquier arma.",
        "bonus_stats": {"destreza": 3, "suerte": 1},
        "bonus_skills": {"sigilo": 25, "saqueo": 20},
        "rasgos":       ["dedos_ligeros"],
        "items_inicio": [
            {"ref": "ganzuas"},
            {"ref": "navaja"},
            {"ref": "botella_agua"},
        ],
    },

    # ── EJEMPLO: cómo agregar un background nuevo ─────────────
    # "enfermero": {
    #     "nombre":      "Enfermero/a de campo",
    #     "descripcion": "Asistente médico en zonas de conflicto previas al colapso.",
    #     "bonus_stats": {"inteligencia": 1, "resistencia": 1, "percepcion": 1},
    #     "bonus_skills": {"medicina": 20, "supervivencia": 15},
    #     "rasgos":      ["instinto_medico"],
    #     "items_inicio": [
    #         {"ref": "botiquin"},
    #         {"ref": "antibiotico"},
    #         {"ref": "venda", "cantidad_override": 3},
    #     ],
    # },
}
