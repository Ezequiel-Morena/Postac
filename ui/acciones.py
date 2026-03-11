# ============================================================
# ui/acciones.py — Menú de acciones expandido del refugio
# ============================================================

from ui.tui import (
    console, limpiar, pausa, menu_rich,
    COLOR_OK, COLOR_WARN, COLOR_DANGER, COLOR_INFO, COLOR_DIM, COLOR_ACCENT,
)
from engine.fuego import esta_encendido, combustible_disponible, encender_fuego, agregar_combustible
from engine.pesca import intentar_pesca, puede_pescar
from engine.caza import cazar_activo, poner_trampa, revisar_trampas, puede_cazar
from engine.recoleccion import recolectar, puede_recolectar
from engine.cocina import cocinar_item, listar_items_cocinables, puede_cocinar

_ACCIONES_MENU = [
    "🎣 Pescar        (cerca del agua)",
    "🏹 Cazar          (zona exterior/forestal)",
    "🌿 Recolectar     (plantas y leña)",
    "🍳 Cocinar",
    "🔥 Encender fuego",
    "🪤 Poner trampa   (zona exterior)",
    "🔍 Revisar trampas",
    "← Volver",
]


def pantalla_acciones_refugio(personaje, opciones_zona: list):
    """Menú de acciones del refugio con menu_rich."""
    while True:
        fuego_str = ""
        if esta_encendido(personaje):
            mins = int(combustible_disponible(personaje))
            fuego_str = f" ✅ fuego activo ~{mins}min"
        else:
            fuego_str = " ❌ sin fuego"

        # Actualizar la opción de cocinar con el estado del fuego
        acciones = list(_ACCIONES_MENU)
        acciones[3] = f"🍳 Cocinar       {fuego_str}"

        idx = menu_rich("ACCIONES DEL REFUGIO", acciones, subtitulo="Esc/0 para volver")
        if idx in (-1, len(acciones) - 1):
            return
        elif idx == 0:
            _accion_pescar(personaje, opciones_zona)
        elif idx == 1:
            _accion_cazar(personaje, opciones_zona)
        elif idx == 2:
            _accion_recolectar(personaje, opciones_zona)
        elif idx == 3:
            _accion_cocinar(personaje)
        elif idx == 4:
            _accion_encender_fuego(personaje)
        elif idx == 5:
            _accion_poner_trampa(personaje, opciones_zona)
        elif idx == 6:
            _accion_revisar_trampas(personaje, opciones_zona)


def _elegir_zona_accion(opciones_zona: list, tipo_accion: str) -> dict | None:
    """Permite elegir zona con menu_rich."""
    if not opciones_zona:
        console.print(f"  [{COLOR_DANGER}]No hay zonas disponibles.[/{COLOR_DANGER}]")
        return None

    nombres = [z.get("nombre", "?") for z in opciones_zona] + ["Cancelar"]
    idx = menu_rich(f"¿En qué zona — {tipo_accion}?", nombres)
    if idx < 0 or idx == len(opciones_zona):
        return None
    return opciones_zona[idx]


def _accion_pescar(personaje, opciones_zona):
    zona = _elegir_zona_accion(opciones_zona, "pesca")
    if not zona:
        return

    puede, razon = puede_pescar(personaje, zona)
    if not puede:
        console.print(f"  [{COLOR_DANGER}]{razon}[/{COLOR_DANGER}]")
        pausa()
        return

    limpiar()
    console.print(f"\n  [{COLOR_DIM}]Iniciando sesión de pesca en {zona.get('nombre', '?')}...[/{COLOR_DIM}]")
    resultado = intentar_pesca(personaje, zona, horas=2.0)
    _mostrar_resultado_accion(resultado, "capturas")

    if resultado["capturas"]:
        almacen = getattr(personaje, "almacen", [])
        almacen.extend(resultado["capturas"])
        personaje.almacen = almacen

    pausa()


def _accion_cazar(personaje, opciones_zona):
    zona = _elegir_zona_accion(opciones_zona, "caza")
    if not zona:
        return

    puede, razon = puede_cazar(personaje, zona)
    if not puede:
        console.print(f"  [{COLOR_DANGER}]{razon}[/{COLOR_DANGER}]")
        pausa()
        return

    limpiar()
    console.print(f"\n  [{COLOR_DIM}]Iniciando caza en {zona.get('nombre', '?')}...[/{COLOR_DIM}]")
    resultado = cazar_activo(personaje, zona, horas=3.0)

    icono = "✅" if resultado["exito"] else "❌"
    col   = COLOR_OK if resultado["exito"] else COLOR_DANGER
    console.print(f"\n  [{col}]{icono} {resultado['mensaje']}[/{col}]")
    if resultado["daño_recibido"] > 0:
        console.print(f"  [{COLOR_DANGER}]⚠ -{resultado['daño_recibido']} salud por ataque del animal.[/{COLOR_DANGER}]")

    if resultado["exito"]:
        almacen = getattr(personaje, "almacen", [])
        for _ in range(resultado["capturas_carne"]):
            almacen.append({"id": "carne_animal_cruda", "nombre": "Carne de animal", "cantidad": 1})
        for _ in range(resultado["capturas_piel"]):
            almacen.append({"id": "piel_animal", "nombre": "Piel de animal", "cantidad": 1})
        personaje.almacen = almacen

    pausa()


def _accion_recolectar(personaje, opciones_zona):
    zona = _elegir_zona_accion(opciones_zona, "recoleccion")
    if not zona:
        return

    puede, razon = puede_recolectar(zona)
    if not puede:
        console.print(f"  [{COLOR_DANGER}]{razon}[/{COLOR_DANGER}]")
        pausa()
        return

    limpiar()
    console.print(f"\n  [{COLOR_DIM}]Recolectando en {zona.get('nombre', '?')}...[/{COLOR_DIM}]")
    resultado = recolectar(personaje, zona, horas=1.5)

    icono = "✅" if resultado["exito"] else "❌"
    col   = COLOR_OK if resultado["exito"] else COLOR_DANGER
    console.print(f"\n  [{col}]{icono} {resultado['mensaje']}[/{col}]")
    if resultado.get("intoxicacion"):
        console.print(f"  [{COLOR_DANGER}]⚠ Intoxicación leve por planta mal identificada.[/{COLOR_DANGER}]")

    if resultado["items"]:
        almacen = getattr(personaje, "almacen", [])
        almacen.extend(resultado["items"])
        personaje.almacen = almacen

    pausa()


def _accion_cocinar(personaje):
    puede, razon = puede_cocinar(personaje)
    if not puede:
        console.print(f"\n  [{COLOR_DANGER}]{razon}[/{COLOR_DANGER}]")
        pausa()
        return

    cocinables = listar_items_cocinables(personaje)
    if not cocinables:
        console.print(f"\n  [{COLOR_DANGER}]No hay nada para cocinar en el inventario o almacén.[/{COLOR_DANGER}]")
        pausa()
        return

    idx = menu_rich("¿Qué cocinar?", cocinables + ["Cancelar"])
    if idx < 0 or idx == len(cocinables):
        return

    resultado = cocinar_item(personaje, cocinables[idx])
    icono = "✅" if resultado["exito"] else "❌"
    col   = COLOR_OK if resultado["exito"] else COLOR_DANGER
    console.print(f"\n  [{col}]{icono} {resultado['mensaje']}[/{col}]")
    pausa()


def _accion_encender_fuego(personaje):
    if esta_encendido(personaje):
        mins = int(combustible_disponible(personaje))
        console.print(f"\n  [{COLOR_DIM}]El fuego ya está activo (~{mins} min restantes).[/{COLOR_DIM}]")
        idx = menu_rich("¿Agregar combustible?", ["Sí, agregar", "No, volver"])
        if idx == 0:
            _agregar_combustible_menu(personaje)
        pausa()
        return

    exito, msg = encender_fuego(personaje)
    icono = "✅" if exito else "❌"
    col   = COLOR_OK if exito else COLOR_DANGER
    console.print(f"\n  [{col}]{icono} {msg}[/{col}]")
    pausa()


def _agregar_combustible_menu(personaje):
    from engine.fuego import COMBUSTIBLES
    disponibles = []
    for col in (getattr(personaje, "inventario", []), getattr(personaje, "almacen", [])):
        for item in col:
            if isinstance(item, dict) and item.get("id") in COMBUSTIBLES:
                if item["id"] not in disponibles:
                    disponibles.append(item["id"])

    if not disponibles:
        console.print(f"  [{COLOR_DANGER}]No tienes combustible disponible.[/{COLOR_DANGER}]")
        return

    idx = menu_rich("¿Qué combustible añadir?", disponibles + ["Cancelar"])
    if idx < 0 or idx == len(disponibles):
        return

    exito, msg = agregar_combustible(personaje, disponibles[idx])
    icono = "✅" if exito else "❌"
    col   = COLOR_OK if exito else COLOR_DANGER
    console.print(f"  [{col}]{icono} {msg}[/{col}]")


def _accion_poner_trampa(personaje, opciones_zona):
    zona = _elegir_zona_accion(opciones_zona, "trampa")
    if not zona:
        return
    exito, msg = poner_trampa(personaje, zona)
    icono = "✅" if exito else "❌"
    col   = COLOR_OK if exito else COLOR_DANGER
    console.print(f"\n  [{col}]{icono} {msg}[/{col}]")
    pausa()


def _accion_revisar_trampas(personaje, opciones_zona):
    zona = _elegir_zona_accion(opciones_zona, "revisar_trampa")
    if not zona:
        return

    capturas = revisar_trampas(personaje, zona)
    if capturas:
        almacen = getattr(personaje, "almacen", [])
        almacen.extend(capturas)
        personaje.almacen = almacen
        nombres = ", ".join(f"{c.get('nombre', c['id'])}×{c.get('cantidad', 1)}" for c in capturas)
        console.print(f"\n  [{COLOR_OK}]✅ Las trampas capturaron: {nombres}[/{COLOR_OK}]")
    else:
        console.print(f"\n  [{COLOR_DIM}]❌ Las trampas estaban vacías.[/{COLOR_DIM}]")
    pausa()


def _mostrar_resultado_accion(resultado: dict, clave_items: str):
    icono = "✅" if resultado.get("exito") else "❌"
    col   = COLOR_OK if resultado.get("exito") else COLOR_DANGER
    console.print(f"\n  [{col}]{icono} {resultado.get('mensaje', '')}[/{col}]")
    for item in resultado.get(clave_items, []):
        nombre   = item.get("nombre", item.get("id", "?"))
        cantidad = item.get("cantidad", 1)
        console.print(f"  [{COLOR_OK}]  + {nombre} ×{cantidad}[/{COLOR_OK}]")
