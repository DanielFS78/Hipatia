# -*- coding: utf-8 -*-
"""
Tests unitarios para BOMImportService.
Verifica que el servicio inyecte correctamente el árbol en el ProductService.
"""

import pytest
from unittest.mock import MagicMock, create_autospec, ANY

from core.import_manager.services.bom_import_service import BOMImportService
from core.import_manager.dto import BOMNodeDTO
from core.dtos_models import ProductDetailsDTO, ProductDTO
from controllers.product.protocols import IProductService

@pytest.fixture
def mock_product_service() -> MagicMock:
    """Crea un mock estricto del servicio de productos."""
    service = create_autospec(IProductService, spec_set=True)
    # Retornar none por defecto (producto no existe)
    service.get_product_by_code.return_value = None
    service.add_product.return_value = "SUCCESS"
    service.update_product.return_value = True
    
    # Mocking product details for dependency update
    mock_prod = ProductDTO(
        codigo="DUMMY",
        descripcion="Dummy Desc",
        departamento="Montaje",
        donde="Almacén",
        tiene_subfabricaciones=True,
        tiempo_optimo=10.0,
        tipo_trabajador=1
    )
    service.get_product_details.return_value = ProductDetailsDTO(producto=mock_prod, subfabricaciones=[], procesos_mecanicos=[])
    
    return service

@pytest.fixture
def import_service(mock_product_service: MagicMock) -> BOMImportService:
    """Proporciona una instancia del servicio de importación con mocks inyectados."""
    return BOMImportService(mock_product_service)

@pytest.mark.unit
class TestBOMImportService:
    """Suite de pruebas para validar el servicio de importación BOM."""
    
    def test_import_single_new_node(self, import_service: BOMImportService, mock_product_service: MagicMock) -> None:
        """Test importando un árbol de un solo nodo que no existe."""
        node = BOMNodeDTO(nivel=0, codigo_componente="P1", denominacion="Prod 1", es_subfabricacion=True, cantidad=1.0)
        
        stats = import_service.import_bom_tree(node)
        
        assert isinstance(stats, dict)
        assert stats['creados'] == 1
        assert stats['actualizados'] == 0
        assert stats['errores'] == 0
        
        mock_product_service.add_product.assert_called_once_with(ANY, [])
        args, _ = mock_product_service.add_product.call_args
        new_data = args[0]
        assert isinstance(new_data, dict)
        assert new_data["codigo"] == "P1"
        assert new_data["descripcion"] == "Prod 1"
        assert new_data["tiene_subfabricaciones"] == 0 # No tiene hijos

    def test_import_existing_node_with_children(self, import_service: BOMImportService, mock_product_service: MagicMock) -> None:
        """Test importando un nodo que ya existe, con un hijo que se convierte en subfabricación."""
        mock_product_service.get_product_by_code.side_effect = lambda code: "Exists" if code == "PADRE" else None
        
        hijo = BOMNodeDTO(nivel=1, codigo_componente="HIJO", denominacion="Sub 1", es_subfabricacion=True, cantidad=2.5)
        padre = BOMNodeDTO(nivel=0, codigo_componente="PADRE", denominacion="Padre", es_subfabricacion=True, cantidad=1.0)
        padre.hijos.append(hijo)
        
        stats = import_service.import_bom_tree(padre)
        
        assert isinstance(stats, dict)
        # El padre se actualiza, el hijo se crea
        assert stats['creados'] == 1
        assert stats['actualizados'] == 1
        
        # El padre debe haber intentado hacer un update_product con las dependencias
        mock_product_service.update_product.assert_called_once_with("PADRE", ANY, ANY)
        args, _ = mock_product_service.update_product.call_args
        
        # Las subfabricaciones enviadas al update deben ser el hijo
        subfab_list = args[2]
        assert isinstance(subfab_list, list)
        assert len(subfab_list) == 1
        assert subfab_list[0]["id"] == "HIJO"
        assert subfab_list[0]["cantidad"] == 2.5

    def test_import_ignore_non_subfab_children(self, import_service: BOMImportService, mock_product_service: MagicMock) -> None:
        """Test que los hijos marcados como es_subfabricacion=False NO se añaden como dependencia, solo se crean."""
        hijo = BOMNodeDTO(nivel=1, codigo_componente="HIJO", denominacion="Material", es_subfabricacion=False, cantidad=10.0)
        padre = BOMNodeDTO(nivel=0, codigo_componente="PADRE", denominacion="Padre", es_subfabricacion=True, cantidad=1.0)
        padre.hijos.append(hijo)
        
        stats = import_service.import_bom_tree(padre)
        
        assert isinstance(stats, dict)
        # Ambos se crean (porque el padre no existía por defecto)
        assert stats['creados'] == 2
        
        # Pero el padre hace un update SIN dependencias, porque el hijo no fue subfabricación
        mock_product_service.update_product.assert_not_called()

    def test_circular_dependency_protection(self, import_service: BOMImportService) -> None:
        """Test para verificar que no entra en loop infinito si el árbol está corrupto."""
        nodo1 = BOMNodeDTO(nivel=0, codigo_componente="N1")
        nodo2 = BOMNodeDTO(nivel=1, codigo_componente="N2")
        
        nodo1.hijos.append(nodo2)
        nodo2.hijos.append(nodo1) # Ciclo malicioso
        
        # No debe crashear con stack overflow
        stats = import_service.import_bom_tree(nodo1)
        assert isinstance(stats, dict)
        assert stats['creados'] == 2 # Crea N1 y N2, pero frena en el ciclo
