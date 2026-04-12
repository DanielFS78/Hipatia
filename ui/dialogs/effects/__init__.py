# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui.dialogs.effects
Descripción: Efectos visuales Qt (resplandores y progreso) usados en canvas y simulación.
"""

from .golden_glow import GoldenGlowEffect
from .progress import SimulationProgressEffect
from .green_cycle import GreenCycleEffect
from .mixed_gold_green import MixedGoldGreenEffect
from .processing_glow import ProcessingGlowEffect

__all__ = [
    "GoldenGlowEffect",
    "SimulationProgressEffect",
    "GreenCycleEffect",
    "MixedGoldGreenEffect",
    "ProcessingGlowEffect",
]
