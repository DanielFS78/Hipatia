#!/usr/bin/env python3
"""
Script de Análisis de Conexiones de Repositorios

Analiza todas las conexiones a un repositorio específico:
- Funciones que lo utilizan
- Archivos que dependen de él
- Métodos llamados
- Mapa de dependencias
"""

import os
import re
import ast
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple


class RepositoryConnectionAnalyzer:
    """Analiza conexiones y dependencias de repositorios."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.connections: Dict[str, List[Dict]] = defaultdict(list)
        self.method_calls: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
        self.file_dependencies: Dict[str, Set[str]] = defaultdict(set)
        
        # Patrones para detectar repositorios
        self.repo_patterns = {
            'worker_repo': r'worker_repo(?:sitory)?',
            'machine_repo': r'machine_repo(?:sitory)?',
            'product_repo': r'product_repo(?:sitory)?',
            'pila_repo': r'pila_repo(?:sitory)?',
            'preproceso_repo': r'preproceso_repo(?:sitory)?',
            'tracking_repo': r'tracking_repo(?:sitory)?',
            'material_repo': r'material_repo(?:sitory)?',
        }
    
    def analyze_file(self, filepath: Path) -> Dict:
        """Analiza un archivo Python buscando usos de repositorios."""
        results = {
            'file': str(filepath.relative_to(self.project_root)),
            'repos_used': [],
            'method_calls': defaultdict(list),
            'import_style': None
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except (UnicodeDecodeError, IOError):
            return results
        
        # Buscar imports de repositorios
        import_pattern = r'from\s+database\.repositories(?:\.(\w+))?\s+import\s+([^#\n]+)'
        for match in re.finditer(import_pattern, content):
            module = match.group(1)
            imports = match.group(2)
            results['import_style'] = 'direct'
            if module:
                results['repos_used'].append(module)
        
        # Buscar patrones de uso de repositorios
        for repo_key, pattern in self.repo_patterns.items():
            # Buscar asignaciones como: self.worker_repo = ...
            assign_pattern = rf'(?:self\.)?({pattern})\s*='
            if re.search(assign_pattern, content, re.IGNORECASE):
                if repo_key not in results['repos_used']:
                    results['repos_used'].append(repo_key)
            
            # Buscar llamadas a métodos como: worker_repo.get_all_workers()
            method_pattern = rf'(?:self\.)?{pattern}\.(\w+)\s*\('
            for m in re.finditer(method_pattern, content, re.IGNORECASE):
                method_name = m.group(1)
                if method_name not in results['method_calls'][repo_key]:
                    results['method_calls'][repo_key].append(method_name)
                    
            # Buscar accesos como: repos["worker"]
            dict_pattern = rf'repos\s*\[\s*[\'"](\w+)[\'"]\s*\]'
            for m in re.finditer(dict_pattern, content):
                repo_name = m.group(1)
                mapped_key = f'{repo_name}_repo'
                if mapped_key in self.repo_patterns:
                    if mapped_key not in results['repos_used']:
                        results['repos_used'].append(mapped_key)
        
        return results
    
    def analyze_project(self) -> Dict:
        """Analiza todo el proyecto."""
        results = {
            'files_analyzed': 0,
            'repos_found': defaultdict(lambda: {
                'used_in_files': [],
                'methods_called': defaultdict(list),
                'total_usages': 0
            }),
            'dependency_map': defaultdict(set)
        }
        
        # Encontrar todos los archivos Python (excluyendo tests y __pycache__)
        for py_file in self.project_root.rglob('*.py'):
            # Excluir directorios
            if '__pycache__' in str(py_file) or '.venv' in str(py_file):
                continue
            
            # Analizar archivo
            file_results = self.analyze_file(py_file)
            results['files_analyzed'] += 1
            
            # Registrar resultados
            for repo in file_results['repos_used']:
                repo_data = results['repos_found'][repo]
                relative_path = str(py_file.relative_to(self.project_root))
                if relative_path not in repo_data['used_in_files']:
                    repo_data['used_in_files'].append(relative_path)
                    repo_data['total_usages'] += 1
                
                for method in file_results['method_calls'].get(repo, []):
                    if relative_path not in repo_data['methods_called'][method]:
                        repo_data['methods_called'][method].append(relative_path)
        
        return results
    
    def generate_report(self, results: Dict, repo_filter: str = None) -> str:
        """Genera un reporte legible."""
        lines = []
        lines.append("=" * 70)
        lines.append("ANÁLISIS DE CONEXIONES DE REPOSITORIOS")
        lines.append("=" * 70)
        lines.append(f"\nArchivos analizados: {results['files_analyzed']}")
        lines.append(f"Repositorios detectados: {len(results['repos_found'])}")
        lines.append("")
        
        repos_to_show = results['repos_found'].items()
        if repo_filter:
            repos_to_show = [(k, v) for k, v in repos_to_show if repo_filter.lower() in k.lower()]
        
        for repo_name, data in sorted(repos_to_show, key=lambda x: -x[1]['total_usages']):
            lines.append("-" * 70)
            lines.append(f"\n📦 REPOSITORIO: {repo_name}")
            lines.append(f"   Usado en {data['total_usages']} archivos")
            lines.append("")
            
            # Archivos que lo usan
            lines.append("   📁 ARCHIVOS QUE LO UTILIZAN:")
            for f in sorted(data['used_in_files']):
                # Categorizar archivo
                if 'test' in f.lower():
                    cat = "🧪 TEST"
                elif 'ui/' in f:
                    cat = "🖥️  UI"
                elif 'app.py' in f:
                    cat = "📱 APP"
                else:
                    cat = "📄 MOD"
                lines.append(f"      {cat}: {f}")
            
            # Métodos llamados
            if data['methods_called']:
                lines.append("\n   📞 MÉTODOS LLAMADOS:")
                for method, files in sorted(data['methods_called'].items()):
                    lines.append(f"      • {method}() -> llamado desde {len(files)} archivo(s)")
                    for f in files[:3]:  # Mostrar máximo 3
                        lines.append(f"         - {f}")
                    if len(files) > 3:
                        lines.append(f"         ... y {len(files) - 3} más")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def export_to_markdown(self, results: Dict, output_path: str = None) -> str:
        """Exporta los resultados a un archivo Markdown."""
        md_lines = []
        md_lines.append("# Análisis de Conexiones de Repositorios\n")
        md_lines.append(f"**Archivos analizados:** {results['files_analyzed']}")
        md_lines.append(f"**Repositorios detectados:** {len(results['repos_found'])}\n")
        
        md_lines.append("## Resumen por Repositorio\n")
        md_lines.append("| Repositorio | Archivos | Métodos Únicos |")
        md_lines.append("|-------------|----------|----------------|")
        
        for repo_name, data in sorted(results['repos_found'].items(), key=lambda x: -x[1]['total_usages']):
            methods_count = len(data['methods_called'])
            md_lines.append(f"| `{repo_name}` | {data['total_usages']} | {methods_count} |")
        
        md_lines.append("\n---\n")
        
        for repo_name, data in sorted(results['repos_found'].items(), key=lambda x: -x[1]['total_usages']):
            md_lines.append(f"## {repo_name}\n")
            
            # Archivos
            md_lines.append("### Archivos que lo utilizan\n")
            
            # Agrupar por categoría
            tests = [f for f in data['used_in_files'] if 'test' in f.lower()]
            ui_files = [f for f in data['used_in_files'] if 'ui/' in f]
            other = [f for f in data['used_in_files'] if f not in tests and f not in ui_files]
            
            if other:
                md_lines.append("**Código principal:**")
                for f in sorted(other):
                    md_lines.append(f"- `{f}`")
                md_lines.append("")
            
            if ui_files:
                md_lines.append("**Interfaz de usuario:**")
                for f in sorted(ui_files):
                    md_lines.append(f"- `{f}`")
                md_lines.append("")
            
            if tests:
                md_lines.append(f"<details>\n<summary>Tests ({len(tests)} archivos)</summary>\n")
                for f in sorted(tests):
                    md_lines.append(f"- `{f}`")
                md_lines.append("</details>\n")
            
            # Métodos
            if data['methods_called']:
                md_lines.append("### Métodos utilizados\n")
                md_lines.append("| Método | Llamadas desde |")
                md_lines.append("|--------|----------------|")
                for method, files in sorted(data['methods_called'].items()):
                    md_lines.append(f"| `{method}()` | {len(files)} archivo(s) |")
                md_lines.append("")
            
            md_lines.append("---\n")
        
        content = "\n".join(md_lines)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return content


def main():
    """Función principal."""
    # Determinar raíz del proyecto
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Filtro opcional por línea de comandos
    repo_filter = sys.argv[1] if len(sys.argv) > 1 else None
    
    print(f"\n🔍 Analizando proyecto: {project_root}")
    print("-" * 50)
    
    analyzer = RepositoryConnectionAnalyzer(str(project_root))
    results = analyzer.analyze_project()
    
    # Generar reporte en consola
    report = analyzer.generate_report(results, repo_filter)
    print(report)
    
    # Exportar a Markdown
    md_output = project_root / "Documentacion" / "repository_connections_analysis.md"
    analyzer.export_to_markdown(results, str(md_output))
    print(f"\n📄 Reporte exportado a: {md_output}")


if __name__ == "__main__":
    main()
