# Reporte de Monolitos — Hipatia
- Generado: **2026-03-19T14:24:16**
- Rutas escaneadas: `controllers, core, database, features, ui`
- Umbral monolito (LOC): **400+**
- Nodos/edges: **343 / 347**
- SCC cíclicas: **3**

## Ranking (top)
| Archivo | LOC | In | Out |
|---|---:|---:|---:|

## Ciclos detectados (SCC > 1)

### Ciclo 1 (tamaño 2)
- `controllers/backup_controller.py`
- `controllers/backup_controller_io_mixin.py`

### Ciclo 2 (tamaño 2)
- `controllers/report_controller.py`
- `controllers/report_controller_export_mixin.py`

### Ciclo 3 (tamaño 2)
- `controllers/schedule_controller.py`
- `controllers/schedule_ui_ops.py`
