# -*- coding: utf-8 -*-
import json
from .base import *

class SettingsWidget(QWidget):
    """Widget para la página de Configuración."""
    import_signal = pyqtSignal()
    export_signal = pyqtSignal()
    save_schedule_signal = pyqtSignal()
    add_break_signal = pyqtSignal()
    sync_signal = pyqtSignal()
    change_own_password_signal = pyqtSignal()
    edit_break_signal = pyqtSignal()
    remove_break_signal = pyqtSignal()
    save_hardware_signal = pyqtSignal()
    detect_cameras_signal = pyqtSignal()
    import_tasks_signal = pyqtSignal()

    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setContentsMargins(30, 30, 30, 30)

        title_label = QLabel("Configuración General")
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        title_label.setFont(font)
        main_layout.addWidget(title_label)
        main_layout.addSpacing(20)

        schedule_frame = QFrame()
        schedule_frame.setFrameShape(QFrame.Shape.StyledPanel)
        schedule_layout = QVBoxLayout(schedule_frame)
        schedule_layout.addWidget(QLabel("<b>Configuración del Horario Laboral</b>"))

        form_layout = QFormLayout()
        self.work_start_time = QTimeEdit()
        self.work_end_time = QTimeEdit()
        form_layout.addRow("Hora de Entrada:", self.work_start_time)
        form_layout.addRow("Hora de Salida:", self.work_end_time)
        schedule_layout.addLayout(form_layout)

        breaks_title_layout = QHBoxLayout()
        breaks_title_layout.addWidget(QLabel("Descansos:"))
        breaks_title_layout.addStretch()
        self.add_break_button = QPushButton("Añadir")
        self.edit_break_button = QPushButton("Editar")
        self.remove_break_button = QPushButton("Eliminar")
        breaks_title_layout.addWidget(self.add_break_button)
        breaks_title_layout.addWidget(self.edit_break_button)
        breaks_title_layout.addWidget(self.remove_break_button)
        schedule_layout.addLayout(breaks_title_layout)

        self.breaks_list = QListWidget()
        self.breaks_list.setMaximumHeight(150)
        self.breaks_list.itemSelectionChanged.connect(self._update_break_buttons_state)
        schedule_layout.addWidget(self.breaks_list)

        self.save_schedule_button = QPushButton("Guardar Horario")
        schedule_layout.addWidget(self.save_schedule_button, 0, Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(schedule_frame)
        main_layout.addSpacing(20)

        calendar_frame = QFrame()
        calendar_frame.setFrameShape(QFrame.Shape.StyledPanel)
        calendar_layout = QVBoxLayout(calendar_frame)
        calendar_layout.addWidget(QLabel("<b>Gestión de Días Festivos y Cierres</b>"))
        calendar_controls_layout = QHBoxLayout()
        self.calendar = QCalendarWidget()
        self.add_holiday_button = QPushButton("Añadir Día Seleccionado")
        self.remove_holiday_button = QPushButton("Eliminar Día Seleccionado")
        calendar_controls_layout.addWidget(self.calendar, 2)
        right_calendar_panel = QVBoxLayout()
        right_calendar_panel.addWidget(self.add_holiday_button)
        right_calendar_panel.addWidget(self.remove_holiday_button)
        right_calendar_panel.addStretch()
        calendar_controls_layout.addLayout(right_calendar_panel, 1)
        calendar_layout.addLayout(calendar_controls_layout)
        main_layout.addWidget(calendar_frame)
        main_layout.addSpacing(20)

        backup_frame = QFrame()
        backup_frame.setFrameShape(QFrame.Shape.StyledPanel)
        backup_layout = QVBoxLayout(backup_frame)
        backup_layout.addWidget(QLabel("<b>Copias de Seguridad</b>"))
        desc_label = QLabel("Importa o exporta la base de datos completa de la aplicación.")
        desc_label.setWordWrap(True)
        backup_layout.addWidget(desc_label)
        buttons_layout = QHBoxLayout()
        self.import_button = QPushButton("Importar...")
        self.export_button = QPushButton("Exportar...")
        self.sync_button = QPushButton("Sincronizar...")
        self.import_tasks_button = QPushButton("Importar Datos de Tareas (JSON)")

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.import_button)
        buttons_layout.addWidget(self.export_button)
        buttons_layout.addWidget(self.sync_button)
        buttons_layout.addWidget(self.import_tasks_button)
        backup_layout.addLayout(buttons_layout)
        main_layout.addWidget(backup_frame)

        main_layout.addSpacing(20)
        hardware_frame = QFrame()
        hardware_frame.setFrameShape(QFrame.Shape.StyledPanel)
        hardware_layout = QVBoxLayout(hardware_frame)
        hardware_layout.addWidget(QLabel("<b>Configuración de Hardware (Cámara QR)</b>"))

        hw_form = QFormLayout()
        self.camera_combo = QComboBox()
        hw_form.addRow("Seleccionar Cámara:", self.camera_combo)

        hw_buttons = QHBoxLayout()
        self.detect_cameras_button = QPushButton("Detectar Cámaras")
        self.save_hardware_button = QPushButton("Guardar Configuración de Cámara")
        self.import_tasks_button.clicked.connect(self.import_tasks_signal.emit)
        hw_buttons.addWidget(self.detect_cameras_button)
        hw_buttons.addStretch()
        hw_buttons.addWidget(self.save_hardware_button)

        hardware_layout.addLayout(hw_form)
        hardware_layout.addLayout(hw_buttons)
        main_layout.addWidget(hardware_frame)

        main_layout.addSpacing(20)
        account_frame = QFrame()
        account_frame.setFrameShape(QFrame.Shape.StyledPanel)
        account_layout = QVBoxLayout(account_frame)
        account_layout.addWidget(QLabel("<b>Gestión de Cuenta</b>"))
        self.change_password_button = QPushButton("Cambiar mi Contraseña")
        account_layout.addWidget(self.change_password_button, 0, Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(account_frame)

        main_layout.addStretch()

        self.import_button.clicked.connect(self.import_signal)
        self.export_button.clicked.connect(self.export_signal)
        self.sync_button.clicked.connect(self.sync_signal)
        self.add_holiday_button.clicked.connect(self._on_add_holiday)
        self.remove_holiday_button.clicked.connect(self._on_remove_holiday)
        self.save_schedule_button.clicked.connect(self._on_save_schedule_settings)
        self.add_break_button.clicked.connect(self._on_add_break)
        self.change_password_button.clicked.connect(self.change_own_password_signal)
        self.edit_break_button.clicked.connect(self._on_edit_break)
        self.remove_break_button.clicked.connect(self._on_remove_break)
        self.detect_cameras_button.clicked.connect(self.detect_cameras_signal.emit)
        self.save_hardware_button.clicked.connect(self.save_hardware_signal.emit)

        self._update_break_buttons_state()

    def _update_break_buttons_state(self):
        has_selection = bool(self.breaks_list.selectedItems())
        self.edit_break_button.setEnabled(has_selection)
        self.remove_break_button.setEnabled(has_selection)

    def _on_add_break(self):
        dialog = QDialog(self.controller.view if self.controller else self)
        dialog.setWindowTitle("Añadir Descanso")
        layout = QFormLayout(dialog)

        start_time = QTimeEdit()
        start_time.setDisplayFormat("HH:mm")
        end_time = QTimeEdit()
        end_time.setDisplayFormat("HH:mm")

        layout.addRow("Hora de Inicio:", start_time)
        layout.addRow("Hora de Fin:", end_time)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            start = start_time.time().toString('HH:mm')
            end = end_time.time().toString('HH:mm')
            self.breaks_list.addItem(f"{start} - {end}")

    def _on_edit_break(self):
        """Edita el descanso seleccionado."""
        current_item = self.breaks_list.currentItem()
        if not current_item:
            return

        text = current_item.text()
        if ' - ' not in text:
            return

        start_str, end_str = text.split(' - ')

        dialog = QDialog(self.controller.view if self.controller else self)
        dialog.setWindowTitle("Editar Descanso")
        layout = QFormLayout(dialog)

        start_time = QTimeEdit()
        start_time.setDisplayFormat("HH:mm")
        start_time.setTime(QTime.fromString(start_str, "HH:mm"))

        end_time = QTimeEdit()
        end_time.setDisplayFormat("HH:mm")
        end_time.setTime(QTime.fromString(end_str, "HH:mm"))

        layout.addRow("Hora de Inicio:", start_time)
        layout.addRow("Hora de Fin:", end_time)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_start = start_time.time().toString('HH:mm')
            new_end = end_time.time().toString('HH:mm')
            current_item.setText(f"{new_start} - {new_end}")

    def _on_remove_break(self):
        """Elimina el descanso seleccionado."""
        row = self.breaks_list.currentRow()
        if row >= 0:
            self.breaks_list.takeItem(row)
            self._update_break_buttons_state()

    def _on_add_holiday(self):
        """Añade el día seleccionado a la lista de festivos."""
        if not self.controller:
            return
            
        selected_date = self.calendar.selectedDate()
        date_str = selected_date.toString(Qt.DateFormat.ISODate)
        
        holidays_json = self.controller.model.db.config_repo.get_setting('holidays', '[]')
        try:
            holidays = json.loads(holidays_json)
        except json.JSONDecodeError:
            holidays = []
            
        if date_str not in holidays:
            holidays.append(date_str)
            self.controller.model.db.config_repo.set_setting('holidays', json.dumps(holidays))
            self._highlight_holidays(holidays)

    def _on_remove_holiday(self):
        """Elimina el día seleccionado de la lista de festivos."""
        if not self.controller:
            return

        selected_date = self.calendar.selectedDate()
        date_str = selected_date.toString(Qt.DateFormat.ISODate)

        holidays_json = self.controller.model.db.config_repo.get_setting('holidays', '[]')
        try:
            holidays = json.loads(holidays_json)
        except json.JSONDecodeError:
            holidays = []

        if date_str in holidays:
            holidays.remove(date_str)
            self.controller.model.db.config_repo.set_setting('holidays', json.dumps(holidays))
            
            # Limpiar formato de fecha para ese día
            clean_format = QTextCharFormat()
            self.calendar.setDateTextFormat(selected_date, clean_format)
            
            self._highlight_holidays(holidays)

    def _highlight_holidays(self, holidays):
        """Marca los días festivos en el calendario con color rojo."""
        holiday_format = QTextCharFormat()
        holiday_format.setForeground(QBrush(QColor("white")))
        holiday_format.setBackground(QBrush(QColor("#e74c3c")))  # Rojo
        
        for date_str in holidays:
            qdate = QDate.fromString(date_str, Qt.DateFormat.ISODate)
            self.calendar.setDateTextFormat(qdate, holiday_format)

    def _on_save_schedule_settings(self):
        if not self.controller or not hasattr(self.controller, 'model') or not hasattr(self.controller, 'schedule_manager'):
            print("Error: Controller or necessary attributes not set.")
            return

        settings_page = self
        start_time = settings_page.work_start_time.time().toString('HH:mm')
        end_time = settings_page.work_end_time.time().toString('HH:mm')

        self.controller.model.db.config_repo.set_setting('work_start_time', start_time)
        self.controller.model.db.config_repo.set_setting('work_end_time', end_time)

        breaks = []
        for i in range(settings_page.breaks_list.count()):
            item_text = settings_page.breaks_list.item(i).text()
            if ' - ' in item_text:
                start, end = item_text.split(' - ')
                breaks.append({"start": start.strip(), "end": end.strip()})

        self.controller.model.db.config_repo.set_setting('breaks', json.dumps(breaks))
        self.controller.schedule_manager.reload_config(self.controller.model.db)

        if hasattr(self.controller, 'view'):
            self.controller.view.show_message("Éxito", "Horario completo guardado y aplicado.", "info")

    def _load_schedule_settings(self):
        if not self.controller or not hasattr(self.controller, 'model'):
            print("Error: Controller or model not set.")
            return

        settings_page = self
        start_time_str = self.controller.model.db.config_repo.get_setting('work_start_time', '08:00')
        end_time_str = self.controller.model.db.config_repo.get_setting('work_end_time', '15:15')

        settings_page.work_start_time.setTime(QTime.fromString(start_time_str, 'HH:mm'))
        settings_page.work_end_time.setTime(QTime.fromString(end_time_str, 'HH:mm'))

        breaks_json = self.controller.model.db.config_repo.get_setting('breaks', '[{"start": "12:00", "end": "13:00"}]')
        try:
            breaks = json.loads(breaks_json)
            settings_page.breaks_list.clear()
            for brk in breaks:
                start = brk.get('start', '??:??')
                end = brk.get('end', '??:??')
                settings_page.breaks_list.addItem(f"{start} - {end}")
            settings_page.breaks_list.addItem(f"{start} - {end}")
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Warning: Error loading breaks: {e}")
            settings_page.breaks_list.clear()
            settings_page.breaks_list.addItem("12:00 - 13:00")

        # Cargar festivos
        holidays_json = self.controller.model.db.config_repo.get_setting('holidays', '[]')
        try:
            holidays = json.loads(holidays_json)
            self._highlight_holidays(holidays)
        except Exception as e:
            print(f"Warning: Error loading holidays: {e}")

    def showEvent(self, event):
        super().showEvent(event)
        self._load_schedule_settings()

    def set_controller(self, controller):
        self.controller = controller
