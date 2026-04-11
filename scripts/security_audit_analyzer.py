#!/usr/bin/env python3
"""
Nombre del Módulo: scripts.security_audit_analyzer

Descripción: Security Audit Analyzer Script Analyzes the codebase for security issues identified in the technical audit.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple
import json


class SecurityAuditAnalyzer:
    """Analyzes code for security vulnerabilities."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.findings: Dict[str, List[Dict]] = {
            'credentials': [],
            'fail_open': [],
            'hashlib_usage': [],
            'no_rate_limiting': [],
            'no_audit_log': [],
            'create_all_calls': [],
            'sqlite_threading': [],
            'session_leaks': [],
        }
    
    def analyze_credentials(self):
        """Find hardcoded credentials."""
        print("🔍 Analyzing hardcoded credentials...")
        
        # Check docker-compose.yml
        docker_file = self.project_root / 'docker-compose.yml'
        if docker_file.exists():
            with open(docker_file, 'r') as f:
                content = f.read()
                if 'PASSWORD' in content or 'password' in content:
                    self.findings['credentials'].append({
                        'file': str(docker_file),
                        'issue': 'Hardcoded passwords in docker-compose.yml',
                        'severity': 'CRITICAL'
                    })
        
        # Check .env files
        env_file = self.project_root / '.env'
        if env_file.exists():
            self.findings['credentials'].append({
                'file': str(env_file),
                'issue': '.env file exists in project root (should not be committed)',
                'severity': 'HIGH'
            })
    
    def analyze_fail_open_policy(self):
        """Find fail-open security patterns."""
        print("🔍 Analyzing fail-open security patterns...")
        
        access_control = self.project_root / 'core' / 'security' / 'access_control.py'
        if access_control.exists():
            with open(access_control, 'r') as f:
                lines = f.readlines()
                for i, line in enumerate(lines, 1):
                    if 'if not service:' in line or 'if not _security_service:' in line:
                        # Check next few lines for fail-open behavior
                        for j in range(min(5, len(lines) - i)):
                            next_line = lines[i + j]
                            if 'return func(' in next_line:
                                self.findings['fail_open'].append({
                                    'file': str(access_control),
                                    'line': i,
                                    'issue': 'Fail-open policy: allows execution when security service not initialized',
                                    'severity': 'CRITICAL'
                                })
                                break
    
    def analyze_hashlib_usage(self):
        """Find hashlib usage for password hashing."""
        print("🔍 Analyzing hashlib usage...")
        
        for py_file in self.project_root.rglob('*.py'):
            if '.venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'import hashlib' in content or 'from hashlib' in content:
                        # Check if it's used for password hashing
                        if 'password' in content.lower() or 'passwd' in content.lower():
                            self.findings['hashlib_usage'].append({
                                'file': str(py_file),
                                'issue': 'hashlib imported in file that handles passwords (check if used for password hashing)',
                                'severity': 'MEDIUM'
                            })
            except Exception as e:
                pass
    
    def analyze_rate_limiting(self):
        """Check for rate limiting in authentication."""
        print("🔍 Analyzing rate limiting...")
        
        session_controller = self.project_root / 'controllers' / 'session_controller.py'
        if session_controller.exists():
            with open(session_controller, 'r') as f:
                content = f.read()
                if 'rate_limit' not in content.lower() and 'attempt' not in content.lower():
                    self.findings['no_rate_limiting'].append({
                        'file': str(session_controller),
                        'issue': 'No rate limiting implementation found in session controller',
                        'severity': 'MEDIUM'
                    })
    
    def analyze_audit_logging(self):
        """Check for audit logging."""
        print("🔍 Analyzing audit logging...")
        
        # Check if there's an audit log model or service
        audit_patterns = ['audit_log', 'AuditLog', 'audit_trail']
        found_audit = False
        
        for py_file in self.project_root.rglob('*.py'):
            if '.venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if any(pattern in content for pattern in audit_patterns):
                        found_audit = True
                        break
            except Exception:
                pass
        
        if not found_audit:
            self.findings['no_audit_log'].append({
                'file': 'N/A',
                'issue': 'No audit logging system found in codebase',
                'severity': 'MEDIUM'
            })
    
    def analyze_database_issues(self):
        """Check for database-related security issues."""
        print("🔍 Analyzing database security issues...")
        
        db_manager = self.project_root / 'database' / 'database_manager.py'
        if db_manager.exists():
            with open(db_manager, 'r') as f:
                lines = f.readlines()
                for i, line in enumerate(lines, 1):
                    # Check for create_all() calls
                    if 'create_all()' in line or 'metadata.create_all' in line:
                        self.findings['create_all_calls'].append({
                            'file': str(db_manager),
                            'line': i,
                            'issue': 'Base.metadata.create_all() called - should use Alembic migrations only',
                            'severity': 'MEDIUM'
                        })
                    
                    # Check for check_same_thread=False
                    if 'check_same_thread' in line and 'False' in line:
                        self.findings['sqlite_threading'].append({
                            'file': str(db_manager),
                            'line': i,
                            'issue': 'check_same_thread=False allows unsafe multi-threaded access to SQLite',
                            'severity': 'MEDIUM'
                        })
    
    def generate_report(self) -> str:
        """Generate a formatted report of findings."""
        report = []
        report.append("=" * 80)
        report.append("SECURITY AUDIT ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")
        
        total_issues = sum(len(issues) for issues in self.findings.values())
        critical_count = sum(1 for issues in self.findings.values() for issue in issues if issue.get('severity') == 'CRITICAL')
        high_count = sum(1 for issues in self.findings.values() for issue in issues if issue.get('severity') == 'HIGH')
        medium_count = sum(1 for issues in self.findings.values() for issue in issues if issue.get('severity') == 'MEDIUM')
        
        report.append(f"Total Issues Found: {total_issues}")
        report.append(f"  - CRITICAL: {critical_count}")
        report.append(f"  - HIGH: {high_count}")
        report.append(f"  - MEDIUM: {medium_count}")
        report.append("")
        report.append("=" * 80)
        
        for category, issues in self.findings.items():
            if issues:
                report.append("")
                report.append(f"{'=' * 80}")
                report.append(f"Category: {category.upper().replace('_', ' ')}")
                report.append(f"{'=' * 80}")
                
                for issue in issues:
                    report.append(f"\n[{issue['severity']}] {issue['issue']}")
                    report.append(f"  File: {issue['file']}")
                    if 'line' in issue:
                        report.append(f"  Line: {issue['line']}")
        
        report.append("")
        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def run_analysis(self):
        """Run all analysis methods."""
        print("\n🔒 Starting Security Audit Analysis...")
        print(f"Project root: {self.project_root}\n")
        
        self.analyze_credentials()
        self.analyze_fail_open_policy()
        self.analyze_hashlib_usage()
        self.analyze_rate_limiting()
        self.analyze_audit_logging()
        self.analyze_database_issues()
        
        print("\n✅ Analysis complete!")
        return self.generate_report()


def main():
    # Get project root (assuming script is in scripts/ directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    analyzer = SecurityAuditAnalyzer(str(project_root))
    report = analyzer.run_analysis()
    
    print("\n" + report)
    
    # Save report to file
    output_file = project_root / 'Documentacion' / 'Pulido seguridad' / 'security_analysis_results.txt'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(report)
    
    print(f"\n📄 Report saved to: {output_file}")


if __name__ == '__main__':
    main()
