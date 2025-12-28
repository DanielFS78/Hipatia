"""
========================================================================
GESTOR DE CÁMARAS - SISTEMA DE DETECCIÓN Y GESTIÓN ROBUSTA
========================================================================
Gestión avanzada de cámaras con detección robusta, validación y
recuperación automática de errores.

Características:
- Detección exhaustiva de cámaras disponibles
- Validación de funcionamiento real
- Información detallada (resolución, FPS, backend)
- Sistema de retry y fallback automático
- Detección de cámaras USB en caliente
- Compatible con Windows, Linux y Mac

Autor: Sistema de Trazabilidad
Fecha: 2025
Versión: 2.0 (Robusta)
========================================================================
"""

import logging
try:
    import cv2
    CV2_AVAILABLE = True
except (ImportError, AttributeError):
    # Fallback for CI/Tests or if OpenCV is broken
    CV2_AVAILABLE = False
    cv2 = None

import platform
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class CameraBackend(Enum):
    """Backends disponibles de OpenCV."""
    if CV2_AVAILABLE:
        AUTO = cv2.CAP_ANY
        DSHOW = cv2.CAP_DSHOW  # DirectShow (Windows)
        MSMF = cv2.CAP_MSMF  # Microsoft Media Foundation (Windows)
        V4L2 = cv2.CAP_V4L2  # Video4Linux2 (Linux)
        AVFOUNDATION = cv2.CAP_AVFOUNDATION  # AVFoundation (Mac)
    else:
        # Mock values for tests
        AUTO = 0
        DSHOW = 700
        MSMF = 1400
        V4L2 = 200
        AVFOUNDATION = 1200


@dataclass
class CameraInfo:
    """Información detallada de una cámara."""
    index: int
    name: str
    backend: str
    width: int
    height: int
    fps: float
    is_working: bool
    is_external: bool = False  # 🆕 Indica si es cámara USB externa
    error_message: Optional[str] = None

    def __str__(self):
        if self.is_working:
            external_indicator = " [USB EXTERNA]" if self.is_external else " [INTEGRADA]"
            return f"Cámara {self.index}: {self.name}{external_indicator} ({self.width}x{self.height} @ {self.fps:.1f}fps)"
        else:
            return f"Cámara {self.index}: ERROR - {self.error_message}"

class CameraManager:
    """
    Gestor robusto de cámaras con detección avanzada.

    Maneja la detección, validación y gestión de cámaras de forma
    robusta con recuperación automática de errores.

    Attributes:
        logger: Logger para registro de operaciones
        max_cameras: Número máximo de índices a probar
        detection_timeout: Timeout por cámara en segundos
        validation_frames: Frames a capturar para validación
    """

    def __init__(
            self,
            max_cameras: int = 10,
            detection_timeout: float = 2.0,
            validation_frames: int = 3
    ):
        """
        Inicializa el gestor de cámaras.

        Args:
            max_cameras: Número máximo de índices de cámara a probar
            detection_timeout: Timeout en segundos para cada cámara
            validation_frames: Número de frames a capturar para validar
        """
        self.logger = logging.getLogger("EvolucionTiemposApp.CameraManager")
        self.max_cameras = max_cameras
        self.detection_timeout = detection_timeout
        self.validation_frames = validation_frames
        self.cached_cameras: List[CameraInfo] = []
        self.last_detection_time: float = 0
        self.cache_duration: float = 30.0  # 30 segundos de cache

        self.logger.info(f"CameraManager inicializado (max: {max_cameras}, timeout: {detection_timeout}s)")

    def get_system_backend(self) -> CameraBackend:
        """
        Determina el backend óptimo según el sistema operativo.

        Returns:
            Backend recomendado para el sistema
        """
        system = platform.system()

        if system == "Windows":
            # En Windows, DSHOW es más estable que MSMF para webcams
            return CameraBackend.DSHOW
        elif system == "Linux":
            return CameraBackend.V4L2
        elif system == "Darwin":  # Mac
            return CameraBackend.AVFOUNDATION
        else:
            return CameraBackend.AUTO

    def validate_camera_hardware(
            self,
            index: int,
            backend: CameraBackend
    ) -> Optional[CameraInfo]:
        """
        Prueba una cámara específica con un backend dado.

        Args:
            index: Índice de la cámara
            backend: Backend de OpenCV a usar

        Returns:
            CameraInfo si la cámara funciona, None si falla
        """
        cap = None
        try:
            # Intentar abrir con el backend especificado
            cap = cv2.VideoCapture(index, backend.value)

            if not cap.isOpened():
                return None

            # Esperar un poco para que la cámara se inicialice
            time.sleep(0.1)

            # Obtener propiedades
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            # Validar capturando frames reales
            frames_captured = 0
            for _ in range(self.validation_frames):
                ret, frame = cap.read()
                if ret and frame is not None:
                    frames_captured += 1
                time.sleep(0.05)  # Pequeña pausa entre frames

            # La cámara debe capturar al menos 2 de 3 frames
            is_working = frames_captured >= (self.validation_frames - 1)

            if not is_working:
                error_msg = f"Solo capturó {frames_captured}/{self.validation_frames} frames"
                return CameraInfo(
                    index=index,
                    name=f"Cámara {index} (No funcional)",
                    backend=backend.name,
                    width=width,
                    height=height,
                    fps=fps,
                    is_working=False,
                    error_message=error_msg
                )

            # Obtener nombre de la cámara y si es externa
            camera_name, is_external = self._get_camera_name(index, backend)

            return CameraInfo(
                index=index,
                name=camera_name,
                backend=backend.name,
                width=width if width > 0 else 640,
                height=height if height > 0 else 480,
                fps=fps if fps > 0 else 30.0,
                is_working=True,
                is_external=is_external
            )

        except Exception as e:
            self.logger.debug(f"Error probando cámara {index} con {backend.name}: {e}")
            return None
        finally:
            if cap is not None:
                cap.release()

    def _get_camera_name(self, index: int, backend: CameraBackend) -> Tuple[str, bool]:
        """
        Intenta obtener el nombre de la cámara y determina si es externa.

        Args:
            index: Índice de la cámara
            backend: Backend usado

        Returns:
            Tupla (nombre_descriptivo, es_externa)
        """
        # REGLA: Índice 0 es casi siempre la cámara integrada en portátiles
        # Índices 1+ son típicamente USB externas

        is_external = False
        camera_name = f"Cámara {index}"

        if platform.system() == "Windows":
            try:
                if index == 0:
                    camera_name = "Cámara Integrada"
                    is_external = False
                else:
                    # Índices mayores a 0 son probablemente USB externas
                    camera_name = f"Cámara USB Externa {index}"
                    is_external = True
            except:
                pass
        elif platform.system() == "Linux":
            # En Linux, intentar leer desde /sys/class/video4linux/
            try:
                device_path = f"/sys/class/video4linux/video{index}/name"
                with open(device_path, 'r') as f:
                    device_name = f.read().strip()
                    # Detectar si contiene palabras clave de USB
                    if any(keyword in device_name.lower() for keyword in ['usb', 'logitech', 'webcam', 'external']):
                        camera_name = device_name
                        is_external = True
                    elif index == 0:
                        camera_name = "Cámara Integrada"
                        is_external = False
                    else:
                        camera_name = device_name
                        is_external = True  # Asumir externa si no es índice 0
            except:
                # Si falla la lectura, usar heurística por índice
                if index == 0:
                    camera_name = "Cámara Integrada"
                    is_external = False
                else:
                    camera_name = f"Cámara USB {index}"
                    is_external = True
        elif platform.system() == "Darwin":  # macOS
            if index == 0:
                camera_name = "Cámara Integrada"
                is_external = False
            else:
                camera_name = f"Cámara USB {index}"
                is_external = True
        else:
            # Otros sistemas: usar heurística por índice
            if index == 0:
                camera_name = "Cámara Integrada"
                is_external = False
            else:
                camera_name = f"Cámara Externa {index}"
                is_external = True

        return camera_name, is_external

    def detect_cameras(
            self,
            force_refresh: bool = False
    ) -> List[CameraInfo]:
        """
        Detecta cámaras disponibles de forma LIGERA Y RÁPIDA.
        Solo comprueba si la cámara "existe" en el índice, no si funciona.
        La validación de hardware (lectura de frames) se hace por separado.

        Args:
            force_refresh: Si True, ignora caché y redetecta

        Returns:
            Lista de CameraInfo (con is_working=False, ya que no están validadas)
        """
        # --- INICIO DE CAMBIOS ---

        # Verificar si podemos usar caché
        current_time = time.time()
        if not force_refresh and self.cached_cameras:
            if (current_time - self.last_detection_time) < self.cache_duration:
                self.logger.debug("Usando cámaras en caché (detección ligera)")
                return self.cached_cameras

        self.logger.info("Iniciando detección LIGERA de cámaras (sondeo de índices)...")
        detected_cameras: List[CameraInfo] = []
        backend = self.get_system_backend()
        self.logger.info(f"Usando backend: {backend.name} para {platform.system()}")

        for index in range(self.max_cameras):
            cap = None
            try:
                cap = cv2.VideoCapture(index, backend.value)
                # La comprobación 'isOpened' es la clave. Es rápida.
                if cap.isOpened():
                    # Obtenemos nombre y heurística (rápido, no usa hardware)
                    camera_name, is_external = self._get_camera_name(index, backend)

                    # Creamos la info, pero marcamos como NO FUNCIONAL (no validada)
                    camera_info = CameraInfo(
                        index=index,
                        name=camera_name,
                        backend=backend.name,
                        width=0,  # No sabemos la res aún
                        height=0,  # No sabemos la res aún
                        fps=0,  # No sabemos los FPS aún
                        is_working=False,  # ¡Importante! No está validada por hardware
                        is_external=is_external,
                        error_message="Pendiente de validacion"
                    )
                    detected_cameras.append(camera_info)
                    self.logger.info(f"✓ Sonda: Cámara encontrada en índice {index} ({camera_name})")
                else:
                    # Si no hay cámara en el índice 0, 1 y 2, paramos
                    if index >= 2 and not detected_cameras:
                        self.logger.debug("No se encontraron cámaras en los primeros 3 índices, deteniendo sondeo.")
                        break

            except Exception:
                # Ignorar errores durante el sondeo
                pass
            finally:
                if cap is not None:
                    cap.release()  # Liberar inmediatamente

        # Actualizar caché
        self.cached_cameras = detected_cameras
        self.last_detection_time = current_time

        self.logger.info(f"Sondeo completado: {len(detected_cameras)} cámara(s) encontrada(s) (pendientes de validar)")
        return detected_cameras
        # --- FIN DE CAMBIOS ---

    def get_camera_info(self, index: int) -> Optional[CameraInfo]:
        """
        Obtiene información de hardware COMPLETA de una cámara específica.
        Utiliza la validación "pesada".

        Args:
            index: Índice de la cámara

        Returns:
            CameraInfo si existe, None si no
        """
        # --- INICIO DE CAMBIOS ---
        self.logger.debug(f"Validando hardware de cámara {index}...")
        backend = self.get_system_backend()

        # 1. Usar la validación pesada
        camera_info = self.validate_camera_hardware(index, backend)

        # 2. Si falla, reintentar con AUTO (si no es ya AUTO)
        if camera_info is None and backend != CameraBackend.AUTO:
            self.logger.debug(f"Reintentando validación de {index} con backend AUTO")
            camera_info = self.validate_camera_hardware(index, CameraBackend.AUTO)

        return camera_info
        # --- FIN DE CAMBIOS ---

    def validate_camera(self, index: int) -> Tuple[bool, Optional[str]]:
        """
        Valida que una cámara funcione correctamente (lectura de frames).
        Utiliza la validación "pesada".

        Args:
            index: Índice de la cámara a validar

        Returns:
            Tupla (es_válida, mensaje_error)
        """
        # --- INICIO DE CAMBIOS ---
        # get_camera_info ahora hace la validación pesada
        camera_info = self.get_camera_info(index)
        # --- FIN DE CAMBIOS ---

        if camera_info is None:
            return False, f"No se pudo acceder a la cámara {index} (isOpened falló)"

        if not camera_info.is_working:
            return False, camera_info.error_message

        return True, None

    def get_best_camera(self) -> Optional[CameraInfo]:
        """
        Obtiene la mejor cámara disponible (validada por hardware).

        Prioriza:
        1. Cámaras USB EXTERNAS sobre integradas
        2. Cámara con mayor resolución
        3. Cámara con mayor FPS
        4. Cámara con índice más bajo

        Returns:
            CameraInfo de la mejor cámara o None
        """
        # --- INICIO DE CAMBIOS ---

        # 1. Detección LIGERA: Obtener lista de candidatas (rápido)
        candidate_cameras = self.detect_cameras()
        if not candidate_cameras:
            self.logger.warning("get_best_camera: No se encontraron cámaras en el sondeo ligero.")
            return None

        # 2. Detección PESADA: Validar por hardware solo las candidatas
        self.logger.info(f"get_best_camera: Validando hardware de {len(candidate_cameras)} candidata(s)...")
        working_cameras: List[CameraInfo] = []
        for probe_info in candidate_cameras:
            # get_camera_info hace la validación pesada
            camera_info = self.get_camera_info(probe_info.index)
            if camera_info and camera_info.is_working:
                working_cameras.append(camera_info)

        if not working_cameras:
            self.logger.error("get_best_camera: Ninguna de las cámaras candidatas pasó la validación de hardware.")
            return None
        # --- FIN DE CAMBIOS ---

        # 3. Separar externas de integradas (Lógica de prioridad)
        external_cameras = [c for c in working_cameras if c.is_external]
        internal_cameras = [c for c in working_cameras if not c.is_external]

        cameras_to_evaluate = external_cameras if external_cameras else internal_cameras

        if not cameras_to_evaluate:
            return working_cameras[0]  # Fallback por si acaso

        # 4. Ordenar por resolución (área) y FPS
        cameras_sorted = sorted(
            cameras_to_evaluate,
            key=lambda c: (c.width * c.height, c.fps, -c.index),
            reverse=True
        )

        best_camera = cameras_sorted[0]

        if best_camera.is_external:
            self.logger.info(f"✓ Mejor cámara (Hardware validado): USB EXTERNA - {best_camera.name}")
        else:
            self.logger.info(
                f"⚠ Mejor cámara (Hardware validado): INTEGRADA - {best_camera.name} (no se encontraron externas)")

        return best_camera

    def get_fallback_camera(self, exclude_index: int = -1) -> Optional[CameraInfo]:
        """
        Obtiene una cámara alternativa cuando falla la principal.

        Args:
            exclude_index: Índice a excluir de la búsqueda

        Returns:
            CameraInfo de cámara alternativa o None
        """
        cameras = self.detect_cameras()

        # Filtrar cámara excluida
        available_cameras = [c for c in cameras if c.index != exclude_index]

        if not available_cameras:
            return None

        # Retornar la primera disponible
        return available_cameras[0]

    def create_camera_selector_data(self) -> List[Dict[str, any]]:
        """
        Crea datos formateados para un selector de cámaras en UI.

        Returns:
            Lista de diccionarios con datos para ComboBox
        """
        cameras = self.detect_cameras()

        selector_data = []
        for camera in cameras:
            if camera.is_working:
                display_text = f"{camera.name} - {camera.width}x{camera.height}"
                selector_data.append({
                    'index': camera.index,
                    'text': display_text,
                    'camera_info': camera
                })

        return selector_data

    def test_camera_with_preview(
            self,
            index: int,
            duration: float = 3.0
    ) -> bool:
        """
        Prueba una cámara mostrando preview temporal.

        Args:
            index: Índice de la cámara
            duration: Duración del preview en segundos

        Returns:
            True si funcionó correctamente
        """
        backend = self.get_system_backend()
        cap = None

        try:
            cap = cv2.VideoCapture(index, backend.value)

            if not cap.isOpened():
                self.logger.error(f"No se pudo abrir cámara {index} para preview")
                return False

            self.logger.info(f"Mostrando preview de cámara {index} por {duration}s...")

            start_time = time.time()
            frames_shown = 0

            while (time.time() - start_time) < duration:
                ret, frame = cap.read()

                if not ret or frame is None:
                    self.logger.warning("No se pudo leer frame")
                    continue

                # Añadir texto al frame
                cv2.putText(
                    frame,
                    f"Probando camara {index}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )

                cv2.imshow(f'Preview Camara {index}', frame)
                frames_shown += 1

                # Permitir cerrar con ESC
                if cv2.waitKey(1) & 0xFF == 27:
                    break

            cv2.destroyAllWindows()

            success = frames_shown > 0
            if success:
                self.logger.info(f"✓ Preview exitoso: {frames_shown} frames mostrados")
            else:
                self.logger.error("✗ No se pudo mostrar ningún frame")

            return success

        except Exception as e:
            self.logger.error(f"Error en preview de cámara: {e}")
            return False
        finally:
            if cap is not None:
                cap.release()
            cv2.destroyAllWindows()


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def quick_detect_cameras() -> List[CameraInfo]:
    """
    Función rápida para detectar cámaras.

    Returns:
        Lista de CameraInfo
    """
    manager = CameraManager(max_cameras=5, detection_timeout=1.0)
    return manager.detect_cameras()


def get_working_camera_index() -> Optional[int]:
    """
    Obtiene el índice de una cámara que funcione.

    Returns:
        Índice de cámara funcional o None
    """
    cameras = quick_detect_cameras()
    if cameras:
        return cameras[0].index
    return None


def validate_camera_index(index: int) -> bool:
    """
    Valida que un índice de cámara funcione.

    Args:
        index: Índice a validar

    Returns:
        True si funciona, False si no
    """
    manager = CameraManager()
    is_valid, _ = manager.validate_camera(index)
    return is_valid


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 70)
    print("GESTOR DE CÁMARAS - Test de Detección")
    print("=" * 70)

    # Crear gestor
    manager = CameraManager(max_cameras=10)

    # Detectar cámaras
    print("\n1. Detectando cámaras...")
    cameras = manager.detect_cameras()

    if not cameras:
        print("✗ No se encontraron cámaras")
    else:
        print(f"\n✓ Se encontraron {len(cameras)} cámara(s):\n")
        for camera in cameras:
            print(f"  • {camera}")

        # Obtener mejor cámara
        best = manager.get_best_camera()
        print(f"\n📹 Mejor cámara: {best}")

        # Preguntar si probar
        print("\n¿Deseas probar la mejor cámara con preview? (s/n): ", end='')
        try:
            respuesta = input().lower()
            if respuesta == 's':
                print("\nMostrando preview (3 segundos)...")
                print("Presiona ESC para cerrar antes")
                manager.test_camera_with_preview(best.index, duration=3.0)
        except:
            pass

    print("\n" + "=" * 70)
    print("Test completado")
    print("=" * 70)