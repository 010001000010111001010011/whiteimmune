#!/usr/bin/env python3
"""Sandbox de WhiteImmune (PROTOTIPO, solo análisis defensivo).

Antes de ejecutar algo desconocido: obsérvalo primero.
1. Análisis estático: lee el archivo SIN ejecutarlo, calcula su
   SHA-256 y busca indicadores simples (cadenas sospechosas). Solo
   informa; nunca decide por sí solo.
2. Ejecución observada (opcional): solo si el usuario la pide
   explícitamente (--ejecutar) Y el puntaje estático es bajo. Corre
   con timeout, captura la salida y no hereda el entorno completo.
   Si el puntaje estático es alto, SE NIEGA a ejecutar.

LIMITES HONESTOS:
- Esto es un prototipo, no un sandbox real: no hay aislamiento de
  kernel, ni contenedores, ni red bloqueada a nivel de sistema.
- NUNCA se ejecuta nada dañino real, ni malware, ni muestras
  peligrosas. La ejecución observada es solo para archivos benignos
  que el usuario ya revisó.
- El puntaje estático por cadenas es una heurística débil: un
  programa legítimo puede mencionar "socket" o "powershell" sin ser
  malicioso. Solo orienta, no condena.

Uso:
    python3 sandbox.py <archivo>              # solo análisis estático
    python3 sandbox.py <archivo> --ejecutar   # + ejecución observada
"""

import hashlib
import os
import subprocess
import sys
from pathlib import Path

# Indicadores débiles, solo para orientar (no son prueba de nada).
INDICADORES = {
    "powershell": 15,
    "cmd.exe": 15,
    "/dev/tcp": 20,
    "socket": 5,
    "base64": 5,
    "mimikatz": 40,
    "autorun": 10,
    "reg add": 10,
    "curl ": 5,
    "wget ": 5,
}

UMBRAL_NO_EJECUTAR = 50
TIMEOUT_SEG = 10


def analisis_estatico(ruta):
    """Analiza un archivo sin ejecutarlo. Devuelve un dict."""
    archivo = Path(ruta)
    if not archivo.exists():
        return {"ok": False, "error": f"no existe: {ruta}"}
    datos = archivo.read_bytes()
    sha = hashlib.sha256(datos).hexdigest()
    try:
        texto = datos.decode("utf-8", errors="ignore").lower()
    except Exception:
        texto = ""
    hallazgos = {}
    for indicador, peso in INDICADORES.items():
        if indicador in texto:
            hallazgos[indicador] = peso
    puntaje = min(100, sum(hallazgos.values()))
    return {
        "ok": True,
        "archivo": str(archivo),
        "tamano_bytes": len(datos),
        "sha256": sha,
        "hallazgos": hallazgos,
        "puntaje": puntaje,
        "recomendacion": ("NO EJECUTAR" if puntaje >= UMBRAL_NO_EJECUTAR
                           else "se puede observar con --ejecutar"),
    }


def ejecucion_observada(ruta, puntaje):
    """Ejecución observada, solo si el usuario la pidió y es segura.

    Se niega si el puntaje estático es alto. Usa timeout y un
    entorno mínimo. Solo para archivos benignos ya revisados.
    """
    if puntaje >= UMBRAL_NO_EJECUTAR:
        return {"ok": False, "error": "puntaje estático alto: "
                "el sandbox se niega a ejecutar"}
    try:
        proc = subprocess.run(
            [sys.executable, str(ruta)],
            capture_output=True, text=True, timeout=TIMEOUT_SEG,
            env={"PATH": os.environ.get("PATH", "")},
            cwd=str(Path(ruta).parent),
        )
        return {
            "ok": True,
            "codigo_salida": proc.returncode,
            "salida": proc.stdout[-2000:],
            "errores": proc.stderr[-2000:],
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"timeout de {TIMEOUT_SEG}s: "
                "proceso detenido por exceder el tiempo"}
    except Exception as exc:  # noqa: BLE001 - prototipo informativo
        return {"ok": False, "error": str(exc)}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return
    resultado = analisis_estatico(args[0])
    if not resultado["ok"]:
        print(resultado)
        return
    print(f"Archivo: {resultado['archivo']}")
    print(f"Tamaño: {resultado['tamano_bytes']} bytes")
    print(f"SHA-256: {resultado['sha256']}")
    print(f"Hallazgos: {resultado['hallazgos'] or 'ninguno'}")
    print(f"Puntaje estático: {resultado['puntaje']}/100")
    print(f"Recomendación: {resultado['recomendacion']}")
    if "--ejecutar" in sys.argv:
        print("\n--- Ejecución observada ---")
        print(ejecucion_observada(args[0], resultado["puntaje"]))


if __name__ == "__main__":
    main()
