# -*- coding: utf-8 -*-
"""Tests unitarios para LogTerminalWidget.

Cubre inicialización, coloración por nivel, limpieza, exportación a .txt
y conexión con QtLogHandler.
"""
from __future__ import annotations

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from ui.widgets.log_terminal_widget import LogTerminalWidget

pytestmark = pytest.mark.unit


class TestLogTerminalWidget:
    """Tests unitarios para LogTerminalWidget."""

    @pytest.fixture
    def widget(self, qtbot: object) -> LogTerminalWidget:
        """Instancia fresca de LogTerminalWidget registrada en qtbot."""
        w = LogTerminalWidget()
        qtbot.addWidget(w)  # type: ignore[attr-defined]
        return w

    def test_init(self, widget: LogTerminalWidget) -> None:
        """El widget se inicializa con el QTextEdit vacío."""
        assert widget._text_edit is not None
        assert widget._text_edit.toPlainText() == ""

    def test_init_has_buttons(self, widget: LogTerminalWidget) -> None:
        """Los botones de limpiar y exportar existen tras la construcción."""
        assert widget._btn_clear is not None
        assert widget._btn_export is not None

    def test_append_log_warning(self, widget: LogTerminalWidget) -> None:
        """append_log añade texto al QTextEdit para un mensaje WARNING."""
        widget.append_log("12:00:00  [ WARNING]  mi.modulo: Algo fue mal")
        content = widget._text_edit.toPlainText()
        assert "Algo fue mal" in content

    def test_append_log_error(self, widget: LogTerminalWidget) -> None:
        """append_log añade texto al QTextEdit para un mensaje ERROR."""
        widget.append_log("12:00:00  [   ERROR]  core.db: Error de base de datos")
        content = widget._text_edit.toPlainText()
        assert "Error de base de datos" in content

    def test_append_log_critical(self, widget: LogTerminalWidget) -> None:
        """append_log añade texto al QTextEdit para un mensaje CRITICAL."""
        widget.append_log("12:00:00  [CRITICAL]  app: Fallo crítico del sistema")
        content = widget._text_edit.toPlainText()
        assert "Fallo crítico del sistema" in content

    def test_append_multiple_lines(self, widget: LogTerminalWidget) -> None:
        """append_log acumula múltiples líneas correctamente."""
        widget.append_log("Línea 1 WARNING")
        widget.append_log("Línea 2 ERROR")
        widget.append_log("Línea 3 CRITICAL")
        content = widget._text_edit.toPlainText()
        assert "Línea 1" in content
        assert "Línea 2" in content
        assert "Línea 3" in content

    def test_clear_empties_text(self, widget: LogTerminalWidget) -> None:
        """El botón Limpiar vacía el contenido visible del panel."""
        widget.append_log("12:00:00  [ WARNING]  test: Texto de prueba WARNING")
        # Se verifica que hay algún contenido HTML (insertHtml deja texto en el documento)
        document = widget._text_edit.document()
        assert document is not None
        assert document.characterCount() > 1
        widget._on_clear()
        assert widget._text_edit.toPlainText().strip() == ""

    def test_export_writes_file(self, widget: LogTerminalWidget) -> None:
        """_on_export escribe el contenido del panel en un archivo .txt."""
        widget.append_log("12:00:00  [ WARNING]  test: Mensaje exportado")

        with tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False, mode="w", encoding="utf-8"
        ) as tmp:
            tmp_path = tmp.name

        try:
            with (
                patch("ui.widgets.log_terminal_widget.QFileDialog.getSaveFileName",
                      return_value=(tmp_path, "Archivos de texto (*.txt)")),
                patch("ui.widgets.log_terminal_widget.QMessageBox.information"),
            ):
                widget._on_export()

            with open(tmp_path, encoding="utf-8") as f:
                content = f.read()

            assert "Mensaje exportado" in content
            assert "hipatia" in content.lower() or "Hipatia" in content
        finally:
            os.unlink(tmp_path)

    def test_export_cancelled_noop(self, widget: LogTerminalWidget) -> None:
        """_on_export no hace nada si el usuario cancela el diálogo (ruta vacía)."""
        widget.append_log("12:00:00  [ WARNING]  test: No exportado")
        with patch("ui.widgets.log_terminal_widget.QFileDialog.getSaveFileName",
                   return_value=("", "")):
            widget._on_export()  # no debe lanzar excepción
        
        assert "No exportado" in widget._text_edit.toPlainText(), "El contenido no debe haberse borrado"

    def test_connect_handler(self, widget: LogTerminalWidget) -> None:
        """connect_to_widget() conecta la señal del QtLogHandler al widget y reproduce el buffer."""
        import logging
        from core.qt_log_handler import QtLogHandler

        handler = QtLogHandler()
        # Simular un mensaje en buffer (antes de conectar)
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="Señal conectada OK",
            args=(),
            exc_info=None,
        )
        handler.emit(record)  # va al buffer (no hay widget conectado)
        assert widget._text_edit.toPlainText() == ""  # sin widget aún

        # Conectar — debe reproducir el buffer
        handler.connect_to_widget(widget.append_log)

        content = widget._text_edit.toHtml()
        assert "Señal conectada OK" in content
