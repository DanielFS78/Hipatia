"""
Lógica o utilidades del núcleo (`ports`): tipos, servicios auxiliares o infraestructura compartida fuera de la capa de interfaz.
"""

from typing import Protocol
from core.import_manager.dto import BOMNodeDTO

class IBOMImporter(Protocol):
    def parse_file(self, file_path: str) -> BOMNodeDTO:
        """Debe leer un archivo y devolver la raíz del árbol de fabricación (BOMNodeDTO)"""
        pass
