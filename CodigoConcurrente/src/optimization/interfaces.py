from __future__ import annotations
from abc import ABC, abstractmethod
from ..domain import Features, SignalPlan

class ISignalOptimizer(ABC):
    """Abstracción Strategy (OCP/DIP)."""

    @abstractmethod
    def optimize(self, f: Features) -> SignalPlan:
        raise NotImplementedError
