# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Nombre del Módulo: protocols.py (Worker)
Paquete: controllers.worker — interfaces estructurales para administración de trabajadores.
"""
from typing import Protocol, Any, List, Optional, Dict, Tuple
import logging

from core.dtos import WorkerDetailDTO, WorkerDTO
from core.protocols import IFabricacionService, IProductService
from core.tracking_dtos import FabricacionAsignadaDTO, TrabajoLogDTO


class IWorkerView(Protocol):
    """
    Vista raíz mínima para administración de trabajadores (p. ej. MainView).
    Solo expone lo que usan management/task/auth sobre `self.view`.
    """

    @property
    def pages(self) -> Dict[str, Any]: ...

    def show_message(self, title: str, message: str, level: str = "info") -> None: ...

    def show_confirmation_dialog(self, title: str, message: str) -> bool: ...


class IWorkerService(Protocol):
    """Contrato alineado con `core.services.worker_service.WorkerService`."""

    def get_worker_details(self, worker_id: int) -> WorkerDetailDTO | None: ...

    def update_user_password(self, worker_id: int, new_password_plain: str) -> bool: ...

    def authenticate_user(self, username: str, password_plain: str) -> dict[str, Any] | None: ...

    def add_worker(
        self,
        nombre: str,
        notas: str,
        tipo_trabajador: int,
        username: Optional[str],
        password_hash: Optional[str],
        role: Optional[str],
    ) -> bool | str: ...

    def update_worker(
        self,
        worker_id: int,
        nombre: str,
        activo: bool,
        notas: str,
        tipo_trabajador: int,
        username: Optional[str],
        password_hash: Optional[str],
        role: Optional[str],
    ) -> bool: ...

    def delete_worker(self, worker_id: int) -> bool: ...

    def get_all_workers(self, include_inactive: bool = False) -> list[WorkerDTO]: ...

    def assign_task_to_worker(
        self,
        worker_id: int,
        product_code: str,
        quantity: int,
        orden_fabricacion: str | None = None,
    ) -> Tuple[bool, str]: ...

    def actualizar_estado_asignacion(
        self, trabajador_id: int, fabricacion_id: int, nuevo_estado: str
    ) -> bool: ...

    def get_worker_history(
        self, worker_id: int
    ) -> Tuple[list[FabricacionAsignadaDTO], list[Any]]: ...

    def get_worker_activity_log(self, worker_id: int) -> list[TrabajoLogDTO]: ...


class IWorkerModel(Protocol):
    """Interfaz legacy para tests que aún mockean el modelo agregado."""

    worker_service: IWorkerService
    product_service: IProductService
    fabricacion_service: Optional[IFabricacionService]
    workers_changed_signal: Any

    def get_worker_history(self, worker_id: int) -> Tuple[List[Any], List[Any]]: ...

    def get_worker_activity_log(self, worker_id: int) -> List[Any]: ...


class WorkerControllerProtocol(Protocol):
    """Interfaz para el controlador fachada de Worker."""

    app: Any
    view: IWorkerView
    worker_service: IWorkerService
    logger: logging.Logger
    management_manager: Any

    def update_workers_view(self) -> None: ...
