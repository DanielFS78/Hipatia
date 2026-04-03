# Monolitos — referencia operativa

La fase de reducción de monolitos quedó **cerrada** en el marco del plan de calidad. Los informes estáticos (`monolith_report.{md,json}`, `Monolitos_finales.md`) se retiraron del repo para evitar datos obsoletos.

## Generar un informe actual

```bash
python3 scripts/monolith_analyzer.py --min-loc 250 --top 30
```

Salida por defecto (según el script): bajo `Documentacion/Refactorizacion_Completa/Monolitos/` o la ruta configurada en `scripts/monolith_analyzer.py`.

## Metodología vigente

- Hub de calidad y fases: `.agents/skills/plan_mejora_calidad/SKILL.md`
- Tests y mocks: skills bajo `.agents/skills/` (`strict_testing`, `testing_fixtures_y_mocks`, etc.)
