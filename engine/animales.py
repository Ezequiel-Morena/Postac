# ============================================================
# engine/animales.py
# Motor de simulación de animales domésticos del refugio.
#
# API pública:
#   generar_animal(tipo, seed)       → dict (estado del animal)
#   integrar_animal(personaje, animal) → str (mensaje de bienvenida)
#   evaluar_encuentro_animal(personaje, area, seed) → dict | None
#   tick_animales(personaje, horas, rng) → list[str] (eventos narrativos)
# ============================================================

from __future__ import annotations

import random

from data.animales import TIPOS_ANIMALES, EVENTOS_ANIMALES, NOMBRES_ANIMALES


def generar_animal(tipo: str, seed: str) -> dict:
    """
    Crea el estado inicial de un animal doméstico.
    seed garantiza reproducibilidad (mismo seed → mismo animal).
    """
    defn = TIPOS_ANIMALES.get(tipo)
    if not defn:
        raise ValueError(f"Tipo de animal desconocido: {tipo}")

    rng = random.Random(seed)
    nombre_pool = NOMBRES_ANIMALES.get(tipo, ["Sin nombre"])
    nombre = rng.choice(nombre_pool)
    edad_dias = rng.randint(180, 1460)   # entre 6 meses y 4 años

    return {
        "tipo":        tipo,
        "nombre":      nombre,
        "salud":       defn["salud_max"],
        "salud_max":   defn["salud_max"],
        "hambre":      rng.randint(10, 35),
        "agua":        rng.randint(5, 25),
        "edad_dias":   edad_dias,
        "esta_enfermo": False,
        "ticks_sin_comer": 0,
        "seed_base":   seed,
    }


def integrar_animal(personaje, animal: dict) -> str:
    """
    Agrega el animal a personaje.animales_refugio.
    Retorna mensaje narrativo de llegada.
    """
    tipo = animal.get("tipo", "animal")
    defn = TIPOS_ANIMALES.get(tipo, {})
    nombre = animal.get("nombre", "el animal")
    personaje.animales_refugio.append(animal)
    return (
        f"🐾 {defn.get('icono','?')} {nombre} se une al refugio. "
        f"{defn.get('desc','')}"
    )


def evaluar_encuentro_animal(personaje, area: dict, seed: str) -> dict | None:
    """
    Durante una expedición, evalúa si se encuentra un animal doméstico.
    Retorna el animal generado o None si no hay encuentro.
    """
    tags_area = {str(t).lower() for t in area.get("tags", [])}
    tags_area.add(str(area.get("area_key", "")).lower())

    rng = random.Random(f"{seed}:animal_encuentro")

    candidatos = []
    for tipo, defn in TIPOS_ANIMALES.items():
        zonas_validas = {z.lower() for z in defn.get("zona_encuentro", [])}
        if tags_area & zonas_validas:
            candidatos.append((tipo, float(defn.get("prob_encuentro", 0.05))))

    if not candidatos:
        # fuera de zona específica: posibilidad menor de perro o gato
        candidatos = [("perro", 0.02), ("gato", 0.015)]

    for tipo, prob in candidatos:
        if rng.random() < prob:
            return generar_animal(tipo, f"{seed}:{tipo}")

    return None


def tick_animales(personaje, horas: float, rng: random.Random) -> list[str]:
    """
    Avanza el estado de todos los animales del refugio.
    Consume recursos, genera eventos narrativos, aplica efectos al personaje.
    """
    if not personaje.animales_refugio:
        return []

    msgs: list[str] = []
    tasa_dia = horas / 24.0
    muertos: list[int] = []

    for idx, animal in enumerate(personaje.animales_refugio):
        tipo = animal.get("tipo", "perro")
        defn = TIPOS_ANIMALES.get(tipo, {})
        nombre = animal.get("nombre", "Animal")
        icono  = defn.get("icono", "🐾")

        # ── Consumo de recursos ──────────────────────────────
        necesidades = defn.get("necesidades_dia", {})
        consumo_comida = necesidades.get("comida", 10) * tasa_dia
        consumo_agua   = necesidades.get("agua",   5)  * tasa_dia

        animal["hambre"] = min(100, animal.get("hambre", 0) + consumo_comida)
        animal["agua"]   = min(100, animal.get("agua",   0) + consumo_agua)

        # Intentar satisfacer necesidades con inventario del personaje
        if animal["hambre"] > 50:
            if personaje.tiene_item("Comida enlatada") or personaje.tiene_item("Ración"):
                # Intentar consumir un ítem de comida para el animal
                for nombre_comida in ("Ración", "Comida enlatada"):
                    if personaje.remover_item(nombre_comida, 1):
                        break
                animal["hambre"] = max(0, animal["hambre"] - 30)
            else:
                animal["ticks_sin_comer"] = animal.get("ticks_sin_comer", 0) + 1

        if animal["ticks_sin_comer"] > 5:
            animal["salud"] = max(0, animal.get("salud", 50) - 5)

        # ── Producción ───────────────────────────────────────
        if animal.get("salud", 0) > 30 and not animal.get("esta_enfermo"):
            produce = defn.get("produce", {})
            if produce and rng.random() < tasa_dia:
                if "comida" in produce:
                    _dar_item_comida(personaje, int(produce["comida"] * tasa_dia))
                if "agua" in produce:
                    personaje.sed = max(0, personaje.sed - int(produce["agua"] * tasa_dia * 2))
                if produce:
                    msgs.append(f"{icono} {nombre} produce su parte del refugio.")

        # ── Defensas ─────────────────────────────────────────
        defensa = int(defn.get("defensa", 0))
        if defensa > 0 and hasattr(personaje, "moral"):
            personaje.moral = min(100, personaje.moral + int(defensa * tasa_dia * 0.5))

        # ── Eventos aleatorios ────────────────────────────────
        eventos_posibles = defn.get("eventos_posibles", [])
        if eventos_posibles and rng.random() < 0.08 * tasa_dia:
            clave_evento = rng.choice(eventos_posibles)
            defn_evento = EVENTOS_ANIMALES.get(clave_evento, {})
            texto = defn_evento.get("texto", "").replace("{nombre}", nombre)
            efecto = defn_evento.get("efecto", {})

            if texto:
                msgs.append(f"{icono} {texto}")

            # Aplicar efectos del evento
            if "moral" in efecto:
                personaje.moral = min(100, max(0, personaje.moral + efecto["moral"]))
            if "comida" in efecto:
                _dar_item_comida(personaje, efecto["comida"])
            if "salud_animal" in efecto:
                animal["salud"] = max(0, animal.get("salud", 50) + efecto["salud_animal"])
            if efecto.get("nueva_cria") and defn.get("puede_reproducirse"):
                _intentar_cria(personaje, animal, msgs, rng)

        # ── Muerte del animal ─────────────────────────────────
        if animal.get("salud", 0) <= 0:
            muertos.append(idx)
            msgs.append(f"💀 {icono} {nombre} ha muerto. Una pérdida que duele.")
            personaje.moral = max(0, personaje.moral - 8)

    # Retirar animales muertos (en orden inverso para no alterar índices)
    for idx in reversed(muertos):
        personaje.animales_refugio.pop(idx)

    return msgs


def _dar_item_comida(personaje, cantidad: int) -> None:
    """Reduce el hambre del personaje simulando que recibe comida."""
    personaje.hambre = max(0, personaje.hambre - max(1, cantidad // 2))


def _intentar_cria(personaje, padre: dict, msgs: list[str], rng: random.Random) -> None:
    """Intenta agregar una cría al refugio (máximo 6 animales totales)."""
    if len(personaje.animales_refugio) >= 6:
        return
    tipo = padre.get("tipo", "perro")
    defn = TIPOS_ANIMALES.get(tipo, {})
    nombre_pool = NOMBRES_ANIMALES.get(tipo, ["Cría"])
    nombre_cria = rng.choice(nombre_pool)
    cria = {
        "tipo":        tipo,
        "nombre":      nombre_cria,
        "salud":       defn.get("salud_max", 40) // 2,
        "salud_max":   defn.get("salud_max", 40),
        "hambre":      20,
        "agua":        10,
        "edad_dias":   0,
        "esta_enfermo": False,
        "ticks_sin_comer": 0,
        "seed_base":   f"cria_{rng.random()}",
    }
    personaje.animales_refugio.append(cria)
    icono = defn.get("icono", "🐾")
    msgs.append(f"{icono} {nombre_cria} nació en el refugio. Un poco de vida nueva.")
