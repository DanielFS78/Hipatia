# -*- coding: utf-8 -*-
"""
Nombre del Módulo: session_controller.py
Descripción: Gestiona el ciclo de vida de la sesión del usuario, incluyendo la 
             autenticación, cierre de sesión, control de acceso por roles y auditoría.
"""
from __future__ import annotations
import logging
import sys
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, Union, cast
from dataclasses import asdict
from PyQt6.QtWidgets import QDialog, QMessageBox
from core.security.security_service import Permission, SecurityService, UserRole
from core.security.access_control import set_security_service
from core.services.rate_limiter import RateLimiter
from core.services.audit_logger import AuditLogger
from core.dtos import AuthResponseDTO

if TYPE_CHECKING:
    from controllers.app_controller import AppController
    from ui.dialogs import LoginDialog
    from ui.widgets import HomeWidget
    from controllers.worker.controller import WorkerController
    from ui.main_view import MainView

class SessionController:
    """
    Controlador de sesiones y seguridad.

    Responsable de validar credenciales, manejar el bloqueo por intentos fallidos 
    (Rate Limiting) y habilitar/deshabilitar funcionalidades de la UI según el rol.
    """
    app: AppController
    db: Any
    worker_service: Any
    view: Any
    security_service: Optional[SecurityService]
    logger: logging.Logger
    rate_limiter: RateLimiter
    audit_logger: AuditLogger
    current_user: Optional[AuthResponseDTO]
    worker_window: Optional[Any]
    worker_feature_controller: Optional[Any]

    def __init__(self, app_controller: AppController, db: Any, worker_service: Any) -> None:
        """
        Inicializa el controlador de sesión.

        Args:
            app_controller: Referencia al controlador principal de la aplicación.
            db: DatabaseManager (misma instancia que expone AppController).
            worker_service: Servicio de trabajadores (inyectado).
        """
        self.app = app_controller
        self.db = db
        self.worker_service = worker_service
        self.view = app_controller.view
        self.security_service = app_controller.security_service
        self.logger = logging.getLogger("EvolucionTiemposApp.Session")
        
        # Inicializar servicios de seguridad
        sf = self.db.SessionLocal
        if sf is None:
            raise RuntimeError("SessionLocal no inicializado en DatabaseManager")
        self.rate_limiter = RateLimiter(sf)
        self.audit_logger = AuditLogger(sf)
        
        self.current_user: Optional[AuthResponseDTO] = None
        self.worker_window = None
        self.worker_feature_controller: Optional[Any] = None

    def handle_login(self) -> Union[Tuple[Optional[AuthResponseDTO], bool], None]:
        """
        Muestra el diálogo de login y gestiona la autenticación.
        """
        from ui.dialogs import LoginDialog

        # Ensure view is available
        parent_view = self.view if hasattr(self.app, 'view') else None
        
        dialog = LoginDialog(parent_view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            username, password = dialog.get_credentials()
            
            # Verificar si el usuario está bloqueado por rate limiting
            if self.rate_limiter.is_blocked(username):
                self.logger.warning(f"Usuario '{username}' bloqueado temporalmente por exceso de intentos")
                self.view.show_message(
                    "Cuenta Bloqueada Temporalmente",
                    "Demasiados intentos de login fallidos. Por favor, espere 5 minutos.",
                    "warning"
                )
                self.audit_logger.log_login(username, success=False, error_message="Bloqueado por rate limiting")
                return (None, False)
            
            # Usar el método original del repositorio
            user_data = self.worker_service.authenticate_user(username, password)
            if user_data:
                # Registrar intento exitoso en rate limiter
                self.rate_limiter.check_and_record_attempt(username, success=True)
                
                # Registrar en audit log
                self.audit_logger.log_login(
                    username=username,
                    success=True,
                    user_id=user_data.id
                )
                
                self.current_user = user_data
                self.app.current_user = user_data  # Keep sync for compatibility for now
                
                # Registrar usuario en servicio de seguridad
                if self.security_service:
                        self.security_service.login_user(user_data)
                
                self.view.show_message("Login Exitoso", f"Bienvenido, {user_data.nombre_completo}", "info")
                self._update_ui_for_role()
            
                self.logger.info(f"Login exitoso para el usuario '{username}' con rol '{user_data.role}'.")
                
                # Cargar frase célebre
                assert self.app.ui_controller is not None
                self.app.ui_controller.load_quote_for_home()
                
                return (user_data, True)
            else:
                # Registrar intento fallido
                self.rate_limiter.check_and_record_attempt(username, success=False)
                self.audit_logger.log_login(
                    username=username,
                    success=False,
                    error_message="Credenciales incorrectas"
                )
                
                self.logger.warning("Intento de login fallido: credenciales incorrectas")
                return (None, False)
        
        self.logger.info("El usuario canceló el inicio de sesión.")
        return None

    def logout(self) -> None:
        """Cierra la sesión actual."""
        self.current_user = None
        self.app.current_user = None
        if self.security_service:
            self.security_service.logout()
        # Reset UI permissions/view logic here if needed
        if hasattr(self.view, 'switch_page'):
             self.view.switch_page("home")
        
        # Disable sensitive buttons
        main_view = cast('MainView', self.view)
        if hasattr(main_view, 'buttons'):
            for btn_name in ['dashboard', 'reportes', 'historial', 'gestion_datos', 'add_product', 'settings']:
                if btn_name in main_view.buttons:
                    main_view.buttons[btn_name].setEnabled(False)
        self.logger.info("Sesión cerrada.")

    def _update_ui_for_role(self) -> None:
        """Habilita o deshabilita elementos de la UI según los permisos del usuario."""
        if not self.current_user:
            return

        # Verificar permisos usando el servicio de seguridad
        if not self.security_service:
             self.logger.error("SecurityService no disponible")
             return

        can_view_dashboard = self.security_service.has_permission(Permission.VIEW_DASHBOARD)
        can_generate_reports = self.security_service.has_permission(Permission.GENERATE_REPORTS)
        can_view_history = self.security_service.has_permission(Permission.VIEW_HISTORY)
        can_manage_data = self.security_service.has_permission(Permission.CREATE_PRODUCT)
        can_add_product = self.security_service.has_permission(Permission.CREATE_PRODUCT)
        can_manage_settings = self.security_service.has_permission(Permission.MANAGE_SETTINGS)

        # Habilitar/Deshabilitar botones
        main_view = cast('MainView', self.view)
        main_view.buttons['dashboard'].setEnabled(can_view_dashboard)
        main_view.buttons['reportes'].setEnabled(can_generate_reports)
        main_view.buttons['historial'].setEnabled(can_view_history)
        main_view.buttons['gestion_datos'].setEnabled(can_manage_data)
        main_view.buttons['settings'].setEnabled(can_manage_settings)

        # Si no tiene permiso de dashboard principal (ej. operario), redirigir
        if not can_view_dashboard and not can_manage_data:
            self.logger.info("Usuario con acceso limitado. Redirigiendo a vista home/limitada.")
            self.view.switch_page("home")
            self.view.show_message("Acceso Limitado",
                                   "Tu rol tiene acceso limitado a las funciones de gestión.",
                                   "info")

    def launch_worker_interface(self) -> None:
        """
        Lanza la interfaz simplificada para trabajadores.
        """
        try:
            from ui.worker.main_window.window import WorkerMainWindow
            
            # Intentar importar el controlador de feature
            try:
                from features.worker_controller import WorkerController as FeatureWorkerController
            except ImportError:
                FeatureWorkerController = None  # type: ignore[assignment,misc]

            self.logger.info("Iniciando interfaz de trabajador...")

            # Crear ventana principal de trabajador
            # NOTA: app.current_user se actualiza en handle_login, usamos self.current_user
            if not self.current_user:
                raise ValueError("No se puede iniciar la interfaz de trabajador sin un usuario logueado.")

            assert self.current_user is not None
            self.worker_window = WorkerMainWindow(current_user=self.current_user)

            self.logger.info("Inicializando QrScanner automáticamente al inicio...")
            # Usar hardware controller para init
            assert self.app.hardware_controller is not None, "hardware_controller not initialized"
            self.app.hardware_controller.initialize_qr_scanner()
            scanner = self.app.hardware_controller.qr_scanner
            
            if not scanner:
                self.logger.error("Fallo al inicializar el QrScanner automáticamente.")

            if FeatureWorkerController is not None:
                # Crear controlador específico para trabajadores (Feature)
                # La firma debe coincidir con la usada en AppController
                # (current_user, db_manager, main_window, qr_scanner, ...)
                
                # Necesitamos acceso a los repos del app controller o model
                # app.tracking_repo se inicializó en StartupController y se asignó a app
                
                self.worker_feature_controller = FeatureWorkerController(
                    current_user=self.current_user,
                    db_manager=self.db,
                    main_window=self.worker_window,
                    qr_scanner=scanner,
                    tracking_repo=self.app.tracking_repo,
                    label_manager=self.app.label_manager,
                    qr_generator=self.app.qr_generator,
                    label_counter_repo=self.app.label_counter_repo
                )

                # Inicializar el controlador
                assert self.worker_feature_controller is not None
                self.worker_feature_controller.initialize()

                # Mostrar la ventana
                assert self.worker_window is not None
                self.worker_window.show()
                
                user_name = self.current_user.nombre_completo if self.current_user else "Usuario"
                self.logger.info(f"Interfaz de trabajador iniciada para: {user_name}")
            else:
                 # Fallback logic if feature not present (should match AppController fallback)
                 self.logger.warning("Los módulos de trabajador (Feature) no se encontraron.")
                 QMessageBox.information(
                    None,
                    "Funcionalidad en Desarrollo",
                    "La interfaz de trabajador no está disponible (Feature module missing)."
                 )

        except Exception as e:
            self.logger.critical(f"Error crítico lanzando interfaz de trabajador: {e}", exc_info=True)
            QMessageBox.critical(None, "Error", f"No se pudo iniciar la interfaz de trabajador.\n\nError: {e}")
            # Solo salir si es un error inesperado (no un error de validación previo)
            if not isinstance(e, ValueError):
                sys.exit(1)
