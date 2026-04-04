# -*- coding: utf-8 -*-
"""RBAC: HistorialReportManager exige GENERATE_REPORTS para exportar PDF."""
from unittest.mock import MagicMock

import pytest

from controllers.historial.report_manager import HistorialReportManager
from core.security.access_control import set_security_service
from core.security.security_service import SecurityService

pytestmark = pytest.mark.unit


def test_on_print_report_clicked_permission_denied() -> None:
    mock_ss = MagicMock(spec=SecurityService)
    mock_ss.has_permission.return_value = False
    set_security_service(mock_ss)
    try:
        view = MagicMock(spec=["pages", "show_message"])
        view.pages = {}
        mgr = HistorialReportManager(
            db=MagicMock(),
            pila_service=MagicMock(),
            worker_service=MagicMock(),
            view=view,
        )
        mgr.on_print_report_clicked()
        view.show_message.assert_called_once()
        assert view.show_message.call_args[0][0] == "Acceso Denegado"
    finally:
        set_security_service(None)
