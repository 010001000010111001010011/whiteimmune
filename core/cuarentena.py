#!/usr/bin/env python3
"""Cuarentena de WhiteImmune (prototipo defensivo, NO destructivo).

Reglas de seguridad, sin excepciones:
- Registrar un elemento en cuarentena SOLO escribe una línea en un
  log JSONL. No borra, no mueve y no modifica nada por sí solo.
- Mover un archivo a la carpeta de cuarentena solo ocurre si el
  usuario lo aprueba explícitamente (aprobar=True). Nunca es
  automático.
- Nunca se borra nada: "aislar" es mover a una carpeta local, y
  siempre se puede restaurar desde ahí.
- La carpeta de cuarentena está en .gitignore: su contenido jamás
  debe subirse a GitHub.

Uso:
    python3 cuarentena.py registrar "agent.exe" "autocopia" 98
    python3 cuarentena.py listar
    python3 cuarentena.py aislar <ruta> --aprobar   # solo con aprobación
    python3 cuarentena.py restaurar <nombre>
"""

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent.parent
CARPETA = BASE / "cuarentena"
LOG = BASE / "cuarentena.jsonl"


def _ahora():
    return datetime.now(timezone.utc).isoformat()


def registrar(elemento, motivo, riesgo):
    """Registra un elemento en el log de cuarentena (solo escribe)."""
    CARPETA.mkdir(exist_ok=True)
    entrada = {
        "fecha": _ahora(),
        "elemento": elemento,
        "motivo": motivo,
        "riesgo": riesgo,
        "estado": "registrado",
    }
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
    return entrada


def listar():
    """Devuelve todas las entradas del log (lista vacía si no hay)."""
    if not LOG.exists():
        return []
    entradas = []
    for linea in LOG.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea:
            entradas.append(json.loads(linea))
    return entradas


def aislar(ruta, aprobar=False):
    """Mueve un archivo a la carpeta de cuarentena.

    Sin aprobar=True, se niega y no hace nada. Nunca borra.
    """
    if not aprobar:
        return {"ok": False, "error": "aislar requiere aprobación "
                "explícita del usuario (--aprobar)"}
    origen = Path(ruta)
    if not origen.exists():
        return {"ok": False, "error": f"no existe: {ruta}"}
    if not origen.is_file():
        return {"ok": False, "error": "solo se aíslan archivos, "
                "no carpetas"}
    CARPETA.mkdir(exist_ok=True)
    destino = CARPETA / origen.name
    shutil.move(str(origen), str(destino))
    registrar(origen.name, "aislamiento aprobado por el usuario", 0)
    return {"ok": True, "destino": str(destino)}


def restaurar(nombre):
    """Devuelve un archivo de la cuarentena a la carpeta del proyecto."""
    origen = CARPETA / nombre
    if not origen.exists():
        return {"ok": False, "error": f"no está en cuarentena: {nombre}"}
    destino = BASE / nombre
    shutil.move(str(origen), str(destino))
    registrar(nombre, "restaurado por el usuario", 0)
    return {"ok": True, "destino": str(destino)}


def main():
    args = sys.argv[1:]
    if not args or args[0] == "listar":
        entradas = listar()
        print(f"Entradas en cuarentena: {len(entradas)}")
        for e in entradas:
            print(f"- {e['fecha'][:19]} | {e['elemento']} | "
                  f"{e['motivo']} | riesgo {e['riesgo']} | {e['estado']}")
        return
    if args[0] == "registrar" and len(args) >= 4:
        entrada = registrar(args[1], args[2], int(args[3]))
        print(f"Registrado: {entrada}")
        return
    if args[0] == "aislar" and len(args) >= 2:
        print(aislar(args[1], aprobar="--aprobar" in args))
        return
    if args[0] == "restaurar" and len(args) >= 2:
        print(restaurar(args[1]))
        return
    print(__doc__)


if __name__ == "__main__":
    main()
