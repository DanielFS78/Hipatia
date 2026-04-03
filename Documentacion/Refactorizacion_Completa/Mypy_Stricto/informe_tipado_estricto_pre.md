## Informe PRE — Fase de Tipado Estricto (Mypy)

### Objetivo

Alcanzar **0 errores** en:

```bash
python3 -m mypy . --config-file mypy.ini --show-error-codes --no-error-summary
```

y mantener:

- `pytest` completo ✅
- `python3 run_tests.py` ✅

### Estado inicial (baseline)

- **Baseline guardado**: `Documentacion/Refactorizacion_Completa/Mypy_Stricto/mypy_baseline.txt`
- **Primeras correcciones aplicadas (2026-03-18)**:
  - `ui/dialogs/production_flow/enhanced_flow_presenter_state.py`: eliminado `type: ignore` ya innecesario.
  - `ui/dialogs/production_flow/enhanced_flow_presenter_builder.py`: eliminado `type: ignore` y definido contrato mínimo (`add_task`, `clear_tasks`) para satisfacer mypy en el mixin.
  - `generate_ui_report.py`: anotación conservadora basada en `Any` para datos JSON y corrección de `var-annotated`.
  - `database/repositories/pila/pila_crud_manager.py`: normalización a `str` para `nombre/descripcion` al construir `PilaDTO` (evita `str | None`).
  - `database/repositories/pila/pila_workflow_manager.py`: normalización a `str` para `descripcion` al construir `PilaDTO`.
  - `database/repositories/tracking/core_manager.py`: filtrado explícito de `None` tras el mapeo para retornar `list[TrabajoLogDTO]` real.
  - `database/repositories/tracking_log_repository.py`: wrappers de mapeo aceptan `logger` posicional/keyword por compatibilidad, usando siempre `self.logger`.
  - `mypy.ini`: excluidos `tests/debugging/*` de mypy (scripts de depuración fuera de la suite).
  - `core/utils/ui_scaler.py`: `QApplication.instance()` casteado para permitir `primaryScreen()` sin falso positivo.
  - `ui/widgets/production_flow/define_control_panel.py`: guarda `None` en `deleteLater()` (evita `union-attr`).
  - `ui/worker/main_window/window.py`: casteo de `QApplication.instance()` y guarda `None` en páginas (evita `attr-defined/union-attr`).
- **Cobertura y suite de tests**: se mantendrá como condición de paso en cada iteración.

### Tipos de errores detectados (categorías)

- **A. Higiene de mypy**
  - `unused-ignore`: ignorados que ya no son necesarios.
  - `var-annotated`: variables sin anotación explícita requeridas por config.
- **B. Optional/None (no_implicit_optional)**
  - `arg-type`, `union-attr`, `operator`: valores `None` llegando a APIs que esperan `str/int/datetime`.
  - defaults `None` en parámetros no-Optional.
- **C. Contratos (Protocols / Interfaces / Mixins)**
  - `attr-defined`, `override`, `misc`: el contrato tipado no refleja el contrato real (atributos/métodos faltantes).
- **D. UI / PyQt6**
  - `union-attr`: Qt puede devolver `None` (ej. `layout.itemAt(i)`).
  - `attr-defined` sobre `QCoreApplication` cuando en realidad se usa `QApplication`.
- **E. Tipos de retorno/estructura**
  - `return-value`, `assignment`: retornos antiguos `dict` vs DTOs ya introducidos, o estructuras inconsistentes.
- **F. Tests**
  - Errores de tipado en fixtures y dobles de test (`method-assign`, lambdas, incompatibilidades de Protocols).

### Estrategia conservadora (orden de ejecución)

1. **A (Higiene)**: eliminar `unused-ignore` y añadir anotaciones faltantes `var-annotated` (bajo riesgo).
2. **B (None/Optional)**: ajustar defaults y guardas (`if x is None: ...`) y tipos `Optional[...]` donde aplique.
3. **C (Contratos)**: alinear `Protocol`/interfaces con el comportamiento real; preferir contratos explícitos a `Any`.
4. **E (Retornos)**: consolidar fronteras (DTOs / tipos estables), minimizando `dict[str, Any]` en producción.
5. **D (UI/Qt)**: cambios mínimos y defensivos (guardas `None`, tipos correctos `QApplication`).
6. **F (Tests)**: corregir tipado en tests **sin relajar** el contrato de producción; si faltan tests, añadirlos antes.

### Ciclo por iteración (obligatorio)

Para cada ítem:

1. Corregir 1 archivo (máximo 3).
2. Ejecutar mypy por archivo y luego completo.
3. Ejecutar `pytest <scope> -x -q`, `pytest -q`, `python3 run_tests.py`.
4. Documentar el cambio (español) y, si fue sustantivo, ejecutar `python3 scripts/generate_daniel_doc.py`.

