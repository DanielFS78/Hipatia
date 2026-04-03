# core/camera_manager/__init__.py

"""
Lógica o utilidades del núcleo (`__init__`): tipos, servicios auxiliares o infraestructura compartida fuera de la capa de interfaz.
"""

try:
    import cv2
except ImportError:
    cv2 = None  # type: ignore[assignment]

from .base import CameraInfo, CameraBackend, CV2_AVAILABLE
from .manager import CameraManager

def quick_detect_cameras():
    return CameraManager(max_cameras=5, detection_timeout=1.0).detect_cameras()

def get_working_camera_index():
    cams = quick_detect_cameras()
    return cams[0].index if cams else None

def validate_camera_index(index: int):
    return CameraManager().validate_camera(index)[0]

__all__ = [
    'CameraInfo',
    'CameraBackend',
    'validate_camera_index',
    'main',
    'cv2'
]

import logging

def main() -> None:
    """Función principal para pruebas manuales."""
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    main_logger = logging.getLogger("EvolucionTiemposApp.CameraManager.main")

    main_logger.info("=" * 70)
    main_logger.info("GESTOR DE CÁMARAS - Test de Detección")
    main_logger.info("=" * 70)

    manager = CameraManager(max_cameras=10)

    main_logger.info("\n1. Detectando cámaras...")
    cameras = manager.detect_cameras()

    if not cameras:
        main_logger.info("✗ No se encontraron cámaras")
    else:
        main_logger.info(f"\n✓ Se encontraron {len(cameras)} cámara(s):\n")
        for camera in cameras:
            main_logger.info(f"  • {camera}")

        best = manager.get_best_camera()
        if best:
             main_logger.info(f"\n📹 Mejor cámara: {best}")

             main_logger.info("\n¿Deseas probar la mejor cámara con preview? (s/n): ")
             try:
                 respuesta = input().lower()
                 if respuesta == 's':
                     main_logger.info("\nMostrando preview (3 segundos)...")
                     main_logger.info("Presiona ESC para cerrar antes")
                     manager.test_camera_with_preview(best.index, duration=3.0)
             except (EOFError, Exception) as e:
                 main_logger.info(f"Salida interactiva no disponible o error: {e}")

    main_logger.info("\n" + "=" * 70)
    main_logger.info("Test completado")
    main_logger.info("=" * 70)

