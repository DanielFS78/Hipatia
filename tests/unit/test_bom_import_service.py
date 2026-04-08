# -*- coding: utf-8 -*-
"""
Tests unitarios para BOMImportService (clasificación import_selected / import_role).
"""

from __future__ import annotations

from unittest.mock import ANY, MagicMock, create_autospec

import pytest

from controllers.product.protocols import IProductService
from core.dtos_models import ProductDetailsDTO, ProductDTO
from core.import_manager.dto import BOMImportRole, BOMNodeDTO
from core.import_manager.services.bom_import_service import BOMImportService


@pytest.fixture
def mock_product_service() -> MagicMock:
    service = create_autospec(IProductService, instance=True, spec_set=True)
    service.get_product_by_code.return_value = None
    service.add_product.return_value = "SUCCESS"
    service.update_product.return_value = True
    mock_prod = ProductDTO(
        codigo="F1",
        descripcion="Final",
        departamento="Mecánica",
        donde="Taller",
        tiene_subfabricaciones=False,
        tiempo_optimo=1.0,
        tipo_trabajador=1,
    )
    service.get_product_details.return_value = ProductDetailsDTO(
        producto=mock_prod, subfabricaciones=[], procesos_mecanicos=[]
    )
    service.get_materials_for_product.return_value = []
    service.add_material.return_value = 501
    service.link_material_to_product.return_value = True
    return service


@pytest.fixture
def import_service(mock_product_service: MagicMock) -> BOMImportService:
    return BOMImportService(mock_product_service)


@pytest.mark.unit
class TestBOMImportService:
    def test_rejects_zero_or_two_finals(self, import_service: BOMImportService) -> None:
        root = BOMNodeDTO(
            nivel=0,
            codigo_componente="A",
            import_selected=True,
            import_role=BOMImportRole.SUBFABRICATION,
        )
        stats = import_service.import_bom_tree(root)
        assert stats["errores"] >= 1

        b = BOMNodeDTO(
            nivel=0,
            codigo_componente="B",
            import_selected=True,
            import_role=BOMImportRole.FINAL_PRODUCT,
        )
        c = BOMNodeDTO(
            nivel=0,
            codigo_componente="C",
            import_selected=True,
            import_role=BOMImportRole.FINAL_PRODUCT,
        )
        root2 = BOMNodeDTO(nivel=0, codigo_componente="R", denominacion="")
        root2.hijos.extend([b, c])
        stats2 = import_service.import_bom_tree(root2)
        assert stats2["errores"] >= 1

    def test_import_final_only_creates_and_updates(
        self, import_service: BOMImportService, mock_product_service: MagicMock
    ) -> None:
        final = BOMNodeDTO(
            nivel=0,
            codigo_componente="F1",
            denominacion="Producto final",
            import_selected=True,
            import_role=BOMImportRole.FINAL_PRODUCT,
        )
        stats = import_service.import_bom_tree(final)
        assert stats["errores"] == 0
        assert stats["creados"] >= 1
        mock_product_service.add_product.assert_called()
        mock_product_service.update_product.assert_called_once_with("F1", ANY, ANY)

    def test_import_final_with_subfab_and_process(
        self, import_service: BOMImportService, mock_product_service: MagicMock
    ) -> None:
        final = BOMNodeDTO(
            nivel=0,
            codigo_componente="F1",
            denominacion="Final",
            import_selected=True,
            import_role=BOMImportRole.FINAL_PRODUCT,
        )
        sub = BOMNodeDTO(
            nivel=1,
            codigo_componente="S1",
            denominacion="Sub",
            cantidad=2.0,
            import_selected=True,
            import_role=BOMImportRole.SUBFABRICATION,
        )
        proc = BOMNodeDTO(
            nivel=1,
            codigo_componente="OP1",
            denominacion="Fresado",
            import_selected=True,
            import_role=BOMImportRole.MECHANICAL_PROCESS,
        )
        final.hijos.extend([sub, proc])

        stats = import_service.import_bom_tree(final)
        assert stats["errores"] == 0
        assert stats["subfabricaciones_vinculadas"] == 1
        assert stats["procesos_mecanicos"] == 1
        # Solo el producto final se crea en catálogo; la subfabricación es fila del padre.
        assert mock_product_service.add_product.call_count == 1

        args, kwargs = mock_product_service.update_product.call_args
        assert args[0] == "F1"
        sub_list = args[2]
        assert isinstance(sub_list, list)
        assert any(row.get("id") == "S1" for row in sub_list)
        assert any("S1" in str(row.get("descripcion", "")) for row in sub_list)
        prod_payload = args[1]
        assert "procesos_mecanicos" in prod_payload
        assert any(p.get("nombre") == "OP1" for p in prod_payload["procesos_mecanicos"])

    def test_import_component_links_material(
        self, import_service: BOMImportService, mock_product_service: MagicMock
    ) -> None:
        final = BOMNodeDTO(
            nivel=0,
            codigo_componente="F1",
            import_selected=True,
            import_role=BOMImportRole.FINAL_PRODUCT,
        )
        comp = BOMNodeDTO(
            nivel=1,
            codigo_componente="M1",
            denominacion="Chapa",
            import_selected=True,
            import_role=BOMImportRole.COMPONENT,
        )
        final.hijos.append(comp)

        stats = import_service.import_bom_tree(final)
        assert stats["errores"] == 0
        assert stats["componentes"] == 1
        mock_product_service.add_material.assert_called_once_with("M1", "Chapa")
        mock_product_service.link_material_to_product.assert_called_once_with("F1", 501)

    def test_unselected_nodes_ignored(
        self, import_service: BOMImportService, mock_product_service: MagicMock
    ) -> None:
        final = BOMNodeDTO(
            nivel=0,
            codigo_componente="F1",
            import_selected=True,
            import_role=BOMImportRole.FINAL_PRODUCT,
        )
        ghost = BOMNodeDTO(
            nivel=1,
            codigo_componente="X99",
            import_selected=False,
            import_role=None,
        )
        final.hijos.append(ghost)

        stats = import_service.import_bom_tree(final)
        assert stats["errores"] == 0
        created = [call[0][0]["codigo"] for call in mock_product_service.add_product.call_args_list]
        assert "X99" not in created

    def test_single_final_in_tree_no_infinite_loop(
        self, import_service: BOMImportService, mock_product_service: MagicMock
    ) -> None:
        """Árbol con ciclo en hijos no afecta: solo se importa el nodo marcado como final."""
        nodo1 = BOMNodeDTO(
            nivel=0,
            codigo_componente="N1",
            import_selected=True,
            import_role=BOMImportRole.FINAL_PRODUCT,
        )
        nodo2 = BOMNodeDTO(nivel=1, codigo_componente="N2", import_selected=False)
        nodo1.hijos.append(nodo2)
        nodo2.hijos.append(nodo1)

        stats = import_service.import_bom_tree(nodo1)
        assert isinstance(stats, dict)
        assert stats["errores"] == 0
