# -*- coding: utf-8 -*-
"""
Nombre del Módulo: protocols.py
Descripción: Define las interfaces (Protocolos) necesarias para que los gestores 
             de Lotes y Pilas interactúen con la Vista y la Base de Datos de 
             forma desacoplada.
"""
from typing import Protocol, List, Dict, Any, Optional, Tuple
from core.dtos import ProductDTO, LoteDTO, FabricacionDTO, PilaDTO

class IPilaView(Protocol):
    """Interfaz para la vista que maneja Pilas y Lotes."""
    pages: Dict[str, Any]
    
    def show_message(self, title: str, message: str, level: str = "info") -> None: ...
    def show_confirmation_dialog(self, title: str, message: str) -> bool: ...

class IPilaDatabase(Protocol):
    """Interfaz para el acceso a datos relacionado con Pilas."""

    @property
    def lote_repo(self) -> Any: ...

    @property
    def preproceso_repo(self) -> Any: ...

    def search_lotes(self, query: str) -> List[LoteDTO]: ...
    def get_lote_details(self, lote_id: int) -> Optional[LoteDTO]: ...
    def create_lote(self, data: Dict[str, Any]) -> Optional[int]: ...
    def update_lote(self, lote_id: int, data: Dict[str, Any]) -> bool: ...
    def delete_lote(self, lote_id: int) -> bool: ...

class IPilaService(Protocol):
    """Interfaz para el servicio de Pilas."""
    def get_all_pilas(self) -> List[Any]: ...
    def load_pila(self, pila_id: int) -> Tuple[PilaDTO | None, Any, Any, Any]: ...
    def save_pila(
        self,
        nombre: str,
        descripcion: str,
        pila_de_calculo: Dict[str, Any],
        production_flow: List[Any],
        simulation_results: List[Any],
        producto_origen_codigo: Optional[str] = ...,
        unidades: int = ...,
    ) -> Any: ...
    def delete_pila(self, pila_id: int) -> bool: ...

class IProductService(Protocol):
    """Interfaz para el servicio de Productos."""
    def search_products(self, text: str) -> List[ProductDTO]: ...

class IFabricacionService(Protocol):
    """Interfaz para el servicio de Fabricaciones."""
    def search_fabricaciones(self, text: str) -> List[FabricacionDTO]: ...
