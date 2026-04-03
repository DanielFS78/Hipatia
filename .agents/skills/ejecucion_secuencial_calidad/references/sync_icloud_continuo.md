# Sincronización continua hacia iCloud — obligación del agente

Este documento es la **fuente de verdad** para copiar cambios del worktree al clon que el usuario ejecuta (`run_tests.py`, git, Cursor abierto desde iCloud).

## Principio

**La sincronización es trabajo del agente, no del usuario.** No cerrar una respuesta sugiriendo «copia tú los archivos» si el agente puede ejecutar `cp` (o equivalente) en el entorno.

## Cuándo sincronizar

1. **Continua:** después de **cada lote de ediciones** que deje archivos guardados en disco (p. ej. al terminar una serie de `apply_patch` / antes de considerar la tarea entregada), si el repo activo **no** es ya el de iCloud.
2. **Cierre:** al terminar un item de auditoría secuencial (Paso 8 del `SKILL.md` principal) o al cerrar una sesión larga: repetir sync de **todos** los paths tocados en la sesión (verificar con `git status` / `git diff --name-only` en `SOURCE_ROOT`).

## Rutas canónicas (macOS)

```bash
export HIPATIA_ICLOUD="${HOME}/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion"
export SOURCE_ROOT="<raíz del repo donde Cursor/worktree escribió>"   # ej. .cursor/worktrees/.../xig
```

- Si `SOURCE_ROOT` y `HIPATIA_ICLOUD` son el **mismo directorio** (proyecto abierto desde iCloud): **Sync N/A**; no copiar.
- Si difieren: **obligatorio** replicar cada archivo relativo `REL` modificado o creado:

```bash
mkdir -p "$(dirname "$HIPATIA_ICLOUD/$REL")"
cp "$SOURCE_ROOT/$REL" "$HIPATIA_ICLOUD/$REL"
```

## Automatización (obligatorio cuando sea posible)

Tras cada lote de cambios, el agente debe ejecutar (mismo `SOURCE_ROOT` y `HIPATIA_ICLOUD` que arriba):

```bash
cd "$SOURCE_ROOT"
export HIPATIA_ICLOUD="${HOME}/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion"
python3 scripts/sync_worktree_to_icloud.py
```

- Vista previa sin copiar: `python3 scripts/sync_worktree_to_icloud.py --dry-run`
- El script usa `git status --porcelain -u`: solo **archivos existentes** en disco (omite borrados; para borrar en iCloud un path eliminado en el worktree, usar `rm` explícito en destino si aplica).

Si `git` no está disponible en el entorno del agente, usar el bucle manual `cp` de la sección anterior con la lista `REL`.

## Cómo obtener la lista `REL`

- Preferible: `python3 scripts/sync_worktree_to_icloud.py` **o** `cd "$SOURCE_ROOT" && git status --short` / `git diff --name-only` (incluir untracked si son archivos nuevos relevantes).
- Incluir siempre, si aplican: código bajo `core/`, `database/`, `ui/`, `controllers/`, `features/`, `tests/`, `mypy.ini`, `Documentacion/**`, `.agents/skills/**`, `scripts/**`, `reports/**`.

## Si la copia falla (permisos, disco, ruta)

- Documentar en la respuesta el error concreto y la lista de `REL` pendientes; intentar ruta alternativa solo si el usuario la indica.
- **No** asumir que el usuario hará la copia por defecto.

## Coherencia con REGISTRO

En items de `REGISTRO_EJECUCION_ITEMS.md`, la línea **Sync iCloud** puede resumir el último lote (p. ej. `OK — N archivos`) o **N/A (workspace = iCloud)**.
