# -*- coding: utf-8 -*-
"""
Nombre del Módulo: report_controller
Descripción: Gestiona la generación y exportación de informes en diversos formatos 
             (Excel, PDF), incluyendo resultados de simulación e historiales.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, Any, List, Dict, TYPE_CHECKING

from PyQt6.QtWidgets import QFileDialog, QApplication, QWidget
from PyQt6.QtCore import Qt

from core.interfaces.controller_interface import IController

if TYPE_CHECKING:
    from core.models.app_model import AppModel
    from core.simulation.engine.schedule_config import ScheduleConfig
    from database.database_manager import DatabaseManager
    from core.services.worker_service import WorkerService
    from core.services.product_service import ProductService
    from core.services.pila_service import PilaService
    from core.dtos import PilaDTO, LoteDTO, ProductIterationDTO
    from core.reports_dtos import OrdenFabricacionResumenDTO, ResultadoBusquedaDTO

from core.services.report_strategy import (
    GeneradorDeInformes,
    ReporteHistorialFabricacion,
    ReporteHistorialIteracion,
    ReportePilaFabricacionExcelMejorado,
)
from controllers.report_export_helper import ReportExportHelper


class ReportController(IController):
    """
    Controlador de informes y exportaciones.

    Responsable de orquestar la creación de documentos PDF y Excel a partir de 
    datos de simulación, históricos de piezas o registros de actividad.
    """

    db: "DatabaseManager"
    view: Any
    worker_service: "WorkerService"
    product_service: "ProductService"
    pila_service: "PilaService"
    schedule_manager: "ScheduleConfig"
    logger: logging.Logger
    
    last_simulation_results: Optional[List[Dict[str, Any]]]
    last_audit_log: Optional[List[Any]]
    last_production_flow: Optional[List[Dict[str, Any]]]
    last_units_calculated: Optional[int]
    last_flexible_workers_needed: int
    selected_report_item: Optional[Any] # Puede ser OrdenResumenDTO o similar

    def __init__(self, db: "DatabaseManager", view: Any, 
                 worker_service: "WorkerService", product_service: "ProductService", 
                 pila_service: "PilaService", schedule_manager: "ScheduleConfig", 
                 logger: Optional[logging.Logger] = None) -> None:
        """
        Inicializa el controlador de informes.

        Args:
            db: Gestor de base de datos.
            view: Referencia a la vista principal.
            worker_service: Servicio de trabajadores.
            product_service: Servicio de productos.
            pila_service: Servicio de pilas de fabricación.
            schedule_manager: Configuración de horarios.
            logger: Logger opcional.
        """
        super().__init__()
        self.db = db
        self.view = view
        self.worker_service = worker_service
        self.product_service = product_service
        self.pila_service = pila_service
        self.schedule_manager = schedule_manager
        self.logger = logger or logging.getLogger("EvolucionTiemposApp.ReportController")
        
        # Referencias a datos de última simulación (se actualizan desde AppController)
        self.last_simulation_results = None
        self.last_audit_log = None
        self.last_production_flow = None
        self.last_units_calculated = None
        self.last_flexible_workers_needed = 0
        self.selected_report_item = None  # State for currently selected item in reports view
        self._export = ReportExportHelper(self)

    def on_export_to_excel_clicked(self, calc_page: QWidget | None = None) -> bool:
        return self._export.on_export_to_excel_clicked(calc_page)

    def on_export_gantt_to_pdf_clicked(self, calc_page: QWidget | None = None) -> bool:
        return self._export.on_export_gantt_to_pdf_clicked(calc_page)

    def initialize(self) -> None:
        """Inicializa el controlador."""
        self.logger.debug("ReportController inicializado.")

    def cleanup(self) -> None:
        """Limpieza de recursos."""
        self.last_simulation_results = None
        self.last_audit_log = None
        self.logger.debug("ReportController limpiado.")

    def update_simulation_data(
        self, 
        results: List[Dict[str, Any]], 
        audit_log: List[Any], 
        production_flow: List[Dict[str, Any]], 
        units: int, 
        flexible_workers: int = 0
    ) -> None:
        """
        Actualiza los datos de la última simulación para usar en exportaciones.
        
        Args:
            results: Lista de resultados de simulación
            audit_log: Log de auditoría de la simulación
            production_flow: Flujo de producción usado
            units: Unidades calculadas
            flexible_workers: Número de trabajadores flexibles necesarios
        """
        self.last_simulation_results = results
        self.last_audit_log = audit_log
        self.last_production_flow = production_flow
        self.last_units_calculated = units
        self.last_flexible_workers_needed = flexible_workers
        self.logger.debug("Datos de simulación actualizados en ReportController")

    def on_generar_informe_clicked(self, tipo_informe: str, item_id: Optional[int] = None) -> None:
        """Genera el informe seleccionado por el usuario desde la página de Reportes."""
        if not self.selected_report_item:
            self.view.show_message("Error", "No hay un elemento seleccionado.", "warning")
            return

        # --- Caso de uso para el nuevo PDF de Pila de Fabricación ---
        if tipo_informe == 'historial_pila_pdf':
            # Cargamos los últimos resultados de la simulación que están en memoria
            if not self.last_simulation_results:
                self.view.show_message("Error", "No hay datos de una simulación reciente para generar el informe.",
                                       "warning")
                return

            datos_informe = {
                "meta_data": self.selected_report_item,
                "planificacion": self.last_simulation_results,
                "audit": self.last_audit_log,
                "flexible_workers_needed": self.last_flexible_workers_needed,
                "production_flow": self.last_production_flow
            }

            file_path, _ = QFileDialog.getSaveFileName(self.view, "Guardar Informe PDF",
                                                       f"Informe_Optimizacion_{self.selected_report_item.code}.pdf",
                                                       "Archivos PDF (*.pdf)")
            if not file_path: return

            generador = GeneradorDeInformes(ReporteHistorialFabricacion(self.worker_service))
            if generador.generar_y_guardar(datos_informe, file_path):
                self.view.show_message("Éxito", "Informe PDF guardado.", "info")
            else:
                self.view.show_message("Error", "No se pudo generar el informe PDF.", "critical")

        # --- Otros casos de uso (se mantienen como estaban) ---
        elif tipo_informe == 'pila_fabricacion_excel':
            # Esta lógica ya se maneja en el botón de la página de cálculo principal
            pass
        elif tipo_informe == 'historial_iteraciones':
            prod_code = self.selected_report_item.code
            history = self.db.iteration_repo.get_product_iterations(prod_code)
            file_path, _ = QFileDialog.getSaveFileName(self.view, "Guardar Informe", f"Historial_{prod_code}.pdf",
                                                       "Archivos PDF (*.pdf)")
            if not file_path: return

            datos_informe = {"product_code": prod_code, "product_desc": self.selected_report_item.get('description'),
                             "history": history}
            generador = GeneradorDeInformes(ReporteHistorialIteracion())
            if generador.generar_y_guardar(datos_informe, file_path):
                self.view.show_message("Éxito", "Informe PDF guardado.", "info")
            else:
                self.view.show_message("Error", "No se pudo generar el informe PDF.", "critical")

    def on_print_historial_report_clicked(self, historial_widget: Any, historial_data: Optional[Any] = None) -> bool:
        """
        Genera un informe PDF del historial seleccionado.
        """
        try:
            self.logger.info("El usuario ha solicitado imprimir un informe de historial.")
            
            selected_items = historial_widget.results_list.selectedItems()
            if not selected_items:
                self.view.show_message(
                    "Selección Requerida", 
                    "Debe seleccionar un elemento de la lista para imprimir.",
                    "warning"
                )
                return False

            item_data = selected_items[0].data(Qt.ItemDataRole.UserRole)
            mode = historial_widget.current_mode
            success = False
            file_path = ""

            if mode == "iteraciones":
                prod_code = item_data.producto_codigo
                prod_desc = item_data.producto_descripcion if hasattr(item_data, 'producto_descripcion') else ""
                full_history = self.db.iteration_repo.get_product_iterations(prod_code)
                
                file_path, _ = QFileDialog.getSaveFileName(
                    self.view, "Guardar Informe", 
                    f"Historial_{prod_code}.pdf",
                    "Archivos PDF (*.pdf)"
                )
                if not file_path:
                    return False
                    
                datos_informe = {
                    "product_code": prod_code, 
                    "product_desc": prod_desc, 
                    "history": full_history
                }
                generador = GeneradorDeInformes(ReporteHistorialIteracion())
                success = generador.generar_y_guardar(datos_informe, file_path)

            elif mode == "fabricaciones":
                pila_id = item_data.id
                meta_data, _, _, planificacion = self.pila_service.load_pila(pila_id)
                _, entradas_bitacora = self.pila_service.get_diario_bitacora(pila_id)
                
                file_path, _ = QFileDialog.getSaveFileName(
                    self.view, "Guardar Informe",
                    f"Informe_{meta_data.nombre if meta_data else 'pila'}.pdf",
                    "Archivos PDF (*.pdf)"
                )
                if not file_path:
                    return False
                    
                datos_completos = {
                    "meta_data": meta_data, 
                    "entradas_bitacora": entradas_bitacora,
                    "planificacion": planificacion
                }
                generador = GeneradorDeInformes(ReporteHistorialFabricacion(self.worker_service))
                success = generador.generar_y_guardar(datos_completos, file_path)

            if success:
                self.view.show_message("Éxito", f"El informe se ha guardado en:\n{file_path}", "info")
            elif file_path:
                self.view.show_message("Error", "No se pudo generar el informe PDF.", "critical")
                
            return success
        except Exception as e:
            self.handle_error(e, "Print Historial Report")
            return False
