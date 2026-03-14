# Optimización Concurrente de Sincronización de Semáforos

Proyecto desarrollado para la materia **Lógica y Programación** del
programa de **Maestría en Ciencias e Innovación Tecnológica (MCIT)**.

El objetivo del proyecto es modelar y optimizar un sistema de
sincronización de semáforos utilizando **programación concurrente**,
**arquitectura orientada a objetos** y **patrones de diseño**, evaluando
el rendimiento frente a una implementación secuencial.

------------------------------------------------------------------------

## Problema

En sistemas de control de tráfico urbano, múltiples intersecciones deben
procesar información de sensores, analizar el estado del tráfico y
calcular planes semafóricos en tiempo real.

Un enfoque completamente secuencial provoca:

-   aumento lineal del tiempo de procesamiento
-   baja escalabilidad
-   incapacidad para responder a redes urbanas grandes

Para resolver esto se propone una arquitectura concurrente basada en
**pipelines independientes por intersección**.

------------------------------------------------------------------------

## Arquitectura del Sistema

Cada intersección se procesa mediante un **pipeline de cuatro etapas**:

```
Read → Analyze → Optimize → Update
```

Formalmente:

```
Pipeline(i) = Update( Optimize( Analyze( Read(i) )))
```

donde:

-   **Read**: adquisición de datos de sensores
-   **Analyze**: procesamiento de métricas de tráfico
-   **Optimize**: cálculo del plan semafórico
-   **Update**: actualización del estado del semáforo

Cada intersección puede procesarse de manera independiente, permitiendo
paralelización.

------------------------------------------------------------------------

## Arquitectura de Software

El sistema está organizado siguiendo principios de **programación
orientada a objetos** y **arquitectura modular**.

Componentes principales:

-   **Acquisition** — lectura de sensores
-   **Processing** — análisis del estado del tráfico
-   **Optimization** — cálculo de planes semafóricos (Strategy Pattern)
-   **Control** — aplicación del plan calculado

------------------------------------------------------------------------

## Patrones de Diseño Utilizados

### Strategy Pattern

Permite intercambiar algoritmos de optimización sin modificar el resto
del sistema.

```
ISignalOptimizer
├── DensityBasedOptimizer
└── PredictiveOptimizer
```

La selección de estrategia se realiza mediante una **Factory basada en
registro** (`_REGISTRY` dict), lo que permite agregar nuevas estrategias
con una sola línea.

### Pipeline Pattern

El sistema modela el procesamiento de cada intersección como una
secuencia de transformaciones.

```
TrafficData → Features → SignalPlan → LightState
```

------------------------------------------------------------------------

## Concurrencia

El sistema utiliza un modelo **híbrido de concurrencia**:

| Tipo de tarea | Tecnología      |
|---------------|-----------------|
| I/O bound     | AsyncIO         |
| CPU bound     | Multiprocessing |

El orquestador (`OrchestratorQ`) soporta dos modos:

- **`workers=1`**: solo AsyncIO (sin multiprocessing)
- **`workers>1`**: AsyncIO + ProcessPoolExecutor

------------------------------------------------------------------------

## Estructura del Proyecto

```
MCIT_LOG_PROG_Proyecto_Final/
│
├── CodigoConcurrente/          # Estado Q: implementación concurrente con POO
│   └── src/
│       ├── acquisition.py      # Lectura asíncrona de sensores
│       ├── processing.py       # Análisis de tráfico (CPU-bound)
│       ├── control.py          # Actualización asíncrona de semáforos
│       ├── pipeline.py         # IntersectionPipeline (4 etapas)
│       ├── workers.py          # Worker CPU-bound para ProcessPool
│       ├── orchestrator_q.py   # Orquestador AsyncIO + Multiprocessing
│       ├── config.py           # Configuración de la simulación
│       ├── domain.py           # Tipos de datos (dataclasses)
│       ├── main.py             # Punto de entrada concurrente
│       └── optimization/
│           ├── interfaces.py   # ISignalOptimizer (ABC)
│           ├── strategies.py   # DensityBased + Predictive
│           └── factory.py      # Factory con _REGISTRY
│
├── CodigoSecuencial/           # Estado P0: implementación secuencial
│   └── run_p0.py
│
├── profiling/                  # Profiling del estado secuencial
│   ├── profile_sequential.py
│   └── ANALYSIS.md
│
├── benchmarks/                 # Comparación P vs Q
│   ├── compare_P_vs_Q.py
│   ├── results.csv
│   └── InformeIndivivualGuillermoTinoco.pdf
│
├── visualizacion/              # Gráficas de resultados
│   ├── generar_graficas.py
│   ├── speedup_vs_n.png
│   ├── throughput_vs_n.png
│   ├── tiempos_comparativa.png
│   └── InformeIndividual.pdf
│
├── Documentacion/              # Reporte LaTeX y figuras
│   ├── reporte.tex
│   ├── speedup_vs_intersections.png
│   └── throughput_vs_intersections.png
│
└── README.md
```

------------------------------------------------------------------------

## Ejecución

### Estado P0 — Secuencial

```bash
cd CodigoSecuencial
python run_p0.py --n 50 --cycles 3
```

### Estado Q — AsyncIO only (workers=1)

```bash
cd CodigoConcurrente
python -m src.main --n 50 --cycles 3 --workers 1
```

### Estado Q — AsyncIO + Multiprocessing (workers=4)

```bash
cd CodigoConcurrente
python -m src.main --n 50 --cycles 3 --workers 4
```

### Benchmarking (P vs Q)

```bash
cd benchmarks
python compare_P_vs_Q.py
```

### Visualización de resultados

```bash
cd visualizacion
python generar_graficas.py
```

------------------------------------------------------------------------

## Resultados del Benchmarking

Comparación entre el estado secuencial (P) y el concurrente (Q):

| n   | T_P (s) | T_Q async (s) | T_Q full (s) | Speedup async | Speedup full |
|-----|---------|---------------|--------------|---------------|--------------|
| 10  | 0.568   | 0.086         | 0.056        | 6.6x          | 10.1x        |
| 25  | 1.421   | 0.158         | 0.075        | 9.0x          | 18.9x        |
| 50  | 2.831   | 0.265         | 0.106        | 10.7x         | 26.7x        |
| 100 | 5.926   | 0.488         | 0.170        | 12.1x         | 34.9x        |
| 200 | 12.153  | 0.926         | 0.295        | 13.1x         | 41.2x        |

El speedup crece con el número de intersecciones gracias al solapamiento
de tareas I/O-bound y la distribución de carga CPU entre procesos.

------------------------------------------------------------------------

## Análisis de Profiling

Distribución del tiempo en el estado secuencial (P0):

| Tarea            | % Tiempo Total |
|------------------|----------------|
| I/O Simulado     | 91.6%          |
| CPU Simulado     | 8.3%           |
| CPU Ligero       | < 0.1%         |

El **91.6%** del tiempo se consume en operaciones I/O, lo que justifica
el uso de AsyncIO como primera optimización. El 8.3% restante en
CPU-bound justifica el uso de Multiprocessing para escalar aún más.

------------------------------------------------------------------------

## Análisis con la Ley de Amdahl

El speedup observado se explica mediante:

```
S = 1 / ((1 − α) + α/p)
```

Resultados experimentales:

```
α ≈ 0.95
```

Esto indica que aproximadamente **95% del sistema es paralelizable**.

------------------------------------------------------------------------

## Tecnologías Utilizadas

-   Python 3
-   AsyncIO
-   Multiprocessing
-   Programación Orientada a Objetos
-   Patrones de diseño (Strategy, Factory, Pipeline)

------------------------------------------------------------------------

## Equipo

| Integrante  | Contribución                             |
|-------------|------------------------------------------|
| Rodrigo     | Strategy Pattern + Factory               |
| Vivi        | Pipeline OOP + eliminación código muerto |
| Ramsés      | Orquestador concurrente + integración    |
| Montserrat  | Profiling del estado secuencial          |
| Guillermo   | Benchmarking P vs Q                      |
| Carmen      | Visualización de resultados              |
| Iván        | Documentación y README                   |
