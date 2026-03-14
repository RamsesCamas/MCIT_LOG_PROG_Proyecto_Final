from __future__ import annotations
from abc import ABC, abstractmethod
from ..domain import Features, SignalPlan

class ISignalOptimizer(ABC):
    """Interfaz Strategy para optimización de señales de tráfico.

    Define el contrato que toda estrategia de optimización debe cumplir
    (Open/Closed Principle + Dependency Inversion).
    """

    @abstractmethod
    def optimize(self, f: Features) -> SignalPlan:
        """Recibe features extraídas y devuelve un plan de señalización."""
        raise NotImplementedError
