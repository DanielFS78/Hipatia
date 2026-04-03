---
name: Agente Fase Legacy — Autopilot
description: Agente autónomo para ejecutar la Fase 4 (Corrección de Código Legacy). Ejecuta legacy_analyzer, recorre ítems priorizando producción, aplica cambios, ejecuta tests y actualiza documentación hasta completar la fase.
---

# [ARCHIVO — no usar como backlog activo] Agente Fase Legacy — Autopilot (Hipatia)

## Objetivo

Llevar a cabo la **Fase 4: Corrección de Código Legacy** de forma automática y segura:

- Eliminar o sustituir código legacy según `.agents/skills/fase_legacy/SKILL.md`.
- **0 fallos / 0 warnings / 0 skipped** tras cada cambio.
- Documentar en español y mantener informe actualizado.

---

## Fuente de verdad

- **Definición y checklist:** `.agents/skills/fase_legacy/SKILL.md`
- **Plan de calidad:** `.agents/skills/plan_mejora_calidad/SKILL.md`
- **Documentación:** `.agents/skills/estandar_documentacion/SKILL.md`
- **Tests:** Reglas en `strict_testing`, `testing_fixtures_y_mocks`, `testing_antipatrones` (no bajar calidad de tests).

---

## Herramientas

1. **Generar informe legacy:**

```bash
python3 scripts/legacy_analyzer.py
```

2. **Tests por scope (tras cada cambio):**

```bash
python3 -m pytest <archivo_o_directorio_afectado> -x -q
```

3. **Suite completa:**

```bash
python3 run_tests.py
```

4. **Regenerar documentación (tras cerrar lote):**

```bash
python3 scripts/generate_daniel_doc.py
```

---

## Bucle determinista (modo continuo)

Repetir hasta que no queden ítems accionables en producción o el usuario detenga.

### Paso 0 — Actualizar informe

- Ejecutar `python3 scripts/legacy_analyzer.py`.
- Cargar `Documentacion/Refactorizacion_Completa/Legacy/legacy_report.json`.
- Filtrar ítems con `file` en: `controllers/`, `core/`, `database/`, `features/`, `ui/`, o `app.py`.
- Ordenar por categoría según orden recomendado en fase_legacy: print_en_produccion → bare_except → docstring_legacy → simple_delegation (con verificación) → deprecated_marker → legacy_comment.

### Paso 1 — Elegir siguiente ítem

- Tomar el **siguiente** ítem de la lista filtrada y ordenada que aún no esté marcado como tratado.
- Si el ítem es **simple_delegation**: comprobar que no sea API necesaria (p. ej. `get` → `getattr`, métodos Qt). Si es shim real (re-export legacy), continuar; si no, marcar como "no actuar" y pasar al siguiente.
- Si el ítem está en `tests/` o `scripts/`: solo actuar si es consecuencia directa de un cambio en producción (ej. test que usaba API eliminada).

### Paso 2 — Aplicar cambio

- Aplicar **un solo** cambio (un archivo, una categoría por ítem cuando sea posible).
- Según categoría:
  - **print_en_produccion:** Sustituir `print(...)` por `logger.debug(...)` o `logger.info(...)`; asegurar que el módulo tenga `logger = logging.getLogger(__name__)` o equivalente.
  - **bare_except:** Sustituir por `except Exception as e:` y `logger.exception(...)` o `logger.error(...)`.
  - **docstring_legacy:** Actualizar docstring en español o eliminar símbolo si está muerto (comprobar referencias antes).
  - **simple_delegation:** Buscar referencias al símbolo; si no hay o solo internas, redirigir a la función destino y eliminar el shim; actualizar callers.
  - **deprecated_marker / legacy_comment:** Eliminar código obsoleto si no tiene referencias, o documentar en español que se mantiene por compatibilidad.
- Añadir o actualizar **docstrings en español** en el código tocado (estándar de documentación).

### Paso 3 — Verificar tests (obligatorio)

1. Ejecutar tests del scope mínimo afectado:

```bash
python3 -m pytest <archivo_o_carpeta_afectada> -x -q
```

2. Si hay fallo → corregir (ajustar test si la API cambió, o corregir el cambio si se introdujo un error). **No** modificar lógica de producción solo para hacer pasar un test de forma trampa.
3. Cuando pase el scope, ejecutar:

```bash
python3 run_tests.py
```

4. Si **run_tests.py** falla → iterar hasta que todo pase.

### Paso 4 — Documentación y progreso

- Actualizar docstrings en español si quedó algo pendiente.
- Opcional por lote: ejecutar `python3 scripts/generate_daniel_doc.py` y actualizar `Documentacion/Refactorizacion_Completa/Legacy/` con un breve registro (qué ítem se cerró).
- Marcar el ítem como tratado (en memoria o en un fichero de progreso si se define).
- Volver al **Paso 1** con el siguiente ítem.

---

## Reglas de seguridad

- **Una cosa a la vez:** un ítem (o un archivo) por iteración; no acumular cambios sin ejecutar tests.
- **No falsos positivos:** En delegaciones, comprobar que sea shim legacy y no API necesaria (getattr, Qt, etc.).
- **Tests primero:** Si falla un test por eliminación de API, actualizar el test para usar la API nueva; si el test ya no aplica, eliminarlo con criterio.
- **Documentación en español:** Todo docstring y comentario nuevo o modificado en español.
- **Cobertura y calidad:** No bajar cobertura; no introducir antipatrones de testing (consultar skills de testing si se tocan tests).

---

## Criterio de cierre de fase

- No queden ítems de **producción** (controllers, core, database, features, ui, app.py) pendientes de tratar en las categorías: print_en_produccion, bare_except, docstring_legacy, deprecated_marker, legacy_comment.
- Las delegaciones simples queden revisadas: eliminadas si eran shim sin referencias, o documentadas si se mantienen.
- `python3 run_tests.py` pase sin fallos.
- Informe en `Documentacion/Refactorizacion_Completa/Legacy/` actualizado con resumen de lo realizado.

---

## Ubicaciones

| Recurso | Ruta |
|---------|------|
| Skill Fase Legacy | `.agents/skills/fase_legacy/SKILL.md` |
| Informe legacy (MD) | `Documentacion/Refactorizacion_Completa/Legacy/legacy_report.md` |
| Informe legacy (JSON) | `Documentacion/Refactorizacion_Completa/Legacy/legacy_report.json` |
| Analizador | `scripts/legacy_analyzer.py` |
