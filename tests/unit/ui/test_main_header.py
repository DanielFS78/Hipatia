# -*- coding: utf-8 -*-
import pytest
from ui.widgets.main_header import MainHeader

@pytest.mark.unit
class TestMainHeader:
    """Tests unitarios para la cabecera principal."""

    @pytest.fixture
    def header(self, qtbot):
        h = MainHeader()
        qtbot.addWidget(h)
        return h

    def test_init_ui(self, header):
        """Verifica que el botón de auto-ajuste existe."""
        assert header.btn_auto_ajustar is not None

    def test_auto_adjust_signal(self, header, qtbot):
        """Verifica que al pulsar el botón se emite la señal de ajuste."""
        with qtbot.waitSignal(header.auto_adjust_requested) as blocker:
            header.btn_auto_ajustar.click()
        assert blocker.signal_triggered
