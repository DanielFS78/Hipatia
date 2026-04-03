# -*- coding: utf-8 -*-
"""Tests unitarios para WorkersWidget (ui/widgets/workers_widget.py)."""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, date

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidgetItem, QLabel, QTableWidget, QLineEdit

from core.dtos import WorkerDTO, WorkerDetailDTO
from ui.widgets.workers_widget import WorkersWidget


def _make_worker_dto(worker_id=1, nombre="Juan Pérez", activo=True):
    """Crea un DTO de prueba con todos los atributos necesarios para evitar AttributeError."""
    dto = MagicMock(spec=WorkerDetailDTO) # Usamos DetailDTO que tiene más campos
    dto.id = worker_id
    dto.nombre_completo = nombre
    dto.activo = activo
    dto.notas = "Notas de prueba"
    dto.tipo_trabajador = 1
    dto.username = "user"
    dto.role = "Trabajador"
    return dto


@pytest.fixture
def controller():
    """Controller mock con model y métodos necesarios."""
    from core.di_container import DIContainer
    from controllers.worker.controller import WorkerController
    ctrl = MagicMock(spec=["model"])
    ctrl.model = MagicMock(spec=["get_worker_history", "get_worker_activity_log"])
    ctrl.model.get_worker_history.return_value = ([], [])
    ctrl.model.get_worker_activity_log.return_value = []
    DIContainer.get_instance().register(WorkerController, instance=ctrl)
    return ctrl


@pytest.fixture
def widget(qtbot, controller):
    """Instancia de WorkersWidget con controller mock."""
    w = WorkersWidget(controller)
    qtbot.addWidget(w)
    return w


@pytest.mark.unit
class TestWorkersWidget:
    """Tests unitarios para el widget de gestión de trabajadores."""

    @pytest.fixture(autouse=True)
    def patch_qt_graphics(self):
        """Parchea clases gráficas de Qt para entorno headless."""
        with patch("PyQt6.QtWidgets.QListWidgetItem.setForeground"), \
             patch("PyQt6.QtWidgets.QListWidgetItem.setFont"), \
             patch("PyQt6.QtWidgets.QTableWidgetItem.setForeground"):
            yield

    def test_init(self, widget):
        """Verifica inicialización correcta del widget."""
        assert widget.current_worker_id is None
        assert widget.workers_list is not None
        assert widget.details_panel is not None
        assert widget.activity_panel is not None

    def test_populate_list(self, widget):
        """Verifica que la lista de trabajadores se puebla correctamente con DTOs."""
        workers = [
            _make_worker_dto(1, "Juan Pérez", True),
            _make_worker_dto(2, "Ana López", False),
        ]
        widget.populate_list(workers)

        assert widget.workers_list.count() == 2
        item0 = widget.workers_list.item(0)
        assert "Juan Pérez" in item0.text()
        assert "(Activo)" in item0.text()

        item1 = widget.workers_list.item(1)
        assert "(Inactivo)" in item1.text()

    def test_populate_list_stores_id_in_user_role(self, widget):
        """Verifica que el ID del trabajador se almacena en UserRole."""
        workers = [_make_worker_dto(42, "Test Worker", True)]
        widget.populate_list(workers)

        item = widget.workers_list.item(0)
        assert item.data(Qt.ItemDataRole.UserRole) == 42

    def test_clear_details_area(self, widget):
        """Verifica que se limpia el área de detalles."""
        widget.show_add_new_form()
        assert not widget.right_tabs.isHidden()
        
        widget.clear_details_area()
        assert widget.current_worker_id is None
        assert widget.right_tabs.isHidden()
        assert not widget.placeholder.isHidden()

    def test_show_add_new_form(self, widget):
        """Verifica que el formulario de nuevo trabajador se configura correctamente."""
        widget.show_add_new_form()

        assert widget.current_worker_id is None
        assert not widget.right_tabs.isHidden()
        assert widget.details_panel.title_label.text() == "Añadir Nuevo Trabajador"
        assert widget.details_panel.form_widgets['activo'].isChecked()
        # En headless use isHidden() en lugar de isVisible()
        assert widget.details_panel.delete_btn.isHidden()
        assert widget.details_panel.change_pass_btn.isHidden()
        assert widget.details_panel.assign_group.isHidden()

    def test_show_worker_details(self, widget, controller):
        """Verifica que se muestran los detalles de un trabajador existente."""
        worker_data = _make_worker_dto(5, 'Carlos García', True)
        worker_data.notas = 'Notas de prueba'
        worker_data.tipo_trabajador = 2
        worker_data.username = 'carlos'
        worker_data.role = 'Trabajador'
        
        widget.show_worker_details(worker_data)

        assert widget.current_worker_id == 5
        assert widget.details_panel.title_label.text() == "Editar Trabajador"
        assert widget.details_panel.form_widgets['nombre'].text() == 'Carlos García'
        assert widget.details_panel.form_widgets['activo'].isChecked()
        assert widget.details_panel.form_widgets['notas'].toPlainText() == 'Notas de prueba'
        assert widget.details_panel.form_widgets['tipo_trabajador'].currentIndex() == 1  # tipo 2 -> index 1
        assert widget.details_panel.form_widgets['username'].text() == 'carlos'
        assert widget.details_panel.form_widgets['role'].currentIndex() == 1  # 'Trabajador'

    def test_show_worker_details_role_responsable(self, widget, controller):
        """Verifica que el rol 'Responsable' se mapea al índice correcto."""
        worker_data = _make_worker_dto(6, "Ana", False)
        worker_data.role = 'Responsable'
        
        widget.show_worker_details(worker_data)
        assert widget.details_panel.form_widgets['role'].currentIndex() == 2

    def test_show_worker_details_no_role(self, widget, controller):
        """Verifica que sin rol se selecciona '(Sin acceso)'."""
        worker_data = _make_worker_dto(7, "Luis", True)
        worker_data.role = None
        
        widget.show_worker_details(worker_data)
        assert widget.details_panel.form_widgets['role'].currentIndex() == 0

    def test_get_form_data_filled(self, widget):
        """Verifica que get_form_data retorna los datos correctos del formulario."""
        widget.show_add_new_form()
        panel = widget.details_panel
        panel.form_widgets['nombre'].setText('Nuevo Trabajador')
        panel.form_widgets['activo'].setChecked(True)
        panel.form_widgets['notas'].setPlainText('Notas test')
        panel.form_widgets['tipo_trabajador'].setCurrentIndex(1)  # Tipo 2
        panel.form_widgets['username'].setText('nuevo_user')
        panel.form_widgets['password'].setText('pass123')
        panel.form_widgets['confirm_password'].setText('pass123')
        panel.form_widgets['role'].setCurrentIndex(1)  # 'Trabajador'

        data = widget.get_form_data()
        assert data.nombre_completo == 'Nuevo Trabajador'
        assert data.activo is True
        assert data.notas == 'Notas test'
        assert data.tipo_trabajador == 2
        assert data.username == 'nuevo_user'
        assert data.password == 'pass123'
        assert data.confirm_password == 'pass123'
        assert data.role == 'Trabajador'

    def test_get_form_data_responsable_role(self, widget):
        """Verifica que el rol 'Responsable' se mapea correctamente."""
        widget.show_add_new_form()
        widget.details_panel.form_widgets['nombre'].setText('Admin')
        widget.details_panel.form_widgets['role'].setCurrentIndex(2)

        data = widget.get_form_data()
        assert data.role == 'Responsable'

    def test_get_form_data_no_username(self, widget):
        """Verifica que username vacío se retorna como None."""
        widget.show_add_new_form()
        widget.details_panel.form_widgets['nombre'].setText('Sin User')
        widget.details_panel.form_widgets['username'].setText('')

        data = widget.get_form_data()
        assert data.username is None

    def test_get_form_data_no_password(self, widget):
        """Verifica que password vacío se retorna como None."""
        widget.show_add_new_form()
        widget.details_panel.form_widgets['nombre'].setText('Sin Pass')
        widget.details_panel.form_widgets['password'].setText('')

        data = widget.get_form_data()
        assert data.password is None
        assert data.confirm_password is None

    def test_populate_history(self, widget):
        """Verifica que la tabla de historial se puebla correctamente."""
        widget.show_add_new_form()

        mock_prod1 = MagicMock(spec=["producto_codigo", "descripcion", "cantidad"])
        mock_prod1.producto_codigo = 'P1'
        mock_prod1.descripcion = 'Producto 1'
        mock_prod1.cantidad = 10
        
        mock_hist1 = MagicMock(spec=["id", "fecha_asignacion", "codigo", "productos", "estado"])
        mock_hist1.id = 1
        mock_hist1.fecha_asignacion = datetime(2024, 1, 15, 10, 30)
        mock_hist1.codigo = 'FAB001'
        mock_hist1.productos = [mock_prod1]
        mock_hist1.estado = 'activo'
        
        history = [mock_hist1]
        widget.activity_panel.populate_history(history)
        table = widget.activity_panel.history_table
        assert table.rowCount() == 1
        assert table.item(0, 0).text() == '15/01/2024 10:30'
        assert table.item(0, 1).text() == 'FAB001'
        assert 'P1' in table.item(0, 2).text()

    def test_populate_activity_log(self, widget):
        """Verifica que el log de actividad se puebla correctamente."""
        widget.show_add_new_form()
        log1 = MagicMock(
            spec=[
                "tiempo_inicio",
                "tiempo_fin",
                "duracion_segundos",
                "producto_descripcion",
                "qr_code",
                "incidencias",
                "estado",
            ]
        )
        log1.tiempo_inicio = datetime(2024, 1, 15, 8, 0, 0)
        log1.tiempo_fin = datetime(2024, 1, 15, 9, 30, 0)
        log1.duracion_segundos = 5400
        log1.producto_descripcion = 'Producto A'
        log1.qr_code = 'QR001'
        log1.incidencias = []
        log1.estado = 'completado'
        
        logs = [log1]
        widget.activity_panel.populate_activity_log(logs)
        table = widget.activity_panel.activity_log_table
        assert table.rowCount() == 1
        assert table.item(0, 0).text() == '15/01/2024 08:00:00'

    def test_get_assignment_data(self, widget):
        """Verifica que get_assignment_data retorna datos correctos."""
        widget.show_worker_details(_make_worker_dto(10))
        panel = widget.details_panel

        item = QListWidgetItem("P1 | Producto 1")
        item.setData(Qt.ItemDataRole.UserRole, "P1")
        panel.form_widgets['product_results'].addItem(item)
        panel.form_widgets['product_results'].setCurrentItem(item)
        panel.form_widgets['quantity'].setValue(5)
        panel.form_widgets['of_search'].setText('of-001')

        data = widget.get_assignment_data()
        assert data is not None
        assert data['worker_id'] == 10
        assert data['product_code'] == 'P1'
        assert data['quantity'] == 5
        assert data['orden_fabricacion'] == 'OF-001'

    def test_update_product_search_results(self, widget):
        """Verifica que la búsqueda de productos actualiza la lista."""
        widget.show_add_new_form()

        product_mock = MagicMock(spec=["codigo", "descripcion"])
        product_mock.codigo = 'P99'
        product_mock.descripcion = 'Producto de prueba'

        widget.update_product_search_results([product_mock])
        assert widget.details_panel.form_widgets['product_results'].count() == 1
        assert 'P99' in widget.details_panel.form_widgets['product_results'].item(0).text()

    def test_setup_of_completer(self, widget):
        """Verifica que el completer de OF se configura."""
        widget.show_add_new_form()
        widget.setup_of_completer(['OF-001', 'OF-002'])
        completer = widget.details_panel.form_widgets['of_search'].completer()
        assert completer is not None

    def test_signals_delegation(self, widget, qtbot):
        """Verifica que las señales de los paneles se delegan al orquestador."""
        with qtbot.waitSignal(widget.save_signal, timeout=1000):
            widget.details_panel.save_signal.emit()
            
        with qtbot.waitSignal(widget.cancel_task_signal, timeout=1000) as blocker:
            widget.activity_panel.cancel_task_signal.emit(123)
        assert blocker.args == [123]

    def test_show_incidences_dialog(self, widget):
        """Verifica que el diálogo de incidencias se muestra correctamente."""
        incidences = [MagicMock(spec=["fecha_reporte", "tipo_incidencia", "descripcion", "estado", "adjuntos"])]
        incidences[0].fecha_reporte = datetime.now()
        incidences[0].tipo_incidencia = 'Test'
        incidences[0].descripcion = 'Test'
        incidences[0].estado = 'Abierta'
        incidences[0].adjuntos = []

        with patch('ui.widgets.workers_widget.WorkerIncidenceDialog') as mock_dialog:
            mock_dialog.return_value.exec.return_value = 0
            widget.show_incidences_dialog(incidences)
            mock_dialog.assert_called_once_with(incidences, widget)
            mock_dialog.return_value.exec.assert_called_once_with()
