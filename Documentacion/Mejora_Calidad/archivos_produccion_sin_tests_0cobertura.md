# Archivos de producción con `0%` de cobertura (según `coverage.json`)

Evidencia: `coverage.json` (generado por `run_tests.py`) marca **42** ficheros Python de producción con `0%` de cobertura.  
Para atacar de forma efectiva sin entrar en “scripts de tooling” (análisis, generadores, runners), aquí se listan los **módulos de negocio** y **protocolos** que aparecen con `0%` y que son alcanzables con test unitario real:

1. `core/health/health_checker.py`
2. `core/health/test_runner.py`
3. `core/health/health_worker.py`
4. `controllers/simulation/protocols.py`
5. `controllers/historial/protocols.py`
6. `database/repositories/protocols.py`

Objetivo: crear suites de test nuevas para que estos ficheros pasen a **100% de cobertura**.

