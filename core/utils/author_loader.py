# -*- coding: utf-8 -*-
"""
Nombre del Módulo: author_loader.py
Descripción: Utilidad para cargar dinámicamente información sobre los autores 
             y colaboradores del proyecto.
"""
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable
from core.quote_service import QuoteService

class WorkerSignals(QObject):
    """Señales para el worker de carga de info de autor."""
    finished = pyqtSignal(object)

class AuthorInfoLoader(QRunnable):
    """
    Worker para cargar información de Wikipedia en segundo plano sin bloquear la UI.
    """
    def __init__(self, service: QuoteService, author_name: str) -> None:
        super().__init__()
        self.service = service
        self.author_name = author_name
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            # Esta llamada puede tardar unos segundos
            # Ahora devuelve un AuthorInfoDTO
            info = self.service.get_author_info(self.author_name)
            self.signals.finished.emit(info)
        except Exception:
            self.signals.finished.emit(None)
