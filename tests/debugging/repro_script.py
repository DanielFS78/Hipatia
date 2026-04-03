import sys
import os
from unittest.mock import MagicMock
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from core.simulation.simulation_events import EventoFinUnidad

# Define FakeEngine here
class ConcreteMockEngine:
    def __init__(self):
        self.logger = MagicMock()
        self.lineas_temporales = {}
        self.gestor_recursos = MagicMock()
        self.calculador_tiempos = MagicMock()
        self.calculador_tiempos.add_work_minutes.side_effect = lambda start, dur: start + timedelta(minutes=dur)
        self.eventos_futuros = []
        self.audit_log_interno = []
        self.tarea_id_a_indice = {}
        self.indice_a_tarea_id = {}
        self.production_flow = []
        self.cancelar_eventos = MagicMock()

    def _verificar_dependencias_cumplidas(self, *args, **kwargs):
        return []

    def _tiene_evento_futuro(self, *args):
        return False
    
    def programar_eventos(self, *args):
        pass

def run():
    print("Staritng repro...")
    mock_engine = ConcreteMockEngine()
    
    lt = MagicMock()
    lt.name = "Test Task"
    lt.unidades_finalizadas_total = 1
    lt.unidades_a_producir = 10
    lt.instancias_activas = []
    lt.historial_unidades = []
    lt.eventos_futuros = []
    lt.dependency_index = 0
    lt.completar_unidad_instancia.return_value = {
        'tarea_completada': False,
        'trabajadores_liberados': ['Worker A']
    }
    lt.trabajadores_asignados = ['Worker A']
    lt.obtener_instancia.return_value = {'trabajadores': ['Worker A'], 'unidad_actual': 1}

    task_id = "task_2"
    pred_id = "task_1"
    
    mock_engine.lineas_temporales[task_id] = lt
    
    mock_pred = MagicMock()
    mock_pred.name = "Predecessor"
    mock_pred.unidades_completadas = 0
    mock_engine.lineas_temporales[pred_id] = mock_pred
    
    mock_engine.tarea_id_a_indice = {task_id: 1, pred_id: 0}
    mock_engine.indice_a_tarea_id = {0: pred_id}
    mock_engine.production_flow = [{}, {'previous_task_index': 0}]
    
    future_time = datetime(2023, 1, 1, 8, 10)
    mock_event_obj = MagicMock()
    mock_event_obj.tipo_evento = 'FIN_BLOQUE_TRABAJO'
    mock_event_obj.datos = {'tarea_id': pred_id, 'numero_unidad': 1}
    
    # Comparisons
    mock_event_obj.__lt__ = lambda s, o: True
    mock_event_obj.__gt__ = lambda s, o: True
    mock_event_obj.__le__ = lambda s, o: True
    mock_event_obj.__ge__ = lambda s, o: True
    mock_event_obj.__eq__ = lambda s, o: True
    mock_event_obj.__ne__ = lambda s, o: False
    
    # IMPORTANT: Ensure mock behaves like it's NOT a number if treated as number
    mock_event_obj.__int__ = lambda s: 999 

    mock_engine.eventos_futuros = [(future_time, 2, mock_event_obj)]
    
    event = EventoFinUnidad(
        timestamp=datetime(2023, 1, 1, 8, 0),
        datos={'tarea_id': task_id, 'numero_unidad': 1, 'id_instancia': 'inst_1'}
    )

    print(f"future_time type: {type(future_time)}")
    print(f"event.timestamp type: {type(event.timestamp)}")
    
    try:
        event.procesar(mock_engine)
        print("Success!")
    except Exception as e:
        print(f"Caught exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run()
