from __future__ import annotations
from dataclasses import dataclass
from .acquisition import TrafficSensorReaderAsync
from .processing import TrafficAnalyzer
from .optimization.interfaces import ISignalOptimizer
from .control import TrafficControllerAsync
from .domain import LightState

@dataclass(frozen=True)
class IntersectionPipeline:
    """Encapsula dependencias por intersección (POO, SRP)."""

    reader: TrafficSensorReaderAsync
    """Componente de adquisición: lee datos de sensores de tráfico de forma
    asíncrona (I/O-bound) y devuelve un ``TrafficData``."""

    analyzer: TrafficAnalyzer
    """Componente de procesamiento: extrae métricas (densidad, flujo, cola)
    a partir de los datos crudos del sensor (CPU-bound)."""

    optimizer: ISignalOptimizer
    """Componente de optimización: aplica una estrategia (Strategy pattern)
    para generar un ``SignalPlan`` a partir de las métricas analizadas."""

    controller: TrafficControllerAsync
    """Componente de control: envía el plan de señalización al semáforo
    de forma asíncrona (I/O-bound) y devuelve el ``LightState`` resultante."""

    async def process(self, intersection_id: int) -> LightState:
        """Ejecuta el flujo completo del pipeline para una intersección.

        Secuencia: read → analyze → optimize → update.

        Parameters
        ----------
        intersection_id : int
            Identificador único de la intersección a procesar.

        Returns
        -------
        LightState
            Estado final del semáforo tras aplicar el plan optimizado.
        """
        data = await self.reader.read(intersection_id)
        features = self.analyzer.analyze(data)
        plan = self.optimizer.optimize(features)
        state = await self.controller.update(intersection_id, plan)
        return state
