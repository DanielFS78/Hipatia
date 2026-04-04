# -*- coding: utf-8 -*-
"""
Interfaz PyQt6 (`preprocesos_widget`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from .base import *
from typing import Any

class PreprocesosWidget(QWidget):
    """
    Widget rediseñado para la gestión de Preprocesos.
    Muestra una lista a la izquierda y los detalles del seleccionado a la derecha.
    """
    
    # Attributes for strict mocks
    add_button: Any = None
    edit_button: Any = None
    delete_button: Any = None
    assign_to_fabricaciones_button: Any = None
    search_entry: Any = None
    preprocesos_list: Any = None
    preprocesos_data_cache: list[Any] = []
    current_preproceso_id: Any = None

    def __init__(self, controller: Any = None) -> None:
        super().__init__()
        from core.di_container import DIContainer
        from controllers.product_controller_v2 import ProductController
        self.preproceso_controller = DIContainer.get_instance().resolve(ProductController)
        self.preprocesos_data_cache = []
        self.current_preproceso_id = None
        self.setup_ui()

    def set_controller(self, controller: Any) -> None:
        """Compat ``MainView.set_controller``; la vista usa DI y ``ProductController``."""
        return

    def setup_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        left_panel = QFrame(); left_layout = QVBoxLayout(left_panel); left_panel.setMaximumWidth(400)
        left_layout.addWidget(QLabel("<b>Listado de Preprocesos</b>"))
        self.search_entry = QLineEdit(); self.search_entry.setPlaceholderText("Filtrar por nombre...")
        self.search_entry.textChanged.connect(self._filter_list)
        left_layout.addWidget(self.search_entry)
        self.preprocesos_list = QListWidget(); self.preprocesos_list.itemClicked.connect(self._on_item_selected)
        left_layout.addWidget(self.preprocesos_list)

        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Añadir"); self.edit_button = QPushButton("Editar"); self.delete_button = QPushButton("Eliminar")
        buttons_layout.addWidget(self.add_button); buttons_layout.addWidget(self.edit_button); buttons_layout.addWidget(self.delete_button)
        left_layout.addLayout(buttons_layout)

        self.assign_to_fabricaciones_button = QPushButton("Asignar preprocesos a fabricaciones")
        self.assign_to_fabricaciones_button.setToolTip(
            "Abre el listado de fabricaciones para ver o abrir la gestión de preprocesos por fabricación."
        )
        self.assign_to_fabricaciones_button.clicked.connect(self._on_assign_to_fabricaciones_clicked)
        left_layout.addWidget(self.assign_to_fabricaciones_button)

        right_panel = QFrame(); right_panel.setFrameShape(QFrame.Shape.StyledPanel)
        self.details_layout = QVBoxLayout(right_panel); self._show_placeholder_details()
        main_layout.addWidget(left_panel); main_layout.addWidget(right_panel, 1)

        self.add_button.clicked.connect(self._on_add_clicked); self.edit_button.clicked.connect(self._on_edit_clicked)
        self.delete_button.clicked.connect(self._on_delete_clicked)

    def load_preprocesos_data(self, data: list[Any]) -> None:
        self.preprocesos_data_cache = data; self.preprocesos_list.clear(); self._show_placeholder_details()
        for p in data:
            item = QListWidgetItem(f"{p.nombre} ({getattr(p, 'tiempo', 0)} min)")
            item.setData(Qt.ItemDataRole.UserRole, p.id); self.preprocesos_list.addItem(item)
        self._filter_list()

    def _filter_list(self) -> None:
        txt = self.search_entry.text().lower()
        for i in range(self.preprocesos_list.count()):
            it = self.preprocesos_list.item(i); it.setHidden(txt not in it.text().lower())

    def _clear_layout(self, layout: Any) -> None:
        while layout.count():
            c = layout.takeAt(0)
            if c.widget(): c.widget().deleteLater()

    def _show_placeholder_details(self) -> None:
        self._clear_layout(self.details_layout); self.current_preproceso_id = None
        self.edit_button.setEnabled(False); self.delete_button.setEnabled(False)
        p = QLabel("Seleccione un preproceso de la lista."); p.setAlignment(Qt.AlignmentFlag.AlignCenter); p.setWordWrap(True)
        self.details_layout.addWidget(p); self.details_layout.addStretch()

    def _on_item_selected(self, item: Any) -> None:
        self.current_preproceso_id = item.data(Qt.ItemDataRole.UserRole)
        sel = next((p for p in self.preprocesos_data_cache if p.id == self.current_preproceso_id), None)
        if not sel: self._show_placeholder_details(); return
        self.edit_button.setEnabled(True); self.delete_button.setEnabled(True); self._clear_layout(self.details_layout)
        t = QLabel(f"<b>{sel.nombre}</b>"); f = t.font(); f.setPointSize(16); t.setFont(f)
        tm = QLabel(f"<b>Tiempo:</b> {getattr(sel, 'tiempo', 0)} min")
        ds = QTextEdit(sel.descripcion or 'Sin descripción.'); ds.setReadOnly(True)
        self.details_layout.addWidget(t); self.details_layout.addWidget(tm); self.details_layout.addWidget(QLabel("<b>Descripción:</b>")); self.details_layout.addWidget(ds, 1)

    def _on_add_clicked(self) -> None:
        if self.preproceso_controller:
            self.preproceso_controller.show_add_preproceso_dialog()

    def _on_edit_clicked(self) -> None:
        if self.preproceso_controller and self.current_preproceso_id:
            sel = next((p for p in self.preprocesos_data_cache if p.id == self.current_preproceso_id), None)
            if sel:
                self.preproceso_controller.show_edit_preproceso_dialog(sel)

    def _on_delete_clicked(self) -> None:
        if self.preproceso_controller and self.current_preproceso_id:
            sel = next((p for p in self.preprocesos_data_cache if p.id == self.current_preproceso_id), None)
            if sel:
                self.preproceso_controller.delete_preproceso(sel.id, sel.nombre)

    def _on_assign_to_fabricaciones_clicked(self) -> None:
        from core.di_container import DIContainer
        from ui.dialogs.fabrication.assignment_dialogs import AssignPreprocesosDialog
        from ui.dialogs.fabrication.dialog_dependencies import resolve_fabricacion_service

        c = DIContainer.get_instance()
        fs = resolve_fabricacion_service(None, c)
        if fs is None:
            return
        dlg = AssignPreprocesosDialog(
            None,
            self,
            fabricacion_service=fs,
            opens_fabricacion_preprocesos=self.preproceso_controller,
        )
        dlg.exec()
