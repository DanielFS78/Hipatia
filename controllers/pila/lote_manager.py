# -*- coding: utf-8 -*-
"""
Nombre del Módulo: lote_manager.py
Descripción: Gestor especializado en la lógica de plantillas de lote (Templates).
             Se encarga de la búsqueda de productos, fabricaciones y el guardado
             de la estructura del lote.
"""
from typing import TYPE_CHECKING, Any, cast, Optional, List
import logging
from PyQt6.QtWidgets import QListWidgetItem
from PyQt6.QtCore import Qt

from controllers.pila.protocols import IPilaView, IPilaDatabase, IProductService, IFabricacionService

class LoteManager:
    """
    Gestor de plantillas de lote.
    Maneja la interacción entre la vista de definición de lotes y los repositorios.
    """
    def __init__(
        self, 
        view: IPilaView, 
        db: IPilaDatabase, 
        product_service: IProductService,
        fab_service: IFabricacionService
    ) -> None:
        self._view = view
        self._db = db
        self._product_service = product_service
        self._fab_service = fab_service
        self.logger = logging.getLogger("EvolucionTiemposApp")

    def on_calc_lote_search_changed(self, text: str) -> None:
        """Busca plantillas de lote para la pila de cálculo.

        Con texto vacío se listan todas las plantillas en BD (misma idea que productos
        en Definir Lote); con texto se filtra por código o descripción.
        """
        calc_page = self._view.pages.get("calculate")
        if not calc_page: return

        q = (text or "").strip()
        results = self._db.search_lotes(q)
        calc_page.lote_search_results.clear()
        for lote in results:
            item = QListWidgetItem(f"{lote.codigo} - {lote.descripcion or 'Sin descripción'}")
            item.setData(Qt.ItemDataRole.UserRole, (lote.id, lote.codigo))
            calc_page.lote_search_results.addItem(item)

    def on_lote_def_product_search_changed(self, text: str) -> None:
        """Busca productos para añadir a una plantilla de lote.

        Con caja vacía se listan todos (hasta el límite del repositorio) para poder
        eleger sin escribir; con texto se filtra por código o descripción.
        """
        lote_page = self._view.pages.get("definir_lote")
        if not lote_page: return

        q = (text or "").strip()
        results = self._product_service.search_products(q)
        lote_page.product_results.clear()
        for product in results:
            item = QListWidgetItem(f"{product.codigo} | {product.descripcion}")
            item.setData(Qt.ItemDataRole.UserRole, (product.codigo, product.descripcion))
            lote_page.product_results.addItem(item)

    def on_lote_def_fab_search_changed(self, text: str) -> None:
        """Busca fabricaciones para añadir a una plantilla de lote.

        Con caja vacía se listan todas las coincidencias del servicio (misma idea que productos).
        """
        lote_page = self._view.pages.get("definir_lote")
        if not lote_page: return

        q = (text or "").strip()
        results = self._fab_service.search_fabricaciones(q)
        lote_page.fab_results.clear()
        for fab in results:
            if fab.codigo and fab.codigo.startswith("TASK-"):
                continue
            label = f"{fab.codigo} - {fab.descripcion or 'Sin descripción'}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, (fab.id, fab.codigo))
            lote_page.fab_results.addItem(item)

    def on_add_product_to_lote_template(self) -> None:
        lote_page = self._view.pages.get("definir_lote")
        if not lote_page: return
        item = lote_page.product_results.currentItem()
        if not item: return
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            if "products" not in lote_page.lote_content:
                lote_page.lote_content["products"] = set()
            lote_page.lote_content["products"].add(data)
            lote_page.update_content_list()

    def on_add_fab_to_lote_template(self) -> None:
        lote_page = self._view.pages.get("definir_lote")
        if not lote_page: return
        item = lote_page.fab_results.currentItem()
        if not item: return
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            if "fabrications" not in lote_page.lote_content:
                lote_page.lote_content["fabrications"] = set()
            lote_page.lote_content["fabrications"].add(data)
            lote_page.update_content_list()

    def on_remove_item_from_lote_template(self) -> None:
        lote_page = self._view.pages.get("definir_lote")
        if not lote_page: return
        item = lote_page.lote_content_list.currentItem()
        if not item: return
        item_code = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(item_code, tuple) and len(item_code) == 2:
            item_type, data = item_code
            if item_type == "product":
                to_remove = [p for p in lote_page.lote_content.get("products", set()) if p[0] == data]
                for p in to_remove: lote_page.lote_content["products"].discard(p)
            elif item_type == "fabrication":
                to_remove = [f for f in lote_page.lote_content.get("fabrications", set()) if f[0] == data]
                for f in to_remove: lote_page.lote_content["fabrications"].discard(f)
            lote_page.update_content_list()

    def update_lotes_view(self) -> None:
        """Actualiza la lista de gestión de lotes."""
        gestion_page = self._view.pages.get("gestion_datos")
        if not gestion_page: return
        
        lotes_tab = gestion_page.lotes_tab
        search_query = lotes_tab.search_entry.text()
        lotes = self._db.search_lotes(search_query)

        lotes_tab.results_list.clear()
        for lote in lotes:
            item = QListWidgetItem(f"{lote.codigo} - {lote.descripcion or 'Sin descripción'}")
            item.setData(Qt.ItemDataRole.UserRole, lote.id)
            lotes_tab.results_list.addItem(item)
        
        if not search_query: lotes_tab.clear_edit_area()

    def save_lote_template(self) -> None:
        """Guarda una nueva plantilla de lote."""
        lote_page = self._view.pages.get("definir_lote")
        if not lote_page: return
        
        data = lote_page.get_data()
        if not data["codigo"]:
            self._view.show_message("Campo Requerido", "El código del lote es obligatorio.", "warning")
            return
            
        if not data["product_codes"] and not data["fabricacion_ids"]:
            self._view.show_message("Contenido Vacío", "La plantilla de lote debe contener al menos un producto o fabricación.", "warning")
            return

        lote_id = self._db.create_lote(data)
        if lote_id:
            self._view.show_message("Éxito", f"Plantilla de Lote '{data['codigo']}' guardada correctamente.", "info")
            lote_page.clear_form()
        else:
            self._view.show_message("Error al Guardar", "No se pudo guardar la plantilla.", "critical")

    def delete_lote_template(self, lote_id: int) -> None:
        """Elimina una plantilla de lote tras confirmación."""
        if self._view.show_confirmation_dialog("Confirmar", "¿Seguro que desea eliminar esta plantilla de lote?"):
            if self._db.delete_lote(lote_id):
                self._view.show_message("Éxito", "Plantilla de Lote eliminada.", "info")
                self.update_lotes_view()
            else:
                self._view.show_message("Error", "No se pudo eliminar la plantilla.", "critical")

    def update_lote_template(self, lote_id: int) -> None:
        gestion_page = self._view.pages.get("gestion_datos")
        if not gestion_page: return
        data = gestion_page.lotes_tab.get_form_data()
        if self._db.update_lote(lote_id, data):
            self._view.show_message("Éxito", "Plantilla actualizada.", "info")
            self.update_lotes_view()
        else:
            self._view.show_message("Error", "No se pudo actualizar.", "critical")
