#!/usr/bin/env python3
"""Red de reputación de amenazas de WhiteImmune (formato + ejemplo).

Idea del concepto: cuando un equipo detecta una amenaza, genera una
ficha y la comparte para que toda la red aprenda. Esto es lo que
hace un sistema inmunológico: lo que aprende un nodo lo protege a
todos.

ESTADO HONESTO: aquí solo está definido el FORMATO de la ficha y
un log local. La red distribuida real (servidores, sincronización
entre nodos, verificación de firmas) es la FASE 2 del roadmap y NO
está implementada en este paquete. No hay servidores reales, no hay
envíos a terceros, no se comparte nada fuera del equipo.

Formato de ficha (JSON):
    {
      "hash": "x7g92",            # identificador del elemento
      "riesgo": 97,               # 0-100, mismo Trust Score del motor
      "comportamiento": "self-replication",  # conducta principal
      "conductas": ["autocopia", "escaneo_red"],
      "origen": "equipo-local",     # quién la reportó
      "fecha": "2026-10-27T..."      # ISO 8601 UTC
    }

Uso:
    python3 reputacion.py ejemplo   # imprime una ficha de ejemplo
    python3 reputacion.py listar    # lista el log local de amenazas
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent.parent
LOG = BASE / "amenazas.jsonl"

CAMPOS_OBLIGATORIOS = ("hash", "riesgo", "comportamiento")


def crear_ficha(hash_valor, riesgo, comportamiento, conductas=None,
                origen="equipo-local"):
    """Crea una ficha de amenaza con el formato del proyecto."""
    return {
        "hash": hash_valor,
        "riesgo": int(riesgo),
        "comportamiento": comportamiento,
        "conductas": list(conductas or []),
        "origen": origen,
        "fecha": datetime.now(timezone.utc).isoformat(),
    }


def validar_ficha(ficha):
    """Valida una ficha: campos obligatorios y riesgo 0-100."""
    for campo in CAMPOS_OBLIGATORIOS:
        if campo not in ficha:
            return False, f"falta el campo: {campo}"
    riesgo = ficha["riesgo"]
    if not isinstance(riesgo, int) or not 0 <= riesgo <= 100:
        return False, "riesgo debe ser un entero entre 0 y 100"
    return True, "válida"


def guardar_ficha(ficha):
    """Guarda una ficha válida en el log local (nada sale del equipo)."""
    ok, mensaje = validar_ficha(ficha)
    if not ok:
        return {"ok": False, "error": mensaje}
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(ficha, ensure_ascii=False) + "\n")
    return {"ok": True, "ficha": ficha}


def listar_fichas():
    """Devuelve las fichas del log local (lista vacía si no hay)."""
    if not LOG.exists():
        return []
    fichas = []
    for linea in LOG.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea:
            fichas.append(json.loads(linea))
    return fichas


def ejemplo():
    """Ficha de ejemplo del concepto original (hash x7g92, riesgo 97)."""
    return crear_ficha(
        "x7g92", 97, "self-replication",
        conductas=["autocopia", "escaneo_red"],
        origen="equipo-ejemplo",
    )


def main():
    args = sys.argv[1:]
    if args and args[0] == "ejemplo":
        print(json.dumps(ejemplo(), indent=2, ensure_ascii=False))
        return
    fichas = listar_fichas()
    print(f"Fichas de amenaza en el log local: {len(fichas)}")
    for f in fichas:
        print(f"- {f['fecha'][:19]} | hash {f['hash']} | "
              f"riesgo {f['riesgo']} | {f['comportamiento']} | "
              f"origen {f['origen']}")


if __name__ == "__main__":
    main()
