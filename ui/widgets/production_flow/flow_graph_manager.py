"""
Nombre del Modulo: flow_graph_manager
Descripcion: Coordina el presenter del flujo mejorado con un ``ProductionFlowCanvas``: creacion
             de tarjetas, sincronizacion de indices, efectos de ciclo/simulacion y conexiones
             logicas. Escucha ``cardMoved`` y ``cardSelected`` del canvas; ``update_connections``
             obtiene todas las aristas con ``canvas_state_all_logical_connections`` y las pinta
             en bloque, resaltando tarjetas relacionadas cuando hay tarea seleccionada.
"""

import logging
from dataclasses import asdict

from PyQt6.QtCore import QObject, QPoint, pyqtSignal, QTimer, Qt
from PyQt6.QtWidgets import QApplication, QLabel

from core.dtos import FlowTaskDataDTO
from core.flow_card_labels import flow_card_task_id_str
from core.flow_canvas_io import (
    CanvasVisualConnection,
    flow_task_config_is_cycle_end_flag,
    flow_task_config_is_cycle_start_flag,
)
from core.enhanced_flow_canvas_state_io import canvas_state_all_logical_connections
from core.flow_graph_manager_io import (
    apply_loaded_flow_step_to_presenter_config,
    canvas_task_data_canvas_unique_id,
    canvas_task_entry_set_position,
    flow_step_position_xy,
    flow_step_task_payload,
    flow_task_payload_is_cycle_start,
    flow_task_payload_set_canvas_unique_id,
    inspector_context_all_tasks_rows,
    logical_connection_edge_type,
    logical_connection_highlights,
    logical_connection_indices,
    presenter_canvas_task_effect_get,
    presenter_canvas_task_effect_set,
    presenter_task_config_mut,
    presenter_task_data_mut,
    task_data_glow_effect_clear,
    task_data_glow_effect_get,
    task_data_glow_effect_set,
    worker_entry_display_name,
)
from core.flow_inspector_context import FlowInspectorTaskContext
from ui.widgets.production_flow.flow_canvas import ProductionFlowCanvas
from ui.widgets.production_flow.flow_card_widget import FlowCardWidget
from ui.dialogs.effects import (
    GoldenGlowEffect, GreenCycleEffect,
    MixedGoldGreenEffect, SimulationProgressEffect
)
from typing import Any, Dict, cast

class FlowGraphManager(QObject):
    """
    Puente entre estado del presenter (``canvas_tasks``) y widgets en ``ProductionFlowCanvas``.

    Registra movimientos y seleccion de tarjetas, reconstruye el grafo desde datos de flujo,
    aplica efectos (madre de ciclo, simulacion) y delega el dibujo de flechas en el canvas via
    ``canvas_state_all_logical_connections`` + ``canvas.set_connections``.
    """
    
    task_selected_signal = pyqtSignal(int)  # index
    
    def __init__(self, canvas: Any, presenter: Any, workers: list[str], parent: Any = None) -> None:
        super().__init__(parent)
        self.canvas = canvas
        self.presenter = presenter
        self.workers = workers
        self.widgets: list[Any] = []  # Mapeado 1:1 con presenter.canvas_tasks
        self.simulation_effects: dict[int, Any] = {} # index -> SimulationProgressEffect
        
        self.logger = logging.getLogger("EvolucionTiemposApp.FlowGraphManager")
        
        # Label flotante para mensajes de simulación (opcional, puede estar en dialog)
        self.simulation_message_label = None

        self.canvas.cardMoved.connect(self._on_card_moved)
        self.canvas.cardSelected.connect(self._on_card_selected)

    def cleanup(self) -> None:
        """Libera recursos y rompe referencias circulares para evitar SegFaults."""
        self.clear()
        try:
            self.canvas.cardSelected.disconnect(self._on_card_selected)
        except (TypeError, RuntimeError, AttributeError):
            pass
        try:
            self.canvas.cardMoved.disconnect(self._on_card_moved)
        except (TypeError, RuntimeError, AttributeError):
            pass
        self.canvas = None
        self.presenter = None
        self.widgets = []

    # --- Gestión de Widgets ---

    def add_task_widget(
        self,
        task_data: dict[str, Any] | FlowTaskDataDTO,
        position: Any,
        restore_effects: bool = False,
    ) -> tuple[int, int]:
        """Crea un widget para una tarea y lo sincroniza con el presenter."""
        task_payload: dict[str, Any] = asdict(task_data) if isinstance(task_data, FlowTaskDataDTO) else dict(task_data)
        card = FlowCardWidget(task_payload)
        self.canvas.add_task_widget(card)
        card.move(position)
        
        # Mapeo y registro
        canvas_unique_id = id(card)
        flow_task_payload_set_canvas_unique_id(task_payload, canvas_unique_id)
        
        pos_dict = {'x': position.x(), 'y': position.y()}
        new_task, index = self.presenter.add_task(task_payload, pos_dict)
        
        self.widgets.append(card)

        if restore_effects and flow_task_payload_is_cycle_start(task_payload):
            self.apply_mother_effect(index, True)

        self.update_connections(None)
        return canvas_unique_id, index

    def update_task_config(self, index: int, key: str, value: Any, simulation_service: Any = None) -> None:
        """Actualiza la configuración de una tarea y reaplica efectos visuales."""
        if self.presenter.update_task_config(index, key, value):
            if key == 'start_condition':
                self.update_connections(index)
            elif key == "workers":
                names = [worker_entry_display_name(w) for w in value]
                if 0 <= index < len(self.widgets):
                    self.widgets[index].update_workers(names)
            elif key == 'is_cycle_start':
                self.apply_mother_effect(index, value)
                self.update_all_cycle_effects(simulation_service)
            elif key in ('is_cycle_end', 'cycle_return_to_index'):
                self.update_all_cycle_effects(simulation_service)

    def load_from_flow(self, flow_data: list[Any]) -> None:
        """Reconstruye el canvas y el estado lógico desde datos de flujo."""
        self.clear()
        # No usamos presenter.load_flow porque add_task_widget ya llama a presenter.add_task
        for step in flow_data:
            task_data = flow_step_task_payload(step)
            if not task_data:
                continue

            px, py = flow_step_position_xy(step)
            pt = QPoint(px, py)

            uid, index = self.add_task_widget(task_data, pt)

            task_entry = self.presenter.get_task(index)
            if not task_entry:
                continue
            config = presenter_task_config_mut(task_entry)
            apply_loaded_flow_step_to_presenter_config(
                config, step, self.presenter.default_units
            )

            if flow_task_config_is_cycle_start_flag(config):
                self.apply_mother_effect(index, True)

    def remove_task_widget(self, index: int) -> bool:
        """Elimina el widget y actualiza el estado lógico."""
        if 0 <= index < len(self.widgets):
            widget = self.widgets.pop(index)
            widget.deleteLater()
            self.presenter.remove_task(index)
            self.update_all_cycle_effects()
            self.update_connections(None)
            return True
        return False

    def clear(self) -> None:
        """Limpia todo el canvas y el estado."""
        for w in self.widgets:
            w.deleteLater()
        self.widgets.clear()
        if self.presenter:
            self.presenter.clear_tasks()
        self.simulation_effects.clear()

    # --- Visualización y Relaciones ---

    def select_task(self, index: int) -> None:
        """Marca visualmente una tarea como seleccionada y actualiza relaciones."""
        if not (0 <= index < len(self.widgets)):
            return

        for i, w in enumerate(self.widgets):
            w.set_selected(i == index)
            if i != index:
                w.set_highlighted(False)
        
        self.widgets[index].raise_()
        self.update_connections(index)

    def update_connections(self, selected_index: int | None = None) -> None:
        """Dibuja todas las flechas del flujo; si hay selección, resalta aristas relacionadas."""
        if not self.widgets or not self.presenter:
            self.canvas.set_connections([])
            return

        for w in self.widgets:
            w.set_highlighted(False)

        all_conns = canvas_state_all_logical_connections(self.presenter.canvas_tasks)
        visual_conns: list[CanvasVisualConnection] = []

        for conn in all_conns:
            i_from, i_to = logical_connection_indices(conn)
            if not (0 <= i_from < len(self.widgets) and 0 <= i_to < len(self.widgets)):
                continue
            from_w = self.widgets[i_from]
            to_w = self.widgets[i_to]
            visual_conns.append(
                CanvasVisualConnection(
                    start=from_w,
                    end=to_w,
                    connection_type=logical_connection_edge_type(conn),
                )
            )

        self.canvas.set_connections(visual_conns)

        if selected_index is None or not (0 <= selected_index < len(self.widgets)):
            return

        highlight_conns = self.presenter.get_logical_connections(selected_index)
        for conn in highlight_conns:
            i_from, i_to = logical_connection_indices(conn)
            if not (0 <= i_from < len(self.widgets) and 0 <= i_to < len(self.widgets)):
                continue
            from_w = self.widgets[i_from]
            to_w = self.widgets[i_to]
            hp, hc, hd, ho = logical_connection_highlights(conn)
            if hp:
                from_w.set_highlighted(True, "#e67e22")
            if hc:
                to_w.set_highlighted(True, "#2ecc71")
            if hd:
                to_w.set_highlighted(True, "#2ecc71")
            if ho:
                from_w.set_highlighted(True, "#f1c40f")

    # --- Efectos Visuales ---

    def apply_mother_effect(self, index: int, active: bool) -> None:
        """Aplica o quita el efecto de GoldenGlowEffect."""
        task = self.presenter.get_task(index)
        if not task:
            return

        card = self.widgets[index]
        data = presenter_task_data_mut(task)
        if active:
            if not task_data_glow_effect_get(data):
                task_data_glow_effect_set(data, GoldenGlowEffect(card))
        else:
            effect = task_data_glow_effect_get(data)
            if effect:
                effect.deleteLater()
                task_data_glow_effect_clear(data)

    def update_all_cycle_effects(self, simulation_service: Any = None) -> None:
        """Sincroniza todos los efectos de ciclo intermedios y finales."""
        if not simulation_service: return

        # Limpiar existentes
        for i, task in enumerate(self.presenter.canvas_tasks):
            self._remove_effect_by_key(i, 'green_cycle_effect_widget')
            self._remove_effect_by_key(i, 'mixed_effect_widget')

        # Identificar y aplicar
        last_tasks = self.presenter.identify_last_tasks_in_cycles(simulation_service)
        for idx in last_tasks:
            if not (0 <= idx < len(self.widgets)):
                continue

            entry = self.presenter.get_task(idx)
            if not entry:
                continue
            config = presenter_task_config_mut(entry)
            if flow_task_config_is_cycle_start_flag(config):
                continue

            if flow_task_config_is_cycle_end_flag(config):
                self._apply_effect_class(idx, MixedGoldGreenEffect, 'mixed_effect_widget')
            else:
                self._apply_effect_class(idx, GreenCycleEffect, 'green_cycle_effect_widget')

    def _apply_effect_class(self, index: int, effect_class: Any, key: str) -> None:
        task = self.presenter.get_task(index)
        card = self.widgets[index]
        if not presenter_canvas_task_effect_get(task, key):
            effect = effect_class(card)
            presenter_canvas_task_effect_set(task, key, effect)
            QTimer.singleShot(100, effect._update_geometry)

    def _remove_effect_by_key(self, index: int, key: str) -> None:
        task = self.presenter.get_task(index)
        effect = presenter_canvas_task_effect_get(task, key)
        if effect:
            effect.deleteLater()
            presenter_canvas_task_effect_set(task, key, None)

    # --- Simulación / Preview Effects ---

    def highlight_processing_task(self, index: int) -> None:
        """Aplica el efecto azul de simulación."""
        self.clear_simulation_effects()
        if not (0 <= index < len(self.widgets)): return
        
        card = self.widgets[index]
        self.simulation_effects[index] = SimulationProgressEffect(card)
        QApplication.processEvents()

    def clear_simulation_effects(self) -> None:
        """Limpia todos los efectos de resaltado de procesamiento."""
        for effect in self.simulation_effects.values():
            effect.deleteLater()
        self.simulation_effects.clear()

    # --- Orquestación ---

    def synchronize_positions(self) -> None:
        """Sincroniza las posiciones de los widgets con el estado del presenter."""
        for i, w in enumerate(self.widgets):
            canvas_task_entry_set_position(self.presenter.canvas_tasks[i], w.x(), w.y())

    def _on_card_selected(self, token: str | int) -> None:
        """Resuelve la tarjeta pulsada (UID de canvas o id lógico) y abre el inspector."""
        if token is None or token == "":
            return
        s = str(token).strip()
        if not s:
            return

        index: int | None = None
        try:
            uid = int(s)
            index = next(
                (
                    i
                    for i, t in enumerate(self.presenter.canvas_tasks)
                    if canvas_task_data_canvas_unique_id(t) == uid
                ),
                None,
            )
        except ValueError:
            pass

        if index is None:
            index = next(
                (
                    i
                    for i, t in enumerate(self.presenter.canvas_tasks)
                    if flow_card_task_id_str(presenter_task_data_mut(t)) == s
                ),
                None,
            )

        if index is not None:
            self.task_selected_signal.emit(index)

    def _on_card_moved(self, task_id: str, pos: Any) -> None:
        """Redibuja conexiones al mover."""
        # Se asume que el canvas ya fuerza update(), pero aquí podríamos 
        # actualizar el estado lógico si quisiéramos persistencia inmediata
        pass
    def get_task_inspector_context(self, index: int, workers_list: list[str]) -> FlowInspectorTaskContext | None:
        """Prepara el contexto tipado para el inspector de tareas."""
        task = self.presenter.get_task(index)
        if not task:
            return None

        return FlowInspectorTaskContext(
            task_canvas_id=canvas_task_data_canvas_unique_id(task),
            task_body=cast(Dict[str, Any], presenter_task_data_mut(task)),
            task_config=cast(Dict[str, Any], presenter_task_config_mut(task)),
            all_tasks_rows=inspector_context_all_tasks_rows(self.presenter.canvas_tasks),
            workers=workers_list,
        )
