# ============================================================
# data/familia.py
# Datos para el sistema de árbol genealógico y generación
# procedural de NPCs. Sin lógica — solo definiciones y pools.
# ============================================================

# ── Tipos de vínculo familiar ──────────────────────────────────────────────────
RELACION_TIPOS = {
    "pareja":   "Pareja",
    "hijo":     "Hijo",
    "hija":     "Hija",
    "padre":    "Padre",
    "madre":    "Madre",
    "hermano":  "Hermano",
    "hermana":  "Hermana",
}

# ── Estados de relación romántica (progresión) ─────────────────────────────────
ESTADOS_RELACION = [
    "desconocido",   # Recién llegado, sin interacción real
    "conocido",      # Han hablado, existe reconocimiento
    "amigo",         # Confianza moderada, interacciones positivas
    "cercano",       # Alta confianza, vínculo emocional
    "interes",       # Una de las partes muestra interés romántico
    "pareja",        # Relación confirmada
    "ex_pareja",     # Relación terminada
]

CONFIANZA_PARA_ESTADO = {
    "conocido":  20,
    "amigo":     45,
    "cercano":   65,
    "interes":   72,   # Umbral para que el simulador proponga relación
    "pareja":    80,
}

# ── Hitos de crecimiento de hijos ─────────────────────────────────────────────
EDAD_JOVEN    = 14   # Puede ayudar con tareas del refugio
EDAD_ADULTO   = 18   # NPC pleno, puede ir de expedición

HITOS_CRECIMIENTO: dict[int, str] = {
    1:  "Da sus primeros pasos. La esperanza tiene peso.",
    3:  "Empieza a hablar. Sus preguntas sobre el mundo duelen.",
    5:  "Hace amigos entre los adultos del refugio.",
    8:  "Entiende que el mundo de afuera es peligroso.",
    10: "Empieza a ayudar con tareas pequeñas. Aprende rápido.",
    14: "Ya puede encargarse de tareas reales en el refugio.",
    18: "Es un adulto. Puede salir al mundo si lo desea.",
}

# ── Roles posibles para NPCs generados proceduralmente ───────────────────────
ROLES_NPC = [
    "cazador",
    "médico",
    "mecánico",
    "cocinero",
    "vigilante",
    "explorador",
    "agricultor",
    "ingeniero",
    "sanitario",
    "maestro",
    "comerciante",
    "soldado",
    "guardia",
    "recolector",
    "carpintero",
    "herrero",
    "enfermero",
    "cartógrafo",
    "pastor",
    "químico",
]

# Roles que tienen bonificación a las expediciones autónomas
ROLES_EXPEDICION = {
    "cazador", "explorador", "soldado", "guardia", "cartógrafo",
}

# Mapeo rol → pool de loot que trae cuando vuelve de expedición
ROLES_LOOT_EXPEDICION: dict[str, str] = {
    "cazador":     "comida",
    "explorador":  "suministros",
    "soldado":     "armas",
    "guardia":     "suministros",
    "recolector":  "comida",
    "médico":      "medicina",
    "sanitario":   "medicina",
    "enfermero":   "medicina",
    "mecánico":    "herramientas",
    "ingeniero":   "herramientas",
    "carpintero":  "herramientas",
    "herrero":     "herramientas",
    "cocinero":    "comida",
    "agricultor":  "comida",
    "pastor":      "comida",
    "comerciante": "suministros",
    "maestro":     "suministros",
    "cartógrafo":  "suministros",
    "químico":     "medicina",
}

# ── Personalidades posibles ───────────────────────────────────────────────────
PERSONALIDADES_NPC = [
    "valiente",
    "cauteloso",
    "pragmatico",
    "empatico",
    "hosco",
    "desconfiado",
    "generoso",
    "reservado",
    "optimista",
    "melancolico",
    "leal",
    "oportunista",
    "curioso",
    "protector",
    "estoico",
]

# Personalidades que favorecen salir de expedición (factor extra)
PERSONALIDADES_EXPEDICION = {"valiente", "curioso", "pragmatico", "estoico"}

# ── Descripciones de backstory por rol (se combinan con el nombre) ────────────
BACKSTORIES_POR_ROL: dict[str, list[str]] = {
    "cazador": [
        "Sobrevivió solo en el bosque durante meses antes de llegar.",
        "Conoce las trampas que dejaron otros antes del colapso.",
        "Dice que cazar le enseñó a ser paciente. El mundo le enseñó a ser rápido.",
    ],
    "médico": [
        "Era residente cuando empezó todo. No ha parado desde entonces.",
        "Sus manos temblaban al principio. Ya no.",
        "Perdió a su último paciente hace tres semanas. Sigue trabajando.",
    ],
    "mecánico": [
        "Puede reparar casi cualquier cosa si le das el tiempo suficiente.",
        "Dice que las máquinas son más honestas que las personas.",
        "Trabajaba en un taller antes. Ahora ese saber vale más que el oro.",
    ],
    "cocinero": [
        "Convirtió una lata de pintura vacía en una olla funcional.",
        "Sabe hacer que lo poco sepa a algo. Eso importa más de lo que parece.",
        "Solía tener un restaurante. A veces lo menciona, rápido, y cambia de tema.",
    ],
    "vigilante": [
        "No duerme bien. Prefiere los turnos de noche.",
        "Confía en sus instintos sobre las personas. Raramente se equivoca.",
        "Dice que vigilar es lo único que sabe hacer bien. Miente: también escucha.",
    ],
    "explorador": [
        "Tiene mapas dibujados a mano de zonas que nadie más ha pisado.",
        "Conoce rutas seguras que no aparecen en ningún lado.",
        "No se queda quieto mucho tiempo. El movimiento lo mantiene cuerdo.",
    ],
    "agricultor": [
        "Encontró tierra cultivable cuando nadie creía que quedara.",
        "Sus manos tienen callo antiguo. Saben lo que hacen.",
        "Le habla a las plantas. Dice que crecen mejor así.",
    ],
    "ingeniero": [
        "Diseñó el sistema de filtrado de agua del refugio de su grupo anterior.",
        "Ve soluciones donde otros ven escombros.",
        "Prefiere los números a las palabras. Pero sus cálculos salvan vidas.",
    ],
    "sanitario": [
        "Aprendió medicina de urgencia en el campo, sin libros.",
        "Nunca pierde la calma cuando hay heridos. Es casi inquietante.",
        "Guarda los últimos antibióticos para quien más los necesite, no para sí.",
    ],
    "maestro": [
        "Insiste en enseñar a los niños aunque nadie entienda para qué.",
        "Dice que el conocimiento es lo único que no se puede saquear.",
        "Tiene memorizada la tabla periódica, los poemas de Neruda y cómo encender fuego.",
    ],
    "comerciante": [
        "Conoce el valor real de cada cosa. No lo usa para aprovecharse, sino para sobrevivir.",
        "Tiene contactos en tres asentamientos que nadie más conoce.",
        "Le gusta negociar. Dice que es la única forma de hablar con extraños sin riesgo.",
    ],
    "soldado": [
        "Cumplió órdenes mucho tiempo. Ahora solo cumple las propias.",
        "Sus cicatrices cuentan más historias de las que él contará jamás.",
        "Prefiere la acción a la conversación. Pero protege a los suyos sin dudar.",
    ],
    "guardia": [
        "Fue policía antes. El uniforme ya no existe, pero el instinto sí.",
        "No le gusta la violencia, pero no la evita cuando hace falta.",
        "Duerme con un ojo abierto. Literal.",
    ],
    "recolector": [
        "Sabe dónde buscar lo que otros descartan.",
        "Ha convertido la basura del viejo mundo en recursos del nuevo.",
        "Camina mucho, habla poco, trae siempre algo útil.",
    ],
    "carpintero": [
        "Construyó las barricadas del refugio anterior con sus propias manos.",
        "Dice que la madera tiene memoria. No lo cree nadie, pero le respetan el trabajo.",
        "Puede fabricar casi cualquier mueble o estructura si le dan el material.",
    ],
    "herrero": [
        "Forja herramientas y armas cuando hay metal suficiente.",
        "Su trabajo es ruidoso. A veces eso es una ventaja, a veces no.",
        "Aprendió el oficio de su padre, que lo aprendió del suyo.",
    ],
    "enfermero": [
        "Pasó años cuidando enfermos terminales. Eso te cambia.",
        "Su paciencia con los heridos parece infinita.",
        "Sabe cuándo un cuerpo puede más y cuándo no. Ese saber duele.",
    ],
    "cartógrafo": [
        "Dibuja mapas de memoria con una precisión que asusta.",
        "Ha recorrido más kilómetros que nadie en el refugio.",
        "Sus mapas han salvado vidas. Él no lo dice, pero todos lo saben.",
    ],
    "pastor": [
        "Cuida un pequeño rebaño desde el primer año del colapso.",
        "Sus animales son la única fuente de leche del refugio.",
        "Habla con los animales más que con las personas. Los entiende mejor.",
    ],
    "químico": [
        "Produce medicamentos básicos con lo que encuentra.",
        "Sus experimentos a veces huelen mal. Siempre terminan siendo útiles.",
        "Antes investigaba en una universidad. Ahora investiga cómo no morir.",
    ],
}

# Backstory genérico para roles sin lista específica
BACKSTORY_GENERICO = [
    "Llegó desde el norte hace unas semanas. No dice de dónde exactamente.",
    "Ha sobrevivido más de lo que cualquiera esperaría.",
    "No habla mucho de su pasado, pero sabe cuidarse en el presente.",
    "Perdió a alguien importante. Eso se nota en cómo mira al horizonte.",
    "Tiene un conjunto de habilidades difícil de clasificar. Resulta útil.",
]

# ── Eventos familiares (pool para tick_familia) ───────────────────────────────
EVENTOS_FAMILIA: list[dict] = [
    {
        "id":      "propuesta_relacion_npc",
        "tipo":    "relacion",
        "titulo":  "{nombre} se acerca a ti",
        "texto":   "{nombre} te busca después de que el refugio se calma. "
                   "No dice mucho, pero algo en su mirada lo dice todo. "
                   "Parece que tiene algo que confesarte.",
        "requiere_estado_relacion": "cercano",
        "requiere_confianza_min":    72,
        "efecto": {"propone_relacion": True},
    },
    {
        "id":      "momento_de_pareja",
        "tipo":    "relacion",
        "titulo":  "Una noche tranquila",
        "texto":   "Por una vez el refugio está quieto. Tú y {nombre} "
                   "encontráis un momento para vosotros. Sin hablar de "
                   "supervivencia. Solo de estar.",
        "requiere_estado_relacion": "pareja",
        "efecto": {"moral_jugador": 8, "confianza_npc": 4},
    },
    {
        "id":      "conflicto_pareja",
        "tipo":    "relacion",
        "titulo":  "Tensión entre vosotros",
        "texto":   "El estrés acumulado estalla. Tú y {nombre} cruzáis "
                   "palabras que no debíais. El silencio después pesa.",
        "requiere_estado_relacion": "pareja",
        "requiere_tension_min":      60,
        "efecto": {"moral_jugador": -5, "confianza_npc": -8, "tension_npc": -10},
    },
    {
        "id":      "embarazo",
        "tipo":    "familia",
        "titulo":  "Una nueva vida",
        "texto":   "{nombre} te da la noticia. Estás esperando un hijo. "
                   "En este mundo, eso es miedo y esperanza a partes iguales.",
        "requiere_estado_relacion": "pareja",
        "requiere_confianza_min":    75,
        "prob":    0.04,  # Probabilidad por tick cuando condiciones se cumplen
        "efecto": {"inicia_embarazo": True, "moral_jugador": 12},
    },
    {
        "id":      "nacimiento",
        "tipo":    "familia",
        "titulo":  "Ha llegado al mundo",
        "texto":   "Después de horas largas, {nombre_bebe} nace. "
                   "Sus primeros lloros llenan el refugio de algo que "
                   "hace tiempo no se sentía: vida nueva.",
        "efecto": {"nace_hijo": True, "moral_jugador": 20},
    },
    {
        "id":      "hito_hijo",
        "tipo":    "familia",
        "titulo":  "Hito: {nombre_hijo}",
        "texto":   "{nombre_hijo} — {hito_texto}",
        "efecto": {"moral_jugador": 10},
    },
    {
        "id":      "hijo_adulto",
        "tipo":    "familia",
        "titulo":  "{nombre_hijo} ya es adulto",
        "texto":   "{nombre_hijo} cumple {edad} años. Ya no es el niño "
                   "que llegó a este mundo entre el caos. Es alguien "
                   "en quien puedes confiar.",
        "efecto": {"moral_jugador": 15, "activa_adulto": True},
    },
    {
        "id":      "npc_forma_pareja",
        "tipo":    "relacion_npc",
        "titulo":  "{nombre_a} y {nombre_b}",
        "texto":   "Parece que algo ha surgido entre {nombre_a} y {nombre_b}. "
                   "No lo dicen abiertamente, pero el refugio lo nota.",
        "efecto": {"forma_pareja_npc": True, "moral_refugio": 5},
    },
    {
        "id":      "npc_embarazo",
        "tipo":    "familia_npc",
        "titulo":  "Buenas noticias en el refugio",
        "texto":   "{nombre_a} y {nombre_b} esperan un hijo. "
                   "La noticia recorre el refugio con una calidad extraña: alegría.",
        "efecto": {"inicia_embarazo_npc": True, "moral_refugio": 8},
    },
]

# ── Nombres para hijos nacidos en el refugio ─────────────────────────────────
NOMBRES_BEBES = {
    "masculino": [
        "Kael", "Ryen", "Sion", "Arlo", "Lev", "Zane", "Coen",
        "Eli", "Jove", "Niko", "Ren", "Luca", "Theo", "Max",
        "Ian", "Sol", "Axel", "Biel", "Kai", "Dario",
    ],
    "femenino": [
        "Aya", "Miel", "Zara", "Lena", "Naia", "Kira", "Tess",
        "Opal", "Lyra", "Vea", "Remi", "Wren", "Isla", "Nell",
        "Clea", "Brea", "Faye", "Rue", "Sela", "Aela",
    ],
}
