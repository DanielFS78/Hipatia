# -*- coding: utf-8 -*-
"""Tests para scripts.detect_dead_code: MethodExtractor, referencias, análisis."""
import pytest
import ast
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
from scripts.detect_dead_code import (
    MethodExtractor,
    find_references_in_file,
    analyze_dead_code,
    generate_report,
    find_all_references,
    extract_package_classes,
    main,
)

pytestmark = pytest.mark.unit


def test_method_extractor():
    code = """
class TestClass:
    def __init__(self):
        self._private_method()
    
    def public_method(self):
        pass
        
    def _private_method(self):
        self.__dunder__()
        
    def __dunder__(self):
        pass
"""
    tree = ast.parse(code)
    extractor = MethodExtractor()
    extractor.visit(tree)
    
    assert "TestClass" in extractor.classes
    methods = extractor.classes["TestClass"]["methods"]
    assert "__init__" in methods
    assert "public_method" in methods
    assert "_private_method" in methods
    assert "__dunder__" in methods
    
    assert methods["_private_method"]["is_private"] is True
    assert methods["__dunder__"]["is_dunder"] is True
    assert "_private_method" in methods["__init__"]["internal_calls"]

def test_find_references_in_file():
    content = """
from module import TestClass
obj = TestClass()
obj.public_method()
if isinstance(x, TestClass):
    pass
"""
    m = mock_open(read_data=content)
    with patch('builtins.open', m):
        mock_base = Path("/fake/base")
        fake_file = Path("/fake/base/fake.py")
        
        with patch('scripts.detect_dead_code.BASE_DIR', mock_base):
            with patch.object(Path, 'relative_to', return_value=Path("fake.py")):
                refs = find_references_in_file(fake_file, {"public_method"}, {"TestClass"})
                
                assert "TestClass" in refs
                assert len(refs["TestClass"]) >= 3
                assert "public_method" in refs
                assert len(refs["public_method"]) == 1

def test_analyze_dead_code():
    classes = {
        "ui/dialogs/unused.py::UnusedClass": {
            "short_class_name": "UnusedClass",
            "source_file": "ui/dialogs/unused.py",
            "methods": {
                "method1": {
                    "is_private": False,
                    "is_dunder": False,
                    "line_start": 1,
                    "line_end": 5,
                    "internal_calls": set(),
                }
            },
            "line_start": 1,
            "line_end": 10,
        },
        "ui/dialogs/used.py::UsedClass": {
            "short_class_name": "UsedClass",
            "source_file": "ui/dialogs/used.py",
            "methods": {
                "used_method": {
                    "is_private": False,
                    "is_dunder": False,
                    "line_start": 11,
                    "line_end": 15,
                    "internal_calls": set(),
                },
                "dead_private": {
                    "is_private": True,
                    "is_dunder": False,
                    "line_start": 16,
                    "line_end": 20,
                    "internal_calls": set(),
                },
                "__init__": {
                    "is_private": False,
                    "is_dunder": True,
                    "line_start": 21,
                    "line_end": 25,
                    "internal_calls": set(),
                },
            },
            "line_start": 11,
            "line_end": 30,
        },
    }

    references = {
        "UsedClass": [{"file": "other.py", "line": 1, "type": "class_usage", "context": ""}],
        "used_method": [{"file": "other.py", "line": 2, "type": "method_call", "context": ""}],
    }

    analysis = analyze_dead_code(classes, references)

    assert any(c["name"] == "ui/dialogs/used.py::UsedClass" for c in analysis["used_classes"])
    assert any(c["name"] == "ui/dialogs/unused.py::UnusedClass" for c in analysis["unused_classes"])
    assert any(m["method"] == "used_method" for m in analysis["used_methods"])
    assert any(m["method"] == "dead_private" for m in analysis["dead_methods"])
    assert any(m["method"] == "__init__" for m in analysis["dunder_methods"])

def test_generate_report():
    classes = {"Test": {"methods": {"m": {"line_start": 1, "line_end": 2}}}}
    analysis = {
        "dead_methods": [{"class": "Test", "method": "m", "lines": 1, "line_start": 1, "line_end": 2, "confidence": "Alta"}],
        "used_methods": [],
        "internal_only_methods": [],
        "dunder_methods": [],
        "unused_classes": [{"name": "Unused", "lines": 10, "method_count": 2}],
        "used_classes": []
    }
    report = generate_report(classes, analysis)
    assert "Análisis de código muerto" in report
    assert "ui/dialogs" in report
    assert "Alta" in report
    assert "Unused" in report

def test_find_all_references():
    with patch('scripts.detect_dead_code.SEARCH_DIRS', [Path("/fake/base")]):
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.is_file', return_value=True):
                with patch('scripts.detect_dead_code.find_references_in_file', return_value={"m": []}) as mock_find:
                    refs = find_all_references({"m"}, {"C"})
                    assert "m" in refs
                    mock_find.assert_called()

def test_main_execution():
    """main() escribe el reporte; no parsea el disco real si el paquete está mockeado."""
    fake_classes = {
        "fake.py::C": {
            "methods": {
                "m": {
                    "line_start": 1,
                    "line_end": 2,
                    "is_private": False,
                    "is_dunder": False,
                    "internal_calls": set(),
                }
            },
            "line_start": 1,
            "line_end": 3,
            "source_file": "fake.py",
            "short_class_name": "C",
        }
    }
    with patch('scripts.detect_dead_code.DIALOGS_PACKAGE') as mock_pkg:
        mock_pkg.is_dir.return_value = True
        with patch(
            'scripts.detect_dead_code.extract_package_classes', return_value=fake_classes
        ):
            with patch(
                'scripts.detect_dead_code.find_all_references', return_value={"C": [], "m": []}
            ):
                with patch('scripts.detect_dead_code.generate_report', return_value="# Report"):
                    with patch('scripts.detect_dead_code.OUTPUT_PATH') as mock_out:
                        mock_out.parent.mkdir.return_value = None
                        with patch('builtins.open', mock_open()) as mock_out_file:
                            main()
                            mock_out_file.assert_called()
                            assert mock_out_file.called, "main() debe escribir el reporte"


def test_extract_package_classes_skips_pycache(tmp_path):
    pkg = tmp_path / "dialogs"
    pkg.mkdir()
    (pkg / "ok.py").write_text(
        "class A:\n    def f(self):\n        pass\n", encoding="utf-8"
    )
    cache = pkg / "__pycache__"
    cache.mkdir()
    (cache / "x.py").write_text("class X: pass\n", encoding="utf-8")

    with patch('scripts.detect_dead_code.BASE_DIR', tmp_path):
        merged = extract_package_classes(pkg)

    keys = list(merged.keys())
    assert len(keys) == 1
    assert keys[0].endswith("ok.py::A")
    assert merged[keys[0]]["source_file"] == "dialogs/ok.py"
    assert merged[keys[0]]["short_class_name"] == "A"
