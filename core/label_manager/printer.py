# core/labels/printer.py

"""
Lógica o utilidades del núcleo (`printer`): tipos, servicios auxiliares o infraestructura compartida fuera de la capa de interfaz.
"""

import os
import subprocess
import platform
import shutil
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger("EvolucionTiemposApp.LabelManager.Printer")

def is_printer_available() -> bool:
    """Comprueba si hay una impresora predeterminada configurada."""
    try:
        system = platform.system()
        if system in ['Darwin', 'Linux']:
            result = subprocess.run(['lpstat', '-d'], capture_output=True, text=True, timeout=5)
            if 'no system default destination' in result.stdout.lower() or (system == 'Linux' and result.returncode != 0):
                return False
            return True
        elif system == 'Windows':
            return True
        return True
    except Exception as e:
        logger.warning(f"Error comprobando impresora: {e}")
        return False

def save_to_documents(doc_path: str) -> Optional[str]:
    """Guarda el documento en la carpeta de Documentos del usuario."""
    try:
        home = Path.home()
        etiquetas_dir = home / "Documents" / "Etiquetas"
        etiquetas_dir.mkdir(parents=True, exist_ok=True)
        dest_path = etiquetas_dir / Path(doc_path).name
        shutil.copy2(doc_path, dest_path)
        return str(dest_path)
    except Exception as e:
        logger.error(f"Error guardando documento: {e}")
        return None

def open_file_location(file_path: str) -> None:
    """Abre la ubicación del archivo en el explorador de archivos."""
    try:
        system = platform.system()
        if system == 'Darwin':
            subprocess.run(['open', '-R', file_path])
        elif system == 'Windows':
            subprocess.run(['explorer', '/select,', file_path])
        elif system == 'Linux':
            subprocess.run(['xdg-open', str(Path(file_path).parent)])
    except Exception as e:
        logger.warning(f"No se pudo abrir la ubicación del archivo: {e}")

def print_document(doc_path: str, printer_name: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """Envía un documento a imprimir o lo guarda si no hay impresora."""
    try:
        if not is_printer_available():
            saved_path = save_to_documents(doc_path)
            if saved_path:
                open_file_location(saved_path)
                return (True, saved_path)
            return (False, None)

        system = platform.system()
        if system == 'Windows':
            os.startfile(doc_path, 'print') # type: ignore[attr-defined]
            return (True, None)
        elif system == 'Linux':
            cmd = ['lp']
            if printer_name: cmd.extend(['-d', printer_name])
            cmd.append(doc_path)
            subprocess.run(cmd, check=True)
            return (True, None)
        elif system == 'Darwin':
            cmd = ['lpr']
            if printer_name: cmd.extend(['-P', printer_name])
            cmd.append(doc_path)
            subprocess.run(cmd, check=True)
            return (True, None)
        return (False, None)
    except Exception as e:
        logger.error(f"Error al imprimir: {e}")
        return (False, None)
