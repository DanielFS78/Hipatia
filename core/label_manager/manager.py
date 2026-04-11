# -*- coding: utf-8 -*-
"""
Nombre del Módulo: core.label_manager.manager

Descripción: Paquete: core.label_manager Descripción: Sistema de gestión y generación de etiquetas de trazabilidad.
"""

import logging
import tempfile
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple

from .base import LABEL_FORMATS
from . import printer
from .ports import IDocumentGenerator
from infrastructure.document_generator.docx_adapter import DocxGeneratorAdapter

class LabelManager:
    """
    Gestor central de plantillas y generación de documentos de etiquetas.
    
    Esta clase actúa como fachada para la generación de documentos, coordinando
    la búsqueda de plantillas, el recuento de placeholders y la invocación de
    los generadores adecuados (físicos o dinámicos).
    
    Attributes:
        LABEL_FORMATS (dict): Diccionario de formatos de etiquetas soportados.
    """
    LABEL_FORMATS = LABEL_FORMATS
    
    def __init__(
        self, 
        templates_dir: str = "templates", 
        qr_generator: Optional[Any] = None, 
        doc_generator: Optional[IDocumentGenerator] = None
    ) -> None:
        """
        Inicializa el gestor de etiquetas.
        
        Args:
            templates_dir: Directorio raíz donde residen las plantillas .docx.
            qr_generator: Instancia del generador de códigos QR únicos.
            doc_generator: Adaptador por defecto para generación de documentos.
        """
        self.logger = logging.getLogger("EvolucionTiemposApp.LabelManager")
        self.templates_dir = Path(templates_dir)
        self.qr_generator = qr_generator
        self.doc_generator = doc_generator or DocxGeneratorAdapter()
        self._ensure_template_structure()

    def _ensure_template_structure(self) -> None:
        try:
            for d in ["etiquetas/A5", "etiquetas/A4", "documentos"]:
                (self.templates_dir / d).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.error(f"Error creando estructura: {e}")

    def get_template_path(self, formato: str, nombre_plantilla: str) -> Optional[Path]:
        if formato in ['A5', 'A4']:
            ruta = self.templates_dir / "etiquetas" / formato / nombre_plantilla
        else:
            ruta = self.templates_dir / formato / nombre_plantilla
        return ruta if ruta.exists() else None

    def list_templates(self, formato: Optional[str] = None) -> List[Dict[str, Any]]:
        templates = []
        formatos = [formato] if formato else ['A5', 'A4', 'documentos']
        for fmt in formatos:
            path = self.templates_dir / ("etiquetas/" + fmt if fmt in ['A5', 'A4'] else fmt)
            if path.exists():
                for archivo in path.glob("*.docx"):
                    if not archivo.name.startswith('~'):
                        templates.append({
                            'nombre': archivo.name, 'formato': fmt, 'ruta': str(archivo),
                            'tamaño': archivo.stat().st_size,
                            'modificado': datetime.fromtimestamp(archivo.stat().st_mtime)
                        })
        return templates

    def _get_generator_and_path(self, plantilla: str, formato: str) -> Tuple[IDocumentGenerator, Optional[Path]]:
        """
        Determina el generador y la ruta de la plantilla (física o virtual).

        Soporta 'plantillas virtuales' como apli_1861_qr.docx que no requieren un archivo
        físico en el disco y usan generadores especializados de bajo nivel.

        Args:
            plantilla: Nombre del archivo de plantilla o identificador virtual.
            formato: Formato de la hoja (A5, A4, etc.).

        Returns:
            Tupla (Generador, Ruta/DummyPath).
        """
        if plantilla == "apli_1861_qr.docx":
            from infrastructure.document_generator.apli_adapter import Apli1861LabelGenerator
            # Para este generador, la ruta es virtual y el generador es especializado
            return Apli1861LabelGenerator(), Path("dynamic")
            
        path = self.get_template_path(formato, plantilla)
        return self.doc_generator, path

    def count_qr_placeholders(self, plantilla: str, formato: str) -> int:
        """
        Cuenta los espacios disponibles para QRs en la plantilla.

        Si la plantilla es virtual, delega en el generador especializado.
        Si es física, escanea el documento Word buscando el placeholder {{qr}}.

        Args:
            plantilla: Nombre de la plantilla.
            formato: Formato de la hoja.

        Returns:
            Número total de huecos para códigos QR.
        """
        try:
            generator, path = self._get_generator_and_path(plantilla, formato)
            if not path: return 0
            return generator.count_qr_placeholders(path)
        except Exception as e:
            self.logger.error(f"Error contando QR: {e}")
            return 0

    def generate_labels(self, plantilla: str, formato: str, datos_lista: List[Dict[str, str]], output_path: Optional[str] = None) -> Optional[str]:
        """Genera el documento de etiquetas."""
        try:
            generator_to_use, path = self._get_generator_and_path(plantilla, formato)
            if not path: return None
            
            if not output_path:
                output_path = os.path.join(tempfile.gettempdir(), f"etiquetas_{formato}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx")

            qr_size_mm = 11
            for _, fmt_val in self.LABEL_FORMATS.items():
                if isinstance(fmt_val, dict) and fmt_val.get('formato_hoja') == formato:
                    qr_size_mm = int(fmt_val.get('qr_size_mm', 11))
                    break

            return generator_to_use.generate_labels(path, datos_lista, self.qr_generator, output_path, qr_size_mm)
        except Exception as e:
            self.logger.error(f"Error generating etiquetas: {e}")
            return None

    def print_document(self, doc_path: str, printer_name: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        return printer.print_document(doc_path, printer_name)

    def create_sample_template(self, formato: str, nombre: str = "plantilla_ejemplo.docx") -> Optional[str]:
        try:
            out = self.templates_dir / ("etiquetas/" + formato if formato in ['A5', 'A4'] else formato) / nombre
            return self.doc_generator.create_sample(formato, out)
        except Exception as e:
            self.logger.error(f"Error creando ejemplo: {e}")
            return None

    # --- Proxy methods for Test Compatibility ---
    def _is_printer_available(self) -> bool:
        try:
            return printer.is_printer_available()
        except Exception as e:
            self.logger.warning(f"Error comprobando impresora: {e}")
            return False

    def _save_to_documents(self, doc_path: str) -> Optional[str]:
        try:
            return printer.save_to_documents(doc_path)
        except Exception as e:
            self.logger.error(f"Error guardando documento: {e}")
            return None

    def _open_file_location(self, file_path: str) -> None:
        try:
            printer.open_file_location(file_path)
        except Exception as e:
            self.logger.warning(f"No se pudo abrir la ubicación del archivo: {e}")

def quick_print_labels(datos: Dict[str, str], formato: str = 'A4', plantilla: str = 'plantilla_ejemplo.docx') -> bool:
    try:
        manager = LabelManager()
        path = manager.generate_labels(plantilla, formato, [datos])
        if path:
            ok, _ = manager.print_document(path)
            return ok
        return False
    except Exception:
        return False
