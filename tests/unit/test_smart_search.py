# -*- coding: utf-8 -*-
"""Tests unitarios para SmartSearchWidget (búsqueda, debounce, resultados)."""
import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QListWidgetItem
from PyQt6.QtCore import Qt

from ui.widgets.reports.smart_search import SmartSearchWidget

pytestmark = pytest.mark.unit


def _make_result(tipo="producto", codigo="P1", descripcion="Prod 1"):
    """Helper para crear DTOs de resultado mock."""
    dto = MagicMock(spec=['tipo', 'codigo', 'descripcion'])
    dto.tipo = tipo
    dto.codigo = codigo
    dto.descripcion = descripcion
    return dto


class TestSmartSearchWidget:
    """Tests unitarios para SmartSearchWidget."""

    @pytest.fixture
    def widget(self, qtbot):
        """Fixture para SmartSearchWidget."""
        model = MagicMock(spec=['search_reports_data'])
        w = SmartSearchWidget(app_model=model)
        qtbot.addWidget(w)
        return w

    def test_init(self, widget):
        """Widget se inicializa con lista oculta."""
        assert widget.results_list.isHidden()
        assert widget.search_input.text() == ""

    def test_on_text_changed_short(self, widget, qtbot):
        """Texto corto (<2 chars) oculta resultados y emite search_cleared si vacío."""
        with qtbot.waitSignal(widget.search_cleared, timeout=1000):
            widget._on_text_changed("")
        assert widget.results_list.isHidden()

    def test_on_text_changed_valid(self, widget):
        """Texto válido (>=2 chars) inicia debounce."""
        widget._on_text_changed("ab")
        assert widget.debounce_timer.isActive()

    def test_perform_search_empty(self, widget):
        """Búsqueda vacía no hace nada."""
        widget.search_input.clear()
        widget._perform_search()
        assert widget.app_model.search_reports_data.call_count == 0
        assert not widget.app_model.search_reports_data.called

    def test_perform_search_no_model(self, qtbot):
        """Sin modelo, búsqueda logea warning."""
        w = SmartSearchWidget(app_model=None)
        qtbot.addWidget(w)
        w.search_input.setText("test")
        try:
            w._perform_search()
        except Exception:
            pytest.fail("_perform_search no debería propagar excepciones sin modelo")
        assert w.app_model is None

    def test_perform_search_success(self, widget):
        """Búsqueda exitosa actualiza resultados."""
        results = [_make_result()]
        widget.app_model.search_reports_data.return_value = results
        widget.search_input.setText("test")
        widget._perform_search()
        assert widget.results_list.count() == 1
        assert not widget.results_list.isHidden()

    def test_perform_search_prefers_report_service(self, qtbot):
        """Si hay ReportService inyectado, no se usa app_model para la búsqueda."""
        model = MagicMock(spec=["search_reports_data"])
        rs = MagicMock(spec=["search_reports_data"])
        rs.search_reports_data.return_value = [_make_result(codigo="RS")]
        w = SmartSearchWidget(app_model=model, report_service=rs)
        qtbot.addWidget(w)
        w.search_input.setText("ab")
        w._perform_search()
        rs.search_reports_data.assert_called_once_with("ab")
        model.search_reports_data.assert_not_called()

    def test_perform_search_error(self, widget):
        """Error en búsqueda no crashea."""
        widget.app_model.search_reports_data.side_effect = Exception("DB Error")
        widget.search_input.setText("test")
        try:
            widget._perform_search()
        except Exception:
            pytest.fail("_perform_search no debería propagar excepciones de BD")
        assert widget.results_list is not None  # widget sigue válido

    def test_update_results_list_empty(self, widget):
        """Lista vacía oculta resultados."""
        widget._update_results_list([])
        assert widget.results_list.isHidden()

    def test_update_results_list_with_data(self, widget):
        """Lista con datos muestra items."""
        results = [_make_result(tipo="producto"), _make_result(tipo="fabricacion", codigo="F1")]
        widget._update_results_list(results)
        assert widget.results_list.count() == 2
        assert not widget.results_list.isHidden()

    def test_on_item_clicked(self, widget, qtbot):
        """Click en item emite result_selected."""
        dto = _make_result(tipo="producto", codigo="P1")
        item = QListWidgetItem("Test")
        item.setData(Qt.ItemDataRole.UserRole, dto)
        widget.results_list.addItem(item)

        with qtbot.waitSignal(widget.result_selected, timeout=1000) as blocker:
            widget._on_item_clicked(item)
        assert blocker.args == ["producto", "P1"]

    def test_on_item_clicked_no_dto(self, widget):
        """Click en item sin DTO no hace nada."""
        item = QListWidgetItem("Test")
        try:
            widget._on_item_clicked(item)
        except Exception:
            pytest.fail("_on_item_clicked no debería propagar excepciones sin DTO")
        assert widget.results_list is not None

    def test_clear_search(self, widget, qtbot):
        """clear_search limpia todo."""
        widget.search_input.setText("test")
        widget.results_list.addItem(QListWidgetItem("item"))
        widget.results_list.show()

        with qtbot.waitSignal(widget.search_cleared, timeout=1000):
            widget.clear_search()
        assert widget.search_input.text() == ""
        assert widget.results_list.count() == 0
        assert widget.results_list.isHidden()

    def test_set_controller(self, widget):
        """set_controller actualiza app_model."""
        ctrl = MagicMock(spec=["model"])
        ctrl.model = MagicMock(spec=[])
        widget.set_controller(ctrl)
        assert widget.app_model is ctrl.model
