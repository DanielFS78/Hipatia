---
name: Limpieza de Archivos Residuales del Proyecto
description: Eliminar archivos .bak_monolith, reportes antiguos en raíz, cobertura obsoleta y cualquier artefacto que no pertenezca al proyecto activo. Ejecutar ANTES de cualquier empaquetado o despliegue.
---

# Limpieza de Archivos Residuales — Proyecto Hipatia

## Objetivo

Eliminar todos los archivos que son artefactos históricos del proceso de refactorización y desarrollo, que no aportan valor al programa en producción y ensucian la raíz del proyecto.

## Archivos a Eliminar

### 1. Backups de monolitos fragmentados (`.bak_monolith`)

Estos archivos son copias de monolitos que ya fueron fragmentados correctamente. El código vivo está en los módulos resultantes.

```
./ui/worker/worker_main_window.py.bak_monolith
./database/models.py.bak_monolith
./database/repositories/pila_repository.py.bak_monolith
./database/repositories/reports_repository.py.bak_monolith
./database/repositories/machine_repository.py.bak_monolith
./core/simulation/simulation_events.py.bak_monolith
./core/camera_manager.py.bak_monolith
./core/label_manager.py.bak_monolith
./core/services/report_sheets.py.bak_monolith
./controllers/simulation_controller.py.bak_monolith
```

**Comando de verificación** (antes de borrar):
```bash
find . -name "*.bak_monolith" -not -path "./.venv/*"
```

### 2. Reportes y artefactos obsoletos en la raíz

```
./mypy_errors.txt
./mypy_full_errors.txt
./mypy_report.txt
./mypy_report_v2.txt
./pytest_report.txt
./codebase_audit_report.json
./coverage_after_business_units.json
./coverage_after_health.json
./coverage_after_health_checker.json
./fabric_cov.json
./dead_code_vulture.txt
./test_output.log
./find_tests_no_assert.py
./syntax_checker.py
./scribd_page.html
./Documentacion Daniel.page_measure_tmp.pdf  (en raíz, fuera de Documentacion/)
```

### 3. Archivos de cobertura duplicados en raíz

```
./.coverage 2
./.coverage 3
```

## Procedimiento

1. **Ejecutar la suite completa de tests** y verificar 0 fallos ANTES de borrar nada.
2. **Hacer un commit git** con el estado actual (safety net).
3. Ejecutar los comandos de eliminación.
4. **Ejecutar la suite de tests de nuevo** para confirmar que la eliminación no rompió imports.
5. **Ejecutar `python3 scripts/generate_daniel_doc.py`** para verificar que la documentación sigue generándose correctamente.

## Verificación Post-Limpieza

```bash
# No debe devolver resultados:
find . -name "*.bak_monolith" -not -path "./.venv/*"

# No deben existir estos archivos:
ls mypy_errors.txt mypy_full_errors.txt dead_code_vulture.txt 2>/dev/null
```

## Estado

- [x] Archivos `.bak_monolith` eliminados
- [x] Reportes de raíz eliminados
- [x] Archivos `.coverage` duplicados eliminados
- [x] Tests pasan al 100% post-limpieza
- [x] Documentación genera correctamente
