# -*- coding: utf-8 -*-
"""
Nombre del Módulo: generate_ui_report

Descripción: Convierte el JSON generado por ``analyze_ui`` en un informe Markdown de la interfaz Hipatia.
"""

import json
import os
from datetime import datetime
from typing import Any

def generate_markdown(json_path: str, output_path: str):
    """
    Lee un informe JSON de análisis de UI y genera un documento Markdown estructurado.
    Args:
        json_path: Ruta al archivo JSON generado por analyze_ui.py.
        output_path: Ruta donde se guardará el informe Markdown resultante.
    """
    if not os.path.exists(json_path):
        print(f"Error: No se encontró el archivo JSON en {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Frases que queremos ignorar completamente para evitar ruido visual
    frases_ignoradas = [
        "",
        "None",
        "Sin descripción disponible",
        "Sin descripción disponible.",
        "None."
    ]

    md_content = f"""# Documentación de Interfaz de Usuario: Hipatia

> **Generado el:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> **Autor de la documentación:** Antigravity (IA)

## 📸 Visión General (Área UI)

### Propósito de este Informe
Este documento se centra en la auditoría y documentación de la capa visual de Hipatia, cubriendo widgets y diálogos críticos para la simulación y trazabilidad.

### Arquitectura UI
La interfaz está construida con **PyQt6**, siguiendo patrones de desacoplamiento para permitir el testeo de la lógica de presentación independientemente de los widgets de Qt.

---
"""

    # --- 1. Generación de Índice por Carpetas ---
    files_by_dir: dict[str, list[dict[str, Any]]] = {}
    for item in data:
        filepath = item.get('file', 'Unknown')
        parts = filepath.split('/')
        # Agrupamos por subcapeta de ui/
        if 'ui/' in filepath:
            rel_ui = filepath.split('ui/')[1]
            dir_name = rel_ui.split('/')[0] if '/' in rel_ui else "Raíz UI"
        else:
            dir_name = "Otros"
        
        if dir_name not in files_by_dir:
            files_by_dir[dir_name] = []
        if isinstance(item, dict):
            files_by_dir[dir_name].append(item)

    md_content += "## 📑 Índice de Componentes UI\n\n"
    
    for dir_name, items in sorted(files_by_dir.items()):
        folder_title = f"Componentes en: {dir_name}"
        md_content += f"### 📂 {folder_title}\n"
        for item in sorted(items, key=lambda x: x.get('file', '')):
            filepath = item.get('file', 'Unknown')
            anchor = filepath.replace('/', '').replace('.', '').replace('_', '').lower()
            md_content += f"  - [{filepath}](#{anchor})\n"

    md_content += "\n<div style='page-break-after: always;'></div>\n\n"

    # --- 2. Generación Detallada de Archivos (CON FILTRO DE RUIDO) ---
    for dir_name, items in sorted(files_by_dir.items()):
        folder_title = f"Detalles de UI: {dir_name}"
        md_content += f"# {folder_title}\n\n"

        for item in sorted(items, key=lambda x: x.get('file', '')):
            filepath = item.get('file', 'Unknown')
            anchor = filepath.replace('/', '').replace('.', '').replace('_', '').lower()
            
            # --- FILTRO 1: ¿El módulo entero está vacío de documentación? ---
            module_desc = item.get('module_docstring', '').strip()
            
            tiene_clases_validas = False
            for cls in item.get('classes', []):
                cls_doc = cls.get('docstring', '').strip()
                if cls_doc and cls_doc not in frases_ignoradas:
                    tiene_clases_validas = True
                    break
                for m in cls.get('methods', []):
                    m_doc = m.get('docstring', '').strip()
                    if m_doc and m_doc not in frases_ignoradas:
                        tiene_clases_validas = True
                        break
            
            if not tiene_clases_validas:
                functions = item.get('functions', [])
                for func in functions:
                    f_doc = func.get('docstring', '').strip()
                    if f_doc and f_doc not in frases_ignoradas:
                        tiene_clases_validas = True
                        break
                        
            if (not module_desc or module_desc in frases_ignoradas) and not tiene_clases_validas:
                continue

            md_content += f"## <a name='{anchor}'></a> 📄 {filepath}\n\n"

            if module_desc and module_desc not in frases_ignoradas:
                md_content += f"### Descripción General\n{module_desc}\n\n"

            classes = item.get('classes', [])
            if classes:
                hay_clases_impresas = False
                clases_content = "### Clases\n\n"
                
                for cls in classes:
                    cls_name = cls.get('name', 'Unknown')
                    cls_doc = cls.get('docstring', '').strip()
                    is_class_doc_valid = cls_doc and cls_doc not in frases_ignoradas
                    
                    metodos_validos = []
                    for method in cls.get('methods', []):
                        m_doc = method.get('docstring', '').strip()
                        m_name = method.get('name', '')
                        if not m_doc or m_doc in frases_ignoradas:
                            continue
                        if m_name == '__init__' and len(m_doc) < 15:
                            continue
                        metodos_validos.append(method)

                    if not is_class_doc_valid and not metodos_validos:
                        continue
                        
                    hay_clases_impresas = True
                    clases_content += f"#### 🏛 Clase: `{cls_name}`\n"
                    if is_class_doc_valid:
                        clases_content += f"{cls_doc}\n\n"
                    if metodos_validos:
                        clases_content += "**Métodos:**\n"
                        for m in metodos_validos:
                            m_doc_clean = m.get('docstring', '').strip().replace('\n', ' ')
                            clases_content += f"- `{m.get('name')}`: {m_doc_clean}\n"
                    clases_content += "\n"
                    
                if hay_clases_impresas:
                    md_content += clases_content

            functions = item.get('functions', [])
            if functions:
                funciones_validas = []
                for func in functions:
                    f_doc = func.get('docstring', '').strip()
                    if f_doc and f_doc not in frases_ignoradas:
                        funciones_validas.append(func)
                
                if funciones_validas:
                    md_content += "### Funciones Globales\n\n"
                    for func in funciones_validas:
                        f_doc_clean = func.get('docstring', '').strip().replace('\n', ' ')
                        md_content += f"- 🔧 `{func.get('name')}`: {f_doc_clean}\n"
                    md_content += "\n"

            md_content += "---\n\n"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f"✅ Documentación generada con éxito y libre de ruido en: {output_path}")

if __name__ == "__main__":
    # Asegurar que el directorio de salida existe
    os.makedirs("Documentacion/Refactorización UI", exist_ok=True)
    generate_markdown('ui_analysis_report.json', 'Documentacion/Refactorización UI/Analisis_y_Plan_Refactorizacion.md')
