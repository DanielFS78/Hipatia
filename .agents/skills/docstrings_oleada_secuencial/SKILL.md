---
name: Docstrings oleada secuencial
description: Protocolo para cerrar docstrings de módulo (`Nombre del Módulo` + `Descripción`) un archivo por iteración, con cola, registro y gates; alineado con Daniel y estandar_documentacion.
---

# Docstrings oleada secuencial (Hipatia)

## Cuándo usarla

- El usuario pide **continuar la oleada de docstrings**, **cerrar módulos sin documentar**, o **verificar cobertura** del bloque estándar de módulo.
- Tras **grandes merges** o nuevos `.py` en `controllers/`, `core/`, `database/`, `features/`, `ui/`, `scripts/`, `tools/`, `migrations/`.

## Fuentes de verdad (orden)

1. [`.agents/skills/estandar_documentacion/SKILL.md`](../estandar_documentacion/SKILL.md) — formato obligatorio del docstring de módulo.
2. [`Documentacion/OLEADA_DOCSTRINGS_COLA.md`](../../../Documentacion/OLEADA_DOCSTRINGS_COLA.md) — cola ordenada (regenerable). Si **Total pendientes: 0**, el cierre global está al día; solo hace falta mantener nuevos archivos.
3. [`Documentacion/REGISTRO_DOCSTRINGS_MODULO.md`](../../../Documentacion/REGISTRO_DOCSTRINGS_MODULO.md) — bitácora de cierres (gates, fechas). No mezclar con `REGISTRO_EJECUCION_ITEMS` de calidad P0–P3.

## Inventario y cola

```bash
python3 scripts/docstrings_queue.py
python3 scripts/docstrings_queue.py --write
python3 scripts/docstrings_queue.py --fail-on-missing
```

- `--write` regenera la cola Markdown con checkboxes.
- `--fail-on-missing` devuelve **exit 1** si queda algún archivo del alcance sin `Nombre del Módulo` en los primeros 8000 bytes (útil en CI).

## Calidad de la `Descripción` (obligatorio)

La `Descripción` debe decir **qué hace el código** en **1–2 frases**, no rotular el fichero.

- Mencionar al menos uno: datos que define, **clases o protocolos** públicos, **servicios o repos** delegados, o efecto observable (CLI, migración, UI).
- **Prohibido** titular vacío («Módulo de…», «utilidades del núcleo», «piezas de dominio», «ver implementación», texto que solo repite el nombre del archivo).
- Tras leer imports y tipos de nivel superior, si el texto sigue siendo pobre, **editar a mano** (no basta con plantillas).

### Auditor y refino automático (asistido)

```bash
python3 scripts/audit_module_description_quality.py
python3 scripts/audit_module_description_quality.py --fail-on-issues
python3 scripts/refine_module_descriptions.py --dry-run
python3 scripts/refine_module_descriptions.py
python3 scripts/refine_module_descriptions.py --path controllers/ejemplo.py
```

- El **auditor** escribe [`reports/module_description_quality.md`](../../../reports/module_description_quality.md) y puede fallar en CI con `--fail-on-issues`.
- El **refinador** sustituye solo el párrafo `Descripción:` conservando `Nombre del Módulo`; es heurístico: **revisar** módulos críticos o muy algorítmicos a mano tras ejecutarlo.

[`scripts/bootstrap_module_docstrings.py`](../../../scripts/bootstrap_module_docstrings.py) **no** sustituye narrativa final: si no hay buen párrafo previo, deja instrucciones explícitas para refinar; no reintroducir frases genéricas de dominio.

## Protocolo por iteración (un solo archivo)

1. Leer la cola y el registro; elegir el **primer** `- [ ]` pendiente (o el archivo que indique el usuario si es corrección puntual).
2. Editar **solo ese** `.py`: añadir o mejorar `Nombre del Módulo` + `Descripción` en español; quitar ruido obsoleto solo si es inequívoco en el mismo fichero.
3. **Gates** tras el cambio:
   - `python3 -m py_compile <ruta>`
   - Tests focalizados si existen (`pytest` sobre tests relacionados).
   - Cada **10–15** archivos tocados en la sesión, o al cerrar una oleada: `python3 scripts/generate_daniel_doc.py`.
4. Marcar `- [x]` en la cola y añadir una fila al **REGISTRO** con fecha, archivo y comandos ejecutados.
5. Si un gate falla, **no** marcar hecho; corregir y repetir.

## Bootstrap mecánico (solo si hace falta)

Para **rehidratar** muchos módulos a la vez (p. ej. tras importar código sin docstring), existe ayuda conservadora:

```bash
python3 scripts/bootstrap_module_docstrings.py --dry-run
python3 scripts/bootstrap_module_docstrings.py
python3 scripts/bootstrap_module_docstrings.py --path core/ejemplo.py
```

Revisa siempre el texto generado: puede acortar párrafos del docstring previo. Preferir edición manual cuando el módulo sea crítico o algorítmico (véase `estandar_documentacion`).

## Duplicados `* 2.py` / `* 3.py`

Son copias típicas de Finder/iCloud: antes de masificar cambios, comprobar que **no** existan imports al duplicado y eliminarlos (`find . -name '* 2.py'`).

## Relación con otras skills

- **No** sustituye a [ejecucion_secuencial_calidad](../ejecucion_secuencial_calidad/SKILL.md): aquí no se exige mypy global por archivo salvo que el cambio toque tipos.
- Tras trabajo largo fuera del árbol iCloud, aplicar la sync descrita en ejecución secuencial si aplica al workspace del usuario.
