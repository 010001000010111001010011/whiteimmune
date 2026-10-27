# WhiteImmune 🛡️

**Un sistema inmunológico digital para Internet — en construcción.**

WhiteImmune no es un antivirus. Es una infraestructura distribuida de
defensa que detecta amenazas **observando comportamientos y
ecosistemas, no firmas conocidas**.

## Filosofía

Los antivirus clásicos preguntan:

> "¿Qué programa es?"

WhiteImmune pregunta:

> "¿Qué está haciendo?"

Lo conocido puede detectarse por firma. Lo desconocido pasa
inadvertido. Si algún día aparecen agentes autónomos capaces de
aprender, cooperar o autorreplicarse, las defensas clásicas podrían
resultar insuficientes. La defensa más resistente no es un policía
digital: es un sistema inmunológico, como los que la naturaleza lleva
miles de millones de años perfeccionando.

## Arquitectura

```
Internet
   │
   ▼
WhiteImmune Network
   │
   ├── Agentes locales (centinela)
   └── Análisis global (reputación + Ecosystem Mapper)
```

### Componentes

| Módulo | Archivo | Qué hace |
|---|---|---|
| Motor de comportamiento | `core/motor_comportamiento.py` | Puntúa conductas: autocopia +30, escaneo de red +15, elevación de privilegios +25, persistencia +20, ofuscación +20. Trust Score 0–100; a los 100 → cuarentena. |
| Centinela | `core/centinela.py` | Observa procesos y conexiones del equipo y los puntúa. **Solo observa: no mata ni bloquea nada.** |
| Cuarentena | `core/cuarentena.py` | Registra elementos aislados. Mover un archivo solo ocurre con aprobación del usuario. Nunca borra nada. |
| Reputación | `network/reputacion.py` | Formato JSON de amenaza compartida (hash, riesgo, comportamiento). La red distribuida real es fase 2. |
| Sandbox | `sandbox/sandbox.py` | Análisis estático + ejecución observada opcional con timeout. Prototipo: no es aislamiento real. |
| Sandbox real | `sandbox/sandbox_real.py` | Aislamiento de verdad en Linux con namespaces (`unshare`): red muerta, entrada en solo lectura, resto cubierto con tmpfs, límites de CPU/memoria y timeout. Reutiliza la puntuación estática: puntaje alto = se niega. |
| Ecosystem Mapper | `ai/ecosystem_mapper.py` | Prototipo SIMULADO: red sintética con patrones emergentes. Detecta un cluster coordinado oculto (78.8/100, ALERTA) y no dispara alarma con tráfico normal (10.0/100). |
| Reporte | `dashboard/reporte.py` | Reporte en texto: estado global, amenazas y cuarentenas. Solo lectura. |
| Pruebas | `tests/` | `test_sandbox_real.py` y `test_mapper.py`, con sus salidas guardadas como evidencia en `tests/evidencia_*.txt`. |

### Ejemplo del motor

```
Proceso conocido (chrome, sin conductas)  → score 4  → OBSERVAR
Proceso desconocido (autocopia, escaneo,
persistencia, ofuscación)                → score 100 → CUARENTENA
```

## Estado honesto del proyecto

**Esto son las bases y un prototipo, NO un producto terminado.**

- ✅ Motor de riesgo por comportamiento (funciona, con ejemplos).
- ✅ Centinela local de observación (funciona, solo observa).
- ✅ Cuarentena no destructiva (solo con aprobación del usuario).
- ✅ Formato de reputación compartida (definido, sin servidores).
- ✅ Sandbox REAL: implementado y **probado en VM** (red muerta,
  entrada en solo lectura, tmpfs, límites y timeout). Requiere Linux
  con `unshare`; en Windows sigue valiendo el prototipo.
- ✅ Ecosystem Mapper: **prototipo simulado** (detecta el cluster
  oculto en la simulación). No es detección sobre Internet real.
- ❌ Red distribuida real: **no implementada** (fase 2).

Límites que se mantienen: la simulación del mapper valida la lógica
del concepto, no prueba nada contra amenazas reales; y un puntaje
alto en una red real podría ser un servicio legítimo (una CDN, una
actualización masiva), así que el mapper orienta y un humano revisa
antes de cualquier acción.

Si buscas protección real hoy, usa un antivirus establecido y buenas
prácticas (contraseñas únicas, 2FA, no abrir archivos desconocidos).
WhiteImmune es una base para construir encima, no un reemplazo.

## Roadmap por fases

- **Fase 0 — Bases (esta versión):** motor, centinela, cuarentena,
  formato de reputación, sandbox prototipo, reporte.
- **Fase 1 — Centinela serio + sandbox real:** mejores heurísticas,
  menos falsos positivos (el mayor enemigo, según la propia evaluación
  del concepto), pruebas en Windows y Linux. El sandbox real y el
  mapper simulado ya están implementados y probados (ver arriba).
- **Fase 2 — Red de reputación:** sincronización entre nodos con
  firmas verificables, sin servidor central obligatorio.
- **Fase 3 — Ecosystem Mapper real:** pasar del simulado a mapas de
  una red observada, para detectar patrones emergentes (crecimiento,
  replicación, cooperación, migración) antes que archivos concretos.
- **Fase 4 — Contención real:** aislamiento a nivel de sistema con
  permisos explícitos del usuario, nunca automático destructivo.

## Uso

Requisitos: Python 3.8 o superior. Sin dependencias externas.

```bash
# Motor de riesgo con los ejemplos del concepto
python core/motor_comportamiento.py

# Centinela: solo observa tu equipo
python core/centinela.py

# Análisis estático de un archivo (sin ejecutarlo)
python sandbox/sandbox.py <archivo>

# Sandbox real (Linux): análisis + ejecución aislada
python sandbox/sandbox_real.py <archivo>

# Ecosystem Mapper simulado (ambos escenarios)
python ai/ecosystem_mapper.py

# Pruebas (desde la raíz del repo)
python tests/test_sandbox_real.py
python tests/test_mapper.py

# Reporte global
python dashboard/reporte.py
```

## Cómo contribuir

Este proyecto existe para que otros lo continúen. Ideas para
empezar:

1. Mejorar las heurísticas del centinela y medir falsos positivos.
2. Diseñar la fase 2 (reputación distribuida con firmas).
3. Llevar el Ecosystem Mapper del simulado a datos reales observados.
4. Escribir pruebas y documentar decisiones.

Abre un issue con tu propuesta antes de un cambio grande, y mantén
la regla de oro: **defensivo, no destructivo, nunca automático**.

## Licencia

MIT. Úsalo, modifícalo y compártelo libremente.

## Aviso

Proyecto de seguridad **defensiva**. No incluye malware real, no
tiene capacidades ofensivas y no debe usarse para dañar, espiar ni
atacar a nadie.
