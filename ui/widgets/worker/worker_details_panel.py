# -*- coding: utf-8 -*-
"""
Interfaz PyQt6 (`worker_details_panel`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox,
    QCheckBox, QTextEdit, QFormLayout, QGroupBox, QSpinBox,
    QPushButton, QHBoxLayout, QTabWidget, QListWidget, QListWidgetItem, QCompleter,
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Any, Dict, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from core.dtos import WorkerDetailDTO, ProductDTO, WorkerFormDataDTO

class WorkerDetailsPanel(QWidget):
    """Panel que contiene el formulario de detalles y asignación de un trabajador."""
    save_signal = pyqtSignal()
    delete_signal = pyqtSignal()
    change_password_signal = pyqtSignal()
    product_search_signal = pyqtSignal(str)
    of_search_signal = pyqtSignal(str)
    assign_task_signal = pyqtSignal()

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.form_widgets: Dict[str, Any] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configura la interfaz gráfica del formulario."""
        layout = QVBoxLayout(self)
        
        self.title_label = QLabel("Detalles del Trabajador")
        font = self.title_label.font()
        font.setBold(True)
        font.setPointSize(14)
        self.title_label.setFont(font)
        layout.addWidget(self.title_label)

        # Usamos un formulario interno para organizar
        form_container = QWidget()
        form_layout = QFormLayout(form_container)

        self.form_widgets['nombre'] = QLineEdit()
        self.form_widgets['tipo_trabajador'] = QComboBox()
        self.form_widgets['tipo_trabajador'].addItems([
            "Tipo 1 (Polivalente)", "Tipo 2 (Intermedio)", "Tipo 3 (Especialista)"
        ])
        self.form_widgets['activo'] = QCheckBox("Trabajador en activo")
        self.form_widgets['notas'] = QTextEdit()
        self.form_widgets['notas'].setMaximumHeight(80)

        # Acceso al sistema
        self.form_widgets['username'] = QLineEdit()
        self.form_widgets['username'].setPlaceholderText("Usuario acceso...")
        self.form_widgets['password'] = QLineEdit()
        self.form_widgets['password'].setEchoMode(QLineEdit.EchoMode.Password)
        self.form_widgets['password'].setPlaceholderText("Nueva contraseña...")
        self.form_widgets['confirm_password'] = QLineEdit()
        self.form_widgets['confirm_password'].setEchoMode(QLineEdit.EchoMode.Password)
        self.form_widgets['confirm_password'].setPlaceholderText("Confirmar...")
        self.form_widgets['role'] = QComboBox()
        self.form_widgets['role'].addItems(["(Sin acceso)", "Trabajador", "Responsable"])

        form_layout.addRow("Nombre Completo:", self.form_widgets['nombre'])
        form_layout.addRow("Nivel Habilidad:", self.form_widgets['tipo_trabajador'])
        form_layout.addRow(self.form_widgets['activo'])
        form_layout.addRow(QLabel("<hr>"))
        form_layout.addRow(QLabel("<b>Acceso al Sistema:</b>"))
        form_layout.addRow("Usuario:", self.form_widgets['username'])
        form_layout.addRow("Contraseña:", self.form_widgets['password'])
        form_layout.addRow("Confirmar:", self.form_widgets['confirm_password'])
        form_layout.addRow("Rol:", self.form_widgets['role'])
        form_layout.addRow("Notas:", self.form_widgets['notas'])

        layout.addWidget(form_container)

        # Grupo de Asignación Rápida
        self.assign_group = QGroupBox("Asignar Nueva Tarea")
        assign_layout = QFormLayout(self.assign_group)
        
        self.form_widgets['product_search'] = QLineEdit()
        self.form_widgets['product_search'].setPlaceholderText("Buscar producto...")
        self.form_widgets['product_results'] = QListWidget()
        self.form_widgets['product_results'].setFixedHeight(100)
        self.form_widgets['of_search'] = QLineEdit()
        self.form_widgets['of_search'].setPlaceholderText("Orden de fabricación...")
        self.form_widgets['quantity'] = QSpinBox()
        self.form_widgets['quantity'].setRange(1, 9999)
        self.form_widgets['assign_button'] = QPushButton("➕ Asignar Tarea")
        self.form_widgets['assign_button'].setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")

        assign_layout.addRow("Producto:", self.form_widgets['product_search'])
        assign_layout.addRow(self.form_widgets['product_results'])
        assign_layout.addRow("O.F. (Pedido):", self.form_widgets['of_search'])
        assign_layout.addRow("Cantidad:", self.form_widgets['quantity'])
        assign_layout.addRow(self.form_widgets['assign_button'])
        
        layout.addWidget(self.assign_group)
        layout.addStretch()

        # Botones de Acción
        actions_layout = QHBoxLayout()
        self.change_pass_btn = QPushButton("Cambiar Contraseña")
        self.delete_btn = QPushButton("Eliminar")
        self.save_btn = QPushButton("Guardar Cambios")
        self.save_btn.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")
        
        actions_layout.addWidget(self.change_pass_btn)
        actions_layout.addWidget(self.delete_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(self.save_btn)
        layout.addLayout(actions_layout)

        # Conexiones internas de señales
        self.form_widgets['product_search'].textChanged.connect(self.product_search_signal.emit)
        self.form_widgets['of_search'].textChanged.connect(self.of_search_signal.emit)
        self.form_widgets['assign_button'].clicked.connect(self.assign_task_signal.emit)
        self.change_pass_btn.clicked.connect(self.change_password_signal.emit)
        self.delete_btn.clicked.connect(self.delete_signal.emit)
        self.save_btn.clicked.connect(self.save_signal.emit)

    def set_worker_data(self, worker_data: Optional["WorkerDetailDTO"]) -> None:
        """Puebla el formulario con los datos de un trabajador."""
        self.title_label.setText("Editar Trabajador" if worker_data else "Añadir Nuevo Trabajador")
        self.form_widgets['nombre'].setText(worker_data.nombre_completo if worker_data else "")
        self.form_widgets['activo'].setChecked(bool(worker_data.activo if worker_data else True))
        self.form_widgets['notas'].setPlainText(worker_data.notas if worker_data else "")
        
        tipo = worker_data.tipo_trabajador if worker_data else 1
        self.form_widgets['tipo_trabajador'].setCurrentIndex(tipo - 1)
        
        self.form_widgets['username'].setText(worker_data.username if worker_data and worker_data.username else "")
        role = worker_data.role if worker_data and worker_data.role else ""
        role_idx = 1 if role == 'Trabajador' else 2 if role == 'Responsable' else 0
        self.form_widgets['role'].setCurrentIndex(role_idx)

        self.form_widgets['password'].clear()
        self.form_widgets['confirm_password'].clear()
        
        # Visibilidad según si es edición o nuevo
        is_edit = bool(worker_data)
        self.delete_btn.setVisible(is_edit)
        self.change_pass_btn.setVisible(is_edit)
        self.assign_group.setVisible(is_edit)

    def get_form_data(self) -> "WorkerFormDataDTO":
        """Extrae los datos del formulario en un WorkerFormDataDTO."""
        from core.dtos import WorkerFormDataDTO
        role_idx = self.form_widgets['role'].currentIndex()
        role = 'Trabajador' if role_idx == 1 else 'Responsable' if role_idx == 2 else None
        
        return WorkerFormDataDTO(
            nombre_completo=self.form_widgets['nombre'].text().strip(),
            activo=self.form_widgets['activo'].isChecked(),
            notas=self.form_widgets['notas'].toPlainText().strip(),
            tipo_trabajador=self.form_widgets['tipo_trabajador'].currentIndex() + 1,
            username=self.form_widgets['username'].text().strip() or None,
            password=self.form_widgets['password'].text() or None,
            confirm_password=self.form_widgets['confirm_password'].text() or None,
            role=role
        )

    def get_assignment_data(self) -> Optional[Dict[str, Any]]:
        """Extrae los datos de la nueva tarea a asignar."""
        current_item = self.form_widgets['product_results'].currentItem()
        if not current_item:
            return None
            
        return {
            "product_code": current_item.data(Qt.ItemDataRole.UserRole),
            "quantity": self.form_widgets['quantity'].value(),
            "orden_fabricacion": self.form_widgets['of_search'].text().strip().upper() or None
        }

    def update_product_results(self, items: List["ProductDTO"]) -> None:
        """Actualiza la lista de resultados de búsqueda de productos."""
        self.form_widgets['product_results'].clear()
        for prod in items:
            item = QListWidgetItem(f"{prod.codigo} | {prod.descripcion}")
            item.setData(Qt.ItemDataRole.UserRole, prod.codigo)
            self.form_widgets['product_results'].addItem(item)

    def clear_assignment_search_fields(self) -> None:
        """Vacía el buscador de producto y reinicia la cantidad en el bloque de asignación."""
        self.form_widgets['product_search'].clear()
        self.form_widgets['quantity'].setValue(1)

    def set_of_completer(self, of_list: List[str]) -> None:
        """Configura autocompletado para el campo de orden de fabricación."""
        completer = QCompleter(of_list)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.form_widgets['of_search'].setCompleter(completer)
