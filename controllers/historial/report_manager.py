# -*- coding: utf-8 -*-
"""
Nombre del Módulo: report_manager.py (Historial)
Descripción: Gestor encargado de la generación de informes PDF para el historial de 
             iteraciones y fabricaciones, utilizando estrategias de reporte personalizadas.
"""
from __future__ import annotations
import logging
from typing import Any, TYPE_CHECKING
from PyQt6.QtWidgets import QFileDialog
from core.services.report_strategy import (
    GeneradorDeInformes,
    ReporteHistorialFabricacion,
    ReporteHistorialIteracion
)

if TYPE_CHECKING:
    from ui.main_window import MainView

class HistorialReportManager:
    """
    Gestor de reportes para el historial.

    Se encarga de recolectar los datos necesarios según el modo de visualización 
    y disparar la generación de documentos PDF.
    """

    def __init__(self, db: Any, pila_service: Any, worker_service: Any, view: MainView, controller_ref: Any = None):
        """
        Inicializa el HistorialReportManager.

        Args:
            db (Any): Instancia del servicio de base de datos.
            pila_service (Any): Instancia del servicio de pila.
            worker_service (Any): Instancia del servicio de worker.
            view (MainView): Referencia a la vista principal de la aplicación.
            controller_ref (Any, optional): Referencia al controlador, si es necesario. Defaults to None.
        """
        self.db = db
        self.pila_service = pila_service
        self.worker_service = worker_service
        self.view = view
        self.controller_ref = controller_ref
        self.logger = logging.getLogger(__name__)

    def on_print_report_clicked(self) -> None:
        """Generador de informes PDF para historial."""
        page = self.view.pages.get("historial")
        if not page or not hasattr(page, 'results_list'):
            return

        selected_items = page.results_list.selectedItems()
        if not selected_items:
            self.view.show_message("Selección Requerida", "Debe seleccionar un elemento de la lista para imprimir.", "warning")
            return
            
        item_data = selected_items[0].data(Qt.ItemDataRole.UserRole)
        mode = page.current_mode
        success = False
        file_path = ""
        
        if mode == "iteraciones":
            prod_code = item_data.producto_codigo
            prod_desc = item_data.producto_descripcion if hasattr(item_data, 'producto_descripcion') else ""
            full_history = self.db.product_repo.get_product_iterations(prod_code)
            
            file_path, _ = QFileDialog.getSaveFileName(self.view, "Guardar Informe", f"Historial_{prod_code}.pdf", "Archivos PDF (*.pdf)")
            if not file_path:
                return
            
            datos_informe = {"product_code": prod_code, "product_desc": prod_desc, "history": full_history}
            generador = GeneradorDeInformes(ReporteHistorialIteracion())
            success = generador.generar_y_guardar(datos_informe, file_path)
            
        elif mode == "fabricaciones":
            pila_id = item_data.id
            meta_data, _, _, planificacion = self.pila_service.load_pila(pila_id)
            meta_data_safe = meta_data
            _, entradas_bitacora = self.pila_service.get_diario_bitacora(pila_id)
            
            file_path, _ = QFileDialog.getSaveFileName(self.view, "Guardar Informe", f"Informe_{meta_data_safe.nombre if meta_data_safe else 'pila'}.pdf", "Archivos PDF (*.pdf)")
            if not file_path:
                return
            
            datos_completos = {"meta_data": meta_data_safe, "entradas_bitacora": entradas_bitacora, "planificacion": planificacion}
            generador = GeneradorDeInformes(ReporteHistorialFabricacion(self.worker_service))
            success = generador.generar_y_guardar(datos_completos, file_path)
            
        if success:
            self.view.show_message("Éxito", f"El informe se ha guardado en:\n{file_path}", "info")
        elif file_path:
            self.view.show_message("Error", "No se pudo generar el informe PDF.", "critical")
from PyQt6.QtCore import Qt # Importación necesaria para Qt.ItemDataRole.UserRole
