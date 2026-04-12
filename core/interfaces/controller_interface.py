"""
Nombre del Módulo: core.interfaces.controller_interface

Descripción: Define protocolos o tipos principales: ``QABCMeta``, ``IController``. Interface base para todos los controladores de la aplicación. Integración típica con: ``PyQt6``.
"""

import logging
from abc import ABCMeta, abstractmethod
from typing import Optional
from PyQt6.QtCore import QObject

# Metaclass to resolve conflict between QObject's metaclass and ABCMeta
class QABCMeta(type(QObject), ABCMeta):  # type: ignore[misc]
    pass

class IController(QObject, metaclass=QABCMeta):
    """
    Interface base para todos los controladores de la aplicación.
    Hereda de QObject para permitir el uso de señales y slots.
    Establece un contrato estándar para inicialización, limpieza y manejo de errores.
    """

    @abstractmethod
    def initialize(self) -> None:
        """
        Configura los recursos necesarios, conecta señales y prepara el controlador para su uso.
        Debe ser llamado explícitamente después de la instanciación si es necesario, 
        o como parte del __init__ si no hay dependencias circulares.
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """
        Libera recursos, desconecta señales y realiza tareas de limpieza antes de destruir el controlador.
        Critical para prevenir memory leaks en aplicaciones PyQt.
        """
        pass

    def handle_error(self, error: Exception, context: str = "") -> None:
        """
        Manejo estándar de errores. Puede ser sobreescrito por subclases.
        
        Args:
            error: La excepción capturada.
            context: Descripción opcional del contexto donde ocurrió el error.
        """
        # Por defecto, solo relanzamos o logueamos. 
        # En una implementación real, esto podría conectar con un servicio de logging centralizado.
        logger = logging.getLogger("EvolucionTiemposApp.IController")
        logger.error(f"Error en controlador ({context}): {str(error)}")
        # raise error # Dependiendo de la estrategia de errores, podríamos relanzar o silenciar.
