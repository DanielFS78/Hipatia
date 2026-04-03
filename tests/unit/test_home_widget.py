# -*- coding: utf-8 -*-
"""Tests unitarios para HomeWidget.

Cubre HomeWidget: inicialización, update_health_report para STABLE/WARNING/CRITICAL,
detalle de sistema y manejo de report inválido (None). Mocks con spec para report/system.
"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime

from ui.widgets.home_widget import HomeWidget

pytestmark = pytest.mark.unit


class TestHomeWidget:
    """Tests unitarios para HomeWidget."""

    @pytest.fixture
    def widget(self, qtbot):
        w = HomeWidget()
        qtbot.addWidget(w)
        return w

    def test_init(self, widget):
        """Widget se inicializa con badge y detalle vacíos."""
        assert widget._status_badge is not None
        assert widget._detail_label is not None

    def test_update_health_report_stable(self, widget):
        """update_health_report con estado STABLE muestra badge verde."""
        report = MagicMock(spec=['overall_status', 'test_results', 'system', 'generated_at'])
        report.overall_status = "STABLE"
        report.test_results = None
        report.system = MagicMock(spec=['last_backup_date', 'disk_free_gb', 'last_session_errors'])
        report.system.last_backup_date = "Hoy"
        report.system.disk_free_gb = 50.0
        report.system.last_session_errors = 0
        report.generated_at = datetime(2026, 3, 14, 16, 0)

        widget.update_health_report(report)

        assert "SISTEMA OPERATIVO" in widget._status_badge.text()
        assert "✅" in widget._status_badge.text()

    def test_update_health_report_warning(self, widget):
        """update_health_report con estado WARNING muestra badge amarillo."""
        report = MagicMock(spec=['overall_status', 'test_results', 'system', 'generated_at'])
        report.overall_status = "WARNING"
        report.test_results = None
        report.system = MagicMock(spec=['last_backup_date', 'disk_free_gb', 'last_session_errors'])
        report.system.last_backup_date = "Ayer"
        report.system.disk_free_gb = 10.0
        report.system.last_session_errors = 2
        report.generated_at = datetime(2026, 3, 14, 16, 0)

        widget.update_health_report(report)

        assert "ADVERTENCIAS DETECTADAS" in widget._status_badge.text()
        assert "⚠️" in widget._status_badge.text()

    def test_update_health_report_critical(self, widget):
        """update_health_report con estado CRITICAL muestra badge rojo."""
        report = MagicMock(spec=['overall_status', 'test_results', 'system', 'generated_at'])
        report.overall_status = "CRITICAL"
        report.test_results = None
        report.system = MagicMock(spec=['last_backup_date', 'disk_free_gb', 'last_session_errors'])
        report.system.last_backup_date = "Nunca"
        report.system.disk_free_gb = 0.5
        report.system.last_session_errors = 10
        report.generated_at = datetime(2026, 3, 14, 16, 0)

        widget.update_health_report(report)

        assert "ERRORES CRÍTICOS" in widget._status_badge.text()
        assert "❌" in widget._status_badge.text()

    def test_update_health_report_with_test_results(self, widget):
        """update_health_report muestra datos del sistema en el detail."""
        report = MagicMock(spec=['overall_status', 'test_results', 'system', 'generated_at'])
        report.overall_status = "STABLE"
        report.test_results = None
        report.system = MagicMock(spec=['last_backup_date', 'disk_free_gb', 'last_session_errors'])
        report.system.last_backup_date = "Hoy"
        report.system.disk_free_gb = 30.0
        report.system.last_session_errors = 0
        report.generated_at = datetime(2026, 3, 14, 16, 0)

        widget.update_health_report(report)

        detail = widget._detail_label.text()
        assert "30.0 GB" in detail
        assert "14/03/2026" in detail

    def test_update_health_report_errors_shown(self, widget):
        """update_health_report muestra errores de sesión anterior si > 0."""
        report = MagicMock(spec=['overall_status', 'test_results', 'system', 'generated_at'])
        report.overall_status = "WARNING"
        report.test_results = None
        report.system = MagicMock(spec=['last_backup_date', 'disk_free_gb', 'last_session_errors'])
        report.system.last_backup_date = "Hoy"
        report.system.disk_free_gb = 20.0
        report.system.last_session_errors = 5
        report.generated_at = datetime(2026, 3, 14, 16, 0)

        widget.update_health_report(report)

        assert "5" in widget._detail_label.text()

    def test_update_health_report_exception_handled(self, widget):
        """update_health_report no lanza excepción si el report es inválido."""
        try:
            widget.update_health_report(None)
        except Exception:
            pytest.fail("update_health_report no debería propagar excepciones con None")
        assert widget._status_badge is not None  # widget sigue en estado válido tras None
