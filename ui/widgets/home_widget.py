# -*- coding: utf-8 -*-
"""
Nombre del Módulo: home_widget
Descripción: Pantalla de inicio de la aplicación Hipatia. Muestra el resumen
             del último arranque del sistema (estado de BD, integridad, datos)
             y alberga la terminal interna de advertencias y errores en tiempo
             real para que el usuario pueda revisar la salud del programa en
             cualquier momento sin necesidad de acceder a archivos de log.

             El mismo tipo de terminal (``LogTerminalWidget``) existe en la vista
             de trabajador (pestaña Log); el ``QtLogHandler`` solo se conecta a
             uno u otro según el rol tras el login.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame,
)

from ui.widgets.log_terminal_widget import LogTerminalWidget

if TYPE_CHECKING:
    from core.qt_log_handler import QtLogHandler

logger = logging.getLogger(__name__)

_STATUS_COLORS = {
    "STABLE":   ("#27ae60", "✅", "SISTEMA OPERATIVO"),
    "WARNING":  ("#f39c12", "⚠️", "ADVERTENCIAS DETECTADAS"),
    "CRITICAL": ("#e74c3c", "❌", "ERRORES CRÍTICOS"),
}


class HomeWidget(QWidget):
    """
    Widget de inicio: resumen esquemático del último arranque y terminal interna.

    Integra dos paneles verticales:
    - Panel de salud del sistema: estado de BD, tablas y último backup.
    - Terminal de log: mensajes desde el nivel del ``QtLogHandler`` (INFO por
      defecto) en tiempo real, con resaltado para WARNING/ERROR/CRITICAL y
      exportación a archivo.
    """

    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 30, 40, 30)
        root.setSpacing(20)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Título
        title = QLabel("Bienvenido a Hipatia")
        f = QFont()
        f.setPointSize(26)
        f.setBold(True)
        title.setFont(f)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        subtitle = QLabel("Sistema de Gestión de Tiempos de Fabricación")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #888; font-size: 13px; margin-bottom: 15px;")
        root.addWidget(subtitle)

        # Badge de estado
        self._status_badge = QLabel("—")
        f2 = QFont()
        f2.setPointSize(15)
        f2.setBold(True)
        self._status_badge.setFont(f2)
        self._status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_badge.setStyleSheet("color: #888; margin-bottom: 10px;")
        root.addWidget(self._status_badge)

        # Panel de resumen esquemático
        self._summary_frame = QFrame()
        self._summary_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self._summary_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #555;
                border-radius: 10px;
                background-color: #2a2a2a;
                padding: 20px;
            }
        """)
        summary_layout = QVBoxLayout(self._summary_frame)
        summary_layout.setContentsMargins(20, 18, 20, 18)
        summary_layout.setSpacing(15)

        section_lbl = QLabel("📋 ÚLTIMO ARRANQUE DEL SISTEMA")
        section_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #3498db; letter-spacing: 1px;")
        summary_layout.addWidget(section_lbl)

        self._detail_label = QLabel("Ejecuta la aplicación para ver el resumen del sistema.")
        self._detail_label.setWordWrap(True)
        self._detail_label.setStyleSheet("color: #aaa; font-style: italic; line-height: 1.6;")
        summary_layout.addWidget(self._detail_label)

        root.addWidget(self._summary_frame)

        # Terminal interna de advertencias y errores
        self._log_terminal = LogTerminalWidget()
        root.addWidget(self._log_terminal, 1)  # stretch=1 para ocupar espacio restante

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def connect_log_handler(self, handler: "QtLogHandler") -> None:
        """
        Conecta el handler de logging Qt a la terminal interna del widget.

        Invoca ``connect_to_widget()`` del handler, que además de conectar la
        señal reproduce el buffer de mensajes acumulados durante el arranque
        (antes de que la UI estuviera lista).

        Debe llamarse una vez desde ``app.py`` en la rama de vista principal
        (no Trabajador), tras registrar el handler en el logger root.

        Args:
            handler: Instancia de ``QtLogHandler`` ya añadida al logger root
                     mediante ``logging.getLogger().addHandler(handler)``.
        """
        handler.connect_to_widget(self._log_terminal.append_log)

    def update_health_report(self, report: object) -> None:
        """
        Actualiza el panel con el HealthReport de forma esquemática y descriptiva.

        Args:
            report: instancia de HealthReport.
        """
        try:
            status = getattr(report, "overall_status", "STABLE")
            color, icon, label = _STATUS_COLORS.get(status, ("#888", "⚪", status))

            self._status_badge.setText(f"{icon}  {label}")
            self._status_badge.setStyleSheet(f"color: {color}; margin-bottom: 10px;")

            lines: list[str] = []

            # Sección de componentes
            lines.append("🧪 COMPONENTES DEL SISTEMA")
            lines.append("   ✅ Todos los módulos cargados correctamente")
            lines.append("")

            # Sección de base de datos
            db_reachable = getattr(report, "db_reachable", False)
            db_integrity = getattr(report, "db_integrity_ok", False)
            tables = getattr(report, "tables", [])

            lines.append("💾 BASES DE DATOS")
            if db_reachable and db_integrity:
                lines.append("   ✅ Conexión y estructura correctas")
                # Contar tablas OK vs vacías
                ok_count = sum(1 for t in tables if t.status == "OK")
                empty_count = sum(1 for t in tables if t.status == "EMPTY")
                if ok_count > 0:
                    lines.append(f"   ✅ {ok_count} tablas con datos operativos")
                if empty_count > 0:
                    lines.append(f"   ⚠️ {empty_count} tablas sin datos")
            else:
                lines.append("   ❌ Problemas de conexión o integridad")
            lines.append("")

            # Sección de sistema
            sys_info = getattr(report, "system", None)
            if sys_info is not None:
                lines.append("🖥️ INFORMACIÓN DEL SISTEMA")
                lines.append(f"   💾 Último backup: {sys_info.last_backup_date}")
                lines.append(f"   💿 Espacio libre: {sys_info.disk_free_gb} GB")
                if sys_info.last_session_errors > 0:
                    lines.append(f"   ⚠️ Errores en sesión anterior: {sys_info.last_session_errors}")
                else:
                    lines.append("   ✅ Sin errores en sesión anterior")
                lines.append("")

            # Timestamp
            generated_at = getattr(report, "generated_at", None)
            if generated_at is not None:
                lines.append(f"🕐 Verificado el {generated_at.strftime('%d/%m/%Y a las %H:%M')}")

            self._detail_label.setStyleSheet("line-height: 1.8; font-size: 12px;")
            self._detail_label.setText("\n".join(lines) if lines else "Sin datos disponibles.")

        except Exception as e:
            logger.warning(f"Error actualizando HomeWidget con HealthReport: {e}")
