
import pytest
from unittest.mock import MagicMock, patch, mock_open
import os
import json
from datetime import datetime
from controllers.app_controller import AppController
from calculation_audit import CalculationDecision, DecisionStatus

@pytest.fixture
def mock_controller(qapp):
    model = MagicMock()
    model.db = MagicMock()
    controller = AppController(model, MagicMock(), MagicMock())
    return controller

class TestAppControllerChunking:

    def test_save_chunk_results(self, mock_controller):
        """Test saving chunk results to JSON."""
        results = [{"id": 1}]
        audit = [CalculationDecision(
            timestamp=datetime.now(),
            decision_type="TEST",
            reason="R1",
            user_friendly_reason="Friendly R1",
            task_name="T1",
            status=DecisionStatus.POSITIVE
        )]
        
        with patch("builtins.open", mock_open()) as m:
            path = mock_controller._save_chunk_results(0, results, audit)
            
            assert "chunk_0.json" in path
            m.assert_called_once()
            handle = m()
            handle.write.assert_called()

    def test_consolidate_chunk_results(self, mock_controller):
        """Test consolidating multiple chunk files."""
        # Create dummy data matching CalculationDecision fields
        audit_item1 = {
            "timestamp": datetime.now().isoformat(),
            "decision_type": "D1",
            "reason": "R1",
            "user_friendly_reason": "UFR1",
            "task_name": "T1",
            "status": "POSITIVE" 
        }
        audit_item2 = {
            "timestamp": datetime.now().isoformat(),
            "decision_type": "D2",
            "reason": "R2",
            "user_friendly_reason": "UFR2",
            "task_name": "T2",
            "status": "WARNING"
        }
        
        data1 = {"results": [{"id": 1}], "audit": [audit_item1]}
        data2 = {"results": [{"id": 2}], "audit": [audit_item2]}
        
        with patch("builtins.open", mock_open()) as m:
            # We skip 'open' logic test here because mocking open iteration is complex
            # Instead we mock json.load to return our data
            files = ["f1.json", "f2.json"]
            
            with patch("json.load", side_effect=[data1, data2]):
                results, audit = mock_controller._consolidate_chunk_results(files)
                
                assert len(results) == 2
                assert len(audit) == 2
                assert isinstance(audit[0], CalculationDecision)
                assert audit[0].status == DecisionStatus.POSITIVE
                assert audit[1].status == DecisionStatus.WARNING

    def test_map_task_keys(self, mock_controller):
        """Test the robust task key mapping."""
        # Case 1: Perfect data
        task1 = {"id": "t1", "name": "Task 1", "duration": 10.5, "department": "D1"}
        mapped1 = mock_controller._map_task_keys(task1, 100)
        assert mapped1["id"] == "t1"
        assert mapped1["duration"] == 10.5
        assert mapped1["trigger_units"] == 100
        
        # Case 2: Legacy keys
        task2 = {"descripcion": "Task 2", "tiempo": "20,5", "tipo_trabajador": 3}
        mapped2 = mock_controller._map_task_keys(task2, 50)
        assert mapped2["name"] == "Task 2"
        assert mapped2["duration"] == 20.5
        assert mapped2["required_skill_level"] == 3
        
        # Case 3: Missing time (should warn but not crash)
        task3 = {"name": "No Time"}
        with patch.object(mock_controller.logger, 'warning') as mock_warn:
            mapped3 = mock_controller._map_task_keys(task3, 10)
            mock_warn.assert_called()
            assert mapped3["duration"] == 0.0
