# -*- coding: utf-8 -*-
"""
Nombre del Módulo: file_controller
Descripción: Gestiona la persistencia de archivos adjuntos, la apertura de documentos 
             del sistema y la importación de datos externos en formato JSON.
"""
from __future__ import annotations

import os
import shutil
import json
import logging
from typing import Any
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QObject, pyqtSignal, QUrl
from database.database_manager import DatabaseManager
from core.dtos import FileOperationResultDTO


class FileController(QObject):
    """
    Controlador dedicado a la gestión de archivos y persistencia de datos externos.
    
    Proporciona utilidades para adjuntar imágenes o planos a productos/fabricaciones,
    visualizar archivos usando aplicaciones del sistema y procesar importaciones JSON 
    de tareas y registros de trabajo.
    """
    
    # Signals
    file_attached = pyqtSignal(str)  # ruta del archivo adjuntado
    import_completed = pyqtSignal()
    
    def __init__(self, db_manager: DatabaseManager, view: Any, logger: logging.Logger) -> None:
        """
        Inicializa el controlador de archivos.

        Args:
            db_manager: Gestor de conexión a la base de datos para operaciones de persistencia.
            view: Referencia a la vista principal para mostrar diálogos de archivo.
            logger: Instancia para el registro de operaciones de sistema de archivos.
        """
        super().__init__()
        self.db: DatabaseManager = db_manager
        self.view: Any = view
        self.logger: logging.Logger = logger
        
    def handle_attach_file(
        self, 
        owner_type: str, 
        owner_id: int, 
        source_file_path: str, 
        file_type: str
    ) -> FileOperationResultDTO:
        """
        Copia un archivo externo al directorio de datos del sistema y genera una ruta relativa.

        Args:
            owner_type: Tipo de entidad (p. ej. 'producto', 'fabricacion').
            owner_id: Identificador de la entidad.
            source_file_path: Ruta absoluta del archivo de origen.
            file_type: Categoría del archivo (p. ej. 'imagen', 'plano').

        Returns:
            FileOperationResultDTO: Resultado de la operación con estado y ruta o error.
        """
        self.logger.info(f"Adjuntando archivo '{source_file_path}' a {owner_type} ID {owner_id}.")
        try:
            # data/imagenes/iteration_1.jpg | data/planos/iteration_1.pdf
            target_dir = os.path.join("data", f"{file_type}s")
            os.makedirs(target_dir, exist_ok=True)

            _, file_extension = os.path.splitext(source_file_path)
            new_filename = f"{owner_type}_{owner_id}{file_extension}"
            destination_path = os.path.join(target_dir, new_filename)

            # Aseguramos que el subdirectorio final exista
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)

            shutil.copy(source_file_path, destination_path)

            relative_path = os.path.join("data", f"{file_type}s", new_filename).replace("\\", "/")
            self.logger.info(f"Archivo guardado en '{destination_path}'. Ruta relativa: '{relative_path}'")
            
            self.file_attached.emit(relative_path)
            return FileOperationResultDTO(success=True, path_or_error=relative_path)
        except Exception as e:
            self.logger.error(f"Error al adjuntar archivo: {e}", exc_info=True)
            return FileOperationResultDTO(success=False, path_or_error=str(e))
        
    def handle_view_file(self, relative_path: str) -> None:
        """
        Abre un archivo usando el visor por defecto del sistema.
        
        Args:
            relative_path: Ruta relativa del archivo
        """
        if not relative_path:
            self.logger.warning("No se proporcionó ruta de archivo para visualizar.")
            return

        # Convertir ruta relativa a absoluta
        abs_path = os.path.abspath(relative_path)

        if not os.path.exists(abs_path):
            self.logger.error(f"El archivo no existe: {abs_path}")
            self.view.show_message(
                "Archivo No Encontrado",
                f"No se pudo encontrar el archivo:\\n{abs_path}",
                "warning"
            )
            return

        # Abrir archivo con aplicación predeterminada
        try:
            url = QUrl.fromLocalFile(abs_path)
            QDesktopServices.openUrl(url)
            self.logger.info(f"Archivo abierto: {abs_path}")
        except Exception as e:
            self.logger.error(f"Error al abrir archivo: {e}", exc_info=True)
            self.view.show_message("Error", f"No se pudo abrir el archivo:\\n{e}", "critical")
        
    def on_import_task_data(self) -> None:
        """
        Inicia un diálogo para importar datos de tareas desde un archivo JSON.
        Fusiona la información importada con la base de datos de tracking local.
        """
        self.logger.info("Iniciando importación de datos de tareas...")

        file_path, _ = QFileDialog.getOpenFileName(
            self.view,
            "Seleccionar Archivo JSON de Tareas",
            "",
            "Archivos JSON (*.json)"
        )

        if not file_path:
            self.logger.info("Importación de tareas cancelada.")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data_to_import = json.load(f)

            if not isinstance(data_to_import, list):
                raise ValueError("El archivo JSON no contiene una lista de trabajos.")

            if not self.view.show_confirmation_dialog(
                    "Confirmar Importación",
                    f"Se encontraron {len(data_to_import)} registros de trabajo en el archivo.\\n"
                    "¿Desea fusionar estos datos con la base de datos central?\\n\\n"
                    "(Los registros existentes se omitirán o actualizarán)."
            ):
                return

            # Procesar la importación
            stats = {'created': 0, 'updated': 0, 'skipped': 0, 'error': 0}

            for trabajo_data in data_to_import:
                status, _ = self.db.tracking_repo.upsert_trabajo_log_from_dict(trabajo_data)

                # Actualizar el contador de estadísticas
                if status in stats:
                    stats[status] += 1

            self.logger.info(f"Importación de tareas completada: {stats}")
            self.view.show_message(
                "Importación Completa",
                f"Importación de datos de tareas finalizada:\\n\\n"
                f"Nuevos: {stats['created']}\\n"
                f"Actualizados: {stats['updated']}\\n"
                f"Omitidos: {stats['skipped']}\\n"
                f"Errores: {stats['error']}",
                "info"
            )
            
            self.import_completed.emit()

        except json.JSONDecodeError:
            self.logger.error(f"Error: El archivo {file_path} no es un JSON válido.")
            self.view.show_message("Error de Archivo", "El archivo seleccionado no es un JSON válido.", "critical")
        except Exception as e:
            self.logger.error(f"Error crítico durante la importación de tareas: {e}", exc_info=True)
            self.view.show_message("Error Crítico", f"Ocurrió un error inesperado: {e}", "critical")
        
    def on_data_after_import(self) -> None:
        """Callback auxiliar para actualizar UI después de importar backup."""
        # Este método será llamado por BackupController después de una importación
        self.logger.info("Actualizando vistas después de importación...")
        self.import_completed.emit()

