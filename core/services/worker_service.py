# -*- coding: utf-8 -*-
"""
Nombre del Módulo: WorkerService
Descripción: Servicio de dominio especializado en la gestión de trabajadores, historial y carga de trabajo.
"""
import logging
from datetime import datetime
from typing import Any
from dataclasses import asdict

from PyQt6.QtCore import QObject, pyqtSignal

from core.dtos import WorkerDTO, WorkerDetailDTO, FabricacionDTO
from core.tracking_dtos import FabricacionAsignadaDTO, TrabajoLogDTO, IncidenciaLogDTO
from database.database_manager import DatabaseManager

class WorkerService(QObject):
    """
    Servicio de dominio para gestionar trabajadores.
    Extraído de FabricacionService para cumplir con SRP.
    """

    workers_changed_signal = pyqtSignal()

    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self._db = db_manager
        self.logger = logging.getLogger("WorkerService")

    @property
    def worker_repo(self) -> Any:
        return self._db.worker_repo

    @property
    def tracking_repo(self) -> Any:
        return self._db.tracking_repo

    @property
    def preproceso_repo(self) -> Any:
        return self._db.preproceso_repo

    @property
    def product_repo(self) -> Any:
        return self._db.product_repo

    @property
    def tracking_assignment_service(self) -> Any:
        if not hasattr(self, '_tracking_assignment_service'):
            from core.services.tracking_assignment_service import TrackingAssignmentService
            self._tracking_assignment_service = TrackingAssignmentService(self._db)
        return self._tracking_assignment_service

    @property
    def pila_repo(self) -> Any:
        return self._db.pila_repo

    def get_all_workers(self, include_inactive: bool = False) -> list[WorkerDTO]:
        """Obtiene todos los trabajadores."""
        return self.worker_repo.get_all_workers(include_inactive)

    def get_latest_workers(self, limit: int = 10) -> list[WorkerDTO]:
        """Obtiene los últimos trabajadores añadidos."""
        return self.worker_repo.get_latest_workers(limit)

    def get_worker_details(self, worker_id: int) -> WorkerDetailDTO | None:
        """Obtiene detalles de un trabajador por ID."""
        return self.worker_repo.get_worker_details(worker_id)

    def add_worker(self, nombre: str, notas: str, tipo_trabajador: int = 1, 
                   username: str | None = None, password_hash: str | None = None, 
                   role: str | None = None) -> bool | str:
        """Añade un nuevo trabajador."""
        result = self.worker_repo.add_worker(
            nombre_completo=nombre, notas=notas, tipo_trabajador=tipo_trabajador,
            activo=True, username=username, password_hash=password_hash, role=role
        )
        if result is True:
            self.workers_changed_signal.emit()
        return result

    def update_worker(self, worker_id: int, nombre: str, activo: bool, notas: str, 
                      tipo_trabajador: int, username: str | None = None, 
                      password_hash: str | None = None, role: str | None = None) -> bool:
        """Actualiza la información de un trabajador."""
        result = self.worker_repo.add_worker(
            nombre_completo=nombre, notas=notas, tipo_trabajador=tipo_trabajador,
            activo=activo, worker_id=worker_id, username=username, 
            password_hash=password_hash, role=role
        )
        success = (result is True)
        if success:
            self.workers_changed_signal.emit()
        return success

    def delete_worker(self, worker_id: int) -> bool:
        """Elimina un trabajador."""
        success = self.worker_repo.delete_worker(worker_id)
        if success:
            self.workers_changed_signal.emit()
        return success

    def assign_task_to_worker(self, worker_id: int, product_code: str, quantity: int, 
                              orden_fabricacion: str | None = None) -> tuple[bool, str]:
        """
        Crea una nueva 'Fabricación' (Fase 12C) y la asigna a un trabajador para su seguimiento.
        
        Este método simplifica el flujo para tareas directas, encapsulando:
        1. Generación de un código único basado en el nombre del trabajador y timestamp.
        2. Creación de la cabecera de fabricación normalizada mediante `FabricacionDTO`.
        3. Asociación del producto requerido a través del repositorio.
        4. Registro de la asignación en el `TrackingAssignmentService`.
        """
        self.logger.info(
            f"Asignando Tarea: W_ID={worker_id}, Prod={product_code}, Qty={quantity}, OF={orden_fabricacion}")
        try:
            # 1. Obtener detalles
            worker_details = self.worker_repo.get_worker_details(worker_id)
            details = self.product_repo.get_product_details(product_code) 
            prod_details = details.producto if details else None

            if not worker_details or not prod_details:
                return False, "No se encontraron detalles del trabajador o producto."

            worker_full_name = worker_details.nombre_completo
            worker_name = worker_full_name.split(' ')[0]

            prod_description = prod_details.descripcion

            timestamp = datetime.now().strftime("%Y%m%d-%H%M")

            # 2. Crear una nueva Fabricación
            fab_codigo = f"TASK-{worker_name.upper()}-{product_code}-{timestamp}"

            if orden_fabricacion:
                fab_desc = f"OF: {orden_fabricacion} | Tarea para {worker_full_name} - {quantity} x {prod_description}"
            else:
                fab_desc = f"Tarea para {worker_full_name} - {quantity} x {prod_description}"

            fab_dto = FabricacionDTO(
                id=0,
                codigo=fab_codigo,
                descripcion=fab_desc,
                preprocesos_ids=[]
            )
            creation_success = self.preproceso_repo.create_fabricacion_with_preprocesos(fab_dto)

            if not creation_success:
                return False, "Error al crear la fabricación. ¿Código duplicado?"

            # Recuperar ID
            fab_id = None
            search_results = self.preproceso_repo.search_fabricaciones(fab_codigo)
            for res in search_results:
                if res.codigo == fab_codigo:
                    fab_id = res.id
                    break

            if not fab_id:
                return False, "Error al recuperar la fabricación recién creada."

            # 3. Añadir el producto a la Fabricación
            add_prod_success = self.preproceso_repo.add_product_to_fabricacion(fab_id, product_code, quantity)
            if not add_prod_success:
                self.preproceso_repo.delete_fabricacion(fab_id)
                return False, "Error al añadir el producto a la fabricación."

            # 4. Asignar la Fabricación al Trabajador
            assign_success = self.tracking_assignment_service.asignar_trabajador_a_fabricacion(worker_id, fab_id)
            if not assign_success:
                self.preproceso_repo.delete_fabricacion(fab_id)
                return False, "Error al asignar la fabricación al trabajador."

            self.logger.info(f"Tarea (Fab ID: {fab_id}) asignada con éxito.")

            of_msg = f" para OF: {orden_fabricacion}" if orden_fabricacion else ""
            return True, f"Tarea '{fab_codigo}'{of_msg} asignada a {worker_full_name}."

        except Exception as e:
            self.logger.error(f"Error crítico en assign_task_to_worker: {e}", exc_info=True)
            return False, f"Error inesperado: {e}"

    def get_worker_history(self, worker_id: int) -> tuple[list[FabricacionAsignadaDTO], list[Any]]:
        """Obtiene el historial de fabricaciones y anotaciones de un trabajador."""
        annotations = self.worker_repo.get_worker_annotations(worker_id)
        try:
            fabrication_history = self.tracking_assignment_service.get_fabricaciones_por_trabajador(worker_id)
        except Exception as e:
            self.logger.error(f"Error obteniendo historial de tareas: {e}")
            fabrication_history = []
        return fabrication_history, annotations

    def get_worker_activity_log(self, worker_id: int) -> list[TrabajoLogDTO]:
        """Obtiene el log de actividad detallado de un trabajador."""
        return self.tracking_repo.get_trabajo_logs_por_trabajador(worker_id)

    def get_worker_load_stats(self) -> dict[str, Any]:
        """
        Calcula la carga de trabajo (duración total de tareas) por trabajador
        basándose en los resultados de simulación de todas las pilas.
        """
        stats: dict[str, float] = {}
        
        pilas = self.pila_repo.get_all_pilas_with_dates()
        for pila in pilas:
            _, _, _, simulation_results = self.pila_repo.load_pila(pila.id)
            
            if not simulation_results:
                continue
                
            for task in simulation_results:
                if not isinstance(task, dict):
                    continue
                    
                duration = task.get("Duracion (min)", 0)
                if not duration:
                    continue
                    
                workers = []
                if "Lista Trabajadores" in task:
                    workers = task["Lista Trabajadores"]
                elif "Trabajador Asignado" in task:
                    w = task["Trabajador Asignado"]
                    workers = w if isinstance(w, list) else [w]
                
                for w_name in workers:
                    if w_name not in stats:
                        stats[w_name] = 0
                    stats[w_name] += duration
                    
        return stats

    def authenticate_user(self, username: str, password_plain: str) -> dict[str, Any] | None:
        """Autentica a un usuario."""
        return self.worker_repo.authenticate_user(username, password_plain)

    def update_user_password(self, worker_id: int, new_password_plain: str) -> bool:
        """Actualiza la contraseña de un usuario."""
        return self.worker_repo.update_user_password(worker_id, new_password_plain)
