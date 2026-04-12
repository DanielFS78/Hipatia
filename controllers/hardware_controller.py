# -*- coding: utf-8 -*-
"""
Nombre del Módulo: hardware_controller
Descripción: Gestiona la interacción con dispositivos de hardware, principalmente
             cámaras de video para el escaneo de códigos QR. La apertura de captura usa
             ``core.camera_manager.capture.open_video_capture`` (misma cadena de backends que ``CameraManager``).
"""
import cv2
import logging
from typing import Any, Optional, TYPE_CHECKING
from PyQt6.QtWidgets import QMessageBox, QApplication
from PyQt6.QtCore import QObject

if TYPE_CHECKING:
    from core.app_model import AppModel
    from controllers.worker.controller import WorkerController

from core.camera_manager import CameraManager
from core.camera_manager.capture import open_video_capture
from core.qr_scanner import QrScanner

class HardwareController(QObject):
    """
    Controlador para la gestión de dispositivos de hardware.

    Maneja el ciclo de vida de la conexión con cámaras, la detección de dispositivos 
    compatibles, la configuración de resolución y la integración con el escáner QR.
    """
    
    def __init__(self, db: Any, view: Any, logger: Optional[logging.Logger] = None) -> None:
        """
        Inicializa el controlador de hardware.

        Args:
            db: Gestor de base de datos para acceder a la configuración de dispositivos.
            view: Referencia a la vista principal de la aplicación.
            logger: Instancia opcional para el registro de eventos de hardware.
        """
        super().__init__()
        self.db: Any = db
        self.view: Any = view
        self.logger: logging.Logger = logger or logging.getLogger(__name__)
        
        self.camera_manager: CameraManager = CameraManager()
        self.qr_scanner: Optional[QrScanner] = None
        
    def initialize_qr_scanner(self, worker_controller: Optional['WorkerController'] = None) -> None:
        """
        Inicializa el escáner QR configurando el dispositivo de captura de video.

        Resuelve el índice de cámara (configuración guardada, mejor cámara o índice 0),
        abre la captura con ``open_video_capture`` (política de backend alineada con ``CameraManager``)
        y pasa el ``cv2.VideoCapture`` resultante a ``QrScanner``.

        Args:
            worker_controller: Opcional; instancia del controlador de operario para inyectar el scanner.
        """
        camera_object = None
        try:
            # 1. Liberar el scanner anterior si existe
            if self.qr_scanner:
                self.logger.info("Liberando instancia de QrScanner anterior...")
                self.qr_scanner.release_camera()
                self.qr_scanner = None

            # 2. Leer el índice de cámara guardado
            try:
                saved_index = int(self.db.config_repo.get_setting('camera_index', '-1'))
            except (ValueError, TypeError):
                saved_index = -1
            
            self.logger.info(f"Buscando cámara. Configuración guardada: {saved_index}")

            final_camera_index = -1
            camera_to_use = None
            camera_object = None

            # 3. Validar o encontrar la mejor cámara
            if saved_index >= 0:
                self.logger.info(f"Validando cámara guardada (índice {saved_index})...")
                camera_to_use = self.camera_manager.get_camera_info(saved_index)
                if camera_to_use and camera_to_use.is_working:
                    self.logger.info("✓ Cámara guardada es válida.")
                    final_camera_index = camera_to_use.index
                else:
                    self.logger.warning(f"Cámara guardada ({saved_index}) no es válida. Buscando la mejor...")
                    saved_index = -1

            if saved_index < 0:
                camera_to_use = self.camera_manager.get_best_camera()
                if camera_to_use:
                    final_camera_index = camera_to_use.index
                    self.logger.info(f"✓ Mejor cámara encontrada: {final_camera_index} ({camera_to_use.name})")
                    self.db.config_repo.set_setting('camera_index', str(final_camera_index))
                else:
                    self.logger.warning("No se encontró ninguna cámara funcional. Intentando fallback a índice 0.")
                    final_camera_index = 0

            # 4. ABRIR LA CÁMARA (mismo criterio de backend que CameraManager: DSHOW/MSMF en Windows)
            if final_camera_index >= 0:
                self.logger.info(f"Intentando abrir hardware de cámara {final_camera_index}...")
                camera_object = open_video_capture(final_camera_index)

                if not camera_object or not camera_object.isOpened():
                    self.logger.error(f"¡Fallo crítico! No se pudo abrir la cámara {final_camera_index}.")
                    camera_object = None
                else:
                    self.logger.info(f"✓ Hardware de cámara {final_camera_index} abierto y listo.")
                    camera_object.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    camera_object.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    camera_object.set(cv2.CAP_PROP_FPS, 30)

            if not camera_object:
                raise Exception(f"No se pudo crear un objeto VideoCapture válido para el índice {final_camera_index}")

            # 5. Crear QrScanner
            self.logger.info(f"Creando instancia de QrScanner...")
            self.qr_scanner = QrScanner(
                camera_manager=self.camera_manager,
                camera_index=final_camera_index,
                camera_object=camera_object
            )

            if not self.qr_scanner.is_camera_ready:
                raise Exception(f"QrScanner reportó que la cámara {final_camera_index} no está lista.")

            self.logger.info(f"✓ QrScanner inicializado y listo con cámara {final_camera_index}")

            if worker_controller:
                worker_controller.qr_scanner = self.qr_scanner

        except Exception as e:
            self.logger.critical(f"Error crítico inicializando QrScanner: {e}", exc_info=True)
            if camera_object:
                camera_object.release()
            self.qr_scanner = None

            if self.view:
                self.view.show_message(
                    "Error de Cámara",
                    "No se pudo inicializar una cámara funcional.\n\n"
                    "Las funciones de escaneo QR no estarán disponibles.\n"
                    f"Error: {e}",
                    "critical"
                )

    def _get_settings_page_with_camera_combo(self) -> Optional[Any]:
        """Obtiene la página de ajustes si expone `camera_combo`."""
        settings_page = self.view.pages.get("settings")
        if settings_page is None or not hasattr(settings_page, "camera_combo"):
            return None
        return settings_page

    def detect_cameras(self) -> None:
        """Detecta cámaras y actualiza la UI de configuración."""
        self.logger.info("Iniciando detección robusta de cámaras...")

        settings_page = self._get_settings_page_with_camera_combo()
        if settings_page is None:
            return
        camera_combo = getattr(settings_page, "camera_combo", None)
        if camera_combo is None:
            return

        camera_combo.clear()
        camera_combo.addItem("🔎 Detectando cámaras...", -2)
        camera_combo.setEnabled(False)
        QApplication.processEvents()

        try:
            cameras = self.camera_manager.detect_cameras(force_refresh=True)
            camera_combo.clear()

            if not cameras:
                camera_combo.addItem("❌ No se detectaron cámaras", -1)
                self.logger.warning("No se detectaron cámaras")
                QMessageBox.warning(
                    settings_page,
                    "Sin Cámaras",
                    "No se detectaron cámaras.\n\nVerifica que esté conectada."
                )
            else:
                for camera in cameras:
                    text = f"📹 Cámara {camera.index}: {camera.name} ({camera.width}x{camera.height})"
                    camera_combo.addItem(text, camera.index)

                camera_combo.setEnabled(True)
                self.logger.info(f"✓ {len(cameras)} cámara(s) detectada(s)")
                
                camera_list = "\n".join([f"• {c.name}" for c in cameras])
                QMessageBox.information(
                    settings_page,
                    "Cámaras Detectadas",
                    f"Se detectaron {len(cameras)} cámara(s):\n\n{camera_list}"
                )

        except Exception as e:
            self.logger.error(f"Error: {e}", exc_info=True)
            camera_combo.clear()
            camera_combo.addItem("⚠️ Error", -1)
            QMessageBox.critical(settings_page, "Error", f"Error detectando cámaras:\n\n{e}")

    def load_hardware_settings(self) -> None:
        """Carga la configuración de hardware guardada en la UI."""
        settings_page = self._get_settings_page_with_camera_combo()
        if settings_page is None:
            return
        camera_combo = getattr(settings_page, "camera_combo", None)
        if camera_combo is None:
            return

        self.detect_cameras()

        saved_index = int(self.db.config_repo.get_setting('camera_index', '0'))
        combo_index = camera_combo.findData(saved_index)
        if combo_index != -1:
            camera_combo.setCurrentIndex(combo_index)

    def save_hardware_settings(self, worker_controller: Optional['WorkerController'] = None) -> None:
        """Guarda la configuración de hardware con validación."""
        settings_page = self._get_settings_page_with_camera_combo()
        if settings_page is None:
            return
        camera_combo = getattr(settings_page, "camera_combo", None)
        if camera_combo is None:
            return

        selected_index = camera_combo.currentData()

        if selected_index is None or selected_index < 0:
            self.view.show_message("Error", "No hay una cámara válida seleccionada.", "warning")
            return

        try:
            self.logger.info(f"Validando cámara {selected_index} antes de guardar...")
            is_valid, error_msg = self.camera_manager.validate_camera(selected_index)

            if not is_valid:
                self.logger.error(f"Cámara {selected_index} no válida: {error_msg}")
                QMessageBox.warning(
                    settings_page, "Cámara No Válida",
                    f"La cámara seleccionada no funciona correctamente:\n\n{error_msg}\n\n"
                    "Por favor selecciona otra cámara."
                )
                return

            self.db.config_repo.set_setting('camera_index', str(selected_index))
            camera_info = self.camera_manager.get_camera_info(selected_index)
            
            if camera_info:
                camera_type = "EXTERNA" if camera_info.is_external else "INTEGRADA"
                self.logger.info(f"✓ Configuración guardada: Cámara {selected_index} - {camera_info.name} [{camera_type}]")
            else:
                self.logger.info(f"✓ Configuración guardada: cámara {selected_index}")

            # Reinicializar scanner
            self.initialize_qr_scanner(worker_controller)

            # Mostrar mensaje éxito
            if camera_info:
                camera_type_str = "Externa (USB)" if camera_info.is_external else "Integrada"
                camera_desc = (
                    f"📹 {camera_info.name}\n"
                    f"📌 Tipo: {camera_type_str}\n"
                    f"📏 Resolución: {camera_info.width}x{camera_info.height}\n"
                    f"🎬 FPS: {camera_info.fps:.1f}"
                )
            else:
                camera_desc = f"Cámara {selected_index}"

            self.view.show_message(
                "Configuración Guardada",
                f"✓ Configuración de cámara guardada correctamente.\n\n{camera_desc}\n\n"
                "El escáner QR se ha reiniciado con la nueva cámara.",
                "info"
            )

        except Exception as e:
            self.logger.error(f"Error guardando configuración de cámara: {e}", exc_info=True)
            QMessageBox.critical(settings_page, "Error", f"No se pudo guardar la configuración:\n\n{str(e)}")

    def test_camera(self) -> None:
        """Prueba la cámara seleccionada mostrando un preview."""
        settings_page = self._get_settings_page_with_camera_combo()
        if settings_page is None:
            return
        camera_combo = getattr(settings_page, "camera_combo", None)
        if camera_combo is None:
            return

        selected_index = camera_combo.currentData()
        if selected_index is None or selected_index < 0:
            self.view.show_message("Error", "Por favor selecciona una cámara primero.", "warning")
            return

        camera_info = self.camera_manager.get_camera_info(selected_index)
        if camera_info:
            camera_type = "Externa (USB)" if camera_info.is_external else "Integrada"
            camera_details = (
                f"📹 {camera_info.name}\n"
                f"📌 Tipo: {camera_type}\n"
                f"📏 Resolución: {camera_info.width}x{camera_info.height}\n"
                f"🎬 FPS: {camera_info.fps:.1f}"
            )
        else:
            camera_details = f"Cámara {selected_index}"

        reply = QMessageBox.question(
            settings_page,
            "Probar Cámara",
            f"¿Deseas probar esta cámara?\n\n{camera_details}\n\n"
            "Se mostrará una ventana de preview durante 5 segundos.\n"
            "Presiona ESC para cerrar antes.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.logger.info(f"Iniciando preview de cámara {selected_index}")
            success = self.camera_manager.test_camera_with_preview(index=selected_index, duration=5.0)

            if success:
                QMessageBox.information(
                    settings_page, "Test Exitoso",
                    f"✓ La cámara funciona correctamente.\n\n{camera_details}\n\nPuedes guardar esta configuración."
                )
            else:
                camera_info = self.camera_manager.get_camera_info(selected_index)
                error_details = f"\n\nError: {camera_info.error_message}" if camera_info and camera_info.error_message else ""
                
                QMessageBox.warning(
                    settings_page, "Test Fallido",
                    f"✗ No se pudo obtener video de la Cámara {selected_index}.{error_details}\n\n"
                    "Posibles causas:\n• Cámara en uso\n• Sin permisos\n• Desconectada"
                )

        except Exception as e:
            self.logger.error(f"Error probando cámara: {e}", exc_info=True)
            QMessageBox.critical(settings_page, "Error", f"Ocurrió un error al probar la cámara:\n\n{str(e)}")
