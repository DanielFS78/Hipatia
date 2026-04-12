# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui_controller

Descripción: Define protocolos o tipos principales: ``UIController``. Controlador de sincronización de la interfaz. Integración típica con: ``__future__``, ``PyQt6``, ``core``.
"""
from __future__ import annotations

import logging
from typing import Optional, Any
from PyQt6.QtCore import QObject, pyqtSignal, QThreadPool
from core.services.machine_service import MachineService
from core.services.worker_service import WorkerService
from core.services.report_service import ReportService
from core.services.product_service import ProductService
from core.quote_service import QuoteService


class UIController(QObject):
    """
    Controlador de sincronización de la interfaz.

    Se encarga de mantener los widgets actualizados frente a cambios en los datos, 
    gestionar barras de progreso y cargar elementos informativos como frases célebres.
    """
    
    # Signals
    dashboard_updated = pyqtSignal()
    workers_view_updated = pyqtSignal()
    machines_view_updated = pyqtSignal()
    
    def __init__(self, view: Any, machine_service: MachineService, worker_service: WorkerService,
                 report_service: ReportService, product_service: ProductService,
                 worker_controller: Any, machine_controller: Any, 
                 quote_service: QuoteService, thread_pool: QThreadPool, logger: logging.Logger) -> None:
        """
        Inicializa el controlador de UI.

        Args:
            view: Referencia a la interfaz principal.
            machine_service: Servicio de máquinas.
            worker_service: Servicio de trabajadores.
            report_service: Servicio de informes.
            product_service: Servicio de productos.
            worker_controller: Referencia al controlador de trabajadores.
            machine_controller: Referencia al controlador de máquinas.
            quote_service: Servicio de frases célebres.
            thread_pool: Pool de hilos para tareas asíncronas.
            logger: Instancia de logging.
        """
        super().__init__()
        self.view = view
        self.machine_service = machine_service
        self.worker_service = worker_service
        self.report_service = report_service
        self.product_service = product_service
        self.worker_controller = worker_controller
        self.machine_controller = machine_controller
        self.quote_service = quote_service
        self.thread_pool = thread_pool
        self.logger = logger
        
    def update_dashboard_view(self) -> None:
        """Actualiza la vista del dashboard."""
        try:
            dashboard_page = self.view.pages.get("dashboard")
            if not dashboard_page:
                return

            # Obtener estadísticas de los servicios
            stats = {
                'machine_stats': self.machine_service.get_machine_usage_stats(),
                'worker_stats': self.worker_service.get_worker_load_stats(),
                'component_stats': self.report_service.get_problematic_components_stats()
            }
            
            # Actualizar el dashboard
            if hasattr(dashboard_page, 'update_stats'):
                dashboard_page.update_stats(stats)
                
            self.dashboard_updated.emit()
        except Exception as e:
            self.logger.error(f"Error actualizando dashboard: {e}", exc_info=True)
        
    def update_workers_view(self) -> None:
        """Actualiza la lista de trabajadores en la vista."""
        self.worker_controller.update_workers_view()
        self.workers_view_updated.emit()
        
    def update_machines_view(self) -> None:
        """Actualiza la lista de máquinas en la vista."""
        self.machine_controller.update_machines_view()
        self.machines_view_updated.emit()
        
    def update_simulation_progress(self, value: int) -> None:
        """
        Actualiza el valor de la barra de progreso en la UI.
        
        Args:
            value: Valor de progreso (0-100)
        """
        try:
            # Buscar el widget de progreso en la vista
            if hasattr(self.view, 'progress_bar'):
                self.view.progress_bar.setValue(value)
        except Exception as e:
            self.logger.error(f"Error actualizando progreso: {e}")
        
    def on_data_changed(self) -> None:
        """
        Maneja eventos de cambio de datos, actualizando vistas relevantes.
        """
        try:
            self.logger.info("Notificando cambio de datos global desde UIController.")
            # Actualizar vistas principales
            self.update_workers_view()
            self.update_machines_view()
            self.update_dashboard_view()
            
            # Refrescar listas específicas si es necesario
            gestion_datos = self.view.pages.get("gestion_datos") if hasattr(self.view, 'pages') else None
            if gestion_datos and hasattr(gestion_datos, "productos_tab"):
                prod_tab = gestion_datos.productos_tab
                if hasattr(prod_tab, "clear_all"):
                    prod_tab.clear_all()
                if hasattr(prod_tab, "update_search_results"):
                    all_products = self.product_service.search_products("")
                    prod_tab.update_search_results(all_products)
        except Exception as e:
            self.logger.error(f"Error en on_data_changed: {e}", exc_info=True)
        
    def load_quote_for_home(self) -> None:
        """
        Anteriormente cargaba una frase de WikiQuote en el HomeWidget.
        El HomeWidget ahora muestra el resumen de salud del sistema en su lugar,
        por lo que este método ya no realiza ninguna acción.
        """
        pass
