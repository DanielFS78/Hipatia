# -*- coding: utf-8 -*-
from .base import *

class FabricationsWidget(QWidget):
    """Widget específico para la gestión de Fabricaciones (CRUD)."""
    save_fabricacion_signal = pyqtSignal(int)
    delete_fabricacion_signal = pyqtSignal(int)
    create_fabricacion_signal = pyqtSignal()
    edit_preprocesos_signal = pyqtSignal(int)
    edit_products_signal = pyqtSignal(int)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.current_fabricacion_id = None
        self.form_widgets = {}

        main_layout = QHBoxLayout(self)
        left_panel = QFrame(); left_layout = QVBoxLayout(left_panel); left_panel.setMaximumWidth(450)
        search_layout = QHBoxLayout()
        self.search_entry = QLineEdit(); self.search_entry.setPlaceholderText("Buscar fabricación...")
        self.create_button = QPushButton("Crear Fabricación")
        search_layout.addWidget(self.search_entry); search_layout.addWidget(self.create_button); left_layout.addLayout(search_layout)
        self.results_list = QListWidget(); left_layout.addWidget(self.results_list)
        main_layout.addWidget(left_panel)

        self.edit_area_container = QFrame(); self.edit_area_container_layout = QVBoxLayout(self.edit_area_container)
        main_layout.addWidget(self.edit_area_container, 1)
        self.clear_edit_area()
        self.create_button.clicked.connect(self.create_fabricacion_signal.emit)

    def update_search_results(self, results):
        self.results_list.clear()
        for fab in results:
            item = QListWidgetItem(f"{fab.codigo} | {fab.descripcion}")
            item.setData(Qt.ItemDataRole.UserRole, fab.id)
            self.results_list.addItem(item)

    def clear_edit_area(self):
        while self.edit_area_container_layout.count():
            child = self.edit_area_container_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        self.form_widgets = {}
        placeholder = QLabel("Seleccione una fabricación de la lista o cree una nueva.")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.edit_area_container_layout.addWidget(placeholder)

    def display_fabricacion_form(self, data, content):
        self.clear_edit_area()
        self.current_fabricacion_id = data.id
        form_layout = QFormLayout()
        self.form_widgets['codigo'] = QLineEdit(str(data.codigo or ''))
        self.form_widgets['descripcion'] = QLineEdit(str(data.descripcion or ''))
        form_layout.addRow("Código:", self.form_widgets['codigo']); form_layout.addRow("Descripción:", self.form_widgets['descripcion'])
        self.edit_area_container_layout.addLayout(form_layout)

        preprocesos_group = QGroupBox("Preprocesos Asignados")
        preprocesos_layout = QVBoxLayout(preprocesos_group)
        self.form_widgets['preprocesos_list'] = QListWidget()
        self.form_widgets['preprocesos_list'].setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        if content:
            for preproceso in content:
                self.form_widgets['preprocesos_list'].addItem(f"{preproceso.nombre} - {preproceso.descripcion or 'Sin descripción'}")
        preprocesos_layout.addWidget(self.form_widgets['preprocesos_list'])
        
        edit_btn = QPushButton("Editar Preprocesos Asignados...")
        edit_btn.clicked.connect(lambda: self.edit_preprocesos_signal.emit(self.current_fabricacion_id))
        preprocesos_layout.addWidget(edit_btn)
        self.edit_area_container_layout.addWidget(preprocesos_group)

        # Sección de Productos Asignados
        productos_group = QGroupBox("Productos Asignados")
        productos_layout = QVBoxLayout(productos_group)
        self.form_widgets['productos_list'] = QListWidget()
        self.form_widgets['productos_list'].setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        if hasattr(data, 'productos') and data.productos:
            for prod in data.productos:
                 # prod es un FabricacionProductoDTO(producto_codigo, cantidad)
                 # Necesitamos la descripción si es posible, si no mostramos el código
                 desc = getattr(prod, 'descripcion', '') 
                 text = f"{prod.producto_codigo} (x{prod.cantidad})"
                 if desc:
                     text += f" - {desc}"
                 self.form_widgets['productos_list'].addItem(text)
        elif content and isinstance(content, dict) and 'productos' in content:
             # Soporte para paso explicito de productos si data no lo tiene
             for prod in content['productos']:
                 self.form_widgets['productos_list'].addItem(f"{prod.producto_codigo} (x{prod.cantidad})")
        
        productos_layout.addWidget(self.form_widgets['productos_list'])
        edit_prod_btn = QPushButton("Editar Productos Asignados...")
        edit_prod_btn.clicked.connect(lambda: self.edit_products_signal.emit(self.current_fabricacion_id))
        productos_layout.addWidget(edit_prod_btn)
        self.edit_area_container_layout.addWidget(productos_group)

        button_layout = QHBoxLayout(); save_btn = QPushButton("Guardar Cambios"); delete_btn = QPushButton("Eliminar Fabricación")
        save_btn.clicked.connect(lambda: self.save_fabricacion_signal.emit(self.current_fabricacion_id))
        delete_btn.clicked.connect(lambda: self.delete_fabricacion_signal.emit(self.current_fabricacion_id))
        button_layout.addStretch(); button_layout.addWidget(delete_btn); button_layout.addWidget(save_btn)
        self.edit_area_container_layout.addLayout(button_layout); self.edit_area_container_layout.addStretch()

    def get_fabricacion_form_data(self):
        if not self.form_widgets: return None
        return {
            "id": self.current_fabricacion_id,
            "codigo": self.form_widgets.get('codigo').text() if self.form_widgets.get('codigo') else "",
            "descripcion": self.form_widgets.get('descripcion').text() if self.form_widgets.get('descripcion') else ""
        }

    def clear_all(self):
        self.search_entry.clear(); self.results_list.clear(); self.clear_edit_area()
