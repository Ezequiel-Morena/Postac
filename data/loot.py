# ============================================================
# data/loot.py — Tablas de botín
#
# Cada pool es una lista de claves de data/items.py.
# El engine elige aleatoriamente de la pool.
# None representa "no encontrar nada" en esa tirada.
#
# Para modificar la rareza de un ítem:
#   - Añadirlo más veces a la lista = más común
#   - Quitarlo o reducir apariciones = más raro
#   - None = probabilidad de no encontrar nada
# ============================================================

LOOT_POOLS = {

    # ── MEDICINA ──────────────────────────────────────────────
    "medicina_basica": [
        "venda", "venda", "venda",
        "antiseptico", "antiseptico",
        "trapos", "trapos",
        None,
    ],
    "medicina_media": [
        "venda", "venda",
        "botiquin", "botiquin",
        "antiseptico",
        "pastilla_purificadora",
        "yodo",
        None,
    ],
    "medicina_rara": [
        "morfina",
        "sutura", "sutura",
        "antibiotico", "antibiotico", "antibiotico",
        "botiquin",
        None,
    ],

    # ── COMIDA ────────────────────────────────────────────────
    "comida_escasa": [
        "lata_frijoles",
        "frutos_silvestres", "frutos_silvestres",
        "barritas_energia",
        None, None,
    ],
    "comida_media": [
        "lata_frijoles", "lata_frijoles",
        "lata_atun", "lata_atun",
        "lata_sopa",
        "barritas_energia", "barritas_energia",
        "carne_ahumada",
        None,
    ],

    # ── AGUA ──────────────────────────────────────────────────
    "agua_escasa": [
        "botella_agua",
        "agua_contaminada", "agua_contaminada",
        None, None,
    ],
    "agua_media": [
        "botella_agua", "botella_agua", "botella_agua",
        "garrafa_agua",
        "filtro_agua",
        None,
    ],

    # ── ARMAS ─────────────────────────────────────────────────
    "arma_improvisada": [
        "pipa_metal", "pipa_metal",
        "cuchillo",
        "lanza_improvisada",
        None, None,
    ],
    "arma_media": [
        "bate_beisbol", "bate_beisbol",
        "hacha",
        "cuchillo_tactico",
        "pistola_9mm",
        None,
    ],
    "arma_rara": [
        "pistola_9mm", "pistola_9mm",
        "escopeta",
        "molotov", "molotov",
    ],

    # ── MUNICIÓN ──────────────────────────────────────────────
    "municion_media": [
        "balas_9mm", "balas_9mm", "balas_9mm",
        "cartuchos_escopeta", "cartuchos_escopeta",
    ],

    # ── HERRAMIENTAS ──────────────────────────────────────────
    "herramientas": [
        "palanca", "palanca",
        "encendedor", "encendedor",
        "cuerda",
        "brujula",
        "ganzuas",
        None,
    ],

    # ── MATERIALES ────────────────────────────────────────────
    "material_basico": [
        "chatarra_metal", "chatarra_metal",
        "trapos", "trapos", "trapos",
        "madera",
        "cable_electrico",
        "pilas",
        None,
    ],
    "material_industrial": [
        "chatarra_metal", "chatarra_metal", "chatarra_metal",
        "gasolina", "gasolina",
        "cable_electrico", "cable_electrico",
        "cuerda",
        None,
    ],
    "material_especial": [
        "alcohol_industrial", "alcohol_industrial",
        "gasolina",
        "cable_electrico",
    ],

    # ── EQUIPO ────────────────────────────────────────────────
    "equipo_especial": [
        "linterna", "linterna",
        "mascarilla", "mascarilla",
        "mochila_tactica",
        "radio_comunicacion",
        "brujula",
        None,
    ],

    # ── COMBUSTIBLE ───────────────────────────────────────────
    "combustible": [
        "gasolina", "gasolina", "gasolina",
        "alcohol_industrial",
        None,
    ],

    # ── LIBROS DE HABILIDAD ───────────────────────────────────
    "libro_habilidad": [
        "cuaderno_medico", "cuaderno_medico",
        "manual_mecanica", "manual_mecanica",
        "guia_supervivencia", "guia_supervivencia",
        "tratado_combate",
        None,
    ],

    # ── MAPAS ─────────────────────────────────────────────────
    "mapa": [
        "mapa_zona", "mapa_zona", "mapa_zona",
        "plano_edificio",
        None, None,
    ],

    # ── POOL ESPECIAL (para depósitos ocultos y cajas fuertes) ─
    "general_buena": [
        "botiquin",
        "pistola_9mm",
        "balas_9mm",
        "lata_atun",
        "linterna",
        "chaleco_cuero",
        "cuchillo_tactico",
        "botella_agua",
        "antibiotico",
    ],

    # ── EJEMPLO: cómo agregar una pool nueva ──────────────────
    # "trofeo_militar": [
    #     "escopeta",
    #     "balas_9mm", "balas_9mm",
    #     "cartuchos_escopeta",
    #     "comida_militar",
    #     "chaleco_tactico",
    # ],
}
