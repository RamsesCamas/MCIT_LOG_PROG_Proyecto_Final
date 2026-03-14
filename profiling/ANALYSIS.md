# Profiling + Documentación del cuello de botella

## Tabla de distribución del tiempo (Estado P0 - Secuencial)

| Tarea del Pipeline | Funciones / Simulación | Porcentaje del Tiempo Total (%) |
| :--- | :--- | :--- |
| **I/O Simulado** | `read_sensor`, `update_light` (`time.sleep`) | **91.6%** |
| **CPU Simulado** | `analyze` (loop `math.sin` / `math.cos`) | **8.3%** |
| **CPU Ligero** | `optimize` (cálculo en microsegundos) | **< 0.1%** |

## Conclusión
El cuello de botella es I/O (91.6%), no CPU (8.3%), por lo tanto AsyncIO es el mecanismo principal a implementar.

---

## Informe individual: Profiling secuencial, clasificación I/O vs CPU y justificación de estrategia

### 1. Definición de Arquitecturas (Transición P0 a Q0)

* [cite_start]**Estado P0 (Baseline):** Sistema secuencial estricto[cite: 41, 42]. La latencia total del ciclo es la suma lineal de las latencias individuales de cada fase por intersección.
  
  The formula for the total execution time in State P is defined as:
  $$T_{P}=\sum_{i=1}^{n}(t_{r}+t_{c}+t_{u})$$
  [cite_start]Where $T_P$ is the total time, $n$ is the number of intersections, $t_r$ is the read time, $t_c$ is the compute time, and $t_u$ is the update time[cite: 48, 50, 51, 54].

* [cite_start]**Estado Q0 (Mejora actual):** Sistema concurrente cooperativo con AsyncIO[cite: 401]. [cite_start]Mantiene la ejecución de CPU secuencial, pero solapa las esperas de I/O[cite: 406]. 

  The approximate total execution time is:
  $$T_{Q0}\approx\max(t_{read})+\sum(t_{compute})+\max(t_{update})$$

### 2. Justificación Teórica del Cuello de Botella y Elección de Herramienta

El análisis del perfilado (profiling) del Estado P0 demuestra que el sistema pasa la mayor parte del tiempo 'bloqueado' esperando respuestas de sensores y hardware simulados (`time.sleep`). 

[cite_start]Al ser un sistema limitado por I/O (I/O-bound)[cite: 113, 391], `asyncio` es la herramienta adecuada. [cite_start]Permite la **'concurrencia cooperativa'**, donde el hilo principal cede el control para iniciar la siguiente operación de I/O mientras la anterior sigue 'esperando', solapando así las latencias de red/hardware[cite: 393].

### 3. Implementación en el Pipeline (Puntos de la Asignación)

Para materializar esta arquitectura, se realizaron las siguientes modificaciones en el código:

* **Punto 3, 4 y 5 (Transición a asíncrono cooperativo):**
  Las funciones I/O-bound (`read_sensor` y `update_light`) han transitado de ser síncronas bloqueantes (utilizando `time.sleep`) a funciones asíncronas cooperativas (`async def` con `await asyncio.sleep`). Esto permite que, mientras la intersección 'i' espera su dato, ceda el control para iniciar la lectura de la intersección 'i+1', solapando los retardos simulados.

```python
async def read_sensor_async(i: int, io_read_ms: int) -> TrafficData:
    """PUNTO 4: Modificación a 'async'. I/O-bound simulado y concurrente (Fase 1)."""
    await asyncio.sleep(io_read_ms / 1000.0) # cede control sin bloquear el hilo
    # ... (generación de datos simulados) ...
    return TrafficData(counts=counts, timestamps=timestamps)

async def update_light_async(i: int, plan: SignalPlan, io_update_ms: int) -> LightState:
    """PUNTO 5: Modificación a 'async'. I/O-bound simulado y concurrente (Fase 4)."""
    await asyncio.sleep(io_update_ms / 1000.0)
    return LightState(applied=True, green_time_s=plan.green_time_s, offset_s=plan.offset_s, phase_count=plan.phase_count)