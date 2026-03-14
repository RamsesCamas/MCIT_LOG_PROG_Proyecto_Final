from __future__ import annotations
from .interfaces import ISignalOptimizer
from ..domain import Features, SignalPlan


class DensityBasedOptimizer(ISignalOptimizer):
    """Estrategia basada en densidad vehicular y longitud de cola.

    Calcula el tiempo de verde proporcional a la densidad,
    el desfase según el flujo, y selecciona 3 o 4 fases
    según la longitud de la cola.
    """

    def optimize(self, f: Features) -> SignalPlan:
        green = min(90.0, max(15.0, 15.0 + f.density * 1.2))
        offset = min(30.0, max(0.0, abs(f.flow) * 0.05))
        phases = 3 if f.queue < 10 else 4
        return SignalPlan(green_time_s=green, offset_s=offset, phase_count=phases)

    def __repr__(self) -> str:
        return "DensityBasedOptimizer()"


class PredictiveOptimizer(ISignalOptimizer):
    """Estrategia predictiva simulada.

    Pondera cola y flujo vehicular con coeficientes distintos,
    simulando un modelo que anticipa cambios en el tráfico.
    """

    def optimize(self, f: Features) -> SignalPlan:
        green = min(90.0, max(15.0, 20.0 + f.queue * 0.9 + abs(f.flow) * 0.2))
        offset = min(30.0, max(0.0, f.density * 0.03))
        phases = 4 if f.queue >= 8 else 3
        return SignalPlan(green_time_s=green, offset_s=offset, phase_count=phases)

    def __repr__(self) -> str:
        return "PredictiveOptimizer()"
