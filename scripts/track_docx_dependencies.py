#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para rastrear dependencias directas de 'docx' (python-docx)
y generar un informe de archivos afectados.
"""

import os
import sys
from pathlib import Path

def track_docx_dependencies(root_dir: str):
    affected_files = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Excluir carpetas no relevantes
        dirnames[:] = [d for d in dirnames if d not in ['.git', '__pycache__', 'venv', '.agents', '.gemini', 'htmlcov']]
        
        for filename in filenames:
            if not filename.endswith('.py'):
                continue
                
            filepath = os.path.join(dirpath, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    if 'import docx' in content or 'from docx' in content or "sys.modules['docx']" in content or "patch('docx" in content:
                        affected_files.append(filepath)
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
                
    return affected_files

if __name__ == '__main__':
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"Buscando acoplamiento con python-docx en: {root}")
    affected = track_docx_dependencies(root)
    
    print("\nArchivos afectados:")
    for f in affected:
        print(f" - {os.path.relpath(f, root)}")
    
    print(f"\nTotal: {len(affected)} archivos.")
