# Fase 2 — Lote 6: Corrección en Masa de assert_called_once() y create_autospec

**Fecha:** 2026-03-15
**Estado:** ✅ Completado

---

## Archivos modificados

| Archivo | Antipatrones corregidos | Tests |
|---------|------------------------|-------|
| `tests/unit/test_prep_dialogs_coverage.py` | 10 `assert_called_once()` → `assert_called_once_with(args)`, `ANY` añadido al import | 35 ✅ |
| `tests/controllers/worker/test_management_manager.py` | 3 `assert_called_once()` → `assert_called_once_with(args)` | 4 ✅ |
| `tests/controllers/worker/test_task_manager.py` | 4 `assert_called_once()` → `assert_called_once_with(args)` | 2 ✅ |
| `tests/controllers/product/test_product_manager.py` | 1 `assert_called_once()` → `assert_called_once_with(ANY, ANY)`, `ANY` añadido | 3 ✅ |
| `tests/controllers/product/test_preproceso_manager.py` | 1 `assert_called_once()` → `assert_called_once_with()` | 3 ✅ |
| `tests/unit/test_navigation_controller_comprehensive.py` | 8 `assert_called_once()` → `assert_called_once_with()` | 29 ✅ |
| `tests/unit/test_app_coverage.py` | `MagicMock()` → `create_autospec(AppController)`, `create_autospec(SessionController)`, `create_autospec(DatabaseManager)` | 7 ✅ |
| `tests/unit/test_file_controller.py` | `MagicMock()` → `create_autospec(logging.Logger)`, fixtures mejorados | 12 ✅ |

**Total tests:** 95 ✅ / 0 ❌

---

## Métricas

| Métrica | Lote 5 | Lote 6 | Δ |
|---------|--------|--------|---|
| Score medio | 36.4 | 36.7 | +0.3 |
| Tests fallando | 0 | 0 | 0 |
| Cobertura | 96.8% | 96.8% | 0 |

---

## Análisis de progreso lento

El score sube muy lentamente (+0.3 por lote) porque:
- 201 archivos en total → cada archivo aporta ~0.5 pts al promedio
- Para subir 1 punto se necesitan ~2 archivos de 0→80 pts
- Los archivos con mayor potencial (+65 a +93 pts) son los `comprehensive` que tienen
  `MagicMock()` sin spec en fixtures de widgets Qt (no corregibles con `create_autospec`)

## Lecciones aprendidas

1. **assert_called_once_with()**: Siempre verificar los argumentos exactos del código fuente antes de asumir el tipo de mensaje ("Error" vs "Campo Requerido", "warning" vs "error")
2. **create_autospec con DatabaseManager**: No funciona directamente porque los repos son atributos dinámicos. Usar `MagicMock()` con repos configurados explícitamente.
3. **Impacto por archivo**: Cada archivo corregido aporta ~0.5 pts. Para llegar a 80/100 se necesitan ~87 archivos más en estado "Actualizado" (actualmente 19/201).

## Recomendación para lote 7

Atacar los archivos con mayor potencial de mejora que NO tienen restricciones Qt:
- `test_product_controller_v2_comprehensive.py` (27→100, +73 pts)
- `test_product_controller_preprocesos.py` (27→100, +73 pts)
- `test_product_dialogs_coverage.py` (35→100, +65 pts)
- `test_historial_controller_comprehensive.py` (35→100, +65 pts)

Estos archivos tienen `loose_mocks=-30` pero NO tienen `patches_no_autospec`, lo que sugiere
que los `MagicMock()` son en fixtures de servicios (corregibles con `create_autospec`).
