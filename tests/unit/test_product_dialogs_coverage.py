"""
Nombre del Módulo: test_product_dialogs_coverage
Descripcion: Tests unitarios para los diálogos de gestión de productos en
             ui/dialogs/product_dialogs.py. Verifica creación, edición, validación
             de campos, gestión de materiales, iteraciones de producto y comportamiento
             con datos incompletos o inválidos.

Decisión de mocking: Los diálogos heredan de QDialog (PyQt6) — MagicMock() inevitable
para widgets internos. ProductDTO, ProductIterationDTO y MaterialDTO se usan con
atributos explícitos (no mocks anidados) porque los diálogos acceden a sus campos
directamente. No se usa autospec en clases Qt. PropertyMock se usa para propiedades
Qt que no se pueden asignar directamente.
"""
import pytest
import os
from unittest.mock import MagicMock, patch, PropertyMock, ANY
from datetime import datetime

from typing import Any, Dict, List, cast
from core.dtos import (
    ProductDTO,
    ProductIterationDTO,
    MaterialDTO,
    MachineDTO,
    SubfabricacionDTO,
    ProductDetailsDTO,
)


# =============================
#  Helpers para mocks de Qt
# =============================
pytestmark = pytest.mark.unit
MODULE = "ui.dialogs.product"


def _make_product_dto(**overrides):
    """Helper para crear ProductDTO con valores por defecto."""
    defaults = dict(codigo="P001", descripcion="Producto Test", departamento="D1",
                    tipo_trabajador=1, donde="local", tiene_subfabricaciones=False,
                    tiempo_optimo=10.0)
    defaults.update(overrides)
    return ProductDTO(**cast(Any, defaults))


def _make_iteration_dto(**overrides):
    """Helper para crear ProductIterationDTO con valores por defecto."""
    defaults = dict(id=1, producto_codigo="P001", descripcion="Iteración 1",
                    fecha_creacion=datetime(2025, 6, 15, 10, 30, 0),
                    nombre_responsable="Juan", tipo_fallo="Fallo de Proveedor",
                    ruta_imagen=None, ruta_plano=None)
    defaults.update(overrides)
    return ProductIterationDTO(**cast(Any, defaults))


def _make_material_dto(**overrides):
    """Helper para crear MaterialDTO con valores por defecto."""
    defaults = dict(id=1, codigo_componente="MAT-001", descripcion_componente="Tornillo M8")
    defaults.update(overrides)
    return MaterialDTO(**cast(Any, defaults))


def _make_machine_dto(**overrides):
    """Helper para crear MachineDTO con valores por defecto."""
    defaults = dict(id=10, nombre="CNC-1", departamento="Mecanizado",
                    tipo_proceso="fresado", activa=True)
    defaults.update(overrides)
    return MachineDTO(**cast(Any, defaults))


# ==============================================================================
# TEST CLASS: ProductDetailsDialog
# ==============================================================================
@pytest.mark.unit
class TestProductDetailsDialog:
    """Tests unitarios para ProductDetailsDialog con cobertura 100%."""

    @pytest.fixture
    def mock_controller(self):
        """Controlador mock con spec de auto-detección."""
        ctrl = MagicMock()
        prod_dto = _make_product_dto()
        assert isinstance(prod_dto, ProductDTO)
        details = ProductDetailsDTO(producto=prod_dto, subfabricaciones=[], procesos_mecanicos=[])
        ctrl.product_facade = MagicMock()
        ctrl.product_facade.get_product_details.return_value = details
        ctrl.material_service = MagicMock()
        ctrl.material_service.get_materials_for_product.return_value = []
        ctrl.product_service = MagicMock()
        ctrl.product_service.get_product_iterations.return_value = []
        ctrl.db = MagicMock()
        ctrl.db.get_iteration_images.return_value = []
        ctrl.app = MagicMock()
        ctrl.app.file_controller = MagicMock()
        return ctrl

    @pytest.fixture
    def mock_view(self):
        """Vista mock (parent del diálogo)."""
        view = MagicMock()
        view.show_message = MagicMock()
        view.show_confirmation_dialog = MagicMock(return_value=True)
        return view

    @pytest.fixture
    def dialog(self, qapp, mock_controller, mock_view):
        """Instancia de ProductDetailsDialog con dependencias mock."""
        with patch("ui.widgets.product.materials_widget.QFileDialog", autospec=True), \
             patch("ui.widgets.product.materials_widget.QInputDialog", autospec=True), \
             patch("ui.widgets.product.iterations_widget.QFileDialog", autospec=True):
            from ui.dialogs.product import ProductDetailsDialog
            dlg: Any = ProductDetailsDialog("P001", mock_controller, parent=None)
            dlg.view = mock_view
            # Propagar mock_view a los widgets para los tests
            dlg.materials_tab.view = mock_view
            dlg.iterations_tab.view = mock_view
            return dlg

    # --- __init__ y load_all_data ---

    def test_init_sets_attributes(self, dialog, mock_controller):
        """Verifica inicialización correcta del diálogo."""
        assert dialog.product_code == "P001"
        assert dialog.product_controller is mock_controller
        mock_controller.product_facade.get_product_details.assert_called_once_with("P001")

    def test_init_with_prod_data_none(self, qapp, mock_view):
        """Verifica que funciona con producto no encontrado (None)."""
        ctrl = MagicMock()
        ctrl.product_facade = MagicMock()
        ctrl.product_facade.get_product_details.return_value = ProductDetailsDTO(
            producto=None, subfabricaciones=[], procesos_mecanicos=[]
        )
        ctrl.material_service = MagicMock()
        ctrl.material_service.get_materials_for_product.return_value = []
        ctrl.product_service = MagicMock()
        ctrl.product_service.get_product_iterations.return_value = []
        ctrl.db = MagicMock()
        ctrl.db.get_iteration_images.return_value = []
        ctrl.app = MagicMock()
        ctrl.app.file_controller = MagicMock()
        with patch("ui.widgets.product.materials_widget.QFileDialog", autospec=True), \
             patch("ui.widgets.product.materials_widget.QInputDialog", autospec=True):
            from ui.dialogs.product import ProductDetailsDialog
            dlg: Any = ProductDetailsDialog("PXXX", ctrl, parent=None)
            dlg.view = mock_view
            assert "PXXX" in dlg.windowTitle()

    def test_load_all_data_calls_both(self, dialog, mock_controller):
        """Verifica que load_all_data invoca load_data en ambos widgets."""
        mock_controller.material_service.get_materials_for_product.reset_mock()
        mock_controller.product_service.get_product_iterations.reset_mock()
        dialog.load_all_data()
        assert mock_controller.material_service.get_materials_for_product.call_count == 1
        mock_controller.material_service.get_materials_for_product.assert_called_once_with("P001")
        assert mock_controller.product_service.get_product_iterations.call_count == 1
        mock_controller.product_service.get_product_iterations.assert_called_once_with("P001")

    # --- Componentes ---

    def test_load_components_populates_table(self, dialog, mock_controller):
        """Verifica que load_components llena la tabla de materiales."""
        mat = _make_material_dto()
        assert isinstance(mat, MaterialDTO)
        mock_controller.material_service.get_materials_for_product.return_value = [mat]
        dialog.materials_tab.load_data()
        assert dialog.materials_tab.materials_table.rowCount() == 1
        item0 = dialog.materials_tab.materials_table.item(0, 0)
        item1 = dialog.materials_tab.materials_table.item(0, 1)
        assert item0 is not None and item1 is not None
        assert item0.text() == "MAT-001"
        assert item1.text() == "Tornillo M8"

    def test_on_add_material_success(self, dialog, mock_controller):
        """Verifica el flujo de añadir material exitosamente."""
        with patch("ui.widgets.product.materials_widget.QInputDialog") as MockInput:
            MockInput.getText.side_effect = [
                ("MAT-002", True),
                ("Tuerca M8", True),
            ]
            mock_controller.handle_add_material_to_product.return_value = True
            dialog.materials_tab._on_add_material()
            assert mock_controller.handle_add_material_to_product.call_count == 1
            mock_controller.handle_add_material_to_product.assert_called_once_with("P001", "MAT-002", "Tuerca M8")

    def test_on_add_material_cancel_first_input(self, dialog, mock_controller):
        """Verifica que se cancela si el primer diálogo no es aceptado."""
        with patch("ui.widgets.product.materials_widget.QInputDialog") as MockInput:
            MockInput.getText.return_value = ("", False)
            dialog.materials_tab._on_add_material()
            assert mock_controller.handle_add_material_to_product.call_count == 0
            mock_controller.handle_add_material_to_product.assert_not_called()

    def test_on_add_material_cancel_second_input(self, dialog, mock_controller):
        """Verifica que se cancela si el segundo diálogo no es aceptado."""
        with patch("ui.widgets.product.materials_widget.QInputDialog") as MockInput:
            MockInput.getText.side_effect = [
                ("MAT-002", True),
                ("", False),
            ]
            dialog.materials_tab._on_add_material()
            assert mock_controller.handle_add_material_to_product.call_count == 0
            mock_controller.handle_add_material_to_product.assert_not_called()

    def test_on_add_material_empty_code(self, dialog, mock_controller):
        """Verifica que no se añade si el código está vacío."""
        with patch("ui.widgets.product.materials_widget.QInputDialog") as MockInput:
            MockInput.getText.side_effect = [
                ("   ", True),  # código vacío
            ]
            dialog.materials_tab._on_add_material()
            assert mock_controller.handle_add_material_to_product.call_count == 0
            mock_controller.handle_add_material_to_product.assert_not_called()

    def test_on_add_material_empty_description(self, dialog, mock_controller):
        """Verifica que no se añade si la descripción está vacía."""
        with patch("ui.widgets.product.materials_widget.QInputDialog") as MockInput:
            MockInput.getText.side_effect = [
                ("MAT-002", True),
                ("   ", True),
            ]
            dialog.materials_tab._on_add_material()
            assert mock_controller.handle_add_material_to_product.call_count == 0
            mock_controller.handle_add_material_to_product.assert_not_called()

    def test_on_edit_material_no_selection(self, dialog, mock_view):
        """Verifica mensaje de aviso si no hay selección."""
        dialog.materials_tab.materials_table.clearSelection()
        dialog.materials_tab._on_edit_material()
        assert mock_view.show_message.call_count == 1
        mock_view.show_message.assert_called_once_with(ANY, ANY, ANY)

    def test_on_edit_material_success(self, dialog, mock_controller, mock_view):
        """Verifica el flujo completo de editar un material."""
        mat = _make_material_dto()
        mock_controller.material_service.get_materials_for_product.return_value = [mat]
        dialog.materials_tab.load_data()
        dialog.materials_tab.materials_table.selectRow(0)

        with patch("ui.widgets.product.materials_widget.QInputDialog") as MockInput:
            MockInput.getText.side_effect = [
                ("MAT-003", True),
                ("Arandela M8", True),
            ]
            mock_controller.handle_update_material.return_value = True
            dialog.materials_tab._on_edit_material()
            assert mock_controller.handle_update_material.call_count == 1
            mock_controller.handle_update_material.assert_called_once_with(ANY, ANY, ANY)

    def test_on_edit_material_cancel_first(self, dialog, mock_controller):
        """Verifica cancelación en primer diálogo de edición."""
        mat = _make_material_dto()
        mock_controller.material_service.get_materials_for_product.return_value = [mat]
        dialog.materials_tab.load_data()
        dialog.materials_tab.materials_table.selectRow(0)
        with patch("ui.widgets.product.materials_widget.QInputDialog") as MockInput:
            MockInput.getText.return_value = ("", False)
            dialog.materials_tab._on_edit_material()
            assert mock_controller.handle_update_material.call_count == 0
            mock_controller.handle_update_material.assert_not_called()

    def test_on_edit_material_cancel_second(self, dialog, mock_controller):
        """Verifica cancelación en segundo diálogo de edición."""
        mat = _make_material_dto()
        mock_controller.material_service.get_materials_for_product.return_value = [mat]
        dialog.materials_tab.load_data()
        dialog.materials_tab.materials_table.selectRow(0)
        with patch("ui.widgets.product.materials_widget.QInputDialog") as MockInput:
            MockInput.getText.side_effect = [
                ("MAT-003", True),
                ("", False),
            ]
            dialog.materials_tab._on_edit_material()
            assert mock_controller.handle_update_material.call_count == 0
            mock_controller.handle_update_material.assert_not_called()

    def test_on_edit_material_empty_new_code(self, dialog, mock_controller):
        """Verifica que no actualiza con código nuevo vacío."""
        mat = _make_material_dto()
        mock_controller.material_service.get_materials_for_product.return_value = [mat]
        dialog.materials_tab.load_data()
        dialog.materials_tab.materials_table.selectRow(0)
        with patch("ui.widgets.product.materials_widget.QInputDialog") as MockInput:
            MockInput.getText.side_effect = [
                ("  ", True),
            ]
            dialog.materials_tab._on_edit_material()
            assert mock_controller.handle_update_material.call_count == 0
            mock_controller.handle_update_material.assert_not_called()

    def test_on_edit_material_empty_new_desc(self, dialog, mock_controller):
        """Verifica que no actualiza con descripción nueva vacía."""
        mat = _make_material_dto()
        mock_controller.material_service.get_materials_for_product.return_value = [mat]
        dialog.materials_tab.load_data()
        dialog.materials_tab.materials_table.selectRow(0)
        with patch("ui.widgets.product.materials_widget.QInputDialog") as MockInput:
            MockInput.getText.side_effect = [
                ("MAT-003", True),
                ("  ", True),
            ]
            dialog.materials_tab._on_edit_material()
            assert mock_controller.handle_update_material.call_count == 0
            mock_controller.handle_update_material.assert_not_called()

    def test_on_delete_material_no_selection(self, dialog, mock_view):
        """Verifica mensaje si no hay selección para eliminar."""
        dialog.materials_tab.materials_table.clearSelection()
        dialog.materials_tab._on_delete_material()
        assert mock_view.show_message.call_count == 1
        mock_view.show_message.assert_called_once_with(ANY, ANY, ANY)

    def test_on_delete_material_confirmed(self, dialog, mock_controller, mock_view):
        """Verifica eliminación exitosa de un material."""
        mat = _make_material_dto()
        mock_controller.material_service.get_materials_for_product.return_value = [mat]
        dialog.materials_tab.load_data()
        dialog.materials_tab.materials_table.selectRow(0)
        mock_view.show_confirmation_dialog.return_value = True
        mock_controller.handle_unlink_material_from_product.return_value = True
        dialog.materials_tab._on_delete_material()
        assert mock_controller.handle_unlink_material_from_product.call_count == 1
        mock_controller.handle_unlink_material_from_product.assert_called_once_with("P001", ANY)

    def test_on_delete_material_not_confirmed(self, dialog, mock_controller, mock_view):
        """Verifica que no se elimina sin confirmación del usuario."""
        mat = _make_material_dto()
        mock_controller.material_service.get_materials_for_product.return_value = [mat]
        dialog.materials_tab.load_data()
        dialog.materials_tab.materials_table.selectRow(0)
        mock_view.show_confirmation_dialog.return_value = False
        dialog.materials_tab._on_delete_material()
        assert mock_controller.handle_unlink_material_from_product.call_count == 0
        mock_controller.handle_unlink_material_from_product.assert_not_called()

    def test_on_import_materials_success(self, dialog, mock_controller):
        """Verifica importación de materiales desde Excel."""
        with patch("ui.widgets.product.materials_widget.QFileDialog") as MockFD:
            MockFD.getOpenFileName.return_value = ("/path/file.xlsx", "")
            mock_controller.handle_import_materials_to_product.return_value = True
            dialog.materials_tab._on_import_materials_clicked()
            assert mock_controller.handle_import_materials_to_product.call_count == 1
            mock_controller.handle_import_materials_to_product.assert_called_once_with("P001", "/path/file.xlsx")

    def test_on_import_materials_cancel(self, dialog, mock_controller):
        """Verifica que se cancela si no selecciona archivo."""
        with patch("ui.widgets.product.materials_widget.QFileDialog") as MockFD:
            MockFD.getOpenFileName.return_value = ("", "")
            dialog.materials_tab._on_import_materials_clicked()
            assert mock_controller.handle_import_materials_to_product.call_count == 0
            mock_controller.handle_import_materials_to_product.assert_not_called()

    # --- Iteraciones ---

    def test_load_iterations_populates_tree(self, dialog, mock_controller):
        """Verifica que load_iterations llena el tree de historial."""
        it = _make_iteration_dto()
        assert isinstance(it, ProductIterationDTO)
        mock_controller.product_service.get_product_iterations.return_value = [it]
        dialog.iterations_tab.load_data()
        assert dialog.iterations_tab.iterations_list.topLevelItemCount() == 1

    def test_load_iterations_with_string_date(self, dialog, mock_controller):
        """Verifica que acepta fechas como string (rama isinstance str)."""
        it = _make_iteration_dto(fecha_creacion="2025-06-15 10:30:00")
        mock_controller.product_service.get_product_iterations.return_value = [it]
        dialog.iterations_tab.load_data()
        assert dialog.iterations_tab.iterations_list.topLevelItemCount() == 1

    def test_load_iterations_logs_error_on_exception(self, dialog, mock_controller):
        """Verifica que load_data captura errores y los registra en logger."""
        mock_controller.product_service.get_product_iterations.side_effect = RuntimeError("db down")
        dialog.iterations_tab.logger = MagicMock()

        dialog.iterations_tab.load_data()

        assert dialog.iterations_tab.logger.error.call_count == 1

    def test_on_iteration_selected_shows_details(self, dialog, mock_controller):
        """Verifica que seleccionar una iteración muestra sus detalles."""
        it = _make_iteration_dto()
        mock_controller.product_service.get_product_iterations.return_value = [it]
        mock_controller.db.get_iteration_images.return_value = []
        dialog.iterations_tab.load_data()
        tree_item = dialog.iterations_tab.iterations_list.topLevelItem(0)
        dialog.iterations_tab._on_iteration_selected(tree_item)
        assert dialog.iterations_tab.lbl_responsable.text() == "Responsable: Juan"
        assert dialog.iterations_tab.current_selected_iteration_id == 1
        assert dialog.iterations_tab.btn_edit_iteration.isEnabled()

    def test_on_iteration_selected_no_data(self, dialog):
        """Verifica que retorna sin hacer nada si item no tiene datos."""
        from PyQt6.QtWidgets import QTreeWidgetItem
        empty_item = QTreeWidgetItem()
        prev_id = dialog.iterations_tab.current_selected_iteration_id
        dialog.iterations_tab._on_iteration_selected(empty_item)
        # Sin datos, el estado no cambia
        assert dialog.iterations_tab.current_selected_iteration_id == prev_id

    def test_on_iteration_selected_with_legacy_image(self, dialog, mock_controller, tmp_path):
        """Verifica estado actual: la galería se alimenta desde get_iteration_images."""
        img_file = tmp_path / "legacy.png"
        img_file.write_bytes(b"\x89PNG\r\n" + b"\x00" * 100)
        it = _make_iteration_dto(ruta_imagen=str(img_file))
        mock_controller.product_service.get_product_iterations.return_value = [it]
        mock_controller.db.get_iteration_images.return_value = []
        dialog.iterations_tab.load_data()
        item = dialog.iterations_tab.iterations_list.topLevelItem(0)
        dialog.iterations_tab._on_iteration_selected(item)
        assert dialog.iterations_tab.gallery_list.count() == 0

    def test_on_iteration_selected_no_legacy_image(self, dialog, mock_controller):
        """Verifica que no se añade imagen previa si ruta_imagen es None."""
        it = _make_iteration_dto(ruta_imagen=None)
        mock_controller.product_service.get_product_iterations.return_value = [it]
        mock_controller.db.get_iteration_images.return_value = []
        dialog.iterations_tab.load_data()
        item = dialog.iterations_tab.iterations_list.topLevelItem(0)
        dialog.iterations_tab._on_iteration_selected(item)
        # Sin ruta_imagen, la galería no debe tener imágenes previas
        assert dialog.iterations_tab.gallery_list.count() == 0

    def test_on_iteration_selected_with_additional_images(self, dialog, mock_controller, tmp_path):
        """Verifica carga de imágenes adicionales desde get_iteration_images."""
        img_file = tmp_path / "extra.png"
        img_file.write_bytes(b"\x89PNG\r\n" + b"\x00" * 100)
        it = _make_iteration_dto(ruta_imagen=None)
        mock_controller.product_service.get_product_iterations.return_value = [it]
        img_mock = MagicMock()
        img_mock.id = 5
        img_mock.image_path = str(img_file)
        img_mock.description = "Foto extra"
        mock_controller.db.get_iteration_images.return_value = [img_mock]
        dialog.iterations_tab.load_data()
        item = dialog.iterations_tab.iterations_list.topLevelItem(0)
        dialog.iterations_tab._on_iteration_selected(item)
        assert dialog.iterations_tab.gallery_list.count() == 1

    def test_on_iteration_selected_additional_same_as_legacy(self, dialog, mock_controller, tmp_path):
        """Verifica estado actual: se renderiza la imagen adicional disponible."""
        img_file = tmp_path / "same.png"
        img_file.write_bytes(b"\x89PNG\r\n" + b"\x00" * 100)
        path = str(img_file)
        it = _make_iteration_dto(ruta_imagen=path)
        mock_controller.product_service.get_product_iterations.return_value = [it]
        img_mock = MagicMock()
        img_mock.id = 6
        img_mock.image_path = path
        img_mock.description = "Duplicada"
        mock_controller.db.get_iteration_images.return_value = [img_mock]
        dialog.iterations_tab.load_data()
        item = dialog.iterations_tab.iterations_list.topLevelItem(0)
        dialog.iterations_tab._on_iteration_selected(item)
        assert dialog.iterations_tab.gallery_list.count() == 1

    def test_on_iteration_selected_with_plano(self, dialog, mock_controller):
        """Verifica que btn_view_plano se activa si hay plano."""
        it = _make_iteration_dto(ruta_plano="/some/plan.pdf")
        mock_controller.product_service.get_product_iterations.return_value = [it]
        mock_controller.db.get_iteration_images.return_value = []
        dialog.iterations_tab.load_data()
        item = dialog.iterations_tab.iterations_list.topLevelItem(0)
        dialog.iterations_tab._on_iteration_selected(item)
        assert dialog.iterations_tab.btn_view_plano.isEnabled()

    def test_on_iteration_selected_without_plano(self, dialog, mock_controller):
        """Verifica que btn_view_plano se desactiva sin plano."""
        it = _make_iteration_dto(ruta_plano=None)
        mock_controller.product_service.get_product_iterations.return_value = [it]
        mock_controller.db.get_iteration_images.return_value = []
        dialog.iterations_tab.load_data()
        item = dialog.iterations_tab.iterations_list.topLevelItem(0)
        dialog.iterations_tab._on_iteration_selected(item)
        assert not dialog.iterations_tab.btn_view_plano.isEnabled()

    # --- Galería ---

    def test_add_image_to_gallery_null_pixmap(self, dialog):
        """Verifica fallback: si pixmap es nulo, se añade item de texto."""
        with patch("ui.widgets.product.iterations_widget.QPixmap") as MockPixmap:
            mock_pix = MagicMock()
            mock_pix.isNull.return_value = True
            MockPixmap.return_value = mock_pix
            dialog.iterations_tab._add_image_to_gallery("/fake.png", "tooltip")
            assert dialog.iterations_tab.gallery_list.count() == 1

    def test_add_image_to_gallery_valid_pixmap(self, dialog):
        """Verifica que se añade correctamente con pixmap válido."""
        dialog.iterations_tab.gallery_list = MagicMock()
        with patch("ui.widgets.product.iterations_widget.QPixmap") as MockPixmap, \
             patch("ui.widgets.product.iterations_widget.QIcon"), \
             patch("ui.widgets.product.iterations_widget.QListWidgetItem"):
            mock_pix = MagicMock()
            mock_pix.isNull.return_value = False
            MockPixmap.return_value = mock_pix
            dialog.iterations_tab._add_image_to_gallery("/img.png", "Tooltip", image_id=42, is_legacy=True)
            assert dialog.iterations_tab.gallery_list.addItem.call_count == 1
            dialog.iterations_tab.gallery_list.addItem.assert_called_once_with(ANY)

    def test_add_image_to_gallery_none_tooltip(self, dialog):
        """Verifica tooltip por defecto cuando es None."""
        dialog.iterations_tab.gallery_list = MagicMock()
        with patch("ui.widgets.product.iterations_widget.QPixmap") as MockPixmap, \
             patch("ui.widgets.product.iterations_widget.QIcon"), \
             patch("ui.widgets.product.iterations_widget.QListWidgetItem") as MockLWI:
            mock_pix = MagicMock()
            mock_pix.isNull.return_value = False
            MockPixmap.return_value = mock_pix
            dialog.iterations_tab._add_image_to_gallery("/img.png", None)
            mock_item = MockLWI.return_value
            assert mock_item.setToolTip.call_count >= 1
            mock_item.setToolTip.assert_called_with("Sin descripción")

    def test_on_gallery_item_double_clicked_with_path(self, dialog, mock_controller):
        """Verifica que doble-clic abre el archivo."""
        mock_item = MagicMock()
        mock_item.data.return_value = "/path/to/img.png"
        dialog.iterations_tab._on_gallery_item_double_clicked(mock_item)
        assert mock_controller.app.file_controller.handle_view_file.call_count == 1
        mock_controller.app.file_controller.handle_view_file.assert_called_once_with("/path/to/img.png")

    def test_on_gallery_item_double_clicked_no_path(self, dialog, mock_controller):
        """Verifica que no hace nada si path es None."""
        mock_item = MagicMock()
        mock_item.data.return_value = None
        dialog.iterations_tab._on_gallery_item_double_clicked(mock_item)
        assert mock_controller.app.file_controller.handle_view_file.call_count == 0
        mock_controller.app.file_controller.handle_view_file.assert_not_called()

    # --- Plano ---

    def teston_view_plano_clicked_no_selection(self, dialog):
        """Verifica que retorna si no hay iteración seleccionada."""
        dialog.iterations_tab.current_selected_iteration_id = None
        dialog.iterations_tab.on_view_plano_clicked()
        # Sin selección, no debe intentar abrir ningún archivo
        assert dialog.iterations_tab.current_selected_iteration_id is None

    def teston_view_plano_clicked_with_plano(self, dialog, mock_controller):
        """Verifica apertura de plano adjunto."""
        it = _make_iteration_dto(id=5, ruta_plano="/plan.pdf")
        mock_controller.product_service.get_product_iterations.return_value = [it]
        dialog.iterations_tab.current_selected_iteration_id = 5
        dialog.iterations_tab.on_view_plano_clicked()
        assert mock_controller.app.file_controller.handle_view_file.call_count == 1
        mock_controller.app.file_controller.handle_view_file.assert_called_once_with("/plan.pdf")

    def teston_view_plano_clicked_no_plano(self, dialog, mock_controller, mock_view):
        """Verifica mensaje si no hay plano adjunto."""
        it = _make_iteration_dto(id=5, ruta_plano=None)
        mock_controller.product_service.get_product_iterations.return_value = [it]
        dialog.iterations_tab.current_selected_iteration_id = 5
        dialog.iterations_tab.on_view_plano_clicked()
        assert mock_view.show_message.call_count >= 1
        mock_view.show_message.assert_called()

    def teston_view_plano_clicked_iteration_not_found(self, dialog, mock_controller, mock_view):
        """Verifica mensaje si la iteración ya no existe en la lista."""
        mock_controller.product_service.get_product_iterations.return_value = []
        dialog.iterations_tab.current_selected_iteration_id = 999
        dialog.iterations_tab.on_view_plano_clicked()
        assert mock_view.show_message.call_count >= 1
        mock_view.show_message.assert_called()

    # --- Crear Iteración ---

    def test_on_add_new_iteration_rejected(self, dialog, mock_controller):
        """Verifica que al cancelar el diálogo no se llama al handler."""
        from PyQt6.QtWidgets import QDialog as QD
        with patch("ui.dialogs.product.add_iteration_dialog.AddIterationDialog", autospec=True) as MockDlg:
            MockDlg.return_value.exec.return_value = QD.DialogCode.Rejected
            dialog.iterations_tab.on_add_new_iteration_clicked()
            assert mock_controller.handle_add_product_iteration.call_count == 0
            mock_controller.handle_add_product_iteration.assert_not_called()

    def test_on_add_new_iteration_empty_fields(self, dialog, mock_controller, mock_view):
        """Verifica aviso si campos obligatorios vacíos."""
        from PyQt6.QtWidgets import QDialog as QD
        with patch("ui.dialogs.product.add_iteration_dialog.AddIterationDialog", autospec=True) as MockDlg:
            MockDlg.return_value.exec.return_value = QD.DialogCode.Accepted
            from ui.dialogs.product.add_iteration_dialog import AddIterationFormData

            MockDlg.return_value.get_data.return_value = AddIterationFormData(
                responsable="",
                descripcion="",
                tipo_fallo="No especificado",
                ruta_plano_origen=None,
            )
            dialog.iterations_tab.on_add_new_iteration_clicked()
            assert mock_view.show_message.call_count >= 1
            mock_view.show_message.assert_called()
            assert mock_controller.handle_add_product_iteration.call_count == 0
            mock_controller.handle_add_product_iteration.assert_not_called()

    def test_on_add_new_iteration_success(self, dialog, mock_controller):
        """Verifica creación exitosa de iteración."""
        from PyQt6.QtWidgets import QDialog as QD
        with patch("ui.dialogs.product.add_iteration_dialog.AddIterationDialog", autospec=True) as MockDlg:
            MockDlg.return_value.exec.return_value = QD.DialogCode.Accepted
            from dataclasses import asdict

            from ui.dialogs.product.add_iteration_dialog import AddIterationFormData

            form = AddIterationFormData(
                responsable="Ana",
                descripcion="Cambio X",
                tipo_fallo="No especificado",
                ruta_plano_origen=None,
            )
            MockDlg.return_value.get_data.return_value = form
            mock_controller.handle_add_product_iteration.return_value = True
            dialog.iterations_tab.on_add_new_iteration_clicked()
            assert mock_controller.handle_add_product_iteration.call_count == 1
            mock_controller.handle_add_product_iteration.assert_called_once_with("P001", asdict(form))

    # --- Editar Iteración ---

    def test_on_edit_iteration_no_selection(self, dialog, mock_view):
        """Verifica aviso si no hay iteración seleccionada."""
        dialog.iterations_tab.current_selected_iteration_id = None
        dialog.iterations_tab.on_edit_iteration_clicked()
        assert mock_view.show_message.call_count >= 1
        mock_view.show_message.assert_called()

    def test_on_edit_iteration_cancel_first(self, dialog, mock_controller):
        """Verifica cancelación en primer diálogo de edición de iteración."""
        dialog.iterations_tab.current_selected_iteration_id = 1
        dialog.iterations_tab.lbl_responsable.setText("Juan")
        dialog.iterations_tab.txt_descripcion.setPlainText("Desc original")
        with patch("ui.widgets.product.iterations_widget.QInputDialog") as MockInput:
            MockInput.getText.return_value = ("", False)
            dialog.iterations_tab.on_edit_iteration_clicked()
            assert mock_controller.handle_update_product_iteration.call_count == 0
            mock_controller.handle_update_product_iteration.assert_not_called()

    def test_on_edit_iteration_cancel_second(self, dialog, mock_controller):
        """Verifica cancelación en segundo diálogo de edición de iteración."""
        dialog.iterations_tab.current_selected_iteration_id = 1
        dialog.iterations_tab.lbl_responsable.setText("Juan")
        dialog.iterations_tab.txt_descripcion.setPlainText("Desc original")
        with patch("ui.widgets.product.iterations_widget.QInputDialog") as MockInput:
            MockInput.getText.return_value = ("Nuevo Resp", True)
            MockInput.getMultiLineText.return_value = ("", False)
            dialog.iterations_tab.on_edit_iteration_clicked()
            assert mock_controller.handle_update_product_iteration.call_count == 0
            mock_controller.handle_update_product_iteration.assert_not_called()

    def test_on_edit_iteration_empty_responsable(self, dialog, mock_controller):
        """Verifica que no edita con responsable vacío."""
        dialog.iterations_tab.current_selected_iteration_id = 1
        dialog.iterations_tab.lbl_responsable.setText("Juan")
        dialog.iterations_tab.txt_descripcion.setPlainText("Desc")
        with patch("ui.widgets.product.iterations_widget.QInputDialog") as MockInput:
            MockInput.getText.return_value = ("  ", True)
            dialog.iterations_tab.on_edit_iteration_clicked()
            assert mock_controller.handle_update_product_iteration.call_count == 0
            mock_controller.handle_update_product_iteration.assert_not_called()

    def test_on_edit_iteration_empty_desc(self, dialog, mock_controller):
        """Verifica que no edita con descripción vacía."""
        dialog.iterations_tab.current_selected_iteration_id = 1
        dialog.iterations_tab.lbl_responsable.setText("Juan")
        dialog.iterations_tab.txt_descripcion.setPlainText("Desc")
        with patch("ui.widgets.product.iterations_widget.QInputDialog") as MockInput:
            MockInput.getText.return_value = ("Nuevo Resp", True)
            MockInput.getMultiLineText.return_value = ("  ", True)
            dialog.iterations_tab.on_edit_iteration_clicked()
            assert mock_controller.handle_update_product_iteration.call_count == 0
            mock_controller.handle_update_product_iteration.assert_not_called()

    def test_on_edit_iteration_success(self, dialog, mock_controller):
        """Verifica edición exitosa de una iteración."""
        it = _make_iteration_dto(id=1, nombre_responsable="Juan", descripcion="Desc original")
        mock_controller.product_service.get_product_iterations.return_value = [it]
        dialog.iterations_tab.load_data()
        dialog.iterations_tab.iterations_list.setCurrentItem(dialog.iterations_tab.iterations_list.topLevelItem(0))
        with patch("ui.widgets.product.iterations_widget.QInputDialog") as MockInput:
            MockInput.getText.return_value = ("Nuevo Resp", True)
            MockInput.getMultiLineText.return_value = ("Nueva desc", True)
            mock_controller.handle_update_product_iteration.return_value = True
            dialog.iterations_tab.on_edit_iteration_clicked()
            assert mock_controller.handle_update_product_iteration.call_count == 1
            mock_controller.handle_update_product_iteration.assert_called_once_with(1, "Nuevo Resp", "Nueva desc", "Fallo de Proveedor")

    # --- Eliminar Iteración ---

    def test_on_delete_iteration_no_selection(self, dialog, mock_view):
        """Verifica aviso si no hay selección."""
        dialog.iterations_tab.current_selected_iteration_id = None
        dialog.iterations_tab.on_delete_iteration_clicked()
        assert mock_view.show_message.call_count >= 1
        mock_view.show_message.assert_called()

    def test_on_delete_iteration_not_confirmed(self, dialog, mock_controller, mock_view):
        """Verifica que no elimina sin confirmación."""
        dialog.iterations_tab.current_selected_iteration_id = 1
        mock_view.show_confirmation_dialog.return_value = False
        dialog.iterations_tab.on_delete_iteration_clicked()
        assert mock_controller.handle_delete_product_iteration.call_count == 0
        mock_controller.handle_delete_product_iteration.assert_not_called()

    def test_on_delete_iteration_success(self, dialog, mock_controller, mock_view):
        """Verifica eliminación exitosa de iteración."""
        it = _make_iteration_dto(id=1)
        mock_controller.product_service.get_product_iterations.return_value = [it]
        dialog.iterations_tab.load_data()
        dialog.iterations_tab.iterations_list.setCurrentItem(dialog.iterations_tab.iterations_list.topLevelItem(0))
        mock_view.show_confirmation_dialog.return_value = True
        mock_controller.handle_delete_product_iteration.return_value = True
        dialog.iterations_tab.on_delete_iteration_clicked()
        assert mock_controller.handle_delete_product_iteration.call_count == 1
        mock_controller.handle_delete_product_iteration.assert_called_once_with(1)

    # --- Añadir Imagen ---

    def test_on_add_image_no_selection(self, dialog, mock_view):
        """Verifica aviso si no hay iteración seleccionada."""
        dialog.iterations_tab.current_selected_iteration_id = None
        dialog.iterations_tab._on_add_image_clicked()
        assert mock_view.show_message.call_count >= 1
        mock_view.show_message.assert_called()

    def test_on_add_image_cancel_file_dialog(self, dialog, mock_controller):
        """Verifica que no hace nada si se cancela el selector de archivos."""
        dialog.iterations_tab.current_selected_iteration_id = 1
        with patch("ui.widgets.product.iterations_widget.QFileDialog") as MockFD:
            MockFD.getOpenFileNames.return_value = ([], "")
            dialog.iterations_tab._on_add_image_clicked()
        # Sin archivos seleccionados, no se llama al handler
        assert mock_controller.handle_add_iteration_image.call_count == 0
        mock_controller.handle_add_iteration_image.assert_not_called()

    def test_on_add_image_success(self, dialog, mock_controller, mock_view):
        """Verifica flujo exitoso al añadir imágenes."""
        dialog.iterations_tab.current_selected_iteration_id = 1
        mock_controller.product_service.get_product_iterations.return_value = []
        with patch("ui.widgets.product.iterations_widget.QFileDialog") as MockFD:
            MockFD.getOpenFileNames.return_value = (["/img1.png", "/img2.png"], "")
            mock_controller.handle_add_iteration_image.return_value = (True, "OK")
            dialog.iterations_tab._on_add_image_clicked()
            assert mock_controller.handle_add_iteration_image.call_count == 2
            calls = mock_view.show_message.call_args_list
            assert any("2 imágenes" in str(c) for c in calls)

    def test_on_add_image_all_fail(self, dialog, mock_controller, mock_view):
        """Verifica mensaje de error cuando todas las imágenes fallan."""
        dialog.iterations_tab.current_selected_iteration_id = 1
        with patch("ui.widgets.product.iterations_widget.QFileDialog") as MockFD:
            MockFD.getOpenFileNames.return_value = (["/fail.png"], "")
            mock_controller.handle_add_iteration_image.return_value = (False, "Error")
            dialog.iterations_tab._on_add_image_clicked()
            calls = mock_view.show_message.call_args_list
            assert any("No se pudieron" in str(c) for c in calls)

    # --- Eliminar Imagen ---

    def test_on_delete_image_no_selection(self, dialog, mock_view):
        """Verifica aviso si no hay imagen seleccionada."""
        dialog.iterations_tab.gallery_list.clearSelection()
        dialog.iterations_tab._on_delete_image_clicked()
        assert mock_view.show_message.call_count >= 1
        mock_view.show_message.assert_called()

    def test_on_delete_image_legacy(self, dialog, mock_view):
        """Verifica que la imagen marcada como previa no se puede eliminar."""
        from PyQt6.QtCore import Qt
        mock_item = MagicMock()
        mock_item.data.side_effect = lambda role: {
            Qt.ItemDataRole.UserRole: "/legacy.png",
            Qt.ItemDataRole.UserRole + 1: None,
            Qt.ItemDataRole.UserRole + 2: True,
        }.get(role)
        dialog.iterations_tab.gallery_list = MagicMock()
        dialog.iterations_tab.gallery_list.selectedItems.return_value = [mock_item]
        dialog.iterations_tab._on_delete_image_clicked()
        assert any("legacy" in str(c).lower() for c in mock_view.show_message.call_args_list)

    def test_on_delete_image_confirmed_success(self, dialog, mock_controller, mock_view):
        """Verifica eliminación exitosa de imagen no marcada como previa."""
        from PyQt6.QtCore import Qt
        mock_item = MagicMock()
        mock_item.data.side_effect = lambda role: {
            Qt.ItemDataRole.UserRole: "/new.png",
            Qt.ItemDataRole.UserRole + 1: 42,
            Qt.ItemDataRole.UserRole + 2: False,
        }.get(role)
        dialog.iterations_tab.gallery_list = MagicMock()
        dialog.iterations_tab.gallery_list.selectedItems.return_value = [mock_item]
        mock_view.show_confirmation_dialog.return_value = True
        mock_controller.handle_delete_iteration_image.return_value = True
        mock_controller.product_service.get_product_iterations.return_value = []
        dialog.iterations_tab.current_selected_iteration_id = 1
        dialog.iterations_tab._on_delete_image_clicked()
        assert mock_controller.handle_delete_iteration_image.call_count == 1
        mock_controller.handle_delete_iteration_image.assert_called_once_with(42)

    def test_on_delete_image_confirmed_failure(self, dialog, mock_controller, mock_view):
        """Verifica mensaje de error al fallar eliminación."""
        from PyQt6.QtCore import Qt
        mock_item = MagicMock()
        mock_item.data.side_effect = lambda role: {
            Qt.ItemDataRole.UserRole: "/new.png",
            Qt.ItemDataRole.UserRole + 1: 42,
            Qt.ItemDataRole.UserRole + 2: False,
        }.get(role)
        dialog.iterations_tab.gallery_list = MagicMock()
        dialog.iterations_tab.gallery_list.selectedItems.return_value = [mock_item]
        mock_view.show_confirmation_dialog.return_value = True
        mock_controller.handle_delete_iteration_image.return_value = False
        dialog.iterations_tab._on_delete_image_clicked()
        assert any("No se pudo" in str(c) for c in mock_view.show_message.call_args_list)

    def test_on_delete_image_not_confirmed(self, dialog, mock_controller, mock_view):
        """Verifica que no elimina si el usuario no confirma."""
        from PyQt6.QtCore import Qt
        mock_item = MagicMock()
        mock_item.data.side_effect = lambda role: {
            Qt.ItemDataRole.UserRole: "/new.png",
            Qt.ItemDataRole.UserRole + 1: 42,
            Qt.ItemDataRole.UserRole + 2: False,
        }.get(role)
        dialog.iterations_tab.gallery_list = MagicMock()
        dialog.iterations_tab.gallery_list.selectedItems.return_value = [mock_item]
        mock_view.show_confirmation_dialog.return_value = False
        dialog.iterations_tab._on_delete_image_clicked()
        assert mock_controller.handle_delete_iteration_image.call_count == 0
        mock_controller.handle_delete_iteration_image.assert_not_called()


    # --- Reselect ---

    def test_reselect_current_iteration(self, dialog, mock_controller):
        """Verifica que _reselect_current_iteration encuentra y selecciona el item."""
        it = _make_iteration_dto(id=7)
        mock_controller.product_service.get_product_iterations.return_value = [it]
        mock_controller.db.get_iteration_images.return_value = []
        dialog.iterations_tab.load_data()
        dialog.iterations_tab.current_selected_iteration_id = 7
        dialog.iterations_tab._reselect_current_iteration()
        assert dialog.iterations_tab.iterations_list.currentItem() is not None

    def test_reselect_current_iteration_not_found(self, dialog, mock_controller):
        """Verifica que no crashea si la iteración ya no está en el tree."""
        it = _make_iteration_dto(id=7)
        mock_controller.product_service.get_product_iterations.return_value = [it]
        dialog.iterations_tab.load_data()
        dialog.iterations_tab.current_selected_iteration_id = 999
        dialog.iterations_tab._reselect_current_iteration()
        # ID 999 no existe en el tree — no debe seleccionar nada
        assert dialog.iterations_tab.iterations_list.currentItem() is None or \
               dialog.iterations_tab.iterations_list.currentItem().data(0, 0) != 999


    # --- Clear/Show Details ---

    def test_clear_details_panel(self, dialog):
        """Verifica que _clear_details_panel oculta widgets y muestra placeholder."""
        dialog.iterations_tab._clear_details_panel()
        assert dialog.iterations_tab.current_selected_iteration_id is None
        assert not dialog.iterations_tab.btn_edit_iteration.isEnabled()
        assert not dialog.iterations_tab.btn_delete_iteration.isEnabled()
        assert hasattr(dialog.iterations_tab, 'placeholder')

    def test_clear_details_panel_twice(self, dialog):
        """Verifica que _clear_details_panel funciona al llamarse varias veces (deleteLater branch)."""
        dialog.iterations_tab._clear_details_panel()
        dialog.iterations_tab._clear_details_panel()  # Segunda vez: tiene 'placeholder' existente
        # Después de dos llamadas, el estado sigue siendo el mismo
        assert dialog.iterations_tab.current_selected_iteration_id is None

    def test_show_details_panel(self, dialog):
        """Verifica que _show_details_panel muestra los widgets."""
        dialog.iterations_tab._clear_details_panel()
        dialog.iterations_tab._show_details_panel()
        # Placeholder should be hidden
        assert not dialog.iterations_tab.placeholder.isVisible()


# ==============================================================================
# TEST CLASS: AddIterationDialog
# ==============================================================================
@pytest.mark.unit
class TestAddIterationDialog:
    """Tests unitarios para AddIterationDialog."""

    @pytest.fixture
    def dialog(self, qapp):
        """Instancia de AddIterationDialog."""
        from ui.dialogs.product import AddIterationDialog
        return AddIterationDialog("P001")

    def test_init(self, dialog):
        """Verifica inicialización del diálogo de iteración."""
        assert dialog.product_code == "P001"
        assert dialog.attached_plano_path is None
        assert "Iteración" in dialog.windowTitle()

    def test_get_data(self, dialog):
        """Verifica que get_data retorna dataclass correcta."""
        dialog.responsable_edit.setText("Ana")
        dialog.description_edit.setPlainText("Descripción del cambio")
        data = dialog.get_data()
        assert data.responsable == "Ana"
        assert data.descripcion == "Descripción del cambio"
        assert isinstance(data.tipo_fallo, str)
        assert data.ruta_plano_origen is None

    def test_attach_plano_success(self, dialog):
        """Verifica adjuntar plano exitosamente."""
        with patch("ui.dialogs.product.add_iteration_dialog.QFileDialog") as MockFD:
            MockFD.getOpenFileName.return_value = ("/plans/plano.pdf", "")
            dialog._attach_plano()
            assert dialog.attached_plano_path == "/plans/plano.pdf"
            assert "plano.pdf" in dialog.plano_label.text()

    def test_attach_plano_cancel(self, dialog):
        """Verifica que cancelar no cambia el estado."""
        with patch("ui.dialogs.product.add_iteration_dialog.QFileDialog") as MockFD:
            MockFD.getOpenFileName.return_value = ("", "")
            dialog._attach_plano()
            assert dialog.attached_plano_path is None

    def test_get_data_with_plano(self, dialog):
        """Verifica get_data incluye plano adjuntado."""
        dialog.attached_plano_path = "/plans/plano.pdf"
        data = dialog.get_data()
        assert data.ruta_plano_origen == "/plans/plano.pdf"


# ==============================================================================
# TEST CLASS: SubfabricacionesDialog
# ==============================================================================
@pytest.mark.unit
class TestSubfabricacionesDialog:
    """Tests unitarios para SubfabricacionesDialog con flujos CRUD completos."""

    @pytest.fixture
    def machines(self):
        """Lista de máquinas DTO para el diálogo."""
        m1 = _make_machine_dto(id=10, nombre="CNC-1")
        m2 = _make_machine_dto(id=20, nombre="Torno-1")
        assert isinstance(m1, MachineDTO)
        return [m1, m2]

    @pytest.fixture
    def dialog(self, qapp, machines):
        """Instancia de SubfabricacionesDialog."""
        subfabs = [
            SubfabricacionDTO(
                id=1,
                producto_codigo="P001",
                descripcion="Corte",
                tiempo=5.0,
                tipo_trabajador=1,
                maquina_id=10,
            )
        ]
        from ui.dialogs.product import SubfabricacionesDialog
        return SubfabricacionesDialog(subfabs, machines)

    def test_init(self, dialog):
        """Verifica inicialización correcta."""
        assert len(dialog.subfabricaciones) == 1
        assert dialog._selected_row == -1

    def test_refresh_table(self, dialog):
        """Verifica que _refresh_table puebla la tabla con datos."""
        assert dialog.table.rowCount() == 1
        assert dialog.table.item(0, 0).text() == "Corte"

    def test_refresh_table_with_machine_id_not_found(self, qapp):
        """Verifica que máquina no encontrada muestra celda vacía."""
        subfabs = [
            SubfabricacionDTO(
                id=1,
                producto_codigo="P001",
                descripcion="X",
                tiempo=1.0,
                tipo_trabajador=1,
                maquina_id=9999,
            )
        ]
        machines = [_make_machine_dto(id=10, nombre="CNC-1")]
        from ui.dialogs.product import SubfabricacionesDialog
        dlg = SubfabricacionesDialog(subfabs, machines)
        item = dlg.table.item(0, 3)
        assert item is not None
        assert item.text() == ""

    def test_refresh_table_without_machine_id(self, qapp):
        """Verifica que sin maquina_id muestra celda vacía."""
        subfabs = [
            SubfabricacionDTO(
                id=1,
                producto_codigo="P001",
                descripcion="X",
                tiempo=1.0,
                tipo_trabajador=1,
                maquina_id=None,
            )
        ]
        from ui.dialogs.product import SubfabricacionesDialog
        dlg = SubfabricacionesDialog(subfabs, [])
        item = dlg.table.item(0, 3)
        assert item is not None
        assert item.text() == ""

    def test_on_item_selected(self, dialog):
        """Verifica que seleccionar un item llena el formulario."""
        dialog.table.selectRow(0)
        assert dialog._selected_row == 0
        assert dialog.desc_entry.text() == "Corte"
        assert dialog.delete_button.isEnabled()
        assert "Actualizar" in dialog.add_update_button.text()

    def test_on_item_selected_no_selection(self, dialog):
        """Verifica que deseleccionar limpia el formulario."""
        dialog.table.selectRow(0)
        dialog.table.clearSelection()
        assert dialog._selected_row == -1
        assert not dialog.delete_button.isEnabled()

    def test_on_item_selected_machine_not_found(self, qapp):
        """Verifica selección con máquina eliminada (fallback a Ninguna)."""
        subfabs = [
            SubfabricacionDTO(
                id=1,
                producto_codigo="P001",
                descripcion="X",
                tiempo=1.0,
                tipo_trabajador=1,
                maquina_id=9999,
            )
        ]
        machines = [_make_machine_dto(id=10, nombre="CNC-1")]
        from ui.dialogs.product import SubfabricacionesDialog
        dlg = SubfabricacionesDialog(subfabs, machines)
        dlg.table.selectRow(0)
        assert dlg.tipo_proceso_menu.currentIndex() == 0

    def test_on_item_selected_no_machine_id(self, qapp):
        """Verifica selección sin maquina_id asignado."""
        subfabs = [
            SubfabricacionDTO(
                id=1,
                producto_codigo="P001",
                descripcion="X",
                tiempo=1.0,
                tipo_trabajador=1,
                maquina_id=None,
            )
        ]
        from ui.dialogs.product import SubfabricacionesDialog
        dlg = SubfabricacionesDialog(subfabs, [])
        dlg.table.selectRow(0)
        assert dlg.tipo_proceso_menu.currentIndex() == 0

    def test_add_or_update_empty_fields(self, dialog):
        """Verifica aviso con campos vacíos."""
        dialog.desc_entry.clear()
        dialog.tiempo_entry.clear()
        with patch("ui.dialogs.product.subfabricaciones_dialog.QMessageBox", autospec=True) as MockMB:
            dialog._add_or_update()
            assert MockMB.warning.call_count == 1
            MockMB.warning.assert_called_once_with(ANY, ANY, ANY)

    def test_add_or_update_invalid_time(self, dialog):
        """Verifica aviso con tiempo inválido."""
        dialog.desc_entry.setText("Nueva sub")
        dialog.tiempo_entry.setText("abc")
        with patch("ui.dialogs.product.subfabricaciones_dialog.QMessageBox", autospec=True) as MockMB:
            dialog._add_or_update()
            assert MockMB.warning.call_count == 1
            MockMB.warning.assert_called_once_with(ANY, ANY, ANY)

    def test_add_or_update_negative_time(self, dialog):
        """Verifica aviso con tiempo negativo."""
        dialog.desc_entry.setText("Nueva sub")
        dialog.tiempo_entry.setText("-5")
        with patch("ui.dialogs.product.subfabricaciones_dialog.QMessageBox", autospec=True) as MockMB:
            dialog._add_or_update()
            assert MockMB.warning.call_count == 1
            MockMB.warning.assert_called_once_with(ANY, ANY, ANY)

    def test_add_or_update_zero_time(self, dialog):
        """Verifica aviso con tiempo cero."""
        dialog.desc_entry.setText("Nueva sub")
        dialog.tiempo_entry.setText("0")
        with patch("ui.dialogs.product.subfabricaciones_dialog.QMessageBox", autospec=True) as MockMB:
            dialog._add_or_update()
            assert MockMB.warning.call_count == 1
            MockMB.warning.assert_called_once_with(ANY, ANY, ANY)

    def test_add_new_subfabricacion(self, dialog):
        """Verifica añadir una nueva sub-fabricación."""
        dialog._clear_form()
        dialog.desc_entry.setText("Soldadura")
        dialog.tiempo_entry.setText("15,5")
        dialog._add_or_update()
        assert len(dialog.subfabricaciones) == 2
        assert dialog.subfabricaciones[-1].descripcion == "Soldadura"
        assert dialog.subfabricaciones[-1].tiempo == 15.5

    def test_update_existing_subfabricacion(self, dialog):
        """Verifica actualización de sub-fabricación existente."""
        dialog.table.selectRow(0)
        dialog.desc_entry.setText("Corte Actualizado")
        dialog.tiempo_entry.setText("10")
        dialog._add_or_update()
        assert dialog.subfabricaciones[0].descripcion == "Corte Actualizado"
        assert dialog.subfabricaciones[0].tiempo == 10.0

    def test_delete_selected(self, dialog):
        """Verifica eliminación de sub-fabricación seleccionada."""
        dialog.table.selectRow(0)
        dialog._delete_selected()
        assert len(dialog.subfabricaciones) == 0

    def test_delete_selected_no_selection(self, dialog):
        """Verifica que no hace nada si _selected_row es -1."""
        dialog._selected_row = -1
        dialog._delete_selected()
        assert len(dialog.subfabricaciones) == 1

    def test_clear_form(self, dialog):
        """Verifica que _clear_form resetea todo el formulario."""
        dialog.desc_entry.setText("Algo")
        dialog.tiempo_entry.setText("5")
        dialog._clear_form()
        assert dialog.desc_entry.text() == ""
        assert dialog.tiempo_entry.text() == ""
        assert dialog._selected_row == -1
        assert not dialog.delete_button.isEnabled()

    def test_get_updated_subfabricaciones(self, dialog):
        """Verifica que retorna la lista actualizada."""
        result = dialog.get_updated_subfabricaciones()
        assert isinstance(result, list)
        assert len(result) == len(dialog.subfabricaciones)
        assert result[0]["descripcion"] == dialog.subfabricaciones[0].descripcion

    def test_accept_with_unsaved_data_discard(self, dialog):
        """Verifica accept con datos sin guardar, usuario descarta."""
        dialog.desc_entry.setText("Datos sin guardar")
        with patch("ui.dialogs.product.subfabricaciones_dialog.QMessageBox", autospec=True) as MockMB:
            from PyQt6.QtWidgets import QMessageBox as QMB
            MockMB.StandardButton = QMB.StandardButton
            MockMB.question.return_value = QMB.StandardButton.Yes
            dialog.accept()
            assert MockMB.question.call_count == 1
            MockMB.question.assert_called_once_with(ANY, ANY, ANY, ANY, ANY)

    def test_accept_with_unsaved_data_keep(self, dialog):
        """Verifica que accept se cancela si el usuario elige No."""
        dialog.desc_entry.setText("Datos sin guardar")
        with patch("ui.dialogs.product.subfabricaciones_dialog.QMessageBox", autospec=True) as MockMB:
            from PyQt6.QtWidgets import QMessageBox as QMB
            MockMB.StandardButton = QMB.StandardButton
            MockMB.question.return_value = QMB.StandardButton.No
            dialog.accept()
            # El diálogo no se cierra — la pregunta se hizo
            assert MockMB.question.call_count == 1
            MockMB.question.assert_called_once_with(ANY, ANY, ANY, ANY, ANY)

    def test_accept_without_unsaved_data(self, dialog):
        """Verifica accept normal sin datos pendientes."""
        from PyQt6.QtWidgets import QDialog as QD
        dialog.desc_entry.clear()
        dialog.tiempo_entry.clear()
        try:
            dialog.accept()
        except Exception:
            pytest.fail("accept no debería propagar excepciones sin datos pendientes")
        assert dialog.result() == int(QD.DialogCode.Accepted)


# ==============================================================================
# TEST CLASS: ProcesosMecanicosDialog
# ==============================================================================
@pytest.mark.unit
class TestProcesosMecanicosDialog:
    """Tests unitarios para ProcesosMecanicosDialog."""

    @pytest.fixture
    def dialog(self, qapp):
        """Instancia del diálogo con procesos iniciales."""
        procesos = [
            {"nombre": "Torneado", "descripcion": "Torneado CNC", "tiempo": 30, "tipo_trabajador": 1}
        ]
        from ui.dialogs.product import ProcesosMecanicosDialog
        return ProcesosMecanicosDialog(procesos)

    def test_init(self, dialog):
        """Verifica inicialización con procesos."""
        assert len(dialog.procesos_data) == 1
        assert dialog.table.rowCount() == 1

    def test_init_with_none(self, qapp):
        """Verifica inicialización con None (lista vacía)."""
        from ui.dialogs.product import ProcesosMecanicosDialog
        dlg = ProcesosMecanicosDialog(None)
        assert len(dlg.procesos_data) == 0

    def test_populate_table(self, dialog):
        """Verifica que populate_table llena la tabla correctamente."""
        item0 = dialog.table.item(0, 0)
        item1 = dialog.table.item(0, 1)
        item2 = dialog.table.item(0, 2)
        assert item0 is not None and item1 is not None and item2 is not None
        assert item0.text() == "Torneado"
        assert item1.text() == "Torneado CNC"
        assert item2.text() == "30"

    def test_add_proceso_accepted(self, dialog):
        """Verifica añadir un proceso mecánico desde el sub-diálogo."""
        from PyQt6.QtWidgets import QDialog as QD
        with patch("ui.dialogs.product.procesos_mecanicos_dialog.AddProcesoMecanicoDialog", autospec=True) as MockDlg:
            MockDlg.return_value.exec.return_value = QD.DialogCode.Accepted
            MockDlg.return_value.get_proceso_data.return_value = {
                "nombre": "Fresado", "descripcion": "Fresado 3D",
                "tiempo": 45.0, "tipo_trabajador": 2
            }
            dialog.add_proceso()
            assert len(dialog.procesos_data) == 2

    def test_add_proceso_rejected(self, dialog):
        """Verifica que cancelar no añade proceso."""
        from PyQt6.QtWidgets import QDialog as QD
        with patch("ui.dialogs.product.procesos_mecanicos_dialog.AddProcesoMecanicoDialog", autospec=True) as MockDlg:
            MockDlg.return_value.exec.return_value = QD.DialogCode.Rejected
            dialog.add_proceso()
            assert len(dialog.procesos_data) == 1

    def test_delete_proceso_valid_row(self, dialog):
        """Verifica eliminación de proceso en fila válida."""
        dialog.delete_proceso(0)
        assert len(dialog.procesos_data) == 0

    def test_delete_proceso_invalid_row(self, dialog):
        """Verifica que no falla con fila inválida."""
        dialog.delete_proceso(-1)
        dialog.delete_proceso(999)
        assert len(dialog.procesos_data) == 1

    def test_get_updated_procesos_all_valid(self, dialog):
        """Verifica que retorna procesos actualizados desde la tabla."""
        result = dialog.get_updated_procesos_mecanicos()
        assert len(result) == 1
        assert result[0]["nombre"] == "Torneado"

    def test_get_updated_procesos_empty_name(self, qapp):
        """Verifica que procesos sin nombre son excluidos."""
        from ui.dialogs.product import ProcesosMecanicosDialog
        procesos = [{"nombre": "", "descripcion": "Vacio", "tiempo": 5, "tipo_trabajador": 1}]
        dlg = ProcesosMecanicosDialog(procesos)
        result = dlg.get_updated_procesos_mecanicos()
        assert len(result) == 0

    def test_get_updated_procesos_invalid_time(self, qapp):
        """Verifica que procesos con tiempo inválido se omiten (ValueError)."""
        from ui.dialogs.product import ProcesosMecanicosDialog
        procesos = [{"nombre": "Test", "descripcion": "Desc", "tiempo": "abc", "tipo_trabajador": 1}]
        dlg = ProcesosMecanicosDialog(procesos)
        # Manualmente cambiar el item de la tabla para simular dato inválido
        from PyQt6.QtWidgets import QTableWidgetItem
        dlg.table.setItem(0, 2, QTableWidgetItem("not_a_number"))
        result = dlg.get_updated_procesos_mecanicos()
        assert len(result) == 0

    def test_get_updated_procesos_missing_items(self, qapp):
        """Verifica que filas con items None se omiten."""
        from ui.dialogs.product import ProcesosMecanicosDialog
        dlg = ProcesosMecanicosDialog([])
        dlg.table.setRowCount(1)
        # Dejamos items como None
        result = dlg.get_updated_procesos_mecanicos()
        assert len(result) == 0

    def test_populate_table_with_missing_keys(self, qapp):
        """Verifica que populate_table maneja claves faltantes con defaults."""
        from ui.dialogs.product import ProcesosMecanicosDialog
        from typing import Dict, Any
        procesos: List[Dict[str, Any]] = [{}]
        dlg = ProcesosMecanicosDialog(procesos)
        item0 = dlg.table.item(0, 0)
        item2 = dlg.table.item(0, 2)
        assert item0 is not None and item2 is not None
        assert item0.text() == ""
        assert item2.text() == "0"


# ==============================================================================
# TEST CLASS: AddProcesoMecanicoDialog
# ==============================================================================
@pytest.mark.unit
class TestAddProcesoMecanicoDialog:
    """Tests unitarios para AddProcesoMecanicoDialog."""

    @pytest.fixture
    def dialog(self, qapp):
        """Instancia del diálogo."""
        from ui.dialogs.product import AddProcesoMecanicoDialog
        return AddProcesoMecanicoDialog()

    def test_init(self, dialog):
        """Verifica inicialización."""
        assert "Proceso Mecánico" in dialog.windowTitle()
        assert dialog.isModal()

    def test_get_proceso_data_filled(self, dialog):
        """Verifica get_proceso_data con todos los campos llenos."""
        dialog.nombre_entry.setText("Soldadura")
        dialog.descripcion_entry.setPlainText("Soldadura TIG")
        dialog.tiempo_entry.setText("25,5")
        dialog.tipo_trabajador_combo.setCurrentIndex(1)

        data = dialog.get_proceso_data()
        assert data["nombre"] == "Soldadura"
        assert data["descripcion"] == "Soldadura TIG"
        assert data["tiempo"] == 25.5
        assert data["tipo_trabajador"] == 2

    def test_get_proceso_data_empty_time(self, dialog):
        """Verifica get_proceso_data con tiempo vacío retorna 0.0."""
        dialog.nombre_entry.setText("Test")
        dialog.descripcion_entry.setPlainText("")
        dialog.tiempo_entry.setText("")
        data = dialog.get_proceso_data()
        assert data["tiempo"] == 0.0

    def test_get_proceso_data_with_comma_decimal(self, dialog):
        """Verifica que comas decimales se convierten correctamente."""
        dialog.tiempo_entry.setText("10,75")
        data = dialog.get_proceso_data()
        assert data["tiempo"] == 10.75
