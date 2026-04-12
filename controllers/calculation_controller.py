# -*- coding: utf-8 -*-
"""
Nombre del Módulo: calculation_controller
Descripción: Gestiona la lógica de cálculo de tiempos de fabricación, incluyendo la 
             interacción con la pila de preprocesos y la exportación de logs de auditoría.
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Optional, List, Dict, Any, cast

from core.dtos import CalculationProductDTO, CalculationSubPartDTO
from PyQt6.QtWidgets import QFileDialog, QWidget

if TYPE_CHECKING:
    from controllers.app_controller import AppController
    from PyQt6.QtWidgets import QListWidgetItem


class CalculationController:
    """
    Controlador para la lógica de cálculo de tiempos de fabricación.
    
    Responsable de orquestar la página de cálculo, gestionar la conexión de sus 
    señales y procesar las operaciones sobre la pila de preprocesos.
    """
    
    def __init__(self, app_controller: "AppController", pila_service: Any) -> None:
        """
        Inicializa el CalculationController.

        Args:
            app_controller: Referencia al AppController principal.
            pila_service: Servicio de pilas (inyectado).
        """
        self.app = app_controller
        self.db = app_controller.db
        self.pila_service = pila_service
        self.view = app_controller.view
        self.logger = logging.getLogger("EvolucionTiemposApp")
        self.logger.info(">>> CALCULATION CONTROLLER LOADED <<<")
    
    # =========================================================================
    # CONEXIÓN DE SEÑALES
    # =========================================================================
    
    def connect_calculate_signals(self) -> None:
        """
        Conecta las señales del widget de cálculo.
        Si la UI no está inicializada, programa la conexión para después.
        """
        calc_page = self.view.pages.get("calculate")
        if not calc_page:
            self.logger.debug("CalculateTimesWidget no disponible aún para conectar señales.")
            return

        # Verificar si la UI está inicializada
        if not hasattr(calc_page, '_ui_setup_complete'):
            self.logger.debug(
                "UI de CalculateTimesWidget no inicializada aún. "
                "Las señales se conectarán cuando se muestre el widget."
            )
            calc_page._pending_signal_connection = True
            return

        # Verificación robusta: Comprobar que los widgets existen
        required_widgets = [
            'lote_search_entry', 'add_lote_button', 'remove_item_button',
            'define_flow_button', 'save_pila_button', 'load_pila_button',
            'manage_bitacora_button', 'export_button', 'export_pdf_button',
            'export_log_button', 'clear_button', 'go_home_button'
        ]

        for widget_name in required_widgets:
            if not hasattr(calc_page, widget_name):
                self.logger.error(f"Widget '{widget_name}' no existe en CalculateTimesWidget")
                return

            widget = getattr(calc_page, widget_name)
            if widget is None:
                self.logger.error(f"Widget '{widget_name}' es None")
                return

            # Verificar que el objeto C++ subyacente no ha sido eliminado
            try:
                widget.objectName()
            except RuntimeError:
                self.logger.error(f"Widget '{widget_name}' ha sido eliminado por Qt")
                return

        # Si llegamos aquí, todos los widgets son válidos
        try:
            assert self.app.pila_controller is not None, "pila_controller no inicializado"
            assert self.app.simulation_controller is not None, "simulation_controller no inicializado"
            
            pila_ctrl = self.app.pila_controller
            sim_ctrl = self.app.simulation_controller
            
            calc_page.lote_search_entry.textChanged.connect(pila_ctrl._on_calc_lote_search_changed)
            calc_page.add_lote_button.clicked.connect(pila_ctrl._on_add_lote_to_pila_clicked)
            calc_page.remove_item_button.clicked.connect(pila_ctrl._on_remove_lote_from_pila_clicked)
            calc_page.define_flow_button.clicked.connect(sim_ctrl._on_define_flow_clicked)
            calc_page.save_pila_button.clicked.connect(pila_ctrl._on_save_pila_clicked)
            calc_page.load_pila_button.clicked.connect(pila_ctrl._on_load_pila_clicked)
            calc_page.manage_bitacora_button.clicked.connect(pila_ctrl._on_ver_bitacora_pila_clicked)
            report_ctrl = getattr(self.app, "report_controller", None)
            if report_ctrl is not None:
                calc_page.export_button.clicked.connect(
                    lambda rc=report_ctrl: rc.on_export_to_excel_clicked(calc_page)
                )
            else:
                calc_page.export_button.clicked.connect(lambda: None)
            calc_page.export_pdf_button.clicked.connect(self.app._on_export_gantt_to_pdf_clicked)
            calc_page.export_log_button.clicked.connect(self.on_export_audit_log)
            calc_page.clear_button.clicked.connect(sim_ctrl._on_clear_simulation)
            calc_page.go_home_button.clicked.connect(self.on_go_home_and_reset_calc)
            self.pila_service.pilas_changed_signal.connect(
                lambda title, msg: self.view.show_message(title, msg, "info")
            )

            calc_page._signals_connected = True
            self.logger.debug("✅ Señales de 'Calcular Tiempos' conectadas correctamente.")
        except RuntimeError as e:
            self.logger.error(f"Error de runtime conectando señales: {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Error inesperado: {e}", exc_info=True)

    # =========================================================================
    # NAVEGACIÓN
    # =========================================================================

    def on_go_home_and_reset_calc(self) -> None:
        """
        Limpia el estado de la simulación y retorna a la pantalla principal.
        Asegura que no queden datos residuales de cálculos anteriores.
        """
        self.logger.info("El usuario solicitó volver al inicio desde la pantalla de cálculo.")
        
        # Reutilizar lógica de limpieza del simulation_controller
        if hasattr(self.app, 'simulation_controller') and self.app.simulation_controller is not None:
            self.app.simulation_controller._on_clear_simulation()
        
        # Navegar a la página de inicio
        self.app.on_nav_button_clicked("home")

    def on_calc_product_result_selected(self, item: Optional[QListWidgetItem]) -> None:
        """Maneja la selección de un producto en los resultados de cálculo."""
        if item:
            self.logger.debug(f"Producto seleccionado en resultados: {item.text()}")
            # Lógica adicional si es necesaria

    # =========================================================================
    # EXPORTACIÓN
    # =========================================================================

    def on_export_audit_log(self) -> None:
        """Exporta el contenido del log de auditoría a un archivo HTML."""
        self.logger.info("Exportando log de auditoría...")
        calc_page = self.view.pages.get("calculate")
        
        if not calc_page or not calc_page.last_audit:
            self.view.show_message("Sin Datos", "No hay un log de auditoría para exportar.", "warning")
            return

        log_content_html = calc_page.audit_log_display.toHtml()

        file_path, _ = QFileDialog.getSaveFileName(
            cast(QWidget, self.view),
            "Guardar Log de Auditoría",
            "Log_Auditoria.html",
            "Archivos HTML (*.html);;Todos los archivos (*.*)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(log_content_html)
            self.view.show_message("Éxito", f"Log de auditoría guardado en:\n{file_path}", "info")
        except Exception as e:
            self.logger.error(f"Error al guardar el log de auditoría: {e}", exc_info=True)
            self.view.show_message("Error", f"No se pudo guardar el archivo: {e}", "critical")

    # =========================================================================
    # OPERACIONES CON PREPROCESOS EN PILA
    # =========================================================================

    def get_fabricacion_products_for_calculation(self, fabricacion_id: int) -> List[CalculationProductDTO]:
        """
        Obtiene y prepara los productos de una fabricación para el motor de cálculo.

        Args:
            fabricacion_id: Identificador único de la fabricación.

        Returns:
            Una lista de CalculationProductDTO con los tiempos y cantidades preparados.
        """
        try:
            # preproceso_repo.get_products_for_fabricacion returns List[FabricacionProductoDTO]
            fabricacion_products = self.db.preproceso_repo.get_products_for_fabricacion(fabricacion_id)

            calculation_data: List[CalculationProductDTO] = []
            for fp_dto in fabricacion_products:
                product_dtos = self.pila_service.get_data_for_calculation(fp_dto.producto_codigo)
                if product_dtos:
                    dto = product_dtos[0]
                    dto.cantidad_en_kit = fp_dto.cantidad
                    calculation_data.append(dto)

            return calculation_data

        except Exception as e:
            self.logger.error(f"Error obteniendo productos de fabricación para cálculo: {e}")
            return []

    def add_preprocesos_to_current_pila(self, preprocesos: List[CalculationProductDTO]) -> int:
        """
        Añade preprocesos a la pila de cálculo actual.

        Args:
            preprocesos: Lista de CalculationProductDTO con la información de los preprocesos.

        Returns:
            int: Número de preprocesos añadidos exitosamente.
        """
        try:
            calc_widget = self.view.pages.get("calculate")
            if not calc_widget or not hasattr(calc_widget, 'add_step_to_pila'):
                self.logger.warning("Widget de cálculo no disponible o no soporta preprocesos")
                return 0

            added_count = 0
            for preproceso in preprocesos:
                if calc_widget.add_step_to_pila(preproceso):
                    added_count += 1

            self.logger.info(f"Añadidos {added_count} preprocesos a la pila actual")
            return added_count

        except Exception as e:
            self.logger.error(f"Error añadiendo preprocesos a pila: {e}")
            return 0


    # =========================================================================
    # MÉTODOS AUXILIARES
    # =========================================================================

    def update_lote_content_table(self) -> None:
        """Refresca la tabla de contenido del lote en la UI."""
        calc_page = self.view.pages.get("calculate")
        if not calc_page:
            return

        # Actualizar la tabla con los datos del lote actual
        if hasattr(calc_page, 'lote_content_table') and calc_page.lote_content_table:
            try:
                calc_page.lote_content_table.setRowCount(0)
                # La lógica de populación puede variar según los datos
            except Exception as e:
                self.logger.error(f"Error actualizando tabla de contenido de lote: {e}")

    def update_calculate_page_lists(self, calc_page: Optional[Any] = None) -> None:
        """
        Actualiza las listas de la página de cálculo.
        
        Args:
            calc_page: Instancia opcional del widget.
        """
        if not calc_page:
            calc_page = self.view.pages.get("calculate")
            
        if calc_page:
            try:
                # Disparar actualización de la tabla si existe logic
                if hasattr(calc_page, '_update_plan_display'):
                    calc_page._update_plan_display()
                # Plantillas de lote: igual que en Definir Lote — al entrar se listan todas
                # (búsqueda vacía en repositorio); el usuario filtra al escribir.
                pila_ctrl = getattr(self.app, "pila_controller", None)
                entry = getattr(calc_page, "lote_search_entry", None)
                if pila_ctrl is not None and entry is not None:
                    try:
                        query = entry.text()
                    except (AttributeError, RuntimeError):
                        query = ""
                    pila_ctrl._on_calc_lote_search_changed(query)
                self.logger.debug("Lista de página de cálculo actualizada.")
            except Exception as e:
                self.logger.error(f"Error actualizando listas de cálculo: {e}")

    def safe_update_calculate_page(self, calc_page: Optional[Any]) -> None:
        """
        Actualiza la página de cálculo de forma segura, con manejo de errores.
        Este método se llama diferido para dar tiempo a Qt a estabilizar los widgets.
        """
        try:
            if not calc_page:
                return
            self.update_calculate_page_lists(calc_page)
        except RuntimeError as e:
            self.logger.error(f"RuntimeError diferido en calculate: {e}", exc_info=True)
        except AttributeError as e:
            self.logger.error(f"AttributeError diferido en calculate: {e}", exc_info=True)
