# -*- coding: utf-8 -*-
"""
Contratos (Ports) para la gestión de generación de documentos.
"""

from typing import Protocol, List, Dict, Any, Optional
from pathlib import Path

class IDocumentGenerator(Protocol):
    """
    Protocolo que define cómo debe comportarse un generador de documentos
    sin acoplarse a librerías específicas (como python-docx).
    """

    def count_qr_placeholders(self, template_path: Path) -> int:
        """
        Cuenta los placeholders `{{qr}}` en el documento indicado.
        """
        ...

    def generate_labels(
        self,
        template_path: Path,
        datos_lista: List[Dict[str, str]],
        qr_generator: Any,
        output_path: str,
        qr_size_mm: int = 11
    ) -> Optional[str]:
        """
        Genera un documento reemplazando placeholders por los datos provistos.
        """
        ...

    def create_sample(self, format_name: str, output_path: Path) -> Optional[str]:
        """
        Crea un documento de ejemplo para un formato especificado ('A4', 'A5', etc.).
        """
        ...
