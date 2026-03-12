from __future__ import annotations
import argparse
import asyncio
import random
import time
import statistics
from typing import List

from .config import SimConfig
from .acquisition import TrafficSensorReaderAsync
from .processing import TrafficAnalyzer
from .optimization.factory import create_optimizer
from .control import TrafficControllerAsync
from .pipeline import IntersectionPipeline
from .orchestrator_q import OrchestratorQ

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Estado Q: Concurrente con POO (AsyncIO + Multiprocessing)")
    ap.add_argument("--n", type=int, default=50, help="Número de intersecciones")
    ap.add_argument("--cycles", type=int, default=3, help="Número de ciclos")
    ap.add_argument("--workers", type=int, default=4, help="Procesos para CPU-bound (multiprocessing)")
    ap.add_argument("--optimizer", type=str, default="density", choices=["density", "predictive"], help="Strategy")
    ap.add_argument("--io-read-ms", type=int, default=25, help="Latencia de lectura (ms)")
    ap.add_argument("--io-update-ms", type=int, default=10, help="Latencia de update (ms)")
    ap.add_argument("--cpu-work", type=int, default=30000, help="Carga CPU (iteraciones)")
    ap.add_argument("--seed", type=int, default=1234, help="Semilla")
    return ap.parse_args()

async def run_experiment(cfg: SimConfig, n: int, cycles: int, workers: int) -> None:
    reader = TrafficSensorReaderAsync(cfg)
    controller = TrafficControllerAsync(cfg)

    if workers == 1:
        analyzer = TrafficAnalyzer(cfg)
        optimizer = create_optimizer(cfg.optimizer_id)
    else:
        analyzer = None
        optimizer = None

    pipeline = IntersectionPipeline(
        reader=reader,
        controller=controller,
        analyzer=analyzer,
        optimizer=optimizer,
    )

    orch = OrchestratorQ(pipeline=pipeline, workers=workers)
    ids: List[int] = list(range(1, n + 1))

    times: List[float] = []
    for c in range(1, cycles + 1):
        t0 = time.perf_counter()
        await orch.run_cycle(ids)
        wall = time.perf_counter() - t0
        times.append(wall)
        print(f"[cycle {c}] wall_time={wall:.3f}s | per_intersection={wall/max(n,1):.4f}s | throughput~{n/max(wall,1e-9):.1f}/s")

    orch.shutdown()

    avg = statistics.mean(times) if times else 0.0
    min_t = min(times) if times else 0.0
    max_t = max(times) if times else 0.0
    std_t = statistics.stdev(times) if len(times) > 1 else 0.0

    print(
        f"Summary: cycles={len(times)} | avg={avg:.3f}s | min={min_t:.3f}s | max={max_t:.3f}s | std={std_t:.3f}s | workers={workers} | optimizer={cfg.optimizer_id}"
    )

def main() -> None:
    args = parse_args()
    random.seed(args.seed)

    cfg = SimConfig(
        io_read_ms=args.io_read_ms,
        io_update_ms=args.io_update_ms,
        cpu_work=args.cpu_work,
        optimizer_id=args.optimizer,
    )

    asyncio.run(run_experiment(cfg=cfg, n=args.n, cycles=args.cycles, workers=args.workers))

if __name__ == "__main__":
    main()
