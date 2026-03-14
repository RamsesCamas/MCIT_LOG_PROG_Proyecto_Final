# Reporte de Benchmark: Estado P (Secuencial) vs Estado Q (Concurrente)

## 1. Objetivo

Evaluar cuantitativamente la ganancia de rendimiento al pasar de una
arquitectura **secuencial** (Estado P) a una arquitectura **concurrente**
(Estado Q) para el procesamiento de intersecciones semafóricas, variando
el número de intersecciones (`n`) y el modelo de concurrencia.

------------------------------------------------------------------------

## 2. Configuración Experimental

| Parámetro             | Valor         |
|-----------------------|---------------|
| Ciclos por prueba     | 30            |
| Carga CPU (`cpu_work`)| 30 000 iter   |
| Latencia I/O lectura  | 25 ms         |
| Latencia I/O update   | 10 ms         |
| Semilla               | 1234          |
| CPU cores disponibles | 20            |
| Optimizer (Strategy)  | `density`     |

### Modos evaluados

| Modo | Descripción | Clave |
|------|-------------|-------|
| **P — Secuencial** | Pipeline completo ejecutado en serie para cada intersección. Sin concurrencia. | `T_P` |
| **Q async-only** | AsyncIO con `workers=1`. Solapa operaciones I/O pero ejecuta CPU en el hilo principal. | `T_Q async` |
| **Q full** | AsyncIO + `ProcessPoolExecutor` con `workers=4`. Solapa I/O y distribuye CPU entre procesos. | `T_Q full` |

------------------------------------------------------------------------

## 3. Resultados

### 3.1 Tiempos promedio por ciclo

| n   | T_P (s) | T_Q async (s) | T_Q full (s) |
|-----|---------|---------------|--------------|
| 10  | 0.377   | 0.054         | 0.044        |
| 25  | 0.938   | 0.080         | 0.051        |
| 50  | 1.893   | 0.121         | 0.062        |
| 100 | 3.763   | 0.201         | 0.083        |
| 200 | 7.562   | 0.370         | 0.125        |

### 3.2 Speedups

| n   | Speedup async (T_P / T_Q async) | Speedup full (T_P / T_Q full) | Speedup paralelo (T_Q async / T_Q full) |
|-----|---------------------------------|-------------------------------|-----------------------------------------|
| 10  | 7.0x                            | 8.6x                          | 1.2x                                   |
| 25  | 11.7x                           | 18.4x                         | 1.6x                                   |
| 50  | 15.6x                           | 30.5x                         | 2.0x                                   |
| 100 | 18.7x                           | 45.3x                         | 2.4x                                   |
| 200 | 20.4x                           | 60.5x                         | 3.0x                                   |

### 3.3 Eficiencia del paralelismo (CPU)

La eficiencia mide qué tan bien se aprovechan los 4 workers del
`ProcessPoolExecutor`:

$$E = \frac{S_{paralelo}}{p} = \frac{T_{Q_{async}} / T_{Q_{full}}}{4}$$

| n   | Eficiencia |
|-----|------------|
| 10  | 0.31       |
| 25  | 0.39       |
| 50  | 0.49       |
| 100 | 0.61       |
| 200 | 0.74       |

La eficiencia crece con `n` porque el overhead de crear y distribuir
tareas al pool se amortiza con más intersecciones.

------------------------------------------------------------------------

## 4. Análisis

### 4.1 Impacto de AsyncIO (P → Q async)

El speedup de AsyncIO crece de **7.0x** (n=10) a **20.4x** (n=200).

Esto se explica directamente por el profiling del Estado P:

| Tarea            | % Tiempo Total |
|------------------|----------------|
| I/O Simulado     | 91.6%          |
| CPU Simulado     | 8.3%           |
| CPU Ligero       | < 0.1%         |

El 91.6% del tiempo en P se gasta en `time.sleep` (lectura de sensores
y actualización de semáforos). AsyncIO convierte estas esperas secuenciales
en **concurrentes**: mientras la intersección *i* espera su respuesta de
sensor, la intersección *i+1* ya inicia su lectura.

En el estado secuencial, el tiempo es:

$$T_P = n \cdot (t_{read} + t_{cpu} + t_{update}) = n \cdot (25 + \sim1.2 + 10) \approx 36.2n \text{ ms}$$

Con AsyncIO, las lecturas y actualizaciones se solapan:

$$T_{Q_{async}} \approx \max(t_{read}) + n \cdot t_{cpu} + \max(t_{update}) \approx 25 + 1.2n + 10 \text{ ms}$$

Para n=200: $T_P \approx 7240$ ms vs $T_{Q_{async}} \approx 275$ ms,
prediciendo un speedup teórico de ~26x. El speedup observado (20.4x) es
menor por el overhead de scheduling de coroutines y la varianza del
`asyncio.sleep`.

### 4.2 Impacto de Multiprocessing (Q async → Q full)

Agregar 4 workers con `ProcessPoolExecutor` reduce el componente CPU:

$$T_{Q_{full}} \approx \max(t_{read}) + \frac{n \cdot t_{cpu}}{p} + \max(t_{update})$$

El speedup paralelo crece de 1.2x (n=10) a 3.0x (n=200), acercándose
al límite teórico de 4x (número de workers). Con n=10, el overhead de
serialización (pickling) y comunicación entre procesos domina; con n=200,
se amortiza y la eficiencia alcanza 0.74.

### 4.3 Escalabilidad

El comportamiento del tiempo de ejecución en Q full es notablemente
sublineal respecto a `n`:

| n   | T_Q full (s) | Ratio vs n=10 |
|-----|--------------|---------------|
| 10  | 0.044        | 1.0x          |
| 25  | 0.051        | 1.2x (n creció 2.5x) |
| 50  | 0.062        | 1.4x (n creció 5x)   |
| 100 | 0.083        | 1.9x (n creció 10x)  |
| 200 | 0.125        | 2.8x (n creció 20x)  |

Multiplicar por 20 el número de intersecciones solo incrementa el tiempo
en 2.8x. Esto confirma que la arquitectura escala eficientemente para
redes urbanas de mayor tamaño.

### 4.4 Ley de Amdahl

La Ley de Amdahl establece el speedup máximo alcanzable:

$$S = \frac{1}{(1 - \alpha) + \frac{\alpha}{p}}$$

Donde $\alpha$ es la fracción paralelizable y $p$ el número de
procesadores/tareas concurrentes.

A partir de los datos experimentales con n=200:

- **Speedup async = 20.4x** con solapamiento de I/O (p efectivo ≈ n = 200):
  Resolviendo: $\alpha \approx 0.952$

- **Speedup full = 60.5x** combinando I/O concurrente + CPU paralelo:
  El sistema opera en dos niveles de paralelismo: AsyncIO para I/O
  y ProcessPool para CPU, lo que permite superar el límite de Amdahl
  para un solo nivel.

La fracción serializable $(1 - \alpha) \approx 5\%$ corresponde al
overhead de orquestación: scheduling de coroutines, serialización de
datos para el pool, y sincronización de resultados.

------------------------------------------------------------------------

## 5. Resumen de hallazgos

1. **AsyncIO es la optimización dominante**: al ser un sistema 91.6%
   I/O-bound, solapar las esperas produce speedups de 7x a 20x.

2. **Multiprocessing complementa**: distribuir el 8.3% de CPU entre
   4 workers añade un factor adicional de hasta 3x, con eficiencia
   creciente conforme aumenta `n`.

3. **Speedup combinado de hasta 60.5x**: con n=200, el sistema
   concurrente es más de 60 veces más rápido que el secuencial.

4. **Escalabilidad sublineal**: el tiempo de Q full crece mucho más
   lentamente que `n`, lo que indica que el sistema puede manejar
   redes urbanas significativamente mayores sin degradación proporcional.

5. **La fracción paralelizable es ~95%**: consistente con la Ley de
   Amdahl, el 5% restante es overhead inherente de orquestación.

------------------------------------------------------------------------

## 6. Reproducibilidad

Para reproducir estos resultados:

```bash
cd benchmarks
python3 compare_P_vs_Q.py
```

El script ejecuta los 3 modos para cada valor de `n`, calcula promedios
sobre 30 ciclos, y genera `results.csv` con los datos tabulados.

Los resultados pueden variar según el hardware (número de cores, velocidad
del scheduler del sistema operativo, carga del sistema).
