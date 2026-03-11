# ============================================================
# engine/inventory_mixin.py
# Mixin con toda la lógica de inventario, ítems, armas y crafteo.
# Extraído de personaje.py para reducir su tamaño.
# ============================================================
from __future__ import annotations

import copy
import random

from data.items    import ITEMS
from data.crafting import RECETAS
from data.skills   import SKILLS
from data.stats    import STATS
from engine.constants import clamp
from engine.medical_system import (
    procesar_uso_farmaco,
    adquirir_condicion_por_consumo,
)

# Tipos cuyas instancias se apilan por cantidad.
# Los ítems con 'usos' individuales NO son apilables.
TIPOS_STACKABLES = frozenset({"comida", "agua", "municion", "material", "misc"})

# Íconos por tipo de ítem
ICONOS_TIPO: dict[str, str] = {
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
    "material_especial": "🧪",
    "medicina_fuerte":  "💉",
    "purificacion":     "🫧",
    "herramienta_medica": "🩺",
}

CATEGORIAS_INVENTARIO: list[tuple[str, tuple[str, ...]]] = [
    ("Armas", ("arma_fuego", "arma_cortante", "arma_contundente", "arma_arrojadiza")),
    ("Armadura", ("armadura", "casco")),
    ("Medicina", ("medicina", "medicina_fuerte", "herramienta_medica")),
    ("Comida y Agua", ("comida", "agua", "agua_sucia")),
    ("Municion", ("municion",)),
    ("Herramientas", ("herramienta",)),
    ("Equipo", ("equipo", "equipo_especial")),
    ("Materiales", ("material", "material_especial")),
    ("Conocimiento", ("libro",)),
]

CATEGORIA_FALLBACK = "Otros"
_ORDEN_CATEGORIAS = {nombre: idx for idx, (nombre, _) in enumerate(CATEGORIAS_INVENTARIO)}
_ALIAS_FILTRO_INVENTARIO = {
    "arma": "armas",
    "armas": "armas",
    "armor": "armadura",
}


class InventoryMixin:
    """Métodos de inventario, ítems, armas y crafteo para Sobreviviente (mixin)."""

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

        # Equipar ropa de inicio directamente en ropa_equipada
        from data.vestimenta import PRENDAS
        for key in self.background.get("ropa_inicio", []):
            prenda = PRENDAS.get(key)
            if prenda:
                item = copy.deepcopy(ITEMS.get(key, prenda))
                item.setdefault("tipo", "vestimenta")
                item.setdefault("slot", prenda["slot"])
                item.setdefault("durabilidad", prenda.get("durabilidad_max", 100))
                self.ropa_equipada[prenda["slot"]] = item

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
        return "cantidad" in item or item.get("tipo", "") in TIPOS_STACKABLES

    def _consumir_uso_item(self, item: dict, cantidad: int = 1) -> None:
        """
        Decrementa usos o cantidad del ítem y lo retira del inventario
        cuando se agota. Centraliza la lógica de consumo.
        """
        campo = "usos" if "usos" in item else "cantidad" if "cantidad" in item else None
        if campo:
            item[campo] -= cantidad
            if item[campo] <= 0:
                self.inventario.remove(item)
        else:
            self.inventario.remove(item)

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
        for item in self.inventario:
            if item.get("nombre") == nombre:
                self._consumir_uso_item(item, cantidad)
                return True
        return False

    def descartar_por_id(self, idx_1: int) -> tuple[bool, str]:
        """Descarta el ítem completo por ID 1-based."""
        if 1 <= idx_1 <= len(self.inventario):
            nombre = self.inventario.pop(idx_1 - 1)["nombre"]
            return True, nombre
        return False, "ID inválido"

    def usar_item(self, nombre: str, forzar_supervivencia: bool = False) -> tuple[bool, str]:
        item = self.obtener_item(nombre)
        if not item:
            return False, f"No tienes '{nombre}'"
        return self._aplicar_efectos_item(item, forzar_supervivencia=forzar_supervivencia)

    def usar_item_por_id(self, idx_1: int, forzar_supervivencia: bool = False) -> tuple[bool, str]:
        """Usa el ítem por ID 1-based."""
        item = self.obtener_item_por_id(idx_1)
        if not item:
            return False, "ID inválido"
        return self._aplicar_efectos_item(item, forzar_supervivencia=forzar_supervivencia)

    def _aplicar_efectos_item(self, item: dict, forzar_supervivencia: bool = False) -> tuple[bool, str]:
        efectos  = item.get("efectos", {})
        msgs: list[str] = []
        mult_med = self.obtener_efecto_rasgo("multiplicador_medicina", 1.0)
        hubo_efecto = False

        tipo_item = item.get("tipo", "")
        tipos_equipables = {
            "arma_fuego", "arma_cortante", "arma_contundente", "arma_arrojadiza",
            "armadura", "casco",
        }

        # Las armas/protecciones no se consumen al "usar".
        if not efectos and tipo_item in tipos_equipables:
            if tipo_item.startswith("arma"):
                if not self.puede_usar_arma(item):
                    return False, self.motivo_bloqueo_arma(item)
                return True, f"{item.get('nombre','Ítem')} se equipa automáticamente en combate."
            return True, f"{item.get('nombre','Ítem')} aporta defensa pasiva mientras esté en inventario."

        if not efectos:
            return False, "Este ítem no tiene uso directo ahora."

        uso_terapeutico = self._uso_terapeutico_estimado(item, efectos)
        consumir, msgs_farmaco = procesar_uso_farmaco(
            self,
            item,
            uso_terapeutico,
            forzar_supervivencia=forzar_supervivencia,
        )
        if not consumir:
            return False, " | ".join(msgs_farmaco) if msgs_farmaco else "No conviene usar ese fármaco ahora."
        if msgs_farmaco:
            msgs.extend(msgs_farmaco)
            if item.get("tipo", "") in ("medicina", "medicina_fuerte"):
                hubo_efecto = True

        if "salud" in efectos:
            ganado = int(min(efectos["salud"] * mult_med, self.salud_max - self.salud))
            if ganado > 0:
                self.salud += ganado
                msgs.append(f"+{ganado} Salud")
                hubo_efecto = True

        if "hambre" in efectos:
            mult_h = self.obtener_efecto_rasgo("multiplicador_consumo_hambre", 1.0)
            hambre_antes = self.hambre
            self.hambre = clamp(self.hambre + int(efectos["hambre"] / mult_h))
            if self.hambre != hambre_antes:
                msgs.append("Hambre reducida" if efectos["hambre"] < 0 else "Hambre aumentada")
                hubo_efecto = True

        if "sed" in efectos:
            mult_s = self.obtener_efecto_rasgo("multiplicador_consumo_sed", 1.0)
            sed_antes = self.sed
            self.sed = clamp(self.sed + int(efectos["sed"] / mult_s))
            if self.sed != sed_antes:
                msgs.append("Sed reducida" if efectos["sed"] < 0 else "Sed aumentada")
                hubo_efecto = True

        if "fatiga" in efectos:
            fatiga_antes = self.fatiga
            self.fatiga = clamp(self.fatiga + efectos["fatiga"])
            if self.fatiga != fatiga_antes:
                msgs.append("Fatiga reducida" if efectos["fatiga"] < 0 else "Fatiga aumentada")
                hubo_efecto = True

        if "moral" in efectos:
            moral_antes = self.moral
            self.moral = clamp(self.moral + int(efectos["moral"]))
            if self.moral != moral_antes:
                msgs.append("Moral reforzada" if efectos["moral"] > 0 else "Moral afectada")
                hubo_efecto = True

        if "radiacion" in efectos:
            rad_antes = self.radiacion
            self.radiacion = clamp(self.radiacion + int(efectos["radiacion"]))
            if self.radiacion != rad_antes:
                msgs.append("Radiación reducida" if efectos["radiacion"] < 0 else "Radiación aumentada")
                hubo_efecto = True

        if "condicion_remove" in efectos:
            if self._reducir_condicion(efectos["condicion_remove"]):
                msgs.append(f"Tratando {efectos['condicion_remove']}")
                hubo_efecto = True

        if "condicion_riesgo" in efectos:
            prob = float(efectos.get("prob_condicion", 0.15))
            clave_riesgo = str(efectos["condicion_riesgo"])
            if random.random() < prob:
                nuevas = adquirir_condicion_por_consumo(self, clave_riesgo, origen="consumo_item")
                if nuevas:
                    msgs.extend(nuevas)
                    hubo_efecto = True

        if "skill_xp" in efectos:
            mult_libro = self.obtener_efecto_rasgo("xp_mult_libro", 1.0)
            for sk, xp in efectos["skill_xp"].items():
                self.ganar_xp_skill(sk, max(1, int(xp * mult_libro)))
            self.libros_leidos += 1
            msgs.append("Conocimiento adquirido")
            hubo_efecto = True

        if not hubo_efecto:
            return False, "Sin efecto ahora. El ítem no se consumió."

        if item.get("nombre") == "Morfina":
            self.usos_morfina += 1

        self._consumir_uso_item(item)
        self.evaluar_rasgos_nuevos()
        return True, " | ".join(msgs) if msgs else "Sin efecto notable"

    # ─────────────────────────────────────────────────────────
    #  ARMAS Y DEFENSA
    # ─────────────────────────────────────────────────────────

    def arma_equipada(self) -> dict | None:
        armas = [i for i in self.inventario
                 if i.get("tipo") in ("arma_contundente", "arma_cortante",
                                       "arma_fuego", "arma_arrojadiza")]
        armas_aptas = [a for a in armas if self.puede_usar_arma(a)]
        return max(armas_aptas, key=lambda a: sum(a.get("daño", (1, 3))) / 2) if armas_aptas else None

    def manos_disponibles(self) -> int:
        """Número de manos funcionales según condiciones activas."""
        inutilizadas = 0
        for c in self.condiciones:
            ef = c.efectos or {}
            inutilizadas += int(ef.get("brazos_inutiles", 0))
            if ef.get("inutiliza_brazo", False):
                inutilizadas += 1

            texto = f"{c.clave} {c.nombre}".lower()
            if "amput" in texto and "brazo" in texto:
                inutilizadas += 1
            elif "fractura" in texto and "brazo" in texto and c.severidad >= 2:
                inutilizadas += 1

        return max(0, 2 - min(2, inutilizadas))

    def manos_requeridas_arma(self, item: dict) -> int:
        if item.get("manos_requeridas") is not None:
            return max(1, int(item.get("manos_requeridas", 1)))
        if item.get("dos_manos", False):
            return 2

        tipo = item.get("tipo", "")
        nombre = item.get("nombre", "").lower()

        if tipo == "arma_fuego":
            una_mano_tokens = ("pistola", "revólver", "revolver", "9mm")
            return 1 if any(t in nombre for t in una_mano_tokens) else 2

        dos_manos_tokens = ("lanza", "dos manos", "mandoble", "hacha larga")
        if any(t in nombre for t in dos_manos_tokens):
            return 2

        return 1

    def puede_usar_arma(self, item: dict) -> bool:
        if not item.get("tipo", "").startswith("arma"):
            return False
        return self.manos_disponibles() >= self.manos_requeridas_arma(item)

    def motivo_bloqueo_arma(self, item: dict) -> str:
        req = self.manos_requeridas_arma(item)
        disp = self.manos_disponibles()
        return (
            f"No puedes usar {item.get('nombre','esa arma')}: requiere {req} mano(s) "
            f"y solo tienes {disp} disponible(s)."
        )

    def mejor_arma_bloqueada(self) -> dict | None:
        armas = [i for i in self.inventario if i.get("tipo", "").startswith("arma")]
        bloqueadas = [a for a in armas if not self.puede_usar_arma(a)]
        return max(bloqueadas, key=lambda a: sum(a.get("daño", (1, 3))) / 2) if bloqueadas else None

    def bonus_sinergia_arma(self, arma: dict | None) -> int:
        if not arma:
            return 0

        tipo = arma.get("tipo", "")
        bonus = 0
        if tipo == "arma_fuego":
            bonus += 2 if self.skills.get("combate_distancia", 0) >= 50 else 0
            bonus += 1 if self.tiene_item("Chaqueta táctica") else 0
        elif tipo in ("arma_cortante", "arma_contundente"):
            bonus += 2 if self.skills.get("combate_cac", 0) >= 50 else 0
            bonus += 1 if self.tiene_item("Manta térmica") else 0

        bonus += 1 if self.skills.get("supervivencia", 0) >= 60 else 0
        return bonus

    def defensa_total(self) -> int:
        return sum(i.get("defensa", 0) for i in self.inventario
                   if i.get("tipo") in ("armadura", "casco"))

    # ─────────────────────────────────────────────────────────
    #  LISTADO Y FILTRADO
    # ─────────────────────────────────────────────────────────

    def listar_inventario(self) -> list[str]:
        """Líneas formateadas con ID visible para interacción por comandos."""
        if not self.inventario:
            return ["  (vacío)"]
        return [linea_item(item, idx + 1) for idx, item in enumerate(self.inventario)]

    def listar_inventario_categorizado(self) -> list[str]:
        """Líneas del inventario agrupadas por categoría, manteniendo IDs globales."""
        if not self.inventario:
            return ["  (vacío)"]

        filas: list[tuple[str, int, dict]] = []
        for idx, item in enumerate(self.inventario, 1):
            categoria = categoria_item(item)
            filas.append((categoria, idx, item))

        filas.sort(
            key=lambda f: (
                _ORDEN_CATEGORIAS.get(f[0], len(_ORDEN_CATEGORIAS)),
                f[2].get("nombre", "").lower(),
            )
        )

        lineas: list[str] = []
        categoria_actual = ""
        for categoria, idx, item in filas:
            if categoria != categoria_actual:
                if lineas:
                    lineas.append("")
                lineas.append(f"[{categoria}]")
                categoria_actual = categoria
            lineas.append(linea_item(item, idx))

        return lineas

    def inventario_filtrado_ordenado(self, filtro: str = "todos", orden: str = "id") -> list[tuple[int, dict, str]]:
        filtro_n = self.normalizar_filtro_inventario(filtro) or "todos"
        orden_n = (orden or "id").strip().lower()

        filas: list[tuple[int, dict, str]] = []
        for idx, item in enumerate(self.inventario, 1):
            cat = categoria_item(item)
            if filtro_n not in ("", "todos"):
                tipo = item.get("tipo", "").lower()
                if filtro_n not in cat.lower() and filtro_n != tipo:
                    continue
            filas.append((idx, item, cat))

        def _k_nombre(fila):
            return fila[1].get("nombre", "").lower()

        def _k_tipo(fila):
            return fila[1].get("tipo", "").lower()

        def _k_peso(fila):
            return float(fila[1].get("peso", 0.0))

        def _k_cantidad(fila):
            return int(fila[1].get("cantidad", fila[1].get("usos", 1)))

        key_map = {
            "id": lambda f: f[0],
            "nombre": _k_nombre,
            "tipo": _k_tipo,
            "peso": _k_peso,
            "cantidad": _k_cantidad,
        }
        filas.sort(key=key_map.get(orden_n, key_map["id"]))
        return filas

    def categorias_inventario_disponibles(self) -> list[str]:
        cats = sorted({categoria_item(it).lower() for it in self.inventario})
        return ["todos"] + cats

    def normalizar_filtro_inventario(self, filtro: str | None) -> str | None:
        if filtro is None:
            return None
        filtro_n = filtro.strip().lower()
        if not filtro_n:
            return "todos"

        canon = _ALIAS_FILTRO_INVENTARIO.get(filtro_n, filtro_n)
        if canon in self.categorias_inventario_disponibles():
            return canon

        tipos_disponibles = {it.get("tipo", "").lower() for it in self.inventario if it.get("tipo")}
        if canon in tipos_disponibles:
            return canon
        return None

    def info_item(self, idx_1: int) -> dict | None:
        """Dict enriquecido para la pantalla de inspección."""
        item = self.obtener_item_por_id(idx_1)
        return info_completa(item, self) if item else None

    def info_item_dict(self, item: dict) -> dict:
        """Dict enriquecido para inspección dado el ítem directamente (sin índice)."""
        return info_completa(item, self)

    def cantidad_item(self, nombre: str) -> int:
        total = 0
        for it in self.inventario:
            if it.get("nombre") != nombre:
                continue
            if "cantidad" in it:
                total += int(it.get("cantidad", 0))
            elif "usos" in it:
                total += int(it.get("usos", 0))
            else:
                total += 1
        return total

    # ─────────────────────────────────────────────────────────
    #  CRAFTEO
    # ─────────────────────────────────────────────────────────

    def recetas_disponibles(self) -> list[dict]:
        filas = []
        for key, rec in RECETAS.items():
            faltantes = self._faltantes_receta(rec)
            filas.append(
                {
                    "id": key,
                    "nombre": rec.get("nombre", key),
                    "desc": rec.get("desc", ""),
                    "faltantes": faltantes,
                    "puede": not faltantes and self._cumple_skill_receta(rec),
                }
            )
        return filas

    def craftear(self, receta_id: str) -> tuple[bool, str]:
        rec = RECETAS.get(receta_id)
        if not rec:
            return False, "Receta no encontrada."

        if not self._cumple_skill_receta(rec):
            return False, "No cumples los requisitos de skill para esa receta."

        faltantes = self._faltantes_receta(rec)
        if faltantes:
            return False, f"Faltan materiales: {', '.join(faltantes)}"

        for nombre, cant in rec.get("requisitos", {}).items():
            if not self.remover_item(nombre, cantidad=int(cant)):
                return False, f"Error consumiendo materiales ({nombre})."

        item_key = rec.get("resultado", {}).get("item_key")
        cant_out = int(rec.get("resultado", {}).get("cantidad", 1))
        if item_key not in ITEMS:
            return False, "Resultado de receta inválido."

        base = copy.deepcopy(ITEMS[item_key])
        for _ in range(max(1, cant_out)):
            if not self.añadir_item(copy.deepcopy(base)):
                return False, "No tienes capacidad de carga para terminar el crafteo."

        self.ganar_xp_skill("mecanica", 2)
        self.ganar_xp_skill("supervivencia", 2)
        return True, f"Crafteaste: {rec.get('nombre', receta_id)}"

    def _cumple_skill_receta(self, rec: dict) -> bool:
        for sk, req in rec.get("skill_req", {}).items():
            if self.skills.get(sk, 0) < int(req):
                return False
        return True

    def _faltantes_receta(self, rec: dict) -> list[str]:
        faltantes: list[str] = []
        for nombre, cant in rec.get("requisitos", {}).items():
            disp = self.cantidad_item(nombre)
            req = int(cant)
            if disp < req:
                faltantes.append(f"{nombre} ({disp}/{req})")
        return faltantes

    def _uso_terapeutico_estimado(self, item: dict, efectos: dict) -> bool:
        """Estima si hay beneficio real antes de procesar farmacología."""
        if not efectos:
            return False

        if "salud" in efectos and efectos["salud"] > 0 and self.salud < self.salud_max:
            return True
        if "hambre" in efectos and efectos["hambre"] < 0 and self.hambre > 0:
            return True
        if "sed" in efectos and efectos["sed"] < 0 and self.sed > 0:
            return True
        if "fatiga" in efectos and efectos["fatiga"] < 0 and self.fatiga > 0:
            return True
        if "condicion_remove" in efectos:
            return any(c.clave == efectos["condicion_remove"] for c in self.condiciones)
        if "skill_xp" in efectos and bool(efectos["skill_xp"]):
            return True

        return item.get("tipo", "") == "medicina_fuerte"


# ──────────────────────────────────────────────────────────────
#  HELPERS DE PRESENTACIÓN DE ÍTEMS (funciones de módulo)
# ──────────────────────────────────────────────────────────────

def icono_item(item: dict) -> str:
    return ICONOS_TIPO.get(item.get("tipo", ""), "·")


def categoria_item(item: dict) -> str:
    tipo = item.get("tipo", "")
    for nombre, tipos in CATEGORIAS_INVENTARIO:
        if tipo in tipos:
            return nombre
    return CATEGORIA_FALLBACK


def qty_str(item: dict) -> str:
    if "cantidad" in item:
        n = item["cantidad"]
        return f"×{n}" if n != 1 else "×1"
    if "usos" in item:
        return f"{item['usos']}u"
    if "durabilidad" in item:
        return f"{item['durabilidad']}%"
    return "  —"


def linea_item(item: dict, idx: int) -> str:
    icono  = icono_item(item)
    nombre = item.get("nombre", "?")[:28]
    qty    = qty_str(item)
    peso   = item.get("peso", 0)
    return f"{idx:3d}  {icono} {nombre:<29} {qty:>5}   {peso:.1f}kg"


def info_completa(item: dict, personaje) -> dict:
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
    if "moral" in efectos:
        lineas.append(f"  Moral      {efectos['moral']:+d}")
    if "radiacion" in efectos:
        lineas.append(f"  Radiación  {efectos['radiacion']:+d}")
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
        manos = personaje.manos_requeridas_arma(item)
        lineas.append(f"  Manos req. {manos}")
        if personaje.puede_usar_arma(item):
            lineas.append("  Estado     utilizable ahora")
        else:
            lineas.append(f"  Estado     bloqueada ({personaje.motivo_bloqueo_arma(item)})")

    farm = item.get("farmacologia", {}) if isinstance(item.get("farmacologia", {}), dict) else {}
    if farm:
        med_skill = personaje.skills.get("medicina", 0)
        lineas.append("  --- Farmacología ---")
        lineas.append(f"  Clase      {farm.get('clase', 'desconocida')}")
        if med_skill >= 35:
            lineas.append(f"  Activo     {farm.get('principio_activo', 'n/d')}")
            lineas.append(f"  Ventana    {farm.get('ventana_horas', '?')}h")
            lineas.append(f"  Dosis      {farm.get('dosis', '?')} (toxicidad: {farm.get('dosis_toxica', '?')})")
            contra = farm.get("contraindicaciones", [])
            if contra:
                lineas.append(f"  Contra     {', '.join(contra)}")
            comb = farm.get("no_combinar_con", [])
            if comb:
                lineas.append(f"  Evitar mix {', '.join(comb)}")
        else:
            lineas.append("  Nota       Requiere más medicina para interpretar dosis/mezclas.")

    return {
        "nombre":   item.get("nombre", "?"),
        "tipo":     item.get("tipo", "—"),
        "icono":    icono_item(item),
        "peso":     item.get("peso", 0),
        "desc":     item.get("desc", "Sin descripción."),
        "qty_str":  qty_str(item),
        "efectos":  lineas,
        "usable":   bool(efectos),
    }


# ── Compatibilidad: alias con prefijo underscore ─────────────
# Algunos módulos internos usaban las funciones con _prefijo.
_icono_item = icono_item
_categoria_item = categoria_item
_qty_str = qty_str
_linea_item = linea_item
_info_completa = info_completa
