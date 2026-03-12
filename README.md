# Optimización Concurrente de Sincronización de Semáforos

Proyecto desarrollado para la materia **Lógica y Programación** del
programa de **Maestría en Ciencias e Innovación Tecnológica (MCIT)**.

El objetivo del proyecto es modelar y optimizar un sistema de
sincronización de semáforos utilizando **programación concurrente**,
**arquitectura orientada a objetos** y **patrones de diseño**, evaluando
el rendimiento frente a una implementación secuencial.

------------------------------------------------------------------------

# Problema

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

# Arquitectura del Sistema

Cada intersección se procesa mediante un **pipeline de cuatro etapas**:

Read → Analyze → Optimize → Update

Formalmente:

Pipeline(i) = Update( Optimize( Analyze( Read(i) )))

donde:

-   **Read**: adquisición de datos de sensores
-   **Analyze**: procesamiento de métricas de tráfico
-   **Optimize**: cálculo del plan semafórico
-   **Update**: actualización del estado del semáforo

Cada intersección puede procesarse de manera independiente, permitiendo
paralelización.

------------------------------------------------------------------------

# Arquitectura de Software

El sistema está organizado siguiendo principios de **programación
orientada a objetos** y **arquitectura modular**.

Componentes principales:

-   Acquisition --- lectura de sensores
-   Processing --- análisis del estado del tráfico
-   Optimization --- cálculo de planes semafóricos
-   Control --- aplicación del plan calculado

------------------------------------------------------------------------

# Patrones de Diseño Utilizados

## Strategy Pattern

Permite intercambiar algoritmos de optimización sin modificar el resto
del sistema.

ISignalOptimizer\
├── DensityBasedOptimizer\
└── PredictiveOptimizer

Esto facilita incorporar nuevos algoritmos de control de tráfico.

------------------------------------------------------------------------

## Pipeline Pattern

El sistema modela el procesamiento de cada intersección como una
secuencia de transformaciones.

TrafficData → Features → SignalPlan → LightState

------------------------------------------------------------------------

# Concurrencia

El sistema utiliza un modelo **híbrido de concurrencia**:

  Tipo de tarea   Tecnología
  --------------- -----------------
  I/O bound       AsyncIO
  CPU bound       Multiprocessing

Esto permite aprovechar mejor los recursos del sistema.

------------------------------------------------------------------------

# Estructura del Proyecto

    MCIT_LOG_PROG_Proyecto_Final/
    │
    ├── CodigoConcurrente/
    │   ├── src/
    │   │   ├── acquisition.py
    │   │   ├── processing.py
    │   │   ├── control.py
    │   │   ├── pipeline.py
    │   │   ├── workers.py
    │   │   ├── orchestrator_q.py
    │   │   ├── config.py
    │   │   ├── domain.py
    │   │   ├── main.py
    │   │   │
    │   │   └── optimization/
    │   │       ├── interfaces.py
    │   │       ├── strategies.py
    │   │       └── factory.py
    │
    ├── Documentacion/
    │   ├── reporte.tex
    │   ├── speedup_vs_intersections.png
    │   └── throughput_vs_intersections.png

------------------------------------------------------------------------

# Ejecución

Para ejecutar el sistema:

  cd CodigoConcurrente
  python -m src.main

------------------------------------------------------------------------

# Evaluación Experimental

El proyecto incluye una evaluación simulada que compara:

-   latencia de procesamiento
-   throughput
-   speedup
-   eficiencia paralela

Resultados principales:

-   reducción significativa de latencia
-   incremento del throughput
-   speedup cercano a **3.5×**

------------------------------------------------------------------------

# Análisis con la Ley de Amdahl

El speedup observado se explica mediante:

S = 1 / ((1 − α) + α/p)

Resultados experimentales:

α ≈ 0.95

Esto indica que aproximadamente **95% del sistema es paralelizable**.

------------------------------------------------------------------------

# Tecnologías Utilizadas

-   Python 3
-   AsyncIO
-   Multiprocessing
-   Programación Orientada a Objetos
-   Patrones de diseño
