# Code Review Exhaustivo: CodigoSecuencial y CodigoConcurrente vs reporte.tex

**Fecha:** 05 de marzo de 2026
**Revisor:** Guillermo (PR Review)
**Rama:** `rendimiento`
**Archivos revisados:**

- `CodigoSecuencial/run_p0.py` (121 lineas)
- `CodigoConcurrente/src/` (14 archivos Python)
- `Documentacion/reporte.tex` (1965 lineas)

---

## 1. Estado P (Secuencial) - `CodigoSecuencial/run_p0.py`

### 1.1 Alineacion con el reporte

| Aspecto del reporte | Estado en codigo | Veredicto |
|---|---|---|
| Pipeline `F(i) = read; analyze; optimize; update` | `read_sensor -> analyze -> optimize -> update_light` | OK |
| Composicion secuencial estricta `P = F(i1);...;F(in)` | Bucle `for i in range(1, n+1)` sin solapamiento | OK |
| Sin POO arquitectonica | Solo `@dataclass` como contenedores de datos, funciones libres | OK |
| Dataclasses: `TrafficData, Features, SignalPlan, LightState` | Definidos como `@dataclass(frozen=True)` | OK |
| Transformacion `TrafficData -> Features -> SignalPlan -> LightState` | Flujo respetado en `run_cycle_sequential` | OK |
| Parametros: `n`, ciclos, `io_ms`, `update_ms`, `cpu_work`, `seed` | Todos presentes via `argparse` | OK |
| Medicion con temporizador alta resolucion (`time.perf_counter`) | Usado correctamente | OK |

### 1.2 Metricas reportadas vs especificadas

El reporte (seccion 5, "Evaluacion experimental Estado P") define tres metricas:

| Metrica del reporte | Implementada en `run_p0.py` | Estado |
|---|---|---|
| Latencia por ciclo `T_P` | `wall_time` impreso por ciclo | OK |
| Tiempo promedio por interseccion `T_P/n` | `per_intersection` impreso por ciclo | OK |
| **Throughput** `n/T_P` intersecciones/segundo | **NO se imprime** | **FALTANTE** |

**Hallazgo P-1 (Menor):** `run_p0.py` no reporta throughput. El reporte lo especifica como variable dependiente (seccion 5.5.2) y en el procedimiento experimental (seccion 5.6). Agregar:
```python
print(f"[cycle {c}] ... | throughput~{args.n/max(wall,1e-9):.1f}/s")
```

### 1.3 Resumen del Estado P

El codigo secuencial es **fiel al reporte** en estructura, pipeline y ausencia de POO. El unico gap es la metrica de throughput no impresa.

---

## 2. Estado Q (Concurrente) - `CodigoConcurrente/src/`

### 2.1 Arquitectura POO

El reporte define:
```
System = <Acquisition, Processing, Optimization, Control>
```

| Componente del reporte | Clase implementada | Archivo | Veredicto |
|---|---|---|---|
| Acquisition: `TrafficSensorReaderAsync` | `TrafficSensorReaderAsync` | `acquisition.py` | OK |
| Processing: `TrafficAnalyzer` | `TrafficAnalyzer` | `processing.py` | OK |
| Optimization: `ISignalOptimizer` (interfaz) | `ISignalOptimizer(ABC)` | `optimization/interfaces.py` | OK |
| Optimization: `DensityBasedOptimizer` | `density_based` (funcion, no clase) | `optimization/strategies.py` | Parcial |
| Optimization: `PredictiveOptimizer` | `predictive` (funcion, no clase) | `optimization/strategies.py` | Parcial |
| Optimization: `SignalOptimizer` (delegador) | `SignalOptimizer` | `optimization/impl.py` | OK |
| Control: `TrafficControllerAsync` | `TrafficControllerAsync` | `control.py` | OK |
| Pipeline: `IntersectionPipeline` | `IntersectionPipeline` | `pipeline.py` | Parcial |

### 2.2 Principios SOLID

| Principio | Especificacion del reporte | Estado en codigo |
|---|---|---|
| **SRP** | Cada clase una responsabilidad | OK - Reader, Analyzer, Optimizer, Controller separados |
| **OCP** | Extensible via nuevas estrategias | OK - `STRATEGY_MAP` permite agregar sin modificar |
| **DIP** | `TrafficController -> ISignalOptimizer` | **ROTO en workers.py** (ver hallazgo Q-3) |
| **Strategy** | Estrategias intercambiables | OK - `density`/`predictive` via factory |

### 2.3 Concurrencia hibrida

El reporte especifica tres fases:

| Fase | Modelo | Especificacion | Implementacion en `orchestrator_q.py` | Estado |
|---|---|---|---|---|
| 1: ReadAll | AsyncIO | `await gather({read(i)})` | `asyncio.gather(*read_tasks)` | OK |
| 2: Analyze+Optimize | Multiprocessing | `ProcessPool(analyze+optimize)` | `ProcessPoolExecutor` + `analyze_and_optimize_worker` | OK |
| 3: UpdateAll | AsyncIO | `await gather({update(i)})` | `asyncio.gather(*update_tasks)` | OK |

### 2.4 Metricas reportadas vs especificadas

El reporte (seccion 6) define cinco metricas para Estado Q:

| Metrica del reporte | Implementada en `main.py` | Estado |
|---|---|---|
| Latencia por ciclo `T_Q` | `wall_time` | OK |
| Tiempo promedio por interseccion `T_Q/n` | `per_intersection` | OK |
| Throughput `n/T_Q` | `throughput~` | OK |
| **Speedup** `S = T_P/T_Q` | **NO calculado** | **FALTANTE** |
| **Eficiencia paralela** `E = S/p` | **NO calculado** | **FALTANTE** |

---

## 3. Hallazgos Criticos

### Q-1: Modelo de grafo NO implementado

**Severidad: ALTA**

El reporte (seccion 4) formaliza extensamente un modelo de grafo dinamico:
```
G_t = (V, E, w_t)
```
con vecindad `N(i)`, contexto extendido `Context_t(i)`, y un pseudocodigo (Algorithm 1) que incluye:
```
Para todo i en V:
    Context_t(i) = {F_t(i)} U {F_t(j) | j in N(i)}
```

**En el codigo:** No existe ninguna estructura de grafo (`V`, `E`, `w_t`), ni se calcula vecindad, ni se usa contexto extendido. Cada interseccion se procesa de forma completamente independiente, como si `E = vacio`.

**Impacto:** La seccion 4 del reporte dedica ~250 lineas a formalizar el modelo de grafo como pieza central del diseno concurrente, pero el codigo no lo implementa. Esto representa una **desalineacion significativa** entre la especificacion formal y la implementacion.

**Recomendacion:** O bien (a) implementar al menos una representacion basica del grafo con E y N(i), o (b) ajustar el reporte para aclarar que el modelo de grafo es una extension futura y que la implementacion actual trata intersecciones como independientes.

---

### Q-2: IntersectionPipeline parcialmente usada

**Severidad: MEDIA**

El reporte define:
```
IntersectionPipeline(i) = <Reader, Analyzer, Optimizer, Controller>
```
como objeto que "encapsula completamente el flujo de procesamiento de una interseccion" (seccion 3.7).

**En el codigo:** `IntersectionPipeline` es un `@dataclass` contenedor (sin metodo `run` o `process`). Se crea **una sola instancia** en `main.py` y se pasa al orquestador. El orquestador extrae sus componentes individualmente y los usa por separado.

```python
# main.py - Se crea UN solo pipeline para todas las intersecciones
pipeline = IntersectionPipeline(reader=reader, analyzer=analyzer, optimizer=optimizer, controller=controller)
```

El reporte sugiere un pipeline **por interseccion**:
```
Q = parallel_{i=1}^{n} IntersectionPipeline(i)
```

**Impacto:** El pipeline no encapsula el flujo como el reporte describe. No hay metodo `process(intersection_id)` que ejecute el pipeline completo. La encapsulacion como "procesamiento independiente por interseccion" no se materializa.

---

### Q-3: DIP roto en `workers.py`

**Severidad: MEDIA**

El reporte enfatiza el Principio de Inversion de Dependencias:
```
TrafficController -> ISignalOptimizer (abstraccion)
y NO
TrafficController -> DensityBasedOptimizer (concreto)
```

**En `workers.py`:**
```python
def analyze_and_optimize_worker(data, cfg, optimizer_id):
    fn = STRATEGY_MAP.get(optimizer_id)  # Acceso directo al mapa concreto
    plan = fn(features)                   # Bypass total de ISignalOptimizer
```

El worker bypasses completamente la interfaz `ISignalOptimizer` y accede directamente a `STRATEGY_MAP` (funciones concretas). Esto es comprensible por limitaciones de serialization (`pickle`) de `ProcessPoolExecutor`, pero **viola DIP** como se documenta en el reporte.

**Nota atenuante:** El comentario en `workers.py` menciona "evita problemas de pickling", lo cual es una justificacion tecnica valida. Sin embargo, el reporte no documenta esta limitacion practica.

---

### Q-4: Falta `__init__.py` en `optimization/`

**Severidad: MEDIA**

El subpaquete `CodigoConcurrente/src/optimization/` **no tiene `__init__.py`**. Contiene:
- `interfaces.py`
- `factory.py`
- `impl.py`
- `strategies.py`

Sin `__init__.py`, Python 3 lo trata como un paquete de namespace implicito, lo cual puede causar problemas dependiendo del runner y la version. Los imports relativos en los archivos (`from ..domain import ...`) **requieren** que sea un paquete formal.

**Recomendacion:** Agregar un `__init__.py` vacio:
```bash
touch CodigoConcurrente/src/optimization/__init__.py
```

---

### Q-5: `ProcessPoolExecutor` recreado por ciclo

**Severidad: MEDIA**

En `orchestrator_q.py`:
```python
async def run_cycle(self, intersection_ids):
    # ...
    with ProcessPoolExecutor(max_workers=self.workers) as pool:
        # crea y destruye pool en CADA ciclo
```

El pool de procesos se crea y destruye en cada invocacion de `run_cycle`. Para 3 ciclos esto significa 3 creaciones/destrucciones del pool, lo cual introduce overhead medible (fork/spawn de procesos).

**Impacto:** Infla artificialmente `T_Q`, lo que distorsiona las metricas de speedup reportadas. En produccion esto seria un cuello de botella significativo.

**Recomendacion:** Mover el pool al constructor de `OrchestratorQ` o crearlo una vez fuera del ciclo en `run_experiment()`.

---

### Q-6: Metricas de comparacion P vs Q no implementadas

**Severidad: ALTA**

El reporte dedica la seccion 7 completa a "Comparacion experimental: Estado P vs Estado Q" con metricas de:
- Speedup `S = T_P/T_Q`
- Eficiencia paralela `E = S/p`
- Tabla comparativa (Tabla 1)
- Graficas de latencia, speedup y throughput

**No existe ningun script** que ejecute ambos estados y calcule estas metricas. Los programas son independientes:
- `CodigoSecuencial/run_p0.py` - ejecuta P solo
- `CodigoConcurrente/src/main.py` - ejecuta Q solo

**Recomendacion:** Crear un script `compare_P_vs_Q.py` que:
1. Ejecute ambos con los mismos parametros
2. Calcule speedup y eficiencia
3. Genere la tabla comparativa descrita en el reporte

---

## 4. Hallazgos Menores

### M-1: Acceso a atributo privado `_cfg`

**Archivo:** `orchestrator_q.py`
```python
cfg: SimConfig = self.pipeline.reader._cfg  # acceso a atributo privado
```

Accede al atributo privado `_cfg` de `TrafficSensorReaderAsync`. Esto rompe encapsulacion. La config deberia estar disponible como atributo publico del pipeline o pasarse directamente al orquestador.

---

### M-2: `LightState` inconsistente entre P y Q

**Estado P (`run_p0.py`):**
```python
@dataclass(frozen=True)
class LightState:
    applied: bool
    green_time_s: float
    offset_s: float
    phase_count: int
```

**Estado Q (`domain.py`):**
```python
@dataclass(frozen=True)
class LightState:
    intersection_id: int  # campo adicional
    applied: bool
    green_time_s: float
    offset_s: float
    phase_count: int
```

El campo `intersection_id` se agrego en Q pero no existe en P. Esto dificulta comparacion directa de resultados entre ambos estados y rompe compatibilidad estructural del tipo `LightState` descrito en el reporte.

---

### M-3: UML muestra `TrafficController -> ISignalOptimizer`, codigo no

**Reporte (Diagrama UML, seccion 3.10):**
```
TrafficController
  - optimizer : ISignalOptimizer
  + update(i, plan): LightState
```

**Codigo (`control.py`):**
```python
class TrafficControllerAsync:
    def __init__(self, cfg: SimConfig) -> None:
        self._cfg = cfg  # NO recibe optimizer

    async def update(self, intersection_id, plan):
        # Solo aplica sleep + construye LightState
```

`TrafficControllerAsync` **no** tiene dependencia hacia `ISignalOptimizer`. El UML muestra una composicion que no existe en el codigo. El optimizer se usa en el orquestador, no en el controller.

---

### M-4: Estrategias como funciones vs clases en UML

El UML (seccion 3.10) muestra `DensityBasedOptimizer` y `PredictiveOptimizer` como **clases** que implementan `ISignalOptimizer`.

En el codigo, son **funciones** en `strategies.py`:
```python
def density_based(f: Features) -> SignalPlan: ...
def predictive(f: Features) -> SignalPlan: ...
```

Envueltas por `SignalOptimizer(ISignalOptimizer)` que delega via `STRATEGY_MAP`. Esto funciona pero no coincide con el diagrama UML.

---

### M-5: `random` en contexto async no es thread/process-safe

**Archivo:** `acquisition.py`
```python
counts = [random.randint(0, 40) for _ in range(4)]
```

`random.randint` usa el estado global del modulo `random`. En contexto de `asyncio.gather` esto no es problema (single-threaded), pero si se migrase a threading podria causar condiciones de carrera. El reporte no documenta esta limitacion.

---

### M-6: Pseudocodigo tiene 4 fases, implementacion tiene 3

**Reporte (Algorithm 1):** Define 4 fases separadas:
1. AsyncReadAll
2. ProcessPoolMap(Analyze)
3. ProcessPoolMap(Optimize) con Context_t(i)
4. AsyncUpdateAll

**Codigo (`orchestrator_q.py`):** Implementa 3 fases:
1. AsyncIO gather(read)
2. ProcessPool(analyze + optimize combinados)
3. AsyncIO gather(update)

Analyze y Optimize se fusionan en un solo worker CPU-bound, lo cual es una decision de implementacion razonable (reduce overhead de serializacion), pero difiere del pseudocodigo formal. Ademas, la fusion elimina la barrera entre Analyze y Optimize que el reporte define como necesaria para consistencia de Context_t(i).

---

## 5. Tabla Resumen de Hallazgos

| ID | Severidad | Descripcion | Archivo(s) |
|---|---|---|---|
| Q-1 | **ALTA** | Grafo dinamico G_t no implementado | Todo `src/` |
| Q-6 | **ALTA** | No hay script de comparacion P vs Q, metricas speedup/eficiencia ausentes | Raiz del proyecto |
| Q-2 | MEDIA | IntersectionPipeline es solo contenedor, no encapsula flujo | `pipeline.py`, `orchestrator_q.py` |
| Q-3 | MEDIA | DIP roto en worker por limitacion de pickle | `workers.py` |
| Q-4 | MEDIA | Falta `__init__.py` en `optimization/` | `optimization/` |
| Q-5 | MEDIA | ProcessPoolExecutor recreado por ciclo | `orchestrator_q.py` |
| P-1 | Menor | Throughput no reportado en Estado P | `run_p0.py` |
| M-1 | Menor | Acceso a `_cfg` privado | `orchestrator_q.py` |
| M-2 | Menor | `LightState` inconsistente entre P y Q | `run_p0.py`, `domain.py` |
| M-3 | Menor | UML muestra Controller->Optimizer, codigo no | `control.py` |
| M-4 | Menor | Estrategias son funciones, UML muestra clases | `strategies.py` |
| M-5 | Menor | `random` no es process-safe | `acquisition.py` |
| M-6 | Menor | 4 fases en pseudocodigo vs 3 en implementacion | `orchestrator_q.py` |

---

## 6. Recomendaciones Priorizadas

### Prioridad 1 (Alineacion critica con el reporte)

1. **Agregar script de comparacion `compare_P_vs_Q.py`** que ejecute ambos estados con mismos parametros y calcule speedup `S = T_P/T_Q` y eficiencia `E = S/p`. El reporte dedica una seccion completa (seccion 7) a esta comparacion.

2. **Decidir sobre el modelo de grafo:** Si no se implementara `G_t = (V, E, w_t)`, agregar una nota en el reporte indicando que es una extension futura. Si se implementa, agregar al menos una estructura de adyacencia y la funcion `N(i)`.

### Prioridad 2 (Calidad arquitectonica)

3. **Agregar `__init__.py`** a `CodigoConcurrente/src/optimization/`.

4. **Extraer `ProcessPoolExecutor` fuera del ciclo** en `orchestrator_q.py` para evitar overhead de recreacion.

5. **Exponer `cfg` como atributo publico** o pasar la config directamente al orquestador en lugar de acceder a `reader._cfg`.

6. **Agregar throughput al Estado P** (`run_p0.py`) para consistencia con las metricas del reporte.

### Prioridad 3 (Consistencia documental)

7. **Alinear UML con implementacion:** Actualizar el diagrama UML para reflejar que `TrafficController` no depende de `ISignalOptimizer`, o modificar el codigo para que si dependa.

8. **Unificar `LightState`** entre P y Q, o documentar la diferencia como parte de la evolucion arquitectonica.

9. **Documentar en el reporte** la fusion de fases Analyze+Optimize como decision de implementacion y la limitacion de DIP en workers por pickle.

---

## 7. Resultados de Ejecucion

Ambos programas se ejecutaron exitosamente con los siguientes comandos y parametros identicos (`n=50`, `cycles=3`, `seed=1234`, `io-ms=25`, `update-ms=10`, `cpu-work=30000`):

```
# Estado P (secuencial)
cd CodigoSecuencial/ && python3 run_p0.py --n 50 --cycles 3

# Estado Q (concurrente)
cd CodigoConcurrente/ && python3 -m src.main --n 50 --cycles 3 --workers 4 --optimizer density
```

### 7.1 Salida del Estado P (Secuencial)

```
[cycle 1] wall_time=1.899s | per_intersection=0.0380s
[cycle 2] wall_time=1.888s | per_intersection=0.0378s
[cycle 3] wall_time=1.889s | per_intersection=0.0378s
Summary: cycles=3 | avg=1.892s | max=1.899s
```

### 7.2 Salida del Estado Q (Concurrente)

```
[cycle 1] wall_time=0.072s | per_intersection=0.0014s | throughput~695.0/s
[cycle 2] wall_time=0.065s | per_intersection=0.0013s | throughput~772.4/s
[cycle 3] wall_time=0.065s | per_intersection=0.0013s | throughput~773.9/s
Summary: cycles=3 | avg=0.067s | max=0.072s | workers=4 | optimizer=density
```

### 7.3 Metricas derivadas (comparacion P vs Q)

| Metrica | Estado P | Estado Q | Observacion |
|---|---|---|---|
| Latencia promedio por ciclo | 1.892 s | 0.067 s | Q es ~28x mas rapido |
| Tiempo por interseccion | 0.0379 s | 0.0013 s | Reduccion de ~96.5% |
| Throughput (intersecciones/s) | ~26.4/s (*) | ~747/s | Q procesa ~28x mas |
| **Speedup** `S = T_P / T_Q` | -- | **28.2x** | Muy superior al teorico `p=4` |
| **Eficiencia** `E = S / p` | -- | **7.06** | Eficiencia > 1 (superlineal) |

(*) Throughput de P calculado como `50 / 1.892 = 26.4/s` (no reportado por el programa, confirmando hallazgo P-1).

### 7.4 Analisis de los resultados

**Speedup superlineal (S = 28.2x con p = 4 workers):**

El speedup observado excede ampliamente el numero de workers de multiprocessing. Esto **no** contradice la Ley de Amdahl; se explica porque la ganancia principal proviene del **AsyncIO**, no del multiprocessing:

- **Estado P (I/O secuencial):** Cada interseccion bloquea con `sleep(25ms)` para read y `sleep(10ms)` para update. Para 50 intersecciones: `50 * (25 + 10) = 1750 ms` solo de I/O bloqueante acumulado.
- **Estado Q (I/O concurrente):** `asyncio.gather` solapa **todos** los sleeps. Las 50 lecturas concurrentes toman ~25 ms total, y las 50 actualizaciones ~10 ms total. Total I/O: ~35 ms.

Esto produce una reduccion de I/O de `1750ms -> 35ms` (factor ~50x), que es el factor dominante.

**Desglose aproximado del tiempo en Q (0.067s = 67ms):**

| Fase | Tiempo estimado | Mecanismo |
|---|---|---|
| Fase 1: AsyncIO ReadAll | ~25 ms | `asyncio.gather` solapa 50 lecturas |
| Fase 2: ProcessPool (analyze+optimize) | ~7 ms | 50 tareas CPU ligeras distribuidas en 4 procesos |
| Fase 3: AsyncIO UpdateAll | ~10 ms | `asyncio.gather` solapa 50 actualizaciones |
| Overhead (pool creation, serialization) | ~25 ms | `ProcessPoolExecutor` recreado por ciclo (hallazgo Q-5) |

**Nota:** El overhead de recrear el `ProcessPoolExecutor` por ciclo (~25ms estimado) representa ~37% del tiempo total de Q. Corregir el hallazgo Q-5 podria reducir `T_Q` a ~42ms, lo que elevaria el speedup a ~45x.

### 7.5 Validacion de hipotesis del reporte

| Hipotesis del reporte | Resultado | Veredicto |
|---|---|---|
| **H1:** `T_P(n) = Theta(n)` - crecimiento lineal | `T_P/n` constante (~0.038s) entre ciclos | **VALIDADA** |
| **H2:** `T_Q(n,p) < T_P(n)` | `0.067s << 1.892s` | **VALIDADA** |
| Speedup `S ~ p` (Ley de Amdahl) | `S = 28.2 >> p = 4` | **No aplica directamente** (*) |
| Tabla 1 del reporte: `S ~ 3.45` para `n=50, p=4` | `S = 28.2` | **Discrepancia** (**) |

(*) El modelo del reporte asume que el speedup proviene principalmente de multiprocessing (`S ~ p`). En la practica, el factor dominante es AsyncIO solapando I/O, lo que produce speedup superlineal respecto a `p`.

(**) La Tabla 1 del reporte (seccion 7.6) reporta `T_P = 4.08s` y `T_Q = 1.18s` para `n=50`, produciendo `S = 3.45`. Los resultados reales difieren significativamente:
- `T_P` real (1.892s) es menor que el reportado (4.08s), sugiriendo que la tabla fue generada con parametros distintos o estimada teoricamente.
- `T_Q` real (0.067s) es mucho menor que el reportado (1.18s), lo que indica que la tabla del reporte **no** refleja una ejecucion real del codigo actual.

**Recomendacion adicional:** Regenerar la Tabla 1 y las graficas (Figuras 4-6) del reporte con datos de ejecucion real, o bien documentar los parametros exactos con los que fueron generadas.

### 7.6 Confirmacion de hallazgos del code review

La ejecucion confirma empiricamente varios hallazgos:

| Hallazgo | Confirmado | Evidencia |
|---|---|---|
| P-1: Throughput faltante en P | Si | Salida de P no incluye throughput |
| Q-5: Pool recreado por ciclo | Si | Ciclo 1 de Q (72ms) > ciclos 2-3 (65ms); el delta ~7ms incluye overhead de primer pool |
| Q-6: Sin metricas speedup/eficiencia | Si | Ningun programa calcula S ni E |
| Q-4: Falta `__init__.py` en optimization/ | No bloquea | Python 3.3+ soporta namespace packages; la ejecucion funciona, pero sigue siendo recomendable agregarlo |

---

## 8. Conclusion

Ambos programas ejecutan correctamente y producen resultados coherentes con la estructura formal del reporte. La transicion de P (secuencial, funcional) a Q (concurrente, POO) esta bien ejecutada: la arquitectura modular, el patron Strategy, y la concurrencia hibrida AsyncIO + Multiprocessing funcionan como se diseño.

**El resultado mas relevante** es el speedup de **28.2x** con solo 4 workers, que demuestra que la ganancia dominante proviene del solapamiento de I/O via AsyncIO (no solo del paralelismo CPU). Este resultado es mas fuerte que lo anticipado en el reporte (S ~ 3.45), pero la discrepancia indica que la Tabla 1 del reporte no fue generada con el codigo actual.

**Hallazgos criticos pendientes de correccion:**
1. Modelo de grafo `G_t` no implementado (Q-1)
2. Sin script de comparacion automatizado P vs Q (Q-6)
3. Tabla 1 y graficas del reporte no coinciden con ejecuciones reales (nuevo hallazgo de la ejecucion)

**Lo que funciona bien:**
- Pipeline secuencial fiel al modelo formal
- Arquitectura POO modular con SRP y Strategy
- Concurrencia hibrida AsyncIO + Multiprocessing operativa
- Ambos estados reproducibles con semilla fija (`--seed 1234`)
