from __future__ import annotations
from ..domain import Features, SignalPlan

def density_based(f: Features) -> SignalPlan:
    # Heurística simple basada en densidad/cola
    green = min(90.0, max(15.0, 15.0 + f.density * 1.2))
    offset = min(30.0, max(0.0, abs(f.flow) * 0.05))
    phases = 3 if f.queue < 10 else 4
    return SignalPlan(green_time_s=green, offset_s=offset, phase_count=phases)

def predictive(f: Features) -> SignalPlan:
    # "Predictivo" simulado: pondera flujo/cola diferente
    green = min(90.0, max(15.0, 20.0 + f.queue * 0.9 + abs(f.flow) * 0.2))
    offset = min(30.0, max(0.0, f.density * 0.03))
    phases = 4 if f.queue >= 8 else 3
    return SignalPlan(green_time_s=green, offset_s=offset, phase_count=phases)

STRATEGY_MAP = {
    "density": density_based,
    "predictive": predictive,
}
