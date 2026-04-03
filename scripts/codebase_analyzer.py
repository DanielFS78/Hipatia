"""
Script ejecutable (`codebase_analyzer`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import os
import ast
import json
import sys

def is_ignored(path):
    ignored_dirs = ['.git', '__pycache__', 'venv', 'env', '.pytest_cache', '.venv', '.agents', '.gemini', 'tests', 'test_', '.tox', '.mypy_cache']
    for d in ignored_dirs:
        if f"/{d}/" in path or path.endswith(f"/{d}") or path.startswith(f"{d}/"):
            return True
    return False

def analyze_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {"error": str(e)}

    lines = content.split('\n')
    loc = len(lines)
    
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return {"error": f"SyntaxError: {e}"}

    class_defs = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    func_defs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    
    # Indicadores de deuda técnica
    print_calls = 0
    bare_excepts = 0
    missing_type_hints_funcs = 0
    total_funcs = len(func_defs)
    
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'print':
            print_calls += 1
        elif isinstance(n, ast.ExceptHandler):
            if n.type is None:
                bare_excepts += 1
                
    for func in func_defs:
        has_any_hint = (
            func.returns is not None
            or any(
                arg.annotation is not None
                for arg in func.args.args
                if arg.arg not in ['self', 'cls']
            )
        )
        if not has_any_hint and (len(func.args.args) > 0 or func.returns is None):
            missing_type_hints_funcs += 1

    large_classes = []
    for c in class_defs:
        methods = [n for n in c.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if c.end_lineno is not None:
            c_lines = c.end_lineno - c.lineno
            if c_lines > 250 or len(methods) > 10:
                large_classes.append({'name': c.name, 'lines': c_lines, 'methods': len(methods)})

    large_functions = []
    for func in func_defs:
        if func.end_lineno is not None:
            f_lines = func.end_lineno - func.lineno
            if f_lines > 40:
                large_functions.append({'name': func.name, 'lines': f_lines})

    return {
        "loc": loc,
        "classes": len(class_defs),
        "functions": total_funcs,
        "print_calls": print_calls,
        "bare_excepts": bare_excepts,
        "funcs_missing_hints": missing_type_hints_funcs,
        "large_classes": large_classes,
        "large_functions": large_functions
    }

def main(base_dir):
    results = {}
    
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.py') and not file.startswith('test_'):
                filepath = os.path.join(root, file)
                if not is_ignored(filepath):
                    res = analyze_file(filepath)
                    results[filepath] = res
                    
    # Analysis summary
    monolithic_files = []
    legacy_files = []
    total_loc = 0
    total_files = 0
    
    for filepath, res in results.items():
        if "error" in res:
            continue
        total_files += 1
        total_loc += res["loc"]
        
        is_monolithic = res["loc"] > 400 or len(res["large_classes"]) > 0 or len(res["large_functions"]) > 3
        if is_monolithic:
            monolithic_files.append((filepath, res))
            
        legacy_score = res["print_calls"] + (res["bare_excepts"] * 5)
        if res["functions"] > 0:
            untyped_ratio = res["funcs_missing_hints"] / res["functions"]
        else:
            untyped_ratio = 0
            
        if legacy_score > 5 or untyped_ratio > 0.7:
            legacy_files.append((filepath, res, untyped_ratio))

    monolithic_files.sort(key=lambda x: x[1]["loc"], reverse=True)
    legacy_files.sort(key=lambda x: x[1]["loc"], reverse=True)
    
    # Strip base_dir from paths for cleaner output
    def clean_path(p):
        return p.replace(base_dir, "").lstrip("/")

    report = {
        "summary": {
            "total_files": total_files,
            "total_loc": total_loc,
        },
        "monolithic_files": [
            {
                "file": clean_path(f[0]), 
                "loc": f[1]["loc"], 
                "large_classes": f[1]["large_classes"], 
                "large_functions": len(f[1]["large_functions"])
            } for f in monolithic_files
        ],
        "legacy_files": [
            {
                "file": clean_path(f[0]), 
                "loc": f[1]["loc"], 
                "prints": f[1]["print_calls"], 
                "bare_excepts": f[1]["bare_excepts"],
                "untyped_ratio": f[2]
            } for f in legacy_files
        ]
    }
    
    out_path = os.path.join(base_dir, "codebase_audit_report.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Analysis complete. Total files: {total_files}, Total LOC: {total_loc}")
    print(f"Found {len(monolithic_files)} monolithic files and {len(legacy_files)} files with technical-debt indicators.")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
