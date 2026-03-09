#!/usr/bin/env python3
# ============================================================
# main.py — Punto de entrada del simulador
#
# Responsabilidad: presentación e input del jugador.
# La simulación vive en engine/tick.py.
# ============================================================
import os
import sys
import time
import random

def cls():
    os.system("cls" if os.name == "nt" else "clear")

R  = "\033[0m"; VE = "\033[92m"; RO = "\033[91m"
AM = "\033[93m"; CI = "\033[96m"; GR = "\033[90m"
BL = "\033[97m"; NE = "\033[1m"

LOGO = f"""{VE}{NE}
  ██████╗  ██████╗ ███████╗████████╗ █████╗  ██████╗
  ██╔══██╗██╔═══██╗██╔════╝╚══██╔══╝██╔══██╗██╔════╝
  ██████╔╝██║   ██║███████╗   ██║   ███████║██║
  ██╔═══╝ ██║   ██║╚════██║   ██║   ██╔══██║██║
  ██║     ╚██████╔╝███████║   ██║   ██║  ██║╚██████╗
  ╚═╝      ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝
{R}{AM}  Simulador de Supervivencia Post-Apocalíptico v2.0{R}
{GR}  Un sobreviviente. Un mundo roto. Cada decisión importa.{R}
"""

def pausa(msg="  [ENTER para continuar]"):
    input(f"\n{GR}{msg}{R}")

def input_num(prompt, lo, hi):
    while True:
        try:
            v = int(input(prompt))
            if lo <= v <= hi: return v
            print(f"  {RO}Elige entre {lo} y {hi}.{R}")
        except ValueError:
            print(f"  {RO}Número inválido.{R}")


# ──────────────────────────────────────────────────────────────
#  CREACIÓN DE PERSONAJE
# ──────────────────────────────────────────────────────────────
def pantalla_creacion():
    from engine.personaje import Sobreviviente
    from data.stats  import STATS
    from data.skills import SKILLS
    from data.rasgos import RASGOS

    cls(); print(LOGO)
    print(f"  {GR}El mundo colapsó hace 847 días.")
    print(f"  La infección borró el 94% de la población.")
    print(f"  Tú eres uno de los pocos que quedan.{R}\n")
    input(f"  {CI}[ENTER para generar tu superviviente...]{R}")

    print(f"\n  {VE}Generando perfil", end="", flush=True)
    for _ in range(8):
        time.sleep(0.15); print(".", end="", flush=True)
    print(f"{R}\n")

    p = Sobreviviente()
    cls(); print(LOGO)

    sexo = "♂" if p.genero == "Masculino" else "♀"
    print(f"\n{AM}{NE}═══ PERFIL GENERADO ═══════════════════{R}")
    print(f"  {CI}{p.nombre} {p.apellido}{R}  {sexo}  {p.edad} años")
    print(f"  {VE}{p.background['nombre']}{R}")
    print(f"  {GR}{p.background['descripcion']}{R}\n")

    print(f"  {AM}ESTADÍSTICAS BASE{R}")
    for key, defn in STATS.items():
        val = p.stats[key]
        bar = "█" * val + "░" * (defn["max"] - val)
        print(f"    {defn['icono']} {defn['abrev']}  [{bar}]  {val}/{defn['max']}")

    print(f"\n  {AM}HABILIDADES{R}")
    for key, defn in SKILLS.items():
        val = p.skills[key]
        bar = "█" * (val // 10) + "░" * (10 - val // 10)
        print(f"    {defn['icono']} {defn['abrev']}  [{bar}]  {val}")

    if p.rasgos:
        print(f"\n  {AM}RASGOS{R}")
        for r in p.rasgos:
            if r in RASGOS:
                print(f"    {RASGOS[r]['icono']} {RASGOS[r]['nombre']}"
                      f"  {GR}{RASGOS[r].get('descripcion','')}{R}")

    print(f"\n{'─'*52}\n  {AM}EQUIPO INICIAL{R}")
    for item in p.inventario:
        print(f"    {VE}+ {item['nombre']}{R}  {GR}{item.get('desc','')[:60]}{R}")
    print(f"\n{'═'*52}")

    while True:
        resp = input(
            f"\n  {CI}¿Aceptar? [S / n=rechazar / r=regenerar]: {R}"
        ).strip().lower()
        if resp in ("s", ""):   return p
        if resp == "n":         return None
        if resp == "r":         return pantalla_creacion()


# ──────────────────────────────────────────────────────────────
#  ESTADO RÁPIDO
# ──────────────────────────────────────────────────────────────
def mostrar_estado(personaje):
    from data.rasgos import RASGOS
    p = personaje

    def b(v, m=100, w=8):
        ll = int((v / max(1, m)) * w)
        return f"{'█'*ll}{'░'*(w-ll)}"

    cs = VE if p.salud > 60 else (AM if p.salud > 30 else RO)
    print(f"\n{AM}{NE}═══ ESTADO ════════════════════════════{R}")
    print(f"  {CI}{p.nombre} {p.apellido}{R} | Día {p.dia} {p.hora:02d}:00hs")
    print(f"  Salud   {cs}{b(p.salud,p.salud_max)}{R} {p.salud}/{p.salud_max}")
    print(f"  Hambre  {RO if p.hambre>70 else AM}{b(100-p.hambre)}{R} {p.hambre}/100")
    print(f"  Sed     {RO if p.sed>70 else AM}{b(100-p.sed)}{R} {p.sed}/100")
    print(f"  Fatiga  {RO if p.fatiga>70 else AM}{b(100-p.fatiga)}{R} {p.fatiga}/100")
    print(f"  Moral   {RO if p.moral<30 else VE}{b(p.moral)}{R} {p.moral}/100")
    if p.radiacion > 0:
        print(f"  Rad     {RO}{b(p.radiacion)}{R} {p.radiacion}/100 ☢")
    if p.condiciones:
        print(f"  {RO}Condiciones: {', '.join(str(c) for c in p.condiciones)}{R}")
    if p.rasgos:
        nombres = [RASGOS[r]["nombre"] for r in p.rasgos if r in RASGOS]
        print(f"  {CI}Rasgos: {', '.join(nombres)}{R}")
    print(f"  {GR}Carga: {p.peso_actual():.1f}/{p.peso_max}kg | "
          f"Exp: {p.expediciones_completadas}{R}")
    print(f"{AM}═══════════════════════════════════════{R}")


# ──────────────────────────────────────────────────────────────
#  MUERTE DEL PERSONAJE
# ──────────────────────────────────────────────────────────────
def procesar_muerte(personaje, causa: str = "desconocida"):
    from engine.save_manager import (registrar_muerte, mostrar_leaderboard,
                                      borrar_guardado)
    cls()
    print(f"\n{RO}{NE}{'═'*52}")
    print(f"  {personaje.nombre} {personaje.apellido} HA CAÍDO")
    print(f"{'═'*52}{R}\n")
    print(f"  Sobrevivió {personaje.dia} días.")
    print(f"  Expediciones completadas: {personaje.expediciones_completadas}")
    print(f"  Infectados eliminados:    {personaje.infectados_eliminados}")
    print(f"  Bandidos eliminados:      {personaje.bandidos_eliminados}")
    print(f"  Causa: {causa}\n")

    pos = registrar_muerte(personaje, causa)
    print(f"  {AM}Posición en el ranking: #{pos}{R}")
    print(mostrar_leaderboard(10))
    borrar_guardado()
    pausa("  [ENTER para volver al menú]")


# ──────────────────────────────────────────────────────────────
#  BUCLE PRINCIPAL
# ──────────────────────────────────────────────────────────────
def bucle_principal(personaje, opciones_pendientes=None):
    from engine.save_manager import guardar
    from engine.mundo        import generar_opciones, mostrar_opciones
    from engine.tick         import ejecutar_expedicion, ejecutar_descanso

    if not opciones_pendientes:
        opciones_pendientes = generar_opciones(personaje, 4)

    while True:
        if not personaje.esta_vivo():
            procesar_muerte(personaje, "heridas de combate")
            return

        cls(); print(LOGO)
        mostrar_estado(personaje)
        print(mostrar_opciones(opciones_pendientes, personaje))

        if personaje.hambre > 80:
            print(f"  {RO}⚠ HAMBRE CRÍTICA — Necesitas comer{R}")
        if personaje.sed > 80:
            print(f"  {RO}⚠ SED CRÍTICA — Necesitas agua{R}")
        if personaje.salud < personaje.salud_max * 0.25:
            print(f"  {RO}⚠ SALUD CRÍTICA — Al borde de la muerte{R}")

        print(f"\n  {AM}[i] Inventario  [f] Ficha  [r] Ranking  "
              f"[g] Guardar  [q] Salir{R}")

        cmd = input(f"\n  > ").strip().lower()

        if cmd == "q":
            guardar(personaje, opciones_pendientes)
            print(f"\n  {VE}Guardado. Hasta la próxima.{R}\n")
            sys.exit(0)

        elif cmd == "g":
            guardar(personaje, opciones_pendientes)
            print(f"  {VE}✔ Estado guardado.{R}")
            pausa()

        elif cmd == "i":
            cls()
            print(f"\n{AM}═══ INVENTARIO ({personaje.peso_actual():.1f}/"
                   f"{personaje.peso_max}kg) ══════════{R}")
            for linea in personaje.listar_inventario():
                print(f"{VE}{linea}{R}")
            print(f"\n  {AM}[u N] Usar item N | [ENTER] Volver{R}")
            sub = input("  > ").strip().lower()
            if sub.startswith("u"):
                try:
                    idx = int(sub.split()[1]) - 1
                    if 0 <= idx < len(personaje.inventario):
                        item = personaje.inventario[idx]
                        ok, msg = personaje.usar_item(item["nombre"])
                        print(f"  {VE if ok else RO}{msg}{R}")
                except (IndexError, ValueError):
                    print(f"  {AM}Uso: u 3  (para usar el item 3){R}")
            pausa()

        elif cmd == "f":
            cls(); print(personaje)
            try:
                from engine.bitacora import exportar_perfil
                exportar_perfil(personaje, "saves/perfil.png")
                print(f"\n  {VE}Perfil exportado: saves/perfil.png{R}")
            except Exception:
                pass
            pausa()

        elif cmd == "r":
            from engine.save_manager import mostrar_leaderboard
            cls(); print(mostrar_leaderboard(15)); pausa()

        elif cmd == "0":
            # Descanso: el tick devuelve un log que aquí se imprime
            resultado = ejecutar_descanso(personaje)
            print(f"\n{VE}[DESCANSO EN REFUGIO]{R}")
            for linea in resultado.log_descanso:
                color = RO if "⚠" in linea else VE
                print(f"{color}{linea}{R}")
            guardar(personaje, opciones_pendientes)
            pausa()

            if not resultado.personaje_vivo:
                procesar_muerte(personaje, resultado.causa_muerte)
                return

        else:
            try:
                idx = int(cmd) - 1
                if 0 <= idx < len(opciones_pendientes):
                    area = opciones_pendientes[idx]
                    cls()
                    print(f"\n{VE}{NE}INICIANDO EXPEDICIÓN: {area['nombre']}{R}")
                    print(f"  {GR}Peligro: {area['peligro']}/5 | "
                           f"~{area['duracion_h']}h{R}\n")
                    time.sleep(0.6)

                    resultado = ejecutar_expedicion(personaje, area,
                                                    exportar_img=True)
                    print(resultado.log_terminal)

                    if resultado.ruta_imagen:
                        print(f"  {VE}📷 Imagen: {resultado.ruta_imagen}{R}")

                    opciones_pendientes = generar_opciones(personaje, 4)
                    guardar(personaje, opciones_pendientes, hacer_backup=True)

                    if not resultado.personaje_vivo:
                        pausa()
                        procesar_muerte(personaje, resultado.causa_muerte)
                        return

                    pausa()
                else:
                    print(f"  {RO}Opción inválida.{R}"); time.sleep(1)
            except ValueError:
                print(f"  {RO}Comando no reconocido.{R}"); time.sleep(1)


# ──────────────────────────────────────────────────────────────
#  MODO BOT (para cron / Bluesky)
# ──────────────────────────────────────────────────────────────
def modo_bot(num_opcion: int = -1):
    from engine.save_manager import cargar, guardar
    from engine.mundo        import generar_opciones
    from engine.personaje    import Sobreviviente
    from engine.tick         import ejecutar_expedicion

    print("[BOT] Iniciando ciclo automático...")
    personaje, opciones = cargar()
    if not personaje:
        print("[BOT] Sin guardado. Generando nuevo personaje...")
        personaje = Sobreviviente()

    if not opciones:
        opciones = generar_opciones(personaje, 4)

    area = (opciones[num_opcion]
            if 0 <= num_opcion < len(opciones)
            else _bot_elegir(personaje, opciones))

    print(f"[BOT] → {area['nombre']} (peligro {area['peligro']})")

    resultado = ejecutar_expedicion(personaje, area, exportar_img=True)
    print(resultado.log_terminal)
    if resultado.ruta_imagen:
        print(f"[BOT] Imagen: {resultado.ruta_imagen}")

    nuevas = generar_opciones(personaje, 4)
    guardar(personaje, nuevas, hacer_backup=True)
    print("[BOT] Estado guardado. Listo para publicar.")

    if not resultado.personaje_vivo:
        from engine.save_manager import registrar_muerte, borrar_guardado
        pos = registrar_muerte(personaje, resultado.causa_muerte)
        borrar_guardado()
        print(f"[BOT] Personaje muerto. Posición #{pos} en el ranking.")


def _bot_elegir(personaje, opciones: list) -> dict:
    """Heurística del bot para elegir la expedición más conveniente."""
    puntajes = []
    for area in opciones:
        p = 50
        loot = area.get("loot_chances", {})
        if personaje.hambre > 70 and any("comida" in k for k in loot):  p += 30
        if personaje.sed    > 70 and any("agua"   in k for k in loot):  p += 35
        if (personaje.salud < personaje.salud_max * 0.5
                and any("medicina" in k for k in loot)):                 p += 40
        p -= area["peligro"] * (10 if personaje.salud < personaje.salud_max * 0.4
                                 else 3)
        if not area["ya_visitada"]: p += 10
        if area.get("high_loot"):   p += 15
        p += random.randint(-8, 8)
        puntajes.append((p, area))
    puntajes.sort(key=lambda x: x[0], reverse=True)
    return puntajes[0][1]


# ──────────────────────────────────────────────────────────────
#  MENÚ DE INICIO
# ──────────────────────────────────────────────────────────────
def menu_inicio():
    from engine.save_manager import (cargar, hay_guardado, info_guardado,
                                      borrar_guardado, guardar,
                                      mostrar_leaderboard)
    from engine.personaje import Sobreviviente
    from data.personajes  import BACKGROUNDS

    cls(); print(LOGO)
    print(f"  {AM}╔═══════════════════════════════════╗")
    print(f"  ║          MENÚ PRINCIPAL           ║")
    print(f"  ╚═══════════════════════════════════╝{R}\n")

    info = info_guardado()
    if info:
        bg_nombre = BACKGROUNDS.get(
            info["background"], {}
        ).get("nombre", info["background"])
        print(f"  {VE}▶ Partida guardada encontrada:{R}")
        print(f"    {info['nombre']} — Día {info['dia']} — "
               f"Salud: {info['salud']}/{info['salud_max']}")
        print(f"    {bg_nombre} | {info['expediciones']} expediciones")
        print(f"    Guardado: {info['timestamp'][:16]}\n")

    print(f"  {CI}[1]{R} {'Continuar partida' if info else '(sin partida guardada)'}")
    print(f"  {CI}[2]{R} Nueva partida")
    print(f"  {CI}[3]{R} Ver ranking")
    print(f"  {CI}[4]{R} Salir\n")

    opcion = input_num("  > ", 1, 4)

    if opcion == 1:
        if not info:
            print(f"  {RO}No hay partida guardada.{R}"); pausa(); menu_inicio()
            return
        personaje, opciones = cargar()
        if personaje:
            bucle_principal(personaje, opciones)
        else:
            print(f"  {RO}Error al cargar.{R}"); pausa(); menu_inicio()

    elif opcion == 2:
        if info:
            resp = input(
                f"  {AM}¿Borrar partida actual y empezar de nuevo? [s/N]: {R}"
            ).strip().lower()
            if resp != "s":
                menu_inicio(); return
            borrar_guardado()
        personaje = pantalla_creacion()
        if personaje:
            guardar(personaje)
            bucle_principal(personaje)
        else:
            menu_inicio()

    elif opcion == 3:
        cls(); print(mostrar_leaderboard(15)); pausa(); menu_inicio()

    elif opcion == 4:
        print(f"\n  {GR}Que la suerte te acompañe, superviviente.{R}\n")
        sys.exit(0)


# ──────────────────────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────────────────────
from pathlib import Path

if __name__ == "__main__":
    args = sys.argv[1:]

    if "--bot" in args:
        num_op = -1
        try:
            idx = args.index("--bot")
            if idx + 1 < len(args):
                num_op = int(args[idx + 1])
        except (ValueError, IndexError):
            pass
        modo_bot(num_op)

    elif "--nueva" in args:
        from engine.personaje import Sobreviviente
        from engine.save_manager import guardar
        p = Sobreviviente()
        guardar(p)
        print(f"Nuevo personaje: {p.nombre} {p.apellido} | {p.background['nombre']}")

    elif "--ranking" in args:
        from engine.save_manager import mostrar_leaderboard
        print(mostrar_leaderboard(20))

    else:
        try:
            menu_inicio()
        except KeyboardInterrupt:
            print(f"\n\n  {GR}Hasta pronto, superviviente.{R}\n")
            sys.exit(0)
