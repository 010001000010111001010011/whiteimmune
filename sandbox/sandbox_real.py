#!/usr/bin/env python3
"""Sandbox REAL de WhiteImmune (Linux, aislamiento de kernel).

A diferencia del prototipo (sandbox/sandbox.py), este módulo ejecuta
el archivo dentro de namespaces del kernel Linux, creados con
`unshare`:

- Namespace de usuario (-U -r): el proceso cree ser root, pero en
  realidad está mapeado al usuario que lanzó el sandbox.
- Namespace de montaje (-m): los montajes de dentro no afectan al
  equipo real; todo se marca privado (sin propagación).
- Namespace de red (-n): la red está muerta. Solo existe el loopback
  apagado; cualquier conexión da "Network is unreachable".
- Sistema de archivos: el script entra por un directorio montado en
  SOLO LECTURA (bind + remount ro). Los directorios del equipo
  (/etc, /home, /var, /tmp, /root, /srv, /opt) se cubren con tmpfs:
  lo que el script escriba ahí desaparece al salir y nunca toca el
  disco real. El único lugar persistente es un directorio temporal
  de salida, que se lee y se borra al terminar.
- Límites: timeout del proceso, límite de CPU y de memoria (prlimit),
  entorno mínimo y directorio de trabajo = la salida temporal.

Antes de ejecutar, reutiliza la puntuación estática de sandbox.py:
si el puntaje es alto, SE NIEGA a ejecutar, sin excepciones.

REQUISITOS: Linux con `unshare` (util-linux). En Windows no funciona:
el prototipo (sandbox.py) sigue siendo la opción ahí.

LIMITES HONESTOS:
- Solo ejecuta archivos benignos que el usuario YA revisó. Nunca
  malware real, nunca muestras peligrosas.
- La puntuación estática por cadenas es una heurística débil: orienta,
  no condena. La negativa por puntaje alto es una red de seguridad,
  no una prueba de malicia.
- En una máquina donde el usuario ya es root, el namespace de usuario
  aporta menos (el mapeo es root->root); las garantías reales ahí son
  la red muerta, los tmpfs y los límites.
- Esto es aislamiento para observación defensiva, no una certificación
  de seguridad absoluta.

Uso:
    python3 sandbox_real.py <archivo>              # análisis + ejecución
    python3 sandbox_real.py <archivo> --timeout 10 # timeout en segundos
"""

import os
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

# Reutiliza el análisis estático del prototipo, sin duplicar lógica.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sandbox.sandbox import UMBRAL_NO_EJECUTAR, analisis_estatico  # noqa: E402

# Directorios del equipo que se cubren con tmpfs dentro del sandbox.
# OJO: /tmp se cubre DESPUÉS de montar entrada/salida, porque los
# puntos de montaje /wim_entrada y /wim_salida ya están fijados.
DIRS_CUBIERTOS = ["/etc", "/home", "/var", "/tmp", "/root", "/srv", "/opt"]

TIMEOUT_SEG_DEF = 15
CPU_SEG_DEF = 30
MEM_MB_DEF = 512

# Script interno: se ejecuta con `bash -c` dentro de los namespaces.
# $1 = directorio de entrada (host), $2 = directorio de salida (host).
SCRIPT_INTERNO = r"""
set -u
ENTRADA="$1"
SALIDA="$2"
mkdir -p /wim_entrada /wim_salida || exit 20
# Sin esto, los montajes podrían propagarse al equipo real: si falla,
# se aborta antes de montar nada.
mount --make-rprivate / 2>/dev/null || exit 25
mount --bind "$ENTRADA" /wim_entrada || exit 21
mount -o remount,ro,bind /wim_entrada || exit 22
mount --bind "$SALIDA" /wim_salida || exit 23
for d in /etc /home /var /tmp /root /srv /opt; do
    mount -t tmpfs tmpfs "$d" 2>/dev/null || true
done
cd /wim_salida || exit 24
exec python3 /wim_entrada/objetivo.py
"""


def _limites(cpu_seg, mem_mb):
    """Preexec: límites de CPU y memoria heredados por todo el árbol."""
    import resource

    def aplicar():
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_seg, cpu_seg))
        except (ValueError, OSError):
            pass
        try:
            resource.setrlimit(resource.RLIMIT_AS,
                               (mem_mb * 1024 * 1024, mem_mb * 1024 * 1024))
        except (ValueError, OSError):
            pass

    return aplicar


def ejecucion_real(ruta, timeout_seg=TIMEOUT_SEG_DEF,
                   cpu_seg=CPU_SEG_DEF, mem_mb=MEM_MB_DEF):
    """Ejecuta un archivo benigno ya revisado dentro del sandbox real.

    Devuelve un dict con el resultado y las garantías aplicadas.
    Si el puntaje estático es alto, se niega sin ejecutar nada.
    """
    if sys.platform.startswith("win"):
        return {"ok": False,
                "error": "el sandbox real requiere Linux con `unshare`"}
    if not shutil.which("unshare"):
        return {"ok": False,
                "error": "`unshare` no disponible en este sistema"}

    estatico = analisis_estatico(ruta)
    if not estatico["ok"]:
        return {"ok": False, "error": estatico.get("error", "sin análisis")}
    if estatico["puntaje"] >= UMBRAL_NO_EJECUTAR:
        return {"ok": False,
                "error": "puntaje estático alto: el sandbox real "
                         "se niega a ejecutar",
                "puntaje": estatico["puntaje"],
                "hallazgos": estatico["hallazgos"]}

    tmp = Path(tempfile.mkdtemp(prefix="wim_sandbox_"))
    entrada = tmp / "entrada"
    salida = tmp / "salida"
    entrada.mkdir()
    salida.mkdir()
    try:
        shutil.copyfile(str(ruta), str(entrada / "objetivo.py"))
        env = {"PATH": "/usr/bin:/bin", "HOME": "/wim_salida",
               "PYTHONDONTWRITEBYTECODE": "1", "LC_ALL": "C.UTF-8"}
        proc = subprocess.Popen(
            ["unshare", "-Urmn", "bash", "-c", SCRIPT_INTERNO,
             "wim", str(entrada), str(salida)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            env=env, preexec_fn=_limites(cpu_seg, mem_mb),
            start_new_session=True,
        )
        try:
            out, err = proc.communicate(timeout=timeout_seg)
            hubo_timeout = False
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            out, err = proc.communicate()
            hubo_timeout = True
        archivos_salida = {}
        for f in sorted(salida.iterdir()):
            if f.is_file() and f.stat().st_size <= 100000:
                try:
                    archivos_salida[f.name] = f.read_text(errors="replace")
                except OSError:
                    pass
        return {
            "ok": True,
            "timeout": hubo_timeout,
            "codigo_salida": proc.returncode,
            "salida": out[-2000:],
            "errores": err[-2000:],
            "puntaje": estatico["puntaje"],
            "sha256": estatico["sha256"],
            "archivos_salida": archivos_salida,
            "aislamiento": {
                "red": "namespace nuevo, sin interfaces (solo loopback apagado)",
                "entrada": "bind en solo lectura",
                "equipo": "tmpfs sobre " + ", ".join(DIRS_CUBIERTOS),
                "salida": "directorio temporal, leído y borrado al terminar",
                "limites": f"timeout {timeout_seg}s, CPU {cpu_seg}s, "
                           f"memoria {mem_mb} MB",
            },
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        # Los puntos de montaje se crean en la raíz dentro del
        # namespace y quedan como directorios vacíos en el equipo:
        # se limpian (rmdir solo borra si están vacíos, es seguro).
        for punto in ("/wim_entrada", "/wim_salida"):
            try:
                os.rmdir(punto)
            except OSError:
                pass


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    timeout = TIMEOUT_SEG_DEF
    for a in sys.argv[1:]:
        if a.startswith("--timeout="):
            try:
                timeout = int(a.split("=", 1)[1])
            except ValueError:
                pass
    if not args:
        print(__doc__)
        return
    resultado = ejecucion_real(args[0], timeout_seg=timeout)
    if not resultado.get("ok"):
        print(f"RECHAZADO / ERROR: {resultado.get('error')}")
        if "puntaje" in resultado:
            print(f"Puntaje estático: {resultado['puntaje']}/100")
            print(f"Hallazgos: {resultado['hallazgos']}")
        return
    print(f"Puntaje estático: {resultado['puntaje']}/100")
    print(f"SHA-256: {resultado['sha256']}")
    print(f"Timeout: {resultado['timeout']}")
    print(f"Código de salida: {resultado['codigo_salida']}")
    print(f"Salida:\n{resultado['salida']}")
    if resultado["errores"]:
        print(f"Errores:\n{resultado['errores']}")
    print(f"Aislamiento: {resultado['aislamiento']}")


if __name__ == "__main__":
    main()
