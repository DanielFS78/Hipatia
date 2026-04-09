---
name: UI dialog dependency wiring
description: Plan por fases para centralizar resolución de dependencias en diálogos UI (FabricacionService, PilaService), inyección opcional, protocolos mínimos y gates de tests. Leer primero en sesiones dedicadas a este refactor; seguir REGISTRO.md y references/gates.md.
---

# UI dialog dependency wiring — Hipatia

## Objetivo

Reducir resolución dispersa (DI + `product_controller` + `model`) en diálogos de borde mediante:

1. Módulo compartido [`ui/dialogs/fabrication/dialog_dependencies.py`](../../../ui/dialogs/fabrication/dialog_dependencies.py) (`resolve_fabricacion_service`, `resolve_pila_service`).
2. Parámetros opcionales `pila_service` / `fabricacion_service` en constructores cuando aplique.
3. Protocolos en [`ui/dialogs/fabrication/ui_dialog_protocols.py`](../../../ui/dialogs/fabrication/ui_dialog_protocols.py) (capa UI para evitar import cíclico con `controllers`): `OpensFabricacionPreprocesos`, `ShowsUserMessage` (bitácora: `user_messaging=` opcional).
4. Fallback a `model.planning_facade` / `model.*` documentado para tests y arranques sin servicios; ver **Fallback** abajo.

## Orden de trabajo

1. Abrir [REGISTRO.md](./REGISTRO.md) y elegir la siguiente fila no cerrada o ampliar con nuevos ítems.
2. Ejecutar gates de [references/gates.md](./references/gates.md) **antes** de editar código del ítem.
3. Un ítem o PR pequeño por vez; tras cambios, pytest + mypy del scope indicado en gates.
4. Marcar filas en REGISTRO (`Estado`, `Commit`, `Tests ejecutados`).

## Fallback a fachada / modelo (Fase 5)

- **Bitácora**: backend `_bitacora_backend` = `pila_service` inyectado → `resolve_pila_service` (DI → `pila_controller.pila_service` → `model.pila_service`) → `model.planning_facade` (`get_diario_bitacora` / `add_diario_evento`). Los delegadores de bitácora en `AppModel` fueron eliminados; no usar `model.get_diario_bitacora`.
- **AssignPreprocesos**: si `resolve_fabricacion_service` devuelve `None`, `get_preprocesos_by_fabricacion` vía `controller.model.fabricacion_service` (sin delegador en `AppModel`).
- **`FlowActionHandler.load_saved_pila`**: `_pila_list_load_api()` = `PilaService` resuelto → `model.planning_facade` → `model` (`get_all_pilas` / `load_pila`).
- **`DefinirLoteWidget`**: con `AppController` en `__init__` o `set_controller`, `FabricacionService` vía `resolve_fabricacion_service`; si `resolve` devuelve `None`, se mantiene el obtenido solo por DI al construir (si estaba registrado).

## Skills relacionadas

- [strict_testing](../strict_testing/SKILL.md), [testing_fixtures_y_mocks](../testing_fixtures_y_mocks/SKILL.md), [testing_antipatrones](../testing_antipatrones/SKILL.md)
- [reduccion_god_objects](../reduccion_god_objects/SKILL.md) — contexto AppModel
- [fase_legacy](../fase_legacy/SKILL.md) — si se elimina diálogo o menú huérfano
- [ejecucion_secuencial_calidad](../ejecucion_secuencial_calidad/SKILL.md) — disciplina de gates (opcional, mismo estilo)

## Regla Cursor

Ver `.cursor/rules/ui-dialog-dependency-wiring.mdc`: leer esta skill y REGISTRO al iniciar una sesión de este refactor.
