# Plan de Acción Técnico — Proyecto Hipatia

> Última actualización: 2026-03-15
> Fuente de verdad operativa: `.agents/skills/plan_mejora_calidad/SKILL.md`

---

## Estado Actual

| Métrica | Baseline (14-Mar) | Hoy (15-Mar) | Objetivo |
|---------|-------------------|--------------|----------|
| Score absoluto medio | 34.1 | 38.0 | 80 |
| Score optimizado medio | — | 41.4 | 80 |
| Tests sin assert | 583 | 433 | 0 |
| Cobertura global | 88.2% | 97.3% | 90% |
| Archivos en techo | — | 66/201 | 201/201 |
| Archivos fallando | — | 0 | 0 |

---

## Fases

| Fase | Nombre | Estado |
|------|--------|--------|
| 1 | Corrección de Tests Críticos | ✅ COMPLETADA |
| **2** | **Eliminación de Antipatrones de Testing** | **🔴 EN PROGRESO** |
| 3 | Refactorización de Archivos Monolíticos | 🟠 PENDIENTE |
| 4 | Corrección de Código Legacy | 🟡 PENDIENTE |
| 5 | Corrección de Errores Mypy | 🟡 PENDIENTE |
| 6 | Configuración de CI/CD | 🟡 PENDIENTE |
| 7 | Documentación Técnica de Arquitectura | 🟢 PENDIENTE |

---

## Fase 2 — Progreso detallado

**Grupo A (≥+30 pts):** 11/11 archivos completados ✅
**Grupo B (≥+20 pts):** 0/6 archivos completados — siguiente a trabajar
**Grupo C (+5-18 pts):** 0/6 archivos completados
**Grupo D (en techo, antipatrones menores):** pendiente
**Grupo E (reescritura completa):** pendiente

Próximos archivos a trabajar (Grupo B):
1. `tests/unit/test_session_controller_comprehensive.py` — score 3 → 33
2. `tests/unit/test_simulation_controller_comprehensive.py` — score 0 → 30
3. `tests/unit/test_features_worker_controller.py` — score 0 → 25
4. `tests/unit/test_settings_widget.py` — score 3 → 23
5. `tests/unit/test_report_controller_comprehensive.py` — score 3 → 23

---

## Fases Pendientes — Resumen

**Fase 3 — Refactorización Monolíticos**
Dividir archivos >400 LOC en componentes más pequeños.
Candidatos principales: `pila_controller.py`, `calculate_times_widget.py`, `settings_widget.py`.

**Fase 4 — Código Legacy**
Reemplazar `print` por `logger`, `bare except` por `except Exception`, añadir type hints.
~50 archivos afectados.

**Fase 5 — Errores Mypy**
127 líneas con errores en modo strict. Empezar por `core/`.

**Fase 6 — CI/CD**
Configurar GitHub Actions para ejecutar `run_tests.py` en cada push.

**Fase 7 — Documentación Técnica**
Generar diagramas de arquitectura y documentar decisiones de diseño.

---

## Referencias

- Plan operativo completo: `.agents/skills/plan_mejora_calidad/SKILL.md`
- Backlog priorizado: `.agents/skills/backlog_tests/SKILL.md`
- Historial de fases: `Documentacion/Mejora_Calidad/`
- Análisis inicial del proyecto: `Documentacion/Analisis_Inicial/`
