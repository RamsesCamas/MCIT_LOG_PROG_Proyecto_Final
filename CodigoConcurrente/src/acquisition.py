from __future__ import annotations
import asyncio
import random
import time
from .domain import TrafficData
from .config import SimConfig

class TrafficSensorReaderAsync:
    """Acquisition (I/O-bound): lectura async simulada."""

    def __init__(self, cfg: SimConfig) -> None:
        self._cfg = cfg

    async def read(self, intersection_id: int) -> TrafficData:
        await asyncio.sleep(self._cfg.io_read_ms / 1000.0)
        counts = [random.randint(0, 40) for _ in range(4)]
        ts = time.time()
        timestamps = [ts - 0.3, ts - 0.2, ts - 0.1, ts]
        return TrafficData(counts=counts, timestamps=timestamps)
