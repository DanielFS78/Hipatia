# -*- coding: utf-8 -*-
"""
Script principal para analizar todos los archivos relevantes para la Fase 5.
Genera documentación en la carpeta code_analysis.
"""
import os
import sys
from pathlib import Path

# Añadir el directorio scripts al path
sys.path.insert(0, str(Path(__file__).parent))
from code_analyzer import analyze_file, format_markdown

# Directorio base del proyecto
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
OUTPUT_DIR = Path(__file__).parent.parent / "code_analysis"

# Archivos a analizar para la Fase 5 (módulo de Reportes)
FILES_TO_ANALYZE = [
    # Repositorios de tracking (fuente de datos)
    "database/repositories/tracking_repository.py",
    "database/repositories/base.py",
    
    # Modelos de base de datos
    "database/models.py",
    
    # DTOs de tracking
    "core/tracking_dtos.py",
    "core/dtos.py",
    
    # Widget de reportes actual (a expandir)
    "ui/widgets/reportes_widget.py",
    "ui/widgets/base.py",
    
    # Referencias de widgets similares
    "ui/widgets/workers_widget.py",
    "ui/widgets/fabrications_widget.py",
    
    # Controladores relacionados
    "controllers/app_controller.py",
    "features/worker_controller.py",
    
    # Modelo de aplicación (proxy a repositorios)
    "core/app_model.py",
    
    # Main window (para contexto de integración)
    "ui/main_window.py",
]


def main():
    # Crear directorio de salida
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("ANÁLISIS DE CÓDIGO PARA FASE 5: MÓDULO DE REPORTES")
    print("=" * 80)
    
    all_analyses = {}
    
    for relative_path in FILES_TO_ANALYZE:
        filepath = PROJECT_ROOT / relative_path
        
        if not filepath.exists():
            print(f"⚠ Archivo no encontrado: {relative_path}")
            continue
        
        print(f"✓ Analizando: {relative_path}")
        analysis = analyze_file(str(filepath))
        all_analyses[relative_path] = analysis
        
        # Generar Markdown
        markdown = format_markdown(analysis)
        
        # Guardar análisis individual
        safe_name = relative_path.replace("/", "_").replace(".py", "_analysis.md")
        output_path = OUTPUT_DIR / safe_name
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
    
    # Generar resumen consolidado
    generate_summary(all_analyses)
    
    print("\n" + "=" * 80)
    print(f"Análisis completado. Resultados en: {OUTPUT_DIR}")
    print("=" * 80)


def generate_summary(analyses: dict):
    """Genera un resumen consolidado de todos los análisis."""
    lines = [
        "# Resumen de Análisis de Código - Fase 5",
        "",
        "Este documento contiene un resumen de la estructura del código relevante",
        "para la implementación del módulo de Reportes de Producción.",
        "",
        "## Archivos Analizados",
        ""
    ]
    
    for path, analysis in analyses.items():
        lines.append(f"### `{path}`")
        
        if "error" in analysis:
            lines.append(f"> Error: {analysis['error']}")
            continue
        
        # Resumen de clases
        if analysis['classes']:
            lines.append(f"- **Clases:** {len(analysis['classes'])}")
            for cls in analysis['classes']:
                methods_count = len(cls['methods'])
                lines.append(f"  - `{cls['name']}` ({methods_count} métodos)")
        
        # Resumen de funciones
        if analysis['functions']:
            lines.append(f"- **Funciones de módulo:** {len(analysis['functions'])}")
        
        lines.append("")
    
    # Añadir guía de nomenclatura
    lines.extend([
        "## Nomenclatura Detectada",
        "",
        "### Convenciones de Nombrado",
        "- **Clases:** PascalCase (ej. `TrackingRepository`, `TrabajoLogDTO`)",
        "- **Métodos:** snake_case (ej. `obtener_estadisticas_fabricacion`)",
        "- **Variables:** snake_case (ej. `trabajo_log_id`, `fecha_inicio`)",
        "- **Constantes:** UPPER_SNAKE_CASE",
        "",
        "### Prefijos Comunes",
        "- `get_` / `obtener_`: Recuperar datos",
        "- `_map_to_*_dto`: Conversión a DTO",
        "- `iniciar_` / `finalizar_`: Acciones de flujo",
        "- `registrar_`: Creación de registros",
        ""
    ])
    
    output_path = OUTPUT_DIR / "00_resumen_analisis.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
