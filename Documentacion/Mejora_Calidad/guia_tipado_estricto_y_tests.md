# Guía práctica: Tipado estricto + Tests profesionales (Hipatia)

Esta guía explica, de forma reproducible, cómo se alcanza la excelencia en Hipatia combinando:

- **MyPy estricto** (incluyendo `tests/`) para eliminar errores silenciosos y contratos ambiguos.
- **Tests profesionales** para prevenir regresiones reales, evitando falsos positivos causados por mocks débiles.

El objetivo no es “hacer pasar” herramientas, sino **reducir el riesgo**: que el test falle cuando el sistema está roto.

---

## 1) Principios (por qué funciona)

### 1.1 MyPy hace que los tests no “mientan”

Muchos falsos positivos nacen de esto:
- tratar una función real como si fuese un mock (acceder a `.call_count`, `.return_value`, etc.);
- asignar a métodos (antipatrón típico) para espiar llamadas;
- usar estructuras `object`/`Any` que hacen que un test “parezca correcto” pero no valida nada.

Con MyPy estrictamente aplicado a `tests/`, estos problemas se vuelven **errores visibles** antes de ejecutar.

### 1.2 Los tests hacen que el tipado no rompa comportamiento

El tipado estricto empuja a refactors conservadores (casts, `Optional`, Protocols).
Los tests garantizan que esos cambios no degradan el sistema.

---

## 2) Flujo operativo recomendado (lote pequeño y evidencia)

### 2.1 Preparación

- Asegurar que `mypy.ini` no ignora `tests/`.
- Trabajar con cambios pequeños (1–3 archivos).

### 2.2 Iteración (loop)

1) **MyPy global** (para listar el backlog real):

```bash
python3 -m mypy . --config-file mypy.ini --show-error-codes
```

2) Elegir un lote pequeño de archivos. Prioridad:
- `method-assign`, `attr-defined`, `union-attr`, `call-arg` en tests de controladores/servicios.
- fixtures (`tests/conftest.py`) porque afectan a toda la suite.
- integración/e2e donde suelen aparecer `object is not indexable` por falta de anotaciones.

3) Corregir siguiendo reglas estrictas (ver sección 3).

4) **MyPy focal** (solo el lote):

```bash
python3 -m mypy tests/path/al_archivo.py --config-file mypy.ini --show-error-codes
```

5) **Pytest focal**:

```bash
python3 -m pytest tests/path/al_archivo.py -q
```

6) **Pytest global** antes de cerrar lote:

```bash
python3 -m pytest -q
```

7) **Analizador de calidad de tests** (score real y penalizaciones):

```bash
python3 scripts/test_quality_analyzer.py
```

8) Documentar decisiones:
- por qué un mock no puede ser autospecced (techo real);
- por qué se usa `cast(Any, ...)` en un punto concreto;
- cómo se evitó un falso positivo.

---

## 3) Reglas prácticas (lo que se acepta y lo que no)

### 3.1 Prohibido: mocks sueltos para clases del proyecto

Evitar `MagicMock()` / `Mock()` sin `spec` para Services/Controllers/Repos del proyecto.
Usar:
- `create_autospec(Clase, instance=True)` (preferido)
- `MagicMock(spec=Clase)` (cuando autospec no es viable)

### 3.2 Parches: `autospec=True` por defecto

Regla general:
- `@patch("...", autospec=True)`

Excepciones típicas (techo real):
- `builtins.open`, diálogos Qt, `os/shutil/platform`, u objetos sin stubs fiables.

### 3.3 Espiar llamadas sin `method-assign`

No asignar a métodos:

```python
# ❌ NO
controller.initialize = MagicMock(wraps=controller.initialize)
```

Sí usar `patch.object(..., wraps=...)`:

```python
with patch.object(controller, "initialize", wraps=controller.initialize) as init_spy:
    controller.initialize()
    init_spy.assert_called_once_with()
```

### 3.4 `cast(Any, ...)` solo en el punto de frontera

Cuando el tipo está declarado como `Callable[...]` pero en runtime es un Mock,
usar `cast(Any, ...)` **solo** para acceder a `.call_count`, `.call_args`, `.return_value`.

Esto mantiene:
- tipado estricto global
- y asserts reales de interacción.

### 3.5 Anotar estructuras dinámicas en integración/e2e

Si una lista/dict es “de negocio” pero se construye inline, anotar:

```python
canvas_tasks: list[dict[str, Any]] = [...]
```

Evita errores como “Value of type `object` is not indexable” y mejora legibilidad.

---

## 4) Cómo interpretar el analizador de calidad (`test_quality_analyzer.py`)

El analizador calcula:
- **Score absoluto**: estado actual.
- **Score optimizado**: potencial si se corrigen penalizaciones corregibles.
- **Techo real**: límites por dependencias inevitables (PyQt6, docx, etc.).

Datos:
- `test_reports/compliance_data.json` contiene el detalle por archivo y métricas.

Objetivo profesional:
- Maximizar score **sin** introducir fragilidad.
- Evitar antipatrones que permiten falsos positivos.

---

## 5) Referencias internas del proyecto

- Reglas de testing: `.agents/skills/strict_testing/SKILL.md`
- Antipatrones de tests: `.agents/skills/testing_antipatrones/SKILL.md`
- Fixtures y mocks: `.agents/skills/testing_fixtures_y_mocks/SKILL.md`
- Tipado estricto: `Documentacion/Refactorizacion_Completa/Mypy_Stricto/README.md`

