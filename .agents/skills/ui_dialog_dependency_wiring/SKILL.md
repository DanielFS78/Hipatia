---
name: UI dialog dependency wiring
description: Plan por fases para centralizar resolución de dependencias en diálogos UI (FabricacionService, PilaService), inyección opcional, protocolos mínimos y gates de tests. Leer primero en sesiones dedicadas a este refactor; seguir REGISTRO.md y references/gates.md.
---

# UI dialog dependency wiring — Hipatia

## Objetivo

Reducir resolución dispersa (DI + `product_controller` + `model`) en diálogos de borde mediante:

1. Módulo compartido [`ui/dialogs/fabrication/dialog_dependencies.py`](../../../ui/dialogs/fabrication/dialog_dependencies.py) (`resolve_fabricacion_service`, `resolve_pila_service`).
2. Parámetros opcionales `pila_service` / `fabricacion_service` en constructores cuando aplique.
3. Protocolos en [`ui/dialogs/fabrication/ui_dialog_protocols.py`](../../../ui/dialogs/fabrication/ui_dialog_protocols.py) (capa UI para evitar import cíclico con `controllers`).
4. Fallback a `model.*` documentado para tests y arranques sin servicios; ver sección **Fallback** abajo.

## Orden de trabajo

1. Abrir [REGISTRO.md](./REGISTRO.md) y elegir la siguiente fila no cerrada o ampliar con nuevos ítems.
2. Ejecutar gates de [references/gates.md](./references/gates.md) **antes** de editar código del ítem.
3. Un ítem o PR pequeño por vez; tras cambios, pytest + mypy del scope indicado en gates.
4. Marcar filas en REGISTRO (`Estado`, `Commit`, `Tests ejecutados`).

## Fallback a AppModel (Fase 5)

- **Bitácora**: si no hay `PilaService` inyectado ni resuelto por DI/`model.pila_service`, se usa `controller.model.get_diario_bitacora` / `add_diario_evento` (tests con mock mínimo de `model`).
- **AssignPreprocesos**: si `resolve_fabricacion_service` devuelve `None`, `get_preprocesos_by_fabricacion` vía `controller.model`.
- **`FlowActionHandler.load_saved_pila`**: `_pila_list_load_api()` devuelve `PilaService` resuelto o `controller.model` para `get_all_pilas` / `load_pila` (misma semántica que antes, sin duplicar ramas).

## Skills relacionadas

- [strict_testing](../strict_testing/SKILL.md), [testing_fixtures_y_mocks](../testing_fixtures_y_mocks/SKILL.md), [testing_antipatrones](../testing_antipatrones/SKILL.md)
- [reduccion_god_objects](../reduccion_god_objects/SKILL.md) — contexto AppModel
- [fase_legacy](../fase_legacy/SKILL.md) — si se elimina diálogo o menú huérfano
- [ejecucion_secuencial_calidad](../ejecucion_secuencial_calidad/SKILL.md) — disciplina de gates (opcional, mismo estilo)

## Regla Cursor

Ver `.cursor/rules/ui-dialog-dependency-wiring.mdc`: leer esta skill y REGISTRO al iniciar una sesión de este refactor.
