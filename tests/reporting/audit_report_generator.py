# tests/reporting/audit_report_generator.py
"""
Sistema de Generación de Informes de Auditoría para Tests
=========================================================
Genera informes PDF profesionales utilizando ReportLab (Pure Python).
Elimina la dependencia de librerías del sistema como Pango/Cairo.

Versión: 3.1 - Migración a ReportLab
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Imports de ReportLab
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class ISO9001AuditReporter:
    """
    Genera informes de auditoría en formato PDF siguiendo estándares
    de calidad ISO 9001, utilizando ReportLab para máxima compatibilidad.
    """

    def __init__(self, output_dir: str = "test_reports/audit"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def generate_business_pdf_report(self, test_data: Dict[str, Any]) -> str:
        """
        Genera un informe PDF profesional.
        """
        try:
            # Preparar datos
            report_data = self._prepare_report_data(test_data)
            
            # Definir ruta de salida
            pdf_filename = f"audit_report_{report_data['report_id']}.pdf"
            pdf_path = self.output_dir / pdf_filename

            # Crear PDF
            self._create_pdf_document(pdf_path, report_data)

            self.logger.info(f"Informe PDF generado exitosamente: {pdf_path}")
            return str(pdf_path)

        except Exception as e:
            self.logger.error(f"Error al generar informe PDF: {e}", exc_info=True)
            return ""

    def _prepare_report_data(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara los datos para el informe (Lógica de negocio)."""
        validation_results = test_data.get('validation_results', [])
        coverage = test_data.get('coverage', {})
        modular_coverage = self._calculate_modular_coverage(test_data.get('raw_coverage_files', {}))

        total_tests = len(validation_results)
        passed_tests = sum(1 for t in validation_results if t['status'] == 'PASS')
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        categorized_tests = self._categorize_tests(validation_results)
        # Sort categorized tests by status (FAIL first) then category
        categorized_tests.sort(key=lambda x: (x['status'] == 'PASS', x['category']))

        return {
            'report_id': f"AUDIT-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': round(success_rate, 2),
            },
            'quality_metrics': {
                'code_coverage': coverage.get('percent_covered', 0),
                'modular_coverage': modular_coverage
            },
            'test_results': categorized_tests,
            'recommendations': self._generate_recommendations(success_rate, coverage)
        }

    def _create_pdf_document(self, pdf_path: Path, data: Dict[str, Any]):
        """Construye el documento PDF usando Platypus."""
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm
        )

        elements = []
        styles = getSampleStyleSheet()
        
        # Estilos personalizados
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], textColor=colors.navy, alignment=1)
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], textColor=colors.grey, alignment=1)
        h2_style = ParagraphStyle('Heading2Custom', parent=styles['Heading2'], textColor=colors.navy, spaceBefore=20)
        
        # 1. Título
        elements.append(Paragraph("📊 Informe de Auditoría de Tests", title_style))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"ID: {data['report_id']} | Fecha: {data['timestamp']}", subtitle_style))
        elements.append(Spacer(1, 1*cm))

        # 2. Resumen Ejecutivo (Tabla métricas)
        elements.append(Paragraph("Resumen Ejecutivo", h2_style))
        elements.append(Spacer(1, 0.5*cm))
        
        summary_data = [
            ["Total Tests", "Exitosos", "Fallidos", "Tasa Éxito", "Cobertura"],
            [
                str(data['summary']['total_tests']),
                str(data['summary']['passed_tests']),
                str(data['summary']['failed_tests']),
                f"{data['summary']['success_rate']}%",
                f"{data['quality_metrics']['code_coverage']}%"
            ]
        ]
        
        t_summary = Table(summary_data, colWidths=[3*cm]*5)
        t_summary.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.navy),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        elements.append(t_summary)
        elements.append(Spacer(1, 1*cm))

        # 2.1 Cobertura por Módulo
        elements.append(Paragraph("Cobertura por Módulo", h2_style))
        elements.append(Spacer(1, 0.5*cm))
        
        mod_table_data = [["Módulo", "Cobertura Est."] ]
        for mod in data['quality_metrics']['modular_coverage']:
            mod_table_data.append([mod['name'], f"{mod['percent']}%"])
            
        t_mod = Table(mod_table_data, colWidths=[6*cm, 4*cm])
        t_mod.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.navy),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ]))
        elements.append(t_mod)
        elements.append(Spacer(1, 1*cm))

        # 3. Recomendaciones
        elements.append(Paragraph("Recomendaciones", h2_style))
        rec_list = [ListItem(Paragraph(rec, styles['Normal'])) for rec in data['recommendations']]
        elements.append(ListFlowable(rec_list, bulletType='bullet', start='circle'))
        elements.append(Spacer(1, 1*cm))

        # 4. Resultados Detallados
        elements.append(Paragraph("Resultados Detallados", h2_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Tabla de resultados
        # Header
        table_data = [["Categoría", "Test", "Estado"]]
        
        # Rows
        for test in data['test_results']:
            # Shorten test name if too long
            test_name = (test['test_name'][:40] + '...') if len(test['test_name']) > 40 else test['test_name']
            table_data.append([
                test['category'],
                test_name,
                test['status']
            ])

        t_results = Table(table_data, colWidths=[5*cm, 8*cm, 3*cm])
        
        # Estilo dinámico para resultados
        table_style = [
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ALIGN', (0,1), (-1,-1), 'LEFT'),
            ('ALIGN', (2,1), (-1,-1), 'CENTER'),
        ]

        # Colorear filas según estado
        for i, row in enumerate(data['test_results'], start=1):
            if row['status'] == 'PASS':
                bg_color = colors.lightgreen
            else:
                bg_color = colors.lightpink
            table_style.append(('BACKGROUND', (2, i), (2, i), bg_color))

        t_results.setStyle(TableStyle(table_style))
        elements.append(t_results)

        # Build
        doc.build(elements)

    def _categorize_tests(self, validation_results: List[Dict]) -> List[Dict[str, Any]]:
        """Organiza los tests por categorías funcionales."""
        test_map = {
            "test_add_and_get_product": "Base de Datos",
            "test_search_products": "Base de Datos",
            "test_complex_scheduler_logic": "Planificación",
            "test_entire_application_cycle": "Validación Global",
            "test_database_connection": "Infraestructura",
            "test_product_crud": "Productos",
            "test_simulation_engine": "Simulación",
            "test_report_generation": "Reportes",
        }

        categorized = []
        for result in validation_results:
            name = result['test_name']
            # Simple heuristic matching
            category = "Unitarios"
            for key, val in test_map.items():
                if key in name:
                    category = val
                    break
            
            # Categoría por prefijo si no coincide mapa exacto
            if category == "Unitarios":
                if "worker" in name: category = "Trabajadores"
                elif "product" in name: category = "Productos"
                elif "machine" in name: category = "Máquinas"
            
            categorized.append({
                "category": category,
                "test_name": name,
                "status": result['status']
            })
        return categorized

    def _calculate_modular_coverage(self, files_data: Dict) -> List[Dict]:
        """Calcula la cobertura por grupos lógicos de archivos."""
        modules = [
            ('Repositorios', 'database/repositories/'),
            ('Core', 'core/'),
            ('Controllers', 'controllers/'),
            ('UI Dialogs', 'ui/dialogs/'),
            ('UI Widgets', 'ui/widgets/'),
            ('App Root', 'app.py')
        ]
        
        results = []
        for name, prefix in modules:
            total_lines = 0
            covered_lines = 0
            
            for file_path, data in files_data.items():
                if file_path.startswith(prefix):
                    summary = data.get('summary', {})
                    total_lines += summary.get('num_statements', 0)
                    covered_lines += summary.get('covered_lines', 0)
            
            percent = round((covered_lines / total_lines * 100), 2) if total_lines > 0 else 0
            results.append({'name': name, 'percent': percent})
            
        return results

    def _generate_recommendations(self, success_rate: float, coverage: Dict) -> List[str]:
        recommendations = []
        if success_rate < 95:
            recommendations.append("Revisar tests fallidos antes de desplegar.")
        
        coverage_pct = coverage.get('percent_covered', 0)
        if coverage_pct < 80:
            recommendations.append(f"Aumentar cobertura de código (actual: {coverage_pct}%).")
            
        if success_rate == 100 and coverage_pct >= 80:
            recommendations.append("Sistema estable y listo para producción.")
            
        if not recommendations:
            recommendations.append("Continuar monitoreo regular.")
            
        return recommendations


class PytestAuditPlugin:
    """Plugin de pytest que captura resultados y genera informe."""

    def __init__(self):
        self.test_results = []
        self.start_time = None
        self.coverage_data = {}

    def pytest_sessionstart(self, session):
        self.start_time = datetime.now()
        logging.info("=== Iniciando sesión de auditoría ===")

    def pytest_runtest_logreport(self, report):
        if report.when == 'call':
            self.test_results.append({
                'test_name': report.nodeid.split("::")[-1],
                'status': 'PASS' if report.passed else 'FAIL',
                'duration': report.duration
            })

    def pytest_sessionfinish(self, session, exitstatus):
        duration = (datetime.now() - self.start_time).total_seconds()
        self.coverage_data = self._load_coverage_data()

        audit_data = {
            'validation_results': self.test_results,
            'coverage': self.coverage_data,
            'raw_coverage_files': self.coverage_data.get('files', {}),
            'test_duration': duration,
            'timestamp': datetime.now().isoformat()
        }

        reporter = ISO9001AuditReporter()
        pdf_path = reporter.generate_business_pdf_report(audit_data)

        if pdf_path:
            print(f"\n{'=' * 70}")
            print(f"📄 INFORME DE AUDITORÍA: {pdf_path}")
            print(f"{'=' * 70}\n")

    def _load_coverage_data(self) -> Dict[str, Any]:
        coverage_file = Path("test_reports/coverage.json")
        if not coverage_file.exists():
            return {'percent_covered': 0, 'lines_covered': 0, 'lines_total': 0}

        try:
            with open(coverage_file, 'r', encoding='utf-8') as f:
                cov_data = json.load(f)
            totals = cov_data.get('totals', {})
            return {
                'percent_covered': totals.get('percent_covered', 0),
                'lines_covered': totals.get('covered_lines', 0),
                'lines_total': totals.get('num_statements', 0),
                'files': cov_data.get('files', {})
            }
        except Exception as e:
            logging.error(f"Error al leer cobertura: {e}")
            return {'percent_covered': 0, 'lines_covered': 0, 'lines_total': 0}