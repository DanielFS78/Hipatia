# Documentación — Plan de Mejora de Calidad

Este directorio centraliza el **plan de mejora de calidad** y la evidencia verificable
de su ejecución (tests, tipado estricto, refactors y documentación).

- Estado operativo actual: `.agents/skills/plan_mejora_calidad/SKILL.md`.
- Analizador de calidad de tests: `scripts/test_quality_analyzer.py`.
- Datos estructurados del analizador (fuente del dashboard): `test_reports/compliance_data.json`.

---

## Estado de Fases

| Fase | Nombre | Estado | Informe |
|------|--------|--------|---------|
| 1 | Corrección de Tests Críticos | ✅ COMPLETADA | `fase1_pre.md`, `fase1_post.md`, `fase1b_post.md` |
| **2** | **Eliminación de Antipatrones** | **✅ COMPLETADA** | `fase2_pre.md`, `fase2_lote5_final.md`, `fase2_lote6.md`, `fase2_post_completo.md`, `informe_en_progreso_a_actualizado.md` |
| A | Cierre Fase A (subfase de 2) | ✅ COMPLETADA | `fase_A_completada.md` |
| — | **Listado orden de trabajo** | — | `listado_tests_orden_trabajo.md` (188 archivos, más trabajo primero) |
| 3 | Refactorización Monolíticos | 🟠 PENDIENTE | — |
| 4 | Código Legacy | 🟡 PENDIENTE | — |
| 5 | Errores Mypy | 🟡 PENDIENTE | — |
| 6 | CI/CD | 🟡 PENDIENTE | — |
| 7 | Documentación Técnica | 🟢 PENDIENTE | — |

---

## Métricas de Progreso

| Fase | Score antes | Score después | Cobertura |
|------|-------------|---------------|-----------|
| Baseline | 34.1 | — | 88.2% |
| Fase 1 | 34.1 | 34.9 | 96.8% |
| Fase 2 (cerrada) | 34.9 | 76.5 (abs) / 78.8 (opt) | 97.4% |

---

## Calidad “de verdad”: tests + tipado estricto

En Hipatia se busca **excelencia** combinando:

- **Tests profesionales** (mocks estrictos, asserts de interacción, fixtures sólidas, sin falsos positivos).
- **Tipado estricto con MyPy** (incluyendo `tests/`, sin ignorarlos).

La combinación es potente: MyPy reduce “zonas grises” en tests (mocks que engañan),
y los tests protegen de refactors por tipado que podrían romper comportamiento.

---

## Cómo ejecutar el analizador de calidad de tests

El script `scripts/test_quality_analyzer.py` recorre `tests/` y aplica una puntuación
real basada en patrones detectables (no opiniones).

Ejecución:

```bash
python3 scripts/test_quality_analyzer.py
```

Salida:
- Resumen por categorías (**Actualizados**, **En Progreso**, **Legacy/Pendiente**).
- Media de score absoluto y “optimizado”.
- Listado de archivos en su **techo real** (ver siguiente sección).
- Lista de **penalizaciones corregibles**.
- Escritura de datos estructurados en `test_reports/compliance_data.json`.

---

## Cómo interpretar el “techo real” (muy importante)

El analizador reporta dos valores:

- **Score absoluto**: lo que tiene el archivo ahora mismo.
- **Score optimizado**: score estimado si se corrigen penalizaciones corregibles,
  respetando límites de dependencias reales.

El “techo real” existe porque hay dependencias sin stubs de tipo o APIs dinámicas.
Ejemplos típicos:

- **PyQt6**: widgets y señales sin stubs completos → en tests a veces es inevitable
  usar `MagicMock` o instancias reales `QWidget()` para satisfacer C++.
- **python-docx**: objetos sin stubs → algunos mocks no pueden ser completamente
  autospecced.
- **Parches a `builtins`/Qt/OS**: `autospec=True` no siempre aplica (y forzarlo puede
  producir falsos negativos o tests frágiles).

Por eso el objetivo profesional no es “100/100 a cualquier coste”, sino:

- **Maximizar score dentro del techo real**.
- **Evitar antipatrones que generan falsos positivos** (ver `testing_antipatrones`).

---

## Flujo operativo recomendado (por lotes, seguro)

Regla: **un lote pequeño**, evidencia, y solo entonces avanzar.

1. Ejecutar MyPy global:

```bash
python3 -m mypy . --config-file mypy.ini --show-error-codes
```

2. Elegir un lote de 1–3 archivos con errores o penalizaciones corregibles.
3. Corregir siguiendo estándares:
   - Mocks estrictos: `create_autospec(..., instance=True)` o `MagicMock(spec=...)`.
   - `@patch(..., autospec=True)` salvo whitelist explícita (builtins/Qt/OS).
   - En controllers/services: siempre algún `assert_called_*`.
   - Evitar `assert True` salvo smoke test justificado.
4. Ejecutar tests focales:

```bash
python3 -m pytest <ruta/al/test.py> -q
```

5. Ejecutar `pytest` completo antes de cerrar el lote:

```bash
python3 -m pytest -q
```

6. Ejecutar el analizador de calidad y verificar que sube o queda en techo real:

```bash
python3 scripts/test_quality_analyzer.py
```

7. Documentar decisiones (por qué el techo real aplica, por qué un mock no puede ser autospecced, etc.).

---

## Fuentes de verdad (documentación y reglas)

- Reglas estrictas: `.agents/skills/strict_testing/SKILL.md`
- Antipatrones/falsos positivos: `.agents/skills/testing_antipatrones/SKILL.md`
- Fixtures y mocks correctos: `.agents/skills/testing_fixtures_y_mocks/SKILL.md`
- Tipado estricto (Mypy): `Documentacion/Refactorizacion_Completa/Mypy_Stricto/README.md`
