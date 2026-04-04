# -*- coding: utf-8 -*-
"""
Interfaz PyQt6 (`lotes_widget`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from .base import *
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

class DefinirLoteWidget(QWidget):
    """Widget para crear y editar plantillas de Lote."""
    save_lote_signal = pyqtSignal()

    def __init__(self, _app_controller: Any = None, parent: Optional[QWidget] = None) -> None:
        """`_app_controller` se ignora en ctor; opcionalmente se usa en ``set_controller``."""
        super().__init__(parent)
        from core.di_container import DIContainer
        from controllers.lote_controller import LoteController
        from core.services.product_service import ProductService
        from core.services.fabricacion_service import FabricacionService

        _c = DIContainer.get_instance()
        self.lote_controller = _c.resolve(LoteController)
        self._product_service = _c.resolve(ProductService) if _c.is_registered(ProductService) else None
        self._fabricacion_service: Any = None
        if _c.is_registered(FabricacionService):
            self._fabricacion_service = _c.resolve(FabricacionService)
        self.current_lote_id = None
        self.lote_content: dict[str, set[Any]] = {"products": set(), "fabrications": set()}
        self.setup_ui()

    def setup_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        left_p = QFrame(); left_l = QVBoxLayout(left_p); left_p.setMaximumWidth(450)
        pb = QGroupBox("Añadir Productos"); pl = QVBoxLayout(pb)
        self.product_search = QLineEdit(); self.product_search.setPlaceholderText("Buscar producto...")
        self.product_results = QListWidget(); self.add_product_button = QPushButton("Añadir Producto")
        
        # Conectar señal de búsqueda de productos
        self.product_search.textChanged.connect(self.filter_products)
        
        pl.addWidget(self.product_search); pl.addWidget(self.product_results); pl.addWidget(self.add_product_button); left_l.addWidget(pb)

        fb = QGroupBox("Añadir Fabricaciones"); fl = QVBoxLayout(fb)
        self.fab_search = QLineEdit(); self.fab_search.setPlaceholderText("Buscar fabricación...")
        self.fab_results = QListWidget(); self.add_fab_button = QPushButton("Añadir Fabricación")
        
        # Conectar señal de búsqueda de fabricaciones
        self.fab_search.textChanged.connect(self.filter_fabrications)
        
        fl.addWidget(self.fab_search); fl.addWidget(self.fab_results); fl.addWidget(self.add_fab_button); left_l.addWidget(fb)
        main_layout.addWidget(left_p)

        right_p = QFrame(); right_p.setFrameShape(QFrame.Shape.StyledPanel); right_l = QVBoxLayout(right_p)
        self.lote_title = QLabel("Nuevo Lote sin Guardar"); f = self.lote_title.font(); f.setPointSize(16); f.setBold(True); self.lote_title.setFont(f)
        right_l.addWidget(self.lote_title); right_l.addWidget(QLabel("<b>Componentes:</b>"))
        self.lote_content_list = QListWidget(); right_l.addWidget(self.lote_content_list)
        self.remove_item_button = QPushButton("Quitar Seleccionado"); right_l.addWidget(self.remove_item_button, alignment=Qt.AlignmentFlag.AlignRight)
        right_l.addStretch()

        sb = QGroupBox("Guardar Plantilla"); sl = QFormLayout(sb)
        self.lote_codigo_entry = QLineEdit(); self.lote_descripcion_entry = QLineEdit()
        self.save_button = QPushButton("Guardar Plantilla"); self.new_button = QPushButton("Crear Nueva")
        sl.addRow("Código:", self.lote_codigo_entry); sl.addRow("Descripción:", self.lote_descripcion_entry)
        bb = QHBoxLayout(); bb.addWidget(self.new_button); bb.addStretch(); bb.addWidget(self.save_button); sl.addRow(bb)
        right_l.addWidget(sb); main_layout.addWidget(right_p, 1)

    def set_controller(self, controller: Any) -> None:
        """Compat ``MainView``: opcionalmente mejora ``FabricacionService`` vía hub y repuebla listas."""
        from core.di_container import DIContainer
        from ui.dialogs.fabrication.dialog_dependencies import resolve_fabricacion_service

        if controller is not None:
            fs = resolve_fabricacion_service(controller, DIContainer.get_instance())
            if fs is not None:
                self._fabricacion_service = fs
        if self.lote_controller:
            self.populate_products_list()
            self.populate_fabrications_list()

    def populate_fabrications_list(self) -> None:
        """Obtiene todas las fabricaciones y llena la lista, excluyendo las tareas generadas automáticamente."""
        if not self.lote_controller: return
        
        self.fab_results.clear()
        try:
            if self._fabricacion_service is None:
                return
            fabrications = self._fabricacion_service.search_fabricaciones("")
            for fab in fabrications:
                # Filtrar las fabricaciones que sean tareas de trabajadores (empiezan por TASK-)
                if fab.codigo and fab.codigo.startswith("TASK-"):
                    continue
                    
                # fab es un objeto FabricacionDTO
                text = f"{fab.codigo} - {fab.descripcion or 'Sin descripción'}"
                item = QListWidgetItem(text)
                # Guardamos TUPLA (id, codigo) para PilaController
                item.setData(Qt.ItemDataRole.UserRole, (fab.id, fab.codigo))
                self.fab_results.addItem(item)
        except Exception:
            logger.exception("Error cargando fabricaciones.")

    def filter_fabrications(self, text: str) -> None:
        """Filtra la lista de fabricaciones según el texto ingresado."""
        search_text = text.lower().strip()
        
        for i in range(self.fab_results.count()):
            item = self.fab_results.item(i)
            if item is None:
                continue
            item_text = item.text().lower()
            
            if search_text in item_text:
                item.setHidden(False)
            else:
                item.setHidden(True)

    def populate_products_list(self) -> None:
        """Obtiene todos los productos y llena la lista."""
        if not self.lote_controller: return
        
        self.product_results.clear()
        try:
            if self._product_service is None:
                return
            products = self._product_service.search_products("")
            for product in products:
                # product es un objeto ProductDTO
                text = f"{product.codigo} - {product.descripcion}"
                item = QListWidgetItem(text)
                # Guardamos TUPLA (codigo, descripcion) para que coincida con lo esperado por PilaController
                item.setData(Qt.ItemDataRole.UserRole, (product.codigo, product.descripcion))
                self.product_results.addItem(item)
        except Exception:
            logger.exception("Error cargando productos.")

    def filter_products(self, text: str) -> None:
        """Filtra la lista de productos según el texto ingresado."""
        search_text = text.lower().strip()
        
        for i in range(self.product_results.count()):
            item = self.product_results.item(i)
            if item is None:
                continue
            item_text = item.text().lower()
            
            # Mostrar si el texto de búsqueda está contenido en el texto del item
            if search_text in item_text:
                item.setHidden(False)
            else:
                item.setHidden(True)

    def clear_form(self) -> None:
        self.current_lote_id = None; self.lote_content = {"products": set(), "fabrications": set()}
        self.lote_codigo_entry.clear(); self.lote_descripcion_entry.clear(); self.lote_title.setText("Nuevo Lote sin Guardar"); self.update_content_list()

    def update_content_list(self) -> None:
        self.lote_content_list.clear()
        for c, d in self.lote_content["products"]:
            it = QListWidgetItem(f"[Producto] {c} - {d}"); it.setData(Qt.ItemDataRole.UserRole, ("product", c)); self.lote_content_list.addItem(it)
        for i, c in self.lote_content["fabrications"]:
            it = QListWidgetItem(f"[Fabricación] {c}"); it.setData(Qt.ItemDataRole.UserRole, ("fabrication", i)); self.lote_content_list.addItem(it)

    def get_data(self) -> dict[str, Any]:
        pc = [i[0] for i in self.lote_content["products"]]; fi = [i[0] for i in self.lote_content["fabrications"]]
        return {"codigo": self.lote_codigo_entry.text().strip(), "descripcion": self.lote_descripcion_entry.text().strip(), "product_codes": pc, "fabricacion_ids": fi}


class LotesWidget(QWidget):
    """Widget específico para editar y visualizar las plantillas de Lote."""
    save_lote_signal = pyqtSignal(int)
    delete_lote_signal = pyqtSignal(int)

    def __init__(self, _app_controller: Any = None, parent: Optional[QWidget] = None) -> None:
        """`_app_controller` se ignora (compat ``MainView``)."""
        super().__init__(parent)
        from core.di_container import DIContainer
        from controllers.lote_controller import LoteController
        self.lote_controller = DIContainer.get_instance().resolve(LoteController)
        self.current_lote_id = None; self.setup_ui()

    def set_controller(self, controller: Any) -> None:
        """Compat ``MainView``; listas y CRUD usan ``LoteController`` del DI."""
        return

    def setup_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        left_p = QFrame(); left_l = QVBoxLayout(left_p); left_p.setMaximumWidth(450)
        self.search_entry = QLineEdit(); self.search_entry.setPlaceholderText("Buscar plantilla...")
        left_l.addWidget(QLabel("<b>Buscar Plantilla de Lote:</b>")); left_l.addWidget(self.search_entry)
        self.results_list = QListWidget(); left_l.addWidget(self.results_list); main_layout.addWidget(left_p)
        self.edit_area_container = QFrame(); self.edit_area_container.setFrameShape(QFrame.Shape.StyledPanel); self.edit_area_container_layout = QVBoxLayout(self.edit_area_container)
        main_layout.addWidget(self.edit_area_container, 1); self.clear_edit_area()

    def clear_edit_area(self) -> None:
        while self.edit_area_container_layout.count():
            c = self.edit_area_container_layout.takeAt(0)
            if c is not None:
                w = c.widget()
                if w is not None: 
                    w.deleteLater()
        self.current_lote_id = None
        p = QLabel("Seleccione una plantilla de lote."); p.setAlignment(Qt.AlignmentFlag.AlignCenter); self.edit_area_container_layout.addWidget(p)

    def display_lote_details(self, lote_data: Any) -> None:
        self.clear_edit_area(); self.current_lote_id = lote_data.id
        dw = QWidget(); dl = QVBoxLayout(dw); fl = QFormLayout()
        self.codigo_edit = QLineEdit(lote_data.codigo); self.descripcion_edit = QTextEdit(lote_data.descripcion); self.descripcion_edit.setFixedHeight(80)
        fl.addRow("<b>Código:</b>", self.codigo_edit); fl.addRow("<b>Descripción:</b>", self.descripcion_edit); dl.addLayout(fl)
        dl.addWidget(QLabel("<b>Contenido:</b>")); self.content_list = QListWidget()
        for p in lote_data.productos: self.content_list.addItem(f"[Producto] {p.codigo} - {p.descripcion}")
        for f in lote_data.fabricaciones: self.content_list.addItem(f"[Fabricación] {f.codigo}")
        dl.addWidget(self.content_list); bl = QHBoxLayout(); db = QPushButton("Eliminar"); sb = QPushButton("Guardar Cambios")
        db.clicked.connect(lambda: self.delete_lote_signal.emit(self.current_lote_id)); sb.clicked.connect(lambda: self.save_lote_signal.emit(self.current_lote_id))
        bl.addStretch(); bl.addWidget(db); bl.addWidget(sb); dl.addLayout(bl); self.edit_area_container_layout.addWidget(dw)

    def get_form_data(self) -> dict[str, Any] | None:
        if not self.current_lote_id: return None
        return {"codigo": self.codigo_edit.text().strip(), "descripcion": self.descripcion_edit.toPlainText().strip()}
