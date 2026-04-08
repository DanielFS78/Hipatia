# -*- coding: utf-8 -*-
"""Tests unitarios para GestionDatosWidget."""
from unittest.mock import create_autospec

import pytest

from core.di_container import DIContainer
from ui.widgets.gestion_datos_widget import GestionDatosWidget
from ui.widgets.products_widget import ProductsWidget


@pytest.mark.unit
class TestGestionDatosWidget:
    """Tests unitarios para GestionDatosWidget."""

    @pytest.fixture
    def widget(self, qtbot, monkeypatch):
        """Fixture con DI simulado: las pestañas resuelven controladores vía contenedor."""
        container = create_autospec(DIContainer, instance=True)
        container.is_registered.return_value = True
        container.resolve.side_effect = lambda service_type: create_autospec(
            service_type, instance=True
        )
        monkeypatch.setattr(DIContainer, "get_instance", lambda: container)
        w = GestionDatosWidget()
        qtbot.addWidget(w)
        return w

    def test_init_creates_five_domain_tabs(self, widget):
        """Crea cinco pestañas con widgets de dominio; sin AppController."""
        assert widget.tab_widget is not None
        assert widget.tab_widget.count() == 5
        assert isinstance(widget.productos_tab, ProductsWidget)
        assert hasattr(widget.productos_tab, "search_entry")
