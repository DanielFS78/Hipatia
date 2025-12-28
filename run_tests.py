#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
import platform

def setup_qt_environment():
    """Configura las variables de entorno para Qt en macOS con espacios en rutas."""
    if platform.system() != "Darwin":
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    site_packages = os.path.join(script_dir, ".venv/lib/python3.13/site-packages")
    
    # Intenta localizar site-packages dinámicamente si la ruta hardcoded falla
    if not os.path.exists(site_packages):
        import site
        # Asumiendo que estamos en venv
        site_packages = [p for p in site.getsitepackages() if "site-packages" in p][0]

    qt6_dir = os.path.join(site_packages, "PyQt6/Qt6")

    if " " in site_packages:
        print("ℹ️ Dectectada ruta con espacios. Configurando workaround para Qt6...")
        tmp_pyqt = "/tmp/pyqt6_venv"
        target_qt = os.path.join(tmp_pyqt, "PyQt6")
        
        if not os.path.exists(target_qt):
            print("⏳ Copiando PyQt6 a /tmp (esto solo sucede una vez)...")
            os.makedirs(tmp_pyqt, exist_ok=True)
            subprocess.run(["cp", "-R", os.path.join(site_packages, "PyQt6"), tmp_pyqt], check=True)
            subprocess.run(["xattr", "-r", "-d", "com.apple.quarantine", target_qt], stderr=subprocess.DEVNULL)
        
        qt6_dir = os.path.join(target_qt, "Qt6")
        os.environ["PYTHONPATH"] = f"{tmp_pyqt}:{os.environ.get('PYTHONPATH', '')}"

    os.environ["QT_PLUGIN_PATH"] = os.path.join(qt6_dir, "plugins")
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(qt6_dir, "plugins/platforms")
    
    # Fix extra para tests: asegurar que no falle por falta de librerías
    dyld_path = f"{os.path.join(qt6_dir, 'lib')}:{os.environ.get('DYLD_LIBRARY_PATH', '')}"
    os.environ["DYLD_LIBRARY_PATH"] = dyld_path
    os.environ["DYLD_FRAMEWORK_PATH"] = dyld_path

def run_tests():
    """Ejecuta pytest con configuración óptima para reportes."""
    
    # Directorio de reportes
    reports_dir = os.path.join(os.getcwd(), "test_reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    # Argumentos base
    pytest_args = [
        sys.executable, "-m", "pytest",
        # Tipos de reporte (HTML + JSON para el plugin de auditoría + Terminal)
        "--cov=core", "--cov=database", "--cov=app", "--cov=ui", "--cov=features", "--cov=controllers",
        "--cov-report=term-missing", 
        f"--cov-report=html:{os.path.join(reports_dir, 'coverage')}",
        f"--cov-report=json:{os.path.join(reports_dir, 'coverage.json')}", # Necesario para el reporte PDF
        f"--html={os.path.join(reports_dir, 'report.html')}",
        # "--self-contained-html",  <-- Removed to avoid errors if plugin version mismatch
        # Mejorar salida
        "-v"
    ]
    
    # Añadir argumentos pasados por el usuario
    pytest_args.extend(sys.argv[1:])
    
    print("🚀 Iniciando suite de tests moderna (Fase 3)...")
    print(f"📂 Los reportes se guardarán en: {reports_dir}")
    print("-" * 60)
    
    # Ejecutar
    try:
        result = subprocess.run(pytest_args)
        exit_code = result.returncode
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrumpidos por el usuario.")
        exit_code = 130

    print("-" * 60)
    if exit_code == 0:
        print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE.")
    else:
        print(f"❌ HUBO FALLOS (Código de salida: {exit_code}). Revisar reporte.")
    
    print(f"✅ TODOS LOS TESTS PASARON EXITOSAMENTE.")
    
    # El usuario prefiere explícitamente el reporte de COBERTURA HTML (Agrupado y detallado)
    coverage_index = os.path.join(reports_dir, 'coverage/index.html')
    
    if os.path.exists(coverage_index):
        print(f"📊 Reporte de Cobertura (Web): file://{coverage_index}")
        
        # Abrir automáticamente en macOS
        if platform.system() == "Darwin":
            try:
                print("🔄 Abriendo reporte web de cobertura...")
                subprocess.run(["open", coverage_index])
            except Exception:
                pass
    else:
        print("⚠️ No se encontró el reporte de cobertura HTML.")

    sys.exit(exit_code)

if __name__ == "__main__":
    setup_qt_environment()
    run_tests()
