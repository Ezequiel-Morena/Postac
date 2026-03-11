# ============================================================
# data/condiciones_medicas.py
# Catalogo data-driven de condiciones cronicas y predisposiciones.
#
# Estructura de cada condición:
#   nombre, descripcion, origen_default, severidad_base,
#   prob_hereditaria, efectos (fatiga_extra_hora,
#   moral_penalidad_tick, riesgo_infeccion_mult, ...)
#   adquirible: True/False — puede adquirirse en campo
# ============================================================

CONDICIONES_CRONICAS = {

    # ──────────────────────────────────────────────────────
    #  CONDICIONES HEREDITARIAS / PREEXISTENTES
    # ──────────────────────────────────────────────────────

    "asma_cronica": {
        "nombre": "Asma crónica",
        "descripcion": "Capacidad pulmonar reducida bajo esfuerzo físico intenso.",
        "origen_default": "hereditaria",
        "severidad_base": 1,
        "prob_hereditaria": 0.10,
        "adquirible": False,
        "efectos": {
            "fatiga_extra_hora":     0.4,
            "moral_penalidad_tick":  0,
            "riesgo_infeccion_mult": 1.10,
        },
    },
    "hipertension": {
        "nombre": "Hipertensión",
        "descripcion": "Mayor desgaste ante estrés, dolor y falta de descanso.",
        "origen_default": "hereditaria",
        "severidad_base": 1,
        "prob_hereditaria": 0.12,
        "adquirible": False,
        "efectos": {
            "fatiga_extra_hora":     0.3,
            "moral_penalidad_tick":  1,
            "riesgo_infeccion_mult": 1.00,
        },
    },
    "inmunodeficiencia_leve": {
        "nombre": "Inmunodeficiencia leve",
        "descripcion": "La progresión de infecciones es notablemente más rápida.",
        "origen_default": "hereditaria",
        "severidad_base": 2,
        "prob_hereditaria": 0.06,
        "adquirible": False,
        "efectos": {
            "fatiga_extra_hora":     0.2,
            "moral_penalidad_tick":  0,
            "riesgo_infeccion_mult": 1.28,
        },
    },
    "dolor_lumbar_cronico": {
        "nombre": "Dolor lumbar crónico",
        "descripcion": "Carga y esfuerzo prolongado generan fatiga adicional severa.",
        "origen_default": "adquirida",
        "severidad_base": 1,
        "prob_hereditaria": 0.04,
        "adquirible": True,
        "efectos": {
            "fatiga_extra_hora":     0.5,
            "moral_penalidad_tick":  0,
            "riesgo_infeccion_mult": 1.00,
        },
    },

    # ──────────────────────────────────────────────────────
    #  CONDICIONES ADQUIRIBLES EN CAMPO
    # ──────────────────────────────────────────────────────

    "sepsis": {
        "nombre": "Sepsis",
        "descripcion": "Infección sistémica grave. La bacteria entró al torrente sanguíneo. Sin antibióticos: fatal.",
        "origen_default": "infeccion_severa",
        "severidad_base": 3,
        "prob_hereditaria": 0.0,
        "adquirible": True,
        "condicion_activadora": "infeccion_cuerpo_critica",
        "prob_adquisicion": 0.25,
        "efectos": {
            "fatiga_extra_hora":     1.2,
            "moral_penalidad_tick":  3,
            "riesgo_infeccion_mult": 1.50,
            "daño_hora":             2,
        },
    },
    "intoxicacion_alimentaria": {
        "nombre": "Intoxicación alimentaria",
        "descripcion": "Vómitos, diarrea, deshidratación acelerada. Dura 12-24h pero debilita profundamente.",
        "origen_default": "comida_contaminada",
        "severidad_base": 2,
        "prob_hereditaria": 0.0,
        "adquirible": True,
        "condicion_activadora": "comida_contaminada",
        "prob_adquisicion": 0.10,
        "efectos": {
            "fatiga_extra_hora":     0.8,
            "moral_penalidad_tick":  2,
            "riesgo_infeccion_mult": 1.15,
            "sed_extra_hora":        3,
        },
    },
    "envenenamiento_radiacion": {
        "nombre": "Envenenamiento por radiación",
        "descripcion": "Exposición acumulada supera el umbral seguro. Náuseas, pérdida de cabello, daño celular.",
        "origen_default": "radiacion_acumulada",
        "severidad_base": 2,
        "prob_hereditaria": 0.0,
        "adquirible": True,
        "condicion_activadora": "radiacion_alta",
        "umbral_radiacion": 70,
        "prob_adquisicion": 0.30,
        "efectos": {
            "fatiga_extra_hora":     0.7,
            "moral_penalidad_tick":  2,
            "riesgo_infeccion_mult": 1.30,
            "daño_hora":             1,
        },
    },
    "quemaduras_acidas": {
        "nombre": "Quemaduras ácidas",
        "descripcion": "La lluvia o granizo ácido disolvió capas de piel. Dolor intenso y riesgo infeccioso alto.",
        "origen_default": "exposicion_acida",
        "severidad_base": 2,
        "prob_hereditaria": 0.0,
        "adquirible": True,
        "condicion_activadora": "clima_acido",
        "prob_adquisicion": 0.0,   # La probabilidad viene del clima directamente
        "efectos": {
            "fatiga_extra_hora":     0.6,
            "moral_penalidad_tick":  2,
            "riesgo_infeccion_mult": 1.40,
        },
    },
    "hipotermia": {
        "nombre": "Hipotermia",
        "descripcion": "La temperatura corporal bajó peligrosamente. Los músculos dejan de responder.",
        "origen_default": "exposicion_frio",
        "severidad_base": 2,
        "prob_hereditaria": 0.0,
        "adquirible": True,
        "condicion_activadora": "clima_frio_extremo",
        "prob_adquisicion": 0.0,   # Viene del clima
        "efectos": {
            "fatiga_extra_hora":     1.0,
            "moral_penalidad_tick":  1,
            "riesgo_infeccion_mult": 1.20,
            "daño_hora":             1,
        },
    },
    "hipertermia": {
        "nombre": "Golpe de calor",
        "descripcion": "La temperatura corporal subió peligrosamente. Confusión, taquicardia y riesgo de fallo orgánico.",
        "origen_default": "exposicion_calor",
        "severidad_base": 2,
        "prob_hereditaria": 0.0,
        "adquirible": True,
        "condicion_activadora": "temperatura_corporal_alta",
        "prob_adquisicion": 0.0,
        "efectos": {
            "fatiga_extra_hora":     1.5,
            "moral_penalidad_tick":  2,
            "riesgo_infeccion_mult": 1.10,
            "daño_hora":             1,
            "sed_extra_hora":        2.0,
        },
    },
    "neumonia": {
        "nombre": "Neumonía",
        "descripcion": "Infección pulmonar severa. Fiebre alta, dificultad para respirar, deterioro progresivo.",
        "origen_default": "exposicion_frio_humedo",
        "severidad_base": 2,
        "prob_hereditaria": 0.0,
        "adquirible": True,
        "condicion_activadora": "frio_humedo_y_fatiga",
        "prob_adquisicion": 0.08,
        "efectos": {
            "fatiga_extra_hora":     0.9,
            "moral_penalidad_tick":  2,
            "riesgo_infeccion_mult": 1.25,
            "daño_hora":             1,
        },
    },
    "sindrome_abstinencia": {
        "nombre": "Síndrome de abstinencia",
        "descripcion": "El cuerpo exige los químicos que ya no recibe. Temblores, irritabilidad, dolor difuso.",
        "origen_default": "dependencia_farmacos",
        "severidad_base": 2,
        "prob_hereditaria": 0.0,
        "adquirible": True,
        "condicion_activadora": "farmaco_carga_alta_reciente",
        "umbral_carga": 100,
        "prob_adquisicion": 0.20,
        "efectos": {
            "fatiga_extra_hora":     0.7,
            "moral_penalidad_tick":  3,
            "riesgo_infeccion_mult": 1.00,
        },
    },
    "agotamiento_profundo": {
        "nombre": "Agotamiento profundo",
        "descripcion": "El cuerpo llegó al límite. Incluso dormir ya no basta para recuperarse completamente.",
        "origen_default": "fatiga_sostenida",
        "severidad_base": 2,
        "prob_hereditaria": 0.0,
        "adquirible": True,
        "condicion_activadora": "fatiga_critica_sostenida",
        "umbral_fatiga": 90,
        "prob_adquisicion": 0.12,
        "efectos": {
            "fatiga_extra_hora":     0.5,
            "moral_penalidad_tick":  2,
            "riesgo_infeccion_mult": 1.10,
        },
    },
    "fractura": {
        "nombre": "Fractura ósea",
        "descripcion": "Un hueso roto sin tratamiento adecuado. Movilidad reducida y dolor constante.",
        "origen_default": "trauma_combate",
        "severidad_base": 2,
        "prob_hereditaria": 0.0,
        "adquirible": True,
        "condicion_activadora": "daño_masivo_combate",
        "prob_adquisicion": 0.15,
        "efectos": {
            "fatiga_extra_hora":     0.6,
            "moral_penalidad_tick":  1,
            "riesgo_infeccion_mult": 1.05,
        },
    },
    "envenenamiento_quimico": {
        "nombre": "Envenenamiento químico",
        "descripcion": "Toxinas industriales en el sistema. Daño hepático, visión borrosa, confusión.",
        "origen_default": "polvo_toxico",
        "severidad_base": 2,
        "prob_hereditaria": 0.0,
        "adquirible": True,
        "condicion_activadora": "clima_toxico",
        "prob_adquisicion": 0.0,   # Viene del clima
        "efectos": {
            "fatiga_extra_hora":     0.8,
            "moral_penalidad_tick":  2,
            "riesgo_infeccion_mult": 1.20,
            "daño_hora":             1,
        },
    },
    "deshidratacion_cronica": {
        "nombre": "Deshidratación crónica",
        "descripcion": "Riñones dañados por falta sostenida de agua. El cuerpo ya no retiene líquidos normalmente.",
        "origen_default": "sed_sostenida",
        "severidad_base": 2,
        "prob_hereditaria": 0.0,
        "adquirible": True,
        "condicion_activadora": "sed_critica_sostenida",
        "umbral_sed": 85,
        "prob_adquisicion": 0.10,
        "efectos": {
            "fatiga_extra_hora":     0.4,
            "moral_penalidad_tick":  1,
            "riesgo_infeccion_mult": 1.15,
            "sed_extra_hora":        2,
        },
    },
    "desnutricion_cronica": {
        "nombre": "Desnutrición crónica",
        "descripcion": "El cuerpo consume masa muscular. Fuerza y resistencia decaen semana a semana.",
        "origen_default": "hambre_sostenida",
        "severidad_base": 2,
        "prob_hereditaria": 0.0,
        "adquirible": True,
        "condicion_activadora": "hambre_critica_sostenida",
        "umbral_hambre": 80,
        "prob_adquisicion": 0.08,
        "efectos": {
            "fatiga_extra_hora":     0.5,
            "moral_penalidad_tick":  2,
            "riesgo_infeccion_mult": 1.20,
            "daño_hora":             1,
        },
    },
    "trauma_psicologico": {
        "nombre": "Trauma psicológico",
        "descripcion": "El horror de lo visto no desaparece. Pesadillas, flashbacks, dificultad para concentrarse.",
        "origen_default": "evento_traumatico",
        "severidad_base": 1,
        "prob_hereditaria": 0.0,
        "adquirible": True,
        "condicion_activadora": "muerte_vista_o_moral_critica",
        "prob_adquisicion": 0.10,
        "efectos": {
            "fatiga_extra_hora":     0.3,
            "moral_penalidad_tick":  3,
            "riesgo_infeccion_mult": 1.00,
        },
    },
}

PREDISPOSICION_POR_BACKGROUND = {
    "medico": [
        {"condicion": "dolor_lumbar_cronico", "prob": 0.08, "origen": "ocupacional"},
    ],
    "militar": [
        {"condicion": "dolor_lumbar_cronico", "prob": 0.16, "origen": "trauma_previo"},
        {"condicion": "hipertension",         "prob": 0.10, "origen": "estres_cronico"},
        {"condicion": "trauma_psicologico",   "prob": 0.12, "origen": "combate_previo"},
    ],
    "granjero": [
        {"condicion": "dolor_lumbar_cronico", "prob": 0.12, "origen": "sobrecarga"},
    ],
    "cientifico": [
        {"condicion": "hipertension",           "prob": 0.12, "origen": "estres_cronico"},
        {"condicion": "envenenamiento_quimico", "prob": 0.06, "origen": "exposicion_laboral"},
    ],
    "paramedico": [
        {"condicion": "dolor_lumbar_cronico", "prob": 0.10, "origen": "ocupacional"},
    ],
    "investigador": [
        {"condicion": "hipertension",         "prob": 0.08, "origen": "estres_cronico"},
    ],
}
