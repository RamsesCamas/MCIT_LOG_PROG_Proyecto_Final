from __future__ import annotations
import asyncio
from .domain import SignalPlan, LightState
from .config import SimConfig

class TrafficControllerAsync:
    """Control (I/O-bound): aplica el plan al semáforo (simulado async)."""

    def __init__(self, cfg: SimConfig) -> None:
        self._cfg = cfg

    async def update(self, intersection_id: int, plan: SignalPlan) -> LightState:
        await asyncio.sleep(self._cfg.io_update_ms / 1000.0)
        return LightState(
            intersection_id=intersection_id,
            applied=True,
            green_time_s=plan.green_time_s,
            offset_s=plan.offset_s,
            phase_count=plan.phase_count,
        )
