## Fase de Tipado Estricto (Mypy)

Esta carpeta contiene los informes y el seguimiento de la fase final de tipado estricto.

- **Objetivo**: llegar a **0 errores** de MyPy en el repositorio (según `mypy.ini`), **incluyendo `tests/`**.
- **Ciclo obligatorio**: auditar → corregir 1–3 archivos → `python3 -m mypy <scope>` → `pytest <scope>` → `pytest` completo → documentar → repetir.
- **Generación de documentación**: tras cambios sustantivos, ejecutar `python3 scripts/generate_daniel_doc.py`.

### Comandos de referencia (fuentes de verdad)

MyPy global:

```bash
python3 -m mypy . --config-file mypy.ini --show-error-codes
```

Pytest global:

```bash
python3 -m pytest -q
```

Analizador de calidad de tests (score real + techo real):

```bash
python3 scripts/test_quality_analyzer.py
```

Datos estructurados del analizador:
- `test_reports/compliance_data.json`

Archivos que se irán generando:

- `mypy_baseline.txt`: salida completa inicial de mypy (baseline).
- `informe_tipado_estricto_pre.md`: informe pre-fase con plan de ataque.
- `informe_tipado_estricto_post.md`: informe post-fase con resultados y decisiones.

