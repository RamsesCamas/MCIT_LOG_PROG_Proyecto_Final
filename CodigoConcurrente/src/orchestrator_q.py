from __future__ import annotations
import asyncio
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .config import SimConfig
from .domain import LightState, TrafficData, Features, SignalPlan
from .pipeline import IntersectionPipeline
from .workers import analyze_and_optimize_worker

@dataclass
class OrchestratorQ:
    """Orquestador del Estado Q:
    - workers=1:  solo AsyncIO (pipeline.process por intersección)
    - workers>1:  AsyncIO gather(read) + ProcessPool(analyze+optimize) + AsyncIO gather(update)
    """
    pipeline: IntersectionPipeline
    workers: int
    _pool: Optional[ProcessPoolExecutor] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.workers > 1:
            self._pool = ProcessPoolExecutor(max_workers=self.workers)

    async def run_cycle(self, intersection_ids: List[int]) -> List[LightState]:
        if self.workers == 1:
            return await self._run_cycle_in_process(intersection_ids)
        return await self._run_cycle_multiprocess(intersection_ids)

    async def _run_cycle_in_process(self, intersection_ids: List[int]) -> List[LightState]:
        """Solo AsyncIO — usa pipeline.process() (sin subprocesos)."""
        tasks = [self.pipeline.process(iid) for iid in intersection_ids]
        states: List[LightState] = await asyncio.gather(*tasks)
        return states

    async def _run_cycle_multiprocess(self, intersection_ids: List[int]) -> List[LightState]:
        """AsyncIO + Multiprocessing — pool persistente."""
        # 1) READ concurrente (AsyncIO)
        read_tasks = [self.pipeline.reader.read(i) for i in intersection_ids]
        traffic_batch: List[TrafficData] = await asyncio.gather(*read_tasks)

        # 2) CPU stage (multiprocessing con pool persistente)
        loop = asyncio.get_running_loop()
        cfg: SimConfig = self.pipeline.reader._cfg
        optimizer_id = cfg.optimizer_id

        cpu_futs = [
            loop.run_in_executor(self._pool, analyze_and_optimize_worker, data, cfg, optimizer_id)
            for data in traffic_batch
        ]
        _results: List[Tuple[Features, SignalPlan]] = await asyncio.gather(*cpu_futs)

        # 3) UPDATE concurrente (AsyncIO)
        update_tasks = [
            self.pipeline.controller.update(intersection_ids[idx], _results[idx][1])
            for idx in range(len(intersection_ids))
        ]
        states: List[LightState] = await asyncio.gather(*update_tasks)
        return states

    def shutdown(self) -> None:
        if self._pool is not None:
            self._pool.shutdown(wait=True)
            self._pool = None
