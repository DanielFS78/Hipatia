# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui.dialogs.fabrication.create_presenter
Descripción: Diálogo o presentador de fabricación: órdenes, preprocesos, productos y persistencia de pilas.
"""

from typing import List, Dict, Any, Tuple, Optional, TYPE_CHECKING
from core.dtos import FabricacionDTO, FabricacionProductoDTO

class CreateFabricacionPresenter:
    """
    Presenter para la creación de Fabricaciones, encargado de la gestión de estado.
    
    Responsabilidades:
    - Filtrar y ordenar listas de preprocesos y productos disponibles.
    - Mantener el estado de las asignaciones temporales (memoria de sesión).
    - Realizar la validación cruzada de datos (ej: código no vacío).
    - Mapear el estado interno a objetos `FabricacionDTO` y `FabricacionProductoDTO`.
    """
    def __init__(self, all_preprocesos: List[Any], all_products: Optional[List[Any]] = None):
        # We assume models have .id, .codigo, .nombre, .descripcion
        self.all_preprocesos = sorted(all_preprocesos, key=lambda x: getattr(x, 'id', 0), reverse=True)
        self.all_products = all_products if all_products else []
        
        self.assigned_preprocesos: Dict[int, Any] = {}
        self.assigned_products: Dict[str, Tuple[Any, int]] = {}

    def get_filtered_preprocesos(self, search_text: str) -> List[Any]:
        search_text = search_text.lower()
        filtered = []
        for p in self.all_preprocesos:
            if getattr(p, 'id', None) in self.assigned_preprocesos:
                continue
            
            text_to_search = f"{getattr(p, 'nombre', '')} {getattr(p, 'descripcion', '')}".lower()
            if search_text in text_to_search:
                filtered.append(p)
        return filtered

    def assign_preprocesos(self, preprocesos: List[Any]) -> None:
        for p in preprocesos:
            p_id = getattr(p, 'id', None)
            if p_id is not None and p_id not in self.assigned_preprocesos:
                self.assigned_preprocesos[p_id] = p

    def unassign_preprocesos(self, preprocesos: List[Any]) -> None:
        for p in preprocesos:
            p_id = getattr(p, 'id', None)
            if p_id in self.assigned_preprocesos:
                del self.assigned_preprocesos[p_id]

    def get_assigned_preprocesos(self) -> List[Any]:
        return sorted(self.assigned_preprocesos.values(), key=lambda x: getattr(x, 'nombre', ''))

    def get_filtered_products(self, search_text: str) -> List[Any]:
        search_text = search_text.lower()
        filtered = []
        for p in self.all_products:
            codigo = getattr(p, 'codigo', None)
            if codigo in self.assigned_products:
                continue
            
            text_to_search = f"{codigo} {getattr(p, 'descripcion', '')}".lower()
            if search_text in text_to_search:
                filtered.append(p)
        return filtered

    def assign_products(self, products: List[Any], default_qty: int = 1) -> None:
        for p in products:
            codigo = getattr(p, 'codigo', None)
            if codigo is not None and codigo not in self.assigned_products:
                self.assigned_products[codigo] = (p, default_qty)

    def unassign_products_by_code(self, codes: List[str]) -> None:
        for code in codes:
            if code in self.assigned_products:
                del self.assigned_products[code]

    def update_product_qty(self, code: str, qty: int) -> None:
        if code in self.assigned_products:
            data, _ = self.assigned_products[code]
            self.assigned_products[code] = (data, qty)

    def get_assigned_products(self) -> List[Tuple[Any, int]]:
        # Returns sorted by code
        keys = sorted(self.assigned_products.keys())
        return [self.assigned_products[k] for k in keys]

    def validate(self, codigo: str) -> Tuple[bool, str]:
        if not codigo.strip():
            return False, "El código de la fabricación es obligatorio."
        if not self.assigned_preprocesos and not self.assigned_products:
            return False, "Debe asignar al menos un preproceso O un producto a la fabricación."
        return True, ""

    def get_products_data(self) -> List[FabricacionProductoDTO]:
        """
        Retorna la lista de productos configurada como DTOs.
        """
        return [
            FabricacionProductoDTO(producto_codigo=code, cantidad=qty) 
            for code, (data, qty) in self.assigned_products.items()
        ]

    def get_fabricacion_data(self, codigo: str, descripcion: str) -> FabricacionDTO:
        products_list = self.get_products_data()
        return FabricacionDTO(
            id=0,
            codigo=codigo.strip(),
            descripcion=descripcion.strip(),
            preprocesos_ids=list(self.assigned_preprocesos.keys()),
            productos=products_list
        )
