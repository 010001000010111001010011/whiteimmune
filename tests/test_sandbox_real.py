#!/usr/bin/env python3
"""Pruebas del sandbox REAL de WhiteImmune (Linux + unshare).

(a) Un script benigno corre dentro del sandbox y produce su salida.
(b) Dentro del sandbox la red está muerta (la conexión falla).
(c) Un archivo con puntaje estático alto es rechazado sin ejecutarse.
(d) El timeout corta un script infinito.
(e) El sistema de archivos: no se puede escribir en /etc ni en la
    entrada (solo lectura); sí en el directorio de salida temporal.

Uso: python3 tests/test_sandbox_real.py  (desde la raíz del repo)
Sale con código 0 si todas las pruebas pasan, 1 si alguna falla.
"""

import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sandbox.sandbox_real import ejecucion_real  # noqa: E402

FALLOS = []


def check(nombre, condicion, detalle=""):
    marca = "PASS" if condicion else "FAIL"
    print(f"[{marca}] {nombre} {detalle}")
    if not condicion:
        FALLOS.append(nombre)


def escribir_tmp(nombre, contenido):
    ruta = Path(tempfile.mkdtemp(prefix="wim_test_")) / nombre
    ruta.write_text(contenido)
    return ruta


def main():
    print("== Pruebas del sandbox real ==\n")

    # (a) Script benigno: corre y produce su salida.
    benigno = escribir_tmp("benigno.py",
                           'print("HOLA_DESDE_SANDBOX")\nprint(2 + 2)\n')
    r = ejecucion_real(str(benigno), timeout_seg=15)
    check("(a) benigno corre y da su salida",
          r.get("ok") and "HOLA_DESDE_SANDBOX" in r.get("salida", "")
          and not r.get("timeout"), f"-> {r.get('salida', '')!r:.80}")

    # (b) Red muerta dentro del sandbox.
    red = escribir_tmp("red.py",
                       "import socket\n"
                       "try:\n"
                       "    socket.create_connection(('8.8.8.8', 53), "
                       "timeout=3)\n"
                       "    print('RED_VIVA')\n"
                       "except Exception as e:\n"
                       "    print(f'RED_MUERTA: {type(e).__name__}')\n")
    r = ejecucion_real(str(red), timeout_seg=15)
    check("(b) red muerta dentro del sandbox",
          r.get("ok") and "RED_MUERTA" in r.get("salida", "")
          and "RED_VIVA" not in r.get("salida", ""),
          f"-> {r.get('salida', '')!r:.80}")

    # (c) Puntaje alto: rechazo sin ejecutar.
    sospechoso = escribir_tmp(
        "sospechoso.txt",
        " ".join(["socket", "powershell", "mimikatz", "autorun",
                  "reg add", "curl ", "wget ", "/dev/tcp",
                  "base64"] * 4) + "\n")
    r = ejecucion_real(str(sospechoso), timeout_seg=15)
    check("(c) puntaje alto rechazado sin ejecutar",
          (not r.get("ok")) and "se niega" in r.get("error", ""),
          f"-> puntaje {r.get('puntaje')}, error: {r.get('error')!r:.80}")

    # (d) Timeout corta un bucle infinito.
    infinito = escribir_tmp("infinito.py", "while True:\n    pass\n")
    inicio = time.time()
    r = ejecucion_real(str(infinito), timeout_seg=5)
    duracion = time.time() - inicio
    check("(d) timeout corta el bucle infinito",
          r.get("timeout") is True and duracion < 30,
          f"-> timeout={r.get('timeout')}, duró {duracion:.1f}s")

    # (e) Sistema de archivos. Ojo con el matiz: escribir en /etc
    # DENTRO del sandbox sí "funciona", porque /etc está cubierto con
    # tmpfs: la escritura va a RAM y desaparece al salir. La garantía
    # real es doble: la entrada es de solo lectura (falla) y nada de
    # lo escrito en /etc persiste en el equipo real.
    fs = escribir_tmp("fs.py",
                      "res = {}\n"
                      "for ruta in ['/etc/wim_prueba_fs', "
                      "'/wim_entrada/mal.txt']:\n"
                      "    try:\n"
                      "        open(ruta, 'w').write('x')\n"
                      "        res[ruta] = 'ESCRITO'\n"
                      "    except OSError:\n"
                      "        res[ruta] = 'BLOQUEADO'\n"
                      "open('desde_sandbox.txt', 'w').write('ok')\n"
                      "print(res)\n")
    r = ejecucion_real(str(fs), timeout_seg=15)
    salida = r.get("salida", "")
    check("(e) entrada en solo lectura, salida temporal funciona",
          r.get("ok") and "'/wim_entrada/mal.txt': 'BLOQUEADO'" in salida
          and r.get("archivos_salida", {}).get("desde_sandbox.txt") == "ok",
          f"-> {salida.strip()!r:.100}")
    check("(e) lo escrito en /etc dentro NO persistió en el equipo",
          not Path("/etc/wim_prueba_fs").exists(),
          "-> /etc/wim_prueba_fs ausente en el host")

    print(f"\n{len(FALLOS)} fallos." if FALLOS else "\nTodas las pruebas "
          "pasaron.")
    return 1 if FALLOS else 0


if __name__ == "__main__":
    sys.exit(main())
