# tests/unit/test_audit_report_generator.py
# -*- coding: utf-8 -*-
"""Tests unitarios para ISO9001AuditReporter y PytestAuditPlugin (generación de informes de auditoría)."""
from __future__ import annotations

import os
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from tests.reporting.audit_report_generator import ISO9001AuditReporter, PytestAuditPlugin

pytestmark = pytest.mark.unit

@pytest.fixture
def mock_test_data():
    return {
        'validation_results': [
            {'category': 'Unitarios', 'test_name': 'test_worker_crud', 'status': 'PASS', 'duration': 0.1},
            {'category': 'Planificación', 'test_name': 'test_complex_scheduler_logic', 'status': 'FAIL', 'duration': 0.2}
        ],
        'coverage': {
            'percent_covered': 85.5
        },
        'raw_coverage_files': {
            'core/utils.py': {'summary': {'num_statements': 100, 'covered_lines': 80}},
            'controllers/worker_controller.py': {'summary': {'num_statements': 200, 'covered_lines': 190}}
        }
    }

class TestISO9001AuditReporter:
    
    def test_init_creates_dir(self, tmp_path):
        out_dir = tmp_path / "reports"
        reporter = ISO9001AuditReporter(output_dir=str(out_dir))
        assert reporter.output_dir.exists()
        assert reporter.output_dir.is_dir()
        
    def test_generate_business_pdf_report_success(self, tmp_path, mock_test_data):
        reporter = ISO9001AuditReporter(output_dir=str(tmp_path))
        pdf_path = reporter.generate_business_pdf_report(mock_test_data)
        
        assert pdf_path.endswith(".pdf")
        assert os.path.exists(pdf_path)
        
    def test_generate_business_pdf_report_exception(self, tmp_path):
        reporter = ISO9001AuditReporter(output_dir=str(tmp_path))
        
        # Force exception by passing None which shouldn't have .get()
        pdf_path = reporter.generate_business_pdf_report(None)
        assert pdf_path == ""
        
    def test_categorize_tests(self, tmp_path):
        reporter = ISO9001AuditReporter(output_dir=str(tmp_path))
        results = [
            {'test_name': 'test_search_products', 'status': 'PASS'},
            {'test_name': 'test_worker_logic', 'status': 'PASS'},
            {'test_name': 'test_product_flow', 'status': 'FAIL'},
            {'test_name': 'test_machine_boot', 'status': 'PASS'},
            {'test_name': 'test_unknown', 'status': 'FAIL'},
        ]
        
        categorized = reporter._categorize_tests(results)
        
        cats = [c['category'] for c in categorized]
        assert "Base de Datos" in cats # from test_search_products
        assert "Trabajadores" in cats # from test_worker_logic
        assert "Productos" in cats # from test_product_flow
        assert "Máquinas" in cats # from test_machine_boot
        assert "Unitarios" in cats # from test_unknown
        
    def test_generate_recommendations(self, tmp_path):
        reporter = ISO9001AuditReporter(output_dir=str(tmp_path))
        
        # Test case 1: Bad success rate, bad coverage
        recs1 = reporter._generate_recommendations(80.0, {'percent_covered': 70.0})
        assert any("Revisar tests fallidos antes de desplegar" in r for r in recs1)
        assert any("Aumentar cobertura de código" in r for r in recs1)
        
        # Test case 2: Perfect success rate and coverage
        recs2 = reporter._generate_recommendations(100.0, {'percent_covered': 90.0})
        assert any("Sistema estable y listo para producción" in r for r in recs2)
        
        # Test case 3: Good success but not perfect, Good coverage
        recs3 = reporter._generate_recommendations(98.0, {'percent_covered': 85.0})
        assert any("Continuar monitoreo regular" in r for r in recs3)


class TestPytestAuditPlugin:
    
    def test_pytest_sessionstart(self):
        plugin = PytestAuditPlugin()
        plugin.pytest_sessionstart(None)
        assert plugin.start_time is not None
        
    def test_pytest_runtest_logreport_pass(self):
        plugin = PytestAuditPlugin()
        mock_report = MagicMock(spec=["when", "nodeid", "passed", "duration"])
        mock_report.when = 'call'
        mock_report.nodeid = 'tests/test_file.py::test_name'
        mock_report.passed = True
        mock_report.duration = 0.5
        
        plugin.pytest_runtest_logreport(mock_report)
        assert len(plugin.test_results) == 1
        assert plugin.test_results[0]['status'] == 'PASS'
        assert plugin.test_results[0]['test_name'] == 'test_name'

    def test_pytest_runtest_logreport_fail(self):
        plugin = PytestAuditPlugin()
        mock_report = MagicMock(spec=["when", "nodeid", "passed", "duration"])
        mock_report.when = 'call'
        mock_report.nodeid = 'tests/test_file.py::test_name_fail'
        mock_report.passed = False
        mock_report.duration = 0.1
        
        plugin.pytest_runtest_logreport(mock_report)
        assert len(plugin.test_results) == 1
        assert plugin.test_results[0]['status'] == 'FAIL'

    def test_pytest_runtest_logreport_setup(self):
        plugin = PytestAuditPlugin()
        mock_report = MagicMock(spec=["when"])
        mock_report.when = 'setup' # Not call
        
        plugin.pytest_runtest_logreport(mock_report)
        assert len(plugin.test_results) == 0

    @patch('tests.reporting.audit_report_generator.ISO9001AuditReporter.generate_business_pdf_report', autospec=True)
    def test_pytest_sessionfinish(self, mock_generate, tmp_path):
        plugin = PytestAuditPlugin()
        plugin.pytest_sessionstart(None)
        
        # Provide coverage data somehow... The plugin reads from "test_reports/coverage.json"
        # We will mock _load_coverage_data
        with patch.object(plugin, '_load_coverage_data', return_value={'percent_covered': 80}):
            plugin.pytest_sessionfinish(None, 0)
            
        assert mock_generate.call_count >= 1

    def test_load_coverage_data_missing_file(self, tmp_path, monkeypatch):
        # Change current working dir for Path behavior
        monkeypatch.chdir(tmp_path)
        plugin = PytestAuditPlugin()
        data = plugin._load_coverage_data()
        assert data['percent_covered'] == 0
        
    def test_load_coverage_data_valid_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        os.makedirs(tmp_path / "test_reports")
        cov_file = tmp_path / "test_reports" / "coverage.json"
        
        cov_content = {
            "totals": {
                "percent_covered": 88.5,
                "covered_lines": 500,
                "num_statements": 600
            },
            "files": {}
        }
        with open(cov_file, 'w') as f:
            json.dump(cov_content, f)
            
        plugin = PytestAuditPlugin()
        data = plugin._load_coverage_data()
        assert data['percent_covered'] == 88.5
        assert data['lines_covered'] == 500

    def test_load_coverage_data_invalid_json(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        os.makedirs(tmp_path / "test_reports")
        cov_file = tmp_path / "test_reports" / "coverage.json"
        with open(cov_file, 'w') as f:
            f.write("invalidd_json_data")
            
        plugin = PytestAuditPlugin()
        data = plugin._load_coverage_data()
        assert data['percent_covered'] == 0

