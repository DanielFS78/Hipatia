"""
Nombre del Módulo: scripts.verify_structure

Descripción: Script ejecutable (`verify_structure`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import os
import sys
from pathlib import Path

REQUIRED_DIRS = [
    "core",
    "controllers",
    "ui",
    "ui/widgets",
    "database",
    "tests",
    "config",
    "scripts"
]

REQUIRED_FILES = [
    "app.py",
    "requirements.txt",
    "mypy.ini",
    "config/config.ini",
    "core/app_model.py",
    "controllers/app_controller.py",
    "ui/main_window.py"
]

def check_structure(root_dir):
    missing_items = []
    
    # Check directories
    for d in REQUIRED_DIRS:
        path = os.path.join(root_dir, d)
        if not os.path.isdir(path):
            missing_items.append(f"MISSING DIR: {d}")
            
    # Check files
    for f in REQUIRED_FILES:
        path = os.path.join(root_dir, f)
        if not os.path.isfile(path):
            missing_items.append(f"MISSING FILE: {f}")
            
    return missing_items

def main():
    root_dir = Path(__file__).parent.parent
    print(f"Verifying project structure in: {root_dir}")
    
    missing = check_structure(root_dir)
    
    if missing:
        print("\n❌ Structural Integrity Issues Found:")
        for item in missing:
            print(f"  - {item}")
        sys.exit(1)
    else:
        print("\n✅ Project Structure Verified. All critical files and directories are present.")
        sys.exit(0)

if __name__ == "__main__":
    main()
