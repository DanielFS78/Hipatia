"""
Script ejecutable (`analyze_coverage_risks`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import json
import os
import sys

# Import the loose mocks analysis logic
sys.path.append(os.getcwd())
try:
    from scripts.analyze_loose_mocks import check_loose_mocks
except ImportError:
    # Fallback if running from scripts dir
    from analyze_loose_mocks import check_loose_mocks

def analyze_risk():
    # 1. Load Coverage Data
    try:
        with open("coverage.json", "r") as f:
            cov_data = json.load(f)
    except FileNotFoundError:
        print("Error: coverage.json not found. Run pytest --cov... first.")
        return

    # 2. Analyze Coverage (Focus on missing branches/lines)
    cov_stats = {}
    for filename, data in cov_data["files"].items():
        # Filter for relevant source files
        if not any(filename.startswith(p) for p in ["controllers/", "ui/", "core/", "database/"]):
            continue
            
        summary = data["summary"]
        missing_lines = summary["missing_lines"]
        missing_branches = summary["missing_branches"] if "missing_branches" in summary else 0
        total_branches = summary["num_branches"] if "num_branches" in summary else 0
        percent = summary["percent_covered"]
        
        cov_stats[filename] = {
            "percent": percent,
            "missing_lines": missing_lines,
            "missing_branches": missing_branches,
            "total_branches": total_branches
        }

    # 3. Analyze Loose Mocks
    loose_mocks = check_loose_mocks("tests")
    mock_stats = {}
    for path, _ in loose_mocks:
        if path not in mock_stats:
            mock_stats[path] = 0
        mock_stats[path] += 1
        
    # 4. Cross-Reference (Heuristic Mapping)
    # Map test files to source files roughly
    risk_report = []
    
    for src_file, stats in cov_stats.items():
        # Try to find corresponding test file
        basename = os.path.basename(src_file).replace(".py", "")
        possible_tests = [
            f"tests/unit/test_{basename}.py",
            f"tests/integration/test_{basename}_integration.py",
            f"tests/unit/test_{basename}_controller.py" # heuristic
        ]
        
        related_mock_count = 0
        related_tests = []
        
        # Check specific matches
        for test_file in possible_tests:
            if test_file in mock_stats:
                max_mocks = mock_stats[test_file]
                related_mock_count += max_mocks
                related_tests.append(f"{test_file} ({max_mocks})")

        # Also check general fuzzy match if no direct match
        if related_mock_count == 0:
             for test_file in mock_stats.keys():
                 if basename in test_file:
                     related_mock_count += mock_stats[test_file]
                     related_tests.append(f"{test_file} ({mock_stats[test_file]})")
        
        # Calculate Risk Score
        # Risk increases with: Low Coverage + High Loose Mocks
        # Score = (100 - Coverage) + (Loose Mocks / 2)
        risk_score = (100 - stats["percent"]) + (related_mock_count * 0.5)
        
        if risk_score > 20: # Filter low risk
            risk_report.append({
                "file": src_file,
                "coverage": stats["percent"],
                "missing_branches": stats["missing_branches"],
                "loose_mocks": related_mock_count,
                "related_tests": related_tests,
                "risk_score": risk_score
            })
            
    # Sort by Risk Score
    risk_report.sort(key=lambda x: x["risk_score"], reverse=True)
    
    # 5. Output Report
    print(f"analyzed {len(cov_stats)} source files and found {len(risk_report)} high risk files.")
    print("\n| Archivo Fuente | Cobertura % | Ramas Faltantes | Mocks Permisivos | Tests Relacionados (Mocks) | Risk Score |")
    print("|:---|:---:|:---:|:---:|:---|:---:|")
    for item in risk_report[:30]: # Top 30
        tests_str = "<br>".join(item['related_tests'][:3]) # Limit to 3 tests for display
        print(f"| `{item['file']}` | {item['coverage']:.1f}% | {item['missing_branches']} | {item['loose_mocks']} | {tests_str} | {item['risk_score']:.1f} |")

if __name__ == "__main__":
    analyze_risk()
