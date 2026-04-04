# Gates — UI dialog dependency wiring

Comandos por fase (ajustar rutas al repo). Usar `python3` como en el resto del proyecto.

## Antes de empezar un ítem

```bash
python3 -m pytest tests/unit/test_fabrication_dialogs.py tests/unit/test_bitacora_dialog.py -q
```

## Fase 1 (módulo `dialog_dependencies`)

```bash
python3 -m pytest tests/unit/test_dialog_dependencies.py tests/unit/test_fabrication_dialogs.py tests/unit/test_bitacora_dialog.py -q
python3 -m mypy ui/dialogs/fabrication/dialog_dependencies.py ui/dialogs/fabrication/assignment_dialogs.py ui/dialogs/fabrication/bitacora_dialog.py --config-file=mypy.ini
```

## Fase 2 (constructores con inyección opcional)

```bash
python3 -m pytest tests/unit/test_fabrication_dialogs.py tests/unit/test_bitacora_dialog.py -q
python3 -m mypy ui/dialogs/fabrication/bitacora_dialog.py ui/dialogs/fabrication/assignment_dialogs.py --config-file=mypy.ini
```

## Fase 3 (call sites — pila_manager)

```bash
python3 -m pytest tests/unit/test_pila_manager_isolated.py tests/unit/test_pila_controller_comprehensive.py -q
python3 -m mypy controllers/pila/pila_manager.py --config-file=mypy.ini
```

## Fase 4 (Protocol)

```bash
python3 -m pytest tests/unit/test_fabrication_dialogs.py -q
python3 -m mypy ui/dialogs/fabrication/assignment_dialogs.py ui/dialogs/fabrication/ui_dialog_protocols.py --config-file=mypy.ini
```

## Fase 5–6 (cierre / production_flow)

```bash
python3 -m pytest tests/unit/ui/production_flow/test_flow_action_handler.py tests/unit/test_define_flow_dialog.py tests/unit/test_define_flow_dialog_edge.py -q
python3 -m mypy ui/dialogs/production_flow/flow_action_handler.py ui/dialogs/production_flow/define_flow_dialog.py ui/dialogs/fabrication/dialog_dependencies.py --config-file=mypy.ini
```

## Call site AssignPreprocesos (fase 7 / seguimiento)

```bash
python3 -m pytest tests/unit/test_preprocesos_widget.py -q
python3 -m mypy ui/widgets/preprocesos_widget.py --config-file=mypy.ini
```

## Cierre recomendado (tras completar fases)

```bash
python3 -m pytest tests/unit/test_dialog_dependencies.py tests/unit/test_fabrication_dialogs.py tests/unit/test_bitacora_dialog.py tests/unit/test_pila_manager_isolated.py tests/unit/ui/production_flow/test_flow_action_handler.py -q
```
