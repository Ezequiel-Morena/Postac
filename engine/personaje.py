# ============================================================
# engine/personaje.py
# Motor del personaje — lee todo desde data/, sin datos hardcodeados.
# ============================================================
import random
import copy
import re
from datetime import datetime

from data.stats      import STATS, VITALES
from data.skills     import SKILLS
from data.rasgos     import RASGOS
from data.items      import ITEMS
from data.personajes import NOMBRES, BACKGROUNDS

# Tipos cuyas instancias se apilan por cantidad.
# Los ítems con 'usos' individuales NO son apilables.
_TIPOS_STACKABLES = {"comida", "agua", "municion", "material", "misc"}

# Íconos por tipo de ítem
_ICONOS_TIPO = {
    "comida":           "🍖",
    "agua":             "💧",
    "medicina":         "💊",
    "arma_fuego":       "🔫",
    "arma_cortante":    "🔪",
    "arma_contundente": "🪓",
    "arma_arrojadiza":  "🏹",
    "armadura":         "🛡 ",
    "casco":            "⛑ ",
    "municion":         "🔋",
    "herramienta":      "🔧",
    "equipo":           "🎒",
    "equipo_especial":  "⭐",
    "material":         "📦",
    "libro":            "📚",
    "misc":             "🔹",
}


def _generar_partida_id(nombre: str, apellido: str) -> str:
    """
    ID único para la partida: nombre_apellido_YYYYMMDD_HHMMSS
    Se usa como subdirectorio para las bitácoras de esa partida.
    """
    n  = re.sub(r"[^\w]", "_", nombre.lower())
    a  = re.sub(r"[^\w]", "_", apellido.lower())
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{n}_{a}_{ts}"


class Condicion:
    """Estado temporal o permanente que afecta al personaje."""

    def __init__(self, clave: str, nombre: str, severidad: int,
                 duracion: int, efectos: dict, descripcion: str = ""):
        self.clave       = clave
        self.nombre      = nombre
        self.severidad   = severidad
        self.duracion    = duracion     # -1 = permanente hasta tratar
        self.efectos     = efectos
        self.descripcion = descripcion
        self.turnos_rest = duracion

    def tick(self) -> bool:
        if self.duracion > 0:
            self.turnos_rest -= 1
        return self.turnos_rest > 0 or self.duracion == -1

    def __str__(self):
        sev = {1: "Leve", 2: "Moderado", 3: "Grave"}.get(self.severidad, "")
        return f"{self.nombre} ({sev})"


class Sobreviviente:
    """
    Personaje completamente data-driven.
    Todos los stats, skills y rasgos se construyen desde los archivos data/.
    """

    def __init__(self):
        # ── IDENTIDAD ─────────────────────────────────────────
        self.genero   = random.choice(["Masculino", "Femenino"])
        pool          = NOMBRES["masculino" if self.genero == "Masculino" else "femenino"]
        self.nombre   = random.choice(pool)
        self.apellido = random.choice(NOMBRES["apellidos"])
        self.edad     = random.randint(19, 54)

        # Identificador único de partida — directorio de bitácoras
        self.partida_id = _generar_partida_id(self.nombre, self.apellido)

        bg_key          = random.choice(list(BACKGROUNDS.keys()))
        self.bg_key     = bg_key
        self.background = BACKGROUNDS[bg_key]

        # ── STATS ─────────────────────────────────────────────
        self.stats: dict[str, int] = {k: v["min"] + 2 for k, v in STATS.items()}
        for _ in range(18):
            k = random.choice(list(STATS.keys()))
            if self.stats[k] < STATS[k]["max"]:
                self.stats[k] += 1
        for k, b in self.background["bonus_stats"].items():
            if k in self.stats:
                self.stats[k] = min(STATS[k]["max"], self.stats[k] + b)

        # ── VITALES ───────────────────────────────────────────
        res       = self.stats.get("resistencia", 3)
        rp        = STATS["resistencia"].get("efectos_pasivos", {})
        self.salud_max   = int(VITALES["salud"]["base"] + res * rp.get("salud_max", 0))
        self.energia_max = int(VITALES["salud"].get("base", 40) + res * rp.get("energia_max", 0))
        self.salud    = self.salud_max
        self.energia  = self.energia_max
        self.hambre   = VITALES["hambre"]["base"]
        self.sed      = VITALES["sed"]["base"]
        self.fatiga   = VITALES["fatiga"]["base"]
        self.moral    = VITALES["moral"]["base"]
        self.radiacion = VITALES["radiacion"]["base"]

        # ── SKILLS ────────────────────────────────────────────
        self.skills: dict[str, int] = self._derivar_skills()
        for k, b in self.background["bonus_skills"].items():
            if k in self.skills:
                self.skills[k] = min(SKILLS[k]["max"], self.skills[k] + b)
        self.skills_xp: dict[str, int] = {k: 0 for k in self.skills}

        # ── RASGOS ────────────────────────────────────────────
        self.rasgos: list[str] = []
        for r in self.background.get("rasgos", []):
            self._aplicar_rasgo(r)

        # ── CONDICIONES ───────────────────────────────────────
        self.condiciones: list[Condicion] = []

        # ── INVENTARIO ────────────────────────────────────────
        fp = STATS["fuerza"].get("efectos_pasivos", {})
        self.peso_max: float = 10.0 + self.stats["fuerza"] * fp.get("carga_max", 2.0)
        self.inventario: list[dict] = []
        self._equipar_inicio()

        # ── CONTADORES ────────────────────────────────────────
        self.dia                      = 1
        self.hora                     = 8
        self.expediciones_completadas = 0
        self.infectados_eliminados    = 0
        self.bandidos_eliminados      = 0
        self.veces_en_peligro_critico = 0
        self.items_recolectados       = 0
        self.muertes_vistas           = 0
        self.expediciones_nocturnas   = 0
        self.usos_morfina             = 0
        self.libros_leidos            = 0
        self.veces_condicion_grave    = 0
        self.areas_visitadas: list[str]         = []
        self.info_areas: dict[str, dict]        = {}
        self.rasgos_en_progreso: dict[str, int] = {}

        # Buffer transiente — NO se persiste en el save
        self._progreso_skills_pendiente: list[str] = []

    # ─────────────────────────────────────────────────────────
    #  SKILLS
    # ─────────────────────────────────────────────────────────

    def _derivar_skills(self) -> dict[str, int]:
        return {
            k: max(0, min(d["max"], int(sum(self.stats.get(s, 0) * m for s, m in d["derivacion"]))))
            for k, d in SKILLS.items()
        }

    # ─────────────────────────────────────────────────────────
    #  XP
    # ─────────────────────────────────────────────────────────

    def ganar_xp_skill(self, skill_key: str, xp_base: int) -> None:
        if skill_key not in self.skills:
            return
        defn  = SKILLS.get(skill_key, {})
        s_max = defn.get("max", 100)
        if self.skills[skill_key] >= s_max:
            return
        mult = self.obtener_efecto_rasgo("xp_mult_global", 1.0)
        self.skills_xp[skill_key] = self.skills_xp.get(skill_key, 0) + max(1, int(xp_base * mult))
        while self.skills[skill_key] < s_max:
            nivel = self.skills[skill_key]
            xp_need = defn.get("xp_base", 10) + (nivel // 10) * defn.get("xp_incremento", 5)
            if self.skills_xp[skill_key] >= xp_need:
                self.skills_xp[skill_key] -= xp_need
                self.skills[skill_key]    += 1
                self._progreso_skills_pendiente.append(
                    f"{defn.get('icono','📈')} {defn['nombre']}  {nivel} → {nivel+1}"
                )
            else:
                break
        if self._progreso_skills_pendiente:
            self.evaluar_rasgos_nuevos()

    def recoger_progreso_skills(self) -> list[str]:
        msgs = self._progreso_skills_pendiente.copy()
        self._progreso_skills_pendiente.clear()
        return msgs

    # ─────────────────────────────────────────────────────────
    #  RASGOS
    # ─────────────────────────────────────────────────────────

    def _aplicar_rasgo(self, key: str) -> None:
        if key not in RASGOS or key in self.rasgos:
            return
        rasgo = RASGOS[key]
        if any(i in self.rasgos for i in rasgo.get("incompatible_con", [])):
            return
        self.rasgos.append(key)
        e = rasgo.get("efectos", {})
        for sk, b in e.get("skills", {}).items():
            if sk in self.skills:
                self.skills[sk] = min(100, self.skills[sk] + b)
        if "salud_max" in e:
            self.salud_max = max(10, self.salud_max + e["salud_max"])
            self.salud     = min(self.salud, self.salud_max)
        if "carga_max" in e:
            self.peso_max += e["carga_max"]

    def tiene_rasgo(self, key: str) -> bool:
        return key in self.rasgos

    def evaluar_rasgos_nuevos(self) -> None:
        for key, rasgo in RASGOS.items():
            if key in self.rasgos:
                continue
            adq = rasgo.get("adquisicion", {})
            if adq.get("tipo") != "acumulacion":
                continue
            if "skill" in adq:
                val = self.skills.get(adq["skill"], 0)
            elif "stat" in adq:
                val = self.stats.get(adq["stat"], 0)
            elif "contador" in adq:
                val = getattr(self, adq["contador"], 0)
            elif "item_usado" in adq:
                val = self.usos_morfina if adq["item_usado"] == "morfina" else 0
            else:
                continue
            if val >= adq["umbral"]:
                self._aplicar_rasgo(key)

    def obtener_efecto_rasgo(self, clave: str, default=None):
        for key in self.rasgos:
            e = RASGOS.get(key, {}).get("efectos", {})
            if clave in e:
                return e[clave]
        return default

    def modificador_skill_en_contexto(self, skill: str, contexto: str) -> int:
        clave = f"skills_en_{contexto}"
        return sum(RASGOS.get(k, {}).get("efectos", {}).get(clave, {}).get(skill, 0)
                   for k in self.rasgos)

    def tiene_inmunidad(self, tipo: str) -> bool:
        return bool(self.obtener_efecto_rasgo(f"inmune_{tipo}", False))

    def tick_dependencias(self) -> list[str]:
        msgs = []
        for key in self.rasgos:
            e = RASGOS.get(key, {}).get("efectos", {})
            dep = e.get("dependencia_item")
            if not dep:
                continue
            nombre = ITEMS.get(dep, {}).get("nombre", dep.capitalize())
            if not self.tiene_item(nombre):
                delta = e.get("penalizacion_sin_item", {}).get("stats_global", 0)
                if delta:
                    for sk in self.stats:
                        self.stats[sk] = max(1, self.stats[sk] + delta)
                    msgs.append(f"⚠ Abstinencia ({RASGOS[key]['nombre']}): stats {delta:+d}")
        return msgs

    # ─────────────────────────────────────────────────────────
    #  INVENTARIO
    # ─────────────────────────────────────────────────────────

    def _equipar_inicio(self) -> None:
        for ref in self.background.get("items_inicio", []):
            key = ref.get("ref")
            if key and key in ITEMS:
                item = copy.deepcopy(ITEMS[key])
                for campo in ("nombre", "tipo", "peso", "desc"):
                    if campo in ref:
                        item[campo] = ref[campo]
                if "cantidad_override" in ref:
                    item["cantidad"] = ref["cantidad_override"]
                self.inventario.append(item)
            elif "nombre" in ref:
                self.inventario.append(copy.deepcopy(ref))

    def peso_actual(self) -> float:
        return round(sum(i.get("peso", 0) for i in self.inventario), 2)

    def puede_cargar(self, item: dict) -> bool:
        return self.peso_actual() + item.get("peso", 0) <= self.peso_max

    def _es_stackable(self, item: dict) -> bool:
        """
        Un ítem es apilable si no tiene 'usos' individuales
        y su tipo está en los tipos stackables.
        """
        if "usos" in item:
            return False
        return "cantidad" in item or item.get("tipo", "") in _TIPOS_STACKABLES

    def añadir_item(self, item: dict) -> bool:
        if not self.puede_cargar(item):
            return False
        if self._es_stackable(item):
            nombre = item.get("nombre")
            for existing in self.inventario:
                if existing.get("nombre") == nombre and self._es_stackable(existing):
                    existing["cantidad"] = existing.get("cantidad", 1) + item.get("cantidad", 1)
                    return True
            nuevo = copy.deepcopy(item)
            if "cantidad" not in nuevo:
                nuevo["cantidad"] = 1
            self.inventario.append(nuevo)
            return True
        self.inventario.append(copy.deepcopy(item))
        return True

    def tiene_item(self, nombre: str) -> bool:
        return any(i.get("nombre") == nombre for i in self.inventario)

    def obtener_item(self, nombre: str) -> dict | None:
        return next((i for i in self.inventario if i.get("nombre") == nombre), None)

    def obtener_item_por_id(self, idx_1: int) -> dict | None:
        """Retorna el ítem por ID 1-based mostrado en el inventario."""
        if 1 <= idx_1 <= len(self.inventario):
            return self.inventario[idx_1 - 1]
        return None

    def remover_item(self, nombre: str, cantidad: int = 1) -> bool:
        for i, item in enumerate(self.inventario):
            if item.get("nombre") == nombre:
                if item.get("cantidad", 1) > cantidad:
                    item["cantidad"] -= cantidad
                else:
                    self.inventario.pop(i)
                return True
        return False

    def descartar_por_id(self, idx_1: int) -> tuple[bool, str]:
        """Descarta el ítem completo por ID 1-based."""
        if 1 <= idx_1 <= len(self.inventario):
            nombre = self.inventario.pop(idx_1 - 1)["nombre"]
            return True, nombre
        return False, "ID inválido"

    def usar_item(self, nombre: str) -> tuple[bool, str]:
        item = self.obtener_item(nombre)
        if not item:
            return False, f"No tienes '{nombre}'"
        return self._aplicar_efectos_item(item)

    def usar_item_por_id(self, idx_1: int) -> tuple[bool, str]:
        """Usa el ítem por ID 1-based."""
        item = self.obtener_item_por_id(idx_1)
        if not item:
            return False, "ID inválido"
        return self._aplicar_efectos_item(item)

    def _aplicar_efectos_item(self, item: dict) -> tuple[bool, str]:
        efectos  = item.get("efectos", {})
        msgs: list[str] = []
        mult_med = self.obtener_efecto_rasgo("multiplicador_medicina", 1.0)

        if "salud" in efectos:
            ganado = int(min(efectos["salud"] * mult_med, self.salud_max - self.salud))
            self.salud += ganado
            msgs.append(f"+{ganado} Salud")

        if "hambre" in efectos:
            mult_h = self.obtener_efecto_rasgo("multiplicador_consumo_hambre", 1.0)
            self.hambre = max(0, self.hambre + int(efectos["hambre"] / mult_h))
            msgs.append("Hambre reducida" if efectos["hambre"] < 0 else "Hambre aumentada")

        if "sed" in efectos:
            mult_s = self.obtener_efecto_rasgo("multiplicador_consumo_sed", 1.0)
            self.sed = max(0, self.sed + int(efectos["sed"] / mult_s))
            msgs.append("Sed reducida" if efectos["sed"] < 0 else "Sed aumentada")

        if "fatiga" in efectos:
            self.fatiga = max(0, self.fatiga + efectos["fatiga"])
            msgs.append("Fatiga reducida" if efectos["fatiga"] < 0 else "Fatiga aumentada")

        if "condicion_remove" in efectos:
            self._reducir_condicion(efectos["condicion_remove"])
            msgs.append(f"Tratando {efectos['condicion_remove']}")

        if "skill_xp" in efectos:
            mult_libro = self.obtener_efecto_rasgo("xp_mult_libro", 1.0)
            for sk, xp in efectos["skill_xp"].items():
                self.ganar_xp_skill(sk, max(1, int(xp * mult_libro)))
            self.libros_leidos += 1
            msgs.append("Conocimiento adquirido")

        if item.get("nombre") == "Morfina":
            self.usos_morfina += 1

        # Consumir ítem
        if "usos" in item:
            item["usos"] -= 1
            if item["usos"] <= 0:
                self.inventario.remove(item)
        elif "cantidad" in item:
            item["cantidad"] -= 1
            if item["cantidad"] <= 0:
                self.inventario.remove(item)
        else:
            self.inventario.remove(item)

        self.evaluar_rasgos_nuevos()
        return True, " | ".join(msgs) if msgs else "Sin efecto notable"

    def arma_equipada(self) -> dict | None:
        armas = [i for i in self.inventario
                 if i.get("tipo") in ("arma_contundente", "arma_cortante",
                                       "arma_fuego", "arma_arrojadiza")]
        return max(armas, key=lambda a: sum(a.get("daño", (1, 3))) / 2) if armas else None

    def defensa_total(self) -> int:
        return sum(i.get("defensa", 0) for i in self.inventario
                   if i.get("tipo") in ("armadura", "casco"))

    def listar_inventario(self) -> list[str]:
        """Líneas formateadas con ID visible para interacción por comandos."""
        if not self.inventario:
            return ["  (vacío)"]
        return [_linea_item(item, idx + 1) for idx, item in enumerate(self.inventario)]

    def info_item(self, idx_1: int) -> dict | None:
        """Dict enriquecido para la pantalla de inspección."""
        item = self.obtener_item_por_id(idx_1)
        return _info_completa(item, self) if item else None

    # ─────────────────────────────────────────────────────────
    #  CONDICIONES
    # ─────────────────────────────────────────────────────────

    def añadir_condicion(self, c: Condicion) -> None:
        if not any(x.clave == c.clave for x in self.condiciones):
            self.condiciones.append(c)
            if c.severidad >= 3:
                self.veces_condicion_grave += 1
                self.evaluar_rasgos_nuevos()

    def _reducir_condicion(self, clave: str) -> None:
        for c in self.condiciones:
            if c.clave == clave:
                c.severidad -= 1
                if c.severidad <= 0:
                    self.condiciones.remove(c)
                return

    def tick_condiciones(self) -> None:
        activas = []
        for c in self.condiciones:
            if c.tick():
                if "daño_por_turno" in c.efectos:
                    self.salud = max(0, self.salud - c.efectos["daño_por_turno"])
                activas.append(c)
        self.condiciones = activas

    # ─────────────────────────────────────────────────────────
    #  CHECKS Y MODIFICADORES
    # ─────────────────────────────────────────────────────────

    def modificador_global(self) -> int:
        mod = 0
        if self.hambre > VITALES["hambre"]["critico"]:      mod -= 1
        if self.hambre > 90:                                 mod -= 1
        if self.sed    > VITALES["sed"]["critico"]:         mod -= 1
        if self.sed    > 85:                                 mod -= 2
        if self.fatiga > VITALES["fatiga"]["critico"]:      mod -= 1
        if self.moral  < VITALES["moral"]["critico"]:       mod -= 1
        if self.radiacion > VITALES["radiacion"]["critico"]: mod -= 1
        mod = int(mod * self.obtener_efecto_rasgo("penalizacion_presion_mult", 1.0))
        for c in self.condiciones:
            mod += c.efectos.get("stats_global", 0)
        return mod

    def check_stat(self, stat: str, dificultad: int) -> bool:
        valor  = self.stats.get(stat, 3) + self.modificador_global()
        tirada = random.randint(1, 10) - (self.stats.get("suerte", 5) - 5) // 3
        return tirada <= valor - (dificultad - 5)

    def check_skill(self, skill: str, dificultad: int = 50,
                    contexto: str = "") -> bool:
        valor = self.skills.get(skill, 20) + self.modificador_global() * 5
        if self.tiene_rasgo("especialista") and valor > 70:
            valor += self.obtener_efecto_rasgo("bonus_check_experto", 0)
        if contexto:
            valor += self.modificador_skill_en_contexto(skill, contexto)
        return random.randint(1, 100) <= valor - (dificultad - 50)

    def multiplicador_loot(self) -> float:
        base = (self.stats.get("percepcion", 3) + self.stats.get("suerte", 3)) / 20.0
        sb   = self.skills.get("saqueo", 20) / 200.0
        sp   = self.stats.get("suerte", 3) * STATS["suerte"].get("efectos_pasivos", {}).get("loot_bonus", 0.05)
        return min(2.0, base + sb + sp + random.uniform(0, 0.2))

    # ─────────────────────────────────────────────────────────
    #  DAÑO / CURACIÓN / TIEMPO
    # ─────────────────────────────────────────────────────────

    def recibir_daño(self, cantidad: int) -> int:
        real = max(1, cantidad - self.defensa_total())
        self.salud = max(0, self.salud - real)
        if self.salud <= self.salud_max * 0.20:
            self.veces_en_peligro_critico += 1
            self.evaluar_rasgos_nuevos()
        return real

    def esta_vivo(self) -> bool:
        return self.salud > 0

    def estado_salud_texto(self) -> str:
        pct = self.salud / self.salud_max * 100
        if pct >= 80: return "Excelente"
        if pct >= 60: return "Buena"
        if pct >= 40: return "Regular"
        if pct >= 20: return "Crítica"
        return "Agonizante"

    def pasar_tiempo(self, horas: float = 1.0) -> None:
        mh = self.obtener_efecto_rasgo("multiplicador_consumo_hambre", 1.0)
        ms = self.obtener_efecto_rasgo("multiplicador_consumo_sed", 1.0)
        hd, sd, fd = VITALES["hambre"], VITALES["sed"], VITALES["fatiga"]
        self.hambre = min(100, self.hambre + int(random.uniform(*hd["subida_hora"]) * horas * mh))
        self.sed    = min(100, self.sed    + int(random.uniform(*sd["subida_hora"]) * horas * ms))
        self.fatiga = min(100, self.fatiga + int(random.uniform(*fd["subida_hora"]) * horas))
        if self.hambre >= 95:
            self.salud = max(0, self.salud - int(hd.get("daño_critico", 3) * horas))
        if self.sed >= 90:
            self.salud = max(0, self.salud - int(sd.get("daño_critico", 8) * horas))
        if self.radiacion >= VITALES["radiacion"]["critico"]:
            self.salud = max(0, self.salud - int(VITALES["radiacion"].get("daño_critico", 5) * horas))
        if self.hambre < 30 and self.sed < 30 and self.salud < self.salud_max:
            self.salud = min(self.salud_max, self.salud + 1)
        self.hora = (self.hora + int(horas)) % 24
        if self.hora < int(horas):
            self.dia += 1
        self.tick_condiciones()

    # ─────────────────────────────────────────────────────────
    #  SERIALIZACIÓN
    # ─────────────────────────────────────────────────────────

    def a_dict(self) -> dict:
        return {
            "partida_id":               self.partida_id,
            "nombre":                   self.nombre,
            "apellido":                 self.apellido,
            "genero":                   self.genero,
            "edad":                     self.edad,
            "bg_key":                   self.bg_key,
            "stats":                    self.stats,
            "skills":                   self.skills,
            "skills_xp":                self.skills_xp,
            "rasgos":                   self.rasgos,
            "salud":                    self.salud,
            "salud_max":                self.salud_max,
            "energia":                  self.energia,
            "energia_max":              self.energia_max,
            "hambre":                   self.hambre,
            "sed":                      self.sed,
            "fatiga":                   self.fatiga,
            "moral":                    self.moral,
            "radiacion":                self.radiacion,
            "condiciones": [
                {"clave": c.clave, "nombre": c.nombre, "severidad": c.severidad,
                 "duracion": c.duracion, "efectos": c.efectos, "turnos_rest": c.turnos_rest}
                for c in self.condiciones
            ],
            "inventario":               self.inventario,
            "peso_max":                 self.peso_max,
            "dia":                      self.dia,
            "hora":                     self.hora,
            "expediciones_completadas": self.expediciones_completadas,
            "infectados_eliminados":    self.infectados_eliminados,
            "bandidos_eliminados":      self.bandidos_eliminados,
            "veces_en_peligro_critico": self.veces_en_peligro_critico,
            "items_recolectados":       self.items_recolectados,
            "muertes_vistas":           self.muertes_vistas,
            "expediciones_nocturnas":   self.expediciones_nocturnas,
            "usos_morfina":             self.usos_morfina,
            "libros_leidos":            self.libros_leidos,
            "veces_condicion_grave":    self.veces_condicion_grave,
            "areas_visitadas":          self.areas_visitadas,
            "info_areas":               self.info_areas,
            "rasgos_en_progreso":       self.rasgos_en_progreso,
        }

    @classmethod
    def desde_dict(cls, data: dict) -> "Sobreviviente":
        p = cls.__new__(cls)
        p.partida_id = data.get("partida_id") or _generar_partida_id(
            data.get("nombre", "survivor"), data.get("apellido", "unknown")
        )
        p.nombre     = data["nombre"]
        p.apellido   = data["apellido"]
        p.genero     = data["genero"]
        p.edad       = data["edad"]
        p.bg_key     = data.get("bg_key", list(BACKGROUNDS.keys())[0])
        p.background = BACKGROUNDS[p.bg_key]
        p.stats      = data["stats"]
        p.skills     = data["skills"]
        p.skills_xp  = data.get("skills_xp", {k: 0 for k in p.skills})
        p.rasgos     = data.get("rasgos", [])
        p.salud      = data["salud"]
        p.salud_max  = data["salud_max"]
        p.energia    = data.get("energia", data["salud_max"])
        p.energia_max = data.get("energia_max", data["salud_max"])
        p.hambre     = data["hambre"]
        p.sed        = data["sed"]
        p.fatiga     = data["fatiga"]
        p.moral      = data["moral"]
        p.radiacion  = data["radiacion"]
        p.condiciones = []
        for cd in data.get("condiciones", []):
            c = Condicion(cd["clave"], cd["nombre"], cd["severidad"],
                          cd["duracion"], cd["efectos"])
            c.turnos_rest = cd["turnos_rest"]
            p.condiciones.append(c)
        p.inventario   = data.get("inventario", [])
        p.peso_max     = data.get("peso_max", 20)
        p.dia          = data.get("dia", 1)
        p.hora         = data.get("hora", 8)
        p.expediciones_completadas = data.get("expediciones_completadas", 0)
        p.infectados_eliminados    = data.get("infectados_eliminados", 0)
        p.bandidos_eliminados      = data.get("bandidos_eliminados", 0)
        p.veces_en_peligro_critico = data.get("veces_en_peligro_critico", 0)
        p.items_recolectados       = data.get("items_recolectados", 0)
        p.muertes_vistas           = data.get("muertes_vistas", 0)
        p.expediciones_nocturnas   = data.get("expediciones_nocturnas", 0)
        p.usos_morfina             = data.get("usos_morfina", 0)
        p.libros_leidos            = data.get("libros_leidos", 0)
        p.veces_condicion_grave    = data.get("veces_condicion_grave", 0)
        p.areas_visitadas          = data.get("areas_visitadas", [])
        p.info_areas               = data.get("info_areas", {})
        p.rasgos_en_progreso       = data.get("rasgos_en_progreso", {})
        p._progreso_skills_pendiente = []
        return p

    # ─────────────────────────────────────────────────────────
    #  REPRESENTACIÓN
    # ─────────────────────────────────────────────────────────

    def barra(self, v: int, m: int, w: int = 12) -> str:
        ll = int((v / max(1, m)) * w)
        return f"[{'█'*ll}{'░'*(w-ll)}]"

    def __str__(self) -> str:
        sexo = "♂" if self.genero == "Masculino" else "♀"
        ls   = [
            f"┌─ {self.nombre} {self.apellido} {sexo}  {self.edad}a  {self.background['nombre']}",
            f"│ Salud    {self.barra(self.salud, self.salud_max)} {self.salud}/{self.salud_max} ({self.estado_salud_texto()})",
            f"│ Hambre   {self.barra(self.hambre, 100)} {self.hambre}/100",
            f"│ Sed      {self.barra(self.sed, 100)} {self.sed}/100",
            f"│ Fatiga   {self.barra(self.fatiga, 100)} {self.fatiga}/100",
            f"│ Moral    {self.barra(self.moral, 100)} {self.moral}/100",
        ]
        if self.radiacion > 0:
            ls.append(f"│ Radiación {self.barra(self.radiacion, 100)} {self.radiacion}/100 ☢")
        if self.condiciones:
            ls.append(f"│ Condiciones: {', '.join(str(c) for c in self.condiciones)}")
        if self.rasgos:
            ls.append(f"│ Rasgos: {', '.join(RASGOS[r]['nombre'] for r in self.rasgos if r in RASGOS)}")
        ls.append(f"│ Día {self.dia} — {self.hora:02d}:00hs  | Carga {self.peso_actual():.1f}/{self.peso_max}kg")
        ls.append("└" + "─" * 55)
        return "\n".join(ls)


# ──────────────────────────────────────────────────────────────
#  HELPERS DE PRESENTACIÓN DE ÍTEMS (usados por main.py)
# ──────────────────────────────────────────────────────────────

def _icono_item(item: dict) -> str:
    return _ICONOS_TIPO.get(item.get("tipo", ""), "·")


def _qty_str(item: dict) -> str:
    if "cantidad" in item:
        n = item["cantidad"]
        return f"×{n}" if n != 1 else "×1"
    if "usos" in item:
        return f"{item['usos']}u"
    if "durabilidad" in item:
        return f"{item['durabilidad']}%"
    return "  —"


def _linea_item(item: dict, idx: int) -> str:
    icono  = _icono_item(item)
    nombre = item.get("nombre", "?")[:28]
    qty    = _qty_str(item)
    peso   = item.get("peso", 0)
    return f"{idx:3d}  {icono} {nombre:<29} {qty:>5}   {peso:.1f}kg"


def _info_completa(item: dict, personaje) -> dict:
    """Construye un dict rico para la pantalla de inspección de ítem."""
    efectos = item.get("efectos", {})
    lineas  = []

    if "salud" in efectos:
        mult = personaje.obtener_efecto_rasgo("multiplicador_medicina", 1.0)
        v    = int(efectos["salud"] * mult)
        suf  = "  ✦ rasgo médico activo" if mult > 1 else ""
        lineas.append(f"  Salud      +{v} hp{suf}")
    if "hambre" in efectos:
        lineas.append(f"  Hambre     {efectos['hambre']:+d}")
    if "sed" in efectos:
        lineas.append(f"  Sed        {efectos['sed']:+d}")
    if "fatiga" in efectos:
        lineas.append(f"  Fatiga     {efectos['fatiga']:+d}")
    if "condicion_remove" in efectos:
        lineas.append(f"  Trata      {efectos['condicion_remove']}")
    if "skill_xp" in efectos:
        for sk, xp in efectos["skill_xp"].items():
            mult_l = personaje.obtener_efecto_rasgo("xp_mult_libro", 1.0)
            v2     = int(xp * mult_l)
            lineas.append(f"  XP {sk:<12} +{v2}")
    if "defensa" in item:
        lineas.append(f"  Defensa    +{item['defensa']}")
    if item.get("tipo") in ("arma_fuego", "arma_cortante", "arma_contundente"):
        daño = item.get("daño", (0, 0))
        lineas.append(f"  Daño       {daño[0]}-{daño[1]}")

    return {
        "nombre":   item.get("nombre", "?"),
        "tipo":     item.get("tipo", "—"),
        "icono":    _icono_item(item),
        "peso":     item.get("peso", 0),
        "desc":     item.get("desc", "Sin descripción."),
        "qty_str":  _qty_str(item),
        "efectos":  lineas,
        "usable":   bool(efectos),
    }
