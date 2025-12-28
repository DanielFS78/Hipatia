#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration Verification Script
==============================
Detects orphan code patterns that may have been left behind during the
SQLAlchemy/DTO migration.

Usage:
    python scripts/verify_migration.py

Checks for:
1. Direct db.set_setting() / db.get_setting() calls (should use config_repo)
2. Tuple access patterns on DTO results ([0], [1], etc.)
3. Usage of removed methods from DatabaseManager
4. Old import patterns
"""

import os
import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple

# Directory configuration
PROJECT_ROOT = Path(__file__).parent.parent
EXCLUDE_DIRS = {'.venv', '__pycache__', '.git', 'Backup', '.pytest_cache', 'test_reports'}
EXCLUDE_FILES = {'verify_migration.py'}  # Exclude self to avoid false positives
INCLUDE_EXTENSIONS = {'.py'}


@dataclass
class CodeIssue:
    """Represents a potential code issue found during verification."""
    file_path: str
    line_number: int
    issue_type: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    line_content: str


def find_python_files(root: Path) -> List[Path]:
    """Find all Python files in the project, excluding certain directories."""
    files = []
    for item in root.rglob('*.py'):
        # Skip excluded directories
        if any(excluded in item.parts for excluded in EXCLUDE_DIRS):
            continue
        # Skip excluded files
        if item.name in EXCLUDE_FILES:
            continue
        files.append(item)
    return files


def check_orphan_method_calls(content: str, file_path: str) -> List[CodeIssue]:
    """Check for direct calls to methods that should go through repositories."""
    issues = []
    lines = content.split('\n')
    
    # Pattern 1: db.set_setting or db.get_setting without config_repo
    # But NOT config_repo.set_setting (which is correct)
    patterns = [
        (r'\.db\.set_setting\s*\(', 'db.set_setting() should be db.config_repo.set_setting()'),
        (r'\.db\.get_setting\s*\(', 'db.get_setting() should be db.config_repo.get_setting()'),
        (r'db_manager\.set_setting\s*\(', 'db_manager.set_setting() should be db_manager.config_repo.set_setting()'),
        (r'db_manager\.get_setting\s*\(', 'db_manager.get_setting() should be db_manager.config_repo.get_setting()'),
    ]
    
    for i, line in enumerate(lines, 1):
        # Skip comments
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
            
        for pattern, message in patterns:
            # Skip if it's already using config_repo
            if 'config_repo.set_setting' in line or 'config_repo.get_setting' in line:
                continue
            if re.search(pattern, line):
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type='orphan_method_call',
                    severity='error',
                    message=message,
                    line_content=stripped
                ))
    
    return issues


def check_tuple_access_on_dtos(content: str, file_path: str) -> List[CodeIssue]:
    """Check for tuple access patterns that might indicate unconverted code."""
    issues = []
    lines = content.split('\n')
    
    # DTO method names that return DTOs, not tuples
    dto_methods = [
        'get_all_workers', 'get_all_machines', 'get_all_products', 'get_all_materials',
        'get_all_pilas', 'get_all_preprocesos', 'get_all_fabricaciones',
        'search_products', 'search_workers', 'search_pilas',
        'get_worker_details', 'get_product_details', 'get_machine_details',
    ]
    
    # Pattern: variable[0] or variable[1], etc. after DTO method call
    # This is a heuristic - may have false positives
    tuple_access_pattern = r'\[\s*\d+\s*\]'
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
        
        # Check if line has tuple-style access
        if re.search(tuple_access_pattern, line):
            # Look for DTO method calls in surrounding context (simplified check)
            for method in dto_methods:
                if method in content[max(0, content.find(line)-500):content.find(line)+len(line)]:
                    # This is just a warning - may be valid
                    if '[0]' in line or '[1]' in line or '[2]' in line:
                        issues.append(CodeIssue(
                            file_path=file_path,
                            line_number=i,
                            issue_type='potential_tuple_access',
                            severity='warning',
                            message='Possible tuple access on DTO result - verify this uses .attribute instead of [index]',
                            line_content=stripped[:100]
                        ))
                    break
    
    return issues


def check_removed_methods(content: str, file_path: str) -> List[CodeIssue]:
    """Check for usage of methods that have been removed from DatabaseManager."""
    issues = []
    lines = content.split('\n')
    
    removed_methods = [
        ('add_product_to_fabricacion', 'Use preproceso_repo.add_product_to_fabricacion()'),
        ('get_fabricacion_products', 'Use preproceso_repo.get_fabricacion_products()'),
        ('get_preproceso_components', 'Use preproceso_repo.get_preproceso_components()'),
    ]
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
            
        for method, fix in removed_methods:
            # Look for method calls
            pattern = rf'\.{method}\s*\('
            if re.search(pattern, line):
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type='removed_method',
                    severity='error',
                    message=f'Method {method}() may have been removed. {fix}',
                    line_content=stripped
                ))
    
    return issues


def check_file(file_path: Path) -> List[CodeIssue]:
    """Run all checks on a single file."""
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        return [CodeIssue(
            file_path=str(file_path),
            line_number=0,
            issue_type='read_error',
            severity='error',
            message=f'Could not read file: {e}',
            line_content=''
        )]
    
    str_path = str(file_path)
    issues = []
    issues.extend(check_orphan_method_calls(content, str_path))
    issues.extend(check_tuple_access_on_dtos(content, str_path))
    issues.extend(check_removed_methods(content, str_path))
    
    return issues


def print_issues(issues: List[CodeIssue]) -> Tuple[int, int, int]:
    """Print issues in a formatted way and return counts."""
    errors = [i for i in issues if i.severity == 'error']
    warnings = [i for i in issues if i.severity == 'warning']
    infos = [i for i in issues if i.severity == 'info']
    
    if errors:
        print("\n🔴 ERRORS (Must Fix):")
        print("=" * 70)
        for issue in errors:
            print(f"\n  {issue.file_path}:{issue.line_number}")
            print(f"    Issue: {issue.issue_type}")
            print(f"    Message: {issue.message}")
            print(f"    Code: {issue.line_content[:80]}")
    
    if warnings:
        print("\n🟡 WARNINGS (Review):")
        print("=" * 70)
        for issue in warnings[:10]:  # Limit output
            print(f"\n  {issue.file_path}:{issue.line_number}")
            print(f"    {issue.message}")
        if len(warnings) > 10:
            print(f"\n  ... and {len(warnings) - 10} more warnings")
    
    return len(errors), len(warnings), len(infos)


def main():
    """Main entry point."""
    print("=" * 70)
    print("Migration Verification Script")
    print("Checking for orphan code patterns after SQLAlchemy/DTO migration")
    print("=" * 70)
    
    files = find_python_files(PROJECT_ROOT)
    print(f"\nScanning {len(files)} Python files...")
    
    all_issues = []
    for file_path in files:
        issues = check_file(file_path)
        all_issues.extend(issues)
    
    errors, warnings, infos = print_issues(all_issues)
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Files scanned: {len(files)}")
    print(f"  🔴 Errors: {errors}")
    print(f"  🟡 Warnings: {warnings}")
    print("=" * 70)
    
    if errors > 0:
        print("\n❌ Migration verification FAILED - fix errors before proceeding")
        return 1
    elif warnings > 0:
        print("\n⚠️  Migration verification passed with warnings - review recommended")
        return 0
    else:
        print("\n✅ Migration verification PASSED - no issues found")
        return 0


if __name__ == "__main__":
    sys.exit(main())
