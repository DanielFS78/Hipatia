# -*- coding: utf-8 -*-
"""Tests unitarios para eventos de simulación (EventoInicioUnidad, EventoFinUnidad, EventoReasignacionTrabajador, EventoTiempoInactivo).

Cubre procesamiento correcto, tarea inexistente, instancia no encontrada, tarea ya completada,
retraso por recurso, reasignación ON_FINISH/AFTER_UNITS, lógica cíclica, dependencias,
registro de inactividad y modos REPLACE/PARALLEL_JOIN.
Decisión de mocking: engine con atributos mínimos; lineas temporales con spec de métodos usados.
"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from core.simulation.simulation_events import EventoInicioUnidad, EventoFinUnidad, EventoReasignacionTrabajador, EventoTiempoInactivo
from core.simulation.timeline_task import LineaTemporalTarea

pytestmark = pytest.mark.unit


class ComparableEvent:
    """Objeto comparable para `sorted()` en eventos futuros."""

    def __init__(self, tipo_evento, datos):
        self.tipo_evento = tipo_evento
        self.datos = datos

    def __lt__(self, other):  # pragma: no cover
        return True

    def __gt__(self, other):  # pragma: no cover
        return True

    def __le__(self, other):  # pragma: no cover
        return True

    def __ge__(self, other):  # pragma: no cover
        return True

    def __eq__(self, other):  # pragma: no cover
        return True

    def __ne__(self, other):  # pragma: no cover
        return False


# Concrete class to avoid MagicMock iteration issues
class ConcreteMockEngine:
    def __init__(self):
        self.logger = MagicMock(spec=["debug", "info", "warning", "error"])
        self.lineas_temporales = {}
        self.gestor_recursos = MagicMock(spec=[])
        self.calculador_tiempos = MagicMock(spec=["add_work_minutes"])
        self.calculador_tiempos.add_work_minutes.side_effect = lambda start, dur: start + timedelta(minutes=dur)
        self.eventos_futuros = []
        self.audit_log_interno = []
        self.tarea_id_a_indice = {}
        self.indice_a_tarea_id = {}
        self.production_flow = []
        self.cancelar_eventos = MagicMock(spec=[])

    def _verificar_dependencias_cumplidas(self, *args, **kwargs):
        return []

    def _tiene_evento_futuro(self, *args):
        return False
    
    def programar_eventos(self, *args):
        pass

class TestEventoInicioUnidad:

    @pytest.fixture
    def mock_engine(self):
        engine = MagicMock(spec=['logger', 'lineas_temporales', 'gestor_recursos', 'calculador_tiempos'])
        engine.logger = MagicMock(spec=["debug", "info", "warning", "error"])
        engine.lineas_temporales = {}
        engine.gestor_recursos = MagicMock(spec=['calendario_trabajadores', 'encontrar_siguiente_momento_disponible', 'asignar_recurso'])
        engine.calculador_tiempos = MagicMock(spec=['add_work_minutes'])
        engine.calculador_tiempos.add_work_minutes.side_effect = lambda start, dur: start + timedelta(minutes=dur)
        return engine

    @pytest.fixture
    def mock_linea_temporal(self):
        lt = MagicMock(spec=['name', 'unidades_finalizadas_total', 'unidades_a_producir', 'machine_id', 'duration_per_unit', 'obtener_instancia'])
        lt.name = "Test Task"
        lt.unidades_finalizadas_total = 0
        lt.unidades_a_producir = 10
        lt.machine_id = None
        lt.duration_per_unit = 60
        return lt

    def test_procesar_success(self, mock_engine, mock_linea_temporal):
        task_id = "task_1"
        mock_engine.lineas_temporales[task_id] = mock_linea_temporal
        mock_instance = {'trabajadores': ['Worker A'], 'inicio_unidad': None}
        mock_linea_temporal.obtener_instancia.return_value = mock_instance
        
        mock_engine.gestor_recursos.calendario_trabajadores = {'Worker A': {}}
        mock_engine.gestor_recursos.encontrar_siguiente_momento_disponible.return_value = datetime(2023, 1, 1, 8, 0)

        event = EventoInicioUnidad(
            timestamp=datetime(2023, 1, 1, 8, 0),
            datos={'tarea_id': task_id, 'unidad': 1, 'id_instancia': "inst_1"}
        )

        new_events = event.procesar(mock_engine)

        assert len(new_events) == 1
        assert isinstance(new_events[0], EventoFinUnidad)
        assert new_events[0].datos['duracion_calculada'] == 60

    def test_procesar_missing_task(self, mock_engine):
        event = EventoInicioUnidad(
            timestamp=datetime(2023, 1, 1, 8, 0),
            datos={'tarea_id': 'unknown', 'unidad': 1, 'id_instancia': 'inst_1'}
        )
        new_events = event.procesar(mock_engine)
        assert len(new_events) == 0

    def test_procesar_missing_instance_id(self, mock_engine, mock_linea_temporal):
        mock_engine.lineas_temporales["task_1"] = mock_linea_temporal
        event = EventoInicioUnidad(
            timestamp=datetime(2023, 1, 1, 8, 0),
            datos={'tarea_id': 'task_1', 'unidad': 1, 'id_instancia': None}
        )
        new_events = event.procesar(mock_engine)
        assert len(new_events) == 0

    def test_procesar_instance_not_found(self, mock_engine, mock_linea_temporal):
        mock_engine.lineas_temporales["task_1"] = mock_linea_temporal
        mock_linea_temporal.obtener_instancia.return_value = None
        event = EventoInicioUnidad(
            timestamp=datetime(2023, 1, 1, 8, 0),
            datos={'tarea_id': 'task_1', 'unidad': 1, 'id_instancia': 'inst_deleted'}
        )
        new_events = event.procesar(mock_engine)
        assert len(new_events) == 0

    def test_procesar_task_already_completed(self, mock_engine, mock_linea_temporal):
        mock_linea_temporal.unidades_finalizadas_total = 10
        mock_linea_temporal.unidades_a_producir = 10
        mock_engine.lineas_temporales["task_1"] = mock_linea_temporal
        mock_linea_temporal.obtener_instancia.return_value = {'trabajadores': ['A']}

        event = EventoInicioUnidad(
            timestamp=datetime(2023, 1, 1, 8, 0),
            datos={'tarea_id': 'task_1', 'unidad': 11, 'id_instancia': 'inst_1'}
        )
        new_events = event.procesar(mock_engine)
        assert len(new_events) == 0 

    def test_procesar_no_workers(self, mock_engine, mock_linea_temporal):
        mock_engine.lineas_temporales["task_1"] = mock_linea_temporal
        mock_linea_temporal.obtener_instancia.return_value = {'trabajadores': []}
        event = EventoInicioUnidad(
            timestamp=datetime(2023, 1, 1, 8, 0),
            datos={'tarea_id': 'task_1', 'unidad': 1, 'id_instancia': 'inst_1'}
        )
        new_events = event.procesar(mock_engine)
        assert len(new_events) == 0

    def test_procesar_resource_unavailable_delay(self, mock_engine, mock_linea_temporal):
        mock_engine.lineas_temporales["task_1"] = mock_linea_temporal
        mock_linea_temporal.obtener_instancia.return_value = {'trabajadores': ['Worker A']}
        mock_engine.gestor_recursos.calendario_trabajadores = {'Worker A': {}}
        mock_engine.gestor_recursos.encontrar_siguiente_momento_disponible.return_value = datetime(2023, 1, 1, 9, 0)

        event = EventoInicioUnidad(
            timestamp=datetime(2023, 1, 1, 8, 0),
            datos={'tarea_id': "task_1", 'unidad': 1, 'id_instancia': 'inst_1'}
        )
        new_events = event.procesar(mock_engine)
        assert len(new_events) == 1
        assert new_events[0].datos['inicio'] == datetime(2023, 1, 1, 9, 0)

class TestEventoFinUnidad:

    @pytest.fixture
    def mock_engine(self):
        # Use ConcreteMockEngine to avoid MagicMock iteration issues
        return ConcreteMockEngine()

    @pytest.fixture
    def mock_linea_temporal(self):
        lt = MagicMock(
            spec=[
                "id",
                "name",
                "unidades_finalizadas_total",
                "unidades_a_producir",
                "instancias_activas",
                "historial_unidades",
                "eventos_futuros",
                "dependency_index",
                "completar_unidad_instancia",
                "trabajadores_asignados",
                "obtener_instancia",
                "iniciar_instancia_inicial",
            ]
        )
        lt.id = "task_1"
        lt.name = "Test Task"
        lt.unidades_finalizadas_total = 0
        lt.unidades_a_producir = 10
        lt.instancias_activas = []
        lt.historial_unidades = []
        lt.eventos_futuros = []
        lt.dependency_index = None 
        lt.completar_unidad_instancia.return_value = {
            'tarea_completada': False,
            'trabajadores_liberados': ['Worker A']
        }
        lt.trabajadores_asignados = ['Worker A']
        lt.obtener_instancia.return_value = {'trabajadores': ['Worker A'], 'unidad_actual': 1}
        return lt

    def test_procesar_completion_standard(self, mock_engine, mock_linea_temporal):
        mock_engine.lineas_temporales["task_1"] = mock_linea_temporal
        mock_linea_temporal.iniciar_instancia_inicial.return_value = "inst_2"
        mock_linea_temporal.unidades_finalizadas_total = 1 

        event = EventoFinUnidad(
            timestamp=datetime(2023, 1, 1, 9, 0),
            datos={'tarea_id': 'task_1', 'numero_unidad': 1, 'id_instancia': 'inst_1', 'inicio': datetime(2023, 1, 1, 8, 0)}
        )

        new_events = event.procesar(mock_engine)
        assert len(new_events) == 1
        assert isinstance(new_events[0], EventoInicioUnidad)

    def test_procesar_task_completion(self, mock_engine, mock_linea_temporal):
        mock_engine.lineas_temporales["task_1"] = mock_linea_temporal
        mock_linea_temporal.completar_unidad_instancia.return_value = {
            'tarea_completada': True,
            'trabajadores_liberados': ['Worker A']
        }
        mock_linea_temporal.unidades_finalizadas_total = 10
        mock_linea_temporal.eventos_futuros = [object()]

        event = EventoFinUnidad(
            timestamp=datetime(2023, 1, 1, 18, 0),
            datos={'tarea_id': 'task_1', 'numero_unidad': 10, 'id_instancia': 'inst_10'}
        )

        new_events = event.procesar(mock_engine)
        assert mock_engine.cancelar_eventos.call_count >= 1
        assert mock_engine.cancelar_eventos.called
        assert not any(isinstance(e, EventoInicioUnidad) for e in new_events)

    def test_procesar_reasignment_on_finish(self, mock_engine, mock_linea_temporal):
        task_id = "task_1"
        mock_engine.lineas_temporales[task_id] = mock_linea_temporal
        mock_linea_temporal.completar_unidad_instancia.return_value = {
            'tarea_completada': True,
            'trabajadores_liberados': ['Worker A']
        }
        
        mock_engine.tarea_id_a_indice = {task_id: 0}
        mock_engine.production_flow = [{
            'workers': [{
                'name': 'Worker A',
                'reassignment_rule': {
                    'condition_type': 'ON_FINISH',
                    'target_task_id': 'task_2',
                    'mode': 'REPLACE'
                }
            }]
        }]
        
        event = EventoFinUnidad(
            timestamp=datetime(2023, 1, 1, 18, 0),
            datos={'tarea_id': task_id, 'numero_unidad': 10, 'id_instancia': 'inst_1'}
        )
        
        new_events = event.procesar(mock_engine)
        assert len(new_events) == 1
        assert isinstance(new_events[0], EventoReasignacionTrabajador)
        assert new_events[0].datos['motivo'] == "Condición cumplida: ON_FINISH"

    def test_procesar_after_units(self, mock_engine, mock_linea_temporal):
        task_id = "task_1"
        mock_engine.lineas_temporales[task_id] = mock_linea_temporal
        
        mock_engine.tarea_id_a_indice = {task_id: 0}
        mock_engine.production_flow = [{
            'workers': [{
                'name': 'Worker A',
                'reassignment_rule': {
                    'condition_type': 'AFTER_UNITS',
                    'condition_value': 5,
                    'target_task_id': 'task_2'
                }
            }]
        }]
        
        event = EventoFinUnidad(
            timestamp=datetime(2023, 1, 1, 12, 0),
            datos={'tarea_id': task_id, 'numero_unidad': 5, 'id_instancia': 'inst_5'}
        )
        
        new_events = event.procesar(mock_engine)
        assert len(new_events) == 1
        assert isinstance(new_events[0], EventoReasignacionTrabajador)

    def test_procesar_cyclic_logic(self, mock_engine, mock_linea_temporal):
        task_id = "task_1"
        mock_engine.lineas_temporales[task_id] = mock_linea_temporal
        mock_linea_temporal.completar_unidad_instancia.return_value = {
            'tarea_completada': True,
            'trabajadores_liberados': ['Worker A']
        }
        
        mock_engine.tarea_id_a_indice = {task_id: 0, "task_cyclic": 1}
        mock_engine.indice_a_tarea_id = {1: "task_cyclic"}
        mock_engine.production_flow = [
            {'units_per_cycle': 1, 'next_cyclic_task_index': 1}, 
            {}
        ]
        
        mock_target = MagicMock(spec=["unidades_finalizadas_total", "unidades_a_producir", "iniciar_instancia_inicial"])
        mock_target.unidades_finalizadas_total = 0
        mock_target.unidades_a_producir = 10
        mock_target.iniciar_instancia_inicial.return_value = "inst_cyclic"
        mock_engine.lineas_temporales["task_cyclic"] = mock_target

        event = EventoFinUnidad(
            timestamp=datetime(2023, 1, 1, 18, 0),
            datos={'tarea_id': task_id, 'numero_unidad': 1, 'id_instancia': 'inst_1'}
        )

        new_events = event.procesar(mock_engine)
        assert len(new_events) == 1
        assert isinstance(new_events[0], EventoInicioUnidad)
        assert new_events[0].datos['activado_por_ciclo'] is True

    def test_procesar_dependency_blocking(self, mock_engine, mock_linea_temporal):
        task_id = "task_2"
        mock_linea_temporal.dependency_index = 0
        mock_engine.lineas_temporales[task_id] = mock_linea_temporal
        mock_linea_temporal.unidades_finalizadas_total = 1
        
        mock_engine.tarea_id_a_indice = {task_id: 1, "pred_task": 0}
        mock_engine.indice_a_tarea_id = {0: "pred_task"}
        mock_engine.production_flow = [
            {}, 
            {'previous_task_index': 0, 'min_predecessor_units': 1}
        ]
        
        mock_pred = MagicMock(spec=["unidades_finalizadas_total"])
        mock_pred.unidades_finalizadas_total = 0 
        mock_engine.lineas_temporales["pred_task"] = mock_pred

        event = EventoFinUnidad(
            timestamp=datetime(2023, 1, 1, 10, 0),
            datos={'tarea_id': task_id, 'numero_unidad': 1, 'id_instancia': 'inst_1'}
        )

        new_events = event.procesar(mock_engine)
        assert not any(isinstance(e, EventoInicioUnidad) for e in new_events)

    def test_registrar_inactividad_con_espera_larga(self, mock_engine, mock_linea_temporal):
        # Assert using ConcreteMockEngine
        assert isinstance(mock_engine, ConcreteMockEngine)
        
        task_id = "task_2"
        pred_id = "task_1"
        mock_linea_temporal.dependency_index = 0
        mock_engine.lineas_temporales[task_id] = mock_linea_temporal
        mock_linea_temporal.unidades_finalizadas_total = 1
        
        mock_pred = MagicMock(spec=["name", "unidades_finalizadas_total"])
        mock_pred.name = "Predecessor"
        mock_pred.unidades_finalizadas_total = 0 # Fixed attribute name
        mock_engine.lineas_temporales[pred_id] = mock_pred
        
        mock_engine.tarea_id_a_indice = {task_id: 1, pred_id: 0}
        mock_engine.indice_a_tarea_id = {0: pred_id}
        mock_engine.production_flow = [{}, {'previous_task_index': 0}]
        
        future_time = datetime(2023, 1, 1, 8, 10)
        mock_event_obj = ComparableEvent(
            tipo_evento="FIN_BLOQUE_TRABAJO",
            datos={"tarea_id": pred_id, "numero_unidad": 1},
        )
        
        mock_engine.eventos_futuros = [(future_time, 2, mock_event_obj)]
        
        # Verify types before processing
        assert isinstance(mock_engine.eventos_futuros, list)
        assert isinstance(mock_engine.eventos_futuros[0][0], datetime)

        event = EventoFinUnidad(
            timestamp=datetime(2023, 1, 1, 8, 0),
            datos={'tarea_id': task_id, 'numero_unidad': 1, 'id_instancia': 'inst_1'}
        )

        event.procesar(mock_engine)
        assert len(mock_engine.audit_log_interno) > 0
        assert mock_engine.audit_log_interno[-1].decision_type == 'TIEMPO_INACTIVO'

    def test_registrar_inactividad_con_espera_corta(self, mock_engine, mock_linea_temporal):
        task_id = "task_2"
        mock_linea_temporal.dependency_index = 0
        mock_engine.lineas_temporales[task_id] = mock_linea_temporal
        mock_engine.lineas_temporales["pred_task"] = MagicMock(spec=["unidades_finalizadas_total"])
        mock_engine.indice_a_tarea_id = {0: "pred_task"}
        
        future_time = datetime(2023, 1, 1, 8, 2)
        mock_engine.eventos_futuros = [
            (
                future_time,
                2,
                ComparableEvent(
                    tipo_evento="FIN_BLOQUE_TRABAJO",
                    datos={"tarea_id": "pred_task", "numero_unidad": 1},
                ),
            )
        ]

        event = EventoFinUnidad(
            timestamp=datetime(2023, 1, 1, 8, 0),
            datos={'tarea_id': task_id, 'numero_unidad': 1, 'id_instancia': 'inst_1'}
        )
        
        event.procesar(mock_engine)
        inactivity_logs = [x for x in mock_engine.audit_log_interno if x.decision_type == 'TIEMPO_INACTIVO']
        assert len(inactivity_logs) == 0

    def test_registrar_inactividad_sin_evento_futuro(self, mock_engine, mock_linea_temporal):
        task_id = "task_2"
        mock_linea_temporal.dependency_index = 0
        mock_engine.lineas_temporales[task_id] = mock_linea_temporal
        mock_engine.lineas_temporales["pred_task"] = MagicMock(spec=["unidades_finalizadas_total"])
        mock_engine.indice_a_tarea_id = {0: "pred_task"}
        
        mock_engine.eventos_futuros = []

        event = EventoFinUnidad(
            timestamp=datetime(2023, 1, 1, 8, 0),
            datos={'tarea_id': task_id, 'numero_unidad': 1, 'id_instancia': 'inst_1'}
        )
        
        event.procesar(mock_engine)
        assert len(mock_engine.audit_log_interno) == 0


    def test_procesar_cyclic_logic_not_complete(self, mock_engine, mock_linea_temporal):
        task_id = "task_1"
        mock_engine.lineas_temporales[task_id] = mock_linea_temporal
        mock_linea_temporal.completar_unidad_instancia.return_value = {
            'tarea_completada': False, # Critical for hitting Priority 4
            'trabajadores_liberados': ['Worker A']
        }
        
        mock_engine.tarea_id_a_indice = {task_id: 0, "task_cyclic": 1}
        mock_engine.indice_a_tarea_id = {1: "task_cyclic"}
        mock_engine.production_flow = [
            {'units_per_cycle': 1, 'next_cyclic_task_index': 1}, 
            {}
        ]
        
        mock_target = MagicMock(spec=["unidades_finalizadas_total", "unidades_a_producir", "iniciar_instancia_inicial"])
        mock_target.unidades_finalizadas_total = 0
        mock_target.unidades_a_producir = 10
        mock_target.iniciar_instancia_inicial.return_value = "inst_cyclic"
        mock_engine.lineas_temporales["task_cyclic"] = mock_target

        event = EventoFinUnidad(
            timestamp=datetime(2023, 1, 1, 18, 0),
            datos={'tarea_id': task_id, 'numero_unidad': 1, 'id_instancia': 'inst_1'}
        )

        new_events = event.procesar(mock_engine)
        # Should generate event because cycle completed (1 % 1 == 0)
        assert len(new_events) == 1
        assert isinstance(new_events[0], EventoInicioUnidad)
        assert new_events[0].datos['activado_por_ciclo'] is True

    def test_procesar_reasignment_edge_cases(self, mock_engine, mock_linea_temporal):
        # Test malformed config
        task_id = "task_1"
        mock_engine.lineas_temporales[task_id] = mock_linea_temporal
        mock_linea_temporal.completar_unidad_instancia.return_value = {
            'tarea_completada': True,
            'trabajadores_liberados': ['Worker A']
        }
        
        mock_engine.tarea_id_a_indice = {task_id: 0}
        mock_engine.production_flow = [{
            'workers': [
                "not_a_dict", # Should be ignored
                {'name': 'Worker B'}, # Not in instance
                {'name': 'Worker A'}, # No rule
            ]
        }]
        
        event = EventoFinUnidad(
            timestamp=datetime(2023, 1, 1, 18, 0),
            datos={'tarea_id': task_id, 'numero_unidad': 1, 'id_instancia': 'inst_1'}
        )
        
        # Should NOT generate reassignment events
        new_events = event.procesar(mock_engine)
        reasignment_events = [e for e in new_events if isinstance(e, EventoReasignacionTrabajador)]
        assert len(reasignment_events) == 0

class TestEventoReasignacionTrabajador:
    
    @pytest.fixture
    def mock_engine(self):
        engine = MagicMock(spec=['logger', 'lineas_temporales'])
        engine.logger = MagicMock(spec=["debug", "info", "warning", "error", "critical"])
        engine.lineas_temporales = {}
        return engine

    def test_procesar_replace_mode(self, mock_engine):
        lt_source = MagicMock(spec=['trabajadores_asignados', 'name'])
        lt_source.trabajadores_asignados = ['Worker A']
        lt_source.name = "source"
        mock_engine.lineas_temporales["source"] = lt_source

        lt_target = MagicMock(spec=['trabajadores_asignados', 'name'])
        lt_target.trabajadores_asignados = []
        lt_target.name = "target"
        mock_engine.lineas_temporales["target"] = lt_target
        
        event = EventoReasignacionTrabajador(
            timestamp=datetime(2023, 1, 1, 8, 0),
            datos={
                'trabajador_id': 'Worker A',
                'tarea_origen': 'source',
                'tarea_destino': 'target',
                'mode': 'REPLACE'
            }
        )
        event.procesar(mock_engine)
        
        assert 'Worker A' not in lt_source.trabajadores_asignados
        assert 'Worker A' in lt_target.trabajadores_asignados

    def test_procesar_parallel_join_mode(self, mock_engine):
        lt_source = MagicMock(spec=['trabajadores_asignados', 'name'])
        lt_source.trabajadores_asignados = ['Worker A']
        lt_source.name = "source"
        mock_engine.lineas_temporales["source"] = lt_source

        lt_target = MagicMock(spec=['trabajadores_asignados', 'agregar_instancia_paralela', 'name'])
        lt_target.name = "target"
        mock_engine.lineas_temporales["target"] = lt_target
        lt_target.agregar_instancia_paralela.return_value = "inst_paralela"

        event = EventoReasignacionTrabajador(
            timestamp=datetime(2023, 1, 1, 8, 0),
            datos={
                'trabajador_id': 'Worker A',
                'tarea_origen': 'source',
                'tarea_destino': 'target',
                'mode': 'PARALLEL_JOIN'
            }
        )
        event.procesar(mock_engine)
        assert lt_target.agregar_instancia_paralela.call_count == 1
        lt_target.agregar_instancia_paralela.assert_called_with('Worker A', event.timestamp, mock_engine)

    def test_procesar_parallel_join_failure(self, mock_engine):
        lt_source = MagicMock(spec=['trabajadores_asignados', 'name'])
        lt_source.trabajadores_asignados = []
        lt_source.name = "source"
        mock_engine.lineas_temporales["source"] = lt_source

        lt_target = MagicMock(spec=['agregar_instancia_paralela', 'name'])
        lt_target.name = "target"
        mock_engine.lineas_temporales["target"] = lt_target
        lt_target.agregar_instancia_paralela.return_value = None

        event = EventoReasignacionTrabajador(
            timestamp=datetime(2023, 1, 1, 8, 0),
            datos={
                'trabajador_id': 'Worker A',
                'tarea_origen': 'source',
                'tarea_destino': 'target',
                'mode': 'PARALLEL_JOIN'
            }
        )
        event.procesar(mock_engine)
        assert mock_engine.logger.warning.call_count >= 1
        mock_engine.logger.warning.assert_called()



class TestEventoTiempoInactivo:
    def test_procesar(self):
        engine = MagicMock(spec=['audit_log_interno', 'logger'])
        engine.audit_log_interno = []
        engine.logger = MagicMock(spec=["debug", "info", "warning", "error"])
        event = EventoTiempoInactivo(
            timestamp=datetime.now(),
            datos={'trabajador': 'W1', 'tiempo_espera_min': 10, 'tarea_actual': 'T1'}
        )
        event.procesar(engine)
        assert len(engine.audit_log_interno) == 1
        assert engine.audit_log_interno[0].decision_type == 'TIEMPO_INACTIVO'
