# -*- coding: utf-8 -*-
"""
Tests de integración reales para DocxGeneratorAdapter.
Verifica que la librería `python-docx` interactúa correctamente con 
archivos .docx reales en el sistema de archivos, sin mockear sus clases internas.
"""

import pytest
import os
from pathlib import Path
from typing import Generator
from tempfile import TemporaryDirectory
from infrastructure.document_generator.docx_adapter import DocxGeneratorAdapter, docx

pytestmark = pytest.mark.integration

@pytest.fixture
def adapter() -> DocxGeneratorAdapter:
    return DocxGeneratorAdapter()

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    with TemporaryDirectory() as d:
        yield Path(d)

@pytest.fixture
def sample_template(temp_dir: Path) -> Path:
    """Crea una plantilla docx real basica con placeholders."""
    if docx is None:
        pytest.skip("python-docx no instalado")
    doc = docx.Document()
    doc.add_paragraph("Root paragraph that is not touched")
    table = doc.add_table(rows=1, cols=1)
    table.rows[0].cells[0].text = "QR aquí: {{qr}} \n Dato: {{var1}}"
    path = temp_dir / "template.docx"
    doc.save(str(path))
    return path

def test_count_qr_placeholders(adapter: DocxGeneratorAdapter, sample_template: Path) -> None:
    """Verifica que cuente correctamente los placeholders {{qr}} reales."""
    if docx is None: pytest.skip("python-docx no instalado")
    count = adapter.count_qr_placeholders(sample_template)
    assert count == 1  # Hay uno en la celda de la tabla

def test_generate_labels(adapter: DocxGeneratorAdapter, sample_template: Path, temp_dir: Path) -> None:
    """Genera etiquetas resolviendo variables y omitiendo qr_generator real."""
    if docx is None: pytest.skip("python-docx no instalado")
    
    out_path = temp_dir / "output.docx"
    data = [{"var1": "HolaMundo", "codigo": "123"}]
    
    # Pasamos qr_generator=None, por lo que {{qr}} se va a extraer
    # y como `qr_img` no se generará, quedará el hueco según la logica del adapter.
    result = adapter.generate_labels(sample_template, data, None, str(out_path))
    
    assert result == str(out_path)
    assert out_path.exists()
    
    # Verificamos contenido final
    doc = docx.Document(result)
    assert "HolaMundo" in doc.tables[0].rows[0].cells[0].text
    # El placeholder {{qr}} debe haber sido vaciado/reemplazado
    assert "{{qr}}" not in doc.tables[0].rows[0].cells[0].text

def test_generate_labels_with_custom_qr_size(adapter: DocxGeneratorAdapter, sample_template: Path, temp_dir: Path) -> None:
    """Verifica que acepte el parámetro qr_size_mm sin errores."""
    if docx is None: pytest.skip("python-docx no instalado")
    out_path = temp_dir / "output_size.docx"
    data = [{"var1": "TestSize", "codigo": "456"}]
    
    # Probamos con un tamaño distinto al default (ej: 8mm)
    result = adapter.generate_labels(sample_template, data, None, str(out_path), qr_size_mm=8)
    
    assert result == str(out_path)
    assert out_path.exists()

def test_create_sample(adapter: DocxGeneratorAdapter, temp_dir: Path) -> None:
    """Genera documentos estandarizados."""
    if docx is None: pytest.skip("python-docx no instalado")
    out_path = temp_dir / "sample_a4.docx"
    result = adapter.create_sample("A4", out_path)
    
    assert result == str(out_path)
    assert out_path.exists()
    doc = docx.Document(result)
    assert len(doc.tables) > 0  # A4 sample inserta tablas

def test_missing_python_docx(adapter: DocxGeneratorAdapter, temp_dir: Path) -> None:
    """Simula ausencia de librería manejado gracilmente."""
    global docx
    original_docx = docx
    import infrastructure.document_generator.docx_adapter as adapter_module
    adapter_module.docx = None
    
    try:
        assert adapter.count_qr_placeholders(Path("dummy")) == 0
        assert adapter.generate_labels(Path("dummy"), [], None, "dummy") is None
        assert adapter.create_sample("A4", Path("dummy")) is None
    finally:
        adapter_module.docx = original_docx
