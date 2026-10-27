#!/usr/bin/env python3
"""Centinela local de WhiteImmune (prototipo, SOLO OBSERVA).

Lista los procesos del equipo y las conexiones de red salientes, y
puntúa cada proceso con el motor de comportamiento
(core/motor_comportamiento.py).

LIMITES HONESTOS DE ESTE PROTOTIPO:
- Solo observa y reporta. NO mata procesos, NO bloquea conexiones,
  NO modifica nada del sistema.
- La heurística es simple: un proceso desconocido con muchas
  conexiones se marca para vigilar, no se condena. Un navegador con
  muchas pestañas también abre muchas conexiones.
- Funciona en Linux (vía /proc) y Windows (vía tasklist). Las
  conexiones se leen con `ss`/`netstat` si están disponibles; si no,
  se informa sin conexiones.

Uso:
    python3 centinela.py            # reporte en texto
    python3 centinela.py --json    # reporte en JSON
"""

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from motor_comportamiento import evaluar_proceso  # noqa: E402

PROCESOS_CONOCIDOS = {
    "chrome", "firefox", "msedge", "code", "python", "python3",
    "explorer", "svchost", "systemd", "bash", "cmd", "powershell",
    "word", "excel", "outlook", "teams", "spotify", "discord",
}

# A partir de cuántas conexiones se considera "muchas" (heurística
# deliberadamente conservadora: solo para vigilar, nunca para actuar).
UMBRAL_MUCHAS_CONEXIONES = 50


def listar_procesos_linux():
    """Lee /proc: devuelve {pid: nombre}."""
    procesos = {}
    proc = Path("/proc")
    if not proc.exists():
        return procesos
    for entrada in proc.iterdir():
        if not entrada.name.isdigit():
            continue
        try:
            nombre = (entrada / "comm").read_text().strip()
        except OSError:
            continue
        procesos[int(entrada.name)] = nombre
    return procesos


def listar_procesos_windows():
    """Usa tasklist: devuelve {pid: nombre}."""
    procesos = {}
    try:
        out = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=30,
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        return procesos
    import csv
    import io
    for fila in csv.reader(io.StringIO(out)):
        if len(fila) >= 2:
            try:
                procesos[int(fila[1])] = fila[0]
            except ValueError:
                continue
    return procesos


def listar_procesos():
    if os.name == "nt":
        return listar_procesos_windows()
    return listar_procesos_linux()


def contar_conexiones_por_pid():
    """Cuenta conexiones TCP/UDP por PID con ss o netstat (si existen)."""
    for cmd in (["ss", "-tunp"], ["netstat", "-tunp"]):
        try:
            out = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
            ).stdout
        except (OSError, subprocess.TimeoutExpired):
            continue
        conteo = {}
        for linea in out.splitlines():
            if "pid=" not in linea:
                continue
            try:
                pid = int(linea.split("pid=")[1].split(",")[0])
            except (ValueError, IndexError):
                continue
            conteo[pid] = conteo.get(pid, 0) + 1
        return conteo
    return {}


def observar():
    """Observa el equipo y devuelve el reporte (sin actuar)."""
    procesos = listar_procesos()
    conexiones = contar_conexiones_por_pid()
    filas = []
    for pid, nombre in sorted(procesos.items()):
        n_conex = conexiones.get(pid, 0)
        conductas = []
        # Heurística conservadora: solo se marca conducta si el proceso
        # es desconocido Y abre muchas conexiones. Nunca basta una sola
        # señal para condenar.
        if (nombre.lower().replace(".exe", "") not in PROCESOS_CONOCIDOS
                and n_conex >= UMBRAL_MUCHAS_CONEXIONES):
            conductas.append("escaneo_red")
        resultado = evaluar_proceso(nombre, conductas)
        resultado["pid"] = pid
        resultado["conexiones"] = n_conex
        filas.append(resultado)
    # Los de mayor riesgo primero.
    filas.sort(key=lambda r: r["score"], reverse=True)
    return filas


def main():
    filas = observar()
    if "--json" in sys.argv:
        print(json.dumps(filas, indent=2, ensure_ascii=False))
        return
    print("=== Centinela WhiteImmune: solo observa, no actúa ===\n")
    print(f"Procesos observados: {len(filas)}")
    altos = [f for f in filas if f["nivel"] in ("ALTO", "CRITICO")]
    print(f"En alerta alta/crítica: {len(altos)}")
    print("\n--- Los 15 de mayor riesgo ---")
    for f in filas[:15]:
        print(f"PID {f['pid']:>6} | {f['proceso']:<30} | "
              f"conex: {f['conexiones']:>3} | score {f['score']:>3} "
              f"| {f['nivel']} -> {f['accion']}")
    print("\nNota: un puntaje alto aquí es solo una señal para revisar, "
          "no una condena. El centinela nunca mata ni bloquea nada.")


if __name__ == "__main__":
    main()
