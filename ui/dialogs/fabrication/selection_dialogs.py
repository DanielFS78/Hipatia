"""
Interfaz PyQt6 (`selection_dialogs`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QScrollArea, QWidget, QCheckBox, 
    QHBoxLayout, QDialogButtonBox, QListWidget, QListWidgetItem,
    QPushButton
)
from PyQt6.QtCore import Qt
from typing import List, Set, Dict, Any, Optional

from core.dtos import CalculationProductDTO

class PreprocesosSelectionDialog(QDialog):
    """
    Diálogo para seleccionar qué preprocesos asignar a una fabricación.
    """

    def __init__(self, fabricacion: Any, all_preprocesos: List[Any], assigned_ids: List[int], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.fabricacion = fabricacion # (id, codigo, descripcion) or object
        self.all_preprocesos = all_preprocesos
        self.assigned_ids: Set[int] = set(assigned_ids)
        self.checkboxes: Dict[int, QCheckBox] = {}

        self.setup_ui()

    def setup_ui(self) -> None:
        # Handle fabricacion being tuple or object
        fab_code = self.fabricacion[1] if isinstance(self.fabricacion, tuple) else self.fabricacion.codigo
        fab_desc = self.fabricacion[2] if isinstance(self.fabricacion, tuple) else getattr(self.fabricacion, 'descripcion', '')
        
        self.setWindowTitle(f"Asignar Preprocesos - {fab_code}")
        self.setModal(True)
        self.resize(600, 500)

        layout = QVBoxLayout(self)

        # Información de la fabricación
        info_label = QLabel(f"<b>Fabricación:</b> {fab_code} - {fab_desc or 'Sin descripción'}")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        layout.addWidget(QLabel("Seleccione los preprocesos que se aplicarán a esta fabricación:"))

        # Área de scroll para los preprocesos
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        if not self.all_preprocesos:
            scroll_layout.addWidget(QLabel("No hay preprocesos disponibles. Cree preprocesos primero."))
        else:
            for preproceso in self.all_preprocesos:
                checkbox = QCheckBox()

                # Crear texto descriptivo
                # Handle generic object or dict access
                comp_list = getattr(preproceso, 'componentes', [])
                componentes_text = ", ".join([c.descripcion for c in comp_list]) if comp_list and hasattr(comp_list[0], 'descripcion') else ""
                
                nombre = getattr(preproceso, 'nombre', 'Sin Nombre')
                descripcion = getattr(preproceso, 'descripcion', '')
                p_id = getattr(preproceso, 'id', -1)

                texto = f"<b>{nombre}</b>"
                if descripcion:
                    texto += f"<br><i>{descripcion}</i>"
                if componentes_text:
                    texto += f"<br>Componentes: {componentes_text}"

                checkbox.setText("")
                checkbox.setChecked(p_id in self.assigned_ids)

                # Layout horizontal para checkbox y texto
                h_layout = QHBoxLayout()
                h_layout.addWidget(checkbox)

                label = QLabel(texto)
                label.setWordWrap(True)
                label.setStyleSheet("margin-left: 10px; padding: 5px;")
                h_layout.addWidget(label)

                # Widget contenedor
                container = QWidget()
                container.setLayout(h_layout)
                scroll_layout.addWidget(container)

                self.checkboxes[p_id] = checkbox

        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        # Botones
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_selected_preprocesos(self) -> List[int]:
        """Retorna lista de IDs de preprocesos seleccionados."""
        return [
            preproceso_id for preproceso_id, checkbox in self.checkboxes.items()
            if checkbox.isChecked()
        ]


class PreprocesosForCalculationDialog(QDialog):
    """
    Diálogo para mostrar y seleccionar preprocesos disponibles
    para añadir al cálculo de tiempos de una fabricación.
    """

    def __init__(
        self,
        fabricacion_id: int,
        available_preprocesos: List[CalculationProductDTO],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.fabricacion_id = fabricacion_id
        self.available_preprocesos = available_preprocesos
        self.selected_preprocesos: List[CalculationProductDTO] = []

        self.setup_ui()

    def setup_ui(self) -> None:
        self.setWindowTitle("Preprocesos Disponibles")
        self.setModal(True)
        self.resize(600, 400)

        layout = QVBoxLayout(self)

        # Instrucciones
        instructions = QLabel(
            "<b>Seleccione los preprocesos que desea añadir al cálculo de tiempos:</b><br>"
            "Los preprocesos seleccionados se añadirán como pasos adicionales en la planificación."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Lista de preprocesos disponibles
        self.preprocesos_list = QListWidget()
        self.preprocesos_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)

        if not self.available_preprocesos:
            item = QListWidgetItem("No hay preprocesos asignados a esta fabricación.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)  # No seleccionable
            self.preprocesos_list.addItem(item)
        else:
            for preproceso in self.available_preprocesos:
                tiempo_estimado = preproceso.tiempo_optimo
                text = f"{preproceso.descripcion} (~{tiempo_estimado} min)"
                
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, preproceso)
                self.preprocesos_list.addItem(item)

        layout.addWidget(self.preprocesos_list)

        # Información adicional
        info_label = QLabel(
            "<i>Nota: Los preprocesos añadidos aparecerán como tareas separadas "
            "que requerirán asignación de trabajadores en el siguiente paso.</i>"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666666; font-size: 10pt;")
        layout.addWidget(info_label)

        # Botones
        button_layout = QHBoxLayout()

        select_all_button = QPushButton("Seleccionar Todos")
        select_all_button.clicked.connect(self.select_all)
        button_layout.addWidget(select_all_button)

        clear_selection_button = QPushButton("Limpiar Selección")
        clear_selection_button.clicked.connect(self.clear_selection)
        button_layout.addWidget(clear_selection_button)

        button_layout.addStretch()

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_layout.addWidget(button_box)

        layout.addLayout(button_layout)

    def select_all(self) -> None:
        """Selecciona todos los preprocesos."""
        for i in range(self.preprocesos_list.count()):
            item = self.preprocesos_list.item(i)
            if item and item.flags() & Qt.ItemFlag.ItemIsSelectable:
                item.setSelected(True)

    def clear_selection(self) -> None:
        """Limpia la selección."""
        self.preprocesos_list.clearSelection()

    def get_selected_preprocesos(self) -> List[CalculationProductDTO]:
        """
        Retorna lista de preprocesos seleccionados.

        Returns:
            list: Lista de DTOs con datos de preprocesos
        """
        selected: list[CalculationProductDTO] = []
        for item in self.preprocesos_list.selectedItems():
            preproceso_data = item.data(Qt.ItemDataRole.UserRole)
            if preproceso_data:
                selected.append(preproceso_data)

        return selected
