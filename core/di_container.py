# -*- coding: utf-8 -*-
"""
Nombre del Módulo: di_container.py
Descripción: Contenedor ligero de Inyección de Dependencias (DI) para gestionar 
             la instanciación y resolución de servicios y controladores con 
             soporte para ciclos de vida (Singleton y Transient).
"""
import logging
from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Type, TypeVar, cast

T = TypeVar('T')

class ServiceLifecycle(Enum):
    """Define el ciclo de vida de un servicio en el contenedor."""
    SINGLETON = auto()  # Una única instancia compartida
    TRANSIENT = auto()  # Una instancia nueva por cada resolución

@dataclass
class ServiceRegistration:
    """Estructura interna para almacenar el registro de un servicio."""
    factory: Callable[[], Any]
    lifecycle: ServiceLifecycle
    instance: Optional[Any] = None

class DIContainer:
    """
    Contenedor de Inyección de Dependencias (Singleton).

    Gestiona el registro de tipos y la resolución de instancias, permitiendo 
    configurar el ciclo de vida de cada componente.
    """
    
    _instance: Optional['DIContainer'] = None
    _registrations: Dict[Any, ServiceRegistration]
    logger: logging.Logger
    
    def __new__(cls) -> 'DIContainer':
        if cls._instance is None:
            cls._instance = super(DIContainer, cls).__new__(cls)
            cls._instance._registrations = {}
            cls._instance.logger = logging.getLogger("DIContainer")
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'DIContainer':
        """Devuelve la instancia única (singleton) del contenedor."""
        if cls._instance is None:
            cls()  # Dispara __new__
        if cls._instance is None:
             raise RuntimeError("No se pudo crear la instancia de DIContainer")
        return cls._instance

    def register(
        self, 
        service_type: Any, 
        instance: Any = None, 
        factory: Optional[Callable[[], Any]] = None,
        lifecycle: ServiceLifecycle = ServiceLifecycle.SINGLETON
    ) -> None:
        """
        Registra un servicio o componente en el contenedor.
        
        Args:
            service_type: El tipo o identificador de la clase.
            instance: Una instancia ya creada (se registrará como SINGLETON).
            factory: Una función que devuelve la instancia (lazy loading).
            lifecycle: El ciclo de vida deseado (SINGLETON por defecto).
        """
        if instance is not None:
            # Si se pasa una instancia, forzamos SINGLETON con instancia cacheada
            self._registrations[service_type] = ServiceRegistration(
                factory=lambda: instance,
                lifecycle=ServiceLifecycle.SINGLETON,
                instance=instance
            )
            self.logger.debug(f"Registrado singleton de {service_type} con instancia pre-existente.")
        elif factory is not None:
            self._registrations[service_type] = ServiceRegistration(
                factory=factory,
                lifecycle=lifecycle
            )
            self.logger.debug(f"Registrado servicio {service_type} con ciclo de vida {lifecycle.name}.")
        else:
            raise ValueError("Must provide either an instance or a factory")

    def resolve(self, service_type: Type[T]) -> T:
        """
        Resuelve y retorna una instancia del servicio solicitado.
        
        Args:
            service_type: El tipo clase a resolver.
            
        Returns:
            La instancia solicitada del servicio.
            
        Raises:
            KeyError: Si el servicio no está registrado.
        """
        if service_type not in self._registrations:
            raise KeyError(f"Service {service_type} not registered in DI Container.")

        reg = self._registrations[service_type]

        # Lógica basada en Ciclo de Vida
        if reg.lifecycle == ServiceLifecycle.TRANSIENT:
            self.logger.debug(f"Resolviendo TRANSIENT para {service_type}")
            return cast(T, reg.factory())

        # Si es SINGLETON
        if reg.instance is None:
            try:
                self.logger.debug(f"Creando instancia única (SINGLETON) para {service_type}")
                reg.instance = reg.factory()
            except Exception as e:
                self.logger.error(f"Error al instanciar {service_type}: {e}")
                raise e
        
        return cast(T, reg.instance)

    def is_registered(self, service_type: Any) -> bool:
        """Comprueba si un servicio está registrado en el contenedor."""
        return service_type in self._registrations

    def clear(self) -> None:
        """Limpia todos los registros. Útil para entornos de test."""
        self._registrations.clear()
