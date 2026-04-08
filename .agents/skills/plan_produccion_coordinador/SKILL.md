---
name: Plan de Producción — Coordinador Maestro
description: Skill coordinadora que orquesta todas las tareas pendientes para llevar Hipatia a producción en Windows. Define prioridades, protocolo estricto de trabajo (tests → trabajo → tests → documentación → marcar), y referencia las skills específicas para cada área. LEE ESTE DOCUMENTO PRIMERO en cada sesión de trabajo hacia producción.
---

# Plan de Producción — Coordinador Maestro

> **⚠️ INSTRUCCIÓN CRÍTICA PARA LA IA:**
> 1. Este documento es la **Única Fuente de Verdad** para priorizar trabajo hacia producción.
> 2. **LEE ESTE DOCUMENTO PRIMERO** en cada sesión de trabajo.
> 3. Sigue el **Protocolo de Trabajo** estrictamente en cada tarea.
> 4. Trabaja **una tarea a la vez** en el orden de prioridad definido.
> 5. **NUNCA** saltes al siguiente bloque sin haber completado el protocolo completo del actual.
> 6. **Sincronización iCloud continua:** si trabajas en un worktree (no en el repo bajo iCloud Drive), **tú** copias con `cp` los archivos tocados al clon `Calcular_tiempos_fabricacion` en iCloud **tras cada lote de cambios** y al cerrar la tarea — ver `.agents/skills/ejecucion_secuencial_calidad/references/sync_icloud_continuo.md`. **No** pedirle al usuario que sincronice por defecto.

---

## Protocolo de Trabajo (OBLIGATORIO para cada tarea)

Cada tarea individual sigue este flujo de 6 pasos. **Sin excepciones.**

```
┌─────────────────────────────────────────────────────────────┐
│  PASO 1: VERIFICAR BASE                                     │
│  Ejecutar: pytest tests/ -x -q --timeout=30                 │
│  → Si hay fallos: PARAR y arreglar antes de cualquier cosa. │
│  → Si hay 0 fallos: continuar.                              │
├─────────────────────────────────────────────────────────────┤
│  PASO 2: EJECUTAR LA TAREA                                   │
│  Leer la skill específica de la tarea y seguir sus pasos.    │
│  Hacer los cambios de código/refactorización necesarios.     │
├─────────────────────────────────────────────────────────────┤
│  PASO 3: CREAR TESTS NUEVOS (si aplica)                      │
│  Si se ha creado código nuevo o clases nuevas:               │
│  → Escribir tests unitarios siguiendo:                       │
│    - .agents/skills/strict_testing/SKILL.md                  │
│    - .agents/skills/testing_por_capa/SKILL.md                │
│    - .agents/skills/testing_fixtures_y_mocks/SKILL.md        │
│  Si es refactorización sin API nueva: verificar tests        │
│  existentes.                                                 │
├─────────────────────────────────────────────────────────────┤
│  PASO 4: EJECUTAR TESTS                                      │
│  Ejecutar: pytest tests/ -x -q --timeout=30                 │
│  → Si hay fallos: ARREGLAR hasta que todos pasen.            │
│  → Si hay 0 fallos: continuar.                              │
│  Ejecutar también: python3 -m mypy . --config-file mypy.ini │
│  → Si hay errores nuevos: arreglar.                         │
├─────────────────────────────────────────────────────────────┤
│  PASO 5: ACTUALIZAR DOCUMENTACIÓN                            │
│  5a. Actualizar docstrings de los archivos modificados       │
│      (seguir .agents/skills/estandar_documentacion/SKILL.md) │
│  5b. Ejecutar: python3 scripts/generate_daniel_doc.py        │
│      Verificar que genera sin errores.                       │
│  5c. Si la tarea pertenece a una skill específica,           │
│      actualizar el estado ([ ] → [x]) en esa skill.         │
├─────────────────────────────────────────────────────────────┤
│  PASO 6: MARCAR TAREA COMO COMPLETADA                        │
│  Actualizar el estado de la tarea en la tabla de             │
│  "Tareas Priorizadas" de ESTE documento.                     │
│  Pasar a la siguiente tarea.                                 │
├─────────────────────────────────────────────────────────────┤
│  (Transversal) SYNC iCloud si worktree ≠ iCloud              │
│  Tras ediciones y al cerrar: copiar paths tocados a           │
│  HIPATIA_ICLOUD — sync_icloud_continuo.md                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Tareas Priorizadas (orden de ejecución)

### Bloque A — Limpieza y Estabilización (antes de cualquier refactor)

| # | Tarea | Skill de referencia | Estado | Prioridad |
|---|-------|---------------------|--------|-----------|
| A1 | Limpiar archivos residuales (.bak_monolith, reportes raíz) | `.agents/skills/limpieza_proyecto/SKILL.md` | ✅ Completada | 🔴 CRÍTICA |
| A2 | Extraer hora de backup del scheduler a ConfigurationRepository | `.agents/skills/preparacion_windows/SKILL.md` §5 | ✅ Completada | 🟡 MEDIA |

### Bloque B — Refactorización Estructural (mejora mantenibilidad)

| # | Tarea | Skill de referencia | Estado | Prioridad |
|---|-------|---------------------|--------|-----------|
| B1 | Migrar mixins de AppModel a composición/absorción (6 mixins) | `.agents/skills/migracion_mixins_composicion/SKILL.md` §Prioridad 1 | ✅ Completada | 🟡 MEDIA |
| B2 | Migrar mixins de ScheduleController (2 mixins → helpers) | `.agents/skills/migracion_mixins_composicion/SKILL.md` §Prioridad 2 | ✅ Completada | 🟡 MEDIA |
| B3 | Absorber mixins de repositorios (4 mixins) | `.agents/skills/migracion_mixins_composicion/SKILL.md` §Prioridad 3 | ✅ Completada | 🟢 BAJA |
| B4 | Absorber/delegar mixins de UI (2 mixins) | `.agents/skills/migracion_mixins_composicion/SKILL.md` §Prioridad 4 | ✅ Completada | 🟢 BAJA |
| B4.5 | Limpieza Final de Mixins (Composición sobre Herencia) | `.agents/skills/migracion_mixins_composicion/SKILL.md` | ✅ Completada | 🟡 MEDIA |
| B5 | Reducir God Object AppModel — inyectar servicios directos | `.agents/skills/reduccion_god_objects/SKILL.md` | ✅ **Completada (definitiva)** | 🟡 MEDIA |

### Bloque C — Preparación para Windows (producción)

| # | Tarea | Skill de referencia | Estado | Prioridad |
|---|-------|---------------------|--------|-----------|
| C1 | Auditar paths del sistema de archivos para compatibilidad Windows | `.agents/skills/preparacion_windows/SKILL.md` §2 | ✅ Completada (repo: `core/paths`, `DatabaseConfig`, health/backup/UI) | 🔴 CRÍTICA |
| C2 | Revisar `_fix_qt_macos()` y verificar que Qt no necesita fix en Windows | `.agents/skills/preparacion_windows/SKILL.md` §1 | ✅ Documentada (`Documentacion/Despliegue_Windows.md`; validación en PC pendiente) | 🟡 MEDIA |
| C3 | Crear archivo `hipatia.spec` y script `build_windows.bat` para PyInstaller | `.agents/skills/preparacion_windows/SKILL.md` §4 | ✅ Completada (`hipatia.spec`, `build_windows.bat`, `requirements-build.txt`) | 🔴 CRÍTICA |
| C4 | Validar UI en Windows con DPI 100%, 125%, 150% | `.agents/skills/preparacion_windows/SKILL.md` §1 | ⬜ Pendiente (solo en PC Windows) | 🔴 CRÍTICA |
| C5 | Validar cámaras/QR en Windows con DirectShow | `.agents/skills/preparacion_windows/SKILL.md` §3 | ⬜ Pendiente (solo en PC Windows) | 🟡 MEDIA |
| C6 | Checklist final pre-producción completo | `.agents/skills/preparacion_windows/SKILL.md` §6 | ⬜ Pendiente (solo en PC Windows) | 🔴 CRÍTICA |

### Bloque D — Mantenimiento Continuo (siempre activo)

| # | Tarea | Skill de referencia | Estado | Prioridad |
|---|-------|---------------------|--------|-----------|
| D1 | Mantener disciplina de señales en multihilo (nunca UI directa desde worker) | `.agents/skills/ui_pyqt_layout_freezes/SKILL.md` | ♻️ Continua | 🔴 CRÍTICA |
| D2 | Mantener frontera UI/DTO limpia (0 findings) | `.agents/skills/fase12c_sanear_frontera_ui/SKILL.md` | ♻️ Continua | 🟡 MEDIA |
| D3 | Mantener score de calidad de tests (no bajar del techo) | `.agents/skills/plan_mejora_calidad/SKILL.md` | ♻️ Continua | 🟡 MEDIA |

#### Detalle Tarea B4.5: Limpieza Final de Mixins
Esta tarea aborda los mixins remanentes que rompen la directriz de **composición sobre herencia**. Casos:
- **`FabricacionManagerProductsMixin`**: ✅ sustituido por **`FabricacionProductsHandler`** (`controllers/product/fabricacion_products_handler.py`), compuesto desde `FabricacionManager`.
- **`AppControllerCompatMixin`**: ✅ métodos absorbidos en **`AppController`** (`controllers/app_controller.py`); archivo mixin eliminado.
- **`EnhancedFlowPresenterBuilderMixin`**: ✅ sustituido por **`FlowBuilder`** (`ui/dialogs/production_flow/flow_builder.py`), instanciado por `EnhancedFlowPresenter`; API pública del presentador sin cambios.

#### Detalle Tarea B5: Reducir fachada AppModel — **FINALIZADA (sin subtareas abiertas)**

**Estado:** la tarea B5 del coordinador está **cerrada de forma definitiva**. No debe figurar como «pendiente» ni «en curso» en ningún otro documento. La **tabla canónica** de «qué queda fuera y por qué» vive en `.agents/skills/reduccion_god_objects/SKILL.md` → sección **«Estado de la tarea B5 (coordinador producción): FINALIZADA»** (tabla + regla para el agente).

**Alcance entregado (bloque B):**

- **Controladores:** `AppController` usa `ProductService` y (en reportes) el stack usa `ReportService` del DI cuando está registrado; fallback coherente a `AppModel` / `model.product_service`. `config_get_setting` / `config_set_setting` en fallback usan `self.db`.
- **Reportes UI:** `ReportesWidget` resuelve `ReportService` del contenedor y lo pasa a `SmartSearchWidget`, `OrderListWidget` y `ReportsChartsWidget` (listas/gráficas usan `AppController` + servicio).
- **Flujo:** `DefineProductionFlowDialog` construye `DefineFlowPresenter` solo con servicios (`MachineService`, `PreparationService`, `FabricacionService`); el presenter no referencia `AppModel`.

**Fuera de alcance de B5 (resumen; motivación detallada en la skill):**

| Fuera de alcance | Motivo breve |
|------------------|--------------|
| Borrar en bloque los delegadores de `AppModel` | Solo poda método a método con `rg` sin consumidores |
| Bitácora sin delegadores en `AppModel` | Resolución vía `PilaService` / `planning_facade`; ver `ui_dialog_dependency_wiring` |
| Mover señales Qt fuera de `AppModel` | Decisión de arquitectura; sería otra tarea |
| `get_dashboard_stats` y orquestación multi-servicio | Rediseño de caso de uso, no alcance B5 |
| Sustituir todo el bootstrap por DI puro | `StartupController` sigue compuesto desde el modelo |
| Más widgets con DI explícito | Opcional; órdenes/gráficas ya reciben `report_service` desde `ReportesWidget` |

**Trabajo futuro** (no es B5): podas puntuales de `AppModel`, nuevos widgets con DI desde el inicio, o ampliar `ui_dialog_dependency_wiring` según su REGISTRO.

---

---

## Orden de Ejecución Recomendado

```
A1 → A2 → B1 → B2 → B3 → B4 → B4.5 → B5 → C1 → C2 → C3 → C4 → C5 → C6
```

**Justificación:**
1. **A1** primero porque la limpieza es zero-risk y desbloquea una raíz limpia para empaquetado.
2. **A2** segundo porque es un cambio pequeño y necesario antes de producción.
3. **B1-B5** antes de Windows porque son refactorizaciones que mejoran la mantenibilidad del código que se va a desplegar.
4. **C1-C6** al final porque requieren acceso a un PC Windows real.

---

## Skills de Referencia Completa

| Skill | Propósito | Cuándo leerla |
|-------|-----------|---------------|
| `.agents/skills/limpieza_proyecto/SKILL.md` | Eliminar archivos residuales | Tarea A1 |
| `.agents/skills/migracion_mixins_composicion/SKILL.md` | Migrar mixins a composición | Tareas B1-B4 |
| `.agents/skills/reduccion_god_objects/SKILL.md` | Reducir AppModel facade | Tarea B5 |
| `.agents/skills/preparacion_windows/SKILL.md` | Validación Windows + empaquetado | Tareas C1-C6 |
| `.agents/skills/ui_pyqt_layout_freezes/SKILL.md` | Prevenir freezes de UI en Qt | Siempre (Bloque D) |
| `.agents/skills/plan_mejora_calidad/SKILL.md` | Hub de calidad de tests | Referencia de calidad |
| `.agents/skills/strict_testing/SKILL.md` | Estándares de tests | Al escribir tests nuevos |
| `.agents/skills/testing_por_capa/SKILL.md` | Qué testear por capa | Al escribir tests nuevos |
| `.agents/skills/testing_fixtures_y_mocks/SKILL.md` | Mocks y fixtures correctos | Al escribir tests nuevos |
| `.agents/skills/testing_pyqt6_headless/SKILL.md` | Testear widgets Qt | Tests de UI |
| `.agents/skills/testing_antipatrones/SKILL.md` | Antipatrones a evitar | Al revisar tests |
| `.agents/skills/estandar_documentacion/SKILL.md` | Docstrings y docs | Paso 5 del protocolo |
| `.agents/skills/fase12c_sanear_frontera_ui/SKILL.md` | Frontera UI/DTO | Mantenimiento |

---

## Métricas de Referencia (baseline antes de empezar)

| Métrica | Valor actual |
|---------|-------------|
| Tests pasando | 225/225 (100%) |
| Cobertura media | 98,5% |
| Score calidad tests | 77,6/100 |
| Archivos en techo | 201/201 |
| MagicMock sin spec | 335 (inevitables) |
| TODOs funcionales | 1 |
| Archivos .bak_monolith | 10 (eliminar con A1) |
| Mixins tipo A (fragmentadores) | 14 (migrar con B1-B4) |
| Métodos delegadores AppModel | ~148 (B5 cerrado: acceso directo donde aplica; poda solo sin consumidores) |

---

## Reglas Estrictas (SIEMPRE ACTIVAS)

1. **Antes de cada tarea:** ejecutar `pytest tests/ -x -q --timeout=30`. Si hay fallos, PARAR y arreglar.
2. **Después de cada tarea:** ejecutar la suite completa + mypy. Si hay fallos, ARREGLAR antes de marcar como completada.
3. **Código nuevo requiere tests nuevos.** No se acepta código sin coverage.
4. **La documentación se actualiza en CADA paso**, no al final del bloque.
5. **El score de calidad no puede bajar.** Si un refactor introduce una regresión en el analizador, corregir.
6. **Español** para todos los docstrings, comentarios e informes.
7. **Una tarea a la vez.** No paralelizar tareas de diferentes bloques.
8. **Las skills se actualizan** al completar cada tarea (marcar `[x]` en la skill específica + en esta tabla).

---

## Última Actualización

- **Fecha:** 2026-04-04
- **Estado:** Bloque B completo (incl. B5). Siguiente prioridad: **C1** (paths Windows).
- **Próxima tarea:** C1 — Auditar paths del sistema de archivos para compatibilidad Windows
