"""
Nombre del Módulo: scripts.analyze_product_controller_coverage

Descripción: Script ejecutable (`analyze_product_controller_coverage`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import ast
import json
import subprocess
import os

target_file = "controllers/product_controller_v2.py"
test_file = "tests/unit/test_product_controller_v2_comprehensive.py"
cov_json = "coverage.json"

def get_methods_info(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=filepath)
    
    methods = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'ProductController':
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    start = item.lineno
                    end = item.end_lineno if item.end_lineno is not None else start
                    methods[item.name] = {
                        'start': start,
                        'end': end,
                        'lines': list(range(start, end + 1)),
                    }
    return methods

def run_coverage():
    print("Ejecutando tests para recolectar cobertura...")
    cmd = [
        "pytest",
        "tests/unit/test_product_controller_v2_comprehensive.py",
        f"--cov=controllers.product_controller_v2",
        "--cov-report=json"
    ]
    subprocess.run(cmd, capture_output=True)

def analyze_coverage(methods):
    if not os.path.exists(cov_json):
        print("No se encontró coverage.json")
        return

    with open(cov_json, 'r') as f:
        data = json.load(f)
    
    file_cov = data.get('files', {}).get(target_file, {})
    executed_lines = set(file_cov.get('executed_lines', []))
    missing_lines = set(file_cov.get('missing_lines', []))
    
    report = ["# Reporte Detallado de Cobertura por Método\n"]
    
    for method, info in methods.items():
        m_lines = set(info['lines'])
        
        # Filtramos lineas que realmente son ejecutables segun coverage
        executable = m_lines.intersection(executed_lines.union(missing_lines))
        if not executable:
            continue
            
        m_exec = m_lines.intersection(executed_lines)
        m_miss = m_lines.intersection(missing_lines)
        
        total = len(executable)
        cov_pct = (len(m_exec) / total) * 100 if total > 0 else 0
        
        status = "✅ 100%" if cov_pct == 100 else f"❌ {cov_pct:.1f}%"
        
        report.append(f"### `{method}`: {status}")
        report.append(f"- Líneas Totales Ejecutables: {total}")
        report.append(f"- Faltantes: {len(m_miss)}\n")
        if m_miss:
            miss_str = ", ".join(map(str, sorted(m_miss)))
            report.append(f"  - **Líneas sin testear:** {miss_str}\n")
            
    with open("analysis_report.md", "w") as f:
        f.write("\n".join(report))
        
    print("Análisis guardado en analysis_report.md")

if __name__ == "__main__":
    methods = get_methods_info(target_file)
    run_coverage()
    analyze_coverage(methods)
