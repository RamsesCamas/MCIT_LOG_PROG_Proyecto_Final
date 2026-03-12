from __future__ import annotations
from .interfaces import ISignalOptimizer
from .strategies import DensityBasedOptimizer, PredictiveOptimizer

def create_optimizer(strategy_id: str) -> ISignalOptimizer:
    # Factory: punto único de decisión para estrategias.
    if strategy_id == "density":
        return DensityBasedOptimizer()
    if strategy_id == "predictive":
        return PredictiveOptimizer()
    raise ValueError(f"Unknown optimizer strategy_id={strategy_id!r}")
