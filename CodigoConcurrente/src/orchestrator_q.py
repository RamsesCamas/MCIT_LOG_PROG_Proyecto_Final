from __future__ import annotations
import asyncio
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from typing import List, Tuple

from .config import SimConfig
from .domain import LightState, TrafficData, Features, SignalPlan
from .pipeline import IntersectionPipeline
from .workers import analyze_and_optimize_worker

@dataclass
class OrchestratorQ:
    """Orquestador del Estado Q:
    1) AsyncIO gather(read)  -> I/O-bound
    2) ProcessPool(analyze+optimize) -> CPU-bound
    3) AsyncIO gather(update) -> I/O-bound
    """
    pipeline: IntersectionPipeline
    workers: int

    async def run_cycle(self, intersection_ids: List[int]) -> List[LightState]:
        # --- 1) READ concurrente (AsyncIO)
        read_tasks = [self.pipeline.reader.read(i) for i in intersection_ids]
        traffic_batch: List[TrafficData] = await asyncio.gather(*read_tasks)

        # --- 2) CPU stage (multiprocessing)
        loop = asyncio.get_running_loop()
        cfg: SimConfig = self.pipeline.reader._cfg  # misma cfg compartida (dataclass)
        optimizer_id = cfg.optimizer_id

        with ProcessPoolExecutor(max_workers=self.workers) as pool:
            cpu_futs = [
                loop.run_in_executor(pool, analyze_and_optimize_worker, data, cfg, optimizer_id)
                for data in traffic_batch
            ]
            _results: List[Tuple[Features, SignalPlan]] = await asyncio.gather(*cpu_futs)

        # --- 3) UPDATE concurrente (AsyncIO)
        update_tasks = [
            self.pipeline.controller.update(intersection_ids[idx], _results[idx][1])
            for idx in range(len(intersection_ids))
        ]
        states: List[LightState] = await asyncio.gather(*update_tasks)
        return states
