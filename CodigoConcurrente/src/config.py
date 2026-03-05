from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class SimConfig:
    io_read_ms: int = 25
    io_update_ms: int = 10
    cpu_work: int = 30000
    optimizer_id: str = "density"  # "density" | "predictive"
