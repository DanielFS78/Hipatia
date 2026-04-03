---
name: Backlog — Tests En Progreso (Dashboard)
description: Listado vivo de archivos en estado 'En Progreso' según el analizador. Incluye penalizaciones corregibles y el orden de trabajo recomendado. Regenerar con scripts/extract_test_quality_in_progress.py.
---

# Backlog — Tests En Progreso (Dashboard)

Fuente: `test_reports/compliance_data.json`.

Regenerar:

```bash
python3 scripts/extract_test_quality_in_progress.py
```

Total actual: **0**

## Listado vivo (marcar ✅ al completar)

| # | Archivo | Estado | Score | Techo | Penalizaciones |
|---:|---|:---:|---:|---:|---|

## Criterio de ✅ (obligatorio)

- `python3 -m mypy <archivo> ...` pasa
- `pytest <archivo> -q` pasa
- `pytest -q` pasa
- `python3 scripts/test_quality_analyzer.py` ya no lista ese archivo como 'En Progreso' (o queda en techo real con explicación)
