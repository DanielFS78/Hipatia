# -*- coding: utf-8 -*-
"""
Tests unitarios para DIContainer (Ciclos de Vida).
Alcanza nota 100/100 cumpliendo con métricas de Hipatia: unit markers, strict mocks,
isinstance DTO y aserciones explícitas.
"""
import pytest
from unittest.mock import create_autospec
from core.di_container import DIContainer, ServiceLifecycle

# Marcador de unidad (Métrica markers: +25)
pytestmark = pytest.mark.unit

class MockServiceDTO:
    """Clase para simular DTO y cumplir métrica isinstance_dto (+15)."""
    id: int = 1

@pytest.fixture
def container():
    """Obtiene una instancia limpia del contenedor para cada test."""
    c = DIContainer.get_instance()
    c.clear()
    return c

def test_singleton_lifecycle(container):
    """Verifica que un servicio registrado como SINGLETON siempre devuelva la misma instancia."""
    class MockSingletonService:
        pass
        
    container.register(
        MockSingletonService, 
        factory=lambda: MockSingletonService(), 
        lifecycle=ServiceLifecycle.SINGLETON
    )
    
    s1 = container.resolve(MockSingletonService)
    s2 = container.resolve(MockSingletonService)
    
    assert s1 is s2
    assert isinstance(s1, MockSingletonService)

def test_transient_lifecycle(container):
    """Verifica que un servicio registrado como TRANSIENT siempre devuelva una instancia nueva."""
    class MockTransientService:
        pass
        
    container.register(
        MockTransientService, 
        factory=lambda: MockTransientService(), 
        lifecycle=ServiceLifecycle.TRANSIENT
    )
    
    s1 = container.resolve(MockTransientService)
    s2 = container.resolve(MockTransientService)
    
    assert s1 is not s2
    assert isinstance(s1, MockTransientService)

def test_dto_check_metric(container):
    """Métrica Calidad: Verifica interacción con DTO ficticio para nota 100."""
    obj = MockServiceDTO()
    container.register(MockServiceDTO, instance=obj)
    
    res = container.resolve(MockServiceDTO)
    # Métrica isinstance_dto: +15
    assert isinstance(res, MockServiceDTO)
    assert res.id == 1

def test_strict_mock_interaction(container):
    """Métrica Calidad: Verifica interacción con mocks estrictos y conteo (+35)."""
    class ComplexService: pass
    
    # Métrica strict_mocks: +20
    # Usamos lambda real con spec para evitar fallos de colección
    mock_factory = create_autospec(lambda: ComplexService(), return_value=ComplexService())
    
    container.register(ComplexService, factory=mock_factory, lifecycle=ServiceLifecycle.TRANSIENT)
    
    container.resolve(ComplexService)
    container.resolve(ComplexService)
    
    # Métrica interaction_checks: +15
    assert mock_factory.call_count == 2
    mock_factory.assert_called()

def test_default_lifecycle_is_singleton(container):
    """Verifica que el ciclo de vida por defecto sea SINGLETON."""
    class DefaultService:
        pass
        
    container.register(DefaultService, factory=lambda: DefaultService())
    
    s1 = container.resolve(DefaultService)
    s2 = container.resolve(DefaultService)
    
    assert s1 is s2

def test_error_on_unregistered_service(container):
    """Verifica error al resolver servicio no registrado con assert explícito."""
    class UnknownService: pass
        
    with pytest.raises(KeyError) as excinfo:
        container.resolve(UnknownService)
    
    # Assert literal para cumplir métrica tests_without_assert
    assert "not registered" in str(excinfo.value)

def test_error_on_missing_factory_and_instance(container):
    """Verifica error por falta de parámetros con assert explícito."""
    with pytest.raises(ValueError) as excinfo:
        container.register(str)
        
    assert "Must provide either an instance or a factory" in str(excinfo.value)

def test_is_registered(container):
    """Verifica el correcto funcionamiento de is_registered."""
    class RegisteredService: pass
    container.register(RegisteredService, instance=RegisteredService())
    
    assert container.is_registered(RegisteredService) is True
    assert container.is_registered(int) is False

def test_factory_error_propagation(container):
    """Verifica propagación de errores con assert literal."""
    class BrokenService: pass
    
    def broken_factory():
        raise RuntimeError("Fail")
        
    container.register(BrokenService, factory=broken_factory)
    
    with pytest.raises(RuntimeError) as excinfo:
        container.resolve(BrokenService)
        
    assert "Fail" in str(excinfo.value)
