from __future__ import annotations
import argparse
import random
import time
import math
import asyncio #Importación esencial para la concurrencia cooperativa
from dataclasses import dataclass
from typing import List

# ----------------------------
# Tipos de datos (ligeros)
# ----------------------------
@dataclass(frozen=True)
class TrafficData:
    counts: List[int]
    timestamps: List[float]

@dataclass(frozen=True)
class Features:
    density: float
    flow: float
    queue: float

@dataclass(frozen=True)
class SignalPlan:
    green_time_s: float
    offset_s: float
    phase_count: int

@dataclass(frozen=True)
class LightState:
    applied: bool
    green_time_s: float
    offset_s: float
    phase_count: int

# ==============================================================================
# FUNCIONES DEL PIPELINE (Transición de Estado P a Q)
# ==============================================================================

# PUNTO 4: Modificación a 'async' de read_sensor
async def read_sensor_async(i: int, io_read_ms: int) -> TrafficData:
    """I/O-bound simulado y concurrente (Fase 1 del Pipeline)."""
    # await reemplaza a time.sleep(). Cede control sin bloquear el hilo.
    await asyncio.sleep(io_read_ms / 1000.0)
    counts = [random.randint(0, 40) for _ in range(4)]
    ts = time.time()
    timestamps = [ts - 0.3, ts - 0.2, ts - 0.1, ts]
    return TrafficData(counts=counts, timestamps=timestamps)

# analyze y optimize se mantienen idénticas al baseline. Son CPU-bound.
def analyze(data: TrafficData, cpu_work: int) -> Features:
    """CPU-bound (simulado): extracción de métricas."""
    total = sum(data.counts)
    density = total / max(len(data.counts), 1)
    flow = (data.counts[-1] - data.counts[0]) / max((data.timestamps[-1] - data.timestamps[0]), 1e-6)
    queue = max(0.0, density - abs(flow) * 0.1)

    # Simulación de carga CPU
    acc = 0.0
    for k in range(cpu_work):
        acc += math.sin(k * 0.0001) * math.cos(k * 0.0002)
    queue = queue + (abs(acc) * 1e-9)

    return Features(density=float(density), flow=float(flow), queue=float(queue))

def optimize(features: Features) -> SignalPlan:
    """Optimización (heurística simple): calcula un plan semafórico."""
    green = min(90.0, max(15.0, 15.0 + features.density * 1.2))
    offset = min(30.0, max(0.0, abs(features.flow) * 0.05))
    phases = 3 if features.queue < 10 else 4
    return SignalPlan(green_time_s=green, offset_s=offset, phase_count=phases)

# PUNTO 5: Modificación a 'async' de update_light
async def update_light_async(i: int, plan: SignalPlan, io_update_ms: int) -> LightState:
    """I/O-bound simulado y concurrente (Fase 4 del Pipeline)."""
    await asyncio.sleep(io_update_ms / 1000.0)
    return LightState(
        applied=True,
        green_time_s=plan.green_time_s,
        offset_s=plan.offset_s,
        phase_count=plan.phase_count,
    )

# ==============================================================================
# EJECUCIÓN CONCURRENTE (ESTADO Q0)
# ==============================================================================
async def run_cycle_concurrent(n: int, io_read_ms: int, io_update_ms: int, cpu_work: int) -> None:
    """
    Ejecuta el pipeline del Estado Q0, solapando fases de I/O de manera concurrente
    y ejecutando el procesamiento de CPU secuencialmente.
    """
    
    # PUNTO 6: Combinación eficiente de tareas con asyncio.gather
    # Se crean múltiples corutinas de lectura (una por intersección) pero NO se inician aún.
    # En lugar de procesarlas uno por uno en un loop secuencial (Estado P0),
    # combinamos las tareas en un solo lote para ejecución concurrente optima.
    read_tasks = [read_sensor_async(i, io_read_ms) for i in range(1, n + 1)]
    
    # JUSTIFICACIÓN TEÓRICA DEL GATHER EN I/O:
    # 'asyncio.gather(*tasks)' permite que todas las corutinas de lectura se inicien
    # casi simultáneamente. Sus retardos (sleep) se solapan, reduciendo la latencia
    # total de la Fase 1 del Pipeline de la suma (linear) al máximo retardo individual
    # registrado entre todas las intersecciones del lote.
    sensor_data_list = await asyncio.gather(*read_tasks)
    
    # FASE 2 y 3: Análisis y Optimización.
    # Se mantienen secuenciales en el Estado Q0. Procesan la CPU una por una.
    plans = []
    for i, data in enumerate(sensor_data_list, start=1):
        features = analyze(data, cpu_work)
        plan = optimize(features)
        plans.append(plan)
        
    # PUNTO 6: Combinación eficiente de tareas de actualización (Fase 4).
    # Se aplica la misma lógica de solapamiento para enviar comandos a controladores remotos.
    update_tasks = [update_light_async(i + 1, plans[i], io_update_ms) for i in range(n)]
    await asyncio.gather(*update_tasks)

# ==============================================================================
# MAIN & ARGPARSE (Se mantienen parámetros originales)
# ==============================================================================
def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Estado Q0: Concurrencia Asíncrona (I/O-bound).")
    ap.add_argument("--n", type=int, default=50, help="Número de intersecciones")
    ap.add_argument("--cycles", type=int, default=3, help="Número de ciclos")
    ap.add_argument("--io-ms", type=int, default=25, help="Latencia de lectura (ms)")
    ap.add_argument("--update-ms", type=int, default=10, help="Latencia de actualización (ms)")
    ap.add_argument("--cpu-work", type=int, default=30000, help="Carga CPU (iteraciones)")
    ap.add_argument("--seed", type=int, default=1234, help="Semilla")
    return ap.parse_args()

async def main_async() -> None:
    args = parse_args()
    random.seed(args.seed)

    times: List[float] = []
    for c in range(1, args.cycles + 1):
        t0 = time.perf_counter()
        # Llamada a la ejecución concurrente del Estado Q0
        await run_cycle_concurrent(args.n, args.io_ms, args.update_ms, args.cpu_work)
        t1 = time.perf_counter()

        wall = t1 - t0
        times.append(wall)
        print(f"[cycle {c}] wall_time={wall:.3f}s | per_intersection={wall/max(args.n,1):.4f}s")

    avg = sum(times) / max(len(times), 1)
    print(f"Summary: cycles={len(times)} | avg={avg:.3f}s | max={max(times):.3f}s")

if __name__ == "__main__":
    # Inicio del bucle de eventos asíncronos
    asyncio.run(main_async())