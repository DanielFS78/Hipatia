"""
Nombre del Módulo: test_reports_widgets
Descripcion: Tests unitarios para los cuatro widgets del módulo de reportes:
             StatCard (tarjeta de estadística), OrderListWidget (lista de órdenes
             de fabricación), SmartSearchWidget (búsqueda con debounce) y
             ReportsChartsWidget (contenedor de gráficas de análisis).
             Verifica inicialización, estado interno, señales y comportamiento
             sin controlador.

Decisión de mocking: QWidget/QFrame con MagicMock donde hace falta; ReportService
con create_autospec(ReportService, instance=True) según testing_fixtures_y_mocks.
"""
import pytest
from unittest.mock import MagicMock, create_autospec

from core.services.report_service import ReportService

pytestmark = pytest.mark.unit


# ─── StatCard ────────────────────────────────────────────────────────────────

class TestStatCard:
    """Verifica StatCard: inicialización con y sin subtítulo, color personalizado y ancho mínimo."""
    @pytest.fixture
    def card(self, qapp):
        from ui.widgets.reports.charts_container import StatCard
        return StatCard(title="Tiempo Promedio", value="5.2 min", subtitle="por unidad")

    def test_instantiation(self, card):
        assert card is not None

    def test_instantiation_without_subtitle(self, qapp):
        from ui.widgets.reports.charts_container import StatCard
        c = StatCard(title="Total", value="100")
        assert c is not None

    def test_instantiation_with_custom_color(self, qapp):
        from ui.widgets.reports.charts_container import StatCard
        c = StatCard(title="Mejor", value="3.1 min", color="#16a34a")
        assert c is not None

    def test_minimum_width(self, card):
        assert card.minimumWidth() == 150


# ─── OrderListWidget ─────────────────────────────────────────────────────────

class TestOrderListWidget:
    """Verifica OrderListWidget: estado inicial, carga de órdenes, clear() y señal order_selected."""
    @pytest.fixture
    def widget(self, qapp):
        from ui.widgets.reports.order_list import OrderListWidget
        return OrderListWidget()

    def test_instantiation(self, widget):
        assert widget is not None

    def test_instantiation_with_report_service(self, qapp):
        from ui.widgets.reports.order_list import OrderListWidget
        rs = create_autospec(ReportService, instance=True)
        w = OrderListWidget(report_service=rs)
        assert w is not None

    def test_has_title_label(self, widget):
        assert widget.title_label is not None

    def test_has_status_label(self, widget):
        assert widget.status_label is not None

    def test_initial_current_producto_is_none(self, widget):
        assert widget._current_producto is None

    def test_initial_order_cards_empty(self, widget):
        assert len(widget._order_cards) == 0

    def test_set_report_service_order_list(self, widget):
        rs = create_autospec(ReportService, instance=True)
        widget.set_report_service(rs)
        assert widget._report_service is rs

    def test_clear_resets_state(self, widget):
        widget._current_producto = "PROD-01"
        widget.clear()
        assert widget._current_producto is None

    def test_clear_resets_title(self, widget):
        widget.title_label.setText("Algo")
        widget.clear()
        assert "Órdenes" in widget.title_label.text()

    def test_load_orders_no_controller(self, widget):
        # Should not raise even without controller
        widget.load_orders_for_product("PROD-01")
        assert widget._current_producto == "PROD-01"

    def test_load_orders_with_report_service_none(self, widget):
        widget.set_report_service(None)
        widget.load_orders_for_product("PROD-01")
        assert widget._current_producto == "PROD-01"

    def test_load_orders_updates_title(self, widget):
        widget.load_orders_for_product("PROD-99")
        assert "PROD-99" in widget.title_label.text()

    def test_select_order_marks_card_selected(self, widget):
        dto = MagicMock(spec=["orden_fabricacion", "estado", "fecha_inicio", "cantidad_unidades", "tiempo_total_segundos", "incidencias_count"])
        dto.orden_fabricacion = "OF-SEL-1"
        dto.estado = "completado"
        dto.fecha_inicio = None
        dto.cantidad_unidades = 1
        dto.tiempo_total_segundos = 60
        dto.incidencias_count = 0
        widget._display_orders([dto])

        widget.select_order("OF-SEL-1")

        assert widget._selected_order == "OF-SEL-1"

    def test_order_selected_signal_exists(self, widget):
        assert hasattr(widget, "order_selected")


# ─── SmartSearchWidget ───────────────────────────────────────────────────────

class TestSmartSearchWidget:
    """Verifica SmartSearchWidget: debounce, clear_search(), _update_results_list() y señales."""
    @pytest.fixture
    def widget(self, qapp):
        from ui.widgets.reports.smart_search import SmartSearchWidget
        rs = create_autospec(ReportService, instance=True)
        return SmartSearchWidget(report_service=rs)

    def test_instantiation(self, widget):
        assert widget is not None

    def test_instantiation_no_report_service(self, qapp):
        from ui.widgets.reports.smart_search import SmartSearchWidget
        w = SmartSearchWidget(report_service=None)
        assert w is not None

    def test_has_search_input(self, widget):
        assert widget.search_input is not None

    def test_has_results_list(self, widget):
        assert widget.results_list is not None

    def test_results_list_initially_hidden(self, widget):
        assert widget.results_list.isVisible() is False

    def test_has_debounce_timer(self, widget):
        assert widget.debounce_timer is not None

    def test_result_selected_signal_exists(self, widget):
        assert hasattr(widget, "result_selected")

    def test_search_cleared_signal_exists(self, widget):
        assert hasattr(widget, "search_cleared")

    def test_clear_search_hides_results(self, widget):
        widget.results_list.show()
        widget.clear_search()
        assert widget.results_list.isVisible() is False

    def test_clear_search_clears_input(self, widget):
        widget.search_input.setText("algo")
        widget.clear_search()
        assert widget.search_input.text() == ""

    def test_short_text_hides_results(self, widget):
        widget.results_list.show()
        widget._on_text_changed("a")
        assert widget.results_list.isVisible() is False

    def test_empty_text_emits_search_cleared(self, widget):
        received = []
        widget.search_cleared.connect(lambda: received.append(True))
        widget._on_text_changed("")
        assert len(received) == 1

    def test_set_controller_updates_report_service(self, widget):
        rs = create_autospec(ReportService, instance=True)
        ctrl = MagicMock(spec=["model", "container"])
        ctrl.model = MagicMock(spec=["report_service"])
        ctrl.model.report_service = rs
        ctrl.container = MagicMock(spec=["is_registered", "resolve"])
        ctrl.container.is_registered.return_value = False
        widget.set_controller(ctrl)
        assert widget._report_service is rs

    def test_perform_search_no_service(self, qapp):
        from ui.widgets.reports.smart_search import SmartSearchWidget
        w = SmartSearchWidget(report_service=None)
        w.search_input.setText("test")
        w._perform_search()
        assert w.results_list.count() == 0

    def test_update_results_list_empty(self, widget):
        widget._update_results_list([])
        assert widget.results_list.isVisible() is False

    def test_update_results_list_with_items(self, widget):
        dto = MagicMock(spec=["tipo", "codigo", "descripcion"])
        dto.tipo = "producto"
        dto.codigo = "P1"
        dto.descripcion = "Producto 1"
        widget._update_results_list([dto])
        assert widget.results_list.count() == 1

    def test_perform_search_skips_same_query(self, widget):
        widget._report_service.search_reports_data.return_value = []
        widget.search_input.setText("ABC")
        widget._perform_search()
        widget._perform_search()
        widget._report_service.search_reports_data.assert_called_once_with("ABC")


# ─── ReportsChartsWidget ─────────────────────────────────────────────────────

class TestReportsChartsWidget:
    """Verifica ReportsChartsWidget: tabs placeholder, clear(), update_charts() sin controlador y set_controller()."""
    @pytest.fixture
    def widget(self, qapp):
        from ui.widgets.reports.charts_container import ReportsChartsWidget
        return ReportsChartsWidget()

    def test_instantiation(self, widget):
        assert widget is not None

    def test_instantiation_with_report_service(self, qapp):
        from ui.widgets.reports.charts_container import ReportsChartsWidget
        rs = create_autospec(ReportService, instance=True)
        w = ReportsChartsWidget(report_service=rs)
        assert w is not None

    def test_has_title_label(self, widget):
        assert widget.title_label is not None

    def test_has_tabs(self, widget):
        assert widget.tabs is not None

    def test_tabs_has_three_placeholder_tabs(self, widget):
        assert widget.tabs.count() == 3

    def test_initial_current_producto_is_none(self, widget):
        assert widget._current_producto is None

    def test_set_report_service_charts(self, widget):
        rs = create_autospec(ReportService, instance=True)
        widget.set_report_service(rs)
        assert widget._report_service is rs

    def test_clear_resets_title(self, widget):
        widget.title_label.setText("Algo")
        widget.clear()
        assert "Análisis" in widget.title_label.text()

    def test_clear_resets_current_producto(self, widget):
        widget._current_producto = "PROD-01"
        widget.clear()
        assert widget._current_producto is None

    def test_clear_recreates_tabs(self, widget):
        widget.clear()
        assert widget.tabs.count() == 3

    def test_update_charts_no_controller(self, widget):
        # Should not raise
        widget.update_charts("PROD-01")
        assert widget._current_producto == "PROD-01"

    def test_update_charts_updates_title(self, widget):
        widget.update_charts("PROD-99")
        assert "PROD-99" in widget.title_label.text()
