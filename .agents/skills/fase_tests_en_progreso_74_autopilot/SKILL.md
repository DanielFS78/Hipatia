---
name: Autopilot — Subir “En Progreso” a “Actualizado”
description: Agente autónomo para procesar en bucle los tests en estado “En Progreso” del dashboard hasta que no quede ninguno. Conservador, sin preguntas, siempre verde (mypy+pytest) y documentación en español.
---

# [ARCHIVO — no usar como backlog activo] Autopilot — Subir “En Progreso” a “Actualizado” (Dashboard)

## Objetivo

Procesar automáticamente todos los archivos de test en estado **“En Progreso”** (según `scripts/test_quality_analyzer.py`) hasta que:

- `En Progreso = 0`, y
- `Legacy / Pendiente = 0`, y
- **MyPy global = 0 errores**, y
- **Pytest global = 0 fallos**.

## Fuente de verdad del backlog

- Generar backlog (OBLIGATORIO antes de empezar):

```bash
python3 scripts/test_quality_analyzer.py
python3 scripts/extract_test_quality_in_progress.py
```

El backlog resultante está en:
- `Documentacion/Mejora_Calidad/backlog_tests_en_progreso.md`
- `.agents/skills/backlog_tests_en_progreso/SKILL.md`

## Reglas estrictas (conservadoras)

1. **Nunca romper la suite**: tras cada cambio, `pytest` debe permanecer verde.
2. **No bajar score**: nunca aceptar una corrección que baje score de archivo o del promedio.
3. **Cambios pequeños**: 1 archivo por iteración (máximo 1–2 si son triviales y acoplados).
4. **No tocar producción para “hacer pasar”**: solo tests y su infraestructura.
5. **Mocks profesionales**:
   - Clases del proyecto: `create_autospec(Clase, instance=True)` o `MagicMock(spec=[...])`.
   - Qt: evitar autospec; usar widgets reales cuando C++ lo exija.
6. **Patches**:
   - `autospec=True` siempre salvo whitelist (Qt/builtins/OS).
7. **Asserts de interacción**:
   - En ctrl/serv: siempre algún `assert_called_*`.
   - Antes de `assert_called_*` incluir `assert call_count ...` para cumplir el analizador.
8. **Docstrings en español**: no añadir ruido; explicar intención y límites (techo real).

## Bucle autónomo (paso a paso)

Repetir hasta `En Progreso = 0`:

1. **Regenerar backlog**:

```bash
python3 scripts/test_quality_analyzer.py
python3 scripts/extract_test_quality_in_progress.py
```

2. **Elegir el siguiente archivo**:
   - Tomar el primero de `.agents/skills/backlog_tests_en_progreso/SKILL.md` con Estado `—`.
   - Si hay empates, priorizar por penalización corregible total (más negativa) y por riesgo bajo.

3. **Analizar qué penalizaciones corregibles tiene**:
   - `loose_mocks`, `tests_without_assert`, `patches_no_autospec`, `assert_called_no_args`, `mock_session`, `spec_object`.
   - Determinar la corrección mínima que suba score sin fragilidad.

4. **Aplicar correcciones** (solo ese archivo):
   - Ajustar mocks, patches, asserts, anotaciones mínimas si MyPy lo requiere.
   - Evitar cambios cosméticos.

5. **Validación obligatoria**:

```bash
python3 -m mypy <archivo> --config-file mypy.ini --show-error-codes
python3 -m pytest <archivo> -q
python3 -m pytest -q
python3 scripts/test_quality_analyzer.py
```

6. **Actualizar backlog**:
   - Regenerar backlog con `extract_test_quality_in_progress.py`.
   - En `.agents/skills/backlog_tests_en_progreso/SKILL.md` marcar ✅ el archivo si:
     - ya no está en “En Progreso”, o
     - el analizador indica techo real y no quedan penalizaciones corregibles.

7. **Continuar** con el siguiente archivo.

## Cierre (cuando ya no quede ninguno)

1. Ejecutar y capturar estado final:

```bash
python3 -m mypy . --config-file mypy.ini --show-error-codes
python3 -m pytest -q
python3 scripts/test_quality_analyzer.py
python3 scripts/generate_daniel_doc.py
```

2. Actualizar documentación en español:
   - `Documentacion/Mejora_Calidad/README.md` (métricas actuales)
   - `Documentacion/Mejora_Calidad/backlog_tests_en_progreso.md` (debe quedar vacío o histórico)
   - Incluir un informe final en `Documentacion/Mejora_Calidad/informe_en_progreso_a_actualizado.md`

