# -*- coding: utf-8 -*-
from .base import *

class AddProductWidget(QWidget):
    """Widget para añadir un nuevo producto con formulario dinámico."""
    manage_subs_signal = pyqtSignal(list)
    manage_procesos_signal = pyqtSignal(list)

    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller
        self.subfabricaciones_temp = []
        self.procesos_mecanicos_temp = []
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title_label = QLabel("Añadir Nuevo Producto")
        font = QFont(); font.setPointSize(20); font.setBold(True)
        title_label.setFont(font)
        main_layout.addWidget(title_label, 0, Qt.AlignmentFlag.AlignHCenter)

        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)

        form_container = QFrame()
        form_main_layout = QVBoxLayout(form_container)
        content_layout.addWidget(form_container, 1)

        top_form_layout = QFormLayout()
        self.codigo_entry = QLineEdit(); self.descripcion_entry = QLineEdit()
        top_form_layout.addRow("Código Producto:", self.codigo_entry)
        top_form_layout.addRow("Descripción:", self.descripcion_entry)
        form_main_layout.addLayout(top_form_layout)

        self.departamento_menu = QComboBox()
        self.departamento_menu.addItems(["Mecánica", "Electrónica", "Montaje"])
        self.donde_textbox = QTextEdit(); self.donde_textbox.setFixedHeight(80)

        other_form_layout = QFormLayout()
        other_form_layout.addRow("Departamento:", self.departamento_menu)
        other_form_layout.addRow("Dónde se encuentra/ubica:", self.donde_textbox)
        form_main_layout.addLayout(other_form_layout)

        self.sub_switch = QCheckBox("¿Tiene subfabricaciones?")
        self.sub_switch.toggled.connect(self._toggle_sub_mode)
        form_main_layout.addWidget(self.sub_switch, 0, Qt.AlignmentFlag.AlignHCenter)

        self.dynamic_form_layout = QFormLayout()
        self.trabajador_menu = QComboBox()
        self.trabajador_menu.addItems(["Tipo 1", "Tipo 2", "Tipo 3"])
        self.tiempo_optimo_entry = QLineEdit()
        self.add_sub_button = QPushButton("Añadir/Editar Subfabricaciones")
        self.add_sub_button.clicked.connect(self._on_manage_subs)
        self.add_procesos_button = QPushButton("Gestionar Procesos Mecánicos")
        self.add_procesos_button.clicked.connect(self._on_manage_procesos)
        self.dynamic_form_layout.addRow("Tipo de Trabajador:", self.trabajador_menu)
        self.dynamic_form_layout.addRow("Tiempo Óptimo (min):", self.tiempo_optimo_entry)
        self.dynamic_form_layout.addRow(self.add_sub_button)
        self.dynamic_form_layout.addRow(self.add_procesos_button)
        form_main_layout.addLayout(self.dynamic_form_layout)

        list_container = QFrame()
        list_layout = QVBoxLayout(list_container)
        content_layout.addWidget(list_container, 2)
        list_label = QLabel("Productos Existentes (Últimos Añadidos)")
        list_font = list_label.font(); list_font.setBold(True); list_label.setFont(list_font)
        list_layout.addWidget(list_label)
        self.existing_products_list = QListWidget()
        list_layout.addWidget(self.existing_products_list)

        self.save_button = QPushButton("Guardar Producto")
        self.save_button.setMinimumHeight(40)
        form_main_layout.addStretch()
        form_main_layout.addWidget(self.save_button, 0, Qt.AlignmentFlag.AlignRight)
        self._toggle_sub_mode()

    def set_controller(self, controller):
        self.controller = controller

    def update_existing_products_list(self, products):
        self.existing_products_list.clear()
        if not products:
            self.existing_products_list.addItem("No hay productos en la base de datos.")
            return
        for product in products:
            self.existing_products_list.addItem(f"{product.codigo} | {product.descripcion}")

    def _toggle_sub_mode(self):
        has_subs = self.sub_switch.isChecked()
        self.trabajador_menu.setEnabled(not has_subs)
        self.tiempo_optimo_entry.setVisible(not has_subs)
        self.add_sub_button.setVisible(has_subs)
        self.dynamic_form_layout.labelForField(self.tiempo_optimo_entry).setVisible(not has_subs)
        self.dynamic_form_layout.labelForField(self.trabajador_menu).setVisible(not has_subs)

    def _on_manage_subs(self):
        self.manage_subs_signal.emit(self.subfabricaciones_temp)

    def _on_manage_procesos(self):
        self.manage_procesos_signal.emit(self.procesos_mecanicos_temp)

    def get_data(self):
        data = {
            "codigo": self.codigo_entry.text().strip(),
            "descripcion": self.descripcion_entry.text().strip(),
            "departamento": self.departamento_menu.currentText(),
            "donde": self.donde_textbox.toPlainText().strip(),
            "tiene_subfabricaciones": 1 if self.sub_switch.isChecked() else 0,
            "tiempo_optimo": 0, "tipo_trabajador": 0, "sub_partes": self.subfabricaciones_temp,
            "procesos_mecanicos": getattr(self, 'procesos_mecanicos_temp', [])
        }
        if data["tiene_subfabricaciones"] == 0:
            data["tiempo_optimo"] = self.tiempo_optimo_entry.text().replace(",", ".")
            data["tipo_trabajador"] = self.trabajador_menu.currentText().split(" ")[1]
        return data

    def clear_form(self):
        self.codigo_entry.clear(); self.descripcion_entry.clear(); self.donde_textbox.clear()
        self.tiempo_optimo_entry.clear(); self.departamento_menu.setCurrentIndex(0)
        self.trabajador_menu.setCurrentIndex(0); self.sub_switch.setChecked(False)
        self.subfabricaciones_temp = []; self.procesos_mecanicos_temp = []


class ProductsWidget(QWidget):
    """Widget para editar y visualizar Productos."""
    save_product_signal = pyqtSignal(str)
    delete_product_signal = pyqtSignal(str)
    manage_subs_signal = pyqtSignal()
    manage_procesos_signal = pyqtSignal()
    manage_details_signal = pyqtSignal(str)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.current_subfabricaciones = []
        self.current_procesos_mecanicos = []
        self.form_widgets = {}

        main_layout = QHBoxLayout(self)
        left_panel = QFrame(); left_layout = QVBoxLayout(left_panel); left_panel.setMaximumWidth(450)
        self.search_entry = QLineEdit(); self.search_entry.setPlaceholderText("Buscar producto...")
        left_layout.addWidget(QLabel("<b>Buscar Producto:</b>")); left_layout.addWidget(self.search_entry)
        self.results_list = QListWidget(); left_layout.addWidget(self.results_list)
        main_layout.addWidget(left_panel)

        self.edit_area_container = QFrame(); self.edit_area_container_layout = QVBoxLayout(self.edit_area_container)
        main_layout.addWidget(self.edit_area_container, 1)
        self.clear_edit_area()

    def update_search_results(self, results):
        self.results_list.clear()
        for product in results:
            iterations = self.controller.model.get_product_iterations(product.codigo) if self.controller else []
            item_text = f"📜 {product.codigo} | {product.descripcion}" if iterations else f"{product.codigo} | {product.descripcion}"
            item = QListWidgetItem(item_text); item.setData(Qt.ItemDataRole.UserRole, product.codigo)
            self.results_list.addItem(item)

    def clear_edit_area(self):
        layout = self.edit_area_container_layout
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget(): item.widget().deleteLater()
                elif item.layout():
                    sub = item.layout()
                    while sub.count():
                        si = sub.takeAt(0)
                        if si.widget(): si.widget().deleteLater()
        self.form_widgets = {}; self.current_subfabricaciones = []; self.current_procesos_mecanicos = []
        placeholder = QLabel("Seleccione un producto para ver sus detalles.")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.edit_area_container_layout.addWidget(placeholder)

    def display_product_form(self, data, sub_data):
        self.clear_edit_area()
        self.current_subfabricaciones = [{"id": s.id, "descripcion": s.descripcion, "tiempo": s.tiempo, "tipo_trabajador": s.tipo_trabajador, "maquina_id": s.maquina_id} for s in sub_data]
        self.current_procesos_mecanicos = []

        form_layout = QFormLayout()
        self.form_widgets['codigo'] = QLineEdit(data.codigo)
        self.form_widgets['descripcion'] = QLineEdit(data.descripcion)
        self.form_widgets['departamento'] = QComboBox(); self.form_widgets['departamento'].addItems(["Mecánica", "Electrónica", "Montaje"])
        self.form_widgets['departamento'].setCurrentText(data.departamento)
        self.form_widgets['donde'] = QTextEdit(data.donde); self.form_widgets['donde'].setFixedHeight(80)
        self.form_widgets['sub_switch'] = QCheckBox("¿Tiene subfabricaciones?"); self.form_widgets['sub_switch'].setChecked(bool(data.tiene_subfabricaciones))

        self.form_widgets['manage_subs_button'] = QPushButton("Gestionar Sub-fabricaciones")
        self.form_widgets['manage_subs_button'].clicked.connect(self.manage_subs_signal.emit)
        self.form_widgets['manage_procesos_button'] = QPushButton("Gestionar Procesos Mecánicos")
        self.form_widgets['manage_procesos_button'].clicked.connect(self.manage_procesos_signal.emit)
        self.form_widgets['manage_details_button'] = QPushButton("Gestionar Componentes e Iteraciones")
        self.form_widgets['manage_details_button'].clicked.connect(lambda: self.manage_details_signal.emit(data.codigo))

        form_layout.addRow("Código:", self.form_widgets['codigo']); form_layout.addRow("Descripción:", self.form_widgets['descripcion'])
        form_layout.addRow("Departamento:", self.form_widgets['departamento']); form_layout.addRow("Dónde se ubica:", self.form_widgets['donde'])

        self.edit_area_container_layout.addLayout(form_layout)
        self.edit_area_container_layout.addWidget(self.form_widgets['sub_switch'])
        self.edit_area_container_layout.addWidget(self.form_widgets['manage_subs_button'])
        self.edit_area_container_layout.addWidget(self.form_widgets['manage_procesos_button'])
        self.edit_area_container_layout.addWidget(self.form_widgets['manage_details_button'])

        button_layout = QHBoxLayout(); save_btn = QPushButton("Guardar Cambios"); delete_btn = QPushButton("Eliminar Producto")
        save_btn.clicked.connect(lambda: self.save_product_signal.emit(data.codigo))
        delete_btn.clicked.connect(lambda: self.delete_product_signal.emit(data.codigo))
        button_layout.addWidget(save_btn); button_layout.addWidget(delete_btn)
        self.edit_area_container_layout.addLayout(button_layout)
        self.edit_area_container_layout.addStretch()

        def toggle_subs():
            visible = self.form_widgets['sub_switch'].isChecked()
            self.form_widgets['manage_subs_button'].setVisible(visible)
        self.form_widgets['sub_switch'].toggled.connect(toggle_subs); toggle_subs()

    def get_product_form_data(self):
        return {
            "codigo": self.form_widgets['codigo'].text(), "descripcion": self.form_widgets['descripcion'].text(),
            "departamento": self.form_widgets['departamento'].currentText(), "donde": self.form_widgets['donde'].toPlainText(),
            "tiene_subfabricaciones": 1 if self.form_widgets['sub_switch'].isChecked() else 0,
            "tiempo_optimo": 0, "tipo_trabajador": 1, "sub_partes": self.current_subfabricaciones,
            "procesos_mecanicos": self.current_procesos_mecanicos
        }

    def clear_all(self):
        self.search_entry.clear(); self.results_list.clear(); self.clear_edit_area()
