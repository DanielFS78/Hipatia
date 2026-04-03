"""Fachada de dominio de trabajadores y asignaciones."""

from __future__ import annotations

from typing import Any


class WorkforceFacade:
    """Agrupa operaciones de WorkerService y TrackingAssignmentService."""

    def __init__(self, worker_service: Any, tracking_assignment_service: Any) -> None:
        self._worker_service = worker_service
        self._tracking_assignment_service = tracking_assignment_service

    def __getattr__(self, name: str) -> Any:
        if hasattr(self._worker_service, name):
            return getattr(self._worker_service, name)
        return getattr(self._tracking_assignment_service, name)
