"""
Interfaz PyQt6 (`__init__`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from .golden_glow import GoldenGlowEffect
from .progress import SimulationProgressEffect
from .green_cycle import GreenCycleEffect
from .mixed_gold_green import MixedGoldGreenEffect
from .processing_glow import ProcessingGlowEffect

__all__ = [
    'GoldenGlowEffect',
    'SimulationProgressEffect',
    'GreenCycleEffect',
    'MixedGoldGreenEffect',
    'ProcessingGlowEffect'
]
