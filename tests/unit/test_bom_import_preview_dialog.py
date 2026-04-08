# -*- coding: utf-8 -*-
"""
Tests para BOMImportPreviewDialog (validación pura sin instanciar QApplication).
La sincronización DTO ↔ persistencia se cubre en ``test_bom_import_service.py``.
"""

from __future__ import annotations

import pytest

from ui.dialogs.product.bom_import_preview_dialog import BOMImportPreviewDialog
from core.import_manager.dto import BOMImportRole


pytestmark = pytest.mark.unit


class TestBOMImportPreviewDialogValidation:
    """Reglas de negocio: un único producto final y tipo obligatorio si se marca."""

    def test_requires_one_final(self) -> None:
        err = BOMImportPreviewDialog.validate_row_selections_from_states(
            [(True, BOMImportRole.SUBFABRICATION)]
        )
        assert err is not None
        assert "Producto final" in err

    def test_rejects_two_finals(self) -> None:
        err = BOMImportPreviewDialog.validate_row_selections_from_states(
            [
                (True, BOMImportRole.FINAL_PRODUCT),
                (True, BOMImportRole.FINAL_PRODUCT),
            ]
        )
        assert err is not None
        assert "Solo puede haber" in err

    def test_checked_row_must_have_role(self) -> None:
        err = BOMImportPreviewDialog.validate_row_selections_from_states([(True, None)])
        assert err is not None
        assert "tipo" in err.lower() or "Elegir" in (err or "")

    def test_valid_single_final_only(self) -> None:
        assert (
            BOMImportPreviewDialog.validate_row_selections_from_states(
                [(True, BOMImportRole.FINAL_PRODUCT)]
            )
            is None
        )

    def test_valid_final_plus_unchecked_rows(self) -> None:
        assert (
            BOMImportPreviewDialog.validate_row_selections_from_states(
                [
                    (True, BOMImportRole.FINAL_PRODUCT),
                    (False, None),
                    (False, None),
                ]
            )
            is None
        )

    def test_valid_final_with_classified_children(self) -> None:
        assert (
            BOMImportPreviewDialog.validate_row_selections_from_states(
                [
                    (True, BOMImportRole.FINAL_PRODUCT),
                    (True, BOMImportRole.SUBFABRICATION),
                    (True, BOMImportRole.COMPONENT),
                ]
            )
            is None
        )
