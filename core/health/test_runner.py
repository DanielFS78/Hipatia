# -*- coding: utf-8 -*-
"""
Nombre del Módulo: test_runner
Descripción: Ejecuta pytest -m unit en un subprocess y parsea el progreso en tiempo real.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Optional

from .health_checker import TestResults

_RE_TEST_LINE = re.compile(r"^(tests/\S+)\s+(PASSED|FAILED|ERROR)", re.MULTILINE)
_RE_SUMMARY = re.compile(
    r"(\d+) passed(?:,\s*(\d+) failed)?(?:,\s*(\d+) error)?.*in ([\d.]+)s"
)


class TestRunner:
    """
    Ejecuta pytest -m unit en un subprocess y emite progreso línea a línea.
    """

    def run(
        self,
        progress_callback: Callable[[str, int, int], None],
        finished_callback: Callable[[TestResults], None],
    ) -> None:
        """
        Lanza pytest -m unit y llama a los callbacks con el progreso.

        Args:
            progress_callback: (test_name, current, total)
            finished_callback: (TestResults)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        root = Path(__file__).resolve().parent.parent.parent
        cmd = [
            sys.executable, "-m", "pytest",
            "-m", "unit",
            "--tb=no", "-v",  # verbose para capturar nombres de tests
            f"--rootdir={root}",
        ]

        logger.info(f"TestRunner: ejecutando comando: {' '.join(cmd)}")
        logger.info(f"TestRunner: directorio de trabajo: {root}")

        passed = failed = errors = 0
        current = 0
        start = time.time()
        failed_tests: list[str] = []
        all_output: list[str] = []

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(root),
            )

            assert proc.stdout is not None
            for line in proc.stdout:
                line = line.rstrip()
                all_output.append(line)

                # Líneas de progreso: "tests/unit/test_foo.py::TestBar::test_x PASSED"
                if " PASSED" in line or " FAILED" in line or " ERROR" in line:
                    current += 1
                    
                    # Extraer nombre del test
                    parts = line.split("::")
                    if len(parts) >= 2:
                        name = parts[-1].split()[0]  # Último componente antes del estado
                    else:
                        name = line.split()[0].split("/")[-1] if line.split() else "test"
                    
                    if " PASSED" in line:
                        passed += 1
                    elif " FAILED" in line:
                        failed += 1
                        failed_tests.append(line.split()[0])
                    elif " ERROR" in line:
                        errors += 1
                        failed_tests.append(line.split()[0])
                    
                    progress_callback(name, current, max(current, 1))

            proc.wait()
            logger.info(f"TestRunner: proceso terminado con código {proc.returncode}")

        except Exception as e:
            errors += 1
            logger.error(f"TestRunner: error ejecutando tests: {e}", exc_info=True)

        duration = time.time() - start
        total = passed + failed + errors
        
        logger.info(f"TestRunner: capturados {total} tests (passed={passed}, failed={failed}, errors={errors})")
        
        # Si no se capturó nada, intentar parsear el resumen
        if total == 0:
            logger.warning("TestRunner: no se capturaron tests individuales, buscando resumen...")
            for line in all_output:
                ms = _RE_SUMMARY.search(line)
                if ms:
                    passed = int(ms.group(1))
                    failed = int(ms.group(2) or 0)
                    errors = int(ms.group(3) or 0)
                    total = passed + failed + errors
                    logger.info(f"TestRunner: resumen encontrado: {total} tests")
                    break
            
            if total == 0:
                logger.error("TestRunner: no se encontraron tests. Primeras 20 líneas de salida:")
                for line in all_output[:20]:
                    logger.error(f"  {line}")

        pass_rate = passed / total if total > 0 else 0.0
        coverage = self._read_coverage(root)

        finished_callback(TestResults(
            total=total,
            passed=passed,
            failed=failed,
            errors=errors,
            pass_rate=pass_rate,
            coverage_pct=coverage,
            duration_seconds=round(duration, 1),
            failed_tests=failed_tests,
        ))

    def _read_coverage(self, root: Path) -> float:
        """Lee la cobertura del último run guardado en test_reports/compliance_data.json."""
        try:
            cov_file = root / "test_reports" / "compliance_data.json"
            if cov_file.exists():
                data = json.loads(cov_file.read_text(encoding="utf-8"))
                scores = [item.get("score", 0) for item in data if not item.get("is_infra")]
                return round(sum(scores) / len(scores), 1) if scores else 0.0
        except Exception:
            pass
        return 0.0
