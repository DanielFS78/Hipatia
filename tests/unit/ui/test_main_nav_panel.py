# -*- coding: utf-8 -*-
import pytest
from PyQt6.QtWidgets import QApplication, QMenu
from unittest.mock import MagicMock
from ui.widgets.main_nav_panel import MainNavPanel

@pytest.mark.unit
class TestMainNavPanel:
    """Tests unitarios para el panel de navegación principal."""

    @pytest.fixture
    def panel(self, qtbot):
        p = MainNavPanel()
        qtbot.addWidget(p)
        return p

    def test_init_ui(self, panel):
        """Verifica que todos los botones se han creado y registrado."""
        assert len(panel.buttons) == 8
        assert "home" in panel.buttons
        assert panel.btn_planificacion is not None
        assert not panel.btn_home.isChecked()

    def test_nav_button_emits_signal(self, panel, qtbot):
        """Verifica que al pulsar un botón se emite la señal correcta."""
        with qtbot.waitSignal(panel.page_requested) as blocker:
            panel.btn_dashboard.click()
        assert blocker.args == ["dashboard"]

    def test_planificacion_menu_emits_signal(self, panel, qtbot):
        """Verifica que las acciones del menú de planificación emiten señales."""
        # Obtenemos las acciones del menú
        menu = panel.btn_planificacion.menu()
        actions = menu.actions()
        
        # Simular activación de "Definir Plantilla de Lote"
        with qtbot.waitSignal(panel.page_requested) as blocker:
            actions[0].trigger()
        assert blocker.args == ["definir_lote"]

        # Simular activación de "Planificar Producción"
        with qtbot.waitSignal(panel.page_requested) as blocker:
            actions[1].trigger()
        assert blocker.args == ["calculate"]

    def test_update_active_button(self, panel):
        """Verifica la actualización visual del estado de los botones."""
        panel.update_active_button("reportes")
        assert panel.btn_reportes.isChecked()
        assert not panel.btn_home.isChecked()
        assert not panel.btn_planificacion.isChecked()

        # Probar caso planificación
        panel.update_active_button("calculate")
        assert panel.btn_planificacion.isChecked()
        assert not panel.btn_reportes.isChecked()

        panel.update_active_button("definir_lote")
        assert panel.btn_planificacion.isChecked()
