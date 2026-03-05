from __future__ import annotations
import math
from .domain import TrafficData, Features
from .config import SimConfig

class TrafficAnalyzer:
    """Processing (CPU-bound): extrae métricas. Se ejecuta en ProcessPool."""

    def __init__(self, cfg: SimConfig) -> None:
        self._cfg = cfg

    def analyze(self, data: TrafficData) -> Features:
        total = sum(data.counts)
        density = total / max(len(data.counts), 1)
        flow = (data.counts[-1] - data.counts[0]) / max((data.timestamps[-1] - data.timestamps[0]), 1e-6)
        queue = max(0.0, density - abs(flow) * 0.1)

        # Simulación de carga CPU
        acc = 0.0
        for k in range(self._cfg.cpu_work):
            acc += math.sin(k * 0.0001) * math.cos(k * 0.0002)
        queue = queue + (abs(acc) * 1e-9)

        return Features(density=float(density), flow=float(flow), queue=float(queue))
