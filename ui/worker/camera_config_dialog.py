"""
========================================================================
DIÁLOGO DE CONFIGURACIÓN DE CÁMARA - INTERFAZ TRABAJADOR
========================================================================
Diálogo simple para que trabajadores configuren la cámara QR
sin necesidad de cambiar de usuario.

Versión 2.1 (Corregida):
- Añadida importación de QApplication faltante.
- Añadida validación de tipo en _on_combo_selection_changed.

Autor: Sistema de Trazabilidad
Fecha: 2025
========================================================================
"""

import logging
from typing import Optional

# --- INICIO DE CORRECCIÓN (AÑADIR QApplication) ---
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QGroupBox, QMessageBox,
    QWidget, QApplication
)
# --- FIN DE CORRECCIÓN ---

from PyQt6.QtCore import Qt, QTimer
# Importar CameraInfo y CameraBackend para type hints
from core.camera_manager import CameraManager, CameraInfo, CameraBackend


class CameraConfigDialog(QDialog):
    """
    Diálogo simple para configurar cámara desde ventana trabajador.
    Optimizado con detección ligera/pesada.
    """

    def __init__(self, camera_manager: CameraManager, current_camera_index: int, parent: Optional[QWidget] = None):
        """
        Inicializa el diálogo de configuración de cámara.

        Args:
            camera_manager: Instancia de CameraManager
            current_camera_index: Índice de la cámara actualmente configurada
            parent: Widget padre (opcional)
        """
        super().__init__(parent)

        self.camera_manager = camera_manager
        self.current_camera_index = current_camera_index
        self.logger = logging.getLogger("EvolucionTiemposApp.CameraConfigDialog")

        self.setWindowTitle("⚙️ Configuración de Cámara QR (Optimizado)")
        self.setModal(True)
        self.setMinimumWidth(550)
        self.setMaximumWidth(700)

        self._setup_ui()

        QTimer.singleShot(50, self._load_cameras_light)

        self.logger.info("CameraConfigDialog inicializado (modo optimizado)")

    def _setup_ui(self):
        """Configura la interfaz del diálogo."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel("🎥 Configuración de Cámara QR")
        title_font = title_label.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)

        description_label = QLabel(
            "Aquí puedes cambiar la cámara que utiliza el sistema.\n"
            "La lista se carga al instante. Usa 'Probar Cámara' para validar el hardware."
        )
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: #666; margin-bottom: 10px;")

        layout.addWidget(title_label)
        layout.addWidget(description_label)

        camera_group = QGroupBox("📹 Cámaras Detectadas (Sondeo Rápido)")
        camera_layout = QVBoxLayout(camera_group)
        camera_layout.setSpacing(10)

        camera_select_layout = QHBoxLayout()
        camera_label = QLabel("Seleccionar cámara:")
        camera_label.setMinimumWidth(120)

        self.camera_combo = QComboBox()
        self.camera_combo.setMinimumHeight(35)
        self.camera_combo.addItem("🔄 Sondeando cámaras...", -2)
        self.camera_combo.currentIndexChanged.connect(self._on_combo_selection_changed)

        camera_select_layout.addWidget(camera_label)
        camera_select_layout.addWidget(self.camera_combo, 1)
        camera_layout.addLayout(camera_select_layout)

        self.detect_btn = QPushButton("🔄 Volver a Sondear")
        self.detect_btn.setMinimumHeight(35)
        self.detect_btn.clicked.connect(self._on_detect_cameras)
        self.detect_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white; border: none;
                padding: 8px 15px; border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)
        camera_layout.addWidget(self.detect_btn)
        layout.addWidget(camera_group)

        info_group = QGroupBox("ℹ️ Información y Validación de Hardware")
        info_layout = QVBoxLayout(info_group)

        self.info_label = QLabel(
            f"Cámara actual: {self.current_camera_index}\n"
            "Detectando cámaras disponibles..."
        )
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("padding: 10px; background-color: #ecf0f1; border-radius: 5px;")
        self.info_label.setMinimumHeight(80) # Espacio para detalles

        info_layout.addWidget(self.info_label)
        layout.addWidget(info_group)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        self.test_btn = QPushButton("🎬 Probar Cámara (Validar Hardware)")
        self.test_btn.setMinimumHeight(40)
        self.test_btn.clicked.connect(self._on_test_camera)
        self.test_btn.setEnabled(False)
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6; color: white; border: none;
                padding: 10px 20px; border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #8e44ad; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)

        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6; color: white; border: none;
                padding: 10px 20px; border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)

        self.save_btn = QPushButton("✅ Guardar y Usar")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.clicked.connect(self._on_save_clicked)
        self.save_btn.setEnabled(False)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white; border: none;
                padding: 10px 20px; border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #229954; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)

        buttons_layout.addWidget(self.test_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(self.save_btn)

        layout.addLayout(buttons_layout)

    def _load_cameras_light(self):
        """
        Detecta cámaras con el método LIGERO (rápido) y puebla el combo.
        """
        try:
            self.logger.info("Iniciando sondeo ligero de cámaras...")
            self.camera_combo.clear()
            self.camera_combo.addItem("🔄 Sondeando...", -2)
            self.detect_btn.setEnabled(False)
            self.test_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            self.info_label.setText("Sondeando índices de cámara...")
            self.info_label.setStyleSheet("padding: 10px; background-color: #fef9e7; border-radius: 5px; color: #f39c12;")

            self.repaint()
            QApplication.processEvents() # Asegurar que se muestra "Sondeando"

            # 1. Detección LIGERA (es rápido)
            cameras = self.camera_manager.detect_cameras(force_refresh=True)

            self.camera_combo.clear()

            if not cameras:
                self.camera_combo.addItem("❌ No se encontraron cámaras", -1)
                self._update_info_label(None, "error", "No se detectaron cámaras en ningún índice.")
                self.logger.warning("Sondeo ligero no encontró cámaras")
            else:
                # 2. Poblar el combo
                for camera in cameras:
                    text = f"📹 {camera.name}"
                    if camera.is_external:
                        text += " [USB EXTERNA]"
                    else:
                        text += " [Integrada]"

                    self.camera_combo.addItem(text, camera)

                # 3. Seleccionar la cámara actual
                current_idx = -1
                for i in range(self.camera_combo.count()):
                    cam_info = self.camera_combo.itemData(i)
                    # Comprobar que cam_info es un objeto antes de acceder a .index
                    if isinstance(cam_info, CameraInfo) and cam_info.index == self.current_camera_index:
                        current_idx = i
                        break

                if current_idx >= 0:
                    self.camera_combo.setCurrentIndex(current_idx)

                # 4. Actualizar estado de UI
                self.test_btn.setEnabled(True)
                self.save_btn.setEnabled(True)
                self.logger.info(f"Sondeo ligero completado: {len(cameras)} cámaras encontradas")

                self._on_combo_selection_changed()

        except Exception as e:
            self.logger.error(f"Error en sondeo ligero: {e}", exc_info=True)
            self.camera_combo.clear()
            self.camera_combo.addItem("❌ Error", -1)
            self._update_info_label(None, "error", f"Error crítico al sondear cámaras: {e}")
        finally:
            self.detect_btn.setEnabled(True)

    def _on_detect_cameras(self):
        """Vuelve a ejecutar el sondeo ligero."""
        self.logger.info("Usuario solicitó re-sondear cámaras.")
        self._load_cameras_light()

    def _on_combo_selection_changed(self):
        """Actualiza el panel de info cuando el usuario cambia la selección del combo."""
        cam_info = self.camera_combo.currentData()

        # --- INICIO DE CORRECCIÓN ---
        # cam_info puede ser un int (-1, -2) para los items placeholder.
        # Solo continuar si es una instancia de CameraInfo.
        if not isinstance(cam_info, CameraInfo):
            self._update_info_label(
                None,
                "info",
                f"Cámara actual guardada: {self.current_camera_index}\n\n"
                "Selecciona una cámara de la lista para validarla."
            )
            return
        # --- FIN DE CORRECCIÓN ---

        self._update_info_label(
            cam_info,
            "info",
            f"Cámara actual guardada: {self.current_camera_index}\n"
            f"Cámara seleccionada: {cam_info.index} ({cam_info.name})\n\n"
            "Pulsa 'Probar Cámara' para validar el hardware y ver la resolución."
        )

    def _update_info_label(self, cam_info: Optional[CameraInfo], level: str, message: str):
        """Helper para actualizar el panel de información."""

        full_message = ""

        if cam_info and isinstance(cam_info, CameraInfo): # Doble check
            full_message = f"ℹ️ Cámara {cam_info.index} ({cam_info.name})\n"
            if cam_info.is_working: # Si ha sido validada
                full_message += f"Resolución: {cam_info.width}x{cam_info.height} @ {cam_info.fps:.0f} FPS\n"
                full_message += f"Backend: {cam_info.backend}\n"

        full_message += f"\n{message}"
        self.info_label.setText(full_message)

        if level == "error":
            self.info_label.setStyleSheet("padding: 10px; background-color: #ffe6e6; border-radius: 5px; color: #c0392b;")
        elif level == "success":
            self.info_label.setStyleSheet("padding: 10px; background-color: #d5f4e6; border-radius: 5px; color: #27ae60;")
        else: # info/warning
            self.info_label.setStyleSheet("padding: 10px; background-color: #ecf0f1; border-radius: 5px; color: #34495e;")


    def _on_test_camera(self):
        """
        Prueba la cámara seleccionada usando la validación PESADA y muestra un preview.
        """
        cam_info_light = self.camera_combo.currentData()

        if not isinstance(cam_info_light, CameraInfo):
            QMessageBox.warning(self, "Aviso", "Por favor selecciona una cámara válida.")
            return

        selected_index = cam_info_light.index
        self.logger.info(f"Iniciando validación PESADA (Test) para cámara {selected_index}...")

        self.detect_btn.setEnabled(False)
        self.test_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self._update_info_label(cam_info_light, "info", "Validando hardware (leyendo frames)... Por favor, espera.")
        self.repaint()
        QApplication.processEvents()

        try:
            success = self.camera_manager.test_camera_with_preview(
                selected_index,
                duration=3.0
            )

            cam_info_heavy = self.camera_manager.get_camera_info(selected_index)

            if success and cam_info_heavy:
                current_combo_index = self.camera_combo.currentIndex()
                self.camera_combo.setItemData(current_combo_index, cam_info_heavy)

                QMessageBox.information(
                    self,
                    "✅ Prueba Exitosa",
                    f"La cámara {selected_index} funciona correctamente.\n"
                    f"Resolución detectada: {cam_info_heavy.width}x{cam_info_heavy.height}"
                )
                self._update_info_label(cam_info_heavy, "success", "¡Hardware validado con éxito!")
                self.logger.info(f"Prueba exitosa de cámara {selected_index}")
            else:
                error_msg = "No se pudo leer ningún frame."
                if cam_info_heavy and cam_info_heavy.error_message:
                    error_msg = cam_info_heavy.error_message

                QMessageBox.warning(
                    self,
                    "❌ Error en Prueba",
                    f"No se pudo probar la cámara {selected_index}.\n\nError: {error_msg}"
                )
                self._update_info_label(cam_info_light, "error", f"Fallo en la validación: {error_msg}")
                self.logger.warning(f"Prueba fallida de cámara {selected_index}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al probar la cámara:\n\n{str(e)}")
            self.logger.error(f"Error probando cámara: {e}", exc_info=True)
            self._update_info_label(cam_info_light, "error", f"Error crítico: {e}")
        finally:
            self.detect_btn.setEnabled(True)
            self.test_btn.setEnabled(True)
            self.save_btn.setEnabled(True)

    def _on_save_clicked(self):
        """
        Valida la cámara seleccionada (si no se ha hecho ya) y
        cierra el diálogo con 'Accepted'.
        """
        cam_info = self.camera_combo.currentData()
        if not isinstance(cam_info, CameraInfo):
            QMessageBox.warning(self, "Aviso", "Por favor selecciona una cámara válida.")
            return

        selected_index = cam_info.index

        if not cam_info.is_working:
            self.logger.info(f"Validando hardware de {selected_index} antes de guardar...")
            self.detect_btn.setEnabled(False)
            self.test_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            self._update_info_label(cam_info, "info", "Validando hardware antes de guardar... Espera.")
            self.repaint()
            QApplication.processEvents()

            is_valid, error_msg = self.camera_manager.validate_camera(selected_index)

            self.detect_btn.setEnabled(True)
            self.test_btn.setEnabled(True)
            self.save_btn.setEnabled(True)

            if not is_valid:
                QMessageBox.critical(
                    self,
                    "Error de Validación",
                    f"La cámara {selected_index} no funciona correctamente.\n\n"
                    f"Error: {error_msg}\n\n"
                    "No se puede guardar esta selección."
                )
                self._update_info_label(cam_info, "error", f"Fallo de validación: {error_msg}")
                return

            cam_info_heavy = self.camera_manager.get_camera_info(selected_index)
            if cam_info_heavy:
                self.camera_combo.setItemData(self.camera_combo.currentIndex(), cam_info_heavy)
                self._update_info_label(cam_info_heavy, "success", "Cámara validada y lista para guardar.")

        self.logger.info(f"Guardando selección: Cámara {selected_index}")
        self.accept()

    def get_selected_camera(self) -> Optional[int]:
        """
        Retorna el índice de cámara seleccionado.

        Returns:
            Índice de la cámara seleccionada, o None si no hay selección válida
        """
        cam_info = self.camera_combo.currentData()

        if cam_info and isinstance(cam_info, CameraInfo):
            return cam_info.index

        return None

# ============================================================================
# EJEMPLO DE USO
# ============================================================================
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    # Importar desde el directorio 'core'
    from core.camera_manager import CameraManager

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    print("=" * 70)
    print("DIÁLOGO DE CONFIGURACIÓN DE CÁMARA - Test (Optimizado)")
    print("=" * 70)

    # Crear QApplication ANTES que cualquier widget
    app = QApplication(sys.argv)

    camera_manager = CameraManager()

    CURRENT_INDEX = 0

    dialog = CameraConfigDialog(
        camera_manager=camera_manager,
        current_camera_index=CURRENT_INDEX
    )

    if dialog.exec() == QDialog.DialogCode.Accepted:
        selected = dialog.get_selected_camera()
        print(f"\n✅ Usuario seleccionó cámara: {selected}")
    else:
        print("\n❌ Usuario canceló la configuración")

    print("\n" + "=" * 70)
    print("Test completado")
    print("=" * 70)