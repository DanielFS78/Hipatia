# -*- coding: utf-8 -*-
"""Tests unitarios para FlowBuilderService.

Cubre build_flow_from_override (casos vacío, copia profunda, actualización de unidades)
y resolve_worker_assignments (workers existentes, asignación por skill, sin worker adecuado).
Sin dependencias externas; workers simulados con mocks con spec.
"""
import pytest
from unittest.mock import MagicMock
from core.services.flow_builder_service import FlowBuilderService

pytestmark = pytest.mark.unit


class TestFlowBuilderService:

    @pytest.fixture
    def service(self):
        return FlowBuilderService()

    def test_build_flow_from_override_empty(self, service):
        assert service.build_flow_from_override(None, 10) == []
        assert service.build_flow_from_override([], 10) == []

    def test_build_flow_from_override_updates_units(self, service):
        override = [
            {'task': {'id': 1}, 'trigger_units': 1},
            {'task': {'id': 2}, 'trigger_units': 5}
        ]
        units = 50
        result = service.build_flow_from_override(override, units)
        
        assert len(result) == 2
        assert result[0]['trigger_units'] == 50
        assert result[1]['trigger_units'] == 50
        # Ensure deep copy
        assert result is not override
        assert result[0] is not override[0]

    def test_resolve_worker_assignments_existing_workers(self, service):
        flow = [{'workers': [{'name': 'Juan'}], 'task': {'required_skill_level': 1}}]
        workers: list = []
        result = service.resolve_worker_assignments(flow, workers)
        assert len(result) == 1
        assert result[0]['workers'][0]['name'] == 'Juan'

    def test_resolve_worker_assignments_assigns_correct_worker(self, service):
        flow = [{'workers': [], 'task': {'required_skill_level': 2, 'name': 'Task 1'}}]
        w1 = MagicMock(spec=['nombre_completo', 'tipo_trabajador'])
        w1.nombre_completo = "Novato"
        w1.tipo_trabajador = 1
        w2 = MagicMock(spec=['nombre_completo', 'tipo_trabajador'])
        w2.nombre_completo = "Experto"
        w2.tipo_trabajador = 3
        sorted_workers = [w2, w1]
        result = service.resolve_worker_assignments(flow, sorted_workers)
        assert len(result) == 1
        assert len(result[0]['workers']) == 1
        assert result[0]['workers'][0]['name'] == "Experto"

    def test_resolve_worker_assignments_no_suitable_worker(self, service):
        flow = [{'workers': [], 'task': {'required_skill_level': 5, 'name': 'Impossible Task'}}]
        w1 = MagicMock(spec=['nombre_completo', 'tipo_trabajador'])
        w1.nombre_completo = "Novato"
        w1.tipo_trabajador = 1
        sorted_workers = [w1]
        result = service.resolve_worker_assignments(flow, sorted_workers)
        assert len(result) == 1
        assert len(result[0]['workers']) == 0

    def test_public_api_methods_are_called(self, service):
        """Smoke de interacción: el servicio se invoca vía API pública."""
        spy = MagicMock(wraps=service.build_flow_from_override)
        service.build_flow_from_override = spy
        out = service.build_flow_from_override([], 10)
        assert spy.call_count == 1
        spy.assert_called_once_with([], 10)
        assert out == []
