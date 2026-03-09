# ============================================================
# engine/personaje.py
# Motor del personaje — lee todo desde data/, no tiene datos hardcodeados.
# ============================================================
import random
import copy

# Los datos viven en data/, la lógica aquí
from data.stats    import STATS, VITALES
from data.skills   import SKILLS
from data.rasgos   import RASGOS
from data.items    import ITEMS
from data.personajes import NOMBRES, BACKGROUNDS


class Condicion:
    """Estado temporal o permanente que afecta al personaje."""
    def __init__(self, clave: str, nombre: str, severidad: int,
                 duracion: int, efectos: dict, descripcion: str = ""):
        self.clave       = clave
        self.nombre      = nombre
        self.severidad   = severidad    # 1=leve 2=moderado 3=grave
        self.duracion    = duracion     # -1=permanente hasta tratar
        self.efectos     = efectos
        self.descripcion = descripcion
        self.turnos_rest = duracion

    def tick(self) -> bool:
        """Avanza un turno. Retorna True si sigue activa."""
        if self.duracion > 0:
            self.turnos_rest -= 1
        return self.turnos_rest > 0 or self.duracion == -1

    def __str__(self):
        sev = {1: "Leve", 2: "Moderado", 3: "Grave"}.get(self.severidad, "")
        return f"{self.nombre} ({sev})"


class Sobreviviente:
    """
    Personaje completamente data-driven.
    Todos los stats, skills y rasgos se construyen
    leyendo data/stats.py, data/skills.py y data/rasgos.py.
    """

    def __init__(self):
        # ── IDENTIDAD ─────────────────────────────────────────
        self.genero   = random.choice(["Masculino", "Femenino"])
        nombre_pool   = NOMBRES["masculino"] if self.genero == "Masculino" else NOMBRES["femenino"]
        self.nombre   = random.choice(nombre_pool)
        self.apellido = random.choice(NOMBRES["apellidos"])
        self.edad     = random.randint(19, 54)

        # Elegir background
        bg_key         = random.choice(list(BACKGROUNDS.keys()))
        self.bg_key    = bg_key
        self.background = BACKGROUNDS[bg_key]

        # ── STATS (construidas desde STATS) ───────────────────
        self.stats: dict[str, int] = {}
        for stat_key, defn in STATS.items():
            self.stats[stat_key] = defn["min"] + 2   # base = min+2
        # Distribuir puntos libres
        puntos = 18
        stat_keys = list(STATS.keys())
        for _ in range(puntos):
            k = random.choice(stat_keys)
            if self.stats[k] < STATS[k]["max"]:
                self.stats[k] += 1
        # Aplicar bonus del background
        for stat_key, bonus in self.background["bonus_stats"].items():
            if stat_key in self.stats:
                self.stats[stat_key] = min(STATS[stat_key]["max"],
                                            self.stats[stat_key] + bonus)

        # ── VITALES (construidos desde VITALES) ───────────────
        # Primero calcular salud máxima con bonus de Resistencia
        res_val     = self.stats.get("resistencia", 3)
        res_pasivos = STATS["resistencia"].get("efectos_pasivos", {})
        self.salud_max  = int(VITALES["salud"]["base"]
                               + res_val * res_pasivos.get("salud_max", 0))
        self.energia_max = int(VITALES["salud"].get("base", 40)
                                + res_val * res_pasivos.get("energia_max", 0))
        self.salud   = self.salud_max
        self.energia = self.energia_max

        # Medidores de supervivencia (empiezan en base)
        self.hambre   = VITALES["hambre"]["base"]
        self.sed      = VITALES["sed"]["base"]
        self.fatiga   = VITALES["fatiga"]["base"]
        self.moral    = VITALES["moral"]["base"]
        self.radiacion = VITALES["radiacion"]["base"]

        # ── SKILLS (derivadas desde SKILLS) ───────────────────
        self.skills: dict[str, int] = self._calcular_skills()
        # Aplicar bonus del background
        for skill_key, bonus in self.background["bonus_skills"].items():
            if skill_key in self.skills:
                self.skills[skill_key] = min(SKILLS[skill_key]["max"],
                                              self.skills[skill_key] + bonus)

        # ── RASGOS ────────────────────────────────────────────
        self.rasgos: list[str] = []
        # Asignar rasgos de background
        for rasgo_key in self.background.get("rasgos", []):
            self._aplicar_rasgo(rasgo_key)

        # ── CONDICIONES ───────────────────────────────────────
        self.condiciones: list[Condicion] = []

        # ── INVENTARIO ────────────────────────────────────────
        # Carga base desde Fuerza + efectos pasivos
        fuerza_pasivos = STATS["fuerza"].get("efectos_pasivos", {})
        self.peso_max: float = 10.0 + self.stats["fuerza"] * fuerza_pasivos.get("carga_max", 2.0)
        self.inventario: list[dict] = []
        self._equipar_items_inicio()

        # ── CONTADORES / HISTORIAL ────────────────────────────
        self.dia                       = 1
        self.hora                      = 8
        self.expediciones_completadas  = 0
        self.infectados_eliminados     = 0
        self.bandidos_eliminados       = 0
        self.veces_en_peligro_critico  = 0
        self.items_recolectados        = 0
        self.muertes_vistas            = 0
        self.expediciones_nocturnas    = 0
        self.usos_morfina              = 0
        self.areas_visitadas: list[str]       = []
        self.info_areas: dict[str, dict]      = {}
        self.rasgos_en_progreso: dict[str, int] = {}  # clave: contador actual

    # ─────────────────────────────────────────────────────────
    #  CONSTRUCCIÓN DE SKILLS
    # ─────────────────────────────────────────────────────────
    def _calcular_skills(self) -> dict[str, int]:
        """
        Deriva todas las skills definidas en data/skills.py
        usando las fórmulas declaradas en 'derivacion'.
        """
        resultado = {}
        for skill_key, defn in SKILLS.items():
            valor = sum(self.stats.get(stat, 0) * mult
                        for stat, mult in defn["derivacion"])
            resultado[skill_key] = max(0, min(defn["max"], int(valor)))
        return resultado

    # ─────────────────────────────────────────────────────────
    #  RASGOS
    # ─────────────────────────────────────────────────────────
    def _aplicar_rasgo(self, rasgo_key: str):
        if rasgo_key not in RASGOS:
            return
        if rasgo_key in self.rasgos:
            return

        rasgo = RASGOS[rasgo_key]
        # Verificar incompatibilidades
        for incompat in rasgo.get("incompatible_con", []):
            if incompat in self.rasgos:
                return

        self.rasgos.append(rasgo_key)
        efectos = rasgo.get("efectos", {})

        # Aplicar bonus de skills
        for skill_key, bonus in efectos.get("skills", {}).items():
            if skill_key in self.skills:
                self.skills[skill_key] = min(100, self.skills[skill_key] + bonus)

        # Aplicar bonus de salud máxima
        if "salud_max" in efectos:
            self.salud_max = max(10, self.salud_max + efectos["salud_max"])
            self.salud     = min(self.salud, self.salud_max)

        # Aplicar bonus de carga
        if "carga_max" in efectos:
            self.peso_max += efectos["carga_max"]

    def tiene_rasgo(self, rasgo_key: str) -> bool:
        return rasgo_key in self.rasgos

    def evaluar_rasgos_nuevos(self):
        """
        Revisa si algún rasgo se debe desbloquear por acumulación.
        Llamar después de expediciones y eventos importantes.
        """
        for rasgo_key, rasgo in RASGOS.items():
            if rasgo_key in self.rasgos:
                continue
            adq = rasgo.get("adquisicion", {})
            tipo = adq.get("tipo")

            if tipo == "acumulacion":
                if "skill" in adq:
                    valor_actual = self.skills.get(adq["skill"], 0)
                    if valor_actual >= adq["umbral"]:
                        self._aplicar_rasgo(rasgo_key)
                elif "stat" in adq:
                    valor_actual = self.stats.get(adq["stat"], 0)
                    if valor_actual >= adq["umbral"]:
                        self._aplicar_rasgo(rasgo_key)
                elif "contador" in adq:
                    valor_actual = getattr(self, adq["contador"], 0)
                    if valor_actual >= adq["umbral"]:
                        self._aplicar_rasgo(rasgo_key)
                elif "item_usado" in adq:
                    if adq["item_usado"] == "morfina":
                        if self.usos_morfina >= adq["umbral"]:
                            self._aplicar_rasgo(rasgo_key)

    def obtener_efecto_rasgo(self, clave_efecto: str, default=None):
        """Retorna el valor acumulado de un efecto de todos los rasgos activos."""
        for rasgo_key in self.rasgos:
            rasgo = RASGOS.get(rasgo_key, {})
            efectos = rasgo.get("efectos", {})
            if clave_efecto in efectos:
                return efectos[clave_efecto]
        return default

    # ─────────────────────────────────────────────────────────
    #  INVENTARIO
    # ─────────────────────────────────────────────────────────
    def _equipar_items_inicio(self):
        """Lee los items de inicio del background y los añade al inventario."""
        for item_ref in self.background.get("items_inicio", []):
            ref_key = item_ref.get("ref")
            if ref_key and ref_key in ITEMS:
                item = copy.deepcopy(ITEMS[ref_key])
                # Override de nombre/campos si el background lo especifica
                for campo in ("nombre", "tipo", "peso", "desc"):
                    if campo in item_ref:
                        item[campo] = item_ref[campo]
                if "cantidad_override" in item_ref:
                    item["cantidad"] = item_ref["cantidad_override"]
                self.inventario.append(item)
            elif "nombre" in item_ref:
                # Item personalizado que no está en ITEMS
                self.inventario.append(copy.deepcopy(item_ref))

    def peso_actual(self) -> float:
        return round(sum(i.get("peso", 0) for i in self.inventario), 2)

    def puede_cargar(self, item: dict) -> bool:
        return self.peso_actual() + item.get("peso", 0) <= self.peso_max

    def añadir_item(self, item: dict) -> bool:
        if not self.puede_cargar(item):
            return False
        # Apilar ítems stackables por nombre
        if "cantidad" in item:
            for inv_item in self.inventario:
                if inv_item.get("nombre") == item["nombre"] and "cantidad" in inv_item:
                    inv_item["cantidad"] += item.get("cantidad", 1)
                    return True
        self.inventario.append(copy.deepcopy(item))
        return True

    def tiene_item(self, nombre: str) -> bool:
        return any(i.get("nombre") == nombre for i in self.inventario)

    def obtener_item(self, nombre: str) -> dict | None:
        return next((i for i in self.inventario if i.get("nombre") == nombre), None)

    def remover_item(self, nombre: str, cantidad: int = 1) -> bool:
        for i, item in enumerate(self.inventario):
            if item.get("nombre") == nombre:
                if item.get("cantidad", 1) > cantidad:
                    item["cantidad"] -= cantidad
                else:
                    self.inventario.pop(i)
                return True
        return False

    def usar_item(self, nombre: str) -> tuple[bool, str]:
        item = self.obtener_item(nombre)
        if not item:
            return False, f"No tienes {nombre}"

        efectos = item.get("efectos", {})
        msgs = []

        # Multiplicador de rasgos médicos
        mult_med = self.obtener_efecto_rasgo("multiplicador_medicina", 1.0)

        if "salud" in efectos:
            ganado = int(min(efectos["salud"] * mult_med,
                              self.salud_max - self.salud))
            self.salud += ganado
            msgs.append(f"+{ganado} Salud")

        if "hambre" in efectos:
            # Multiplicador de metabolismo lento
            mult_ham = self.obtener_efecto_rasgo("multiplicador_consumo_hambre", 1.0)
            delta = int(efectos["hambre"] / mult_ham)
            self.hambre = max(0, self.hambre + delta)
            msgs.append("Hambre reducida" if efectos["hambre"] < 0 else "Hambre aumentada")

        if "sed" in efectos:
            mult_sed = self.obtener_efecto_rasgo("multiplicador_consumo_sed", 1.0)
            delta = int(efectos["sed"] / mult_sed)
            self.sed = max(0, self.sed + delta)
            msgs.append("Sed reducida" if efectos["sed"] < 0 else "Sed aumentada")

        if "fatiga" in efectos:
            self.fatiga = max(0, self.fatiga + efectos["fatiga"])
            msgs.append("Fatiga reducida" if efectos["fatiga"] < 0 else "Fatiga aumentada")

        if "condicion_remove" in efectos:
            self._reducir_condicion(efectos["condicion_remove"])
            msgs.append(f"Tratando {efectos['condicion_remove']}")

        if "skill_xp" in efectos:
            for skill_key, xp in efectos["skill_xp"].items():
                if skill_key in self.skills:
                    self.skills[skill_key] = min(100, self.skills[skill_key] + xp)
                    msgs.append(f"+{xp} {SKILLS[skill_key]['nombre']}")

        # Tracking especial
        if nombre == "Morfina":
            self.usos_morfina += 1

        # Consumir
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
        if not armas:
            return None
        return max(armas, key=lambda a: sum(a.get("daño", (1, 3))) / 2)

    def defensa_total(self) -> int:
        return sum(i.get("defensa", 0) for i in self.inventario
                   if i.get("tipo") in ("armadura", "casco"))

    def listar_inventario(self) -> list[str]:
        if not self.inventario:
            return ["(vacío)"]
        lineas = []
        for item in self.inventario:
            extras = []
            if item.get("cantidad", 1) > 1: extras.append(f"x{item['cantidad']}")
            if "usos" in item: extras.append(f"{item['usos']}u")
            if "durabilidad" in item: extras.append(f"dur:{item['durabilidad']}%")
            extras.append(f"{item.get('peso', 0)}kg")
            lineas.append(f"  {item['nombre']:<30} {' '.join(extras)}")
        return lineas

    # ─────────────────────────────────────────────────────────
    #  CONDICIONES
    # ─────────────────────────────────────────────────────────
    def añadir_condicion(self, condicion: Condicion):
        if not any(c.clave == condicion.clave for c in self.condiciones):
            self.condiciones.append(condicion)

    def _reducir_condicion(self, clave: str):
        for c in self.condiciones:
            if c.clave == clave:
                c.severidad -= 1
                if c.severidad <= 0:
                    self.condiciones.remove(c)
                return

    def tick_condiciones(self):
        activas = []
        for c in self.condiciones:
            if c.tick():
                if "daño_por_turno" in c.efectos:
                    self.salud = max(0, self.salud - c.efectos["daño_por_turno"])
                activas.append(c)
        self.condiciones = activas

    # ─────────────────────────────────────────────────────────
    #  MODIFICADORES Y CHECKS
    # ─────────────────────────────────────────────────────────
    def modificador_global(self) -> int:
        """Penalizador/bonus global calculado dinámicamente."""
        mod = 0
        # Hambre
        if self.hambre > VITALES["hambre"]["critico"]:    mod -= 1
        if self.hambre > 90:                               mod -= 1
        # Sed
        if self.sed > VITALES["sed"]["critico"]:          mod -= 1
        if self.sed > 85:                                  mod -= 2
        # Fatiga
        if self.fatiga > VITALES["fatiga"]["critico"]:    mod -= 1
        # Moral
        if self.moral < VITALES["moral"]["critico"]:      mod -= 1
        # Radiación
        if self.radiacion > VITALES["radiacion"]["critico"]: mod -= 1
        # Rasgo sangre fría: reduce penalizaciones
        mult = self.obtener_efecto_rasgo("penalizacion_presion_mult", 1.0)
        mod = int(mod * mult)
        # Condiciones activas
        for c in self.condiciones:
            mod += c.efectos.get("stats_global", 0)
        return mod

    def check_stat(self, stat: str, dificultad: int) -> bool:
        valor  = self.stats.get(stat, 3) + self.modificador_global()
        tirada = random.randint(1, 10)
        tirada -= (self.stats.get("suerte", 5) - 5) // 3
        return tirada <= valor - (dificultad - 5)

    def check_skill(self, skill: str, dificultad: int = 50) -> bool:
        valor  = self.skills.get(skill, 20) + self.modificador_global() * 5
        tirada = random.randint(1, 100)
        return tirada <= valor - (dificultad - 50)

    def multiplicador_loot(self) -> float:
        base        = (self.stats.get("percepcion", 3) + self.stats.get("suerte", 3)) / 20.0
        skill_bonus = self.skills.get("saqueo", 20) / 200.0
        # Rasgo ojos de águila ya está en saqueo; suerte pasiva
        suerte_pasivo = self.stats.get("suerte", 3) * STATS["suerte"].get(
            "efectos_pasivos", {}).get("loot_bonus", 0.05)
        return min(2.0, base + skill_bonus + suerte_pasivo + random.uniform(0, 0.2))

    # ─────────────────────────────────────────────────────────
    #  DAÑO Y CURACIÓN
    # ─────────────────────────────────────────────────────────
    def recibir_daño(self, cantidad: int) -> int:
        defensa   = self.defensa_total()
        daño_real = max(1, cantidad - defensa)
        self.salud = max(0, self.salud - daño_real)
        if self.salud <= self.salud_max * 0.20:
            self.veces_en_peligro_critico += 1
            self.evaluar_rasgos_nuevos()
        return daño_real

    def esta_vivo(self) -> bool:
        return self.salud > 0

    def estado_salud_texto(self) -> str:
        pct = self.salud / self.salud_max * 100
        if pct >= 80: return "Excelente"
        if pct >= 60: return "Buena"
        if pct >= 40: return "Regular"
        if pct >= 20: return "Crítica"
        return "Agonizante"

    # ─────────────────────────────────────────────────────────
    #  TIEMPO
    # ─────────────────────────────────────────────────────────
    def pasar_tiempo(self, horas: float = 1.0):
        # Multiplicadores de rasgos
        mult_ham = self.obtener_efecto_rasgo("multiplicador_consumo_hambre", 1.0)
        mult_sed = self.obtener_efecto_rasgo("multiplicador_consumo_sed", 1.0)

        h_def = VITALES["hambre"]
        s_def = VITALES["sed"]
        f_def = VITALES["fatiga"]

        subida_ham = int(random.uniform(*h_def["subida_hora"]) * horas * mult_ham)
        subida_sed = int(random.uniform(*s_def["subida_hora"]) * horas * mult_sed)
        subida_fat = int(random.uniform(*f_def["subida_hora"]) * horas)

        self.hambre    = min(100, self.hambre + subida_ham)
        self.sed       = min(100, self.sed    + subida_sed)
        self.fatiga    = min(100, self.fatiga + subida_fat)

        # Daño por inanición / deshidratación
        if self.hambre >= 95:
            self.salud = max(0, self.salud - int(h_def.get("daño_critico", 3) * horas))
        if self.sed >= 90:
            self.salud = max(0, self.salud - int(s_def.get("daño_critico", 8) * horas))
        if self.radiacion >= VITALES["radiacion"]["critico"]:
            self.salud = max(0, self.salud - int(VITALES["radiacion"].get("daño_critico", 5) * horas))

        # Curación natural lenta
        if self.hambre < 30 and self.sed < 30 and self.salud < self.salud_max:
            self.salud = min(self.salud_max, self.salud + int(1 * horas))

        # Moral decae si condiciones básicas mal
        if self.hambre > 75 or self.sed > 75:
            self.moral = max(0, self.moral - 3)

        # Avanzar reloj
        horas_int  = int(horas)
        self.hora  = (self.hora + horas_int) % 24
        if (self.hora) < horas_int:
            self.dia += 1

        # Tracking nocturno
        if self.hora >= 20 or self.hora <= 5:
            self.expediciones_nocturnas += 1

        self.tick_condiciones()
        self.evaluar_rasgos_nuevos()

    # ─────────────────────────────────────────────────────────
    #  SERIALIZACIÓN
    # ─────────────────────────────────────────────────────────
    def a_dict(self) -> dict:
        return {
            "nombre":    self.nombre,
            "apellido":  self.apellido,
            "genero":    self.genero,
            "edad":      self.edad,
            "bg_key":    self.bg_key,
            "stats":     self.stats,
            "skills":    self.skills,
            "rasgos":    self.rasgos,
            "salud":     self.salud,
            "salud_max": self.salud_max,
            "energia":   self.energia,
            "energia_max": self.energia_max,
            "hambre":    self.hambre,
            "sed":       self.sed,
            "fatiga":    self.fatiga,
            "moral":     self.moral,
            "radiacion": self.radiacion,
            "condiciones": [
                {"clave": c.clave, "nombre": c.nombre, "severidad": c.severidad,
                 "duracion": c.duracion, "efectos": c.efectos,
                 "turnos_rest": c.turnos_rest}
                for c in self.condiciones
            ],
            "inventario":    self.inventario,
            "peso_max":      self.peso_max,
            "dia":           self.dia,
            "hora":          self.hora,
            "expediciones_completadas":  self.expediciones_completadas,
            "infectados_eliminados":     self.infectados_eliminados,
            "bandidos_eliminados":       self.bandidos_eliminados,
            "veces_en_peligro_critico":  self.veces_en_peligro_critico,
            "items_recolectados":        self.items_recolectados,
            "muertes_vistas":            self.muertes_vistas,
            "expediciones_nocturnas":    self.expediciones_nocturnas,
            "usos_morfina":              self.usos_morfina,
            "areas_visitadas":           self.areas_visitadas,
            "info_areas":                self.info_areas,
            "rasgos_en_progreso":        self.rasgos_en_progreso,
        }

    @classmethod
    def desde_dict(cls, data: dict) -> "Sobreviviente":
        p = cls.__new__(cls)
        p.nombre    = data["nombre"]
        p.apellido  = data["apellido"]
        p.genero    = data["genero"]
        p.edad      = data["edad"]
        p.bg_key    = data.get("bg_key", list(BACKGROUNDS.keys())[0])
        p.background = BACKGROUNDS[p.bg_key]
        p.stats     = data["stats"]
        p.skills    = data["skills"]
        p.rasgos    = data.get("rasgos", [])
        p.salud     = data["salud"]
        p.salud_max = data["salud_max"]
        p.energia   = data["energia"]
        p.energia_max = data["energia_max"]
        p.hambre    = data["hambre"]
        p.sed       = data["sed"]
        p.fatiga    = data["fatiga"]
        p.moral     = data["moral"]
        p.radiacion = data["radiacion"]
        p.condiciones = []
        for cd in data.get("condiciones", []):
            c = Condicion(cd["clave"], cd["nombre"], cd["severidad"],
                          cd["duracion"], cd["efectos"])
            c.turnos_rest = cd["turnos_rest"]
            p.condiciones.append(c)
        p.inventario  = data.get("inventario", [])
        p.peso_max    = data.get("peso_max", 20)
        p.dia         = data.get("dia", 1)
        p.hora        = data.get("hora", 8)
        p.expediciones_completadas = data.get("expediciones_completadas", 0)
        p.infectados_eliminados    = data.get("infectados_eliminados", 0)
        p.bandidos_eliminados      = data.get("bandidos_eliminados", 0)
        p.veces_en_peligro_critico = data.get("veces_en_peligro_critico", 0)
        p.items_recolectados       = data.get("items_recolectados", 0)
        p.muertes_vistas           = data.get("muertes_vistas", 0)
        p.expediciones_nocturnas   = data.get("expediciones_nocturnas", 0)
        p.usos_morfina             = data.get("usos_morfina", 0)
        p.areas_visitadas          = data.get("areas_visitadas", [])
        p.info_areas               = data.get("info_areas", {})
        p.rasgos_en_progreso       = data.get("rasgos_en_progreso", {})
        return p

    # ─────────────────────────────────────────────────────────
    #  REPRESENTACIÓN
    # ─────────────────────────────────────────────────────────
    def barra(self, valor: int, maximo: int, ancho: int = 12) -> str:
        llenos = int((valor / max(1, maximo)) * ancho)
        return f"[{'█'*llenos}{'░'*(ancho-llenos)}]"

    def __str__(self) -> str:
        sexo = "♂" if self.genero == "Masculino" else "♀"
        bg   = self.background["nombre"]
        lineas = [
            f"┌─ {self.nombre} {self.apellido} {sexo}  {self.edad}a  {bg}",
            f"│ Salud    {self.barra(self.salud, self.salud_max)} "
            f"{self.salud}/{self.salud_max} ({self.estado_salud_texto()})",
            f"│ Hambre   {self.barra(self.hambre, 100)} {self.hambre}/100",
            f"│ Sed      {self.barra(self.sed, 100)} {self.sed}/100",
            f"│ Fatiga   {self.barra(self.fatiga, 100)} {self.fatiga}/100",
            f"│ Moral    {self.barra(self.moral, 100)} {self.moral}/100",
        ]
        if self.radiacion > 0:
            lineas.append(f"│ Radiación {self.barra(self.radiacion, 100)} {self.radiacion}/100 ☢")
        if self.condiciones:
            lineas.append(f"│ Condiciones: {', '.join(str(c) for c in self.condiciones)}")
        if self.rasgos:
            nombres_rasgos = [RASGOS[r]["nombre"] for r in self.rasgos if r in RASGOS]
            lineas.append(f"│ Rasgos: {', '.join(nombres_rasgos)}")
        lineas.append(f"│ Día {self.dia} — {self.hora:02d}:00hs  | "
                      f"Carga {self.peso_actual():.1f}/{self.peso_max}kg")
        lineas.append("└" + "─" * 55)
        return "\n".join(lineas)
