---
name: Refactorización Pre-Tipado (MCP)
description: Plan de refactorización pre-tipado — **cerrado** (2026-03-20). Historial de fases 0–13, herramientas y skills de mantenimiento. Lee al orientar trabajo en legacy, UI/DTO o calidad.
---

# MCP: Master Control Plan — Refactorización Pre-Tipado Estricto

> **⚠️ INSTRUCCIÓN CRÍTICA PARA LA IA:**
> Este documento es la **Única Fuente de Verdad** del estado de la refactorización.
> Al iniciar **cualquier** sesión de trabajo, **LEE ESTE DOCUMENTO PRIMERO**.
> El **plan de fases numeradas está cerrado** (2026-03-20). Para un tema concreto, abre la skill que aplique (`fase_legacy`, `strict_testing`, `fase12c_sanear_frontera_ui` para mantenimiento del catálogo, etc.) y la documentación en `Documentacion/Refactorizacion_Completa/`.

---

## 🧭 Estado Actual del Proyecto

* **Plan MCP (fases 0–13):** ✅ **Cerrado** (2026-03-20). **No hay fase activa.** Criterios finales: mypy global en verde, `run_tests.py` en verde, catálogo UI/DTO estricto en 0.
* **Última auditoría:** 2026-03-20 — cierre 12C + suite completa en verde
* **Cobertura Global:** 97.4%
* **Tests:** ✅ suite completa PASSED (`python3 run_tests.py`)
* **Estado de Mypy:** ✅ `python3 -m mypy . --config-file mypy.ini` sin errores (Fase 7 cerrada)
* **Tipado Estricto:** ✅ ACTIVO
---

## 📋 Mapa de Fases y Estado

| Fase | Skill | Estado | Descripción |
|------|-------|--------|-------------|
| **0** | _(eliminado)_ | ✅ COMPLETADA | Crear `__init__.py`, actualizar `mypy.ini`, obtener baseline mypy |
| **1** | _(eliminado)_ | ✅ COMPLETADA | Eliminar `bare except`, migrar `print()` a logging, limpiar archivos basura |
| **2** | _(eliminado)_ | ✅ COMPLETADA | Romper 9 ciclos de dependencias circulares detectados |
| **3** | _(eliminado)_ | ✅ COMPLETADA | Dividir 14 archivos monolíticos (>500 LOC) |
| **4** | _(eliminado)_ | ✅ COMPLETADA | Configurar mypy estricto gradual, tipado bottom-up |
| **5** | _(eliminado)_ | ✅ COMPLETADA | Tipado estricto de 21 controllers con ciclo test-first |
| **6** | _(eliminado)_ | ✅ COMPLETADA | Tipado estricto de la capa Visual (UI) y fragmentación UI |
| **7** | _(skill eliminada)_ | ✅ COMPLETADA | Resolución de errores residuales de Mypy (auditoría global en verde) |
| **8** | `fase_legacy` / `fase_legacy_autopilot` | ✅ COMPLETADA | Código legacy abordado en el marco del Plan Mejora (Fase 4); sin bloqueos MCP pendientes |
| **9** | _(eliminado)_ | ✅ COMPLETADA | Limpieza de deuda técnica (Core, Business, UI, Entry) |
| **10A** | _(eliminado)_ | ✅ COMPLETADA | Extraer WorkerService de FabricacionService |
| **10B** | _(eliminado)_ | ✅ COMPLETADA | Extraer MachineService de FabricacionService |
| **10C** | _(eliminado)_ | ✅ COMPLETADA | Extraer PreparationService de FabricacionService |
| **10D** | _(eliminado)_ | ✅ COMPLETADA | Consolidación: AppModel delega a 7 servicios |
| **11A** | *(eliminado)* | ✅ COMPLETADA | Redirigir accesos directos a repos en controllers |
| **11B** | *(eliminado)* | ✅ COMPLETADA | Extraer TrackingAssignmentService |
| **11C** | *(eliminado)* | ✅ COMPLETADA | Verificación final y limpieza de accesos legacy |
| **12A** | `fase12a_puenteo_directo` | ✅ COMPLETADA | Inyectar servicios directo en controllers |
| **12B** | `fase12b_mixins_a_gestores` | ✅ COMPLETADA | Convertir Mixins de controllers en Gestores (Worker y Product OK) |
| **12C** | `fase12c_sanear_frontera_ui` / `fase12c_autopilot_production_flow_refactor` | ✅ COMPLETADA | Frontera UI/DTO: catálogo estricto en 0; lecturas/mutaciones en `core/*_io.py` y contratos tipados en rutas críticas |
| **13** | `fase13_escalado_ui` | ✅ COMPLETADA | Implementación de Escalado Dinámico UI y Botones Auto-Ajustar |

---

## 🔎 Herramientas de análisis

**Monolitos/dependencias:**

```bash
python3 scripts/monolith_analyzer.py --min-loc 250 --top 30
```

Salida: `Documentacion/Refactorizacion_Completa/Monolitos/monolith_report.{md,json}`. Skill: `.agents/skills/fase_monolitos_autopilot/SKILL.md`.

**Código legacy (Fase 4 / Fase 8):**

```bash
python3 scripts/legacy_analyzer.py
```

Salida: `Documentacion/Refactorizacion_Completa/Legacy/legacy_report.{md,json}`. Skills: `.agents/skills/fase_legacy/SKILL.md`, `.agents/skills/fase_legacy_autopilot/SKILL.md`.

---

## 🔄 Flujo de Trabajo Cíclico Estricto (OBLIGATORIO)

Cada vez que se trabaje en una fase, se **DEBE** seguir este ciclo **completo** y en **orden**:

### Paso 1: Preparación
1. **Leer este MCP** — Confirmar alcance (plan cerrado) o identificar la skill del tema si se abre trabajo nuevo
2. **Leer la skill aplicable** — Instrucciones detalladas por tema (`fase_legacy`, testing, catálogo UI/DTO, etc.)
3. **Leer la documentación** en `Documentacion/Refactorizacion_Completa/` — Ver informes anteriores
4. **Analizar el código** — Confirmar el estado actual del codebase relevante

### Paso 2: Planificación
5. **Generar informe pre-fase** — Documento markdown detallando qué se va a hacer y cómo
6. **Guardar el informe** en `Documentacion/Refactorizacion_Completa/` con nombre `informe_fase{N}_pre.md`
7. **Pedir aprobación al usuario** — No ejecutar sin aprobación

### Paso 3: Ejecución
8. **Ejecutar los cambios** — Siguiendo las instrucciones de la skill de fase
9. **Restricción:** Máximo **2-3 archivos** de código base modificados a la vez
10. **Restricción:** Prohibido tipado prematuro en archivos no divididos

### Paso 4: Documentación Post-Ejecución
11. **Generar informe post-fase** — Markdown explicando:
    - ✅ Qué se hizo exactamente
    - 🔧 Cómo se hizo (técnicas, patrones aplicados)
    - ⚠️ Problemas encontrados
    - 🛠️ Cómo se solucionaron los problemas
12. **Guardar** en `Documentacion/Refactorizacion_Completa/` con nombre `informe_fase{N}_post.md`

### Paso 5: Tests
13. **Ejecutar la suite completa de tests:** `pytest`
14. **Si algún test falla** → Corregir hasta que TODOS pasen. **Máxima prioridad.**

### Paso 6: Cobertura y Calidad
15. **Verificar cobertura** de los archivos modificados → Debe ser **100%**
16. **Si no es 100%** → Crear/mejorar tests hasta alcanzarlo
17. **Verificar calidad de tests** → Consultar skills `strict_testing` + `testing_antipatrones` + `testing_fixtures_y_mocks` + `testing_por_capa` + `testing_pyqt6_headless` → Score medio real debe ser **≥ 80**
18. **Si score < 80** → Rediseñar tests aplicando las skills de testing hasta cumplir
19. **Verificar antipatrones** → Ejecutar `python3 run_tests.py` y revisar la sección "ANTIPATRONES DETECTADOS". Si hay valores > 0 en cualquier categoría, corregirlos antes de continuar.

### Paso 7: Cierre
19. **Notificar al usuario** — Presentar resultado con informe post-fase
20. **Si el usuario aprueba:**
    - Marcar la fase como `[x]` completada en este MCP
    - Actualizar el estado actual (`Fase Actual`, `Estado de Mypy`, etc.)
    - Si hay nuevo trabajo temático → Volver al **Paso 1** con la skill que corresponda (el plan de fases numeradas ya está cerrado)

---

## 📁 Ubicaciones Importantes

| Recurso | Ruta |
|---------|------|
| **Este MCP** | `.agents/skills/refactorizacion_mcp/SKILL.md` |
| **Skills de fases** | `.agents/skills/fase{N}_*/SKILL.md` |
| **Plan de Mejora de Calidad** | `.agents/skills/plan_mejora_calidad/SKILL.md` |
| **Testing — reglas generales** | `.agents/skills/strict_testing/SKILL.md` |
| **Testing — antipatrones y falsos positivos** | `.agents/skills/testing_antipatrones/SKILL.md` |
| **Testing — fixtures y mocks** | `.agents/skills/testing_fixtures_y_mocks/SKILL.md` |
| **Testing — por capa** | `.agents/skills/testing_por_capa/SKILL.md` |
| **Testing — PyQt6 headless** | `.agents/skills/testing_pyqt6_headless/SKILL.md` |
| **Documentación central** | `Documentacion/Refactorizacion_Completa/` |
| **Informe de auditoría** | `Documentacion/Refactorizacion Pre-Tipado/informe_auditoria_pre_tipado_estricto.md` |
| **Guía de referencia mypy** | `Documentacion/Mypy tipado/guia_referencia.md` |
| **Plan original de tipado** | `Documentacion/Mypy tipado/plan_implementacion.md` |
| **Config mypy** | `mypy.ini` |

---

## 🛑 Reglas Estrictas (SIEMPRE ACTIVAS)

1. **Máximo 2-3 archivos** de código base modificados por iteración
2. **Prohibido tipado prematuro** en archivos monolíticos (Fase 3 primero)
3. **Prohibido `print()` nuevo** — Solo `logging`
4. **Prohibido `except:`** desnudo — Siempre `except Exception as e:` con logging
5. **100% tests passing** antes de marcar una tarea como completada
6. **100% cobertura** en archivos modificados
7. **100% compliance** de calidad de tests (skill `strict_testing`)
8. **Informes obligatorios** — Pre y post fase, siempre guardados en documentación
