# Fase 3.7: Análisis de Código Muerto en `ui/dialogs.py`

> **Fecha de análisis:** 27 de December de 2025, 16:23
> **Generado por:** `scripts/detect_dead_code.py`

---

## 1. Resumen Ejecutivo

| Categoría | Cantidad | Porcentaje |
|-----------|----------|------------|
| **Métodos totales** | 237 | 100% |
| Usados externamente | 189 | 79% |
| Solo uso interno | 0 | 0% |
| Dunders (implícitos) | 36 | 15% |
| **⚠️ Potencialmente muertos** | 12 | 5% |

> **Líneas de código potencialmente eliminables:** ~118 líneas

---

## 2. Clases sin Uso Externo Detectado

> [!WARNING]
> Estas clases no tienen instanciaciones detectadas fuera de `dialogs.py`.
> Podrían ser usadas dinámicamente o a través de imports indirectos.

| Clase | Líneas | Métodos |
|-------|--------|---------|
| `PrepStepsDialog` | 179 | 6 |
| `ReassignmentRuleDialog` | 129 | 3 |
| `MultiWorkerSelectionDialog` | 37 | 2 |
| `SeleccionarHojasExcelDialog` | 36 | 2 |
| `GetUnitsDialog` | 23 | 2 |

---

## 3. Métodos Muertos - Alta Confianza

> [!CAUTION]
> Estos métodos privados (`_nombre`) no tienen referencias detectables.
> Son candidatos seguros para eliminación.

| Clase | Método | Líneas | Rango |
|-------|--------|--------|-------|
| `EnhancedProductionFlowDialog` | `_highlight_dependencies_in_tree` | 39 | L4225-4264 |
| `DefineProductionFlowDialog` | `_on_worker_selected` | 17 | L1504-1521 |
| `DefineProductionFlowDialog` | `_on_prep_step_selected` | 17 | L1523-1540 |
| `ProcessingGlowEffect` | `_update_pulse` | 13 | L2815-2828 |
| `EnhancedProductionFlowDialog` | `_is_task_in_cycle_chain` | 2 | L5960-5962 |

**Total eliminable con alta confianza: ~88 líneas**

---

## 4. Métodos Sin Referencias - Media Confianza

> [!IMPORTANT]
> Estos métodos públicos no tienen referencias directas detectadas.
> Podrían ser parte de la API pública del diálogo o usados vía connect().
> **Revisar manualmente antes de eliminar.**

| Clase | Método | Líneas | Rango |
|-------|--------|--------|-------|
| `EnhancedProductionFlowDialog` | `update_all_geometries` | 8 | L5073-5081 |
| `DefinirCantidadesDialog` | `get_cantidades` | 8 | L7900-7908 |
| `SeleccionarHojasExcelDialog` | `get_opciones` | 6 | L7254-7260 |
| `CanvasWidget` | `dropEvent` | 5 | L68-73 |
| `CanvasWidget` | `dragEnterEvent` | 1 | L62-63 |
| `CanvasWidget` | `dragMoveEvent` | 1 | L65-66 |
| `GetUnitsDialog` | `get_units` | 1 | L7844-7845 |

---

## 5. Métodos con Solo Uso Interno

Estos métodos son llamados solo desde dentro de `dialogs.py`:

| Clase | Método | Líneas | Es Privado |
|-------|--------|--------|------------|

---

## 6. Recomendaciones

### Paso 1: Eliminar Código Muerto de Alta Confianza

Métodos a eliminar primero (privados sin referencias):

```python
# Eliminar estos métodos:
# - DefineProductionFlowDialog._on_worker_selected()  # Líneas 1504-1521
# - DefineProductionFlowDialog._on_prep_step_selected()  # Líneas 1523-1540
# - ProcessingGlowEffect._update_pulse()  # Líneas 2815-2828
# - EnhancedProductionFlowDialog._highlight_dependencies_in_tree()  # Líneas 4225-4264
# - EnhancedProductionFlowDialog._is_task_in_cycle_chain()  # Líneas 5960-5962
```

### Paso 2: Verificar Manualmente Métodos de Media Confianza

Antes de eliminar métodos públicos, verificar:

1. ¿Son slots conectados via `signal.connect(self.metodo)`?
2. ¿Son llamados desde UI via eventos (`clicked`, `textChanged`, etc.)?
3. ¿Son parte de la API pública que devuelve datos al controlador?

### Paso 3: Ejecutar Tests Después de Cada Eliminación

```bash
source .venv/bin/activate && python -m pytest tests/ -v --tb=short
```

---

*Documento generado automáticamente - 27/12/2025 16:23*