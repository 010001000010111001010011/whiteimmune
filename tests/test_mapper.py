#!/usr/bin/env python3
"""Pruebas del Ecosystem Mapper simulado de WhiteImmune.

Corre dos escenarios sintéticos y verifica que el análisis distingue:
- NORMAL: tráfico disperso, sin cluster -> sin alarma.
- OCULTO: cluster coordinado oculto -> ALERTA.

Uso: python3 tests/test_mapper.py  (desde la raíz del repo)
Sale con código 0 si ambos veredictos son correctos, 1 si no.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from ai.ecosystem_mapper import UMBRAL_ALARMA, analizar  # noqa: E402


def main():
    print("== Pruebas del Ecosystem Mapper (simulado) ==\n")
    fallos = 0
    for con_cluster, esperado in [(False, "sin alarma"),
                                  (True, "ALERTA")]:
        r = analizar(42, con_cluster)
        ok = esperado in r["veredicto"]
        marca = "PASS" if ok else "FAIL"
        print(f"[{marca}] {r['escenario']}")
        print(f"        nodos={r['nodos']}, aristas={r['aristas']}")
        print(f"        métricas={r['metricas']}")
        print(f"        puntaje={r['puntaje']}/100 "
              f"(umbral {UMBRAL_ALARMA}) -> {r['veredicto']}")
        if not ok:
            fallos += 1
    print(f"\n{fallos} fallos." if fallos else "\nAmbos escenarios "
          "detectados correctamente.")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
