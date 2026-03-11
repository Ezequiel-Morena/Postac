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
        "suero_rehidratacion",
        None,
    ],
    "medicina_media": [
        "venda", "venda",
        "botiquin", "botiquin",
        "antiseptico",
        "pastilla_purificadora",
        "yodo",
        "pastillas_yodo",
        "vitaminas_c",
        "calmante_nervioso",
        None,
    ],
    "medicina_rara": [
        "morfina",
        "sutura", "sutura",
        "antibiotico", "antibiotico", "antibiotico",
        "botiquin",
        "antidoto_universal",
        "purgante_medico",
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
        "racion_deshidratada",
        "carne_ahumada",
        "racion_militar",
        "carne_cruda",
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
        "suero_rehidratacion",
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
        "detector_radiacion",
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
        "filtro_hepa",
        "cable_electrico",
    ],

    # ── EQUIPO ────────────────────────────────────────────────
    "equipo_especial": [
        "linterna", "linterna",
        "manta_termica",
        "mascarilla", "mascarilla",
        "mochila_tactica",
        "radio_comunicacion",
        "brujula",
        "mascara_gas",
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
        "racion_militar",
        "pastillas_yodo",
    ],

    # ── EJEMPLO: cómo agregar una pool nueva ──────────────────
    # "trofeo_militar": [
    #     "escopeta",
    #     "balas_9mm", "balas_9mm",
    #     "cartuchos_escopeta",
    #     "comida_militar",
    #     "chaleco_tactico",
    # ],

    # ── VESTIMENTA ─────────────────────────────────────────────
    "ropa_comun": [
        "camiseta_algodon", "camiseta_algodon",
        "pantalon_algodon", "pantalon_algodon",
        "zapatillas", "zapatillas",
        "gorro_lana",
        "guantes_lana",
        "sombrero_ala",
        None, None,
    ],
    "ropa_abrigo": [
        "abrigo_invierno", "abrigo_invierno",
        "chaqueta_cuero",
        "pantalon_cuero",
        "botas_cuero", "botas_cuero",
        "gorro_lana", "gorro_lana",
        "guantes_cuero",
        "pasamontanas",
        None,
    ],
    "ropa_impermeable": [
        "impermeable", "impermeable",
        "capucha_sintetica",
        "botas_invierno",
        "pantalon_termico",
        "guantes_trabajo",
        None,
    ],
    "ropa_tactica": [
        "camisa_militar",
        "gabardina_militar",
        "pantalon_cargo",
        "botas_militares",
        "casco_construccion",
        "guantes_cuero",
        None, None,
    ],
    "ropa_nbq": [
        "traje_nbq",
        "pantalon_termico",
        "botas_invierno",
        "guantes_trabajo",
        "casco_construccion",
        None, None, None,
    ],
}
