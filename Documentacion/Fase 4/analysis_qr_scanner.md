# Analysis of qr_scanner.py

**Path**: `/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/core/qr_scanner.py`

## Class: QrScanner
- Method: `__init__(self, camera_manager, camera_index, camera_object)`
  - Doc: Inicializa el escáner de QR.
- Method: `_init_detector(self)`
  - Doc: Inicializa el mejor detector disponible.
- Method: `_fallback_detector(self)`
  - Doc: Inicializa el detector estándar de OpenCV como respaldo.
- Method: `initialize_camera(self)`
  - Doc: VERSIÓN SÚPER-SIMPLIFICADA: Solo comprueba si el objeto
- Method: `_check_cooldown(self, data)`
  - Doc: Comprueba si el QR escaneado está en período de enfriamiento.
- Method: `release_camera(self)`
  - Doc: Libera la cámara y cierra ventanas de OpenCV.
- Method: `scan_frame(self, frame)`
  - Doc: Escanea un frame en busca de códigos QR usando OpenCV.
- Method: `draw_qr_detection(self, frame, qr_data, bbox)`
  - Doc: Dibuja indicadores visuales en el frame.
- Method: `parse_qr_data(self, qr_data)`
  - Doc: Parsea el contenido de un QR de trazabilidad.
- Method: `validate_qr_format(self, qr_data)`
  - Doc: Valida que un QR tenga el formato correcto de trazabilidad.
- Method: `scan_once(self, timeout)`
  - Doc: Escanea hasta detectar un QR (bloqueo).
- Method: `get_qr_info_for_display(self, qr_data)`
  - Doc: Obtiene información formateada del QR para mostrar al usuario.
- Method: `set_camera_index(self, new_index)`
  - Doc: Permite cambiar la cámara activa del escáner.

## Class: QrScannerCallback
- Method: `__init__(self, on_consulta, on_trabajo)`
  - Doc: Inicializa los callbacks.
- Method: `handle_consulta(self, qr_data, parsed_info)`
  - Doc: Maneja escaneo en modo consulta.
- Method: `handle_trabajo(self, qr_data, parsed_info)`
  - Doc: Maneja escaneo en modo trabajo.
