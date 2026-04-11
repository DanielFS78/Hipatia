"""
Nombre del Módulo: scripts.run_quality_audit

Descripción: Script ejecutable (`run_quality_audit`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

# Important paths
BASE_DIR = Path(__file__).parent.parent.resolve()
TESTS_DIR = BASE_DIR / "tests"
QA_REPORT_PATH = BASE_DIR / "QA_MASTER_REPORT.md"

def print_header(title):
    print(f"\n{'='*80}")
    print(f"🚀 {title}")
    print(f"{'='*80}\n")

def run_command(cmd, cwd=None, capture=True):
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=capture, text=True, check=False)
        return result
    except Exception as e:
        print(f"Error executing command: {cmd}\n{e}")
        return None

def analyze_mypy():
    print_header("Run Mypy Strict Type Checking")
    print("Running: mypy . (This may take a moment...)")
    # Run mypy on the whole project
    result = run_command([sys.executable, "-m", "mypy", "."], cwd=BASE_DIR)
    
    if result.returncode == 0:
        print("✅ Mypy passed successfully.")
        status = "✅ PASSED"
    else:
        print(f"⚠️ Mypy found issues (Exit code {result.returncode}).")
        stdout_lines = result.stdout.splitlines() if result.stdout else []
        status = f"⚠️ ISSUES FOUND ({len(stdout_lines)} lines of output)"
        
    return status, result.stdout if result.stdout else ""

def analyze_tests_and_coverage():
    print_header("Run Pytest & Coverage (JSON report)")
    print("Running: pytest --cov=. --cov-report=json (This will take a couple of minutes...)")
    
    # Create temp .coveragerc if needed to exclude tests
    cov_rc = BASE_DIR / ".coveragerc"
    cov_rc_created = False
    if not cov_rc.exists():
        with open(cov_rc, "w") as f:
            f.write("[run]\nomit = \n    tests/*\n    scripts/*\n    venv/*\n    .venv/*\n")
        cov_rc_created = True

    result = run_command([sys.executable, "-m", "pytest", "--cov=.", "--cov-report=json:coverage.json"], cwd=BASE_DIR)
    
    # Check test success
    if result.returncode == 0:
        test_status = "✅ PASSED (All tests passed)"
    elif result.returncode == 1:
        test_status = "❌ FAILED (Some tests failed)"
    elif result.returncode == 5:
        test_status = "⚠️ NO TESTS COLLECTED"
    else:
        test_status = f"⚠️ ERROR (Exit code {result.returncode})"
        
    print(f"Tests Status: {test_status}")

    # Process coverage json
    cov_json_path = BASE_DIR / "coverage.json"
    cov_status = "⚠️ No coverage data"
    global_cov = 0.0
    
    if cov_json_path.exists():
        try:
            with open(cov_json_path, "r") as f:
                cov_data = json.load(f)
            
            total_stats = cov_data.get("totals", {})
            global_cov = total_stats.get("percent_covered", 0.0)
            cov_status = f"{global_cov:.2f}%"
            print(f"Global Coverage: {cov_status}")
        except Exception as e:
            print(f"Error parsing coverage JSON: {e}")
    
    # Cleanup
    if cov_rc_created and cov_rc.exists():
        os.remove(cov_rc)
        
    # we don't return stdout because pytest output is huge
    # Just parse the summary lines from the end of pytest output
    summary_lines = []
    if result and result.stdout:
        lines = result.stdout.splitlines()
        # Get the last 15 lines for the summary
        summary_lines = lines[-15:]
        
    return test_status, cov_status, global_cov, "\n".join(summary_lines)

def analyze_codebase():
    print_header("Run Codebase Legacy/Monolith Analysis")
    print("Running codebase_analyzer.py...")
    
    script_path = BASE_DIR / "scripts" / "codebase_analyzer.py"
    result = run_command([sys.executable, str(script_path), str(BASE_DIR)], cwd=BASE_DIR)
    
    audit_json = BASE_DIR / "codebase_audit_report.json"
    
    total_files = 0
    monoliths = 0
    legacy = 0
    
    if audit_json.exists():
        try:
            with open(audit_json, "r") as f:
                data = json.load(f)
            total_files = data.get("summary", {}).get("total_files", 0)
            monoliths = len(data.get("monolithic_files", []))
            legacy = len(data.get("legacy_files", []))
            print(f"Analyzed {total_files} files. Found {monoliths} monoliths, {legacy} legacy files.")
        except Exception as e:
            print(f"Error parsing codebase audit JSON: {e}")
    else:
        print("codebase_audit_report.json not generated.")
        
    return total_files, monoliths, legacy

def analyze_test_quality():
    print_header("Run Test Quality Analyzer")
    print("Running test_quality_analyzer.py...")
    
    script_path = BASE_DIR / "scripts" / "test_quality_analyzer.py"
    result = run_command([sys.executable, str(script_path)], cwd=BASE_DIR)
    
    # This generates test_reports/compliance_data.json
    compliance_json = BASE_DIR / "test_reports" / "compliance_data.json"
    
    total_tests = 0
    perfect_score = 0
    good_score = 0
    poor_score = 0
    
    if compliance_json.exists():
        try:
            with open(compliance_json, "r") as f:
                data = json.load(f)
            
            total_tests = len(data)
            for t in data:
                if t.get("score", 0) == 100:
                    perfect_score += 1
                elif t.get("score", 0) >= 80:
                    good_score += 1
                else:
                    poor_score += 1
            # Just count those with "status": "Actualizado" (score >= 80)
            updated = sum(1 for t in data if t.get("status") in ("Actualizado", "Perfecto")) # test quality analyzer assigns Actualizado if >= 80
            print(f"Analyzed {total_tests} test files. {updated} are compliant (>=80 score), {perfect_score} are perfect (100 score).")
        except Exception as e:
            print(f"Error parsing compliance JSON: {e}")
            
    return total_tests, perfect_score, good_score + perfect_score

def generate_markdown_report(mypy_status, mypy_out, test_status, cov_status, test_summary, files, monoliths, legacy, test_files, perfect_tests, good_tests):
    print_header("Generating Master QA Report")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    lines = [
        f"# 📊 Master Code Quality Assurance Report",
        f"**Date:** {timestamp}\n",
        
        "## 🎯 Executive Summary",
        "| Metric | Status |",
        "|--------|--------|",
        f"| **Test Suite** | {test_status} |",
        f"| **Global Coverage** | {cov_status} |",
        f"| **Mypy Strict Typing** | {mypy_status} |",
        f"| **Codebase Health** | {monoliths} Monolithic files, {legacy} Legacy files |",
        f"| **Test Compliance** | {good_tests}/{test_files} files comply with Strict Testing |",
        "\n---",
        
        "## 1️⃣ Test Execution & Coverage",
        f"**Test Outcome:** {test_status}",
        f"**Coverage:** {cov_status}",
        "```text",
        test_summary,
        "```",
        "*Note: See `coverage.json` or run `scripts/generate_coverage_report.py` for detailed line-by-line coverage.*",
        "\n---",
        
        "## 2️⃣ Strict Type Checking (Mypy)",
        f"**Status:** {mypy_status}",
        "```text"
    ]
    
    # Add mypy output, truncated if too long
    mypy_lines = mypy_out.splitlines() if mypy_out else []
    if len(mypy_lines) > 50:
        lines.extend(mypy_lines[:50])
        lines.append(f"... (+ {len(mypy_lines) - 50} more lines. Run `mypy .` for full output)")
    else:
        lines.extend(mypy_lines)
    lines.append("```")
    lines.append("\n---")
    
    lines.extend([
        "## 3️⃣ Structural Health & Deuda Técnica",
        f"Analizados **{files}** archivos fuente.",
        f"- **Archivos Monolíticos (>400 LOC / Clases grandes):** {monoliths}",
        f"- **Archivos Legacy (`print`, `bare except`, no tipados):** {legacy}",
        "*Note: See `codebase_audit_report.json` for exactly which files need attention.*",
        "\n---",
        
        "## 4️⃣ Strict Testing Compliance",
        f"Analizados **{test_files}** archivos de test.",
        f"- **Test Files Actualizados (Score >= 80):** {good_tests} ({(good_tests/test_files*100) if test_files else 0:.1f}%)",
        f"- **Test Files Perfectos (Score 100):** {perfect_tests} ({(perfect_tests/test_files*100) if test_files else 0:.1f}%)",
        "*Note: Compliance depends on using `@pytest.mark`, `DTO` instance checks, Strict Mocks, and docstrings. See `test_reports/compliance_data.json`.*",
        "\n"
    ])
    
    with open(QA_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    print(f"Report successfully saved to: {QA_REPORT_PATH}")

def main():
    print_header("HIPATIA - MASTER QUALITY AUDIT")
    
    # 1. Tests & Coverage
    test_status, cov_status, cov_pct, test_summary = analyze_tests_and_coverage()
    
    # 2. Mypy
    mypy_status, mypy_out = analyze_mypy()
    
    # 3. Codebase Metrics
    files, monoliths, legacy = analyze_codebase()
    
    # 4. Test Quality
    test_files, perfect_tests, good_tests = analyze_test_quality()
    
    # 5. Generate Report
    generate_markdown_report(
        mypy_status, mypy_out, test_status, cov_status, test_summary, 
        files, monoliths, legacy, test_files, perfect_tests, good_tests
    )
    
    print("\n✅ Audit Complete!")

if __name__ == "__main__":
    main()
