#!/usr/bin/env python3
"""Ecosystem Mapper de WhiteImmune (PROTOTIPO SIMULADO).

Idea del concepto: si algún día aparece un agente autónomo distribuido
a gran escala, probablemente no se detecte analizando un archivo, sino
observando patrones globales, como un biólogo detecta una especie nueva
por migración, crecimiento, coordinación y consumo de recursos.

Este módulo NO observa Internet real. Construye redes sintéticas y
prueba si el análisis detecta un patrón emergente:

- Escenario NORMAL: nodos con tráfico disperso, crecimiento estable,
  sin coordinación. No debe disparar alarma.
- Escenario OCULTO: la misma base MÁS un cluster coordinado y oculto:
  nodos densamente conectados entre sí, actividad sincronizada en las
  mismas ventanas de tiempo, crecimiento exponencial de conexiones,
  nodos nuevos que se conectan primero al cluster (replicación) y
  aristas que cruzan regiones (migración). Debe disparar alarma.

Métricas (cada una 0-1) y peso en el puntaje final (0-100):
- densidad del subconjunto más conectado (30%): aristas internas
  frente al máximo posible. Un cluster real es denso; tráfico normal
  es disperso.
- sincronía (30%): fracción de ventanas de tiempo en las que más de
  la mitad del subconjunto está activo a la vez.
- crecimiento (20%): cuánto más rápido crecen las aristas internas
  del subconjunto que las del resto de la red.
- replicación (10%): fracción de nodos nuevos cuya primera conexión
  va al subconjunto.
- migración (10%): fracción de aristas del subconjunto que cruzan
  entre regiones distintas.

Umbral de alarma: 60/100. Todo determinista (semilla fija), para que
las pruebas sean reproducibles.

LIMITES HONESTOS:
- Simulación, no detección real. Validar la lógica del concepto, no
  probar nada contra amenazas reales.
- Un puntaje alto en una red real podría ser un servicio legítimo
  (una CDN, una actualización masiva). El mapper orienta, no condena:
  un humano debe revisar antes de cualquier acción.

Uso:
    python3 ecosystem_mapper.py          # ambos escenarios
    python3 ecosystem_mapper.py --json   # salida en JSON
"""

import json
import random
import sys
from collections import defaultdict

UMBRAL_ALARMA = 60
VENTANAS = 24          # ventanas de tiempo de la simulación
NODOS_BASE = 120
NODOS_CLUSTER = 15


def _nodos_y_aristas(semilla, con_cluster):
    """Construye una red sintética. Devuelve (nodos, aristas, pasos).

    nodos: {id: {"region": str, "activo": set(ventanas)}}
    aristas: lista de (a, b, paso, region_a, region_b)
    pasos: número de pasos de crecimiento simulados.
    """
    rnd = random.Random(semilla)
    regiones = ["norte", "sur", "este", "oeste"]
    nodos = {}
    for i in range(NODOS_BASE):
        nodos[f"n{i}"] = {
            "region": regiones[i % 4],
            "activo": set(rnd.sample(range(VENTANAS), rnd.randint(3, 8))),
        }
    aristas = []
    # Tráfico normal: aristas dispersas entre nodos cualesquiera.
    for _ in range(300):
        a, b = rnd.sample(sorted(nodos), 2)
        aristas.append((a, b, 0, nodos[a]["region"], nodos[b]["region"]))

    nuevos_al_cluster = 0
    nuevos_totales = 0
    if con_cluster:
        cluster = [f"c{i}" for i in range(NODOS_CLUSTER)]
        # Ventanas sincronizadas: el cluster actúa siempre junto.
        ventanas_cluster = set(rnd.sample(range(VENTANAS), 10))
        for i, cid in enumerate(cluster):
            nodos[cid] = {"region": regiones[i % 4],
                          "activo": set(ventanas_cluster)}
        # Crecimiento exponencial de aristas internas por pasos.
        internas = 0
        for paso in range(1, 6):
            nuevas = 4 * (2 ** (paso - 1))  # 4, 8, 16, 32, 64
            for _ in range(nuevas):
                a, b = rnd.sample(cluster, 2)
                aristas.append((a, b, paso, nodos[a]["region"],
                                nodos[b]["region"]))
                internas += 1
        # Replicación: nodos nuevos que se conectan primero al cluster.
        for j in range(20):
            nid = f"r{j}"
            nodos[nid] = {"region": rnd.choice(regiones),
                          "activo": set(ventanas_cluster)}
            destino = rnd.choice(cluster)
            aristas.append((nid, destino, 5, nodos[nid]["region"],
                            nodos[destino]["region"]))
            nuevos_al_cluster += 1
            nuevos_totales += 1
    return nodos, aristas, nuevos_al_cluster, nuevos_totales


def _subconjunto_sospechoso(nodos, aristas, k=15):
    """Top-k nodos por grado (los más conectados)."""
    grado = defaultdict(int)
    for a, b, _, _, _ in aristas:
        grado[a] += 1
        grado[b] += 1
    top = sorted(grado, key=lambda n: -grado[n])[:k]
    return set(top)


def analizar(semilla=42, con_cluster=False):
    """Analiza un escenario y devuelve métricas + puntaje + veredicto."""
    nodos, aristas, nuevos_al_cluster, nuevos_totales = _nodos_y_aristas(
        semilla, con_cluster)
    sub = _subconjunto_sospechoso(nodos, aristas)

    # Densidad interna del subconjunto (pares únicos, sin repetir).
    internas = [(a, b, p, ra, rb) for a, b, p, ra, rb in aristas
                if a in sub and b in sub]
    pares_unicos = {(a, b) for a, b, _, _, _ in internas}
    max_posibles = len(sub) * (len(sub) - 1) // 2
    densidad = len(pares_unicos) / max_posibles if max_posibles else 0.0

    # Sincronía: ventanas donde >50% del subconjunto está activo.
    sinc = 0
    for v in range(VENTANAS):
        activos = sum(1 for n in sub if v in nodos[n]["activo"])
        if activos > len(sub) / 2:
            sinc += 1
    sincronia = sinc / VENTANAS

    # Crecimiento: aristas internas por paso (último paso vs primero).
    por_paso = defaultdict(int)
    for a, b, paso, _, _ in aristas:
        if a in sub and b in sub:
            por_paso[paso] += 1
    pasos = sorted(por_paso)
    if len(pasos) >= 2 and por_paso[pasos[0]] > 0:
        crecimiento = min(1.0, (por_paso[pasos[-1]] /
                                por_paso[pasos[0]] - 1) / 5.0)
    else:
        crecimiento = 0.0

    # Replicación y migración.
    replicacion = (nuevos_al_cluster / nuevos_totales
                   if nuevos_totales else 0.0)
    cruzan = sum(1 for _, _, _, ra, rb in internas if ra != rb)
    migracion = cruzan / len(internas) if internas else 0.0

    puntaje = round(min(100.0, densidad * 30 + sincronia * 30 +
                        crecimiento * 20 + replicacion * 10 +
                        migracion * 10), 1)
    return {
        "escenario": "OCULTO (con cluster coordinado)"
                     if con_cluster else "NORMAL (sin cluster)",
        "nodos": len(nodos),
        "aristas": len(aristas),
        "subconjunto": sorted(sub),
        "metricas": {
            "densidad": round(densidad, 3),
            "sincronia": round(sincronia, 3),
            "crecimiento": round(crecimiento, 3),
            "replicacion": round(replicacion, 3),
            "migracion": round(migracion, 3),
        },
        "puntaje": puntaje,
        "veredicto": ("ALERTA: patrón emergente coordinado"
                      if puntaje >= UMBRAL_ALARMA
                      else "sin alarma: tráfico disperso"),
    }


def main():
    resultados = [analizar(42, False), analizar(42, True)]
    if "--json" in sys.argv:
        print(json.dumps(resultados, indent=2, ensure_ascii=False))
        return
    for r in resultados:
        print(f"\n=== {r['escenario']} ===")
        print(f"Nodos: {r['nodos']}, aristas: {r['aristas']}")
        print(f"Métricas: {r['metricas']}")
        print(f"Puntaje: {r['puntaje']}/100 (umbral {UMBRAL_ALARMA})")
        print(f"Veredicto: {r['veredicto']}")


if __name__ == "__main__":
    main()
