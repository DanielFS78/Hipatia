"""
========================================================================
ESCÁNER DE CÓDIGOS QR - SISTEMA DE TRAZABILIDAD (OpenCV)
========================================================================
Escanea códigos QR en tiempo real usando SOLO OpenCV (sin pyzbar).
Compatible con Windows sin necesidad de DLLs adicionales.

Características:
- Escaneo en tiempo real con OpenCV nativo
- Dos modos de operación: CONSULTA y TRABAJO
- Modo CONSULTA: Ver información sin registrar
- Modo TRABAJO: Iniciar/finalizar trabajos
- Validación de formato de QR
- Decodificación de información del QR

Autor: Sistema de Trazabilidad
Fecha: 2025
Versión: 2.0 (OpenCV nativo)
========================================================================
"""

import logging
try:
    import cv2
except (ImportError, AttributeError):
    from unittest.mock import MagicMock
    cv2 = MagicMock()
from typing import Optional, Dict, Tuple, Callable
from datetime import datetime
import re
import os
from core.camera_manager import CameraManager, CameraInfo

# Intentar importar WeChatQRCode (requiere opencv-contrib-python)
try:
    from cv2 import wechat_qrcode_WeChatQRCode
    HAS_WECHAT_QR = True
except ImportError:
    HAS_WECHAT_QR = False

class QrScanner:
    """
    Escáner de códigos QR para trazabilidad usando OpenCV.

    Esta versión usa el detector QR nativo de OpenCV, eliminando la
    dependencia de pyzbar que tiene problemas en Windows.

    Soporta dos modos de operación:
    - CONSULTA: Solo muestra información del QR sin registrar nada
    - TRABAJO: Registra inicio/fin de trabajo en la base de datos

    Attributes:
        logger: Logger para registro de operaciones
        camera_index: Índice de la cámara (0 por defecto)
        camera: Objeto VideoCapture de OpenCV
        qr_detector: Detector QR (WeChatQRCode o QRCodeDetector fallback)
        use_wechat: Booleano indicando si se está usando el motor optimizado
        last_scan: Último QR escaneado (para evitar lecturas duplicadas)
        scan_cooldown: Tiempo mínimo entre escaneos del mismo QR (segundos)
    """

    def __init__(self, camera_manager: CameraManager, camera_index: int, camera_object: cv2.VideoCapture):
        """
        Inicializa el escáner de QR.
        MODIFICADO: Acepta un objeto de cámara YA ABIERTO.

        Args:
            camera_manager: La instancia global de CameraManager.
            camera_index: Índice de la cámara a usar.
            camera_object: La instancia de cv2.VideoCapture ya inicializada.
        """
        self.logger = logging.getLogger("EvolucionTiemposApp.QrScanner")

        # --- INICIO DE CAMBIOS ---
        self.camera_manager = camera_manager
        self.camera_index = camera_index
        self.camera = camera_object  # Aceptamos el objeto ya creado
        self.logger.info(f"QrScanner inicializado con manager y objeto de cámara (índice {camera_index})")
        
        # --- Inicialización del Motor de Escaneo (WeChatQRCode) ---
        self.use_wechat = False
        self.qr_detector = None
        self._init_detector()

        self.last_scan = None
        self.last_scan_time = None
        self.scan_cooldown = 4.0
        self.is_camera_ready = False
        self.is_camera_ready = self.initialize_camera()

        if self.is_camera_ready:
            self.logger.info(f"QrScanner recibió una cámara lista (índice {self.camera_index})")
        else:
            self.logger.error(f"QrScanner recibió una cámara NO VÁLIDA (índice {self.camera_index})")

    def _init_detector(self):
        """Inicializa el mejor detector disponible."""
        # Rutas a los modelos (asumiendo estructura core/models/)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(base_dir, "models")
        
        detect_proto = os.path.join(models_dir, "detect.prototxt")
        detect_caffe = os.path.join(models_dir, "detect.caffemodel")
        sr_proto = os.path.join(models_dir, "sr.prototxt")
        sr_caffe = os.path.join(models_dir, "sr.caffemodel")
        
        models_exist = (os.path.exists(detect_proto) and os.path.exists(detect_caffe) and 
                        os.path.exists(sr_proto) and os.path.exists(sr_caffe))

        if HAS_WECHAT_QR and models_exist:
            try:
                self.logger.info("Inicializando WeChatQRCode (Motor Optimizado)...")
                self.qr_detector = wechat_qrcode_WeChatQRCode(
                    detect_proto, detect_caffe, sr_proto, sr_caffe
                )
                self.use_wechat = True
                self.logger.info("✓ WeChatQRCode inicializado correctamente")
            except Exception as e:
                self.logger.error(f"Error cargando modelos WeChatQRCode: {e}")
                self._fallback_detector()
        else:
            if not HAS_WECHAT_QR:
                self.logger.warning("WeChatQRCode no disponible en cv2 (opencv-contrib-python faltante?).")
            if not models_exist:
                self.logger.warning(f"Modelos de WeChatQRCode no encontrados en {models_dir}")
            self._fallback_detector()

    def _fallback_detector(self):
        """Inicializa el detector estándar de OpenCV como respaldo."""
        self.logger.info("Usando cv2.QRCodeDetector estándar (Rendimiento Básico)")
        self.qr_detector = cv2.QRCodeDetector()
        self.use_wechat = False

    def initialize_camera(self) -> bool:
        """
        VERSIÓN SÚPER-SIMPLIFICADA: Solo comprueba si el objeto
        de cámara recibido es válido y está abierto.
        """
        if self.camera and self.camera.isOpened():
            self.logger.info("El objeto de cámara recibido es válido y está abierto.")
            self.is_camera_ready = True
            return True
        else:
            self.logger.error("El objeto de cámara recibido es None o no está abierto.")
            self.is_camera_ready = False
            return False

    def _check_cooldown(self, data: str) -> bool:
        """Comprueba si el QR escaneado está en período de enfriamiento."""
        now = datetime.now()
        if self.last_scan == data and self.last_scan_time:
            elapsed = (now - self.last_scan_time).total_seconds()
            if elapsed < self.scan_cooldown:
                # Cooldown activo
                return True

        # Actualizar último escaneo
        self.last_scan = data
        self.last_scan_time = now
        return False

    def release_camera(self):
        """Libera la cámara y cierra ventanas de OpenCV."""
        if self.camera is not None:
            self.logger.info("Liberando cámara...")  # Log movido al inicio
            self.camera.release()

            self.camera = None  # Importante para forzar reinicialización
            self.is_camera_ready = False  # Actualizar estado

            cv2.destroyAllWindows()
            self.logger.info("Cámara liberada y estado reseteado")
        else:
            # Si ya está liberada, solo asegurar que las ventanas se cierren
            cv2.destroyAllWindows()

    def scan_frame(self, frame) -> Tuple[Optional[str], Optional[any]]:
        """
        Escanea un frame en busca de códigos QR usando OpenCV.
        MODIFICADO: Redimensiona el frame a 640px para acelerar la detección.
        """

        # --- 1. Redimensionar Frame para Análisis ---
        try:
            original_h, original_w = frame.shape[:2]

            # --- CAMBIO CLAVE: 800 -> 640 ---
            # 640px es el punto dulce para velocidad/fiabilidad de cv2
            target_w = 640

            if original_w <= target_w:
                scale_factor = 1.0
                small_frame = frame
            else:
                scale_factor = original_w / float(target_w)
                target_h = int(original_h / scale_factor)
                small_frame = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
        except Exception as e:
            self.logger.error(f"Error redimensionando frame: {e}")
            small_frame = frame  # Fallback
            scale_factor = 1.0

            # --- 2. Analizar el Frame Pequeño ---
            try:
                # No necesitamos conversión a gris/threshold manual tan agresiva con WeChatQRCode
                # pero mantenemos la lógica básica por si acaso
                
                # WeChatQRCode funciona excelente con BGR directo,
                # pero si falla, probamos con gris.
                images_to_try = [small_frame]
                
                # Si usamos el detector estándar, mantenemos la lógica antigua de gris/threshold
                if not self.use_wechat:
                    gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
                    thresh_adapt = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                       cv2.THRESH_BINARY, 11, 2)
                    images_to_try = [gray, thresh_adapt]

                data = None
                bbox = None  # Bbox en la escala pequeña

                for img in images_to_try:
                    try:
                        if self.use_wechat:
                            # WeChatQRCode devuelve una lista de resultados
                            res, points = self.qr_detector.detectAndDecode(img)
                            if res and len(res) > 0:
                                data = res[0]  # Tomamos el primero
                                bbox = points[0] # Tomamos los puntos del primero
                        else:
                            # Detector estándar
                            d, b, _ = self.qr_detector.detectAndDecode(img)
                            if d:
                                data = d
                                bbox = b
                    except cv2.error as e:
                        self.logger.debug(f"Excepción interna de OpenCV en detectAndDecode: {e}")
                        continue

                    if data:
                        break # Encontrado!
                    
                    if not self.use_wechat and bbox is not None and data is None:
                        # Para el detector estándar, a veces detecta caja sin datos
                        # Para WeChat suele ser todo o nada
                        pass

                # --- 3. Lógica de Retorno con Re-escalado ---
                scaled_bbox = None
                if bbox is not None:
                    # Normalizar bbox para que sea consistente
                    # WeChat devuelve float32 (4, 2), standard devuelve float32 (1, 4, 2)
                    
                    current_bbox = bbox
                    if self.use_wechat:
                         # Asegurar formato similar al standar para compatibilidad (1, 4, 2)
                         # Aunque draw_qr_detection lo arreglaremos para que sea agnóstico
                         pass
                    
                    # Escalar
                    scaled_bbox = current_bbox * scale_factor

                if data:
                    if self._check_cooldown(data):
                        return (None, scaled_bbox)

                    self.logger.info(f"QR escaneado ({'WeChat' if self.use_wechat else 'Std'}): {data}")
                    return (data, scaled_bbox)

                if scaled_bbox is not None:
                    return (None, scaled_bbox) 

                return (None, None)

            except Exception as e:
                self.logger.error(f"Error grave en lógica de detección: {e}", exc_info=True)
                return (None, None)

    def draw_qr_detection(self, frame, qr_data: Optional[str], bbox: Optional[any]):
        """
        Dibuja indicadores visuales en el frame.
        MODIFICADO: Acepta bbox como argumento.

        Args:
            frame: Frame de OpenCV
            qr_data: Datos del QR detectado (opcional)
            bbox: Bounding box del QR detectado (opcional)

        Returns:
            Frame con los indicadores dibujados
        """
        try:
            # --- INICIO DE CAMBIOS ---
            # ELIMINADA la llamada a self.qr_detector.detectAndDecode(frame)
            # Ahora usamos el 'bbox' que recibimos como argumento
            # --- FIN DE CAMBIOS ---

            if bbox is not None:
                # Convertir bbox a puntos enteros
                # Manejar diferentes formatos de bbox (WeChat vs Standard)
                points = bbox
                
                # Estandarizar a lista de puntos (4, 2)
                if len(points.shape) == 3: # (1, 4, 2) del standard
                    points = points[0]
                
                points = points.astype(int)

                # Dibujar rectángulo verde alrededor del QR
                for i in range(4):
                    pt1 = tuple(points[i])
                    pt2 = tuple(points[(i + 1) % 4])
                    cv2.line(frame, pt1, pt2, (0, 255, 0), 3)

                # Mostrar texto del QR si está disponible
                if qr_data:
                    x, y = points[0]
                    # Truncar texto si es muy largo
                    text = qr_data[:35] + "..." if len(qr_data) > 35 else qr_data

                    # Fondo negro para mejor legibilidad
                    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                    cv2.rectangle(frame, (x, y - 35), (x + text_size[0] + 5, y - 5), (0, 0, 0), -1)

                    # Texto en verde
                    cv2.putText(frame, text, (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Si hay datos escaneados recientemente, mostrar confirmación grande
            if qr_data:
                # Mensaje de confirmación en la parte superior
                msg = "QR DETECTADO!"
                text_size = cv2.getTextSize(msg, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]

                # Fondo verde
                cv2.rectangle(frame, (5, 5), (text_size[0] + 15, 45), (0, 255, 0), -1)

                # Texto negro
                cv2.putText(frame, msg, (10, 35),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)

            # Instrucciones en la parte inferior
            instructions = "Presiona ESC para cancelar"
            cv2.putText(frame, instructions, (10, frame.shape[0] - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            return frame

        except Exception as e:
            self.logger.error(f"Error dibujando detección: {e}")
            return frame

    def parse_qr_data(self, qr_data: str) -> Optional[Dict]:
        """
        Parsea el contenido de un QR de trazabilidad.

        Formato esperado: FAB{id}-{producto}-UNIT{num}-{timestamp}-{hash}
        Ejemplo: FAB123-PROD001-UNIT1-20250131143022-A3F9

        Args:
            qr_data: Contenido del QR

        Returns:
            Diccionario con la información parseada o None si el formato no es válido
        """
        try:
            # Patrón para validar el formato
            pattern = r'FAB(\d+)-([A-Z0-9/]+)-UNIT(\d+)-(\d{14})-([A-F0-9]{4})'
            # (He modificado el patrón para aceptar tu código de producto con '/')

            match = re.match(pattern, qr_data)

            if not match:
                self.logger.warning(f"QR con formato inválido: {qr_data}")
                return None

            fabricacion_id, producto_codigo, unit_number, timestamp_str, hash_code = match.groups()

            # Parsear timestamp
            timestamp = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')

            return {
                'valido': True,
                'fabricacion_id': int(fabricacion_id),
                'producto_codigo': producto_codigo,
                'unit_number': int(unit_number),
                'timestamp': timestamp,
                'hash': hash_code,
                'qr_completo': qr_data
            }

        except Exception as e:
            self.logger.error(f"Error parseando QR: {e}")
            return None

    def validate_qr_format(self, qr_data: str) -> bool:
        """
        Valida que un QR tenga el formato correcto de trazabilidad.

        Args:
            qr_data: Contenido del QR

        Returns:
            True si el formato es válido, False si no
        """
        parsed = self.parse_qr_data(qr_data)
        return parsed is not None and parsed.get('valido', False)

    def scan_once(self, timeout: int = 30) -> Optional[str]:
        """
        Escanea hasta detectar un QR (bloqueo).
        USA LA CÁMARA YA INICIALIZADA.
        """
        # 1. Comprobar si la cámara está lista
        if not self.is_camera_ready:
            self.logger.error("Se llamó a scan_once() pero la cámara no está lista.")
            # Intentar reinicializarla como último recurso
            if not self.initialize_camera():
                self.logger.error("Fallo al reinicializar la cámara.")
                return None

        # 2. Comprobación de seguridad
        if self.camera is None or not self.camera.isOpened():
            self.logger.error("Error crítico: Objeto de cámara no existe o no está abierto.")
            self.is_camera_ready = False
            return None

        try:
            start_time = datetime.now()
            window_name = 'Escaner QR - Acerca un codigo QR a la camara'  # Nombre de ventana

            self.logger.info("Iniciando escaneo de QR... (Presiona ESC para cancelar)")

            while True:
                # Verificar timeout
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > timeout:
                    self.logger.warning(f"Timeout de {timeout}s alcanzado esperando QR")
                    return None

                # Leer frame
                ret, frame = self.camera.read()
                if not ret:
                    self.logger.warning("No se pudo leer frame de la cámara")
                    cv2.waitKey(10)
                    continue

                # --- INICIO DE CAMBIOS ---
                # 1. Escanear y obtener AMBOS resultados
                qr_data, bbox = self.scan_frame(frame)

                # 2. Dibujar detección y decoraciones, pasando AMBOS resultados
                frame = self.draw_qr_detection(frame, qr_data, bbox)
                # --- FIN DE CAMBIOS ---

                # Añadir contador de tiempo
                time_left = int(timeout - elapsed)
                cv2.putText(frame, f"Tiempo: {time_left}s", (frame.shape[1] - 120, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                # Mostrar frame
                cv2.imshow(window_name, frame)  # Usar nombre de ventana

                # Si se detectó QR, retornar
                if qr_data:
                    self.logger.info("QR detectado exitosamente")
                    return qr_data

                # Verificar tecla ESC
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC
                    self.logger.info("Escaneo cancelado por usuario")
                    return None

        except Exception as e:
            self.logger.error(f"Error durante el escaneo: {e}")
            return None
        finally:
            # ¡¡NO LIBERAR LA CÁMARA!!
            # Solo cerrar la ventana de escaneo
            self.logger.info("Cerrando ventana de escaneo, pero la cámara sigue lista.")
            cv2.destroyWindow(window_name)

    def get_qr_info_for_display(self, qr_data: str) -> str:
        """
        Obtiene información formateada del QR para mostrar al usuario.

        Args:
            qr_data: Contenido del QR

        Returns:
            String con información formateada
        """
        parsed = self.parse_qr_data(qr_data)

        if not parsed or not parsed.get('valido', False):
            return f"⚠️ QR NO VÁLIDO\n\nContenido: {qr_data}"

        info = f"""✓ QR VÁLIDO

Fabricación: FAB{parsed['fabricacion_id']}
Producto: {parsed['producto_codigo']}
Unidad: #{parsed['unit_number']}
Generado: {parsed['timestamp'].strftime('%d/%m/%Y %H:%M:%S')}
Hash: {parsed['hash']}

Código completo:
{qr_data}"""

        return info

    def set_camera_index(self, new_index: int) -> bool:
        """
        Permite cambiar la cámara activa del escáner.
        Libera la cámara antigua e inicializa la nueva.

        Args:
            new_index: El nuevo índice de cámara a usar.

        Returns:
            True si la nueva cámara se inicializó con éxito, False si no.
        """
        self.logger.info(f"Solicitud para cambiar a cámara índice {new_index}")

        # Si el índice es el mismo y la cámara ya funciona, no hacer nada
        if new_index == self.camera_index and self.is_camera_ready:
            self.logger.info(f"La cámara {new_index} ya está activa y lista.")
            return True

        # 1. Liberar la cámara antigua (si está abierta)
        self.release_camera()

        # 2. Actualizar al nuevo índice
        self.camera_index = new_index

        # 3. Inicializar la nueva cámara
        self.is_camera_ready = self.initialize_camera()

        if self.is_camera_ready:
            self.logger.info(f"✓ Cámara cambiada y lista (índice {self.camera_index})")
        else:
            self.logger.error(f"✗ Fallo al cambiar a la cámara {self.camera_index}")

        return self.is_camera_ready


class QrScannerCallback:
    """
    Clase auxiliar para manejar callbacks del escáner.

    Permite definir acciones personalizadas cuando se escanea un QR
    en diferentes modos (consulta o trabajo).
    """

    def __init__(
            self,
            on_consulta: Optional[Callable[[str, Dict], None]] = None,
            on_trabajo: Optional[Callable[[str, Dict], bool]] = None
    ):
        """
        Inicializa los callbacks.

        Args:
            on_consulta: Función a llamar en modo consulta (qr_data, parsed_info)
            on_trabajo: Función a llamar en modo trabajo (qr_data, parsed_info) -> bool
        """
        self.on_consulta = on_consulta
        self.on_trabajo = on_trabajo

    def handle_consulta(self, qr_data: str, parsed_info: Dict):
        """Maneja escaneo en modo consulta."""
        if self.on_consulta:
            self.on_consulta(qr_data, parsed_info)

    def handle_trabajo(self, qr_data: str, parsed_info: Dict) -> bool:
        """Maneja escaneo en modo trabajo."""
        if self.on_trabajo:
            return self.on_trabajo(qr_data, parsed_info)
        return False


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def scan_qr_simple(camera_index: int = 0, timeout: int = 30) -> Optional[str]:
    """
    DEPRECATED: Esta función no es compatible con la nueva API de QrScanner.
    
    Use QrScanner directamente con un CameraManager y camera_object.
    
    Args:
        camera_index: Índice de la cámara
        timeout: Tiempo máximo de espera

    Returns:
        Contenido del QR o None
        
    Raises:
        DeprecationWarning: Esta función está obsoleta
    """
    import warnings
    warnings.warn(
        "scan_qr_simple() está obsoleta. Use QrScanner con CameraManager directamente.",
        DeprecationWarning,
        stacklevel=2
    )
    # Intentar crear scanner con la API antigua causará error
    # Retornamos None para evitar crash
    return None


def validate_qr(qr_data: str) -> bool:
    """
    Función de utilidad para validar formato de QR.
    
    Esta función NO requiere cámara y valida el formato usando regex.

    Args:
        qr_data: Contenido del QR

    Returns:
        True si es válido, False si no

    Example:
        >>> qr = "FAB123-PROD001-UNIT1-20250131143022-A3F9"
        >>> if validate_qr(qr):
        ...     print("QR válido")
    """
    # Patrón validación standalone (sin necesidad de instancia de QrScanner)
    pattern = r'FAB(\d+)-([A-Z0-9/]+)-UNIT(\d+)-(\d{14})-([A-F0-9]{4})'
    return re.match(pattern, qr_data) is not None


def get_qr_info(qr_data: str) -> Optional[Dict]:
    """
    Función de utilidad para obtener información de un QR.
    
    Esta función NO requiere cámara y parsea el formato usando regex.

    Args:
        qr_data: Contenido del QR

    Returns:
        Diccionario con información o None

    Example:
        >>> qr = "FAB123-PROD001-UNIT1-20250131143022-A3F9"
        >>> info = get_qr_info(qr)
        >>> if info:
        ...     print(f"Producto: {info['producto_codigo']}")
    """
    # Parseo standalone (sin necesidad de instancia de QrScanner)
    pattern = r'FAB(\d+)-([A-Z0-9/]+)-UNIT(\d+)-(\d{14})-([A-F0-9]{4})'
    match = re.match(pattern, qr_data)
    
    if not match:
        return None
    
    fabricacion_id, producto_codigo, unit_number, timestamp_str, hash_code = match.groups()
    
    try:
        timestamp = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
    except ValueError:
        return None
    
    return {
        'valido': True,
        'fabricacion_id': int(fabricacion_id),
        'producto_codigo': producto_codigo,
        'unit_number': int(unit_number),
        'timestamp': timestamp,
        'hash': hash_code,
        'qr_completo': qr_data
    }


# ============================================================================
# MAIN - PARA PRUEBAS
# ============================================================================

if __name__ == "__main__":
    """
    Script de prueba para verificar el funcionamiento del escáner.
    Ejecutar: python qr_scanner.py
    """
    print("=" * 70)
    print("TEST: Escáner de Códigos QR (OpenCV)")
    print("=" * 70)

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n1. Probando detección de cámara...")
    scanner = QrScanner()
    if scanner.initialize_camera():
        print("✓ Cámara detectada correctamente")
        scanner.release_camera()
    else:
        print("✗ No se pudo detectar la cámara")
        exit(1)

    print("\n2. Probando validación de formato...")
    qr_valido = "FAB123-PROD001-UNIT1-20250131143022-A3F9"
    qr_invalido = "INVALID-QR"

    if validate_qr(qr_valido):
        print(f"✓ QR válido reconocido: {qr_valido}")
    else:
        print(f"✗ Error: QR válido no reconocido")

    if not validate_qr(qr_invalido):
        print(f"✓ QR inválido rechazado: {qr_invalido}")
    else:
        print(f"✗ Error: QR inválido aceptado")

    print("\n3. Probando parseo de información...")
    info = get_qr_info(qr_valido)
    if info:
        print("✓ Información parseada correctamente:")
        print(f"  - Fabricación: {info['fabricacion_id']}")
        print(f"  - Producto: {info['producto_codigo']}")
        print(f"  - Unidad: {info['unit_number']}")
        print(f"  - Hash: {info['hash']}")

    print("\n" + "=" * 70)
    print("Pruebas básicas completadas. ¿Quieres probar el escaneo real?")
    print("(Necesitas tener un QR impreso o en pantalla)")
    respuesta = input("Probar escaneo? (s/n): ")

    if respuesta.lower() == 's':
        print("\nIniciando escaneo (30 segundos de timeout)...")
        print("Presiona ESC para cancelar")
        qr_result = scan_qr_simple(timeout=30)

        if qr_result:
            print(f"\n✓ QR ESCANEADO: {qr_result}")
            info = get_qr_info(qr_result)
            if info:
                print("\nInformación del QR:")
                print(scanner.get_qr_info_for_display(qr_result))
        else:
            print("\n✗ No se detectó ningún QR")

    print("\n" + "=" * 70)
    print("Test completado")
    print("=" * 70)