from __future__ import annotations
from dataclasses import dataclass
from .interfaces import ISignalOptimizer
from ..domain import Features, SignalPlan
from .strategies import STRATEGY_MAP

@dataclass(frozen=True)
class SignalOptimizer(ISignalOptimizer):
    """Implementación concreta que delega a una estrategia seleccionada."""
    strategy_id: str

    def optimize(self, f: Features) -> SignalPlan:
        fn = STRATEGY_MAP.get(self.strategy_id)
        if fn is None:
            raise ValueError(f"Unknown optimizer strategy_id={self.strategy_id!r}")
        return fn(f)
