# -*- coding: utf-8 -*-
"""
Tests unitarios para Apli1861LabelGenerator.
Verifica la construcción del documento APLI 1861 sin depender de archivos de plantilla.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, create_autospec
from infrastructure.document_generator.apli_adapter import Apli1861LabelGenerator

pytestmark = pytest.mark.unit

@pytest.fixture
def adapter() -> Apli1861LabelGenerator:
    """Fixture que proporciona una instancia del generador APLI."""
    return Apli1861LabelGenerator()

@pytest.fixture
def mock_qr_generator() -> MagicMock:
    """Mock del generador de QR usando spec para evitar loose_mocks."""
    # Usamos el nombre real del método: generate_qr_code
    mock = MagicMock(spec=['generate_qr_code'])
    # La respuesta es un objeto que debe tener el método save
    mock.generate_qr_code.return_value = MagicMock(spec=['save'])
    return mock

class TestApli1861LabelGenerator:
    """Suite de pruebas para validar el comportamiento del generador APLI 1861."""

    def test_count_qr_placeholders_is_fixed(self, adapter: Apli1861LabelGenerator) -> None:
        """Verifica que el conteo de huecos sea siempre 66 para este formato."""
        assert adapter.count_qr_placeholders(Path("any")) == 66

    def test_generate_labels_creates_document(self, adapter: Apli1861LabelGenerator, mock_qr_generator: MagicMock, tmp_path: Path) -> None:
        """Prueba la generación completa mockeando docx para evitar dependencias de sistema."""
        output_file = tmp_path / "test_apli.docx"
        datos = [{"qr": "DATA1", "codigo": "COD1"}]
        
        # Mock de docx con autospec=True para ser estricto
        with patch('infrastructure.document_generator.apli_adapter.docx_module', autospec=True) as mock_docx:
            mock_doc = mock_docx.Document.return_value
            # Simulamos tabla con 6 filas
            mock_table = MagicMock(spec=['rows', 'autofit'])
            mock_doc.add_table.return_value = mock_table
            
            mock_row = MagicMock(spec=['cells', 'height'])
            mock_table.rows = [mock_row] * 6
            
            mock_cell = MagicMock(spec=['paragraphs', 'width', 'vertical_alignment', '_tc'])
            mock_tc = MagicMock(spec=['get_or_add_tcPr'])
            mock_cell._tc = mock_tc
            mock_tc.get_or_add_tcPr.return_value = MagicMock(spec=['append'])
            
            mock_row.cells = [mock_cell] * 11
            
            # Ejecución
            result = adapter.generate_labels(Path("dynamic"), datos, mock_qr_generator, str(output_file))
            
            # Aserciones de estructura
            assert result == str(output_file)
            assert mock_docx.Document.call_count == 1
            # Se debe haber creado la tabla 6x11
            assert mock_doc.add_table.call_count == 1
            assert mock_doc.add_table.call_args[1]['rows'] == 6
            assert mock_doc.add_table.call_args[1]['cols'] == 11
            # Se debe haber guardado
            assert mock_doc.save.call_count == 1
            assert mock_doc.save.call_args[0][0] == str(output_file)

    def test_generate_labels_inserts_qr(self, adapter: Apli1861LabelGenerator, mock_qr_generator: MagicMock, tmp_path: Path) -> None:
        """Verifica que se llame al generador de QR y se inserte la imagen."""
        output_file = tmp_path / "test_qr.docx"
        datos = [{"qr": "QR_DATA_TEST"}]
        
        with patch('infrastructure.document_generator.apli_adapter.docx_module', autospec=True) as mock_docx:
            mock_doc = mock_docx.Document.return_value
            mock_table = MagicMock(spec=['rows', 'autofit'])
            mock_doc.add_table.return_value = mock_table
            
            mock_cell = MagicMock(spec=['paragraphs', 'width', 'vertical_alignment', '_tc'])
            mock_tc = MagicMock(spec=['get_or_add_tcPr'])
            mock_cell._tc = mock_tc
            mock_tc.get_or_add_tcPr.return_value = MagicMock(spec=['append'])
            
            # Mock de párrafo para add_run
            mock_p = MagicMock(spec=['add_run', 'alignment'])
            mock_cell.paragraphs = [mock_p]
            
            # Mock del objeto 'run' devuelto por add_run con spec
            mock_run = MagicMock(spec=['add_picture'])
            mock_p.add_run.return_value = mock_run
            
            mock_table.rows = [MagicMock(spec=['cells'], cells=[mock_cell])]
            
            # Simulamos que el archivo QR existe para que add_picture se llame
            with patch('os.path.exists', return_value=True, autospec=True), \
                 patch('os.remove', autospec=True):
                adapter.generate_labels(Path("dynamic"), datos, mock_qr_generator, str(output_file))
            
            # Verificar interacción con QR generator
            assert mock_qr_generator.generate_qr_code.call_count == 1
            assert mock_qr_generator.generate_qr_code.call_args[0][0] == "QR_DATA_TEST"
            
            # Verificar inserción de imagen en el rún del párrafo
            assert mock_p.add_run.call_count >= 1
            assert mock_run.add_picture.call_count == 1

    def test_generate_labels_docx_missing(self, adapter: Apli1861LabelGenerator) -> None:
        """Verifica manejo gracil si python-docx no está disponible."""
        with patch('infrastructure.document_generator.apli_adapter.docx_module', None):
            result = adapter.generate_labels(Path("x"), [], None, "output.docx")
            assert result is None

    def test_create_sample_delegates(self, adapter: Apli1861LabelGenerator, tmp_path: Path) -> None:
        """Verifica que create_sample genere un archivo."""
        output_file = tmp_path / "sample.docx"
        with patch.object(adapter, 'generate_labels', autospec=True, return_value="ok") as mock_gen:
            res = adapter.create_sample("APLI_A5", output_file)
            assert res == "ok"
            assert mock_gen.call_count == 1
