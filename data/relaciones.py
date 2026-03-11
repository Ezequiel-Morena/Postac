# ============================================================
# data/relaciones.py
# Datos de eventos sociales autónomos del refugio.
# Los NPCs ya no son un pool fijo — se generan proceduralmente
# en engine/familia.py usando los pools de data/familia.py.
# ============================================================

# ── Eventos autónomos que ocurren en el refugio ──────────────────────────────
# Cada evento puede tener:
#   requiere_tension_min    — tension del NPC debe ser >= valor
#   requiere_confianza_min  — confianza del NPC debe ser >= valor
#   requiere_personalidad   — lista de personalidades compatibles
#   item_ref                — item que se obtiene si el evento ocurre
#
EVENTOS_REFUGIO = [
    {
        "id":     "busqueda_exitosa",
        "nombre": "consiguió suministros en las cercanías",
        "peso":   20,
        "efectos": {"moral": 2, "confianza": 3, "lealtad": 2, "hambre_npc": -15},
        "item_ref": "lata_frijoles",
    },
    {
        "id":     "apoyo_emocional",
        "nombre": "te sostuvo emocionalmente tras un día duro",
        "peso":   16,
        "efectos": {"moral": 3, "confianza": 4, "tension": -2},
    },
    {
        "id":     "disputa_interna",
        "nombre": "entró en una disputa por los recursos del grupo",
        "peso":   12,
        "efectos": {"moral": -2, "confianza": -3, "tension": 5},
    },
    {
        "id":     "accidente_menor",
        "nombre": "sufrió un accidente leve durante tareas del refugio",
        "peso":   9,
        "efectos": {"moral": -1, "tension": 3, "salud_npc": -10},
    },
    {
        "id":     "mantenimiento",
        "nombre": "reforzó una zona del refugio",
        "peso":   14,
        "efectos": {"confianza": 2, "lealtad": 3, "tension": -1},
    },
    {
        "id":     "dia_rutinario",
        "nombre": "cumplió su rutina sin novedades",
        "peso":   25,
        "efectos": {"confianza": 1, "tension": -1},
    },
    {
        "id":     "enfermedad_leve",
        "nombre": "cayó enfermo durante tu ausencia",
        "peso":   8,
        "efectos": {"moral": -3, "tension": 4, "salud_npc": -20, "confianza": -1},
    },
    {
        "id":     "conflicto_violento",
        "nombre": "tuvo un altercado físico con otro habitante del refugio",
        "peso":   5,
        "efectos": {"moral": -5, "confianza": -5, "tension": 12, "salud_npc": -15},
        "requiere_tension_min": 50,
    },
    {
        "id":     "hallazgo_valioso",
        "nombre": "encontró algo valioso mientras exploraba los alrededores",
        "peso":   7,
        "efectos": {"moral": 4, "confianza": 4, "lealtad": 2},
        "item_ref": "botiquin",
        "requiere_personalidad": ["valiente", "pragmatico"],
    },
    {
        "id":     "confesion_miedo",
        "nombre": "te confesó que tiene miedo de no sobrevivir",
        "peso":   6,
        "efectos": {"moral": -2, "confianza": 6, "tension": -3},
        "requiere_confianza_min": 60,
    },
    {
        "id":     "descanso_profundo",
        "nombre": "descansó bien y recuperó fuerzas",
        "peso":   15,
        "efectos": {"moral": 2, "tension": -2, "salud_npc": 10, "hambre_npc": 5},
    },
    {
        "id":     "traicion_pequena",
        "nombre": "gastó reservas compartidas sin permiso",
        "peso":   4,
        "efectos": {"moral": -3, "confianza": -8, "tension": 8},
        "requiere_tension_min": 45,
        "requiere_personalidad": ["hosco", "desconfiado", "oportunista"],
    },
    {
        "id":     "rescate_npc",
        "nombre": "salvó a otro habitante de una situación peligrosa en el refugio",
        "peso":   4,
        "efectos": {"moral": 6, "confianza": 7, "lealtad": 5, "tension": -5},
    },
    {
        "id":     "relato_pasado",
        "nombre": "compartió contigo recuerdos de su vida antes del colapso",
        "peso":   8,
        "efectos": {"moral": 3, "confianza": 5, "tension": -2},
        "requiere_confianza_min": 45,
    },
    {
        "id":     "mediacion_conflicto",
        "nombre": "medió en una disputa entre dos habitantes del grupo",
        "peso":   6,
        "efectos": {"moral": 2, "tension": -4, "confianza": 3},
        "requiere_personalidad": ["empatico", "generoso", "optimista"],
    },
    {
        "id":     "baja_moral_colectiva",
        "nombre": "expresó que el grupo está perdiendo la esperanza",
        "peso":   5,
        "efectos": {"moral": -4, "tension": 6, "confianza": -2},
        "requiere_tension_min": 40,
    },
    {
        "id":     "cuidado_a_enfermo",
        "nombre": "cuidó a otro miembro del grupo durante su enfermedad",
        "peso":   7,
        "efectos": {"moral": 4, "confianza": 5, "lealtad": 3, "tension": -2},
        "requiere_personalidad": ["empatico", "generoso", "optimista"],
    },
    {
        "id":     "amago_de_irse",
        "nombre": "habló en serio sobre abandonar el grupo",
        "peso":   3,
        "efectos": {"moral": -6, "tension": 8, "confianza": -5},
        "requiere_tension_min": 60,
    },
    {
        "id":     "recuerdo_compartido",
        "nombre": "te compartió un objeto de su vida anterior que guarda con celo",
        "peso":   5,
        "efectos": {"moral": 3, "confianza": 8, "tension": -3},
        "requiere_confianza_min": 70,
    },
]
