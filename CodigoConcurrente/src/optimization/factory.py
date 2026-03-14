from __future__ import annotations
from typing import Dict, Type
from .interfaces import ISignalOptimizer
from .strategies import DensityBasedOptimizer, PredictiveOptimizer

_REGISTRY: Dict[str, Type[ISignalOptimizer]] = {
    "density": DensityBasedOptimizer,
    "predictive": PredictiveOptimizer,
}

def create_optimizer(strategy_id: str) -> ISignalOptimizer:
    """Factory: instancia la estrategia según su identificador.

    Raises ValueError con las estrategias disponibles si el id no existe.
    """
    cls = _REGISTRY.get(strategy_id)
    if cls is None:
        available = ", ".join(sorted(_REGISTRY))
        raise ValueError(
            f"Unknown optimizer strategy_id={strategy_id!r}. "
            f"Available: {available}"
        )
    return cls()
