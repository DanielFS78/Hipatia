# -*- coding: utf-8 -*-
"""
Nombre del Módulo: app_model.py
Descripción: Fachada principal que centraliza el acceso a todos los servicios de 
             dominio (productos, máquinas, trabajadores, etc.) y la base de datos.
"""
import logging
from datetime import datetime, date
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal

from database.database_manager import DatabaseManager
from core.dtos import (
    ProductDTO, PreprocesoDTO, PilaDTO, WorkerDTO, MachineDTO,
    ProductIterationDTO, PreparationStepDTO, PreparationGroupDTO, MaterialDTO, WorkerAnnotationDTO,
    IterationImageDTO, LoteDTO, FabricacionDTO, WorkerDetailDTO, ProductDetailsDTO,
    CalculationProductDTO, FabricacionProductoDTO
)
from core.reports_dtos import (
    ResultadoBusquedaDTO, OrdenFabricacionResumenDTO, OrdenFabricacionDetalleDTO,
    PromedioTiempoDTO, TiempoTrabajadorDTO, IncidenciaResumenDTO,
    PuntoEvolucionDTO, UnidadTrabajoDTO, ResumenProductoDTO
)

# Import New Services
from core.services.product_service import ProductService
from core.services.pila_service import PilaService
from core.services.worker_service import WorkerService  # Added in Phase 10A
from core.services.machine_service import MachineService  # Added in Phase 10B
from core.services.preparation_service import PreparationService  # Added in Phase 10C
from core.services.fabricacion_service import FabricacionService
from core.services.report_service import ReportService
from core.services.tracking_assignment_service import TrackingAssignmentService
from core.tracking_dtos import FabricacionAsignadaDTO, TrabajoLogDTO
from core.facades import PlanningFacade, ProductFacade
from core.app_model_bridges import (
    AppModelCompatBridge,
    AppModelPlanningBridge,
    AppModelProductBridge,
)
from core.services.system_integration_service import SystemIntegrationService


class AppModel(QObject):
    """
    Modelo unificado de la aplicación (Fachada).

    Proporciona un punto de entrada único para los controladores, delegando la 
    lógica de negocio en servicios especializados y emitiendo señales de cambio.
    """
    # Re-emit signals from services for compatibility
    product_added_signal = pyqtSignal(str)
    product_updated_signal = pyqtSignal()
    product_deleted_signal = pyqtSignal()
    pilas_changed_signal = pyqtSignal(str, str)
    workers_changed_signal = pyqtSignal()
    machines_changed_signal = pyqtSignal()
    
    # Signals that might still be used directly or need bridging
    simulation_state_updated = pyqtSignal(str) 

    def __init__(self, db_manager: DatabaseManager):
        """
        Inicializa el modelo de la aplicación.

        Args:
            db_manager: Gestor de conexión a la base de datos.
        """
        super().__init__()
        self.db = db_manager
        self.logger = logging.getLogger("AppModel")

        # --- Initialize Domain Services ---
        self.product_service = ProductService(db_manager)
        self.pila_service = PilaService(db_manager)
        self.worker_service = WorkerService(db_manager)  # Added in Phase 10A
        self.machine_service = MachineService(db_manager)  # Added in Phase 10B
        self.preparation_service = PreparationService(db_manager)  # Added in Phase 10C
        self.fabricacion_service = FabricacionService(db_manager)
        self.report_service = ReportService(db_manager)
        self.tracking_assignment_service = TrackingAssignmentService(db_manager)
        
        # Alias para compatibilidad con controladores que esperan servicios granulares
        self.material_service = self.product_service

        # Fachadas de dominio (controladores pueden migrar a model.product_facade / planning_facade)
        self.product_facade = ProductFacade(self.product_service)
        self.planning_facade = PlanningFacade(self.pila_service)
        self.system_integration = SystemIntegrationService(self.db)

        # Puentes: mantienen la API legacy de AppModel sobre las fachadas / servicios
        self._product_bridge = AppModelProductBridge(self.product_facade)
        self._planning_bridge = AppModelPlanningBridge(self.planning_facade)
        self._compat_bridge = AppModelCompatBridge(self.report_service, self.system_integration)
        
        # Inicialización de Repositorios
        # NOTA: Las propiedades directas a repos (self.product_repo, etc)
        # se han eliminado en la Fase 11C. Los controladores deben usar
        # los métodos delegadores de AppModel.
        
        # --- Connect Signals ---
        self._connect_service_signals()

    def _connect_service_signals(self):
        """Conecta las señales de los servicios a las señales del AppModel (Bridge)."""
        self.product_service.product_added_signal.connect(self.product_added_signal)
        self.product_service.product_updated_signal.connect(self.product_updated_signal)
        self.product_service.product_deleted_signal.connect(self.product_deleted_signal)
        
        self.pila_service.pilas_changed_signal.connect(self.pilas_changed_signal)
        
        self.worker_service.workers_changed_signal.connect(self.workers_changed_signal)
        self.machine_service.machines_changed_signal.connect(self.machines_changed_signal)

    # Producto / pilas / reportes básicos viven en core.app_model_bridges (ver _product_bridge, etc.).

    # =========================================================================
    # DELEGACIÓN A FABRICACION SERVICE (Trabajadores, Máquinas)
    # =========================================================================

    def get_all_workers(self, include_inactive: bool = False) -> list[WorkerDTO]:
        return self.worker_service.get_all_workers(include_inactive)

    def get_latest_workers(self, limit: int = 10) -> list[WorkerDTO]:
        return self.worker_service.get_latest_workers(limit)
        
    def get_worker_details(self, worker_id: int) -> WorkerDetailDTO | None:
        return self.worker_service.get_worker_details(worker_id)

    def add_worker(self, nombre: str, notas: str, tipo_trabajador: int = 1, username: str | None = None, password_hash: str | None = None, role: str | None = None) -> bool | str:
        return self.worker_service.add_worker(nombre, notas, tipo_trabajador, username, password_hash, role)

    def update_worker(self, worker_id: int, nombre: str, activo: bool, notas: str, tipo_trabajador: int, username: str | None = None, password_hash: str | None = None, role: str | None = None) -> bool:
        return self.worker_service.update_worker(worker_id, nombre, activo, notas, tipo_trabajador, username, password_hash, role)

    def delete_worker(self, worker_id: int) -> bool:
        return self.worker_service.delete_worker(worker_id)

    def authenticate_user(self, username: str, password_plain: str) -> dict[str, Any] | None:
        return self.worker_service.authenticate_user(username, password_plain)

    def update_user_password(self, worker_id: int, new_password_plain: str) -> bool:
        return self.worker_service.update_user_password(worker_id, new_password_plain)

    def assign_task_to_worker(self, worker_id: int, product_code: str, quantity: int, orden_fabricacion: str | None = None) -> tuple[bool, str]:
        return self.worker_service.assign_task_to_worker(worker_id, product_code, quantity, orden_fabricacion)

    # =========================================================================
    # DELEGACIÓN A TRACKING Y ASSIGNMENT
    # =========================================================================

    def get_fabricaciones_por_trabajador(self, trabajador_id: int) -> list[FabricacionAsignadaDTO]:
        return self.tracking_assignment_service.get_fabricaciones_por_trabajador(trabajador_id)

    def actualizar_estado_asignacion(self, trabajador_id: int, fabricacion_id: int, nuevo_estado: str) -> bool:
        return self.tracking_assignment_service.actualizar_estado_asignacion(trabajador_id, fabricacion_id, nuevo_estado)

    def asignar_trabajador_a_fabricacion(self, trabajador_id: int, fabricacion_id: int) -> bool:
        return self.tracking_assignment_service.asignar_trabajador_a_fabricacion(trabajador_id, fabricacion_id)

    def desasignar_trabajador_de_fabricacion(self, trabajador_id: int, fabricacion_id: int) -> bool:
        return self.tracking_assignment_service.desasignar_trabajador_de_fabricacion(trabajador_id, fabricacion_id)
    
    def get_worker_history(self, worker_id: int) -> tuple[list[FabricacionAsignadaDTO], list[Any]]:
        return self.worker_service.get_worker_history(worker_id)

    def get_worker_activity_log(self, worker_id: int) -> list[TrabajoLogDTO]:
        return self.worker_service.get_worker_activity_log(worker_id)
        
    def get_worker_load_stats(self) -> dict[str, Any]:
        return self.worker_service.get_worker_load_stats()
        
    def get_problematic_components_stats(self) -> dict[str, Any]:
         return self.report_service.get_problematic_components_stats()

    def get_dashboard_stats(self) -> dict[str, Any]:
        """
        Obtiene estadísticas consolidadas para el dashboard.
        Delega a los servicios correspondientes.
        """
        return {
            'machine_stats': self.get_machine_usage_stats(),
            'worker_stats': self.get_worker_load_stats(),
            'component_stats': self.get_problematic_components_stats()
        }

    def get_all_machines(self, include_inactive: bool = False) -> list[MachineDTO]:
        return self.machine_service.get_all_machines(include_inactive)
        
    def get_latest_machines(self, limit: int = 10) -> list[MachineDTO]:
        return self.machine_service.get_latest_machines(limit)

    def get_machines_by_process_type(self, tipo_proceso: str) -> list[MachineDTO]:
        return self.machine_service.get_machines_by_process_type(tipo_proceso)

    def add_machine(self, nombre: str, departamento: str, tipo_proceso: str) -> bool | str:
        return self.machine_service.add_machine(nombre, departamento, tipo_proceso)
        
    def update_machine(self, machine_id: int, nombre: str, departamento: str, tipo_proceso: str, activa: bool) -> bool:
        return self.machine_service.update_machine(machine_id, nombre, departamento, tipo_proceso, activa)
        
    def delete_machine(self, machine_id: int) -> bool:
        """Elimina una máquina del registro."""
        return self.machine_service.delete_machine(machine_id)
        
    def get_machine_history(self, machine_id: int) -> dict[str, Any]:
        return self.machine_service.get_machine_history(machine_id)
        
    def add_machine_maintenance(self, machine_id: int, maintenance_date: date, notes: str) -> bool:
        return self.machine_service.add_machine_maintenance(machine_id, maintenance_date, notes)
        
    def get_groups_for_machine(self, machine_id: int) -> list[PreparationGroupDTO]:
        return self.preparation_service.get_groups_for_machine(machine_id)
 
    def add_prep_group(self, machine_id: int, name: str, description: str, producto_codigo: str | None = None) -> int | str | None:
        return self.preparation_service.add_prep_group(machine_id, name, description, producto_codigo)
 
    def update_prep_group(self, group_id: int, name: str, description: str, producto_codigo: str | None = None) -> bool:
        return self.preparation_service.update_prep_group(group_id, name, description, producto_codigo)
 
    def delete_prep_group(self, group_id: int) -> bool:
        return self.preparation_service.delete_prep_group(group_id)
 
    def get_steps_for_group(self, group_id: int) -> list[PreparationStepDTO]:
        return self.preparation_service.get_steps_for_group(group_id)
 
    def add_prep_step(self, group_id: int, name: str, time: float, description: str, is_daily: bool) -> int | None:
        return self.preparation_service.add_prep_step(group_id, name, time, description, is_daily)
 
    def update_prep_step(self, step_id: int, data: dict[str, Any]) -> bool:
        return self.preparation_service.update_prep_step(step_id, data)
 
    def delete_prep_step(self, step_id: int) -> bool:
        return self.preparation_service.delete_prep_step(step_id)

    def get_group_details(self, group_id: int) -> PreparationGroupDTO | None:
        return self.preparation_service.get_group_details(group_id)
        
    def get_prep_step_details(self, step_id: int) -> PreparationStepDTO | None:
        return self.preparation_service.get_prep_step_details(step_id)
        
    def get_prep_step_details_by_ids(self, step_ids: list[int]) -> dict[int, PreparationStepDTO]:
        return self.preparation_service.get_prep_step_details_by_ids(step_ids)
        
    def get_distinct_machine_processes(self) -> list[str]:
        return self.machine_service.get_distinct_machine_processes()
        
    def get_all_prep_steps(self) -> list[Any]:
        return self.fabricacion_service.get_all_prep_steps() if hasattr(self.fabricacion_service, 'get_all_prep_steps') else []
        
    def get_machine_usage_stats(self) -> dict[str, Any]:
        return self.fabricacion_service.get_machine_history_summary() if hasattr(self.fabricacion_service, 'get_machine_history_summary') else {}
        
    def get_prep_info_for_product(self, producto_codigo: str) -> list[Any]:
        return self.fabricacion_service.get_prep_info_for_product(producto_codigo) if hasattr(self.fabricacion_service, 'get_prep_info_for_product') else []

    # =========================================================================
    # DELEGACIÓN A FABRICACION SERVICE (Fabricaciones, Preprocesos)
    # =========================================================================

    def get_latest_fabricaciones(self, limit: int = 5) -> list[Any]:
        """Obtiene las últimas órdenes de fabricación creadas."""
        return self.fabricacion_service.get_latest_fabricaciones(limit)

    def search_fabricaciones(self, query: str) -> list[Any]:
        """Busca órdenes de fabricación por código o descripción."""
        return self.fabricacion_service.search_fabricaciones(query)

    def get_iteration_images(self, iteration_id: int) -> list[IterationImageDTO]:
        """Obtiene las imágenes adicionales vinculadas a una iteración de producto."""
        return self.db.get_iteration_images(iteration_id)

    def update_iteration_file_path(self, iteration_id: int, key: str, final_path: str) -> bool:
        """Actualiza la ruta de almacenamiento de archivos adjuntos (planos/imágenes)."""
        return self.db.update_iteration_file_path(iteration_id, key, final_path)

    def create_fabricacion(self, codigo: str, descripcion: str) -> bool:
        """Crea una nueva orden de fabricación básica."""
        return self.fabricacion_service.create_fabricacion(codigo, descripcion)

    def update_fabricacion_preprocesos(self, fabricacion_id: int, preproceso_ids: list[int]) -> bool:
        """Vincula un conjunto de preprocesos a una fabricación."""
        return self.fabricacion_service.update_fabricacion_preprocesos(fabricacion_id, preproceso_ids)

    def get_preprocesos_by_fabricacion(self, fabricacion_id: int) -> list[PreprocesoDTO]:
        return self.fabricacion_service.get_preprocesos_by_fabricacion(fabricacion_id)

    def get_all_preprocesos_with_components(self) -> list[PreprocesoDTO]:
        return self.fabricacion_service.get_all_preprocesos_with_components()

    def create_preproceso(self, data: dict[str, Any]) -> bool:
        """Crea un nuevo preproceso en el sistema."""
        dto = PreprocesoDTO(
            id=int(data.get("id", 0) or 0),
            nombre=str(data.get("nombre", "")),
            descripcion=str(data.get("descripcion", "")),
            tiempo=float(data.get("tiempo", 0.0) or 0.0),
            componentes_ids=[int(x) for x in (data.get("componentes_ids") or [])],
        )
        return self.fabricacion_service.create_preproceso(dto)

    def update_preproceso(self, preproceso_id: int, data: dict[str, Any]) -> bool:
        """Actualiza los datos de un preproceso existente."""
        dto = PreprocesoDTO(
            id=preproceso_id,
            nombre=str(data.get("nombre", "")),
            descripcion=str(data.get("descripcion", "")),
            tiempo=float(data.get("tiempo", 0.0) or 0.0),
            componentes_ids=[int(x) for x in (data.get("componentes_ids") or [])],
        )
        return self.fabricacion_service.update_preproceso(preproceso_id, dto)

    def delete_preproceso(self, preproceso_id: int) -> bool:
        """Elimina un preproceso del sistema."""
        return self.fabricacion_service.delete_preproceso(preproceso_id)

    def get_fabricacion_by_id(self, fabricacion_id: int) -> FabricacionDTO | None:
        """Busca una orden de fabricación por su ID numérico."""
        return self.db.preproceso_repo.get_fabricacion_by_id(fabricacion_id)

    def get_fabricacion_by_codigo(self, codigo: str) -> FabricacionDTO | None:
        """Busca una orden de fabricación por su código alfanumérico."""
        return self.db.preproceso_repo.get_fabricacion_by_codigo(codigo)

    def get_products_for_fabricacion(self, fabricacion_id: int) -> list[Any]:
        """Obtiene los productos asociados a una orden de fabricación."""
        return self.db.get_products_for_fabricacion(fabricacion_id)

    def create_fabricacion_with_preprocesos(self, data: dict[str, Any]) -> bool:
        """Crea una fabricación y sus preprocesos asociados en una sola transacción."""
        dto = FabricacionDTO(
            id=int(data.get("id", 0) or 0),
            codigo=str(data.get("codigo", "")),
            descripcion=str(data.get("descripcion", "")),
            preprocesos_ids=[int(x) for x in (data.get("preprocesos_ids") or [])],
        )
        return self.db.preproceso_repo.create_fabricacion_with_preprocesos(dto)

    def set_products_for_fabricacion(self, fabricacion_id: int, productos: list[dict[str, Any]]) -> bool:
        """Asigna una lista de productos a una fabricación específica."""
        products_dto = [
            FabricacionProductoDTO(
                producto_codigo=str(p.get("producto_codigo", "")),
                cantidad=max(1, int(p.get("cantidad", 1) or 1)),
                descripcion=str(p.get("descripcion", "")),
            )
            for p in productos
        ]
        return self.db.preproceso_repo.set_products_for_fabricacion(fabricacion_id, products_dto)

    def update_fabricacion_and_preprocesos(
        self, fabricacion_id: int, data: dict[str, Any], preprocesos: list[int] | None
    ) -> bool:
        dto = FabricacionDTO(
            id=fabricacion_id,
            codigo=data.get("codigo", ""),
            descripcion=data.get("descripcion", "")
        )
        return self.db.preproceso_repo.update_fabricacion_and_preprocesos(fabricacion_id, dto, preprocesos)

    def delete_fabricacion(self, fabricacion_id: int) -> bool:
        return self.db.preproceso_repo.delete_fabricacion(fabricacion_id)

    # =========================================================================
    # DELEGACIÓN A PRODUCT BRIDGE (Productos, Iteraciones, Materiales)
    # =========================================================================

    def search_products(self, query: str) -> list[ProductDTO]:
        return self._product_bridge.search_products(query)

    def get_latest_products(self, limit: int = 10) -> list[ProductDTO]:
        return self._product_bridge.get_latest_products(limit)

    def get_product_details(self, codigo: str) -> ProductDetailsDTO:
        return self._product_bridge.get_product_details(codigo)

    def add_product(self, data: dict[str, Any], sub_data: list[Any] | None = None) -> str:
        return self._product_bridge.add_product(data, sub_data)

    def update_product(self, codigo_original: str, data: dict[str, Any], subfabricaciones: list[Any] | None = None) -> bool:
        return self._product_bridge.update_product(codigo_original, data, subfabricaciones)

    def delete_product(self, codigo: str) -> bool:
        """Elimina un producto del catálogo por su código."""
        return self._product_bridge.delete_product(codigo)

    def get_product_iterations(self, codigo_producto: str) -> list[ProductIterationDTO]:
        return self._product_bridge.get_product_iterations(codigo_producto)

    def add_product_iteration(
        self,
        codigo_producto: str,
        responsable: str,
        descripcion: str,
        tipo_fallo: str,
        materiales_list: list[dict[str, Any]],
        ruta_imagen: str | None = None,
        ruta_plano: str | None = None,
    ) -> int | None:
        return self._product_bridge.add_product_iteration(
            codigo_producto, responsable, descripcion, tipo_fallo, materiales_list, ruta_imagen, ruta_plano
        )

    def update_product_iteration_details(self, iteracion_id: int, responsable: str, descripcion: str, tipo_fallo: str) -> bool:
        return self._product_bridge.update_product_iteration_details(iteracion_id, responsable, descripcion, tipo_fallo)

    def add_iteration_image(self, iteracion_id: int, ruta_imagen: str) -> bool:
        return self._product_bridge.add_iteration_image(iteracion_id, ruta_imagen)

    def get_product_iterations_by_id_or_similar(self, iteracion_id: int) -> ProductIterationDTO | None:
        return self._product_bridge.get_product_iterations_by_id_or_similar(iteracion_id)

    def delete_iteration_image(self, image_id: int) -> bool:
        return self._product_bridge.delete_iteration_image(image_id)

    def get_materials_for_product(self, producto_codigo: str) -> list[MaterialDTO]:
        return self._product_bridge.get_materials_for_product(producto_codigo)

    def add_material_to_iteration(self, iteracion_id: int, codigo: str, descripcion: str) -> int | None:
        return self._product_bridge.add_material_to_iteration(iteracion_id, codigo, descripcion)

    def get_all_materials_for_selection(self) -> list[MaterialDTO]:
        return self._product_bridge.get_all_materials_for_selection()

    def update_material(self, material_id: int, nuevo_codigo: str, nueva_descripcion: str) -> bool:
        return self._product_bridge.update_material(material_id, nuevo_codigo, nueva_descripcion)

    def delete_material_link(self, iteracion_id: int, material_id: int) -> bool:
        return self._product_bridge.delete_material_link(iteracion_id, material_id)

    def add_material(self, codigo: str, descripcion: str) -> int | None:
        return self._product_bridge.add_material(codigo, descripcion)

    def delete_material(self, material_id: int) -> bool:
        return self._product_bridge.delete_material(material_id)

    def delete_product_iteration(self, iteracion_id: int) -> bool:
        return self._product_bridge.delete_product_iteration(iteracion_id)

    def link_material_to_product(self, producto_codigo: str, material_id: int) -> bool:
        return self._product_bridge.link_material_to_product(producto_codigo, material_id)

    def unlink_material_from_product(self, producto_codigo: str, material_id: int) -> bool:
        return self._product_bridge.unlink_material_from_product(producto_codigo, material_id)

    def get_all_iterations_with_dates(self) -> list[ProductIterationDTO]:
        return self._product_bridge.get_all_iterations_with_dates()

    # =========================================================================
    # DELEGACIÓN A PLANNING BRIDGE (Pilas, Diario, Cálculo)
    # =========================================================================

    def get_all_pilas(self) -> list[PilaDTO]:
        return self._planning_bridge.get_all_pilas()

    def get_all_pilas_with_dates(self) -> list[PilaDTO]:
        return self._planning_bridge.get_all_pilas_with_dates()

    def load_pila(self, pila_id: int) -> tuple[PilaDTO | None, dict[Any, Any] | None, list[Any] | None, list[Any] | None]:
        return self._planning_bridge.load_pila(pila_id)

    def save_pila(
        self,
        nombre: str,
        descripcion: str,
        pila_de_calculo: dict[str, Any],
        production_flow: list[Any],
        simulation_results: list[Any],
        producto_origen_codigo: str | None = None,
        unidades: int = 1,
    ) -> str | bool | int:
        return self._planning_bridge.save_pila(
            nombre,
            descripcion,
            pila_de_calculo,
            production_flow,
            simulation_results,
            producto_origen_codigo,
            unidades,
        )

    def delete_pila(self, pila_id: int) -> bool:
        return self._planning_bridge.delete_pila(pila_id)

    def get_diario_bitacora(self, pila_id: int) -> tuple[int | None, list[Any]]:
        return self._planning_bridge.get_diario_bitacora(pila_id)

    def add_diario_evento(
        self, pila_id: int, fecha: date, dia_numero: int, plan_previsto: str, trabajo_realizado: str, notas: str
    ) -> bool:
        return self._planning_bridge.add_diario_evento(
            pila_id, fecha, dia_numero, plan_previsto, trabajo_realizado, notas
        )

    def create_diario_bitacora(self, pila_id: int) -> bool:
        return self._planning_bridge.create_diario_bitacora(pila_id)

    def get_data_for_calculation(self, producto_codigo: str) -> list[CalculationProductDTO]:
        return self._planning_bridge.get_data_for_calculation(producto_codigo)

    def get_data_for_calculation_from_session(self, planning_session: list[CalculationProductDTO | dict[str, Any]]) -> list[CalculationProductDTO]:
        return self._planning_bridge.get_data_for_calculation_from_session(planning_session)

    # =========================================================================
    # DELEGACIÓN A REPORT SERVICE (resto de reporting)
    # =========================================================================

    def get_order_units(self, order_id: str) -> list[UnidadTrabajoDTO]:
        return self.report_service.get_order_units(order_id)

    def get_product_reports_dashboard(self, product_code: str, evolution_days: int = 30) -> dict[str, Any]:
        """Obtiene bundle completo de datos de reportes para el producto solicitado."""
        return self.report_service.get_product_dashboard(product_code, evolution_days)

    # =========================================================================
    # DELEGACIÓN A COMPAT BRIDGE (reportes tabulares, lotes, config, órdenes tracking)
    # =========================================================================

    def search_reports_data(self, query: str) -> list[ResultadoBusquedaDTO]:
        return self._compat_bridge.search_reports_data(query)

    def get_orders_for_product(self, product_code: str) -> list[OrdenFabricacionResumenDTO]:
        return self._compat_bridge.get_orders_for_product(product_code)

    def get_order_details(self, order_id: str) -> OrdenFabricacionDetalleDTO | None:
        return self._compat_bridge.get_order_details(order_id)

    def get_product_time_stats(self, product_code: str) -> PromedioTiempoDTO | None:
        return self._compat_bridge.get_product_time_stats(product_code)

    def get_worker_time_stats(self, product_code: str) -> list[TiempoTrabajadorDTO]:
        return self._compat_bridge.get_worker_time_stats(product_code)

    def get_incidents_stats(self, product_code: str) -> list[IncidenciaResumenDTO]:
        return self._compat_bridge.get_incidents_stats(product_code)

    def get_evolution_stats(self, product_code: str, days: int = 30) -> list[PuntoEvolucionDTO]:
        return self._compat_bridge.get_evolution_stats(product_code, days)

    def get_product_summary(self, product_code: str) -> ResumenProductoDTO | None:
        return self._compat_bridge.get_product_summary(product_code)

    def search_lotes(self, query: str) -> list[Any]:
        return self._compat_bridge.search_lotes(query)

    def create_lote(self, data: dict[str, Any]) -> int | None:
        return self._compat_bridge.create_lote(data)

    def get_lote_details(self, lote_id: int) -> LoteDTO | None:
        return self._compat_bridge.get_lote_details(lote_id)

    def update_lote(self, lote_id: int, data: dict[str, Any]) -> bool:
        return self._compat_bridge.update_lote(lote_id, data)

    def delete_lote(self, lote_id: int) -> bool:
        return self._compat_bridge.delete_lote(lote_id)

    def config_get_setting(self, key: str, default: str) -> str:
        return self._compat_bridge.config_get_setting(key, default)

    def config_set_setting(self, key: str, value: str) -> bool:
        return self._compat_bridge.config_set_setting(key, value)

    def get_all_ordenes_fabricacion(self) -> list[str]:
        return self._compat_bridge.get_all_ordenes_fabricacion()
