# Optimización Concurrente de Semáforos para Ciudades Inteligentes

## Descripción

Este repositorio contiene la implementación y evaluación experimental de
un sistema de sincronización de semáforos diseñado para entornos de
**ciudades inteligentes**.

El proyecto analiza dos estados arquitectónicos del sistema:

-   **Estado P** --- Implementación secuencial sin programación
    orientada a objetos
-   **Estado Q** --- Implementación concurrente con arquitectura
    orientada a objetos

El objetivo principal es analizar cómo la **concurrencia y el diseño
modular** pueden mejorar el rendimiento y la escalabilidad de sistemas
de control de tráfico.

------------------------------------------------------------------------

# Arquitectura del Sistema

El sistema modela cada intersección como un **pipeline de
procesamiento** compuesto por cuatro etapas:

1.  **Adquisición de datos**
2.  **Procesamiento**
3.  **Optimización**
4.  **Control**

Formalmente:

Pipeline(i) = Update( Optimize( Analyze( Read(i) )))

Cada intersección puede procesarse de manera independiente, lo cual
permite paralelizar el sistema.

------------------------------------------------------------------------

# Estado P --- Sistema Secuencial

El **Estado P** representa la implementación base del sistema.

Características:

-   Ejecución completamente secuencial
-   Sin uso de programación orientada a objetos
-   Pipeline implementado de forma procedural

Modelo de ejecución:

P = F(i1); F(i2); ... ; F(in)

Limitaciones:

-   Crecimiento lineal del tiempo de ejecución
-   Baja escalabilidad
-   Dificultad para extender el sistema

------------------------------------------------------------------------

# Estado Q --- Sistema Concurrente

El **Estado Q** introduce una arquitectura orientada a objetos junto con
concurrencia.

## Patrones de Diseño Utilizados

-   **Strategy Pattern** --- Permite intercambiar algoritmos de
    optimización
-   **Pipeline Pattern** --- Define el flujo de procesamiento del
    sistema

## Modelo de Concurrencia

El sistema utiliza un enfoque híbrido:

  Tipo de tarea   Tecnología
  --------------- -----------------
  I/O bound       AsyncIO
  CPU bound       Multiprocessing

Esto permite aprovechar mejor los recursos del sistema.

------------------------------------------------------------------------

# Evaluación Experimental

El repositorio incluye un conjunto de experimentos simulados que
comparan el rendimiento entre el **Estado P** y el **Estado Q**.

Las métricas evaluadas incluyen:

-   Latencia de procesamiento
-   Throughput
-   Speedup
-   Eficiencia paralela

Los resultados muestran mejoras significativas en rendimiento al
utilizar concurrencia.

------------------------------------------------------------------------

# Análisis con la Ley de Amdahl

El speedup observado fue analizado utilizando la **Ley de Amdahl**:

S = 1 / ((1 - α) + α / p)

Los resultados experimentales sugieren:

α ≈ 0.95

Esto indica que aproximadamente **el 95% del sistema es paralelizable**.

------------------------------------------------------------------------

# Estructura del Proyecto

traffic_sync_project/ │ ├── estado_p/ │ ├── main.py │ ├── simulacion.py
│ └── modelo_trafico.py │ ├── estado_q/ │ ├── main.py │ ├── pipeline/ │
├── optimizadores/ │ ├── concurrencia/ │ └── controlador/ │ ├──
experimentos/ │ ├── benchmark.py │ ├── graficas.py │ └── resultados/ │
└── docs/ └── reporte_evaluacion.pdf

------------------------------------------------------------------------

# Ejecución

Versión secuencial:

python estado_p/main.py

Versión concurrente:

python estado_q/main.py

------------------------------------------------------------------------

# Requisitos

Python 3.10 o superior

Librerías utilizadas:

-   numpy
-   matplotlib
-   asyncio
-   multiprocessing

------------------------------------------------------------------------

# Contexto Académico

Este proyecto fue desarrollado como parte de un trabajo de **maestría en
Ingeniería de Software y Sistemas Inteligentes**.

El trabajo explora temas relacionados con:

-   Programación concurrente
-   Arquitectura de software
-   Optimización de tráfico urbano
-   Sistemas escalables para ciudades inteligentes

------------------------------------------------------------------------

# Autor

Guillermo Tinoco
