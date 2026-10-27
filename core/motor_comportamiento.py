#!/usr/bin/env python3
"""Motor de riesgo por comportamiento de WhiteImmune (prototipo defensivo).

Idea central del proyecto: no preguntar "¿qué programa es?" (firmas),
sino "¿qué está haciendo?" (conducta). Cada conducta observada suma
riesgo; al superar el umbral, el elemento se deriva a cuarentena.

Pesos del concepto original de Ped:
    autocopia (self-replication)      +30
    escaneo de red                     +15
    elevación de privilegios          +25
    persistencia                       +20
    ofuscación                         +20

Trust Score: 0 (seguro) a 100 (muy peligroso). La suma bruta puede
superar 100; el score mostrado se limita a 100 y el umbral de
cuarentena es >= 100.

Este módulo SOLO calcula puntajes. No mata procesos, no bloquea nada
y no modifica el sistema: la decisión de aislar la toma el usuario
(ver core/cuarentena.py).
"""

# Conductas reconocidas y su peso.
PESOS = {
    "autocopia": 30,            # crea copias de sí mismo
    "escaneo_red": 15,          # escanea la red o abre muchas conexiones
    "elevacion_privilegios": 25,  # busca permisos de administrador
    "persistencia": 20,         # intenta sobrevivir a reinicios
    "ofuscacion": 20,           # esconde su código o su origen
}

# Puntaje base según lo conocido que sea el proceso (concepto original:
# Chrome 4, Excel 7, proceso desconocido alto).
BASE_CONOCIDO = {
    "chrome": 4,
    "firefox": 4,
    "excel": 7,
    "word": 6,
    "code": 5,
    "python": 5,
}
BASE_DESCONOCIDO = 15

UMBRAL_CUARENTENA = 100


def evaluar_conductas(conductas):
    """Suma los pesos de una lista de conductas. Ignora las desconocidas."""
    total = 0
    detalle = {}
    for c in conductas:
        peso = PESOS.get(c)
        if peso is not None:
            total += peso
            detalle[c] = peso
    return total, detalle


def evaluar_proceso(nombre, conductas):
    """Devuelve el dict de riesgo de un proceso.

    nombre: nombre del proceso (p. ej. "chrome", "agent.exe").
    conductas: lista de conductas observadas (claves de PESOS).
    """
    clave = (nombre or "").lower().replace(".exe", "")
    base = BASE_CONOCIDO.get(clave, BASE_DESCONOCIDO)
    suma_conductas, detalle = evaluar_conductas(conductas)
    suma = base + suma_conductas
    score = min(100, suma)
    if score >= 100:
        nivel, accion = "CRITICO", "CUARENTENA"
    elif score >= 70:
        nivel, accion = "ALTO", "ALERTA"
    elif score >= 30:
        nivel, accion = "MEDIO", "VIGILAR"
    else:
        nivel, accion = "BAJO", "OBSERVAR"
    return {
        "proceso": nombre,
        "conductas": detalle,
        "base": base,
        "suma": suma,
        "score": score,
        "nivel": nivel,
        "accion": accion,
    }


def mostrar(resultado):
    """Imprime un resultado de forma legible."""
    print(f"Proceso: {resultado['proceso']}")
    print(f"  Conductas: {resultado['conductas'] or 'ninguna'}")
    print(f"  Base: {resultado['base']} + conductas: "
          f"{resultado['suma'] - resultado['base']} = {resultado['suma']} "
          f"(score {resultado['score']}/100)")
    print(f"  Nivel: {resultado['nivel']} -> {resultado['accion']}")


if __name__ == "__main__":
    print("=== Ejemplos del concepto WhiteImmune ===\n")
    print("--- Proceso conocido, sin conductas sospechosas ---")
    mostrar(evaluar_proceso("chrome", []))
    print("\n--- Proceso conocido, sin conductas sospechosas ---")
    mostrar(evaluar_proceso("excel", []))
    print("\n--- Proceso desconocido, varias conductas (caso del concepto) ---")
    mostrar(evaluar_proceso("agent.exe", [
        "autocopia", "escaneo_red", "persistencia", "ofuscacion",
    ]))
    print("\n--- Proceso desconocido, todas las conductas ---")
    mostrar(evaluar_proceso("desconocido", list(PESOS)))
