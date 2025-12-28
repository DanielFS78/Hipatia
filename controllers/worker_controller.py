# -*- coding: utf-8 -*-
import logging
import hashlib
import sys
from PyQt6.QtCore import QObject, Qt
from PyQt6.QtWidgets import QDialog, QMessageBox

# UI Imports
from ui.dialogs import ChangePasswordDialog
from ui.widgets import GestionDatosWidget, WorkersWidget
from ui.worker.worker_main_window import WorkerMainWindow

# Feature Import (Aliased to avoid collision)
try:
    from features.worker_controller import WorkerController as FeatureWorkerController
except ImportError:
    FeatureWorkerController = None
    
import constants

class WorkerController(QObject):
    """
    Controlador para la gestión de trabajadores (Admin).
    Incluye CRUD de trabajadores, asignación de tareas y lanzamiento de interfaz de operario.
    """
    
    def __init__(self, app_controller):
        super().__init__()
        self.app = app_controller
        self.db = app_controller.db
        self.model = app_controller.model
        self.view = app_controller.view
        self.logger = logging.getLogger("EvolucionTiemposApp")
        
        self.worker_window = None
        self.worker_feature_controller = None

    def _launch_worker_interface(self):
        """
        Lanza la interfaz simplificada para trabajadores.
        """
        try:
            self.logger.info("Iniciando interfaz de trabajador...")

            # Crear ventana principal de trabajador
            self.worker_window = WorkerMainWindow(self.app.current_user)

            self.logger.info("Inicializando QrScanner automáticamente al inicio...")
            self.app._initialize_qr_scanner()
            if not self.app.qr_scanner:
                self.logger.error("Fallo al inicializar el QrScanner automáticamente.")

            if FeatureWorkerController:
                # Crear controlador específico para trabajadores (Feature)
                self.worker_feature_controller = FeatureWorkerController(
                    current_user=self.app.current_user,
                    db_manager=self.model.db,
                    main_window=self.worker_window,
                    qr_scanner=self.app.qr_scanner,
                    tracking_repo=self.app.tracking_repo,
                    label_manager=self.app.label_manager,
                    qr_generator=self.app.qr_generator,
                    label_counter_repo=self.app.label_counter_repo
                )

                # Inicializar el controlador
                self.worker_feature_controller.initialize()

                # Mostrar la ventana
                self.worker_window.show()
                self.logger.info(f"Interfaz de trabajador iniciada para: {self.app.current_user.get('nombre', 'Usuario')}")
            else:
                raise ImportError("No se pudo cargar FeatureWorkerController")

        except ImportError as e:
            self.logger.error(f"Error importando módulos de trabajador: {e}")
            self.logger.warning("Los módulos de trabajador aún no están creados. Mostrando interfaz básica.")

            QMessageBox.information(
                None, "Funcionalidad en Desarrollo",
                "La interfaz de trabajador está en desarrollo.\n\n"
                f"Bienvenido/a: {self.app.current_user.get('nombre', 'Usuario')}\n"
                "Próximamente podrás acceder a tus fabricaciones asignadas."
            )
            sys.exit(0)

        except Exception as e:
            self.logger.critical(f"Error crítico lanzando interfaz de trabajador: {e}", exc_info=True)
            QMessageBox.critical(None, "Error", f"No se pudo iniciar la interfaz de trabajador.\n\nError: {e}")
            sys.exit(1)

    def _on_worker_selected_in_list(self, item):
        worker_id = item.data(Qt.ItemDataRole.UserRole)
        worker_data = self.model.get_worker_details(worker_id)
        gestion_datos_page = self.view.pages.get("gestion_datos")
        if not isinstance(gestion_datos_page, GestionDatosWidget):
            return

        workers_page = gestion_datos_page.trabajadores_tab

        if worker_data:
            workers_page.show_worker_details(worker_data)
            of_list = self.model.db.tracking_repo.get_all_ordenes_fabricacion()
            workers_page.setup_of_completer(of_list)
        else:
            workers_page.clear_details_area()

    def _on_save_worker_clicked(self):
        """Maneja el guardado/actualización de trabajadores."""
        gestion_datos_page = self.view.pages.get("gestion_datos")
        if not isinstance(gestion_datos_page, GestionDatosWidget):
            return

        workers_page = gestion_datos_page.trabajadores_tab
        worker_id = workers_page.current_worker_id
        data = workers_page.get_form_data()

        try:
            if not data or not isinstance(data, dict):
                self.view.show_message("Error", "Datos de trabajador inválidos.", "warning")
                return

            nombre = data.get("nombre_completo", "").strip()
            if not nombre:
                self.view.show_message("Error", "El nombre del trabajador es obligatorio.", "warning")
                return

            username = (data.get("username") or "").strip()
            password = data.get("password") or ""
            role = data.get("role", "Trabajador")

            password_hash = None
            if password:
                self.logger.info(f"Hasheando nueva contraseña para {'nuevo usuario' if worker_id is None else f'usuario ID {worker_id}'}")
                password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

            if username and not role:
                self.view.show_message("Error", "Si se define un nombre de usuario, se debe seleccionar un rol.", "warning")
                return

            username_to_save = username if username else None
            role_to_save = role if username else None

            if worker_id is None:
                if username and not password:
                    self.view.show_message("Error", "Un nuevo usuario debe tener una contraseña.", "warning")
                    return

                result = self.model.add_worker(
                    nombre,
                    data.get("notas", "").strip(),
                    data.get("tipo_trabajador", 1),
                    username_to_save,
                    password_hash,
                    role_to_save
                )
                if result is True:
                    self.view.show_message("Éxito", "Trabajador añadido.", "info")
                    self.update_workers_view()
                elif result == "UNIQUE_CONSTRAINT":
                    self.view.show_message("Error", "Ya existe un trabajador con ese nombre o nombre de usuario.", "warning")
                else:
                    self.view.show_message("Error", "No se pudo añadir el trabajador.", "critical")
            else:
                if self.model.update_worker(
                        worker_id,
                        nombre,
                        data.get("activo", True),
                        data.get("notas", "").strip(),
                        data.get("tipo_trabajador", 1),
                        username_to_save,
                        password_hash,
                        role_to_save
                ):
                    self.view.show_message("Éxito", "Trabajador actualizado.", "info")
                    self.update_workers_view()
                else:
                    self.view.show_message("Error", "No se pudo actualizar.", "critical")

        except Exception as e:
            self.logger.error(f"Error guardando trabajador: {e}")
            self.view.show_message("Error", f"Error inesperado: {e}", "critical")

    def _on_delete_worker_clicked(self, worker_id):
        if self.view.show_confirmation_dialog("Confirmar", "¿Seguro que quieres eliminar a este trabajador?"):
            if self.model.delete_worker(worker_id):
                self.view.show_message("Éxito", "Trabajador eliminado.", "info")
            else:
                self.view.show_message("Error", "No se pudo eliminar.", "critical")

    def update_workers_view(self):
        """Actualiza la vista de trabajadores con TODOS los trabajadores."""
        self.logger.info("Actualizando la vista de trabajadores...")
        gestion_datos_page = self.view.pages.get("gestion_datos")
        if isinstance(gestion_datos_page, GestionDatosWidget):
            workers_page = gestion_datos_page.trabajadores_tab
            workers_data = self.model.get_all_workers()
            workers_page.populate_list(workers_data)

    def _on_change_worker_password_clicked(self, worker_id):
        import traceback
        self.logger.info("DEBUG: _on_change_worker_password_clicked CALLED")
        self.logger.info("".join(traceback.format_stack()))
        
        if not self.app.current_user or self.app.current_user.get('role') != 'Responsable':
            self.view.show_message("Acceso Denegado", "No tienes permisos para esta acción.", "warning")
            return

        worker_data = self.model.get_worker_details(worker_id)
        if not worker_data:
            self.view.show_message("Error", "No se encontró al trabajador.", "critical")
            return

        dialog = ChangePasswordDialog(require_current_password=False, parent=self.view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            passwords = dialog.get_passwords()
            new_pass = passwords['new']
            confirm_pass = passwords['confirm']

            if not new_pass:
                self.view.show_message("Error", "La nueva contraseña no puede estar vacía.", "warning")
                return

            if new_pass != confirm_pass:
                self.view.show_message("Error", "Las contraseñas no coinciden.", "warning")
                return

            if self.model.worker_repo.update_user_password(worker_id, new_pass):
                self.view.show_message("Éxito", f"Contraseña actualizada para {worker_data.get('nombre_completo', 'el trabajador')}.", "info")
            else:
                self.view.show_message("Error", "No se pudo actualizar la contraseña en la base de datos.", "critical")

    def _on_change_own_password_clicked(self):
        if not self.app.current_user:
            return

        admin_id = self.app.current_user['id']
        dialog = ChangePasswordDialog(require_current_password=True, parent=self.view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            passwords = dialog.get_passwords()
            current_pass = passwords['current']
            new_pass = passwords['new']
            confirm_pass = passwords['confirm']

            user_data = self.model.worker_repo.authenticate_user(self.app.current_user['username'], current_pass)
            if not user_data:
                self.view.show_message("Error", "La contraseña actual es incorrecta.", "warning")
                return

            if not new_pass:
                self.view.show_message("Error", "La nueva contraseña no puede estar vacía.", "warning")
                return

            if new_pass != confirm_pass:
                self.view.show_message("Error", "Las nuevas contraseñas no coinciden.", "warning")
                return

            if self.model.worker_repo.update_user_password(admin_id, new_pass):
                self.view.show_message("Éxito", "Tu contraseña ha sido actualizada.", "info")
            else:
                self.view.show_message("Error", "No se pudo actualizar tu contraseña en la base de datos.", "critical")

    def _on_worker_product_search_changed(self, text):
        """Maneja la búsqueda de productos en la pestaña de asignación de tareas del trabajador."""
        gestion_datos_page = self.view.pages.get("gestion_datos")
        if not isinstance(gestion_datos_page, GestionDatosWidget):
            return

        workers_page = gestion_datos_page.trabajadores_tab

        if len(text) < constants.VALIDATION['MIN_SEARCH_LENGTH']:
            workers_page.update_product_search_results([])
            return

        # Usar product_repo directamente
        results = self.model.product_repo.search_products(text)
        workers_page.update_product_search_results(results)

    def _on_assign_task_to_worker_clicked(self):
        gestion_datos_page = self.view.pages.get("gestion_datos")
        if not isinstance(gestion_datos_page, GestionDatosWidget):
            return

        workers_page = gestion_datos_page.trabajadores_tab
        data = workers_page.get_assignment_data()

        if not data:
            self.view.show_message("Error", "Debe seleccionar un producto de la lista.", "warning")
            return

        worker_id = data.get("worker_id")
        product_code = data.get("product_code")
        quantity = data.get("quantity")

        if not all([worker_id, product_code, quantity]):
            self.view.show_message("Error de Datos", "Faltan datos (Trabajador, Producto o Cantidad).", "critical")
            return

        try:
            self.logger.info(f"Creando nueva Tarea/OF para producto {product_code}")
            success, message = self.model.assign_task_to_worker(worker_id, product_code, quantity)

            if success:
                self.view.show_message("Éxito", message, "info")
                workers_page.update_product_search_results([])
                workers_page.form_widgets['product_search'].clear()
                workers_page.form_widgets['quantity_spinbox'].setValue(1)
                self._on_worker_selected_in_list(workers_page.workers_list.currentItem())
            else:
                self.view.show_message("Error", message, "critical")

        except Exception as e:
            self.logger.error(f"Error crítico en _on_assign_task_to_worker_clicked: {e}", exc_info=True)
            self.view.show_message("Error Crítico", f"Error inesperado: {e}", "critical")

    def _on_cancel_task_clicked(self, fabricacion_id):
        try:
            gestion_datos_page = self.view.pages.get("gestion_datos")
            if not isinstance(gestion_datos_page, GestionDatosWidget):
                return

            workers_page = gestion_datos_page.trabajadores_tab
            worker_id = workers_page.current_worker_id

            if not worker_id:
                self.view.show_message("Error", "No hay trabajador seleccionado.", "warning")
                return

            reply = self.view.show_confirmation_dialog(
                "Cancelar Tarea",
                "¿Está seguro que desea cancelar esta tarea?\n\n"
                "La tarea quedará marcada como 'cancelada' y el trabajador ya no la verá en su lista."
            )

            if not reply:
                return

            success = self.model.db.tracking_repo.actualizar_estado_asignacion(
                trabajador_id=worker_id,
                fabricacion_id=fabricacion_id,
                nuevo_estado='cancelado'
            )

            if success:
                self.view.show_message("Éxito", "La tarea ha sido cancelada correctamente.", "info")
                fabrication_history, annotations = self.model.get_worker_history(worker_id)
                workers_page.populate_history_tables(fabrication_history, annotations)
            else:
                self.view.show_message("Error", "No se pudo cancelar la tarea. Verifique los logs para más detalles.", "critical")

        except Exception as e:
            self.logger.error(f"Error cancelando tarea: {e}", exc_info=True)
            self.view.show_message("Error", f"Error inesperado al cancelar la tarea:\n\n{str(e)}", "critical")

    def _connect_workers_signals(self):
        workers_page = self.view.pages.get("gestion_datos").trabajadores_tab
        if isinstance(workers_page, WorkersWidget):
            workers_page.workers_list.itemClicked.connect(self._on_worker_selected_in_list)
            workers_page.add_button.clicked.connect(workers_page.show_add_new_form)
            workers_page.save_signal.connect(self._on_save_worker_clicked)
            workers_page.delete_signal.connect(self._on_delete_worker_clicked)
            workers_page.change_password_signal.connect(self._on_change_worker_password_clicked)
            self.model.workers_changed_signal.connect(self.update_workers_view)
            workers_page.product_search_signal.connect(self._on_worker_product_search_changed)
            workers_page.assign_task_signal.connect(self._on_assign_task_to_worker_clicked)
            workers_page.cancel_task_signal.connect(self._on_cancel_task_clicked)
        self.logger.debug("Señales de 'Gestión Trabajadores' conectadas.")
