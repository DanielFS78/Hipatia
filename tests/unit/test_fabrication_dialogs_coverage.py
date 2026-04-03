"""
Nombre del Módulo: test_fabrication_dialogs_coverage
Descripcion: Tests unitarios para CreateFabricacionDialog, el diálogo de creación
             de fabricaciones con asignación de preprocesos y productos. Verifica
             inicialización, validación, obtención de datos y delegación al presenter.

Decisión de mocking: CreateFabricacionDialog hereda de QDialog (PyQt6) — MagicMock()
inevitable para widgets internos. CreateFabricacionPresenter es Python puro y se
mockea con MagicMock() estándar. Los objetos Preproceso y Producto se simulan con
MagicMock() con atributos id (int), nombre y codigo explícitos porque el presenter
usa sorted() sobre el atributo id y MagicMock() no es comparable por defecto.
"""
import pytest
from unittest.mock import MagicMock, patch

pytestmark = pytest.mark.unit


def make_preproceso(nombre="Prep A", descripcion="Desc A", id=1):
    p = MagicMock(spec=["nombre", "descripcion", "id"])
    p.nombre = nombre
    p.descripcion = descripcion
    p.id = id
    return p


def make_product(codigo="PROD-01", descripcion="Producto Uno", id=1):
    p = MagicMock(spec=["codigo", "descripcion", "id"])
    p.codigo = codigo
    p.descripcion = descripcion
    p.id = id
    return p


@pytest.fixture
def dialog(qapp):
    from ui.dialogs.fabrication.create_dialog import CreateFabricacionDialog
    preps = [make_preproceso("Prep A", id=1), make_preproceso("Prep B", id=2)]
    prods = [make_product("P1", id=1), make_product("P2", id=2)]
    return CreateFabricacionDialog(preps, prods)


class TestCreateFabricacionDialogInit:
    """Verifica la inicialización del diálogo, sus widgets principales y el presenter interno."""
    def test_instantiation(self, dialog):
        assert dialog is not None

    def test_has_codigo_entry(self, dialog):
        assert dialog.codigo_entry is not None

    def test_has_descripcion_entry(self, dialog):
        assert dialog.descripcion_entry is not None

    def test_has_tabs(self, dialog):
        assert dialog.tabs is not None
        assert dialog.tabs.count() == 2

    def test_has_presenter(self, dialog):
        assert dialog.presenter is not None

    def test_window_title(self, dialog):
        assert "Fabricación" in dialog.windowTitle() or "fabricaci" in dialog.windowTitle().lower()


class TestCreateFabricacionDialogValidation:
    """Verifica validate_and_accept(): muestra warning con código vacío o inválido, acepta con código válido."""
    def test_validate_and_accept_empty_codigo_shows_warning(self, dialog):
        dialog.codigo_entry.setText("")
        with patch("PyQt6.QtWidgets.QMessageBox.warning") as mock_warn:
            dialog.validate_and_accept()
            assert mock_warn.call_count == 1

    def test_validate_and_accept_valid_codigo_accepts(self, dialog):
        dialog.codigo_entry.setText("FAB-001")
        dialog.presenter.validate = MagicMock(return_value=(True, ""))
        with patch.object(dialog, "accept") as mock_accept:
            dialog.validate_and_accept()
            assert mock_accept.call_count == 1

    def test_validate_and_accept_invalid_shows_warning(self, dialog):
        dialog.codigo_entry.setText("X")
        dialog.presenter.validate = MagicMock(return_value=(False, "Código inválido"))
        with patch("PyQt6.QtWidgets.QMessageBox.warning") as mock_warn:
            dialog.validate_and_accept()
            assert mock_warn.call_count == 1


class TestCreateFabricacionDialogGetData:
    """Verifica que get_fabricacion_data() delega al presenter y devuelve un dict."""
    def test_get_fabricacion_data_returns_dict(self, dialog):
        dialog.codigo_entry.setText("FAB-001")
        dialog.descripcion_entry.setText("Desc")
        dialog.presenter.get_fabricacion_data = MagicMock(return_value={"codigo": "FAB-001"})
        result = dialog.get_fabricacion_data()
        assert isinstance(result, dict)

    def test_get_fabricacion_data_calls_presenter(self, dialog):
        dialog.codigo_entry.setText("FAB-001")
        dialog.descripcion_entry.setText("Desc")
        dialog.presenter.get_fabricacion_data = MagicMock(return_value={})
        dialog.get_fabricacion_data()
        assert dialog.presenter.get_fabricacion_data.call_count == 1


class TestCreateFabricacionDialogAssign:
    """Verifica que los métodos de asignación/desasignación de preprocesos y productos delegan al presenter."""
    def test_assign_preproceso_calls_presenter(self, dialog):
        dialog.presenter.assign_preprocesos = MagicMock(spec=[])
        dialog.presenter.get_assigned_preprocesos = MagicMock(return_value=[])
        dialog.presenter.get_filtered_preprocesos = MagicMock(return_value=[])
        dialog._assign_preproceso()
        assert dialog.presenter.assign_preprocesos.call_count == 1

    def test_unassign_preproceso_calls_presenter(self, dialog):
        dialog.presenter.unassign_preprocesos = MagicMock(spec=[])
        dialog.presenter.get_assigned_preprocesos = MagicMock(return_value=[])
        dialog.presenter.get_filtered_preprocesos = MagicMock(return_value=[])
        dialog._unassign_preproceso()
        assert dialog.presenter.unassign_preprocesos.call_count == 1

    def test_assign_product_calls_presenter(self, dialog):
        dialog.presenter.assign_products = MagicMock(spec=[])
        dialog.presenter.get_assigned_products = MagicMock(return_value=[])
        dialog.presenter.get_filtered_products = MagicMock(return_value=[])
        dialog._assign_product()
        assert dialog.presenter.assign_products.call_count == 1

    def test_unassign_product_calls_presenter(self, dialog):
        dialog.presenter.unassign_products_by_code = MagicMock(spec=[])
        dialog.presenter.get_assigned_products = MagicMock(return_value=[])
        dialog.presenter.get_filtered_products = MagicMock(return_value=[])
        dialog._unassign_product()
        assert dialog.presenter.unassign_products_by_code.call_count == 1


class TestCreateFabricacionDialogCompatibility:
    """Verifica las propiedades de compatibilidad con la versión anterior del diálogo (sin productos)."""
    def test_search_entry_property(self, dialog):
        assert dialog.search_entry is dialog.prep_search_entry

    def test_available_list_property(self, dialog):
        assert dialog.available_list is dialog.prep_available_list

    def test_assigned_list_property(self, dialog):
        assert dialog.assigned_list is dialog.prep_assigned_list

    def test_add_button_property(self, dialog):
        assert dialog.add_button is dialog.prep_add_button

    def test_remove_button_property(self, dialog):
        assert dialog.remove_button is dialog.prep_remove_button
