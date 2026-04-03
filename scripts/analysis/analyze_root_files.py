#!/usr/bin/env python3
"""
Script de Análisis de Archivos Raíz
===================================
Analiza los scripts Python en la raíz del proyecto para determinar:
1. Qué definen (Clases, Funciones).
2. De qué dependen (Imports).
3. Dónde se usan (Referencias en el resto del proyecto).

Ayuda a decidir si moverlos a `core/`, `ui/`, `tools/` o eliminarlos.
"""

import ast
import os
import re
from pathlib import Path
from collections import defaultdict
import json
from typing import TypedDict

# Configuración
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_FILES_TO_ANALYZE = [
    "backup_database.py",
    "calculation_audit.py",
    "calendar_helper.py",
    "check_local_users.py",
    "constants.py",
    "debug_fabricaciones.py",
    "debug_settings_widget.py",
    "detectar_todas_camaras.py",
    "event_engine.py",
    "generate_nomenclature.py",
    "importer.py",
    "pila_serializer.py",
    "qr_generator.py",
    "report_strategy.py",
    "reset_admin.py",
    "resource_manager.py",
    "schedule_config.py",
    "simulation_engine.py",
    "simulation_events.py",
    "temporal_storage.py",
    "time_calculator.py",
    "timeline_task.py",
    "utils.py",
    "verify_postgres_connection.py",
    "visualization_generator.py"
]

SEARCH_DIRS = [
    BASE_DIR / "core",
    BASE_DIR / "ui",
    BASE_DIR / "controllers",
    BASE_DIR / "database",
    BASE_DIR / "tests",
    BASE_DIR / "app.py"
]

class DefinitionsDict(TypedDict):
    classes: list[str]
    functions: list[str]


class DefinitionsPayload(TypedDict):
    definitions: DefinitionsDict
    imports: list[str]


class ErrorPayload(TypedDict):
    error: str


class MissingResult(TypedDict):
    status: str


class RootFileAnalysis(TypedDict):
    definitions: DefinitionsDict
    imports_count: int
    usages_count: int
    usages_files: list[str]


Payload = DefinitionsPayload | ErrorPayload
ResultValue = RootFileAnalysis | MissingResult


def get_definitions_and_imports(file_path: Path) -> Payload:
    """Extrae clases, funciones e imports de un archivo."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except Exception as e:
        return {"error": str(e)}

    definitions: DefinitionsDict = {"classes": [], "functions": []}
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            definitions["classes"].append(node.name)
        elif isinstance(node, ast.FunctionDef):
            # Solo funciones de nivel superior
            if not isinstance(getattr(node, 'parent', None), ast.ClassDef):
                 definitions["functions"].append(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for n in node.names:
                    imports.append(n.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for n in node.names:
                    imports.append(f"{module}.{n.name}")

    return {"definitions": definitions, "imports": imports}

def find_usages(file_name: str, search_dirs: list[Path]) -> list[str]:
    """Busca ocurrencias del nombre del módulo o sus definiciones en el proyecto."""
    module_name = file_name.replace(".py", "")
    usages = []
    
    # Patrones a buscar: "import module_name", "from module_name", "module_name."
    patterns = [
        re.compile(rf"\bimport\s+{module_name}\b"),
        re.compile(rf"\bfrom\s+{module_name}\b"),
        # re.compile(rf"\b{module_name}\.") # Puede dar muchos falsos positivos si el nombre es común
    ]

    for search_path in search_dirs:
        path_obj = Path(search_path)
        if path_obj.is_file():
            files: list[Path] = [path_obj]
        else:
            files = list(path_obj.rglob("*.py"))

        for file_path in files:
            if file_path.name == file_name: 
                continue # No contarse a sí mismo
            
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    for pattern in patterns:
                        if pattern.search(content):
                            rel_path = str(file_path.relative_to(BASE_DIR))
                            usages.append(rel_path)
                            break # Encontrado en este archivo, pasar al siguiente
            except Exception:
                continue
                
    return usages

def main():
    print(f"Analizando {len(ROOT_FILES_TO_ANALYZE)} archivos en la raíz...\n")
    
    results: dict[str, ResultValue] = {}
    
    for file_name in ROOT_FILES_TO_ANALYZE:
        file_path = BASE_DIR / file_name
        if not file_path.exists():
            results[file_name] = {"status": "MISSING"}
            continue
            
        # 1. Analizar contenido
        content_info = get_definitions_and_imports(file_path)

        if "error" in content_info:
            definitions_info: DefinitionsDict = {"classes": [], "functions": []}
            imports_list: list[str] = []
        else:
            definitions_info = content_info["definitions"]
            imports_list = content_info["imports"]
        
        # 2. Analizar uso
        usages = find_usages(file_name, SEARCH_DIRS)
        
        results[file_name] = {
            "definitions": definitions_info,
            "imports_count": len(imports_list),
            "usages_count": len(usages),
            "usages_files": usages[:5],  # Mostrar primeros 5
        }

    # Imprimir reporte Markdown
    print("| Archivo | Clases/Func | Imports | Usado En (Cant) | Sugerencia |")
    print("|---|---|---|---|---|")
    
    for file_name, data in sorted(results.items()):
        if "status" in data:
            continue
            
        defs = len(data["definitions"]["classes"]) + len(data["definitions"]["functions"])
        imports = data["imports_count"]
        usages_count = data["usages_count"]
        
        # Heurística simple para sugerencia
        suggestion = "???"
        if usages_count == 0:
            suggestion = "🗑️ ELIMINAR / ARCHIVAR"
        elif "tests" in str(data["usages_files"]):
            suggestion = "🧪 MOVER A TESTS / TOOLS"
        elif "debug" in file_name or "check" in file_name or "verify" in file_name:
            suggestion = "🛠️ MOVER A SCRIPTS/TOOLS"
        elif "utils" in file_name or "helper" in file_name:
             suggestion = "📦 MOVER A CORE/UTILS"
        else:
            suggestion = "📦 MOVER A CORE/ O UI/"

        print(f"| `{file_name}` | {defs} | {imports} | {usages_count} | {suggestion} |")

    # Detalle JSON para análisis profundo
    # print("\n--- DETALLE JSON ---")
    # print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
