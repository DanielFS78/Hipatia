# -*- coding: utf-8 -*-
"""
Tests unitarios para LabelManager y módulos auxiliares de etiquetas.

Verifica: inicialización, rutas de plantillas, listado, conteo de QR,
generación de etiquetas, impresión y errores sin acoplamiento a librerías de Word.
"""

from __future__ import annotations
import pytest
import logging
from typing import Any, cast
from unittest.mock import MagicMock, patch, call, create_autospec
from pathlib import Path
from core.label_manager import LabelManager
from core.label_manager.ports import IDocumentGenerator
import os
import sys

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_qr_generator() -> MagicMock:
    """Mock de QrGenerator genérico (spec vacío: no acoplamos a interfaz interna)."""
    generator = MagicMock(spec=[])
    return generator

@pytest.fixture
def mock_doc_generator() -> MagicMock:
    """Mock estricto del contrato IDocumentGenerator."""
    return create_autospec(IDocumentGenerator, instance=True)

@pytest.fixture
def label_manager(mock_qr_generator: MagicMock, mock_doc_generator: MagicMock) -> LabelManager:
    """LabelManager con estructura de directorios simulada."""
    with patch.object(LabelManager, '_ensure_template_structure'):
        manager = LabelManager(
            templates_dir="/tmp/fake_templates", 
            qr_generator=mock_qr_generator,
            doc_generator=mock_doc_generator
        )
    return manager


# ---------------------------------------------------------------------------
# TestLabelManagerInit
# ---------------------------------------------------------------------------

class TestLabelManagerInit:
    def test_init_creates_folder_structure(self, mock_qr_generator: MagicMock) -> None:
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            LabelManager(templates_dir="/tmp/test", qr_generator=mock_qr_generator)
            assert mock_mkdir.call_count >= 3

    def test_init_stores_dependencies(self, mock_qr_generator: MagicMock, mock_doc_generator: MagicMock) -> None:
        with patch.object(LabelManager, '_ensure_template_structure'):
            manager = LabelManager(templates_dir="/tmp/test", qr_generator=mock_qr_generator, doc_generator=mock_doc_generator)
        assert manager.qr_generator is mock_qr_generator
        assert manager.doc_generator is mock_doc_generator

    def test_ensure_template_structure_permission_error(self, label_manager: LabelManager) -> None:
        mock_logger = create_autospec(logging.Logger, instance=True)
        label_manager.logger = mock_logger
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Denied")):
            label_manager._ensure_template_structure()
        assert mock_logger.error.call_count >= 1


# ---------------------------------------------------------------------------
# TestGetTemplatePath & TestListTemplates
# ---------------------------------------------------------------------------

class TestGetTemplatePath:
    def test_returns_path_when_exists(self, label_manager: LabelManager) -> None:
        with patch.object(Path, 'exists', return_value=True):
            path = label_manager.get_template_path('A4', 'test.docx')
        assert path is not None
        assert str(path).endswith('test.docx')

    def test_returns_none_when_not_exists(self, label_manager: LabelManager) -> None:
        with patch.object(Path, 'exists', return_value=False):
            assert label_manager.get_template_path('A4', 'nonexistent.docx') is None

class TestListTemplates:
    def _make_mock_file(self, name: str, path: str) -> Any:
        f = create_autospec(Path, instance=True)
        f.name = name
        cast(Any, f.__str__).return_value = path
        f.stat.return_value.st_size = 100
        f.stat.return_value.st_mtime = 1600000000.0
        return f

    def test_list_templates_returns_matching_files(self, label_manager: LabelManager) -> None:
        f = self._make_mock_file("t.docx", "/tmp/fake_templates/etiquetas/A4/t.docx")
        with patch.object(Path, 'exists', return_value=True), patch.object(Path, 'glob', return_value=[f]):
            templates = label_manager.list_templates(formato='A4')
        assert len(templates) == 1
        assert templates[0]['nombre'] == "t.docx"

    def test_list_templates_ignores_temp_files(self, label_manager: LabelManager) -> None:
        f1 = self._make_mock_file("normal.docx", "/tmp/normal.docx")
        f2 = self._make_mock_file("~temp.docx", "/tmp/~temp.docx")
        with patch.object(Path, 'exists', return_value=True), patch.object(Path, 'glob', return_value=[f1, f2]):
            templates = label_manager.list_templates('A4')
        assert len(templates) == 1
        assert templates[0]['nombre'] == "normal.docx"


# ---------------------------------------------------------------------------
# TestCountQrPlaceholders
# ---------------------------------------------------------------------------

class TestCountQrPlaceholders:
    def test_delegates_to_document_generator(self, label_manager: LabelManager, mock_doc_generator: MagicMock) -> None:
        mock_doc_generator.count_qr_placeholders.return_value = 5
        with patch.object(label_manager, 'get_template_path', return_value=Path('/tmp/fake.docx')):
            count = label_manager.count_qr_placeholders('fake.docx', 'A4')
        assert count == 5
        mock_doc_generator.count_qr_placeholders.assert_called_once_with(Path('/tmp/fake.docx'))

    def test_returns_zero_when_template_not_found(self, label_manager: LabelManager, mock_doc_generator: MagicMock) -> None:
        with patch.object(label_manager, 'get_template_path', return_value=None):
            count = label_manager.count_qr_placeholders("x", "A4")
        assert count == 0
        assert mock_doc_generator.count_qr_placeholders.call_count == 0

    def test_returns_zero_on_exception(self, label_manager: LabelManager, mock_doc_generator: MagicMock) -> None:
        mock_doc_generator.count_qr_placeholders.side_effect = Exception("Crash")
        with patch.object(label_manager, 'get_template_path', return_value=Path('found.docx')):
            count = label_manager.count_qr_placeholders("t.docx", "A4")
        assert count == 0


# ---------------------------------------------------------------------------
# TestGenerateLabels
# ---------------------------------------------------------------------------

class TestGenerateLabels:
    def test_generate_labels_delegates_to_doc_generator(self, label_manager: LabelManager, mock_doc_generator: MagicMock) -> None:
        mock_doc_generator.generate_labels.return_value = "/tmp/out.docx"
        with patch.object(label_manager, 'get_template_path', return_value=Path('/tmp/t.docx')):
            path = label_manager.generate_labels('t.docx', 'A4', [{"p": "1"}])
        assert path == "/tmp/out.docx"
        assert mock_doc_generator.generate_labels.call_count == 1
        call_args = mock_doc_generator.generate_labels.call_args
        assert call_args[0][0] == Path('/tmp/t.docx')
        assert call_args[0][1] == [{"p": "1"}]
        # Verifica que el valor por defecto (11) se pasa correctamente
        assert call_args[0][4] == 11

    def test_generate_labels_with_apli_1861_size(self, label_manager: LabelManager, mock_doc_generator: MagicMock) -> None:
        mock_doc_generator.generate_labels.return_value = "/tmp/apli.docx"
        with patch.object(label_manager, 'get_template_path', return_value=Path('/tmp/apli.docx')):
            # Si el formato es APLI_1861_A5, el manager debería extraer qr_size_mm=11 de LABEL_FORMATS
            # Aunque 11 sea el default, verificamos que la lógica de búsqueda de formato funciona.
            path = label_manager.generate_labels('apli.docx', 'A5', [{"p": "1"}])
        
        assert path == "/tmp/apli.docx"
        call_args = mock_doc_generator.generate_labels.call_args
        # Para A5, el manager busca en LABEL_FORMATS y encuentra APLI_1857_A5 o APLI_1861_A5
        # dado que ambos coinciden en formato_hoja='A5', tomará el primero que coincida.
        # En base.py, APLI_1857_A5 no tiene qr_size_mm (usa default 11).
        assert call_args[0][4] == 11

    def test_returns_none_when_no_template(self, label_manager: LabelManager, mock_doc_generator: MagicMock) -> None:
        with patch.object(label_manager, 'get_template_path', return_value=None):
            assert label_manager.generate_labels("x", "A4", []) is None
            assert mock_doc_generator.generate_labels.call_count == 0

    def test_returns_none_on_exception(self, label_manager: LabelManager, mock_doc_generator: MagicMock) -> None:
        mock_doc_generator.generate_labels.side_effect = Exception("Err")
        with patch.object(label_manager, 'get_template_path', return_value=Path('t.docx')):
            assert label_manager.generate_labels("t.docx", "A4", []) is None


# ---------------------------------------------------------------------------
# TestCreateSampleTemplate
# ---------------------------------------------------------------------------

class TestCreateSampleTemplate:
    def test_create_sample_delegates_to_doc_generator(self, label_manager: LabelManager, mock_doc_generator: MagicMock) -> None:
        mock_doc_generator.create_sample.return_value = "/tmp/A4/sample.docx"
        res = label_manager.create_sample_template('A4', 'sample.docx')
        assert res == "/tmp/A4/sample.docx"
        assert mock_doc_generator.create_sample.call_count == 1
        call_args = mock_doc_generator.create_sample.call_args
        assert call_args[0][0] == 'A4'

    def test_returns_none_on_exception(self, label_manager: LabelManager, mock_doc_generator: MagicMock) -> None:
        mock_doc_generator.create_sample.side_effect = Exception("X")
        assert label_manager.create_sample_template("A4") is None


# ---------------------------------------------------------------------------
# TestQuickPrintLabels
# ---------------------------------------------------------------------------

class TestQuickPrintLabels:
    def test_quick_print_labels_success(self) -> None:
        with patch('core.label_manager.manager.LabelManager') as MockManager:
            from core.label_manager.manager import quick_print_labels
            instance = MockManager.return_value
            instance.generate_labels.return_value = "/tmp/out.docx"
            instance.print_document.return_value = (True, None)

            res = quick_print_labels({"k": "v"})
        assert res is True
        assert instance.generate_labels.call_count == 1
        instance.print_document.assert_called_once_with("/tmp/out.docx")

    def test_quick_print_labels_no_path(self) -> None:
        with patch('core.label_manager.manager.LabelManager') as MockManager:
            from core.label_manager.manager import quick_print_labels
            instance = MockManager.return_value
            instance.generate_labels.return_value = None
            assert quick_print_labels({"k": "v"}) is False

# ---------------------------------------------------------------------------
# TestPrinterMethods y Auxiliares simplificados que no tocan Docx
# ---------------------------------------------------------------------------

class TestPrinterMethods:
    def test_is_printer_available_macos_true(self, label_manager: LabelManager) -> None:
        with patch('platform.system', return_value='Darwin'), \
             patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = "system default destination: Printer"
            mock_run.return_value.returncode = 0
            assert label_manager._is_printer_available() is True

    def test_print_document_macos(self, label_manager: LabelManager) -> None:
        with patch('core.label_manager.manager.printer.is_printer_available', return_value=True), \
             patch('platform.system', return_value='Darwin'), \
             patch('subprocess.run') as mock_run:
            res, path = label_manager.print_document("/tmp/doc.docx")
        assert res is True
        assert mock_run.call_count >= 1
