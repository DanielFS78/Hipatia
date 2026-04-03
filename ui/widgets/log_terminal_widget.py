# -*- coding: utf-8 -*-
"""
Nombre del Módulo: log_terminal_widget
Descripcion: Widget de terminal interna para la pantalla de inicio de Hipatia.
             Muestra en tiempo real los mensajes de nivel WARNING, ERROR y CRITICAL
             generados por el sistema de logging durante la ejecución, con
             coloración diferenciada por nivel y botones de limpieza y exportación.

             El widget está pensado para uso no técnico: el operario puede trabajar
             con normalidad y consultar este panel antes de cerrar el programa para
             detectar posibles incidencias internas, o exportarlo a un archivo .txt
             para enviar al soporte técnico.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from core.qt_log_handler import QtLogHandler

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paleta de colores de la terminal
# ---------------------------------------------------------------------------
_COLOR_BG = "#1e1e1e"
_COLOR_DEFAULT = "#d4d4d4"
_COLOR_WARNING = "#e5c07b"    # amarillo suave
_COLOR_ERROR = "#e06c75"      # rojo suave
_COLOR_CRITICAL = "#ff5555"   # rojo intenso
_COLOR_TIMESTAMP = "#5c6370"  # gris apagado

_LEVEL_COLORS: dict[str, str] = {
    "WARNING": _COLOR_WARNING,
    "ERROR": _COLOR_ERROR,
    "CRITICAL": _COLOR_CRITICAL,
}


class LogTerminalWidget(QWidget):
    """
    Panel tipo terminal que muestra advertencias y errores internos en tiempo real.

    Características:
    - Muestra únicamente mensajes de nivel WARNING, ERROR y CRITICAL del sistema
      de logging de Python, coloreando cada nivel con un color distinto.
    - Botón **Limpiar** para vaciar la visualización sin afectar los logs en disco.
    - Botón **Exportar** para guardar el contenido completo en un archivo ``.txt``
      seleccionado por el usuario mediante diálogo de sistema.
    - Se integra con ``QtLogHandler`` mediante ``connect_handler()``.

    Uso típico::

        terminal = LogTerminalWidget()
        terminal.connect_handler(qt_log_handler)
        layout.addWidget(terminal)
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Inicializa el widget de terminal y construye su interfaz.

        Args:
            parent: Widget padre de Qt, o None si es raíz.
        """
        super().__init__(parent)
        self._build_ui()

    # ------------------------------------------------------------------
    # Construcción de la UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Construye todos los elementos visuales del widget."""
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        # --- Cabecera ---
        root.addWidget(self._build_header())

        # --- Marco de terminal ---
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setStyleSheet(f"""
            QFrame {{
                border: 1px solid #444;
                border-radius: 8px;
                background-color: {_COLOR_BG};
            }}
        """)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)

        # QTextEdit principal
        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {_COLOR_BG};
                color: {_COLOR_DEFAULT};
                border: none;
                padding: 10px;
            }}
        """)
        mono_font = QFont("Courier New", 10)
        mono_font.setStyleHint(QFont.StyleHint.Monospace)
        self._text_edit.setFont(mono_font)
        self._text_edit.setPlaceholderText(
            "Sin advertencias ni errores registrados durante esta sesión."
        )
        frame_layout.addWidget(self._text_edit)
        root.addWidget(frame)

    def _build_header(self) -> QWidget:
        """
        Construye la cabecera con título y botones de acción.

        Returns:
            Widget que contiene el encabezado completo.
        """
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QLabel("🖥️ TERMINAL DE SISTEMA  —  Advertencias y errores en tiempo real")
        title.setStyleSheet(
            "font-size: 12px; font-weight: bold; color: #3498db; letter-spacing: 1px;"
        )
        layout.addWidget(title)
        layout.addStretch()

        # Botón Limpiar
        self._btn_clear = QPushButton("🗑️  Limpiar")
        self._btn_clear.setToolTip("Limpia la terminal (los logs en disco no se borran)")
        self._btn_clear.setStyleSheet(self._button_style("#555", "#666"))
        self._btn_clear.clicked.connect(self._on_clear)
        layout.addWidget(self._btn_clear)

        # Botón Exportar
        self._btn_export = QPushButton("📤  Exportar .txt")
        self._btn_export.setToolTip(
            "Guarda todo el contenido de la terminal en un archivo .txt para enviar al soporte"
        )
        self._btn_export.setStyleSheet(self._button_style("#2471a3", "#1a5276"))
        self._btn_export.clicked.connect(self._on_export)
        layout.addWidget(self._btn_export)

        return header

    @staticmethod
    def _button_style(bg: str, hover: str) -> str:
        """
        Genera el estilo CSS de un botón de la cabecera.

        Args:
            bg: Color de fondo normal en formato hexadecimal.
            hover: Color de fondo al pasar el cursor.

        Returns:
            Cadena de estilo QSS.
        """
        return f"""
            QPushButton {{
                background-color: {bg};
                color: white;
                border: none;
                padding: 6px 14px;
                border-radius: 5px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {hover}; }}
        """

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def append_log(self, text: str) -> None:
        """
        Añade una línea de log formateada al panel de la terminal.

        Detecta el nivel de log en el texto recibido y aplica la coloración
        correspondiente mediante HTML incrustado en el ``QTextEdit``.
        Desplaza automáticamente el panel al final del contenido.

        Args:
            text: Mensaje de log ya formateado, tal como lo entrega
                  ``QtLogHandler`` tras pasar por su ``Formatter``.
        """
        # Determinar color según nivel contenido en el texto
        color_hex = _COLOR_DEFAULT
        for level, color in _LEVEL_COLORS.items():
            if f"[{level:>8}]" in text or f"[{level}]" in text:
                color_hex = color
                break

        # Escapar caracteres HTML especiales antes de insertar
        safe_text = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        html_line = f'<span style="color:{color_hex}; font-family: Courier New, monospace;">{safe_text}</span><br>'
        self._text_edit.insertHtml(html_line)
        self._text_edit.ensureCursorVisible()

    def connect_handler(self, handler: "QtLogHandler") -> None:
        """
        Conecta la señal del handler de logging al slot de visualización.

        Args:
            handler: Instancia de ``QtLogHandler`` ya registrada en el logger
                     root. A partir de esta llamada, cada mensaje WARNING/ERROR/
                     CRITICAL generado aparecerá automáticamente en el panel.
        """
        handler.emitter.log_emitted.connect(self.append_log)

    # ------------------------------------------------------------------
    # Slots privados
    # ------------------------------------------------------------------

    def _on_clear(self) -> None:
        """Vacía el contenido visible del panel de terminal."""
        self._text_edit.clear()

    def _on_export(self) -> None:
        """
        Abre un diálogo de guardado y exporta el contenido del panel a un .txt.

        El nombre de archivo sugerido incluye la fecha y hora actual para
        facilitar la referencia al soporte técnico.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"hipatia_log_{timestamp}.txt"
        default_dir = os.path.expanduser("~/Desktop")
        default_path = os.path.join(default_dir, default_name)

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar log de sistema",
            default_path,
            "Archivos de texto (*.txt);;Todos los archivos (*)",
        )
        if not path:
            return  # usuario canceló

        try:
            content = self._text_edit.toPlainText()
            with open(path, "w", encoding="utf-8") as f:
                f.write(
                    f"# Log de sistema Hipatia — exportado el "
                    f"{datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}\n"
                    f"# Enviar este archivo al soporte técnico para revisión.\n\n"
                )
                f.write(content)
            QMessageBox.information(
                self,
                "Exportación completada",
                f"El log se ha guardado correctamente en:\n{path}",
            )
        except OSError as exc:
            logger.error("Error al exportar el log de terminal: %s", exc)
            QMessageBox.critical(
                self,
                "Error al exportar",
                f"No se pudo guardar el archivo:\n{exc}",
            )
