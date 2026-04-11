
"""
Nombre del Módulo: scripts.generate_coverage_report

Descripción: Script ejecutable (`generate_coverage_report`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import json
import subprocess
import sys
import os
from collections import defaultdict
from typing import List, Dict, Any

def run_coverage():
    """Runs pytest with coverage json report."""
    print("Running pytest with coverage... (this may take a moment)")
    # Run coverage for the whole project, excluding tests folder from the coverage report itself
    # We want to see coverage OF the code, not OF the tests.
    cmd = [
        "pytest",
        "--cov=.",
        "--cov-report=json:coverage.json",
        "--cov-config=.coveragerc"  # Optional if we create one, but defaults are usually okay
    ]
    
    # We create a temporary .coveragerc to exclude tests from coverage calculation if it doesn't exist
    if not os.path.exists(".coveragerc"):
        with open(".coveragerc", "w") as f:
            f.write("[run]\nomit = \n    tests/*\n    scripts/*\n")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and result.returncode != 1: # 1 can mean test failures, but coverage still gen
        print("Error running pytest:")
        print(result.stderr)
        return False
    return True

def load_coverage_data():
    """Loads coverage.json."""
    if not os.path.exists("coverage.json"):
        print("coverage.json not found!")
        return None
    with open("coverage.json", "r") as f:
        return json.load(f)

def get_category(filename: str) -> str:
    """Determines category based on filename."""
    if filename.startswith("controllers/"):
        return "Controllers"
    elif filename.startswith("core/"):
        return "Core & Services"
    elif filename.startswith("database/"):
        return "Database"
    elif filename.startswith("ui/"):
        return "UI & Widgets"
    elif filename.startswith("tests/"):
        return "Tests"
    elif filename.startswith("scripts/"):
        return "Scripts"
    else:
        return "Root / Misc"

def format_missing_lines(lines: List[int]) -> str:
    """Formats a list of missing lines into ranges (e.g. '1-5, 8, 10-12')."""
    if not lines:
        return ""
    
    ranges = []
    lines.sort()
    start = lines[0]
    end = lines[0]
    
    for i in range(1, len(lines)):
        if lines[i] == end + 1:
            end = lines[i]
        else:
            if start == end:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{end}")
            start = lines[i]
            end = lines[i]
    
    if start == end:
        ranges.append(str(start))
    else:
        ranges.append(f"{start}-{end}")
        
    return ", ".join(ranges)

def print_report(data: Dict[str, Any]):
    """Prints the categorized report."""
    files = data.get("files", {})
    
    categorized = defaultdict(list)
    total_statements = 0
    total_covered = 0
    
    for filename, stats in files.items():
        # Skip site-packages or other external files if they sneaked in
        if not filename.endswith(".py"):
            continue
            
        category = get_category(filename)
        summary = stats["summary"]
        
        stmts = summary["num_statements"]
        covered = summary["covered_lines"]
        missing = summary["missing_lines"]
        percent = (covered / stmts * 100) if stmts > 0 else 100.0
        
        file_data = {
            "name": filename,
            "stmts": stmts,
            "covered": covered,
            "percent": percent,
            "missing_lines": stats["missing_lines"] # List of ints
        }
        
        categorized[category].append(file_data)
        
        # Global stats (excluding tests/scripts if desired, but let's keep all valid code)
        if category not in ["Tests", "Scripts"]:
            total_statements += stmts
            total_covered += covered

    # Define strict order
    order = ["Controllers", "Core & Services", "Database", "UI & Widgets", "Root / Misc"]
    
    print("\n" + "="*100)
    print(f"{'FILE / COMPONENT':<60} | {'STMTS':<6} | {'MISS':<5} | {'COVER':<6} | {'MISSING RANGES'}")
    print("="*100)
    
    for category in order:
        files_list = categorized.get(category, [])
        if not files_list:
            continue
            
        # Sort by name
        files_list.sort(key=lambda x: x["name"])
        
        # Category Header
        cat_stmts = sum(f["stmts"] for f in files_list)
        cat_covered = sum(f["covered"] for f in files_list)
        cat_percent = (cat_covered / cat_stmts * 100) if cat_stmts > 0 else 100.0
        
        print(f"\n📂 {category.upper()}  ({cat_percent:.1f}%)")
        print("-" * 100)
        
        for f in files_list:
            missing_fmt = format_missing_lines(f["missing_lines"])
            # Truncate missing lines if too long
            if len(missing_fmt) > 30:
                missing_fmt = missing_fmt[:27] + "..."
                
            color_code = ""
            if f["percent"] < 50:
                color_code = "🔴 "
            elif f["percent"] < 80:
                color_code = "🟡 "
            else:
                color_code = "🟢 "
                
            print(f"{color_code}{f['name']:<57} | {f['stmts']:<6} | {f['stmts']-f['covered']:<5} | {f['percent']:>5.1f}% | {missing_fmt}")

    print("\n" + "="*100)
    global_percent = (total_covered / total_statements * 100) if total_statements > 0 else 100.0
    print(f"🌍 GLOBAL CODE COVERAGE: {global_percent:.2f}%  ({total_covered}/{total_statements} lines)")
    print("="*100 + "\n")

if __name__ == "__main__":
    if run_coverage():
        data = load_coverage_data()
        if data:
            print_report(data)
            # cleanup
            if os.path.exists("coverage.json"):
                os.remove("coverage.json")
            if os.path.exists(".coveragerc"):
                os.remove(".coveragerc")
