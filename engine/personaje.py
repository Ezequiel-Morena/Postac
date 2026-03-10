# ============================================================
# engine/personaje.py
# Motor del personaje — lee todo desde data/, sin datos hardcodeados.
# Mixins: SkillsMixin (skills_mixin.py), InventoryMixin (inventory_mixin.py)
# ============================================================
import random
import copy
import re
from datetime import datetime

from data.stats      import STATS, VITALES
from data.skills     import SKILLS
from data.condiciones_medicas import CONDICIONES_CRONICAS, PREDISPOSICION_POR_BACKGROUND
from data.rasgos     import RASGOS
from data.items      import ITEMS
from data.personajes import NOMBRES, BACKGROUNDS
from engine.constants import clamp
from engine.medical_system import (
    aplicar_condicion_a_cuerpo,
    asegurar_estado_cuerpo,
    estado_cuerpo_base,
    aplicar_condiciones_cronicas_tick,
    tick_medico,
    evaluar_adquisicion_condiciones,
)
from engine.relaciones import estado_relaciones_refugio_base, normalizar_relaciones_guardadas
from engine.skills_mixin import SkillsMixin
from engine.inventory_mixin import (
    InventoryMixin,
    TIPOS_STACKABLES, ICONOS_TIPO, CATEGORIAS_INVENTARIO,
    CATEGORIA_FALLBACK,
    icono_item, categoria_item, qty_str, linea_item, info_completa,
)

# ── Compatibilidad: re-exportar con nombres originales ────────
_TIPOS_STACKABLES = TIPOS_STACKABLES
_ICONOS_TIPO = ICONOS_TIPO
_CATEGORIAS_INVENTARIO = CATEGORIAS_INVENTARIO
_CATEGORIA_FALLBACK = CATEGORIA_FALLBACK
_icono_item = icono_item
_categoria_item = categoria_item
_qty_str = qty_str
_linea_item = linea_item
_info_completa = info_completa


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


class Sobreviviente(SkillsMixin, InventoryMixin):
    """
    Personaje completamente data-driven.
    Todos los stats, skills y rasgos se construyen desde los archivos data/.
    Skills en SkillsMixin, inventario/ítems/armas/crafteo en InventoryMixin.
    """

    def __init__(self):
        # ── IDENTIDAD ─────────────────────────────────────────
        self.genero   = random.choice(["Masculino", "Femenino"])
        pool          = NOMBRES["masculino" if self.genero == "Masculino" else "femenino"]
        self.nombre   = random.choice(pool)
        self.apellido = random.choice(NOMBRES["apellidos"])
        self.edad     = random.randint(19, 54)
        self.edad_inicio: int = self.edad  # inmutable — edad al inicio de partida

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
        self.especialidades_desbloqueadas: dict[str, list[str]] = {k: [] for k in self.skills}

        # ── RASGOS ────────────────────────────────────────────
        self.rasgos: list[str] = []
        for r in self.background.get("rasgos", []):
            self._aplicar_rasgo(r)

        # ── CONDICIONES ───────────────────────────────────────
        self.condiciones: list[Condicion] = []

        # ── SISTEMA MÉDICO MODULAR ───────────────────────────
        self.cuerpo: dict[str, dict] = estado_cuerpo_base()
        self.farmaco_carga: float = 0.0
        self.historial_farmacos: list[dict] = []
        self.condiciones_cronicas: list[dict] = []
        self._log_medico_pendiente: list[str] = []
        self._inicializar_condiciones_cronicas()

        # ── INVENTARIO ────────────────────────────────────────
        fp = STATS["fuerza"].get("efectos_pasivos", {})
        self.peso_max: float = 10.0 + self.stats["fuerza"] * fp.get("carga_max", 2.0)
        self.inventario: list[dict] = []
        self._equipar_inicio()
        self._recalcular_especialidades()

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
        self.relaciones_refugio: dict[str, dict] = estado_relaciones_refugio_base()
        # Árbol genealógico: {npc_id: {tipo, nombre, apellido}}
        self.familia: dict[str, dict] = {}
        # Animales domésticos del refugio
        self.animales_refugio: list[dict] = []
        # Registro de penalizaciones de envejecimiento ya aplicadas (por umbral)
        self.penalizaciones_envejecimiento: list[int] = []
        # Almacén compartido del refugio (ilimitado)
        self.almacen: list = []
        # Estado del fuego del refugio
        self.fuego_activo: bool = False
        self.combustible_restante: int = 0
        self.temperatura_refugio: float = 18.0
        self.trampas_activas: list = []

        # Buffer transiente — NO se persiste en el save
        self._progreso_skills_pendiente: list[str] = []

    # ─────────────────────────────────────────────────────────
    #  CONDICIONES CRÓNICAS
    # ─────────────────────────────────────────────────────────

    def _inicializar_condiciones_cronicas(self) -> None:
        self.condiciones_cronicas = []

        for key, defn in CONDICIONES_CRONICAS.items():
            if random.random() <= float(defn.get("prob_hereditaria", 0.0)):
                self.condiciones_cronicas.append(
                    {
                        "clave": key,
                        "nombre": defn.get("nombre", key),
                        "origen": defn.get("origen_default", "hereditaria"),
                        "severidad": int(defn.get("severidad_base", 1)),
                        "efectos": dict(defn.get("efectos", {})),
                    }
                )

        for regla in PREDISPOSICION_POR_BACKGROUND.get(self.bg_key, []):
            key = regla.get("condicion")
            if key not in CONDICIONES_CRONICAS:
                continue
            if any(c.get("clave") == key for c in self.condiciones_cronicas):
                continue
            if random.random() > float(regla.get("prob", 0.0)):
                continue
            defn = CONDICIONES_CRONICAS[key]
            self.condiciones_cronicas.append(
                {
                    "clave": key,
                    "nombre": defn.get("nombre", key),
                    "origen": regla.get("origen", "adquirida"),
                    "severidad": int(defn.get("severidad_base", 1)),
                    "efectos": dict(defn.get("efectos", {})),
                }
            )

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
    #  CONDICIONES
    # ─────────────────────────────────────────────────────────

    def añadir_condicion(self, c: Condicion) -> None:
        if not any(x.clave == c.clave for x in self.condiciones):
            self.condiciones.append(c)
            self._log_medico_pendiente.extend(aplicar_condicion_a_cuerpo(self, c))
            if c.severidad >= 3:
                self.veces_condicion_grave += 1
                self.evaluar_rasgos_nuevos()

    def _reducir_condicion(self, clave: str) -> bool:
        for c in self.condiciones:
            if c.clave == clave:
                c.severidad -= 1
                if c.severidad <= 0:
                    self.condiciones.remove(c)
                return True
        return False

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
        valor += self.bonus_especialidades(skill, contexto)
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
        self._log_medico_pendiente.extend(aplicar_condiciones_cronicas_tick(self, horas))
        self._log_medico_pendiente.extend(tick_medico(self, horas))

    def recoger_log_medico(self) -> list[str]:
        msgs = self._log_medico_pendiente.copy()
        self._log_medico_pendiente.clear()
        return msgs

    # ─────────────────────────────────────────────────────────
    #  ENVEJECIMIENTO
    # ─────────────────────────────────────────────────────────

    # Umbrales de edad → (stat, penalidad, mensaje narrativo)
    _PENALIZACIONES_EDAD: dict[int, list[tuple[str, int, str]]] = {
        50: [("fuerza",     -1, "Los años pesan sobre tus articulaciones.")],
        55: [("resistencia",-1, "Tu cuerpo ya no se recupera tan rápido.")],
        60: [("fuerza",     -1, "La vejez cobra su precio en músculo."),
             ("destreza",   -1, "Tus reflejos ya no son lo que eran.")],
        65: [("resistencia",-1, "El esfuerzo prolongado te cuesta más."),
             ("percepcion", -1, "La vista y el oído van perdiendo filo.")],
        70: [("fuerza",     -1, "El cuerpo ya no aguanta como antes."),
             ("inteligencia", -1, "La memoria empieza a fallar en pequeñas cosas.")],
        75: [("resistencia",-1, "Solo la voluntad te mantiene en pie."),
             ("destreza",   -1, "Los movimientos rápidos son cosa del pasado.")],
        80: [("fuerza",     -2, "El cuerpo exige descanso que ya nunca basta."),
             ("suerte",     -1, "Los años acumulan más sombra que luz.")],
    }

    def tick_envejecimiento(self) -> list[str]:
        """
        Calcula si el personaje cumplió años desde el último tick.
        Aplica penalizaciones de stat por umbrales de edad.
        Retorna mensajes narrativos de los eventos de envejecimiento.
        """
        nueva_edad = self.edad_inicio + self.dia // 365
        if nueva_edad <= self.edad:
            return []

        msgs: list[str] = []
        for ano in range(self.edad + 1, nueva_edad + 1):
            msgs.append(f"🎂 Cumples {ano} años. El tiempo sigue su marcha implacable.")
            # Reducir salud máxima gradualmente a partir de los 60
            if ano >= 60 and ano % 5 == 0:
                reduccion = 5
                self.salud_max = max(40, self.salud_max - reduccion)
                self.salud = min(self.salud, self.salud_max)
                msgs.append(f"  Tu cuerpo acusa los años: salud máxima -{reduccion}.")
            # Penalizaciones de stats por umbrales
            if ano in self._PENALIZACIONES_EDAD and ano not in self.penalizaciones_envejecimiento:
                for stat, delta, mensaje in self._PENALIZACIONES_EDAD[ano]:
                    if stat in self.stats:
                        self.stats[stat] = max(1, self.stats[stat] + delta)
                        msgs.append(f"  {mensaje}")
                self.penalizaciones_envejecimiento.append(ano)

        self.edad = nueva_edad

        # Muerte natural: probabilidad acumulativa a partir de los 70
        if self.edad >= 70:
            prob_muerte = max(0.0, (self.edad - 70) * 0.012)
            if random.random() < prob_muerte:
                self.salud = 0
                msgs.append(f"💀 A los {self.edad} años, el corazón cede. Muerte natural.")

        return msgs
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
            "cuerpo":                   self.cuerpo,
            "farmaco_carga":            self.farmaco_carga,
            "historial_farmacos":       self.historial_farmacos,
            "especialidades_desbloqueadas": self.especialidades_desbloqueadas,
            "condiciones_cronicas":     self.condiciones_cronicas,
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
            "relaciones_refugio":       self.relaciones_refugio,
            "familia":                  self.familia,
            "animales_refugio":         self.animales_refugio,
            "almacen":                   self.almacen,
            "fuego_activo":              self.fuego_activo,
            "combustible_restante":      self.combustible_restante,
            "temperatura_refugio":       self.temperatura_refugio,
            "trampas_activas":           self.trampas_activas,
            "edad_inicio":              self.edad_inicio,
            "penalizaciones_envejecimiento": self.penalizaciones_envejecimiento,
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
        p.cuerpo = asegurar_estado_cuerpo(data.get("cuerpo"))
        p.farmaco_carga = float(data.get("farmaco_carga", 0.0))
        p.historial_farmacos = list(data.get("historial_farmacos", []))
        p.especialidades_desbloqueadas = dict(data.get("especialidades_desbloqueadas", {}))
        p.condiciones_cronicas = list(data.get("condiciones_cronicas", []))
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
        p.relaciones_refugio = normalizar_relaciones_guardadas(data.get("relaciones_refugio"))
        p.familia = {
            k: v for k, v in data.get("familia", {}).items()
            if isinstance(v, dict)
        }
        p.animales_refugio = list(data.get("animales_refugio", []))
        p.almacen = list(data.get("almacen", []))
        p.fuego_activo         = data.get("fuego_activo", False)
        p.combustible_restante = data.get("combustible_restante", 0)
        p.temperatura_refugio  = data.get("temperatura_refugio", 18.0)
        p.trampas_activas      = list(data.get("trampas_activas", []))
        p.edad_inicio = data.get("edad_inicio", p.edad)
        p.penalizaciones_envejecimiento = list(data.get("penalizaciones_envejecimiento", []))
        p._progreso_skills_pendiente = []
        p._log_medico_pendiente = []
        p._recalcular_especialidades()
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
