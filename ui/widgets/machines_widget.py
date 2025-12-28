# -*- coding: utf-8 -*-
from .base import *

class MachinesWidget(QWidget):
    """Widget para gestionar la base de datos de máquinas (CRUD)."""
    save_signal = pyqtSignal()
    manage_groups_signal = pyqtSignal(int, str)
    add_maintenance_signal = pyqtSignal(int)
    delete_signal = pyqtSignal(int)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.current_machine_id = None
        self.form_widgets = {}

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)

        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("<b>Máquinas Existentes</b>"))

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Filtrar máquinas por nombre...")
        self.search_bar.textChanged.connect(self._filter_machines_list)
        left_layout.addWidget(self.search_bar)

        self.machines_list = QListWidget()
        left_layout.addWidget(self.machines_list)
        self.add_button = QPushButton("Añadir Nueva Máquina")
        left_layout.addWidget(self.add_button)

        right_panel = QFrame()
        self.details_container_layout = QVBoxLayout(right_panel)

        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)

        self.clear_details_area()

    def _filter_machines_list(self):
        filter_text = self.search_bar.text().lower()
        for i in range(self.machines_list.count()):
            item = self.machines_list.item(i)
            item.setHidden(filter_text not in item.text().lower())

    def populate_list(self, machines_data):
        self.machines_list.blockSignals(True)
        self.machines_list.clear()
        for machine in machines_data:
            item_text = f"{machine.nombre} {'(Activa)' if machine.activa else '(Inactiva)'}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, machine.id)
            if not machine.activa: item.setForeground(QColor("gray"))
            self.machines_list.addItem(item)
        self.machines_list.blockSignals(False)
        self.clear_details_area()
        self._filter_machines_list()

    def clear_details_area(self):
        while self.details_container_layout.count():
            child = self.details_container_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        self.form_widgets = {}
        self.current_machine_id = None
        placeholder = QLabel("Seleccione una máquina de la lista para ver sus detalles o añada una nueva.")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setWordWrap(True)
        self.details_container_layout.addWidget(placeholder)

    def _create_form_widgets(self):
        self.clear_details_area()
        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)
        self.form_widgets['title'] = QLabel()
        font = self.form_widgets['title'].font()
        font.setBold(True); font.setPointSize(14)
        self.form_widgets['title'].setFont(font)
        container_layout.addWidget(self.form_widgets['title'])

        tab_widget = QTabWidget()
        container_layout.addWidget(tab_widget, 1)

        details_tab = QWidget()
        form_layout = QFormLayout(details_tab)
        self.form_widgets['nombre'] = QLineEdit()
        self.form_widgets['departamento'] = QComboBox()
        self.form_widgets['departamento'].addItems(["Mecánica", "Electrónica", "Montaje"])
        self.form_widgets['tipo_proceso'] = QComboBox()
        self.form_widgets['tipo_proceso'].setEditable(True)
        if self.controller: self.form_widgets['tipo_proceso'].addItems(self.controller.model.get_distinct_machine_processes())
        self.form_widgets['activa'] = QCheckBox("Máquina en activo")

        form_layout.addRow("Nombre Máquina:", self.form_widgets['nombre'])
        form_layout.addRow("Departamento:", self.form_widgets['departamento'])
        form_layout.addRow("Tipo de Proceso:", self.form_widgets['tipo_proceso'])
        form_layout.addRow(self.form_widgets['activa'])
        tab_widget.addTab(details_tab, "Detalles")

        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        history_layout.addWidget(QLabel("<b>Historial de Mantenimientos</b>"))
        self.form_widgets['maintenance_table'] = QTableWidget()
        self.form_widgets['maintenance_table'].setColumnCount(2)
        self.form_widgets['maintenance_table'].setHorizontalHeaderLabels(["Fecha", "Notas"])
        self.form_widgets['maintenance_table'].horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.form_widgets['maintenance_table'].setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        history_layout.addWidget(self.form_widgets['maintenance_table'])
        add_btn = QPushButton("Añadir Registro de Mantenimiento")
        add_btn.clicked.connect(lambda: self.add_maintenance_signal.emit(self.current_machine_id))
        history_layout.addWidget(add_btn, 0, Qt.AlignmentFlag.AlignRight)
        tab_widget.addTab(history_tab, "📊 Historial")

        button_layout = QHBoxLayout()
        save_btn = QPushButton("Guardar Cambios"); delete_btn = QPushButton("Eliminar Máquina")
        manage_btn = QPushButton("Gestionar Grupos de Preparación")
        self.form_widgets['manage_groups_button'] = manage_btn
        self.form_widgets['delete_button'] = delete_btn
        save_btn.clicked.connect(self.save_signal.emit)
        delete_btn.clicked.connect(lambda: self.delete_signal.emit(self.current_machine_id))
        button_layout.addStretch()
        button_layout.addWidget(delete_btn); button_layout.addWidget(manage_btn); button_layout.addWidget(save_btn)
        container_layout.addLayout(button_layout)
        self.details_container_layout.addWidget(container_widget)

    def show_machine_details(self, machine_data):
        self._create_form_widgets()
        self.current_machine_id = machine_data.id
        self.form_widgets['title'].setText("Editar Máquina")
        self.form_widgets['nombre'].setText(machine_data.nombre)
        self.form_widgets['departamento'].setCurrentText(machine_data.departamento)
        self.form_widgets['tipo_proceso'].setCurrentText(machine_data.tipo_proceso or "")
        self.form_widgets['activa'].setChecked(bool(machine_data.activa))
        self.form_widgets['manage_groups_button'].setVisible(True)
        self.form_widgets['delete_button'].setVisible(True)
        self.form_widgets['manage_groups_button'].clicked.connect(lambda: self.manage_groups_signal.emit(self.current_machine_id, machine_data.nombre))

    def show_add_new_form(self):
        self._create_form_widgets()
        self.current_machine_id = None
        self.form_widgets['title'].setText("Añadir Nueva Máquina")
        self.form_widgets['activa'].setChecked(True)
        # Ocultar pestañas de historial para nueva máquina
        self.form_widgets['title'].parent().findChild(QTabWidget).setTabVisible(1, False)
        self.form_widgets['manage_groups_button'].setVisible(False)
        self.form_widgets['delete_button'].setVisible(False)
        self.form_widgets['nombre'].setFocus()

    def get_form_data(self):
        if not self.form_widgets: return None
        return {
            "nombre": self.form_widgets['nombre'].text().strip(),
            "departamento": self.form_widgets['departamento'].currentText(),
            "tipo_proceso": self.form_widgets['tipo_proceso'].currentText().strip(),
            "activa": self.form_widgets['activa'].isChecked()
        }

    def populate_history_tables(self, maintenance_history):
        table = self.form_widgets.get('maintenance_table')
        if not table: return
        table.setRowCount(0)
        for maintenance in maintenance_history:
            row = table.rowCount()
            table.insertRow(row)
            fecha = maintenance.maintenance_date
            fecha_str = fecha.strftime('%d/%m/%Y') if isinstance(fecha, (date, datetime)) else str(fecha)
            table.setItem(row, 0, QTableWidgetItem(fecha_str))
            table.setItem(row, 1, QTableWidgetItem(str(maintenance.notes)))
