from __future__ import annotations
from dataclasses import dataclass
from .acquisition import TrafficSensorReaderAsync
from .processing import TrafficAnalyzer
from .optimization.interfaces import ISignalOptimizer
from .control import TrafficControllerAsync

@dataclass(frozen=True)
class IntersectionPipeline:
    """Encapsula dependencias por intersección (POO, SRP)."""
    reader: TrafficSensorReaderAsync
    analyzer: TrafficAnalyzer
    optimizer: ISignalOptimizer
    controller: TrafficControllerAsync
