
"""
Nombre del Módulo: scripts.analysis.analyze_db_usage

Descripción: Script ejecutable (`analyze_db_usage`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import os
import ast
import re

OUTPUT_FILE = "Documentacion/migracion_sql/analisis_base_de_datos.md"
PROJECT_ROOT = "."

def analyze_file(filepath):
    """Analyzes a python file for DB related keywords and AST nodes."""
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            content = f.read()
            tree = ast.parse(content)
        except Exception as e:
            return None

    db_details: dict[str, list[str]] = {
        "models": [],
        "repositories": [],
        "functions": [],
        "imports": [],
        "connection_strings": []
    }

    # Check for keywords first (fast filter)
    keywords = ["sqlalchemy", "sqlite", "database", "session", "repository", "execute", "commit"]
    if not any(k in content.lower() for k in keywords):
        return None

    # AST Analysis
    for node in ast.walk(tree):
        # Find Models (Classes inheriting from Base or similar)
        if isinstance(node, ast.ClassDef):
            is_model = any(
                (isinstance(b, ast.Name) and b.id in ["Base", "Model"]) or
                (isinstance(b, ast.Attribute) and b.attr in ["Base", "Model"])
                for b in node.bases
            )
            if is_model:
                db_details["models"].append(node.name)
            
            if "Repository" in node.name:
                db_details["repositories"].append(node.name)

        # Find Functions with DB operations (heuristic)
        if isinstance(node, ast.FunctionDef):
            # Check if function code contains 'commit', 'query', 'add', 'execute'
            func_source = ast.get_source_segment(content, node)
            if func_source and any(op in func_source for op in [".commit()", ".query(", ".add(", ".execute("]):
                db_details["functions"].append(node.name)

        # Find Imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                if "sqlalchemy" in alias.name or "database" in alias.name:
                    db_details["imports"].append(alias.name)
        if isinstance(node, ast.ImportFrom):
            if node.module and ("sqlalchemy" in node.module or "database" in node.module):
                db_details["imports"].append(node.module)

    # Regex for connection strings
    if "sqlite:///" in content:
        db_details["connection_strings"].append("Generic SQLite URL found")

    return db_details

def generate_report():
    print(f"Analyzing codebase from {os.path.abspath(PROJECT_ROOT)}...")
    report_data = {}

    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Skip hidden folders and venv
        if ".git" in root or "__pycache__" in root or "venv" in root:
            continue

        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                details = analyze_file(path)
                if details and any(details.values()):
                    report_data[path] = details

    # Generate Markdown
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# Informe de Análisis de Base de Datos\n\n")
        f.write(f"**Fecha:** {os.popen('date').read().strip()}\n")
        f.write("**Objetivo:** Mapear la estructura actual de base de datos para migración a PostgreSQL.\n\n")

        f.write("## Resumen de Archivos Afectados\n")
        f.write(f"Total de archivos analizados con relevancia DB: {len(report_data)}\n\n")

        # Section 1: Models
        f.write("## 1. Modelos de Datos (SQLAlchemy)\n")
        for path, details in report_data.items():
            if details["models"]:
                f.write(f"### `{path}`\n")
                for model in details["models"]:
                    f.write(f"- 📦 Class **{model}**\n")
        
        # Section 2: Repositories
        f.write("\n## 2. Repositorios y Acceso a Datos\n")
        for path, details in report_data.items():
            if details["repositories"]:
                f.write(f"### `{path}`\n")
                for repo in details["repositories"]:
                    f.write(f"- 🗄️ Class **{repo}**\n")

        # Section 3: DB Management & Configuration
        f.write("\n## 3. Configuración y Gestión de DB\n")
        for path, details in report_data.items():
            if "database_manager" in path or details["connection_strings"]:
                f.write(f"### `{path}`\n")
                if details["connection_strings"]:
                    f.write("- ⚠️ **Cadena de conexión detectada** (Posible hardcoding)\n")
                f.write("- Funciones clave detectadas:\n")
                for func in details["functions"][:5]: # Limit so it doesn't get too long
                    f.write(f"  - `{func}`\n")

        # Section 4: All DB Interactions
        f.write("\n## 4. Detalle Completo de Interacciones\n")
        for path, details in report_data.items():
            f.write(f"<details><summary><b>{path}</b></summary>\n\n")
            if details["imports"]:
                f.write("**Imports:**\n")
                for imp in set(details["imports"]):
                    f.write(f"- `{imp}`\n")
            if details["functions"]:
                f.write("\n**Funciones con operaciones DB:**\n")
                for func in details["functions"]:
                    f.write(f"- `{func}`\n")
            f.write("</details>\n\n")

    print(f"Report generated at {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_report()
