from __future__ import annotations
import argparse
import random
import time
import math
import statistics
from dataclasses import dataclass
from typing import List, Dict, Tuple

# ----------------------------
# Tipos de datos (ligeros, NO POO arquitectónica)
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

# ----------------------------
# Funciones del pipeline (baseline P0)
# ----------------------------
def read_sensor(i: int, io_read_ms: int) -> TrafficData:
    """I/O-bound (simulado): lectura de sensores/cámaras.
    En un sistema real: lectura serial/puerto, request HTTP, etc.
    """
    time.sleep(io_read_ms / 1000.0)
    counts = [random.randint(0, 40) for _ in range(4)]
    ts = time.time()
    timestamps = [ts - 0.3, ts - 0.2, ts - 0.1, ts]
    return TrafficData(counts=counts, timestamps=timestamps)

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

def update_light(i: int, plan: SignalPlan, io_update_ms: int) -> LightState:
    """I/O-bound (simulado): aplica el plan al controlador del semáforo."""
    time.sleep(io_update_ms / 1000.0)
    return LightState(
        applied=True,
        green_time_s=plan.green_time_s,
        offset_s=plan.offset_s,
        phase_count=plan.phase_count,
    )

# ----------------------------
# Ejecución secuencial Estado P0
# ----------------------------
def run_cycle_sequential(n: int, io_read_ms: int, io_update_ms: int, cpu_work: int) -> None:
    """Procesa intersecciones en orden: i1, i2, ..., in (sin solapamiento)."""
    for i in range(1, n + 1):
        d = read_sensor(i, io_read_ms)
        f = analyze(d, cpu_work)
        p = optimize(f)
        _ = update_light(i, p, io_update_ms)

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Estado P0: Secuencial SIN POO (simulado).")
    ap.add_argument("--n", type=int, default=50, help="Número de intersecciones")
    ap.add_argument("--cycles", type=int, default=3, help="Número de ciclos")
    ap.add_argument("--io-ms", type=int, default=25, help="Latencia de lectura (ms)")
    ap.add_argument("--update-ms", type=int, default=10, help="Latencia de actualización (ms)")
    ap.add_argument("--cpu-work", type=int, default=30000, help="Carga CPU (iteraciones)")
    ap.add_argument("--seed", type=int, default=1234, help="Semilla")
    return ap.parse_args()

def main() -> None:
    args = parse_args()
    random.seed(args.seed)

    times: List[float] = []
    for c in range(1, args.cycles + 1):
        t0 = time.perf_counter()
        run_cycle_sequential(args.n, args.io_ms, args.update_ms, args.cpu_work)
        t1 = time.perf_counter()

        wall = t1 - t0
        times.append(wall)
        print(f"[cycle {c}] wall_time={wall:.3f}s | per_intersection={wall/max(args.n,1):.4f}s")

    avg = statistics.mean(times) if times else 0.0
    min_t = min(times) if times else 0.0
    max_t = max(times) if times else 0.0
    std_t = statistics.stdev(times) if len(times) > 1 else 0.0

    print(
        f"Summary: cycles={len(times)} | avg={avg:.3f}s | min={min_t:.3f}s | max={max_t:.3f}s | std={std_t:.3f}s"
    )

if __name__ == "__main__":
    main()
