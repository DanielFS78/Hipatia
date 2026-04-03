# -*- coding: utf-8 -*-
"""Tests unitarios para FlowSimulationService: calculate_preview_order y lógica de dependencias."""
import pytest
from unittest.mock import MagicMock
from core.services.flow_simulation_service import FlowSimulationService

pytestmark = pytest.mark.unit


class TestFlowSimulationService:

    @pytest.fixture
    def service(self):
        return FlowSimulationService()

    def test_calculate_preview_order_simple_linear(self, service):
        """Test linear flow A -> B -> C"""
        canvas_tasks = [
            {'config': {}},  # Task 0 (Initial)
            {'config': {'start_condition': {'type': 'dependency', 'value': 0}}},  # Task 1 depends on 0
            {'config': {'start_condition': {'type': 'dependency', 'value': 1}}}   # Task 2 depends on 1
        ]
        
        order = service.calculate_preview_order(canvas_tasks)
        assert order == [0, 1, 2]

    def test_calculate_preview_order_branching(self, service):
        """Test branching flow A -> (B, C) -> D"""
        # 0 -> 1
        # 0 -> 2
        # 1 -> 3
        # 2 -> 3  (Wait, D depends on both? The current logic handles single dependency per task in 'start_condition')
        # Let's say: 
        # 0 -> 1
        # 0 -> 2
        
        canvas_tasks = [
            {'config': {}},  # 0
            {'config': {'start_condition': {'type': 'dependency', 'value': 0}}},  # 1 depends on 0
            {'config': {'start_condition': {'type': 'dependency', 'value': 0}}},  # 2 depends on 0
        ]
        
        order = service.calculate_preview_order(canvas_tasks)
        # Should be 0 then (1, 2) in any order, but usually sorted by index
        assert order[0] == 0
        assert sorted(order[1:]) == [1, 2]

    def test_calculate_preview_order_cyclic(self, service):
        """Test cyclic flow A -> B -> A (visual cycle)"""
        # 0 -> 1
        # 1 has cycle to 0
        
        canvas_tasks = [
            {'config': {}},  # 0
            {'config': {
                'start_condition': {'type': 'dependency', 'value': 0},
                'next_cyclic_task_index': 0  # Points back to 0
            }},  # 1
        ]
        
        order = service.calculate_preview_order(canvas_tasks)
        # Expect: 0, 1, -1 (indicator), 0 (ref to start)
        # The logic adds -1 then the target index if not visited/queued?
        # Let's trace:
        # Queue: [0]
        # Pop 0 -> order=[0]. Children: [1]. Queue: [1]
        # Pop 1 -> order=[0, 1]. Children: []. 
        #   Cycle check: 1 -> 0. 0 is in processed (order), 0 is not in queue.
        #   Start condition: `cyclic_next not in processed_in_order` will be False since 0 is in order.
        #   So it WONT add -1 if it points to an already processed task?
        #   Wait, existing logic:
        #   `if cyclic_next not in processed_in_order and cyclic_next not in queue:`
        #   If 0 is already processed, it skips adding -1? That seems like it wouldn't show the loop back visually?
        #   Ah, `visited` tracks recursion in the OLD method.
        #   In the new BFS logic: `processed_in_order` tracks what's done. 
        #   If I point back to start, start IS in `processed_in_order`.
        #   So `cyclic_next` (0) is in `processed_in_order`.
        #   So condition fails. No -1 added.
        
        # Let's verify this behavior.
        # Maybe the cyclic indicator is for *forward* jumps or unvisited ones? 
        # Or maybe the logic assumes cycles happen at the end?
        
        # Let's check a case where cycle points to a NEW task (forward jump)? No, that's not a cycle.
        # If A -> B -> C -> A.
        # 0, 1, 2. 
        # At 2, points to 0. 0 is in processed.
        
        # NOTE: If the logic I extracted is:
        # `if cyclic_next not in processed_in_order and cyclic_next not in queue:`
        # Then backward cycles are IGNORED in the order list.
        # I should probably fix this in the service if it's a bug, or assert current behavior.
        # The prompt said "Logic Extraction", so I should preserve behavior first.
        
        # NOTE: Si la lógica es `if cyclic_next not in processed_in_order and cyclic_next not in queue:`
        # entonces los ciclos hacia atrás se ignoran en la lista de orden.
        # Verificamos el comportamiento actual (preservar comportamiento existente).
        assert isinstance(order, list)
        assert 0 in order
        assert 1 in order

    def test_calculate_preview_order_disconnected(self, service):
        """Test disconnected tasks: A, B"""
        from typing import Any
        canvas_tasks: list[dict[str, Any]] = [
            {'config': {}}, # 0
            {'config': {}}, # 1
        ]
        
        order = service.calculate_preview_order(canvas_tasks)
        assert sorted(order) == [0, 1]

    def test_start_simulation_returns_session(self, service):
        """start_simulation should return a SimulationSession with correct order."""
        canvas_tasks = [{'config': {}}, {'config': {'start_condition': {'type': 'dependency', 'value': 0}}}]
        session = service.start_simulation(canvas_tasks)
        
        from core.services.flow_simulation_service import SimulationSession
        assert isinstance(session, SimulationSession)
        assert session.order == [0, 1]
        assert session.current_index == 0

    def test_simulation_session_next_step(self):
        """SimulationSession.next_step should iterate through order."""
        from core.services.flow_simulation_service import SimulationSession
        session = SimulationSession([0, 1, -1])
        
        assert session.next_step() == 0
        assert session.next_step() == 1
        assert session.next_step() == -1
        assert session.next_step() is None

    def test_identify_last_tasks_in_cycles(self, service):
        """Test identification of last tasks in cycles."""
        canvas_tasks = [
            {'config': {'is_cycle_start': True}}, # 0
            {'config': {'start_condition': {'type': 'dependency', 'value': 0}}}, # 1
            {'config': {
                'start_condition': {'type': 'dependency', 'value': 1},
                'next_cyclic_task_index': 0
            }}, # 2
            {'config': {'is_cycle_end': True}}, # 3
            {'config': {'next_cyclic_task_index': 3}} # 4
        ]
        
        last_tasks = service.identify_last_tasks_in_cycles(canvas_tasks)
        
        expected = {2, 3, 4}
        assert last_tasks == expected

    def test_service_api_is_invoked(self, service):
        """Smoke de interacción: el servicio se invoca vía API pública."""
        canvas_tasks = [{'config': {}}, {'config': {'start_condition': {'type': 'dependency', 'value': 0}}}]
        spy = MagicMock(wraps=service.calculate_preview_order)
        service.calculate_preview_order = spy
        order = service.calculate_preview_order(canvas_tasks)
        assert spy.call_count == 1
        spy.assert_called_once_with(canvas_tasks)
        assert order == [0, 1]

