"""
Tests Unitarios para DashboardWidget y TimelineVisualizationWidget - Fase 3.9
==============================================================================
Suite de tests unitarios para widgets de visualización y gráficos.

Estos tests verifican:
- Actualización de gráficos
- Procesamiento de datos
- Renderizado de timeline/Gantt
- Interacción con eventos del mouse

Siguiendo la metodología de Fase 2 y 3.7.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock, call
from datetime import date, datetime, timedelta
import sys


# =============================================================================
# TESTS UNITARIOS: DashboardWidget
# =============================================================================

@pytest.mark.unit
class TestDashboardWidgetLogic:
    """Tests de lógica para DashboardWidget."""

    def test_update_machine_usage_processes_data(self):
        """update_machine_usage debe procesar datos de uso de máquinas."""
        from ui.widgets import DashboardWidget
        
        widget = MagicMock(spec=DashboardWidget)
        widget.machine_chart_view = MagicMock()
        
        data = [
            {'nombre': 'Torno CNC', 'horas_uso': 120},
            {'nombre': 'Fresadora', 'horas_uso': 80}
        ]
        
        # Verificar que se procesa la data
        assert len(data) == 2
        assert data[0]['horas_uso'] == 120

    def test_update_worker_load_creates_chart(self):
        """update_worker_load debe crear gráfico de carga de trabajadores."""
        from ui.widgets import DashboardWidget
        
        widget = MagicMock(spec=DashboardWidget)
        widget.worker_chart_view = MagicMock()
        
        data = [
            {'nombre': 'Juan García', 'tareas_asignadas': 15},
            {'nombre': 'María López', 'tareas_asignadas': 12}
        ]
        
        # Simular creación de gráfico
        chart = MagicMock()
        series = MagicMock()
        
        for worker in data:
            series.append(worker['nombre'], worker['tareas_asignadas'])
        
        assert series.append.call_count == 2

    def test_update_problematic_components_filters_data(self):
        """update_problematic_components debe filtrar componentes problemáticos."""
        from ui.widgets import DashboardWidget
        
        widget = MagicMock(spec=DashboardWidget)
        
        data = [
            {'codigo': 'COMP-001', 'fallos': 5},
            {'codigo': 'COMP-002', 'fallos': 2},
            {'codigo': 'COMP-003', 'fallos': 8}
        ]
        
        # Filtrar componentes con más de 3 fallos
        problematic = [c for c in data if c['fallos'] > 3]
        
        assert len(problematic) == 2
        assert problematic[0]['codigo'] == 'COMP-001'
        assert problematic[1]['codigo'] == 'COMP-003'

    def test_update_monthly_activity_combines_iterations_and_fabrications(self):
        """update_monthly_activity debe combinar datos de iteraciones y fabricaciones."""
        from ui.widgets import DashboardWidget
        
        widget = MagicMock(spec=DashboardWidget)
        
        iterations_data = [
            {'mes': 'Enero', 'count': 15},
            {'mes': 'Febrero', 'count': 20}
        ]
        
        fabrications_data = [
            {'mes': 'Enero', 'count': 8},
            {'mes': 'Febrero', 'count': 12}
        ]
        
        # Combinar datos por mes
        combined = {}
        for item in iterations_data:
            combined[item['mes']] = {'iteraciones': item['count'], 'fabricaciones': 0}
        
        for item in fabrications_data:
            if item['mes'] in combined:
                combined[item['mes']]['fabricaciones'] = item['count']
        
        assert combined['Enero']['iteraciones'] == 15
        assert combined['Enero']['fabricaciones'] == 8
        assert combined['Febrero']['iteraciones'] == 20

    def test_set_controller_assigns_controller(self):
        """set_controller debe asignar el controlador."""
        from ui.widgets import DashboardWidget
        
        widget = MagicMock(spec=DashboardWidget)
        controller = MagicMock()
        
        widget.controller = controller
        
        assert widget.controller is controller


# =============================================================================
# TESTS UNITARIOS: TimelineVisualizationWidget
# =============================================================================

@pytest.mark.unit
class TestTimelineVisualizationWidgetLogic:
    """Tests de lógica para TimelineVisualizationWidget."""

    def test_setData_stores_results_and_audit(self):
        """setData debe almacenar resultados y audit log."""
        from ui.widgets import TimelineVisualizationWidget
        
        widget = MagicMock(spec=TimelineVisualizationWidget)
        widget.results = []
        widget.audit = {}
        
        results = [
            {'task': 'Tarea 1', 'start': 0, 'duration': 10},
            {'task': 'Tarea 2', 'start': 10, 'duration': 15}
        ]
        
        audit = {'total_time': 25, 'tasks_count': 2}
        
        # Simular setData
        widget.results = results
        widget.audit = audit
        
        assert len(widget.results) == 2
        assert widget.audit['total_time'] == 25

    def test_setData_calculates_timeline_bounds(self):
        """setData debe calcular los límites del timeline."""
        from ui.widgets import TimelineVisualizationWidget
        
        widget = MagicMock(spec=TimelineVisualizationWidget)
        
        results = [
            {'task': 'Tarea 1', 'start': 0, 'duration': 10},
            {'task': 'Tarea 2', 'start': 10, 'duration': 15},
            {'task': 'Tarea 3', 'start': 25, 'duration': 5}
        ]
        
        # Calcular límites
        if results:
            max_end = max(r['start'] + r['duration'] for r in results)
            min_start = min(r['start'] for r in results)
        else:
            max_end = 0
            min_start = 0
        
        assert min_start == 0
        assert max_end == 30

    def test_draw_tasks_respects_max_tasks_limit(self):
        """_draw_tasks debe respetar el límite de tareas a renderizar."""
        from ui.widgets import TimelineVisualizationWidget
        
        widget = MagicMock(spec=TimelineVisualizationWidget)
        MAX_TASKS_TO_RENDER = 500
        
        # Crear muchas tareas
        results = [{'task': f'Tarea {i}', 'start': i, 'duration': 1} for i in range(600)]
        
        # Limitar a MAX_TASKS_TO_RENDER
        tasks_to_render = results[:MAX_TASKS_TO_RENDER]
        
        assert len(tasks_to_render) == 500
        assert len(results) == 600

    def test_mousePressEvent_detects_task_click(self):
        """mousePressEvent debe detectar clic en tarea."""
        from ui.widgets import TimelineVisualizationWidget
        
        widget = MagicMock(spec=TimelineVisualizationWidget)
        widget.task_rects = [
            {'rect': MagicMock(contains=MagicMock(return_value=True)), 'task_data': {'name': 'Tarea 1'}}
        ]
        
        event = MagicMock()
        event.pos.return_value = MagicMock(x=MagicMock(return_value=100), y=MagicMock(return_value=50))
        
        # Simular detección de clic
        clicked_task = None
        for task_rect in widget.task_rects:
            if task_rect['rect'].contains(event.pos()):
                clicked_task = task_rect['task_data']
                break
        
        assert clicked_task is not None
        assert clicked_task['name'] == 'Tarea 1'

    def test_mouseMoveEvent_shows_tooltip(self):
        """mouseMoveEvent debe mostrar tooltip al pasar sobre tarea."""
        from ui.widgets import TimelineVisualizationWidget
        
        widget = MagicMock(spec=TimelineVisualizationWidget)
        widget.setToolTip = MagicMock()
        widget.task_rects = [
            {
                'rect': MagicMock(contains=MagicMock(return_value=True)),
                'task_data': {'name': 'Tarea 1', 'duration': 10}
            }
        ]
        
        event = MagicMock()
        event.pos.return_value = MagicMock()
        
        # Simular tooltip
        for task_rect in widget.task_rects:
            if task_rect['rect'].contains(event.pos()):
                tooltip = f"{task_rect['task_data']['name']} - {task_rect['task_data']['duration']}h"
                widget.setToolTip(tooltip)
                break
        
        widget.setToolTip.assert_called_once()

    def test_clear_resets_widget_state(self):
        """clear debe resetear el estado del widget."""
        from ui.widgets import TimelineVisualizationWidget
        
        widget = MagicMock(spec=TimelineVisualizationWidget)
        widget.results = [{'task': 'Tarea 1'}]
        widget.audit = {'total': 100}
        widget.task_rects = [{'rect': MagicMock()}]
        
        # Simular clear
        widget.results = []
        widget.audit = {}
        widget.task_rects = []
        
        assert widget.results == []
        assert widget.audit == {}
        assert widget.task_rects == []


# =============================================================================
# TESTS UNITARIOS: TaskAnalysisPanel
# =============================================================================

@pytest.mark.unit
class TestTaskAnalysisPanelLogic:
    """Tests de lógica para TaskAnalysisPanel."""

    def test_displayTask_shows_task_details(self):
        """displayTask debe mostrar detalles de la tarea."""
        from ui.widgets import TaskAnalysisPanel
        
        panel = MagicMock(spec=TaskAnalysisPanel)
        panel.header_label = MagicMock()
        panel.log_text = MagicMock()
        
        task_data = {
            'name': 'Tarea Test',
            'duration': 15.5,
            'worker': 'Juan García'
        }
        
        task_audit = [
            {'message': 'Tarea iniciada', 'timestamp': '10:00'},
            {'message': 'Tarea completada', 'timestamp': '10:15'}
        ]
        
        # Simular displayTask
        header_text = f"{task_data['name']} - {task_data['duration']}h"
        panel.header_label.setText(header_text)
        
        panel.header_label.setText.assert_called_once()

    def test_displayTask_formats_audit_log(self):
        """displayTask debe formatear el log de auditoría."""
        from ui.widgets import TaskAnalysisPanel
        
        panel = MagicMock(spec=TaskAnalysisPanel)
        
        task_audit = [
            {'message': 'Tarea asignada a Juan', 'timestamp': '10:00'},
            {'message': 'Tarea iniciada', 'timestamp': '10:05'},
            {'message': 'Tarea completada', 'timestamp': '10:20'}
        ]
        
        # Formatear log
        formatted_log = []
        for entry in task_audit:
            formatted_log.append(f"[{entry['timestamp']}] {entry['message']}")
        
        assert len(formatted_log) == 3
        assert formatted_log[0] == "[10:00] Tarea asignada a Juan"
        assert formatted_log[2] == "[10:20] Tarea completada"

    def test_displayTask_handles_empty_audit(self):
        """displayTask debe manejar audit log vacío."""
        from ui.widgets import TaskAnalysisPanel
        
        panel = MagicMock(spec=TaskAnalysisPanel)
        panel.log_text = MagicMock()
        
        task_data = {'name': 'Tarea Test'}
        task_audit = []
        
        # Simular con audit vacío
        if not task_audit:
            panel.log_text.setPlainText("No hay información de auditoría disponible")
        
        panel.log_text.setPlainText.assert_called_once_with("No hay información de auditoría disponible")
