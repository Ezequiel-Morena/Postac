#!/usr/bin/env python3
# ============================================================
# main.py — Punto de entrada del simulador
# ============================================================
import os, sys, time, random

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

    print(f"{AM}{'═'*52}{R}")
    print(f"  {VE}{NE}SUPERVIVIENTE GENERADO{R}")
    print(f"{'─'*52}")
    sexo = "♂ Masculino" if p.genero == "Masculino" else "♀ Femenino"
    print(f"  Nombre:    {CI}{p.nombre} {p.apellido}{R}")
    print(f"  Género:    {sexo}  |  Edad: {p.edad} años")
    print(f"  Trasfondo: {AM}{p.background['nombre']}{R}")
    print(f"  Historia:  {GR}{p.background['descripcion']}{R}")

    print(f"\n{'─'*52}\n  {AM}ESTADÍSTICAS{R}")
    for k, defn in STATS.items():
        v = p.stats[k]
        barras = "█"*v + "░"*(defn["max"]-v)
        col = VE if v >= 7 else (AM if v >= 5 else RO)
        print(f"  {defn['nombre']:<14} {col}[{barras}] {v}/{defn['max']}{R}")

    print(f"\n{'─'*52}\n  {AM}HABILIDADES{R}")
    for k, defn in SKILLS.items():
        v = p.skills[k]
        ll = int((v/100)*15); barras = "█"*ll + "░"*(15-ll)
        col = VE if v >= 60 else (AM if v >= 40 else RO)
        print(f"  {defn['nombre']:<24} {col}[{barras}] {v:3d}/100{R}")

    print(f"\n{'─'*52}\n  {AM}RASGOS INICIALES{R}")
    for rk in p.rasgos:
        r = RASGOS.get(rk, {})
        print(f"  {CI}✦ {r.get('nombre','?')}{R}  {GR}{r.get('descripcion','')}{R}")

    print(f"\n{'─'*52}\n  {AM}EQUIPO INICIAL{R}")
    for item in p.inventario:
        print(f"    {VE}+ {item['nombre']}{R}  {GR}{item.get('desc','')[:60]}{R}")
    print(f"\n{'═'*52}")

    while True:
        resp = input(f"\n  {CI}¿Aceptar? [S / n=rechazar / r=regenerar]: {R}").strip().lower()
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
        ll = int((v/max(1,m))*w)
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
#  RESOLVER EXPEDICIÓN
# ──────────────────────────────────────────────────────────────
def resolver_expedicion(personaje, area: dict,
                         exportar_img: bool = True) -> tuple:
    from engine.bitacora  import Bitacora, render_terminal, render_texto_plano, \
                                  exportar_imagen, exportar_perfil
    from engine.mundo     import generar_loot_area
    from engine.eventos   import resolver_evento, generar_secuencia_eventos
    from engine.combate   import resolver_combate

    bit       = Bitacora(personaje)
    loot_total: list[dict] = []
    exito      = True

    bit.entrada(f"Salida → {area['nombre']} (peligro {area['peligro']}/5). "
                 f"ETA ~{area['duracion_h']}h.")

    # Advertencias pre-expedición
    if personaje.hambre > 70: bit.estado_critico("hambre")
    if personaje.sed   > 70:  bit.estado_critico("sed")
    if personaje.salud < personaje.salud_max * 0.4: bit.estado_critico("salud_baja")

    secuencia = generar_secuencia_eventos(area, personaje)

    for ev_data in secuencia:
        if not personaje.esta_vivo() or not exito:
            break

        tipo_ev = ev_data[0]
        zona    = ev_data[2]
        bit.entrada(f"Explorando: {zona.replace('_',' ').title()}")

        if tipo_ev == "combate":
            enemigo_key = ev_data[1]
            iniciativa  = ev_data[3] if len(ev_data) > 3 else "tirar"
            r_c = resolver_combate(personaje, enemigo_key, iniciativa)
            bit.log_combate(r_c)
            for item in r_c.loot_enemigo:
                if personaje.añadir_item(item):
                    loot_total.append(item)
            if r_c.derrota:
                exito = False

        elif tipo_ev == "evento":
            r_e = resolver_evento(personaje, ev_data[1], area)
            bit.log_evento(r_e)
            for item in r_e.items_obtenidos:
                if personaje.añadir_item(item):
                    loot_total.append(item)
                    personaje.items_recolectados += 1
            if r_e.info_obtenida:
                personaje.info_areas[area["area_key"]] = {
                    "conocido": True, "detalle": "Zona explorada previamente"}

        # Avanzar tiempo
        horas_zona = area["duracion_h"] / max(1, len(secuencia))
        personaje.pasar_tiempo(horas_zona)
        _auto_consumir(personaje, bit)

        if personaje.salud < personaje.salud_max * 0.15:
            bit.entrada("¡Salud crítica! Aborto la expedición.", "critico")
            exito = False

    # Loot general del área
    if exito:
        loot_base = generar_loot_area(area, personaje)
        bit.log_loot(loot_base)
        for item in loot_base:
            if personaje.añadir_item(item):
                loot_total.append(item)
                personaje.items_recolectados += 1

    bit.fin(area["nombre"], exito)

    if area["area_key"] not in personaje.areas_visitadas:
        personaje.areas_visitadas.append(area["area_key"])
    if exito:
        personaje.expediciones_completadas += 1
        personaje.moral = min(100, personaje.moral + 5)

    log_term = render_terminal(bit, personaje, loot_total)
    txt_plano = render_texto_plano(bit, personaje, loot_total, area["nombre"])

    Path("saves").mkdir(exist_ok=True)
    with open("saves/bitacora_ultima.txt", "w", encoding="utf-8") as f:
        f.write(txt_plano)

    ruta_img = ""
    if exportar_img:
        nombre_img = f"saves/bitacora_dia{personaje.dia}.png"
        try:
            ruta_img = exportar_imagen(txt_plano, nombre_img)
            exportar_perfil(personaje, "saves/perfil.png")
        except Exception as e:
            print(f"  {AM}⚠ Imagen no generada: {e}{R}")

    return log_term, txt_plano, ruta_img, exito


def _auto_consumir(personaje, bit):
    if personaje.sed > 85 and personaje.tiene_item("Botella de agua"):
        ok, msg = personaje.usar_item("Botella de agua")
        if ok: bit.entrada("Bebiste el agua que llevabas.", "aviso")
    if personaje.hambre > 90 and personaje.tiene_item("Barrita energética"):
        ok, msg = personaje.usar_item("Barrita energética")
        if ok: bit.entrada("Comiste algo al vuelo.", "aviso")
    if personaje.salud < personaje.salud_max * 0.30:
        for nombre in ["Botiquín básico", "Venda"]:
            if personaje.tiene_item(nombre):
                ok, msg = personaje.usar_item(nombre)
                if ok: bit.entrada(f"Usé {nombre} de emergencia. {msg}", "aviso")
                break


# ──────────────────────────────────────────────────────────────
#  DESCANSO
# ──────────────────────────────────────────────────────────────
def resolver_descanso(personaje):
    print(f"\n{VE}[DESCANSO EN REFUGIO]{R}")
    for nombre_item, tipo_check, umbral in [
        ("Lata de frijoles", "hambre", 40),
        ("Lata de atún",     "hambre", 40),
        ("Barrita energética","hambre", 50),
    ]:
        if getattr(personaje, tipo_check) > umbral and personaje.tiene_item(nombre_item):
            ok, msg = personaje.usar_item(nombre_item)
            if ok: print(f"  Comiste: {nombre_item}. {msg}")
            break
    if personaje.sed > 30 and personaje.tiene_item("Botella de agua"):
        ok, msg = personaje.usar_item("Botella de agua")
        if ok: print(f"  Bebiste agua. {msg}")
    if personaje.salud < personaje.salud_max * 0.7:
        for nombre in ["Botiquín básico", "Venda"]:
            if personaje.tiene_item(nombre):
                ok, msg = personaje.usar_item(nombre)
                if ok: print(f"  Trataste heridas: {msg}")
                break
    personaje.fatiga = max(0, personaje.fatiga - 40)
    personaje.moral  = min(100, personaje.moral + 5)
    personaje.pasar_tiempo(6)
    print(f"  Descansaste 6 horas.")
    if personaje.hambre > 75: print(f"  {RO}⚠ Sin comida. El hambre es crítica.{R}")
    if personaje.sed    > 75: print(f"  {RO}⚠ Sin agua. La deshidratación avanza.{R}")


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
    from engine.mundo import generar_opciones, mostrar_opciones

    if not opciones_pendientes:
        opciones_pendientes = generar_opciones(personaje, 4)

    while True:
        # Verificar muerte
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
            except Exception: pass
            pausa()

        elif cmd == "r":
            from engine.save_manager import mostrar_leaderboard
            cls(); print(mostrar_leaderboard(15)); pausa()

        elif cmd == "0":
            resolver_descanso(personaje)
            guardar(personaje, opciones_pendientes)
            pausa()

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

                    log_term, _, ruta_img, exito = resolver_expedicion(
                        personaje, area, exportar_img=True)
                    print(log_term)

                    if ruta_img:
                        print(f"  {VE}📷 Imagen: {ruta_img}{R}")

                    # Guardar con backup antes de regenerar opciones
                    opciones_pendientes = generar_opciones(personaje, 4)
                    guardar(personaje, opciones_pendientes, hacer_backup=True)

                    # Verificar si murió durante la expedición
                    if not personaje.esta_vivo():
                        pausa()
                        procesar_muerte(personaje, "heridas de expedición")
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
    from engine.mundo import generar_opciones
    from engine.personaje import Sobreviviente

    print("[BOT] Iniciando ciclo automático...")
    personaje, opciones = cargar()
    if not personaje:
        print("[BOT] Sin guardado. Generando nuevo personaje...")
        personaje = Sobreviviente()

    if not opciones:
        opciones = generar_opciones(personaje, 4)

    # Elegir expedición
    if 0 <= num_opcion < len(opciones):
        area = opciones[num_opcion]
    else:
        area = _bot_elegir(personaje, opciones)

    print(f"[BOT] → {area['nombre']} (peligro {area['peligro']})")
    log_term, _, ruta_img, _ = resolver_expedicion(personaje, area, exportar_img=True)
    print(log_term)
    if ruta_img:
        print(f"[BOT] Imagen: {ruta_img}")

    nuevas = generar_opciones(personaje, 4)
    guardar(personaje, nuevas, hacer_backup=True)
    print("[BOT] Estado guardado. Listo para publicar.")

    if not personaje.esta_vivo():
        from engine.save_manager import registrar_muerte, borrar_guardado
        pos = registrar_muerte(personaje, "expedición fatal")
        borrar_guardado()
        print(f"[BOT] Personaje muerto. Posición #{pos} en el ranking.")


def _bot_elegir(personaje, opciones):
    puntajes = []
    for area in opciones:
        p = 50
        loot = area.get("loot_chances", {})
        if personaje.hambre > 70 and any("comida" in k for k in loot): p += 30
        if personaje.sed    > 70 and any("agua"   in k for k in loot): p += 35
        if personaje.salud  < personaje.salud_max * 0.5 and any("medicina" in k for k in loot): p += 40
        p -= area["peligro"] * (10 if personaje.salud < personaje.salud_max * 0.4 else 3)
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
    from engine.save_manager import cargar, hay_guardado, info_guardado, \
                                    borrar_guardado, guardar, mostrar_leaderboard
    from engine.personaje import Sobreviviente
    from data.personajes  import BACKGROUNDS

    cls(); print(LOGO)
    print(f"  {AM}╔═══════════════════════════════════╗")
    print(f"  ║          MENÚ PRINCIPAL           ║")
    print(f"  ╚═══════════════════════════════════╝{R}\n")

    info = info_guardado()
    if info:
        bg_nombre = BACKGROUNDS.get(info["background"], {}).get("nombre", info["background"])
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
            resp = input(f"  {AM}¿Borrar partida actual y empezar de nuevo? [s/N]: {R}").strip().lower()
            if resp != "s": menu_inicio(); return
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
