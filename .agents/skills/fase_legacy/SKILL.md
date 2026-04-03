---
name: Fase 4 — Corrección de Código Legacy
description: Definición de código legacy, criterios de actuación y checklist para su eliminación o sustitución. Prioridad sobre archivos de producción (controllers, core, database, features, ui).
---

# Fase 4 — Corrección de Código Legacy

> **Objetivo:** Eliminar o sustituir código legacy sin romper tests. Cada cambio debe verificar tests y documentación en español.

---

## 1. Qué se considera código legacy

| Categoría | Descripción | Acción recomendada |
|-----------|-------------|---------------------|
| **print en producción** | `print()` en controllers/, core/, database/, features/, ui/, app.py | Sustituir por `logger.debug()` o `logger.info()` según nivel. Añadir `self.logger` o `logger = logging.getLogger(__name__)` si falta. |
| **bare except** | `except:` sin tipo | Sustituir por `except Exception as e:` y registrar con `logger.exception(...)` o `logger.error(...)`. |
| **Marcadores deprecated** | Comentarios con `@deprecated`, `TODO: Remove`, `# DEPRECATED` | Eliminar el código marcado cuando no tenga referencias, o actualizar documentación si se mantiene temporalmente. |
| **Docstrings obsoleto/legacy** | Docstrings que indican "obsoleto", "legacy", "deprecated" | Si el símbolo ya no se usa: eliminar. Si se mantiene por compatibilidad: actualizar docstring en español indicando "Mantenido por compatibilidad. Preferir X." |
| **Delegaciones simples (shim)** | Función que solo llama a otra (ej. `def foo(): return bar()`) | Verificar referencias (grep/analizador). Si no hay callers externos, eliminar y redirigir callers internos al destino. Si hay callers: mantener y documentar o migrar callers. |
| **Comentarios legacy/re-export** | Comentarios tipo "Métodos Legacy / Re-Exports", "mantenido temporalmente" | Revisar si los métodos pueden eliminarse migrando a la API nueva; si no, dejar documentado en español. |

---

## 2. Ámbitos de actuación

- **Prioridad alta (producción):** `controllers/`, `core/`, `database/`, `features/`, `ui/`, `app.py`.
- **Prioridad baja o excluir de eliminación:** `tests/` (solo cambiar si el test es de código legacy que se elimina), `scripts/` y `tools/` (CLI puede usar print; valorar sustitución por logging).

---

## 3. Herramienta de análisis

```bash
python3 scripts/legacy_analyzer.py
```

Salida:
- `Documentacion/Refactorizacion_Completa/Legacy/legacy_report.json`
- `Documentacion/Refactorizacion_Completa/Legacy/legacy_report.md`

El agente debe usar el JSON para iterar sobre ítems; el MD para contexto humano.

---

## 4. Checklist por cambio (obligatorio)

Antes de dar por cerrado **cada** ítem:

1. [ ] Cambio aplicado solo en archivos de producción (o tests si se eliminó código testeado).
2. [ ] **Tests:** `python3 -m pytest <archivos_afectados_o_scope> -x -q` → 0 fallos, 0 warnings, 0 skipped.
3. [ ] **Suite global:** `python3 run_tests.py` → 0 fallos.
4. [ ] **Docstrings:** Código nuevo o modificado con docstrings en **español** (ver `.agents/skills/estandar_documentacion/SKILL.md`).
5. [ ] No se ha modificado lógica para "hacer pasar" tests; si un test falla por eliminación de API, actualizar el test para usar la API nueva o eliminar el test si ya no aplica.

---

## 5. Orden de actuación recomendado

1. **print → logger** en producción (impacto bajo, mejora trazabilidad).
2. **Bare except** → `except Exception` + logging (si aparecen en futuras auditorías).
3. **Docstrings legacy** en producción: actualizar texto o eliminar símbolo si está muerto.
4. **Delegaciones:** comprobar referencias; eliminar shim y redirigir solo si no hay falsos positivos (p. ej. `get` que delega en `getattr` es implementación, no shim a eliminar).
5. **Marcadores y comentarios legacy:** eliminar código obsoleto o documentar en español.

---

## 6. Reglas estrictas

- **Nunca** eliminar código sin comprobar referencias (búsqueda en proyecto o informe del analizador).
- **Siempre** ejecutar tests del scope afectado y `run_tests.py` tras cada cambio.
- **Siempre** documentar en español (docstrings y comentarios).
- Si un ítem es dudoso (ej. delegación que es API pública), **documentar** y no eliminar.

---

## 7. Referencias

| Recurso | Ruta |
|---------|------|
| Plan de Mejora de Calidad | `.agents/skills/plan_mejora_calidad/SKILL.md` |
| Estándar documentación | `.agents/skills/estandar_documentacion/SKILL.md` |
| Informe legacy | `Documentacion/Refactorizacion_Completa/Legacy/legacy_report.md` |
