from __future__ import annotations
from dataclasses import dataclass
from typing import List

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
    intersection_id: int
    applied: bool
    green_time_s: float
    offset_s: float
    phase_count: int
