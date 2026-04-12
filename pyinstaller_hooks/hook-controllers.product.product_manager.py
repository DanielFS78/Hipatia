# -*- coding: utf-8 -*-
"""
Hook PyInstaller para ``controllers.product.product_manager``.

``BOMImportPreviewDialog`` se resuelve con ``importlib`` (``ui_class``); sin este hook
el módulo del diálogo no entra en el bundle y el .exe falla en Windows.
"""

hiddenimports = ["ui.dialogs.product.bom_import_preview_dialog"]
