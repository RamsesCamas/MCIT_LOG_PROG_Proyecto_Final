# Propuesta de Mejoras: Proyecto Final - Sincronizacion de Semaforos

**Fecha:** 05 de marzo de 2026
**Autor:** Guillermo
**Rama:** `rendimiento`
**Documento base:** `CODE_REVIEW_PR_GUILLERMO_050326.md`

---

## 1. Logica de Hoare

### 1.1 Tripletas describen 3 etapas, codigo tiene 4

**Estado actual:** El reporte (seccion 1.8) formaliza:

```
{traffic_data(i)}  read(i)     {raw_data(i)}
{raw_data(i)}      compute(i)  {timing(i)}
{timing(i)}        update(i)   {light_state(i)}
```

Pero el codigo implementa 4 etapas: `read -> analyze -> optimize -> update`. Las tripletas no cubren la separacion `analyze`/`optimize`. La seccion 4.5 del reporte si las define por separado, pero las tripletas originales nunca se actualizan, creando inconsistencia interna.

**Mejora propuesta:** Reemplazar las tripletas de la seccion 1.8 por las 4 etapas reales:

```
{traffic_data(i)}   read(i)      {raw_data(i)}
{raw_data(i)}       analyze(i)   {features(i)}
{features(i)}       optimize(i)  {signal_plan(i)}
{signal_plan(i)}    update(i)    {light_state(i)}
```

**Severidad:** Media
**Archivos afectados:** `Documentacion/reporte.tex` (seccion 1.8)

---

### 1.2 Precondiciones nunca verificadas

**Estado actual:** La tripleta del ciclo concurrente:

```
{G_t ∧ SensorsReady}  Q_t  {LightsUpdated ∧ ConsistentPlans}
```

- `G_t` (grafo dinamico) no existe en el codigo
- `SensorsReady` nunca se verifica
- `read_sensor(i)` ignora el parametro `i` para generar datos — no indexa ningun sensor real

```python
# run_p0.py:43-44
def read_sensor(i: int, io_read_ms: int) -> TrafficData:
    time.sleep(io_read_ms / 1000.0)
    counts = [random.randint(0, 40) for _ in range(4)]  # i no se usa
```

**Mejora propuesta:** Dos opciones:

**(a) Minima (ajustar reporte):** Reemplazar la precondicion por una que refleje la simulacion:

```
{n > 0 ∧ cfg_valid}  Q_t  {|results| = n ∧ ∀i: applied(i) = True}
```

**(b) Completa (ajustar codigo):** Agregar validacion de precondiciones con asserts o guardas:

```python
def read_sensor(i: int, io_read_ms: int) -> TrafficData:
    assert i > 0, f"intersection_id must be positive, got {i}"
    assert io_read_ms >= 0, f"io_read_ms must be non-negative, got {io_read_ms}"
    ...
```

**Severidad:** Alta
**Archivos afectados:** `Documentacion/reporte.tex`, `CodigoSecuencial/run_p0.py`, `CodigoConcurrente/src/acquisition.py`

---

### 1.3 Postcondicion `applied=True` trivial

**Estado actual:** Tanto en P como en Q, update siempre retorna `applied=True`:

```python
# control.py:12
return LightState(intersection_id=intersection_id, applied=True, ...)
```

No existe camino donde `applied=False`. La tripleta se cumple trivialmente porque no hay posibilidad de falla.

**Mejora propuesta:** Introducir al menos un camino de falla simulado para que la postcondicion sea significativa:

```python
async def update(self, intersection_id: int, plan: SignalPlan) -> LightState:
    await asyncio.sleep(self._cfg.io_update_ms / 1000.0)
    success = random.random() > 0.01  # 1% de falla simulada
    return LightState(
        intersection_id=intersection_id,
        applied=success,
        green_time_s=plan.green_time_s if success else 0.0,
        offset_s=plan.offset_s if success else 0.0,
        phase_count=plan.phase_count if success else 0,
    )
```

**Severidad:** Baja
**Archivos afectados:** `CodigoConcurrente/src/control.py`, `CodigoSecuencial/run_p0.py`

---

### 1.4 Falta invariante de ciclo

**Estado actual:** El reporte no define un invariante para el bucle de ciclos (`for c in range(1, cycles+1)`). No hay formalizacion de que cada ciclo deja el sistema en estado valido antes del siguiente.

**Mejora propuesta:** Agregar al reporte:

```
Invariante de ciclo:
{∀k < c: cycle_k_completed ∧ |lights_updated_k| = n}
```

Y en el codigo, verificar:

```python
states = await orch.run_cycle(ids)
assert len(states) == n, f"Expected {n} states, got {len(states)}"
assert all(s.applied for s in states), "Not all lights were updated"
```

**Severidad:** Baja
**Archivos afectados:** `Documentacion/reporte.tex`, `CodigoConcurrente/src/main.py`

---

## 2. Requisito 1: Definir el problema (PCQ)

### 2.1 Problema y cuello de botella artificiales

**Estado actual:** El cuello de botella es fabricado mediante `time.sleep()`. No hay datos reales, sensores reales, ni latencias reales. Todo es inventado.

**Mejora propuesta:** Sustituir al menos una etapa por I/O real para que el cuello de botella sea genuino. Opciones:

- **Lectura de archivos CSV** con datos de trafico (uno por interseccion)
- **Peticiones HTTP** a una API mock local (e.g., Flask/FastAPI)
- **Lectura de base de datos SQLite** con registros por interseccion

Ejemplo minimo con archivos:

```python
async def read(self, intersection_id: int) -> TrafficData:
    path = f"data/intersection_{intersection_id}.csv"
    async with aiofiles.open(path) as f:
        content = await f.read()
    # parsear CSV real en lugar de random.randint
```

**Severidad:** Media
**Archivos afectados:** `CodigoSecuencial/run_p0.py`, `CodigoConcurrente/src/acquisition.py`

---

## 3. Requisito 2: Hallar la mejora

### 3.1 `optimize` clasificado como CPU-bound incorrectamente

**Estado actual:** El reporte clasifica `optimize` como CPU-bound y lo ejecuta en el `ProcessPoolExecutor` junto con `analyze`. En realidad `optimize` son 3 lineas de aritmetica:

```python
def density_based(f: Features) -> SignalPlan:
    green = min(90.0, max(15.0, 15.0 + f.density * 1.2))
    offset = min(30.0, max(0.0, abs(f.flow) * 0.05))
    phases = 3 if f.queue < 10 else 4
    return SignalPlan(green_time_s=green, offset_s=offset, phase_count=phases)
```

Esto toma microsegundos. No es CPU-bound.

**Mejora propuesta:** Dos opciones:

**(a)** Documentar en el reporte que `optimize` es CPU-ligero y que se fusiona con `analyze` en el worker por eficiencia de serializacion, no por necesidad de paralelismo.

**(b)** Hacer `optimize` genuinamente CPU-bound: implementar una busqueda local, simulacion Monte Carlo, o algoritmo genetico simplificado que justifique el multiprocessing.

**Severidad:** Media
**Archivos afectados:** `Documentacion/reporte.tex`, `CodigoConcurrente/src/optimization/strategies.py`

---

### 3.2 No hay profiling previo del codigo secuencial

**Estado actual:** El requisito dice "proponer estrategia de paralelizacion antes de implementar". No hay evidencia de haber perfilado el Estado P para determinar donde esta el cuello de botella real.

**Mejora propuesta:** Agregar al reporte (y al repositorio) un profiling del Estado P:

```bash
python -m cProfile -s cumtime CodigoSecuencial/run_p0.py --n 50 --cycles 1
```

Esto mostraria que ~92% del tiempo es `time.sleep` (I/O simulado) y ~8% es el loop sin/cos (CPU simulado), justificando la estrategia AsyncIO > Multiprocessing.

**Severidad:** Media
**Archivos afectados:** `Documentacion/reporte.tex` (nueva subseccion de profiling)

---

## 4. Requisito 3: Aplicar POO

### 4.1 `analyzer` y `optimizer` son codigo muerto en `main.py`

**Estado actual:** En `main.py:31-32`:

```python
analyzer = TrafficAnalyzer(cfg)                    # se guarda en pipeline
optimizer = create_optimizer(cfg.optimizer_id)      # se guarda en pipeline
```

Estos objetos se guardan en `IntersectionPipeline` pero el orquestador **nunca** los usa. El worker reconstruye `TrafficAnalyzer` internamente y accede directo a `STRATEGY_MAP`. Son objetos muertos.

**Mejora propuesta:** Dos opciones:

**(a) Eliminar codigo muerto:** Remover `analyzer` y `optimizer` del pipeline si no se van a usar. Reducir `IntersectionPipeline` a solo `reader` y `controller` (los componentes que si se usan).

**(b) Usarlos realmente:** Redisenar el orquestador para que use los objetos del pipeline. Esto requeriria resolver el problema de pickle para `ProcessPoolExecutor`, por ejemplo usando `concurrent.futures` con `ThreadPoolExecutor` para CPU-bound (perdiendo paralelismo real por GIL) o pasando funciones serializables que respeten la interfaz.

**Severidad:** Alta
**Archivos afectados:** `CodigoConcurrente/src/main.py`, `CodigoConcurrente/src/pipeline.py`, `CodigoConcurrente/src/orchestrator_q.py`

---

### 4.2 `IntersectionPipeline` sin comportamiento

**Estado actual:** `IntersectionPipeline` es un `@dataclass` sin metodos. El reporte lo describe como objeto que "encapsula completamente el flujo de procesamiento de una interseccion" (seccion 3.7), pero no tiene metodo `process()` ni `run()`.

```python
@dataclass(frozen=True)
class IntersectionPipeline:
    reader: TrafficSensorReaderAsync
    analyzer: TrafficAnalyzer
    optimizer: ISignalOptimizer
    controller: TrafficControllerAsync
    # ningun metodo
```

**Mejora propuesta:** Agregar un metodo que encapsule el flujo:

```python
@dataclass(frozen=True)
class IntersectionPipeline:
    reader: TrafficSensorReaderAsync
    analyzer: TrafficAnalyzer
    optimizer: ISignalOptimizer
    controller: TrafficControllerAsync

    async def process(self, intersection_id: int) -> LightState:
        data = await self.reader.read(intersection_id)
        features = self.analyzer.analyze(data)
        plan = self.optimizer.optimize(features)
        state = await self.controller.update(intersection_id, plan)
        return state
```

Esto alinearia el codigo con la formalizacion del reporte y permitiria:
```python
Q = await asyncio.gather(*[pipeline.process(i) for i in ids])
```

**Nota:** Este enfoque pierde la separacion AsyncIO/Multiprocessing para CPU-bound, pero alinea completamente con el modelo formal del reporte.

**Severidad:** Media
**Archivos afectados:** `CodigoConcurrente/src/pipeline.py`

---

### 4.3 Strategy y Factory ceremoniales

**Estado actual:**

**Factory** (`optimization/factory.py`):
```python
def create_optimizer(strategy_id: str) -> ISignalOptimizer:
    return SignalOptimizer(strategy_id=strategy_id)
```
Una linea sin logica de decision. Equivale a llamar el constructor directamente.

**Strategy:** Una sola clase concreta (`SignalOptimizer`) que delega a un diccionario de funciones. La interfaz `ISignalOptimizer` nunca se usa polimorficamente en el flujo real (`workers.py` la bypasea).

**Mejora propuesta:** Si se quiere Strategy real, implementar cada estrategia como clase:

```python
class DensityBasedOptimizer(ISignalOptimizer):
    def optimize(self, f: Features) -> SignalPlan:
        green = min(90.0, max(15.0, 15.0 + f.density * 1.2))
        offset = min(30.0, max(0.0, abs(f.flow) * 0.05))
        phases = 3 if f.queue < 10 else 4
        return SignalPlan(green_time_s=green, offset_s=offset, phase_count=phases)

class PredictiveOptimizer(ISignalOptimizer):
    def optimize(self, f: Features) -> SignalPlan:
        green = min(90.0, max(15.0, 20.0 + f.queue * 0.9 + abs(f.flow) * 0.2))
        offset = min(30.0, max(0.0, f.density * 0.03))
        phases = 4 if f.queue >= 8 else 3
        return SignalPlan(green_time_s=green, offset_s=offset, phase_count=phases)
```

Y en Factory, logica real:

```python
def create_optimizer(strategy_id: str) -> ISignalOptimizer:
    if strategy_id == "density":
        return DensityBasedOptimizer()
    elif strategy_id == "predictive":
        return PredictiveOptimizer()
    raise ValueError(f"Unknown strategy: {strategy_id}")
```

Esto alinearia con el UML del reporte que muestra `DensityBasedOptimizer` y `PredictiveOptimizer` como clases separadas.

**Severidad:** Media
**Archivos afectados:** `CodigoConcurrente/src/optimization/strategies.py`, `CodigoConcurrente/src/optimization/impl.py`, `CodigoConcurrente/src/optimization/factory.py`

---

### 4.4 OCP requiere editar 3 archivos para nueva estrategia

**Estado actual:** Para agregar una nueva estrategia se necesita:

1. Agregar funcion en `strategies.py`
2. Agregar entrada en `STRATEGY_MAP`
3. Agregar opcion en `choices` de `argparse` en `main.py`

Esto viola OCP (abierto para extension, cerrado para modificacion).

**Mejora propuesta:** Usar registro automatico con decorador:

```python
# strategies.py
STRATEGY_MAP = {}

def register_strategy(name: str):
    def decorator(fn):
        STRATEGY_MAP[name] = fn
        return fn
    return decorator

@register_strategy("density")
def density_based(f: Features) -> SignalPlan: ...

@register_strategy("predictive")
def predictive(f: Features) -> SignalPlan: ...
```

Y en `main.py`, generar choices dinamicamente:
```python
ap.add_argument("--optimizer", choices=STRATEGY_MAP.keys(), default="density")
```

**Severidad:** Baja
**Archivos afectados:** `CodigoConcurrente/src/optimization/strategies.py`, `CodigoConcurrente/src/main.py`

---

## 5. Requisito 4: Concurrencia apropiada

### 5.1 Multiprocessing cuesta mas que el computo que paraleliza

**Estado actual:** Con `cpu_work=30000`, el computo total para 50 intersecciones toma ~7ms. El overhead de `ProcessPoolExecutor` (crear pool + pickle + IPC) toma ~25ms. El mecanismo de paralelizacion introduce mas latencia que la que elimina.

**Evidencia:**
```
Ciclo 1 Q: 72ms (incluye creacion de pool)
Ciclo 2 Q: 65ms
Ciclo 3 Q: 65ms
I/O teorico (AsyncIO): ~35ms
CPU teorico (4 workers): ~7ms
Overhead estimado: ~25ms (37% del tiempo total)
```

**Mejora propuesta:** Dos opciones:

**(a)** Incrementar `cpu_work` a un valor donde multiprocessing se justifique (e.g., 500000+) y documentar el punto de cruce.

**(b)** Medir y comparar 3 configuraciones para demostrar el valor de cada mecanismo:
```bash
# Solo secuencial (P)
python3 run_p0.py --n 50 --cycles 3

# Solo AsyncIO (sin multiprocessing)
python3 -m src.main --n 50 --cycles 3 --workers 1

# AsyncIO + Multiprocessing
python3 -m src.main --n 50 --cycles 3 --workers 4
```

**Severidad:** Alta
**Archivos afectados:** `CodigoConcurrente/src/orchestrator_q.py`, `CodigoConcurrente/src/main.py`

---

### 5.2 `ProcessPoolExecutor` recreado cada ciclo

**Estado actual:** En `orchestrator_q.py:32`:

```python
async def run_cycle(self, intersection_ids):
    with ProcessPoolExecutor(max_workers=self.workers) as pool:
        # pool creado y destruido en CADA llamada a run_cycle
```

**Mejora propuesta:** Mover la creacion del pool fuera del ciclo:

```python
@dataclass
class OrchestratorQ:
    pipeline: IntersectionPipeline
    workers: int
    _pool: ProcessPoolExecutor = field(init=False)

    def __post_init__(self):
        self._pool = ProcessPoolExecutor(max_workers=self.workers)

    async def run_cycle(self, intersection_ids):
        loop = asyncio.get_running_loop()
        cpu_futs = [
            loop.run_in_executor(self._pool, analyze_and_optimize_worker, data, cfg, optimizer_id)
            for data in traffic_batch
        ]
        ...

    def shutdown(self):
        self._pool.shutdown(wait=True)
```

**Severidad:** Media
**Archivos afectados:** `CodigoConcurrente/src/orchestrator_q.py`

---

### 5.3 No se mide aporte individual de cada mecanismo

**Estado actual:** No hay ejecucion que aisle el efecto de AsyncIO vs Multiprocessing. No se puede saber cuanto aporta cada uno.

**Mejora propuesta:** Agregar al script de comparacion (o al reporte) una tabla como:

| Configuracion | T (s) | Speedup vs P |
|---|---|---|
| P (secuencial) | 1.892 | 1.0x |
| Q (AsyncIO only, workers=1) | ? | ?x |
| Q (AsyncIO + MP, workers=4) | 0.067 | 28.2x |

Esto demostraria que AsyncIO aporta la mayor parte del speedup y multiprocessing aporta un delta incremental.

**Severidad:** Media
**Archivos afectados:** Script de comparacion (nuevo), `Documentacion/reporte.tex`

---

### 5.4 `random.seed` no se propaga a procesos hijos

**Estado actual:** `random.seed(args.seed)` se ejecuta en el proceso principal. Los workers de `ProcessPoolExecutor` heredan el estado por `fork` (Linux), pero si se usara `spawn` (macOS default, Windows) cada worker tendria semilla distinta.

**Mejora propuesta:** Pasar la semilla al worker y setearla explicitamente:

```python
def analyze_and_optimize_worker(data, cfg, optimizer_id, seed):
    random.seed(seed)  # reproducibilidad garantizada
    ...
```

O bien documentar que la reproducibilidad depende del metodo de inicio del pool (`fork`).

**Severidad:** Baja
**Archivos afectados:** `CodigoConcurrente/src/workers.py`, `CodigoConcurrente/src/orchestrator_q.py`

---

## 6. Requisito 5: Documentar rendimiento

### 6.1 Speedup no calculado en codigo

**Estado actual:** Ningun programa calcula `S = T_P / T_Q` ni `E = S / p`. El requisito pide explicitamente "incluir speedup".

**Mejora propuesta:** Crear `compare_P_vs_Q.py` en la raiz del proyecto:

```python
import subprocess, re

def run_and_parse(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    match = re.search(r"avg=(\d+\.\d+)s", result.stdout)
    return float(match.group(1))

t_p = run_and_parse("cd CodigoSecuencial && python3 run_p0.py --n 50 --cycles 3")
t_q = run_and_parse("cd CodigoConcurrente && python3 -m src.main --n 50 --cycles 3 --workers 4")

speedup = t_p / t_q
efficiency = speedup / 4

print(f"T_P = {t_p:.3f}s")
print(f"T_Q = {t_q:.3f}s")
print(f"Speedup = {speedup:.2f}x")
print(f"Efficiency = {efficiency:.2f}")
```

**Severidad:** Alta
**Archivos afectados:** Nuevo archivo `compare_P_vs_Q.py`

---

### 6.2 Tabla del reporte no coincide con ejecucion real

**Estado actual:** El reporte (Tabla 1, seccion 7.6) muestra:

| n | T_P (s) | T_Q (s) | Speedup |
|---|---|---|---|
| 50 | 4.08 | 1.18 | 3.45 |

La ejecucion real produce:

| n | T_P (s) | T_Q (s) | Speedup |
|---|---|---|---|
| 50 | 1.892 | 0.067 | 28.2 |

**Mejora propuesta:** Regenerar la tabla con ejecuciones reales para multiples valores de `n` y actualizar el reporte. Los parametros exactos deben quedar documentados.

**Severidad:** Alta
**Archivos afectados:** `Documentacion/reporte.tex` (Tabla 1, Figuras 4-6)

---

### 6.3 No se varia `n` para mostrar escalabilidad

**Estado actual:** Solo se ejecuta con `n=50`. El reporte muestra datos para `n = 10, 25, 50, 100` pero no hay script que los genere.

**Mejora propuesta:** Extender `compare_P_vs_Q.py` para iterar sobre multiples valores de `n`:

```python
for n in [10, 25, 50, 100, 200]:
    t_p = run_and_parse(f"... --n {n} ...")
    t_q = run_and_parse(f"... --n {n} ...")
    print(f"n={n} | T_P={t_p:.3f} | T_Q={t_q:.3f} | S={t_p/t_q:.2f}")
```

**Severidad:** Media
**Archivos afectados:** `compare_P_vs_Q.py`

---

### 6.4 No se mide uso de CPU/nucleos

**Estado actual:** El requisito dice "si aplica, uso de recursos (CPU/nucleos)". Con multiprocessing aplica directamente, pero no hay medicion.

**Mejora propuesta:** Agregar medicion basica con `psutil` o al menos documentar la cantidad de nucleos usados y su utilizacion observada:

```python
import os
print(f"CPU cores available: {os.cpu_count()}")
print(f"Workers used: {args.workers}")
```

**Severidad:** Baja
**Archivos afectados:** `CodigoConcurrente/src/main.py`

---

## 7. Tabla resumen de mejoras priorizadas

### Prioridad 1 — Criticas (afectan calificacion directamente)

| # | Mejora | Requisito |
|---|---|---|
| 6.1 | Crear script `compare_P_vs_Q.py` con speedup y eficiencia | Req 5 |
| 6.2 | Regenerar Tabla 1 del reporte con datos reales | Req 5 |
| 4.1 | Eliminar o usar realmente `analyzer`/`optimizer` en pipeline | Req 3 |
| 5.1 | Demostrar que multiprocessing aporta valor (subir `cpu_work` o medir aislado) | Req 4 |
| 1.2 | Verificar precondiciones o ajustar tripletas de Hoare | Hoare |

### Prioridad 2 — Importantes (mejoran calidad significativamente)

| # | Mejora | Requisito |
|---|---|---|
| 1.1 | Unificar tripletas de Hoare a 4 etapas | Hoare |
| 3.1 | Documentar que `optimize` no es CPU-bound | Req 2 |
| 4.2 | Agregar metodo `process()` a `IntersectionPipeline` | Req 3 |
| 4.3 | Implementar Strategy como clases, no funciones | Req 3 |
| 5.2 | Sacar `ProcessPoolExecutor` fuera del ciclo | Req 4 |
| 5.3 | Medir aporte individual AsyncIO vs Multiprocessing | Req 4 |
| 6.3 | Variar `n` para demostrar escalabilidad | Req 5 |

### Prioridad 3 — Menores (deseables pero no criticas)

| # | Mejora | Requisito |
|---|---|---|
| 1.3 | Introducir camino de falla en `update` | Hoare |
| 1.4 | Agregar invariante de ciclo | Hoare |
| 2.1 | Sustituir I/O simulado por I/O real | Req 1 |
| 3.2 | Agregar profiling del Estado P | Req 2 |
| 4.4 | Registro automatico de estrategias (OCP real) | Req 3 |
| 5.4 | Propagar semilla a workers | Req 4 |
| 6.4 | Medir uso de CPU/nucleos | Req 5 |
