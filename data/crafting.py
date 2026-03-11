# ============================================================
# data/crafting.py
# Recetas de crafteo data-driven.
#
# Para agregar una receta nueva:
#   1. Añadir entrada al diccionario RECETAS con clave única
#   2. Definir requisitos (items del inventario) y resultado
#   3. Opcionalmente skill_req para el check de habilidad
#   Nada más. El engine lo interpretará.
# ============================================================

RECETAS = {

    # ══════════════════════════════════════════════════════════
    #  MEDICINA Y SUPERVIVENCIA
    # ══════════════════════════════════════════════════════════

    "venda_improvisada": {
        "nombre": "Venda improvisada",
        "requisitos": {"Tiras de tela": 2, "Alcohol industrial": 1},
        "resultado": {"item_key": "venda", "cantidad": 2},
        "skill_req": {"supervivencia": 20},
        "desc": "Trapos y alcohol para improvisar material de curación básico.",
    },
    "botiquin_campo": {
        "nombre": "Botiquín de campo",
        "requisitos": {"Venda": 2, "Antiséptico": 1, "Tiras de tela": 1},
        "resultado": {"item_key": "botiquin", "cantidad": 1},
        "skill_req": {"medicina": 30},
        "desc": "Botiquín de emergencia hecho con componentes básicos.",
    },
    "agua_potable": {
        "nombre": "Purificar agua",
        "requisitos": {"Agua contaminada": 1, "Pastillas purificadoras": 1},
        "resultado": {"item_key": "botella_agua", "cantidad": 1},
        "skill_req": {"supervivencia": 10},
        "desc": "Convierte agua insegura en agua potable.",
    },
    "suero_improvisado": {
        "nombre": "Suero de rehidratación improvisado",
        "requisitos": {"Botella de agua": 1, "Sal (bolsa)": 1},
        "resultado": {"item_key": "suero_rehidratacion", "cantidad": 1},
        "skill_req": {"medicina": 35},
        "desc": "Mezcla salina para rehidratación de emergencia.",
    },
    "purgante_improviso": {
        "nombre": "Purgante de emergencia",
        "requisitos": {"Carbon activado": 1, "Botella de agua": 1},
        "resultado": {"item_key": "purgante_medico", "cantidad": 1},
        "skill_req": {"farmacologia": 25},
        "desc": "Carbón activado disuelto para absorber toxinas digestivas.",
    },
    "filtro_gas_improvisado": {
        "nombre": "Filtro de gas improvisado",
        "requisitos": {"Tiras de tela": 3, "Carbon activado": 2, "Cable eléctrico": 1},
        "resultado": {"item_key": "mascara_gas", "cantidad": 1},
        "skill_req": {"mecanica": 40},
        "desc": "Protección rudimentaria contra polvo tóxico y gases.",
    },

    # ══════════════════════════════════════════════════════════
    #  ARMAS Y COMBATE
    # ══════════════════════════════════════════════════════════

    "molotov_casero": {
        "nombre": "Cóctel molotov",
        "requisitos": {"Gasolina (1L)": 1, "Tiras de tela": 1, "Botella de agua": 1},
        "resultado": {"item_key": "molotov", "cantidad": 1},
        "skill_req": {"mecanica": 30},
        "desc": "Arma incendiaria rudimentaria. Alta efectividad contra grupos.",
    },
    "lanza_reforzada": {
        "nombre": "Lanza reforzada",
        "requisitos": {"Madera": 2, "Cuchillo": 1, "Cable eléctrico": 1},
        "resultado": {"item_key": "lanza_improvisada", "cantidad": 1},
        "skill_req": {"combate_cac": 25},
        "desc": "Punta cortante fijada a un asta estable. Alcance y daño mejorados.",
    },
    "explosivo_primitivo": {
        "nombre": "Explosivo primitivo",
        "requisitos": {"Gasolina (1L)": 1, "Madera": 2, "Cable eléctrico": 2},
        "resultado": {"item_key": "explosivo_casero", "cantidad": 1},
        "skill_req": {"mecanica": 55, "combate_cac": 20},
        "desc": "Inestable pero potente. Manéjalo con mucho cuidado.",
    },
    "trampa_caza": {
        "nombre": "Trampa de caza",
        "requisitos": {"Cable eléctrico": 2, "Madera": 1},
        "resultado": {"item_key": "trampa_caza", "cantidad": 2},
        "skill_req": {"supervivencia": 30, "botanica": 15},
        "desc": "Trampa para pequeños animales. Puede proporcionar proteínas.",
    },

    # ══════════════════════════════════════════════════════════
    #  EQUIPO Y UTILIDAD
    # ══════════════════════════════════════════════════════════

    "linterna_improvisada": {
        "nombre": "Linterna improvisada",
        "requisitos": {"Cable eléctrico": 2, "Gasolina (1L)": 1},
        "resultado": {"item_key": "linterna", "cantidad": 1},
        "skill_req": {"mecanica": 25},
        "desc": "Luz portátil de emergencia. No dura mucho, pero ilumina cuando importa.",
    },
    "cuerda_reforzada": {
        "nombre": "Cuerda reforzada",
        "requisitos": {"Tiras de tela": 4, "Cable eléctrico": 1},
        "resultado": {"item_key": "cuerda", "cantidad": 2},
        "skill_req": {"supervivencia": 20},
        "desc": "Cuerda resistente para escalar, atar o improvisar estructuras.",
    },
    "armadura_cuero": {
        "nombre": "Armadura de cuero reforzada",
        "requisitos": {"Tiras de tela": 4, "Madera": 1, "Llave inglesa": 1},
        "resultado": {"item_key": "chaleco_improvisado", "cantidad": 1},
        "skill_req": {"mecanica": 45, "supervivencia": 25},
        "desc": "Protección básica hecha con materiales de refugio.",
    },
    "senal_socorro": {
        "nombre": "Señal de socorro",
        "requisitos": {"Madera": 2, "Gasolina (1L)": 1, "Tiras de tela": 1},
        "resultado": {"item_key": "senal_fuego", "cantidad": 1},
        "skill_req": {"supervivencia": 15},
        "desc": "Fuego de señalización. Puede atraer ayuda... o amenazas.",
    },
    "destilador_agua": {
        "nombre": "Destilador de agua rudimentario",
        "requisitos": {"Madera": 3, "Cable eléctrico": 1, "Tiras de tela": 2},
        "resultado": {"item_key": "botella_agua", "cantidad": 3},
        "skill_req": {"mecanica": 50, "supervivencia": 30},
        "desc": "Purifica grandes cantidades de agua. Instalación fija en el refugio.",
    },
}
