# -*- coding: utf-8 -*-
"""
Nombre del Módulo: WorkerController
Descripción: Controlador principal para la gestión de trabajadores y acceso a la interfaz de operario.
"""
from __future__ import annotations
import sys
import logging
from typing import Any, Optional
from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QMessageBox

from ui.worker.main_window.window import WorkerMainWindow
from ui.widgets import GestionDatosWidget, WorkersWidget
from .management_manager import WorkerManagementManager
from .auth_manager import WorkerAuthManager
from .task_manager import WorkerTaskManager

# Feature Import (Aliased to avoid collision)
try:
    from features.worker_controller import WorkerController as FeatureWorkerController
except ImportError:  # pragma: no cover
    FeatureWorkerController = None  # type: ignore[assignment,misc]

from .protocols import WorkerControllerProtocol, IWorkerView, IWorkerService, IProductService, IFabricacionService

class WorkerController(QObject):
    """
    Controlador para la gestión de trabajadores (Admin).
    Incluye CRUD de trabajadores, asignación de tareas y lanzamiento de interfaz de operario.
    Implementa WorkerControllerProtocol (Fachada).
    """
    
    def __init__(
        self,
        app_controller: Any,
        view: IWorkerView,
        worker_service: IWorkerService,
        product_service: IProductService,
        fabricacion_service: Optional[IFabricacionService],
        workers_changed_signal: Any,
    ) -> None:
        """
        Inicializa el controlador de trabajadores inyectando dependencias.

        Args:
            app_controller: Controlador principal (sesión, QR, navegación).
            view: Vista principal (protocolo IWorkerView).
            worker_service: Servicio de dominio de trabajadores.
            product_service: Búsqueda de productos en asignación de tareas.
            fabricacion_service: Órdenes de fabricación para autocompletado.
            workers_changed_signal: Señal re-emitida por AppModel al cambiar trabajadores.
        """
        super().__init__()
        self.app = app_controller
        self.view = view
        self.worker_service = worker_service
        self.product_service = product_service
        self.fabricacion_service = fabricacion_service
        self.workers_changed_signal = workers_changed_signal
        self.logger = logging.getLogger("EvolucionTiemposApp")

        self.management_manager = WorkerManagementManager(
            app=self.app,
            view=self.view,
            worker_service=self.worker_service,
            fabricacion_service=self.fabricacion_service,
        )
        self.auth_manager = WorkerAuthManager(
            app=self.app,
            view=self.view,
            worker_service=self.worker_service,
        )
        self.task_manager = WorkerTaskManager(
            app=self.app,
            view=self.view,
            worker_service=self.worker_service,
            product_service=self.product_service,
            controller_ref=self,
        )
        
        self.worker_window: Optional[WorkerMainWindow] = None
        self.worker_feature_controller: Any = None
        self.qr_scanner: Any = None

    def update_workers_view(self) -> None:
        """Actualiza la lista de trabajadores en la vista."""
        self.management_manager.update_workers_view()

    def _launch_worker_interface(self) -> None:
        """
        Lanza la interfaz simplificada para trabajadores.
        """
        try:
            self.logger.info("Iniciando interfaz de trabajador...")
            self.worker_window = WorkerMainWindow(self.app.current_user)

            self.logger.info("Inicializando QrScanner automáticamente al inicio...")
            self.app._initialize_qr_scanner()
            if not self.app.qr_scanner:
                self.logger.error("Fallo al inicializar el QrScanner automáticamente.")

            if FeatureWorkerController is not None:
                self.worker_feature_controller = FeatureWorkerController(
                    current_user=self.app.current_user,
                    db_manager=self.app.db,
                    main_window=self.worker_window,
                    qr_scanner=self.app.qr_scanner,
                    tracking_repo=self.app.tracking_repo,
                    label_manager=self.app.label_manager,
                    qr_generator=self.app.qr_generator,
                    label_counter_repo=self.app.label_counter_repo
                )
                self.worker_feature_controller.initialize()
                self.worker_window.show()
                self.logger.info(f"Interfaz de trabajador iniciada para: {getattr(self.app.current_user, 'nombre_completo', 'Usuario')}")
            else:
                raise ImportError("No se pudo cargar FeatureWorkerController")

        except ImportError as e:
            self.logger.error(f"Error importando módulos de trabajador: {e}")
            self.logger.warning("Los módulos de trabajador aún no están creados. Mostrando interfaz básica.")
            QMessageBox.information(
                None, "Funcionalidad en Desarrollo",
                "La interfaz de trabajador está en desarrollo.\n\n"
                f"Bienvenido/a: {getattr(self.app.current_user, 'nombre_completo', 'Usuario')}\n"
                "Próximamente podrás acceder a tus fabricaciones asignadas."
            )
            sys.exit(0)
        except Exception as e:
            self.logger.critical(f"Error crítico lanzando interfaz de trabajador: {e}", exc_info=True)
            QMessageBox.critical(None, "Error", f"No se pudo iniciar la interfaz de trabajador.\n\nError: {e}")
            sys.exit(1)

    def _connect_workers_signals(self) -> None:
        gestion_datos_page = self.view.pages.get("gestion_datos")
        if gestion_datos_page is None:
            return
        if not hasattr(gestion_datos_page, 'trabajadores_tab'):
            return

        workers_page = gestion_datos_page.trabajadores_tab
        if not workers_page:
            return
        if isinstance(workers_page, WorkersWidget):
            workers_page.workers_list.itemClicked.connect(self.management_manager._on_worker_selected_in_list)
            workers_page.add_button.clicked.connect(workers_page.show_add_new_form)
            workers_page.save_signal.connect(self.management_manager._on_save_worker_clicked)
            workers_page.delete_signal.connect(self.management_manager._on_delete_worker_clicked)
            workers_page.change_password_signal.connect(self.auth_manager._on_change_worker_password_clicked)
            self.workers_changed_signal.connect(self.management_manager.update_workers_view)
            workers_page.product_search_signal.connect(self.task_manager._on_worker_product_search_changed)
            workers_page.assign_task_signal.connect(self.task_manager._on_assign_task_to_worker_clicked)
            workers_page.cancel_task_signal.connect(self.task_manager._on_cancel_task_clicked)
        self.logger.debug("Señales de 'Gestión Trabajadores' conectadas.")
