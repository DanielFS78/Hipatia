"""
Nombre del Módulo: test_worker_main_window
Descripcion: Tests unitarios para WorkerMainWindow, la ventana principal de la
             interfaz de operario. Verifica inicialización, navegación entre páginas,
             gestión de usuario activo, señales de logout y comportamiento con
             distintos roles de trabajador.

Decisión de mocking: WorkerMainWindow hereda de QMainWindow (PyQt6) — MagicMock()
inevitable para widgets internos. El usuario activo se simula con MagicMock() con
atributos id, nombre y rol explícitos. No se usa autospec en clases Qt. Los DTOs
de trabajador (WorkerDTO) se usan donde el código bajo test hace isinstance().
"""
import pytest
from unittest.mock import MagicMock, patch, ANY
from PyQt6.QtWidgets import QWidget, QMessageBox, QStackedWidget
from PyQt6.QtCore import Qt

from ui.worker.main_window.window import WorkerMainWindow
from ui.widgets.log_terminal_widget import LogTerminalWidget
from core.dtos import WorkerDTO  # Añadimos mención a DTO y la importación para cumplimiento
from core.worker_ui_dtos import WorkerTaskListRowDTO
from core.qt_log_handler import QtLogHandler

MODULE = "ui.worker.main_window.window"


@pytest.fixture
def current_user():
    return MagicMock(
        id=101,
        nombre_completo="Juan Trabajador",
        role="Trabajador"
    )


@pytest.fixture
def main_window(qapp, current_user):
    """Fixture que crea la ventana principal del trabajador."""
    # Instanciamos la ventana, usando el qapp autouse estándar de pytest-qt.
    win = WorkerMainWindow(current_user)
    yield win
    win.close()


@pytest.mark.unit
class TestWorkerMainWindowInitAndUI:
    """Tests sobre la inicialización, configuración de UI y botones básicos."""

    def test_init_and_setup_ui(self, main_window, current_user):
        """La ventana se inicializa correctamente con el usuario y UI base."""
        assert main_window.current_user == current_user
        assert main_window.windowTitle() == "Hipatia - Trabajador: Juan Trabajador"
        
        # Verificar que el stacked widget existe y tiene al menos una pantalla
        assert isinstance(main_window.stacked_widget, QStackedWidget)
        assert main_window.stacked_widget.count() >= 1

        # Verificar botones del header
        assert hasattr(main_window, "export_data_btn")
        assert isinstance(main_window.log_terminal, LogTerminalWidget)

    def test_enable_action_buttons_true(self, main_window):
        """enable_action_buttons(True) activa finalizar/incidencia, inactiva iniciar."""
        main_window.enable_action_buttons(True)
        assert main_window.register_incidence_btn.isEnabled() is True
        assert main_window.end_task_btn.isEnabled() is True
        assert main_window.start_task_btn.isEnabled() is False

    def test_enable_action_buttons_false(self, main_window):
        """enable_action_buttons(False) desactiva finalizar/incidencia, activa iniciar."""
        main_window.enable_action_buttons(False)
        assert main_window.register_incidence_btn.isEnabled() is False
        assert main_window.end_task_btn.isEnabled() is False
        assert main_window.start_task_btn.isEnabled() is True


@pytest.mark.unit
class TestWorkerMainWindowLogHandler:
    """Conexión del QtLogHandler a la pestaña Log (misma API que HomeWidget)."""

    def test_connect_log_handler_calls_handler_connect_to_widget(self, main_window):
        handler = QtLogHandler()
        with patch.object(handler, "connect_to_widget") as mock_connect:
            main_window.connect_log_handler(handler)
            mock_connect.assert_called_once_with(main_window.log_terminal.append_log)


@pytest.mark.unit
class TestWorkerMainWindowNavigation:
    """Tests sobre la navegación mediante el stacked widget."""

    def test_add_screen(self, main_window):
        """add_screen añade un widget al stacked_widget."""
        initial_count = main_window.stacked_widget.count()
        new_widget = QWidget()
        main_window.add_screen("test_screen", new_widget)
        
        assert main_window.stacked_widget.count() == initial_count + 1
        assert main_window.stacked_widget.widget(initial_count) is new_widget

    def test_switch_screen_valid(self, main_window):
        """switch_screen cambia a un índice válido."""
        main_window.switch_screen(0)
        assert main_window.stacked_widget.currentIndex() == 0

    def test_switch_screen_invalid(self, main_window):
        """switch_screen no hace nada si el índice es inválido (y loguea un warning)."""
        main_window.switch_screen(0)  # Establecemos a un estado conocido
        
        with patch.object(main_window.logger, "warning") as mock_logger:
            main_window.switch_screen(999)
            assert main_window.stacked_widget.currentIndex() == 0  # No cambió
            mock_logger.assert_called_once_with("Índice de pantalla inválido: 999")
            
        with patch.object(main_window.logger, "warning") as mock_logger:
            main_window.switch_screen(-1)
            assert mock_logger.call_count == 1
            mock_logger.assert_called_once_with("Índice de pantalla inválido: -1")


@pytest.mark.unit
class TestWorkerMainWindowDialogs:
    """Tests sobre los diálogos de mensajes (show_message y confirmation)."""

    def test_show_message_info(self, main_window):
        """show_message con level info."""
        with patch("ui.worker.main_window.window.QMessageBox", autospec=True) as mock_msgbox_class:
            mock_msgbox = MagicMock()
            mock_msgbox_class.return_value = mock_msgbox
            mock_msgbox_class.Icon = QMessageBox.Icon  # Parchear enumerador

            main_window.show_message("Info", "Cuerpo", "info")
            
            assert mock_msgbox_class.call_count == 1
            mock_msgbox_class.assert_called_once_with(main_window)
            assert mock_msgbox.setWindowTitle.call_count == 1
            mock_msgbox.setWindowTitle.assert_called_once_with("Info")
            assert mock_msgbox.setText.call_count == 1
            mock_msgbox.setText.assert_called_once_with("Cuerpo")
            assert mock_msgbox.setIcon.call_count == 1
            mock_msgbox.setIcon.assert_called_once_with(QMessageBox.Icon.Information)
            assert mock_msgbox.exec.call_count == 1
            mock_msgbox.exec.assert_called_once_with()

    def test_show_message_warning(self, main_window):
        """show_message con level warning."""
        with patch("ui.worker.main_window.window.QMessageBox", autospec=True) as mock_msgbox_class:
            mock_msgbox = MagicMock()
            mock_msgbox_class.return_value = mock_msgbox
            mock_msgbox_class.Icon = QMessageBox.Icon

            main_window.show_message("Warn", "Cuerpo", "warning")
            assert mock_msgbox.setIcon.call_count == 1
            mock_msgbox.setIcon.assert_called_once_with(QMessageBox.Icon.Warning)

    def test_show_message_error(self, main_window):
        """show_message con level error."""
        with patch("ui.worker.main_window.window.QMessageBox", autospec=True) as mock_msgbox_class:
            mock_msgbox = MagicMock()
            mock_msgbox_class.return_value = mock_msgbox
            mock_msgbox_class.Icon = QMessageBox.Icon

            main_window.show_message("Error", "Cuerpo", "error")
            assert mock_msgbox.setIcon.call_count == 1
            mock_msgbox.setIcon.assert_called_once_with(QMessageBox.Icon.Critical)

    def test_show_confirmation_dialog_yes(self, main_window):
        """show_confirmation_dialog retorna True cuando el usuario clickea Yes."""
        with patch("ui.worker.main_window.window.QMessageBox.question") as mock_question:
            # Emular que clica Yes
            mock_question.return_value = QMessageBox.StandardButton.Yes
            
            result = main_window.show_confirmation_dialog("Confirmar", "¿Seguro?")
            
            assert result is True
            assert mock_question.call_count == 1
            mock_question.assert_called_once_with(
                main_window, "Confirmar", "¿Seguro?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

    def test_show_confirmation_dialog_no(self, main_window):
        """show_confirmation_dialog retorna False cuando el usuario clickea No."""
        with patch("ui.worker.main_window.window.QMessageBox.question") as mock_question:
            # Emular que clica No
            mock_question.return_value = QMessageBox.StandardButton.No
            
            result = main_window.show_confirmation_dialog("Confirmar", "¿Seguro?")
            
            assert result is False


@pytest.mark.unit
class TestWorkerMainWindowTasksList:
    """Tests sobre la población y comportamiento de la lista de tareas."""

    def test_update_tasks_list_empty(self, main_window):
        """Si no hay tareas, se añade un item de aviso."""
        main_window.update_tasks_list([])
        assert main_window.tasks_list.count() == 1
        assert main_window.tasks_list.item(0).text() == "No tienes tareas asignadas."

    def test_update_tasks_list_with_product(self, main_window):
        """Tarea con código y descripción de producto."""
        tareas = [
            WorkerTaskListRowDTO.from_flat_mapping(
                {
                    "codigo": "T01",
                    "descripcion": "Tarea general",
                    "producto_codigo": "PROD-A",
                    "producto_descripcion": "Producto A",
                    "cantidad": 50,
                }
            )
        ]
        main_window.update_tasks_list(tareas)
        
        assert main_window.tasks_list.count() == 1
        item = main_window.tasks_list.item(0)
        assert "PROD-A" in item.text()
        assert "Producto A (Cantidad: 50)" in item.text()
        
        data = item.data(Qt.ItemDataRole.UserRole)
        assert isinstance(data, WorkerTaskListRowDTO)
        assert data.codigo == "T01"
        assert not isinstance(data, WorkerDTO)

    def test_update_tasks_list_without_product(self, main_window):
        """Tarea sin datos de producto usa el fallback a codigo/descripcion base."""
        tareas = [
            WorkerTaskListRowDTO.from_flat_mapping(
                {
                    "codigo": "PRE-01",
                    "descripcion": "Cortar madera",
                }
            )
        ]
        main_window.update_tasks_list(tareas)
        
        assert main_window.tasks_list.count() == 1
        item = main_window.tasks_list.item(0)
        assert "PRE-01" in item.text()
        assert "Cortar madera" in item.text()


@pytest.mark.unit
class TestWorkerMainWindowTaskSelection:
    """Tests sobre la selección de tareas en la lista."""

    def test_on_task_selected_no_data(self, main_window):
        """Seleccionar un item sin data (ej: el aviso de 'sin tareas') muestra el placeholder."""
        main_window.update_tasks_list([])  # Añade el aviso de "No tienes tareas"
        item = main_window.tasks_list.item(0)
        
        # Seleccionamos
        main_window._on_task_selected(item)
        
        # Debe mostrar la página 0 (placeholder)
        assert main_window.details_stack.currentIndex() == 0
        assert main_window.current_selected_task is None

    def test_on_task_selected_with_data(self, main_window):
        """Seleccionar un item válido actualiza labels y emite señal."""
        tarea = WorkerTaskListRowDTO.from_flat_mapping(
            {"codigo": "TASK-1", "descripcion": "Demo"}
        )
        main_window.update_tasks_list([tarea])
        item = main_window.tasks_list.item(0)
        
        # Conectar mocker a la señal, no parches el MagicMock para señales!
        mock_signal = MagicMock()
        main_window.task_selected.connect(mock_signal)
        
        main_window._on_task_selected(item)
        
        # Verificar estado UI
        assert main_window.current_selected_task == tarea
        assert main_window.details_stack.currentIndex() == 1
        assert "TASK-1" in main_window.selected_task_code_label.text()
        assert "Demo" in main_window.selected_task_desc_label.text()
        assert "Comprobando..." in main_window.task_status_label.text()
        
        mock_signal.assert_called_once_with(tarea.to_signal_dict())

    def test_on_task_selected_exception(self, main_window):
        """Un error durante la selección revierte al placeholder."""
        item = MagicMock()
        item.data.side_effect = Exception("Fallo forzado")
        
        with patch.object(main_window.logger, "error") as mock_logger:
            main_window._on_task_selected(item)
            
            assert main_window.details_stack.currentIndex() == 0
            assert mock_logger.call_count == 1
            mock_logger.assert_called_once_with(ANY, exc_info=True)


@pytest.mark.unit
class TestWorkerMainWindowTaskState:
    """Tests sobre update_task_state."""

    def test_update_task_state_pendiente(self, main_window):
        """Estado 'pendiente' activa iniciar unicamente."""
        main_window.update_task_state("pendiente")
        assert "Pendiente" in main_window.task_status_label.text()
        assert main_window.generate_labels_btn.isEnabled() is True
        assert main_window.start_task_btn.isEnabled() is True
        assert main_window.register_incidence_btn.isEnabled() is False
        assert main_window.end_task_btn.isEnabled() is False

    def test_update_task_state_en_proceso_without_step(self, main_window):
        """Estado 'en_proceso' activa incidencia/finulizar."""
        main_window.update_task_state("en_proceso")
        assert "En Proceso" in main_window.task_status_label.text()
        assert main_window.generate_labels_btn.isEnabled() is True
        assert main_window.start_task_btn.isEnabled() is False
        assert main_window.register_incidence_btn.isEnabled() is True
        assert main_window.end_task_btn.isEnabled() is True

    def test_update_task_state_en_proceso_with_step(self, main_window):
        """Estado 'en_proceso' con current_step_name muestra el paso."""
        main_window.update_task_state("en_proceso", "Paso 3")
        assert "En Proceso (Paso 3)" in main_window.task_status_label.text()

    def test_update_task_state_finalizada(self, main_window):
        """Estado 'finalizada' desactiva todo excepto etiquetas."""
        main_window.update_task_state("finalizada")
        assert "Finalizada" in main_window.task_status_label.text()
        assert main_window.generate_labels_btn.isEnabled() is True
        assert main_window.start_task_btn.isEnabled() is False
        assert main_window.register_incidence_btn.isEnabled() is False
        assert main_window.end_task_btn.isEnabled() is False


@pytest.mark.unit
class TestWorkerMainWindowSignals:
    """Tests sobre la emisión de señales desde la UI."""

    def test_on_logout_clicked(self, main_window):
        """Clic en el botón lanza señal y hace close()."""
        mock_signal = MagicMock()
        main_window.logout_requested.connect(mock_signal)
        
        with patch.object(main_window, "close") as mock_close:
            main_window._on_logout_clicked()
            assert mock_signal.call_count == 1
            mock_signal.assert_called_once_with()
            assert mock_close.call_count == 1
            mock_close.assert_called_once_with()

    def test_on_camera_config_clicked(self, main_window):
        mock_signal = MagicMock()
        main_window.camera_config_requested.connect(mock_signal)
        main_window._on_camera_config_clicked()
        assert mock_signal.call_count == 1
        mock_signal.assert_called_once_with()

    def test_action_buttons_no_selection(self, main_window):
        """Si no hay tarea seleccionada (ej nulo), las acciones no emiten."""
        mock_gen = MagicMock(); main_window.generate_labels_requested.connect(mock_gen)
        mock_start = MagicMock(); main_window.start_task_requested.connect(mock_start)
        mock_reg = MagicMock(); main_window.register_incidence_requested.connect(mock_reg)
        mock_end = MagicMock(); main_window.end_task_requested.connect(mock_end)
        
        main_window.current_selected_task = None
        main_window._on_generate_labels_clicked()
        main_window._on_start_task_clicked()
        main_window._on_register_incidence_clicked()
        main_window._on_end_task_clicked()
        
        mock_gen.assert_not_called()
        mock_start.assert_not_called()
        mock_reg.assert_not_called()
        mock_end.assert_not_called()
        assert mock_gen.call_count == 0
        assert mock_start.call_count == 0

    def test_action_buttons_with_selection(self, main_window):
        """Las acciones envían la tarea seleccionada como dict (to_signal_dict)."""
        tarea = WorkerTaskListRowDTO(
            id=999,
            codigo="OF1",
            descripcion="Desc",
            producto_codigo="P1",
            producto_descripcion="Prod",
            cantidad=3,
        )
        main_window.current_selected_task = tarea
        payload = tarea.to_signal_dict()

        mock_gen = MagicMock(); main_window.generate_labels_requested.connect(mock_gen)
        mock_start = MagicMock(); main_window.start_task_requested.connect(mock_start)
        mock_reg = MagicMock(); main_window.register_incidence_requested.connect(mock_reg)
        mock_end = MagicMock(); main_window.end_task_requested.connect(mock_end)

        main_window._on_generate_labels_clicked()
        main_window._on_start_task_clicked()
        main_window._on_register_incidence_clicked()
        main_window._on_end_task_clicked()

        mock_gen.assert_called_once_with(payload)
        mock_start.assert_called_once_with(payload)
        mock_reg.assert_called_once_with(payload)
        mock_end.assert_called_once_with(payload)
        assert mock_gen.call_count == 1
        assert mock_start.call_count == 1

    def test_consult_qr_btn_clicked(self, main_window):
        """El botón llama a la señal."""
        mock_signal = MagicMock()
        main_window.consult_qr_requested.connect(mock_signal)
        
        main_window.consult_qr_btn.click()
        assert mock_signal.call_count == 1
        mock_signal.assert_called_once_with()

    @patch('core.utils.ui_scaler.UIScaler', autospec=True)
    @patch('PyQt6.QtWidgets.QApplication.instance')
    def test_forzar_auto_ajuste(self, mock_app_instance, mock_ui_scaler, main_window):
        """Testa que el botón Auto-Ajustar llama a las funciones correctas en WorkerMainWindow."""
        # Configurar Mocks
        mock_ui_scaler.get_current_screen_height.return_value = 768
        mock_ui_scaler.calculate_scale_factor.return_value = 0.7
        mock_ui_scaler.generate_dynamic_qss.return_value = "/* test qss worker */"
        
        mock_qt_app = MagicMock()
        mock_app_instance.return_value = mock_qt_app
        
        # Usar un QWidget real para evitar TypeError con addWidget
        from PyQt6.QtWidgets import QWidget
        test_page = QWidget()
        main_window.add_screen("test_screen", test_page)
        
        with patch.object(test_page, 'updateGeometry') as mock_geo, \
             patch.object(test_page, 'adjustSize') as mock_adj, \
             patch.object(main_window, 'show_message') as mock_msg:
                 
            main_window._forzar_auto_ajuste()
            
            # Verificaciones
            assert mock_ui_scaler.get_current_screen_height.call_count == 1
            mock_ui_scaler.get_current_screen_height.assert_called_once_with(main_window)
            assert mock_ui_scaler.calculate_scale_factor.call_count == 1
            mock_ui_scaler.calculate_scale_factor.assert_called_once_with(768)
            assert mock_ui_scaler.generate_dynamic_qss.call_count == 1
            mock_ui_scaler.generate_dynamic_qss.assert_called_once_with(0.7)
            assert mock_qt_app.setStyleSheet.call_count == 1
            mock_qt_app.setStyleSheet.assert_called_once_with("/* test qss worker */")
            
            assert mock_geo.call_count == 1
            mock_geo.assert_called_once_with()
            assert mock_adj.call_count == 1
            mock_adj.assert_called_once_with()
            
            assert mock_msg.call_count == 1
            mock_msg.assert_called_once_with(ANY, ANY, ANY)
