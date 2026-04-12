"""
Nombre del Módulo: scripts.generate_comprehensive_report

Descripción: Script ejecutable (`generate_comprehensive_report`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Import our other scripts
# Add parent dir to path to import scripts if needed, but we'll run them as subprocesses to be safe
# and capture output independently.

def run_script(script_name):
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=False
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def run_mypy(root_dir):
    try:
        # Run mypy on core/ only for now as per plan, or full project?
        # Let's run on 'core' as a sample since full run might be huge output
        result = subprocess.run(
            [sys.executable, "-m", "mypy", "core"],
            cwd=root_dir,
            capture_output=True,
            text=True,
            check=False
        )
        return result.stdout, result.returncode
    except Exception as e:
        return str(e), 1

def generate_report():
    root_dir = Path(__file__).parent.parent
    report_lines = []
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_lines.append(f"# Project Health Report - {timestamp}\n")
    
    # 1. Structure Check
    print("Running Structure Check...")
    out, err, code = run_script("verify_structure.py")
    report_lines.append("## 1. Structural Integrity")
    if code == 0:
        report_lines.append("✅ **PASSED**: All critical files and directories are present.")
    else:
        report_lines.append("❌ **FAILED**")
        report_lines.append("```")
        report_lines.append(out)
        report_lines.append(err)
        report_lines.append("```")
    
    # 2. Typing Coverage
    print("Running Typing Coverage Analysis...")
    out, _, _ = run_script("check_typing_coverage.py")
    report_lines.append("\n## 2. Typing Coverage Statistics")
    # Parse output to look for "Coverage: XX%"
    coverage_line = next((line for line in out.splitlines() if "Coverage:" in line), "Coverage: Unknown")
    report_lines.append(f"**Current Status:** {coverage_line}")
    report_lines.append("```")
    report_lines.append(out)
    report_lines.append("```")
    
    # 3. Mypy Strictness Check (Core)
    print("Running Mypy on core/...")
    out, code = run_mypy(root_dir)
    report_lines.append("\n## 3. Strict Type Check (Mypy - Core module)")
    if code == 0:
        report_lines.append("✅ **PASSED**: No type errors found in `core/` module.")
    else:
        report_lines.append(f"⚠️ **ISSUES FOUND**: Mypy reported errors (Exit code {code}).")
        report_lines.append("Summary of errors (first 20 lines):")
        report_lines.append("```")
        report_lines.append("\n".join(out.splitlines()[:20]))
        if len(out.splitlines()) > 20:
            report_lines.append(f"... (+ {len(out.splitlines()) - 20} more lines)")
        report_lines.append("```")

    # Write report to file
    report_path = os.path.join(root_dir, "PROJECT_HEALTH_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"\nReport generated at: {report_path}")
    print("\n" + "\n".join(report_lines))

if __name__ == "__main__":
    generate_report()
