"""
Nombre del Módulo: core.interfaces.view_interface

Descripción: Define protocolos o tipos principales: ``IView``. Interfaz abstracta para la vista principal.
"""

from abc import abstractmethod
from typing import Any, Dict, Optional

class IView:
    """
    Interfaz abstracta para la vista principal.
    Define los métodos que el controlador puede invocar sin depender 
    de la implementación concreta de PyQt.
    """

    @abstractmethod
    def show_message(self, title: str, message: str, level: str = "info") -> None:
        """Muestra un mensaje al usuario."""
        pass

    @abstractmethod
    def show_confirmation_dialog(self, title: str, message: str) -> bool:
        """Muestra un diálogo de confirmación."""
        pass

    @abstractmethod
    def switch_page(self, page_name: str) -> None:
        """Cambia la página visible."""
        pass

    @abstractmethod
    def get_page(self, name: str) -> Any:
        """Obtiene una página (widget) específica por nombre."""
        pass

    @abstractmethod
    def get_products_tab(self) -> Any:
        """Retorna el widget de gestión de productos."""
        pass

    @abstractmethod
    def get_fabrications_tab(self) -> Any:
        """Retorna el widget de gestión de fabricaciones."""
        pass

    @property
    @abstractmethod
    def pages(self) -> Dict[str, Any]:
        """Diccionario de páginas registradas."""
        pass
