# Gates canonicos por item

## Scripts de analisis (antes o durante el item — lectura / verificacion)

Ejecutar segun la **prioridad P** del item (ver `SKILL.md`, mapa P0–P3):

| Prioridad | Script / comando tipico |
|-----------|-------------------------|
| P0 (ciclos / dependencias) | Informes en `scripts/analysis/` referenciados en el PLAN o en el REGISTRO |
| P1 (UI/DTO) | `python3 scripts/ui_dto_boundary_analyzer.py` — 0 hallazgos si se toca `ui/` |
| P2 (tipado ITEM 004) | `python3 scripts/check_typing_coverage.py` — filtrar mentalmente a `core/`, `database/`, `ui/`, `controllers/`, `features/` |
| P3 (legacy) | `python3 scripts/legacy_analyzer.py` si existe en el arbol |

Registrar en el item (campo **Scripts ejecutados** del REGISTRO) los que se hayan usado.

## Baseline (antes de tocar codigo)

```bash
python3 -m pytest <tests_focales>
python3 -m mypy <modulos_focales> --config-file=mypy.ini
```

## Tras refactor del item

```bash
python3 -m pytest <tests_focales>
python3 -m mypy <modulos_focales> --config-file=mypy.ini
```

## Cierre global obligatorio

```bash
python3 -m mypy . --config-file=mypy.ini
python3 -m pytest -q
python3 scripts/generate_daniel_doc.py
python3 scripts/check_documentation_omissions.py
```

## Sincronizacion iCloud (continua + Paso 8)

**Regla:** la copia al arbol iCloud es **obligacion del agente** cuando el workspace es un worktree distinto de `HIPATIA_ICLOUD`. Hacerlo **tras cada lote de ediciones** y **verificar al cerrar el item**. Detalle: `sync_icloud_continuo.md` en esta carpeta.

### Paso 8 — checklist al cerrar el item

Definir rutas (ajustar `SOURCE_ROOT` al worktree o repo activo):

```bash
export HIPATIA_ICLOUD="${HOME}/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion"
export SOURCE_ROOT="<raiz del repo donde se edito>"   # ej. worktree xig
```

**Checklist minima** (copiar si hubo cambios en el item):

- `mypy.ini`
- Modulo(s) foco (`core/`, `database/`, `ui/`, `controllers/`, `features/`)
- Tests bajo `tests/` tocados
- `Documentacion/Refactorizacion_Completa/Auditoria_Secuencial/REGISTRO_EJECUCION_ITEMS.md`
- `Documentacion/Documentacion Daniel.md` / `.pdf` si se regeneraron
- `.agents/skills/ejecucion_secuencial_calidad/` si se edito la skill

Por cada archivo relativo `REL` tocado en el item:

```bash
mkdir -p "$(dirname "$HIPATIA_ICLOUD/$REL")"
cp "$SOURCE_ROOT/$REL" "$HIPATIA_ICLOUD/$REL"
```

Si `SOURCE_ROOT` coincide con `HIPATIA_ICLOUD`, no hace falta copiar; indicar en registro: **Sync iCloud: N/A (workspace = iCloud)**.

Tras copiar, opcional pero recomendable en cambios amplios:

```bash
cd "$HIPATIA_ICLOUD" && python3 -m pytest <tests_focales> -q
```
