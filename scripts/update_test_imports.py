"""
Nombre del Módulo: scripts.update_test_imports

Descripción: Script ejecutable (`update_test_imports`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import os

target_file = "tests/unit/test_product_dialogs_coverage.py"

with open(target_file, "r") as f:
    content = f.read()

new_content = content.replace("ui.dialogs.product_dialogs", "ui.dialogs.product")

with open(target_file, "w") as f:
    f.write(new_content)

print("Updated test_product_dialogs_coverage.py")
