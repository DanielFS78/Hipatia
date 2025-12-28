# calculation_audit.py

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

class DecisionStatus(Enum):
    """Define los estados visuales para las decisiones en la interfaz."""
    NEUTRAL = 'NEUTRAL'   # Azul - Informativo
    POSITIVE = 'POSITIVE' # Verde - OK, Avance
    WARNING = 'WARNING'   # Ámbar - Espera, Conflicto leve
    CRITICAL = 'CRITICAL' # Rojo - Error, Conflicto grave

@dataclass
class CalculationDecision:
    """
    Representa una decisión o evento único dentro del motor de cálculo,
    enriquecida con contexto para una mejor experiencia de usuario (UX).
    """
    timestamp: datetime
    decision_type: str
    reason: str
    user_friendly_reason: str

    # Hacemos que los campos específicos de la tarea sean opcionales
    task_name: Optional[str] = None
    product_code: Optional[str] = None
    product_desc: Optional[str] = None

    details: Dict[str, Any] = field(default_factory=dict)
    status: DecisionStatus = DecisionStatus.NEUTRAL
    icon: str = "ℹ️"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
