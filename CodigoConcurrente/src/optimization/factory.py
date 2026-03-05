from __future__ import annotations
from .interfaces import ISignalOptimizer
from .impl import SignalOptimizer

def create_optimizer(strategy_id: str) -> ISignalOptimizer:
    # Factory: crea la estrategia según configuración
    return SignalOptimizer(strategy_id=strategy_id)
