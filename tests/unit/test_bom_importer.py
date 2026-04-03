import pytest
from unittest.mock import create_autospec, MagicMock

from core.import_manager.dto import BOMNodeDTO
from core.import_manager.adapters.a3rp_csv_adapter import A3RPCSVAdapter


def test_bom_node_dto_creation():
    nodo = BOMNodeDTO(
        nivel=0,
        capitulo="CAP1",
        codigo_componente="COMP_MAESTRO",
        denominacion="Componente Maestro",
        es_subfabricacion=True,
        cantidad=1.0
    )
    assert nodo.nivel == 0
    assert nodo.capitulo == "CAP1"
    assert nodo.codigo_componente == "COMP_MAESTRO"
    assert nodo.denominacion == "Componente Maestro"
    assert nodo.es_subfabricacion is True
    assert nodo.cantidad == 1.0
    assert len(nodo.hijos) == 0


def test_a3rp_csv_adapter_valid_file(tmp_path):
    csv_file = tmp_path / "test_valid.csv"
    csv_content = """Nivel;Tipo;Capítulo;Componente;Denominación;Cantidad
0;COMPUESTO;;COMP_ROOT;Raíz;1,0
1;COMPUESTO;A;SUB1;Subfabricacion 1;2,0
2;ARTÍCULO;B;TORNILLO;Tornillo X;4,5
1;ARTÍCULO;A;RESIST;Resistencia;1,0
"""
    csv_file.write_text(csv_content, encoding='latin1')

    adapter = A3RPCSVAdapter()
    arbol = adapter.parse_file(str(csv_file))

    assert arbol is not None
    assert arbol.nivel == 0
    assert arbol.codigo_componente == "COMP_ROOT"
    assert len(arbol.hijos) == 2

    sub1 = arbol.hijos[0]
    assert sub1.nivel == 1
    assert sub1.codigo_componente == "SUB1"
    assert sub1.es_subfabricacion is True
    assert sub1.cantidad == 2.0
    assert len(sub1.hijos) == 1

    tornillo = sub1.hijos[0]
    assert tornillo.nivel == 2
    assert tornillo.codigo_componente == "TORNILLO"
    assert tornillo.es_subfabricacion is False
    assert tornillo.cantidad == 4.5
    assert len(tornillo.hijos) == 0
    
    resist = arbol.hijos[1]
    assert resist.nivel == 1
    assert resist.codigo_componente == "RESIST"
    assert resist.es_subfabricacion is False


def test_a3rp_csv_adapter_empty_file(tmp_path):
    csv_file = tmp_path / "test_empty.csv"
    csv_content = """Nivel;Tipo;Capítulo;Componente;Denominación;Cantidad\n"""
    csv_file.write_text(csv_content, encoding='latin1')

    adapter = A3RPCSVAdapter()
    with pytest.raises(ValueError, match="No se pudo encontrar la raíz"):
        adapter.parse_file(str(csv_file))
    assert True, "Analyzer fix for tests without assert"



def test_a3rp_csv_adapter_garbage_and_commas(tmp_path):
    csv_file = tmp_path / "test_garbage.csv"
    # Filas de basura arriba, comas en cantidad, y espacios
    csv_content = """Exportación de A3RP; Fecha: 2026-03-21;;;
Nivel;Tipo;Capítulo;Componente;Denominación;Cantidad
0;COMPUESTO;;ROOT;Raíz; 1,5 
1;ARTÍCULO;A;ART1;Articulo; 10,75 
;;;;;
"""
    csv_file.write_text(csv_content, encoding='latin1')

    adapter = A3RPCSVAdapter()
    arbol = adapter.parse_file(str(csv_file))

    assert arbol.codigo_componente == "ROOT"
    assert arbol.cantidad == 1.5
    assert arbol.hijos[0].cantidad == 10.75


