#!/usr/bin/env python3
"""Reporte global de WhiteImmune (solo lectura, no actúa).

Genera un reporte en texto con:
- Estado del centinela (procesos observados y los de mayor riesgo).
- Amenazas del log local de reputación.
- Elementos registrados en cuarentena.

No modifica nada: solo lee los logs locales si existen y corre el
centinela en modo observación.

Uso:
    python3 reporte.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
sys.path.insert(0, str(Path(__file__).parent.parent / "network"))
from centinela import observar  # noqa: E402
from reputacion import listar_fichas  # noqa: E402
from cuarentena import listar  # noqa: E402


def main():
    print("=== WhiteImmune: reporte global ===\n")
    try:
        filas = observar()
        print(f"Dispositivos: 1 (este equipo)")
        print(f"Procesos observados: {len(filas)}")
        altos = [f for f in filas if f["nivel"] in ("ALTO", "CRITICO")]
        print(f"Amenazas (riesgo alto/crítico): {len(altos)}")
        for f in altos[:10]:
            print(f"  - {f['proceso']} (PID {f['pid']}): "
                  f"score {f['score']} -> {f['accion']}")
    except Exception as exc:  # noqa: BLE001 - reporte informativo
        print(f"Centinela no disponible: {exc}")
    fichas = listar_fichas()
    print(f"\nFichas de amenaza compartidas (log local): {len(fichas)}")
    for f in fichas[-5:]:
        print(f"  - hash {f['hash']} | riesgo {f['riesgo']} | "
              f"{f['comportamiento']}")
    entradas = listar()
    print(f"\nEn cuarentena (registros): {len(entradas)}")
    for e in entradas[-5:]:
        print(f"  - {e['elemento']} | {e['motivo']} | "
              f"riesgo {e['riesgo']} | {e['estado']}")
    print("\nRecuerda: WhiteImmune en este estado es un prototipo de "
          "observación. Nada de lo listado fue bloqueado ni eliminado "
          "automáticamente.")


if __name__ == "__main__":
    main()
