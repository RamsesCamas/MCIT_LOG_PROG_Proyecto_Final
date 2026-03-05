# Estado Q – Concurrente con POO (AsyncIO + Multiprocessing)

Implementación **con POO** y **concurrencia híbrida**, coherente con tu documento:

- **Acquisition (I/O-bound):** `TrafficSensorReaderAsync` (AsyncIO)
- **Processing (CPU-bound):** `TrafficAnalyzer` (en ProcessPool)
- **Optimization (CPU-bound + Strategy):** `ISignalOptimizer` + estrategias (en ProcessPool)
- **Control (I/O-bound):** `TrafficControllerAsync` (AsyncIO)
- **Pipeline por intersección:** `IntersectionPipeline`
- **Orquestación global Q:** `OrchestratorQ` (gather + process pool + gather)

## Ejecutar (simulación)
```bash
python -m src.main --n 50 --cycles 3 --workers 4 --optimizer density
```

Parámetros:
- `--n`: intersecciones
- `--cycles`: ciclos
- `--workers`: procesos (multiprocessing) para CPU-bound
- `--optimizer`: estrategia (`density` o `predictive`)
- `--io-read-ms`, `--io-update-ms`: latencias I/O simuladas (ms)
- `--cpu-work`: carga CPU simulada

## Nota de diseño (Strategy + multiprocessing)
Para evitar problemas de *pickling* al enviar objetos a procesos, el worker CPU recibe:
- `traffic_data` (dataclass simple)
- `optimizer_id` (string)
y despacha a la estrategia correspondiente en el proceso.
