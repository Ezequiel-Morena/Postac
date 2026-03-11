# ============================================================
# engine/almacen.py
# Gestión del almacén compartido del refugio.
# El almacén es ilimitado — es una ubicación fija, no una mochila.
# ============================================================

from __future__ import annotations

import copy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.personaje import Sobreviviente

from engine.inventory_mixin import TIPOS_STACKABLES as _TIPOS_STACKABLES


def almacen_vacio() -> list:
    """Retorna un almacén nuevo y vacío."""
    return []


def agregar_item(almacen: list, item: dict) -> None:
    """
    Agrega un ítem al almacén. Los ítems stackables se apilan por nombre.
    Los ítems con 'usos' individuales se añaden como entradas separadas.
    """
    tipo = item.get("tipo", "")
    if tipo in _TIPOS_STACKABLES:
        nombre = item.get("nombre")
        for existente in almacen:
            if existente.get("nombre") == nombre:
                existente["cantidad"] = existente.get("cantidad", 1) + item.get("cantidad", 1)
                return
        nuevo = copy.deepcopy(item)
        if "cantidad" not in nuevo:
            nuevo["cantidad"] = 1
        almacen.append(nuevo)
    else:
        almacen.append(copy.deepcopy(item))


def quitar_item(almacen: list, nombre: str, cantidad: int = 1) -> dict | None:
    """
    Quita `cantidad` unidades del ítem con ese nombre del almacén.
    Retorna una copia del ítem quitado (para pasarlo al inventario personal),
    o None si no estaba disponible.
    """
    for i, item in enumerate(almacen):
        if item.get("nombre") == nombre:
            tipo = item.get("tipo", "")
            if tipo in _TIPOS_STACKABLES:
                disponible = item.get("cantidad", 1)
                if disponible <= cantidad:
                    return almacen.pop(i)
                item["cantidad"] -= cantidad
                salida = copy.deepcopy(item)
                salida["cantidad"] = cantidad
                return salida
            else:
                return almacen.pop(i)
    return None


def consumir_tipo(almacen: list, tipo: str, cantidad: int = 1) -> list[dict]:
    """
    Consume hasta `cantidad` ítems del tipo indicado.
    Retorna los ítems consumidos (para aplicar sus efectos).
    Preferencia: los ítems con mayor efecto primero.
    """
    candidatos = [it for it in almacen if it.get("tipo") == tipo]
    candidatos.sort(key=lambda x: _valor_item(x), reverse=True)
    consumidos = []
    restante = cantidad
    for item in candidatos:
        if restante <= 0:
            break
        disp = item.get("cantidad", 1)
        tomar = min(disp, restante)
        resultado = quitar_item(almacen, item["nombre"], tomar)
        if resultado:
            consumidos.append(resultado)
            restante -= tomar
    return consumidos


def buscar_tipo(almacen: list, tipo: str) -> list[dict]:
    """Retorna todos los ítems del almacén con el tipo indicado (sin modificar)."""
    return [it for it in almacen if it.get("tipo") == tipo]


def buscar_nombre(almacen: list, nombre: str) -> dict | None:
    """Busca un ítem por nombre exacto. Retorna el dict o None."""
    return next((it for it in almacen if it.get("nombre") == nombre), None)


def cantidad_total_tipo(almacen: list, tipo: str) -> int:
    """Cuenta el total de unidades de un tipo en el almacén."""
    return sum(it.get("cantidad", 1) for it in almacen if it.get("tipo") == tipo)


def listar_items(almacen: list) -> list[dict]:
    """Retorna una copia de la lista de ítems del almacén."""
    return list(almacen)


def transferir_al_inventario(
    almacen: list,
    personaje: "Sobreviviente",
    nombre: str,
    cantidad: int = 1,
) -> tuple[bool, str]:
    """
    Mueve `cantidad` unidades del ítem del almacén al inventario personal.
    Retorna (éxito, mensaje).
    """
    item = buscar_nombre(almacen, nombre)
    if not item:
        return False, f"'{nombre}' no está en el almacén."
    tomado = quitar_item(almacen, nombre, cantidad)
    if tomado is None:
        return False, "No se pudo quitar del almacén."
    if not personaje.añadir_item(tomado):
        # No cabe en la mochila — devolver al almacén.
        agregar_item(almacen, tomado)
        return False, f"No cabe en la mochila (límite {personaje.peso_max}kg)."
    return True, f"Tomaste {tomado.get('nombre')} del almacén."


def _valor_item(item: dict) -> float:
    """Heurística de valor: preferir ítems con mayor efecto nutricional/curativo."""
    efectos = item.get("efectos", {})
    return sum(abs(v) for v in efectos.values() if isinstance(v, (int, float)))


def depositar_al_almacen(
    personaje: "Sobreviviente",
    almacen: list,
    nombre: str,
    cantidad: int = 1,
) -> tuple[bool, str]:
    """
    Mueve `cantidad` unidades del ítem del inventario personal al almacén.
    Retorna (éxito, mensaje).
    """
    extraido = _extraer_del_inventario(personaje, nombre, cantidad)
    if extraido is None:
        return False, f"'{nombre}' no está en el inventario."
    agregar_item(almacen, extraido)
    return True, f"Depositaste {extraido.get('nombre')} en el almacén."


def _extraer_del_inventario(
    personaje: "Sobreviviente",
    nombre: str,
    cantidad: int = 1,
) -> dict | None:
    """
    Extrae y retorna un ítem del inventario personal (para transferirlo al almacén).
    Reduce la cantidad si el ítem es stackable, lo elimina si se agota.
    """
    import copy
    inv = personaje.inventario
    for i, it in enumerate(inv):
        if it.get("nombre") != nombre:
            continue
        tipo = it.get("tipo", "")
        if tipo in _TIPOS_STACKABLES:
            disponible = it.get("cantidad", 1)
            if disponible <= cantidad:
                return inv.pop(i)
            it["cantidad"] -= cantidad
            salida = copy.deepcopy(it)
            salida["cantidad"] = cantidad
            return salida
        else:
            return inv.pop(i)
    return None
