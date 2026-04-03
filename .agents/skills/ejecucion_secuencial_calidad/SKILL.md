---
name: Ejecucion Secuencial de Calidad
description: Flujo unico para ejecutar auditoria tecnica por items uno a uno con gates estrictos (pytest+mypy+docs), fuentes de verdad claras (REGISTRO + priorizacion), sincronizacion iCloud continua y al cierre (responsabilidad del agente), y avance controlado al siguiente item.
---

# Ejecucion Secuencial de Calidad

> **Instruccion critica para la IA**
> 1. Ejecutar exactamente **un item a la vez**.
> 2. No avanzar al siguiente item si falla cualquier gate.
> 3. Respetar el **orden de fuentes de verdad** (seccion siguiente).
> 4. Registrar cierre de cada item en `Documentacion/Refactorizacion_Completa/Auditoria_Secuencial/REGISTRO_EJECUCION_ITEMS.md`.
> 5. **Sincronizacion iCloud — trabajo del agente, no del usuario:** si el workspace es un **worktree** distinto de `HIPATIA_ICLOUD`, **tras cada lote de cambios guardados** y **de nuevo en el Paso 8**, ejecutar `python3 scripts/sync_worktree_to_icloud.py` (o el bucle `cp` manual descrito en `references/sync_icloud_continuo.md`) para replicar **todos** los archivos tocados hacia el arbol iCloud. **No** finalizar la entrega solo pidiendo al usuario que sincronice.
> 6. El **Paso 8** cierra el item: checklist completa + linea **Sync iCloud** en REGISTRO; la sync **continua** del punto 5 evita deriva entre worktree e iCloud durante la sesion.

## Fuentes de verdad (orden obligatorio)

1. **`references/priorizacion.md`** — Rubrica **P0 > P1 > P2 > P3**. Un item de mayor prioridad pendiente **no** se deja atras por conveniencia (salvo que el usuario fije otro orden por mensaje explicito).

2. **`Documentacion/Refactorizacion_Completa/Auditoria_Secuencial/REGISTRO_EJECUCION_ITEMS.md`** — Estado **vivo** del trabajo: seccion **«Siguiente item sugerido»** o el primer bloque *En progreso*. Es la referencia **principal** para saber **que toca ahora**.

3. **`Documentacion/Refactorizacion_Completa/Auditoria_Secuencial/PLAN_EJECUCION_UNO_A_UNO.md`** — **Opcional / contexto**: backlog P0–P3, evidencias (`check_typing_coverage.txt`, etc.). Puede **no existir** en algun worktree (solo en el clon principal, p. ej. iCloud). **No** sustituye al REGISTRO. Si el usuario **prohibe editar el PLAN**, el cierre del item se documenta solo en **REGISTRO** (y aqui).

**Regla anti-confusion:** El Paso 0 **no** dice «abrir el PLAN y buscar el primer pendiente». Dice: **abrir REGISTRO + aplicar priorizacion**; el PLAN solo orienta si esta presente y al dia.

## Mapa de la fase (parametros P0–P3)

| Prioridad | Que es | Scripts / gates utiles (solo lectura o verificacion) | Notas |
|-----------|--------|------------------------------------------------------|--------|
| **P0** | Arquitectura runtime: puentes/shims, **ciclos** que afectan `controllers.app_controller` | Informes bajo `scripts/analysis/` (p. ej. dependencias citados en el PLAN); no mezclar con ITEM 004 P2 | Puentes `create_dialog_compat` / `flow_dialog_bridges` ya cerrados en REGISTRO; **ciclos** pueden ser un **item aparte** (no es «un archivo» tipo mypy) |
| **P1** | Frontera UI/DTO (`dict`/`vars().get` en UI para dominio) | `python3 scripts/ui_dto_boundary_analyzer.py` — objetivo **0 hallazgos** tras tocar UI | Cerrado en REGISTRO (ITEM 001/002); re-ejecutar si el item toca `ui/` |
| **P2** | Tipado estricto por **modulo**: `disallow_untyped_defs` en `mypy.ini` + anotaciones minimas (**ITEM 004** y sucesores) | `python3 scripts/check_typing_coverage.py` — ver filtro **codigo de producto** abajo | Un **paso** = **un modulo** (o par ya acoplado en REGISTRO) + bloque `[mypy-...]` |
| **P3** | Legacy puntual: `print`, `bare except`, docstrings/comentarios legacy | `scripts/legacy_analyzer.py` si existe en el arbol | Puede mezclarse con otro item si el REGISTRO lo documenta |

**ITEM 004 (tipado P2) — definicion unica**

- **Un paso** = **un modulo Python** de produccion (ruta importable, p. ej. `core.services.worker_service`) **mas** entrada en `mypy.ini` con `disallow_untyped_defs = True` para ese modulo (mismo patron que lotes A/B/C del REGISTRO).
- **Sin** cambiar comportamiento: solo firmas / `Any` donde haga falta / `cast` puntuales.
- **Eleccion del siguiente modulo P2** si el REGISTRO no nombra uno:
  1. Ejecutar `python3 scripts/check_typing_coverage.py`.
  2. En el «Top Untyped», **ignorar** rutas bajo `scripts/`, `tools/`, `Documentacion/` (ruido del analizador AST).
  3. Priorizar prefijos: `core/`, `database/`, `ui/`, `controllers/`, `features/`.
  4. Desempate: mayor centralidad / riesgo, y **tests focales** existentes (`rg` / `pytest --collect-only`).

**Cierre de la cola P2:** No hay **N total** fijo en el PLAN; se continua mientras haya modulos de producto con deuda clara **o** el REGISTRO defina el siguiente. Opcional: parar cuando `check_typing_coverage` no liste candidatos utiles bajo los prefijos anteriores.

## Arbol iCloud (destino obligatorio)

Ruta canonica del proyecto en iCloud Drive (misma estructura relativa que el repo):

```text
${HIPATIA_ICLOUD}
```

Definicion estandar (macOS):

```bash
HIPATIA_ICLOUD="${HOME}/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion"
```

Si el workspace **ya es** ese directorio (Cursor abrio el proyecto desde iCloud), no hace falta copiar; el Paso 8 se limita a **verificar** que no queden cambios solo en otro worktree. Si se trabajo en un worktree distinto (p. ej. `.cursor/worktrees/.../xig`), **es obligatorio** `cp` (o equivalente) de **cada archivo modificado o creado** hacia `$HIPATIA_ICLOUD/<ruta relativa>` — **de forma continua durante la sesion y al cierre** (detalle: `references/sync_icloud_continuo.md`).

## Objetivo

Estandarizar el proceso completo para reducir deuda tecnica y mantener calidad estable:
- baseline reproducible,
- refactor conservador,
- gates focales y globales,
- documentacion validada,
- cierre formal del item,
- **una sola fuente de verdad en el arbol que el usuario ejecuta (`run_tests.py`, git, etc.).**

## Protocolo obligatorio por item

### Paso 0: Seleccion del item
- Leer **`references/priorizacion.md`** y **`REGISTRO_EJECUCION_ITEMS.md`** (seccion «Siguiente item sugerido» o item en progreso).
- Si existe **`PLAN_EJECUCION_UNO_A_UNO.md`** en el workspace, usarlo solo como **contexto** (no reemplaza al REGISTRO; el texto del PLAN puede estar desfasado respecto al registro).
- Definir **alcance minimo** (un modulo, un widget, un informe de ciclos, etc.) **sin mezclar** dos prioridades P distintas en el mismo cierre.

### Paso 1: Baseline inicial
- Ejecutar tests focales.
- Ejecutar mypy focal.
- Si baseline falla, reparar baseline antes del refactor.

### Paso 2: Refactor minimo y seguro
- Aplicar cambios minimos para cerrar el item.
- Mantener API publica salvo necesidad justificada.

### Paso 3: Tests del item
- Si aparece comportamiento nuevo: crear tests nuevos.
- Si cambia contrato: actualizar tests existentes.

### Paso 4: Gates focales
- Repetir tests focales.
- Repetir mypy focal.
- Si falla algo: rollback parcial o correccion inmediata (no seguir).

### Paso 5: Gates globales
- Ejecutar mypy global.
- Ejecutar pytest global.
- Si falla algo: corregir y repetir hasta verde.

### Paso 6: Documentacion y validacion
- Regenerar documentacion Daniel.
- Validar omisiones AST/doc (`omitidos=0`).
- Actualizar documentos de deuda/arquitectura impactados por el item.

### Paso 7: Cierre del item
- Actualizar **REGISTRO** con la plantilla de abajo (incl. **Sync iCloud** en el siguiente paso).
- No editar el PLAN si el usuario lo prohibe; si el PLAN permite marcar estado, hacerlo de forma coherente con el REGISTRO.

### Paso 8: Sincronizacion al arbol iCloud (**obligatorio**; repeticion del cierre)
- Ya deberia haberse sincronizado en **lotes** durante el item (ver `references/sync_icloud_continuo.md`). Este paso **verifica** que no quede ningun archivo solo en el worktree y actualiza REGISTRO.
- Identificar `SOURCE_ROOT` (raiz del repo donde se aplicaron los cambios: worktree o iCloud).
- **Checklist minima** de rutas a copiar si aplicaron cambios en el item (ademas de cualquier otro archivo tocado):
  - `mypy.ini` (casi siempre en items P2),
  - modulo(s) foco bajo `core/`, `database/`, `ui/`, `controllers/`, `features/`,
  - tests modificados bajo `tests/`,
  - `Documentacion/Refactorizacion_Completa/Auditoria_Secuencial/REGISTRO_EJECUCION_ITEMS.md`,
  - `Documentacion/Documentacion Daniel.md` y `Documentacion/Documentacion Daniel.pdf` si se regeneraron,
  - `.agents/skills/ejecucion_secuencial_calidad/**` (incl. `references/sync_icloud_continuo.md`) si se edito la skill.
- Si `SOURCE_ROOT` no es `HIPATIA_ICLOUD`, para cada `REL` tocado: `mkdir -p "$(dirname "$HIPATIA_ICLOUD/$REL")"` y `cp "$SOURCE_ROOT/$REL" "$HIPATIA_ICLOUD/$REL"`.
- Opcional: `cd "$HIPATIA_ICLOUD" && python3 -m pytest <tests_focales> -q` tras cambios grandes.
- En el REGISTRO: linea **Sync iCloud: OK** (o **N/A (workspace = iCloud)**) con lista breve de archivos.

## Gates canonicos

Usar comandos exactos en `references/gates.md`.

## Reglas de rollback

1. Si falla un gate focal:
   - revertir cambio parcial del item o corregir de inmediato,
   - volver a baseline focal.
2. Si falla gate global:
   - no cerrar item,
   - corregir regresion,
   - repetir gate global completo.
3. Nunca mezclar arreglo de otro item dentro del item actual sin documentarlo como dependencia.

## Plantilla de registro por item

Usar este bloque en `REGISTRO_EJECUCION_ITEMS.md`:

```md
## ITEM <id> - <titulo>
- Estado: En progreso | Completado
- Prioridad: P0 | P1 | P2 | P3
- Alcance: <archivos/modulos>
- Scripts ejecutados (opcional): p. ej. check_typing_coverage.py, ui_dto_boundary_analyzer.py, legacy_analyzer.py
- Baseline:
  - pytest focal: OK/FAIL
  - mypy focal: OK/FAIL
- Refactor aplicado: <resumen corto>
- Tests nuevos/ajustados: <lista>
- Gates post-refactor:
  - pytest focal: OK/FAIL
  - mypy focal: OK/FAIL
  - mypy global: OK/FAIL
  - pytest global: OK/FAIL
- Docs:
  - generate_daniel_doc.py: OK/FAIL
  - check_documentation_omissions.py: OK/FAIL
- Sync iCloud: OK — <archivos copiados> | N/A (workspace = iCloud)
- Evidencia: <comandos ejecutados>
- Fecha cierre: YYYY-MM-DD
```

## Limitacion conocida: check_typing_coverage.py

El script recorre el repo completo (excluye `tests/`) y mezcla **herramientas** (`scripts/`, `tools/`, `Documentacion/`) con **codigo de producto**. Para elegir el siguiente **ITEM 004**, aplicar siempre el **filtro de prefijos** de la tabla P2 arriba; no abrir un item P2 solo porque un script de analisis aparezca primero en el ranking.
