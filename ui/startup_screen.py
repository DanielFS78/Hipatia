# -*- coding: utf-8 -*-
"""
Nombre del Módulo: startup_screen
Descripción: Ventana de arranque que verifica el estado del sistema antes de
             mostrar la aplicación principal. Diseñada para usuarios no técnicos
             con mensajes contextuales claros y opción de exportar informe.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QCloseEvent
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QFrame, QScrollArea, QWidget, QFileDialog, QMessageBox,
)

from core.health.health_checker import HealthReport, TableHealth
from core.health.health_worker import HealthCheckWorker

from ui.startup_screen_constants import AUTO_ADVANCE_SECONDS, STATUS_COLORS
from ui.startup_screen_report import generate_startup_report_text
from ui.startup_screen_ui import StartupSectionWidgets, build_startup_ui, render_db_report

logger = logging.getLogger(__name__)


class StartupScreen(QDialog):
    """
    Diálogo modal de arranque que verifica BD y ejecuta tests unitarios.
    Diseñado para usuarios no técnicos con mensajes contextuales.
    """

    startup_complete = pyqtSignal(object)  # HealthReport

    def __init__(self, db_manager: object, run_tests: bool = True, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._db_manager = db_manager
        # DESACTIVAR tests por defecto — causan crash por conflicto con QApplication
        # Los tests unitarios con PyQt6 no pueden ejecutarse desde un subprocess
        # cuando ya hay una QApplication corriendo
        self._run_tests = False  # Forzar a False independientemente del parámetro
        self._report: Optional[HealthReport] = None
        self._auto_timer: Optional[QTimer] = None
        self._auto_countdown = AUTO_ADVANCE_SECONDS
        self._worker: Optional[HealthCheckWorker] = None

        # Atributos de UI (inicializados en `_build_ui`).
        self._scroll_content: Optional[QWidget] = None
        self._scroll_layout: Any = None
        self._tests_section: Optional[StartupSectionWidgets] = None
        self._test_status: Optional[QLabel] = None
        self._test_note: Optional[QLabel] = None
        self._db_section: Optional[StartupSectionWidgets] = None
        self._db_status: Optional[QLabel] = None
        self._db_results_area: Optional[QWidget] = None
        self._db_results_layout: Any = None
        self._summary_section: Optional[StartupSectionWidgets] = None
        self._summary_badge: Optional[QLabel] = None
        self._summary_detail: Optional[QLabel] = None
        self._auto_label: Optional[QLabel] = None
        self._btn_export: Optional[QPushButton] = None
        self._btn_enter: Optional[QPushButton] = None
        self._btn_cancel: Optional[QPushButton] = None

        self.setWindowTitle("Hipatia — Verificación del Sistema")
        self.setMinimumSize(750, 600)
        self.setModal(True)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.CustomizeWindowHint
        )

        self._build_ui()
        self._start_worker()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        build_startup_ui(self)

    # ------------------------------------------------------------------
    # Worker
    # ------------------------------------------------------------------

    def _start_worker(self) -> None:
        logger.info("StartupScreen: iniciando verificación del sistema...")
        self._worker = HealthCheckWorker(self._db_manager, run_tests=self._run_tests)
        self._worker.db_checked.connect(self._on_db_checked)
        self._worker.test_progress.connect(self._on_test_progress)
        self._worker.test_finished.connect(self._on_test_finished)
        self._worker.all_done.connect(self._on_all_done)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_test_finished(self, results: object) -> None:
        """Los tests no se ejecutan durante el startup — este método no se usa."""
        pass

    def _on_test_progress(self, name: str, current: int, total: int) -> None:
        """Los tests no se ejecutan durante el startup — este método no se usa."""
        pass

    def _on_db_checked(self, report: HealthReport) -> None:
        """Actualiza la sección de BD con los resultados."""
        render_db_report(self, report)

    def _on_all_done(self, report: HealthReport) -> None:
        """Muestra el resumen final y habilita botones."""
        self._report = report
        logger.info(f"StartupScreen: verificación completada — estado: {report.overall_status}")

        assert self._summary_section is not None
        assert self._summary_badge is not None
        assert self._summary_detail is not None
        assert self._btn_export is not None
        assert self._btn_enter is not None
        assert self._auto_label is not None

        self._summary_section.frame.show()

        color, icon, label = STATUS_COLORS.get(
            report.overall_status, ("#888", "⚪", report.overall_status)
        )
        self._summary_badge.setText(f"{icon}  {label}")
        self._summary_badge.setStyleSheet(f"color: {color};")

        # Detalle contextual
        lines = []
        if report.overall_status == "STABLE":
            lines.append("El sistema está funcionando correctamente.")
            lines.append("Todos los componentes se han cargado sin errores.")
        elif report.overall_status == "WARNING":
            lines.append("Se han detectado advertencias que requieren atención.")
            lines.append("El sistema puede funcionar, pero se recomienda revisar los detalles.")
        else:
            lines.append("Se han detectado errores críticos en el sistema.")
            lines.append("Contacte con soporte técnico antes de continuar.")

        self._summary_detail.setText("\n".join(lines))

        # Habilitar botones
        self._btn_export.setEnabled(True)
        self._btn_enter.setEnabled(True)

        if report.overall_status == "CRITICAL":
            if not report.db_reachable:
                self._btn_enter.setEnabled(False)
                self._btn_enter.setText("Sistema No Disponible")
            else:
                self._btn_enter.setText("Entrar de Todas Formas")
                self._btn_enter.setStyleSheet("background-color: #c0392b; color: white;")
            self._auto_label.setText("⚠️ Se recomienda exportar el informe y contactar con soporte.")
        elif report.overall_status == "WARNING":
            self._btn_enter.setText("Entrar al Sistema")
            self._auto_label.setText("💡 Puede exportar el informe para revisión posterior.")
        else:
            self._btn_enter.setText("Entrar al Sistema")
            self._start_auto_advance()

    def _on_error(self, msg: str) -> None:
        """Maneja errores durante la verificación."""
        assert self._test_status is not None
        assert self._btn_enter is not None
        assert self._btn_export is not None
        self._test_status.setText(f"❌ Error: {msg}")
        self._btn_enter.setEnabled(True)
        self._btn_export.setEnabled(True)

    # ------------------------------------------------------------------
    # Auto-avance
    # ------------------------------------------------------------------

    def _start_auto_advance(self) -> None:
        """Inicia cuenta regresiva para entrar automáticamente."""
        assert self._auto_label is not None
        self._auto_countdown = AUTO_ADVANCE_SECONDS
        self._auto_label.setText(f"✨ Entrando automáticamente en {self._auto_countdown} segundos...")
        self._auto_timer = QTimer(self)
        self._auto_timer.setInterval(1000)
        self._auto_timer.timeout.connect(self._tick_auto)
        self._auto_timer.start()

    def _tick_auto(self) -> None:
        """Tick de la cuenta regresiva."""
        assert self._auto_label is not None
        self._auto_countdown -= 1
        if self._auto_countdown <= 0:
            if self._auto_timer:
                self._auto_timer.stop()
            self._on_enter()
        else:
            self._auto_label.setText(f"✨ Entrando automáticamente en {self._auto_countdown} segundos...")

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def _on_export_report(self) -> None:
        """Exporta el informe completo a un archivo de texto."""
        if not self._report:
            QMessageBox.warning(self, "Sin Datos", "No hay informe disponible para exportar.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"informe_sistema_{timestamp}.txt"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Informe del Sistema",
            default_name,
            "Archivos de Texto (*.txt);;Todos los Archivos (*)"
        )

        if not file_path:
            return

        try:
            report_text = self._generate_report_text()
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(report_text)

            QMessageBox.information(
                self,
                "Informe Exportado",
                f"El informe se ha guardado correctamente en:\n\n{file_path}\n\n"
                "Puede enviar este archivo a soporte técnico para su revisión."
            )
            logger.info(f"Informe del sistema exportado a: {file_path}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error al Exportar",
                f"No se pudo guardar el informe:\n\n{e}"
            )
            logger.error(f"Error exportando informe: {e}")

    def _generate_report_text(self) -> str:
        """Genera el texto completo del informe para exportación."""
        return generate_startup_report_text(self._report)

    def _on_enter(self) -> None:
        """Acepta el diálogo y continúa al sistema."""
        if self._auto_timer:
            self._auto_timer.stop()
        if self._report:
            self.startup_complete.emit(self._report)
        self.accept()

    def closeEvent(self, event: QCloseEvent | None) -> None:
        """Limpia recursos al cerrar."""
        if self._worker and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait(2000)
        super().closeEvent(event)
