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
| Reporte | `dashboard/reporte.py` | Reporte en texto: estado global, amenazas y cuarentenas. Solo lectura. |

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
- ⚠️ Sandbox: prototipo. No hay aislamiento real de kernel ni red
  bloqueada a nivel de sistema.
- ❌ Red distribuida real: **no implementada** (fase 2).
- ❌ Ecosystem Mapper: **concepto documentado, no implementado**
  (fase 3).

Si buscas protección real hoy, usa un antivirus establecido y buenas
prácticas (contraseñas únicas, 2FA, no abrir archivos desconocidos).
WhiteImmune es una base para construir encima, no un reemplazo.

## Roadmap por fases

- **Fase 0 — Bases (esta versión):** motor, centinela, cuarentena,
  formato de reputación, sandbox prototipo, reporte.
- **Fase 1 — Centinela serio:** mejores heurísticas, menos falsos
  positivos (el mayor enemigo, según la propia evaluación del
  concepto), pruebas en Windows y Linux.
- **Fase 2 — Red de reputación:** sincronización entre nodos con
  firmas verificables, sin servidor central obligatorio.
- **Fase 3 — Ecosystem Mapper:** mapas vivos de la red para detectar
  patrones emergentes (crecimiento, replicación, cooperación,
  migración) antes que archivos concretos.
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

# Reporte global
python dashboard/reporte.py
```

## Cómo contribuir

Este proyecto existe para que otros lo continúen. Ideas para
empezar:

1. Mejorar las heurísticas del centinela y medir falsos positivos.
2. Diseñar la fase 2 (reputación distribuida con firmas).
3. Prototipar el Ecosystem Mapper con datos simulados.
4. Escribir pruebas y documentar decisiones.

Abre un issue con tu propuesta antes de un cambio grande, y mantén
la regla de oro: **defensivo, no destructivo, nunca automático**.

## Licencia

MIT. Úsalo, modifícalo y compártelo libremente.

## Aviso

Proyecto de seguridad **defensiva**. No incluye malware real, no
tiene capacidades ofensivas y no debe usarse para dañar, espiar ni
atacar a nadie.
