#!/usr/bin/env python3
"""
🚀 HIPATIA MASTER TEST RUNNER & QA DASHBOARD
============================================
Orquesta la ejecución de tests y genera un reporte visual de cobertura
y calidad real de código por cada archivo de test.
"""

import hashlib
import os
import re
import sys
import json
import subprocess
import time
import tempfile
from pathlib import Path
from typing import Any

# Copias Finder/iCloud: ``test_algo 2.py``, ``test_algo 3.py``, etc.
_FINDER_DUP_TEST = re.compile(r" \d+\.py$")


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_banner() -> None:
    print(f"""
{Colors.HEADER}{Colors.BOLD}================================================================================
          HIPATIA - MASTER TEST RUNNER & QUALITY DASHBOARD 🚀
================================================================================{Colors.ENDC}""")


def run_command(cmd: list[str], text: str = "") -> subprocess.CompletedProcess[str]:
    if text:
        print(f"{Colors.OKCYAN}⚙️  {text}...{Colors.ENDC}")
    return subprocess.run(cmd, capture_output=True, text=True)


def _is_finder_duplicate_test(path: Path) -> bool:
    """True si es copia accidental tipo ``test_foo 2.py`` / ``test_foo 3.py`` (Finder/iCloud)."""
    return path.name.startswith("test_") and bool(_FINDER_DUP_TEST.search(path.name))


def _collect_test_files(root_dir: Path) -> list[Path]:
    """Devuelve todos los archivos test_*.py bajo tests/ (sin duplicados ``* N.py``)."""
    return sorted(
        p for p in (root_dir / "tests").rglob("test_*.py") if not _is_finder_duplicate_test(p)
    )


def _run_file_with_coverage(test_file: Path, cov_data_dir: Path, root_dir: Path) -> tuple[bool, str]:
    """Ejecuta un archivo de test con cobertura en subproceso aislado.

    Cada archivo genera su propio .coverage.<n> que luego se combina.
    Devuelve (passed, output_summary).
    """
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    # Nombre único por ruta relativa (evita colisión test_x.py vs test_x 3.py y espacios en stem)
    try:
        rel_key = str(test_file.resolve().relative_to(root_dir.resolve()))
    except ValueError:
        rel_key = str(test_file.resolve())
    tag = hashlib.sha256(rel_key.encode()).hexdigest()[:24]
    cov_file = str(cov_data_dir / f".coverage.{tag}")
    env["COVERAGE_FILE"] = cov_file

    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file),
        f"--cov={root_dir}",
        "--cov-report=",                      # sin reporte individual
        "--tb=no", "-q", "--no-header",
        "--timeout=30",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120)
    # Extraer línea de resumen (ej: "5 passed in 0.3s")
    summary = ""
    for line in result.stdout.splitlines():
        if "passed" in line or "failed" in line or "error" in line or "skipped" in line:
            summary = line.strip()
            break
    # exit code 5 = todos los tests saltados (válido)
    return result.returncode in (0, 5), summary


def _score_color(score: float) -> str:
    if score >= 80:
        return Colors.OKGREEN
    if score >= 50:
        return Colors.WARNING
    return Colors.FAIL


def _cov_color(pct: float) -> str:
    if pct >= 90:
        return Colors.OKGREEN
    if pct >= 80:
        return Colors.WARNING
    return Colors.FAIL


def _print_quality_legend() -> None:
    print(f"\n{Colors.BOLD}LEYENDA DE CALIDAD (score real):{Colors.ENDC}")
    print(f"  +25  tiene @pytest.mark.*")
    print(f"  +20  usa mocks estrictos (create_autospec / spec= / autospec=True)")
    print(f"  +15  verifica interacciones (assert_called_with / assert_called_once_with)")
    print(f"  +15  valida DTOs con isinstance(..., XxxDTO)")
    print(f"  +15  todos los @patch usan autospec=True")
    print(f"  +10  tiene docstrings")
    print(f"  -5   por cada MagicMock() / Mock() suelto (sin spec)  [máx -30]")
    print(f"  -3   por cada @patch sin autospec=True                 [máx -20]")
    print(f"  -5   por cada test sin ningún assert                   [máx -20]")
    print(f"  -10  archivo ctrl/servicio sin assert_called*")
    print(f"  -3   por cada assert_called_once() sin args            [máx -15]")
    print(f"  -8   mockea sesión de BD (antipatrón en repositorios)")
    print(f"  -5   por cada MagicMock(spec=object)                  [máx -15]")


def _print_worst_files(
    test_files_stats: list[dict[str, Any]],
    quality_map: dict[str, Any],
    root_dir: Path,
) -> None:
    """Muestra los archivos con peor score corregible para priorizar mejoras."""
    non_infra = [
        s for s in test_files_stats
        if not quality_map.get(str(root_dir / s["path"]), {}).get("is_infra", False)
        and not quality_map.get(str(root_dir / s["path"]), {}).get("at_ceiling", False)
    ]
    worst = sorted(non_infra, key=lambda x: x["ceiling"])[:5]
    if not worst:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}🏆 Todos los archivos están en su techo real.{Colors.ENDC}")
        return

    print(f"\n{Colors.BOLD}⚠️  TOP 5 ARCHIVOS CON MAYOR POTENCIAL DE MEJORA:{Colors.ENDC}")
    for s in worst:
        q_info = quality_map.get(str(root_dir / s["path"]), {})
        actionable = q_info.get("actionable_penalties", {})
        penalty_str = ""
        if actionable:
            parts = [f"{k}: {v}" for k, v in actionable.items()]
            penalty_str = f"  corregibles → {', '.join(parts)}"
        color = _score_color(s["ceiling"])
        ceil = s["ceiling"]
        abs_s = s["quality"]
        score_display = f"{abs_s:>3.0f}→{ceil:>3.0f}" if abs_s != ceil else f"{abs_s:>3.0f}/100"
        print(f"  {color}{score_display}{Colors.ENDC}  {s['path']}{penalty_str}")


def main() -> None:
    start_time = time.time()
    print_banner()

    root_dir = Path(__file__).resolve().parent
    scripts_dir = root_dir / "scripts"

    # 1. Ejecutar tests archivo por archivo (evita segfault Qt) y recopilar cobertura
    test_files = _collect_test_files(root_dir)
    total_files = len(test_files)
    cov_data_dir = root_dir / ".coverage_parts"
    cov_data_dir.mkdir(exist_ok=True)
    for stale in cov_data_dir.glob(".coverage.*"):
        try:
            stale.unlink()
        except OSError:
            pass

    print(f"{Colors.OKCYAN}⚙️  Ejecutando suite de tests y calculando cobertura "
          f"({total_files} archivos)...{Colors.ENDC}")

    passed_count = 0
    failed_count = 0
    any_failure = False

    for idx, tf in enumerate(test_files, 1):
        rel = str(tf.relative_to(root_dir))
        print(f"  [{idx:>3}/{total_files}] {rel} ... ", end="", flush=True)
        try:
            ok, summary = _run_file_with_coverage(tf, cov_data_dir, root_dir)
        except subprocess.TimeoutExpired:
            ok, summary = False, "TIMEOUT"
        if ok:
            passed_count += 1
            print(f"{Colors.OKGREEN}✓{Colors.ENDC}  {summary}")
        else:
            failed_count += 1
            any_failure = True
            print(f"{Colors.FAIL}✗{Colors.ENDC}  {summary}")

    # Combinar archivos de cobertura parciales en uno solo
    print(f"\n{Colors.OKCYAN}⚙️  Combinando datos de cobertura...{Colors.ENDC}")
    cov_parts = sorted(cov_data_dir.glob(".coverage.*"))
    env_combine = os.environ.copy()
    env_combine["COVERAGE_FILE"] = str(root_dir / ".coverage")
    if not cov_parts:
        print(
            f"{Colors.FAIL}❌ No hay fragmentos en .coverage_parts/ "
            f"(¿pytest-cov instalado?).{Colors.ENDC}"
        )
    else:
        # Un solo argumento (directorio) evita límites de argv con cientos de fragmentos
        rc_c = subprocess.run(
            [
                sys.executable,
                "-m",
                "coverage",
                "combine",
                "--keep",
                str(cov_data_dir),
            ],
            capture_output=True,
            text=True,
            env=env_combine,
            cwd=str(root_dir),
        )
        if rc_c.returncode != 0:
            print(f"{Colors.FAIL}coverage combine falló (código {rc_c.returncode}){Colors.ENDC}")
            if rc_c.stderr:
                print(rc_c.stderr)
            if rc_c.stdout:
                print(rc_c.stdout)
        rc_j = subprocess.run(
            [sys.executable, "-m", "coverage", "json", "-o", str(root_dir / "coverage.json")],
            capture_output=True,
            text=True,
            env=env_combine,
            cwd=str(root_dir),
        )
        if rc_j.returncode != 0:
            print(f"{Colors.FAIL}coverage json falló (código {rc_j.returncode}){Colors.ENDC}")
            if rc_j.stderr:
                print(rc_j.stderr)
            if rc_j.stdout:
                print(rc_j.stdout)

    # Resultado global de tests (para el mensaje final)
    test_result_ok = not any_failure

    # 2. Ejecutar analizador de calidad real
    run_command(
        [sys.executable, str(scripts_dir / "test_quality_analyzer.py")],
        "Ejecutando analizador de calidad real (Strict Testing)",
    )

    # 3. Cargar datos
    try:
        with open(root_dir / "coverage.json") as f:
            coverage_data = json.load(f)
        with open(root_dir / "test_reports" / "compliance_data.json") as f:
            quality_data = json.load(f)
    except FileNotFoundError as e:
        print(f"{Colors.FAIL}❌ Error: no se encontraron archivos de datos ({e}){Colors.ENDC}")
        sys.exit(1)

    quality_map = {item["path"]: item for item in quality_data}

    # 4. Dashboard
    col_file = 52
    print(f"\n{Colors.BOLD}{'ARCHIVO DE TEST':<{col_file}} {'COB%':>6}  {'ABS→TECHO':>11}  {'MOCKS+':>7}  {'MOCKS-':>7}  {'SIN-ASS':>7}  ESTADO{Colors.ENDC}")
    print("─" * 120)

    test_files_stats: list[dict[str, Any]] = []

    for file_path, stats in sorted(coverage_data.get("files", {}).items()):
        if not file_path.startswith("tests/"):
            continue

        full_path = str(root_dir / file_path)
        q_info = quality_map.get(full_path, {})
        metrics = q_info.get("metrics", {})

        cov_pct: float = stats["summary"]["percent_covered"]
        quality_score: float = q_info.get("score", 0)
        ceiling_score: float = q_info.get("ceiling_score", quality_score)
        at_ceiling: bool = q_info.get("at_ceiling", False)
        status: str = q_info.get("status", "Pendiente")
        strict_count: int = metrics.get("strict_mock_count", 0)
        loose_count: int = metrics.get("loose_mock_count", 0)
        no_assert_count: int = metrics.get("tests_without_assert", 0)
        missing_interaction: bool = metrics.get("missing_interaction_check", False)
        actionable = q_info.get("actionable_penalties", {})

        # Truncar path largo
        display_path = file_path if len(file_path) <= col_file else "…" + file_path[-(col_file - 1):]

        # Indicadores de estado
        alert = f" {Colors.FAIL}⚠ sin assert_called{Colors.ENDC}" if missing_interaction else ""
        ceil_indicator = f"{Colors.OKGREEN}✅{Colors.ENDC}" if at_ceiling else "  "
        # Mostrar score/techo solo si difieren
        if quality_score == ceiling_score:
            score_str = f"{quality_score:>3.0f}/100"
        else:
            score_str = f"{quality_score:>3.0f}→{ceiling_score:>3.0f}"

        print(
            f"{display_path:<{col_file}} "
            f"{_cov_color(cov_pct)}{cov_pct:>5.1f}%{Colors.ENDC}  "
            f"{_score_color(ceiling_score)}{score_str:>9}{Colors.ENDC} {ceil_indicator}  "
            f"{Colors.OKGREEN}{strict_count:>6}✓{Colors.ENDC}  "
            f"{Colors.FAIL if loose_count > 0 else Colors.OKGREEN}{loose_count:>6}✗{Colors.ENDC}  "
            f"{Colors.FAIL if no_assert_count > 0 else Colors.OKGREEN}{no_assert_count:>6}✗{Colors.ENDC}  "
            f"{status}{alert}"
        )

        test_files_stats.append({
            "path": file_path,
            "cov": cov_pct,
            "quality": quality_score,
            "ceiling": ceiling_score,
            "at_ceiling": at_ceiling,
        })

    # 5. Resumen ejecutivo
    duration = time.time() - start_time
    total = len(test_files_stats)
    avg_cov = sum(s["cov"] for s in test_files_stats) / total if total else 0
    avg_qual = sum(s["quality"] for s in test_files_stats) / total if total else 0
    avg_ceil = sum(s["ceiling"] for s in test_files_stats) / total if total else 0
    at_ceiling_count = sum(1 for s in test_files_stats if s["at_ceiling"])

    updated = sum(1 for item in quality_data if item["status"] == "Actualizado")
    in_progress = sum(1 for item in quality_data if item["status"] == "En Progreso")
    legacy = sum(1 for item in quality_data if item["status"] == "Legacy / Pendiente")

    # Métricas de antipatrones globales — separar inevitables de corregibles
    total_loose = sum(item.get("metrics", {}).get("loose_mock_count", 0) for item in quality_data)
    total_no_autospec = sum(item.get("metrics", {}).get("patches_without_autospec", 0) for item in quality_data)
    total_no_assert = sum(item.get("metrics", {}).get("tests_without_assert", 0) for item in quality_data)
    total_missing_interaction = sum(
        1 for item in quality_data
        if item.get("metrics", {}).get("missing_interaction_check", False)
    )
    total_mock_session = sum(
        1 for item in quality_data
        if item.get("metrics", {}).get("has_mock_session", False)
    )
    total_spec_object = sum(
        item.get("metrics", {}).get("spec_object_count", 0) for item in quality_data
    )
    # Penalizaciones corregibles (las que sí se pueden mejorar)
    total_actionable_loose = sum(
        abs(item.get("actionable_penalties", {}).get("loose_mocks", 0)) // 5
        for item in quality_data
    )
    total_actionable_patches = sum(
        abs(item.get("actionable_penalties", {}).get("patches_no_autospec", 0)) // 3
        for item in quality_data
    )

    print("─" * 120)
    print(f"{Colors.BOLD}RESUMEN EJECUTIVO:{Colors.ENDC}")
    print(f"  ⏱️  Duración: {duration:.2f}s")
    print(f"  🧪 Archivos analizados: {total}")
    print(f"  📊 Cobertura media:     {_cov_color(avg_cov)}{avg_cov:.1f}%{Colors.ENDC}")
    print(f"  🎯 Score absoluto medio:   {_score_color(avg_qual)}{avg_qual:.1f}/100{Colors.ENDC}")
    print(f"  🏆 Score optimizado medio: {_score_color(avg_ceil)}{avg_ceil:.1f}/100{Colors.ENDC}  "
          f"(en techo: {at_ceiling_count}/{total} archivos)")
    print(f"  📈 Estado: Actualizados: {updated} | En Progreso: {in_progress} | Legacy: {legacy}")
    print(
        f"  {Colors.OKCYAN}ℹ️  'En Progreso' mide calidad/estrictitud del análisis, no fallos de tests."
        f"{Colors.ENDC}"
    )
    print(
        f"  {Colors.OKCYAN}   Gate piloto/release: 0 fallos en esta suite y CI verde en la rama."
        f"{Colors.ENDC}"
    )

    print(f"\n{Colors.BOLD}ANTIPATRONES DETECTADOS:{Colors.ENDC}")
    _loose_c = Colors.FAIL if total_loose > 0 else Colors.OKGREEN
    _noauto_c = Colors.FAIL if total_no_autospec > 0 else Colors.OKGREEN
    _noass_c = Colors.FAIL if total_no_assert > 0 else Colors.OKGREEN
    _nointer_c = Colors.FAIL if total_missing_interaction > 0 else Colors.OKGREEN
    _sess_c = Colors.FAIL if total_mock_session > 0 else Colors.OKGREEN
    # MagicMock() sin spec: mostrar total y cuántos son corregibles
    loose_corr_str = f"  ({total_actionable_loose} corregibles)" if total_actionable_loose > 0 else f"  ({Colors.OKGREEN}todos inevitables ✅{Colors.ENDC})"
    patch_corr_str = f"  ({total_actionable_patches} corregibles)" if total_actionable_patches > 0 else f"  ({Colors.OKGREEN}todos inevitables ✅{Colors.ENDC})"
    print(f"  {_loose_c}MagicMock() sin spec:          {total_loose:>4}{Colors.ENDC}{loose_corr_str}")
    print(f"  {_noauto_c}@patch sin autospec=True:      {total_no_autospec:>4}{Colors.ENDC}{patch_corr_str}")
    print(f"  {_noass_c}Tests sin ningún assert:        {total_no_assert:>4}{Colors.ENDC}")
    print(f"  {_nointer_c}Ctrl/Svc sin assert_called*:   {total_missing_interaction:>4} archivos{Colors.ENDC}")
    print(f"  {_sess_c}Mock de sesión BD:              {total_mock_session:>4} archivos{Colors.ENDC}")
    _spec_c = Colors.FAIL if total_spec_object > 0 else Colors.OKGREEN
    print(f"  {_spec_c}MagicMock(spec=object):         {total_spec_object:>4}{Colors.ENDC}")

    _print_worst_files(test_files_stats, quality_map, root_dir)
    _print_quality_legend()

    if test_result_ok:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}✨ TODOS LOS TESTS HAN PASADO{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}❌ SE DETECTARON FALLOS EN LA SUITE DE TESTS "
              f"({failed_count} archivos con fallos){Colors.ENDC}")

    if test_result_ok:
        print(
            f"\n{Colors.OKCYAN}📄 Para refrescar la tabla de métricas del README: "
            f"`python scripts/update_readme_metrics.py`{Colors.ENDC} "
            f"(usa `coverage.json` y `test_reports/compliance_data.json` generados arriba)."
        )


if __name__ == "__main__":
    main()
