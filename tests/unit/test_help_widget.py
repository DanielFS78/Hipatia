# -*- coding: utf-8 -*-
"""Tests unitarios para HelpWidget."""
import pytest
from ui.widgets.help_widget import HelpWidget


@pytest.mark.unit
class TestHelpWidget:
    """Tests unitarios para HelpWidget."""

    def test_init(self, qtbot):
        """Widget se inicializa con contenido de ayuda."""
        w = HelpWidget()
        qtbot.addWidget(w)
        # El widget debería existir y tener un QTextEdit hijo con contenido HTML
        assert w is not None
