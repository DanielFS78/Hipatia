# -*- coding: utf-8 -*-
"""
Tests unitarios para A3RPExcelAdapter.
Valida la lectura correcta, parseo jerárquico y manejo de errores
de las listas de materiales exportadas por A3RP en Excel.
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from core.import_manager.adapters.a3rp_excel_adapter import A3RPExcelAdapter
from core.import_manager.dto import BOMNodeDTO


@pytest.fixture
def a3rp_adapter() -> A3RPExcelAdapter:
    """Proporciona una instancia limpia del adaptador."""
    return A3RPExcelAdapter()

@pytest.fixture
def dummy_excel_data() -> pd.DataFrame:
    """Datos simulados de un Excel jerárquico perfecto."""
    return pd.DataFrame({
        'Nivel': [0, 1, 2, 1],
        'Capítulo': ['1', '1.1', '1.1.1', '1.2'],
        'Componente': ['PROD_MAESTRO', 'SUB1', 'MAT1', 'SUB2'],
        'Denominación': ['Producto Final', 'Subconjunto 1', 'Materia Prima 1', 'Subconjunto 2'],
        'Tipo': ['Compuesto', 'Compuesto', 'Simple', 'Compuesto'],
        'Cantidad': [1.0, 2.0, 5.5, 1.0]
    })


@pytest.mark.unit
class TestA3RPExcelAdapter:
    """Suite de pruebas para validar el adaptador Excel de A3RP."""

    @patch('core.import_manager.adapters.a3rp_excel_adapter.pd.read_excel', autospec=True)
    def test_parse_valid_excel_hierarchy(self, mock_read_excel: MagicMock, a3rp_adapter: A3RPExcelAdapter, dummy_excel_data: pd.DataFrame) -> None:
        """Verifica que un árbol correcto se reconstruye perfectamente."""
        mock_read_excel.return_value = dummy_excel_data
        
        raiz: BOMNodeDTO = a3rp_adapter.parse_file("dummy_path.xlsx")
        
        assert raiz is not None
        assert isinstance(raiz, BOMNodeDTO)
        assert raiz.nivel == 0
        assert raiz.codigo_componente == "PROD_MAESTRO"
        assert raiz.es_subfabricacion is True
        
        # Validar hijos: SUB1 y SUB2
        assert len(raiz.hijos) == 2
        hijo_1 = raiz.hijos[0]
        hijo_2 = raiz.hijos[1]
        
        assert isinstance(hijo_1, BOMNodeDTO)
        assert hijo_1.codigo_componente == "SUB1"
        assert hijo_1.es_subfabricacion is True
        assert hijo_1.cantidad == 2.0
        
        assert isinstance(hijo_2, BOMNodeDTO)
        assert hijo_2.codigo_componente == "SUB2"
        assert hijo_2.es_subfabricacion is True
        
        # Validar nieto: MAT1
        assert len(hijo_1.hijos) == 1
        nieto = hijo_1.hijos[0]
        assert isinstance(nieto, BOMNodeDTO)
        assert nieto.codigo_componente == "MAT1"
        assert nieto.es_subfabricacion is False
        assert nieto.cantidad == 5.5
        
        # Autospec test
        mock_read_excel.assert_called_once_with("dummy_path.xlsx", sheet_name=0)

    @patch('core.import_manager.adapters.a3rp_excel_adapter.pd.read_excel', autospec=True)
    def test_parse_missing_required_columns(self, mock_read_excel: MagicMock, a3rp_adapter: A3RPExcelAdapter) -> None:
        """Verifica el error si faltan las columnas clave (Nivel o Componente)."""
        df_invalid = pd.DataFrame({
            'OtraColumna': [1, 2],
            'Componente': ['A', 'B']  # Falta 'Nivel'
        })
        mock_read_excel.return_value = df_invalid
        
        with pytest.raises(ValueError, match="no contiene las columnas obligatorias"):
            a3rp_adapter.parse_file("dummy_path.xlsx")
        
        assert mock_read_excel.call_count == 1
        mock_read_excel.assert_called_once_with("dummy_path.xlsx", sheet_name=0)

    @patch('core.import_manager.adapters.a3rp_excel_adapter.pd.read_excel', autospec=True)
    def test_parse_missing_root_node(self, mock_read_excel: MagicMock, a3rp_adapter: A3RPExcelAdapter) -> None:
        """Verifica el error si el CSV no contiene ningún nodo de Nivel 0."""
        df_no_root = pd.DataFrame({
            'Nivel': [1, 2],
            'Componente': ['SUB1', 'MAT1']
        })
        mock_read_excel.return_value = df_no_root
        
        with pytest.raises(ValueError, match="No se pudo extraer el producto raíz"):
            a3rp_adapter.parse_file("dummy_path.xlsx")
        
        assert mock_read_excel.call_count == 1
        mock_read_excel.assert_called_once_with("dummy_path.xlsx", sheet_name=0)

    @patch('core.import_manager.adapters.a3rp_excel_adapter.pd.read_excel', autospec=True)
    def test_parse_handles_messy_data(self, mock_read_excel: MagicMock, a3rp_adapter: A3RPExcelAdapter) -> None:
        """Verifica la robustez ante filas en blanco, NaN y cantidades con comas europeas."""
        import numpy as np
        df_messy = pd.DataFrame({
            'Nivel': [0, np.nan, 'Basura', 1],
            'Componente': ['PROD', np.nan, 'XXX', 'SUB1'],
            'Denominación': ['Prod Final', np.nan, '', np.nan],
            'Tipo': ['Compuesto', '', '', 'Simple'],
            'Cantidad': ['1,0', np.nan, '1', '2,5']  # Comas europeas
        })
        mock_read_excel.return_value = df_messy
        
        raiz = a3rp_adapter.parse_file("messy.xlsx")
        
        assert isinstance(raiz, BOMNodeDTO)
        assert raiz.codigo_componente == "PROD"
        assert raiz.cantidad == 1.0 # Parseo con reemplazo de coma
        assert len(raiz.hijos) == 1
        
        hijo = raiz.hijos[0]
        assert isinstance(hijo, BOMNodeDTO)
        assert hijo.codigo_componente == "SUB1"
        assert hijo.cantidad == 2.5
        assert hijo.denominacion == "" # NaN manejado correctamente
        assert hijo.es_subfabricacion is False
        mock_read_excel.assert_called_once_with("messy.xlsx", sheet_name=0)

    @patch('core.import_manager.adapters.a3rp_excel_adapter.pd.read_excel', autospec=True)
    def test_parse_io_error(self, mock_read_excel: MagicMock, a3rp_adapter: A3RPExcelAdapter) -> None:
        """Verifica que se envuelva el error subyacente de lectura."""
        mock_read_excel.side_effect = FileNotFoundError("Archivo no existe")
        
        with pytest.raises(IOError, match="Error al leer el archivo Excel"):
            a3rp_adapter.parse_file("fantasma.xlsx")
            
        assert mock_read_excel.call_count == 1
        mock_read_excel.assert_called_once_with("fantasma.xlsx", sheet_name=0)
