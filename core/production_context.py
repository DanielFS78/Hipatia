from dataclasses import dataclass
from typing import Optional

@dataclass
class ProductionStatus:
    """Data class to hold the status of the current production session."""
    order_number: str
    total_units: int
    units_completed: int
    current_process: str
    active: bool = False

class ProductionContext:
    """
    Manages the context of the current production session for a worker.
    Keeps track of the current Order (OF), progress (1 of X), and current process layer.
    """
    def __init__(self):
        self._status = ProductionStatus(
            order_number="",
            total_units=0,
            units_completed=0,
            current_process="",
            active=False
        )

    def start_session(self, order_number: str, total_units: int, process_name: str):
        """Starts a new production session."""
        self._status = ProductionStatus(
            order_number=order_number,
            total_units=total_units,
            units_completed=0,
            current_process=process_name,
            active=True
        )

    def increment_unit(self):
        """Increments the completed units counter."""
        if self._status.active:
            self._status.units_completed += 1

    def is_complete(self) -> bool:
        """Checks if the target number of units has been reached."""
        return self._status.active and self._status.units_completed >= self._status.total_units

    def get_progress_label(self) -> str:
        """Returns a formatted string like 'Unit 5 of 100'."""
        if not self._status.active:
            return "Sin sesión activa"
        return f"Unidad {self._status.units_completed + 1} de {self._status.total_units}"

    def reset(self):
        """Clears the current session."""
        self._status = ProductionStatus(
            order_number="",
            total_units=0,
            units_completed=0,
            current_process="",
            active=False
        )

    @property
    def order_number(self) -> str:
        return self._status.order_number

    @property
    def current_process(self) -> str:
        return self._status.current_process

    @property
    def is_active(self) -> bool:
        return self._status.active
