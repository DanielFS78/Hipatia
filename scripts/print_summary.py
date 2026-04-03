"""
Script ejecutable (`print_summary`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import json

with open("codebase_audit_report.json") as f:
    d = json.load(f)

print("Top 15 Monolithic Files:")
for i, f in enumerate(d["monolithic_files"][:15]):
    print(f"  {i+1}. {f['file']} - {f['loc']} LOC, {f['large_functions']} large funcs, {len(f['large_classes'])} large classes")

print("\nTop 15 Legacy Files:")
for i, f in enumerate(d["legacy_files"][:15]):
    print(f"  {i+1}. {f['file']} - {f['loc']} LOC, untyped: {f['untyped_ratio']:.2%}, prints: {f['prints']}, bare_excepts: {f['bare_excepts']}")
