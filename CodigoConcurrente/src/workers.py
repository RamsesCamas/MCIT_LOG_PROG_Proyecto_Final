from __future__ import annotations
from typing import Tuple
from .domain import TrafficData, Features, SignalPlan
from .config import SimConfig
from .processing import TrafficAnalyzer
from .optimization.strategies import STRATEGY_MAP

def analyze_and_optimize_worker(data: TrafficData, cfg: SimConfig, optimizer_id: str) -> Tuple[Features, SignalPlan]:
    """Worker CPU-bound para ProcessPool.

    Nota: se construyen componentes dentro del proceso (evita problemas de pickling).
    El Strategy se selecciona por `optimizer_id` (string), coherente con Factory/Strategy.
    """
    analyzer = TrafficAnalyzer(cfg)
    features = analyzer.analyze(data)

    fn = STRATEGY_MAP.get(optimizer_id)
    if fn is None:
        raise ValueError(f"Unknown optimizer_id={optimizer_id!r}")
    plan = fn(features)

    return features, plan
