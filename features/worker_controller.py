"""
Controlador para la interfaz de trabajador.

Maneja la lógica de negocio para trabajadores:
- Carga de fabricaciones asignadas
- Registro de tiempos mediante QR
- Gestión de incidencias
- Comunicación con la base de datos
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
try:
    import cv2
except (ImportError, AttributeError):
    from unittest.mock import MagicMock
    cv2 = MagicMock()
from core.camera_manager import CameraBackend
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, QMessageBox, QInputDialog,
    QDialogButtonBox, QPushButton, QFileDialog, QListWidget, QLabel, QInputDialog
)
from PyQt6.QtCore import Qt


# ============================================================================
# DIÁLOGO PARA REGISTRAR INCIDENCIAS
# ============================================================================

class IncidenceDialog(QDialog):
    """
    Diálogo modal para que el trabajador registre una incidencia,
    incluyendo título, descripción y la posibilidad de adjuntar fotos.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Nueva Incidencia")
        self.setModal(True)
        self.setMinimumSize(450, 400)

        self.fotos_paths = []  # Lista para guardar las rutas de las fotos

        # --- Layout Principal ---
        layout = QVBoxLayout(self)

        # --- Formulario ---
        form_layout = QFormLayout()
        self.tipo_incidencia_edit = QLineEdit()
        self.tipo_incidencia_edit.setPlaceholderText("Ej: 'Material defectuoso', 'Parada de máquina'...")

        self.descripcion_edit = QTextEdit()
        self.descripcion_edit.setPlaceholderText("Explica qué ha ocurrido...")

        form_layout.addRow("Título/Tipo de Incidencia:", self.tipo_incidencia_edit)
        form_layout.addRow("Descripción detallada:", self.descripcion_edit)

        layout.addLayout(form_layout)

        # --- Sección de Fotos ---
        layout.addWidget(QLabel("Fotos (Opcional):"))
        self.fotos_list_widget = QListWidget()
        self.fotos_list_widget.setFixedHeight(80)
        layout.addWidget(self.fotos_list_widget)

        self.add_foto_btn = QPushButton("📷 Adjuntar Foto...")
        self.add_foto_btn.clicked.connect(self._on_add_foto)
        layout.addWidget(self.add_foto_btn)

        # --- Botones OK/Cancelar ---
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _on_add_foto(self):
        """
        Abre un diálogo para seleccionar archivos de imagen.
        """
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar Fotos",
            "",  # Directorio inicial
            "Imágenes (*.png *.jpg *.jpeg *.bmp)"
        )

        if files:
            for file_path in files:
                self.fotos_paths.append(file_path)
                self.fotos_list_widget.addItem(file_path.split('/')[-1])  # Mostrar solo el nombre

    def get_data(self) -> Optional[Dict[str, Any]]:
        """
        Devuelve los datos del formulario si son válidos.
        """
        tipo_incidencia = self.tipo_incidencia_edit.text().strip()
        descripcion = self.descripcion_edit.toPlainText().strip()

        if not tipo_incidencia or not descripcion:
            return None  # Faltan datos obligatorios

        return {
            "tipo_incidencia": tipo_incidencia,
            "descripcion": descripcion,
            "fotos_paths": self.fotos_paths
        }


# ============================================================================
# CLASE DEL CONTROLADOR
# ============================================================================



class WorkerController:
    """
    Controlador para gestionar las operaciones de trabajadores.

    Este controlador actúa como intermediario entre la interfaz de trabajador
    y la capa de datos, gestionando todas las operaciones relacionadas con
    el registro de tiempos, escaneo de QR e incidencias.

    Attributes:
        current_user (dict): Datos del trabajador autenticado
        db_manager: Gestor de base de datos
        main_window: Ventana principal del trabajador
        qr_scanner: Escáner de códigos QR
        tracking_repo: Repositorio de trazabilidad
    """

    def __init__(
            self,
            current_user: Dict[str, Any],
            db_manager,
            main_window,
            qr_scanner=None,
            tracking_repo=None,
            label_manager=None,
            qr_generator=None,
            label_counter_repo=None
    ):
        """
        Inicializa el controlador de trabajador.

        Args:
            current_user: Diccionario con datos del trabajador autenticado
            db_manager: Instancia del DatabaseManager
            main_window: Instancia de WorkerMainWindow
            qr_scanner: Instancia del QrScanner (opcional)
            tracking_repo: Instancia del TrackingRepository (opcional)
        """
        self.current_user = current_user
        self.db_manager = db_manager
        self.main_window = main_window
        self.qr_scanner = qr_scanner
        self.tracking_repo = tracking_repo or db_manager.tracking_repo

        self.label_manager = label_manager
        self.qr_generator = qr_generator
        self.label_counter_repo = label_counter_repo
        # Crear instancia de CameraManager para configuración
        from core.camera_manager import CameraManager
        self.camera_manager = CameraManager()

        self.logger = logging.getLogger("EvolucionTiemposApp.WorkerController")

        # Cache de datos
        self._fabricaciones_asignadas = []
        self._trabajos_activos = []

        self.logger.info(
            f"WorkerController inicializado para trabajador ID: {current_user.get('id')}"
        )

    def initialize(self):
        """
        Inicializa el controlador y carga los datos iniciales.

        Este método debe llamarse después de crear el controlador
        para cargar las fabricaciones asignadas y configurar la interfaz.
        """
        try:
            self.logger.info("Inicializando WorkerController...")

            # Cargar fabricaciones asignadas al trabajador
            self._load_assigned_fabricaciones()

            # Cargar trabajos activos
            self._load_active_trabajos()

            # Conectar señales de la ventana
            self._connect_signals()

            self.logger.info("WorkerController inicializado correctamente")

        except Exception as e:
            self.logger.error(f"Error inicializando WorkerController: {e}", exc_info=True)
            self.main_window.show_message(
                "Error de Inicialización",
                f"No se pudo inicializar correctamente: {e}",
                "error"
            )

    def _connect_signals(self):
        """Conecta las señales de la ventana con los métodos del controlador."""
        try:
            # Conectar señal de logout
            self.main_window.logout_requested.connect(self._handle_logout)
            # Conectar señal de configuración de cámara
            self.main_window.camera_config_requested.connect(self._handle_camera_config)
            # Conectar señales de acciones de tarea
            self.main_window.task_selected.connect(self._handle_task_selected)
            self.main_window.generate_labels_requested.connect(self._handle_generate_labels)
            self.main_window.consult_qr_requested.connect(self._handle_consult_qr)
            self.main_window.start_task_requested.connect(self._handle_start_task)

            # Añade las conexiones que faltaban para los botones muertos
            self.main_window.end_task_requested.connect(self._handle_end_task)
            self.main_window.register_incidence_requested.connect(self._handle_register_incidence)

            self.main_window.export_data_requested.connect(self._handle_export_data)
            # (Aquí conectaremos el resto de botones más adelante)

            self.logger.debug("Señales conectadas correctamente")

        except Exception as e:
            self.logger.error(f"Error conectando señales: {e}", exc_info=True)

    def _load_assigned_fabricaciones(self):
        """Carga las fabricaciones asignadas al trabajador actual."""
        try:
            trabajador_id = self.current_user.get('id')

            if not trabajador_id:
                self.logger.warning("ID de trabajador no disponible")
                self._fabricaciones_asignadas = []
                if hasattr(self.main_window, 'update_tasks_list'):
                    self.main_window.update_tasks_list(self._fabricaciones_asignadas)
                return

            self.logger.debug(f"Cargando fabricaciones para trabajador ID: {trabajador_id}")

            # Obtener fabricaciones asignadas del repositorio
            fabricaciones = self.tracking_repo.get_fabricaciones_por_trabajador(trabajador_id)

            # Convertir a formato esperado por la UI
            self._fabricaciones_asignadas = []
            for fab in fabricaciones:
                # Extraer información del primer producto
                # DTO tiene lista de dicts en 'productos'
                productos = fab.productos
                producto_info = productos[0] if productos else {}

                # Construir descripción enriquecida
                fab_dict = {
                    'id': fab.id,
                    'codigo': fab.codigo,
                    'descripcion': fab.descripcion,
                    'producto_codigo': producto_info.get('codigo', ''),
                    'producto_descripcion': producto_info.get('descripcion', ''),
                    'cantidad': producto_info.get('cantidad', 0),
                    'fecha_asignacion': fab.fecha_asignacion,
                    'estado': fab.estado,
                    'productos': productos
                }
                self._fabricaciones_asignadas.append(fab_dict)

            self.logger.info(f"Cargadas {len(self._fabricaciones_asignadas)} fabricaciones")

            # Actualizar UI
            if hasattr(self.main_window, 'update_tasks_list'):
                self.main_window.update_tasks_list(self._fabricaciones_asignadas)

        except Exception as e:
            self.logger.error(f"Error cargando fabricaciones asignadas: {e}", exc_info=True)
            self._fabricaciones_asignadas = []
            if hasattr(self.main_window, 'update_tasks_list'):
                self.main_window.update_tasks_list(self._fabricaciones_asignadas)

    def _load_active_trabajos(self):
        """
        Carga los trabajos activos del trabajador.

        Consulta los trabajos que están en estado 'en_proceso' para este trabajador.
        """
        try:
            trabajador_id = self.current_user.get('id')

            if not trabajador_id:
                self.logger.warning("ID de trabajador no disponible")
                return

            self.logger.debug(f"Cargando trabajos activos para trabajador ID: {trabajador_id}")

            # Obtener trabajos activos desde el repositorio
            self._trabajos_activos = self.tracking_repo.obtener_trabajos_activos(
                trabajador_id
            )

            self.logger.info(
                f"Cargados {len(self._trabajos_activos)} trabajos activos"
            )

        except Exception as e:
            self.logger.error(f"Error cargando trabajos activos: {e}", exc_info=True)
            self._trabajos_activos = []

    def get_assigned_fabricaciones(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de fabricaciones asignadas al trabajador.

        Returns:
            Lista de diccionarios con información de las fabricaciones
        """
        return self._fabricaciones_asignadas

    def get_active_trabajos(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de trabajos activos del trabajador.

        Returns:
            Lista de diccionarios con información de los trabajos activos
        """
        return self._trabajos_activos

    def iniciar_trabajo(
            self,
            qr_code: str,
            fabricacion_id: int,
            producto_codigo: str
    ) -> Optional[Dict[str, Any]]:
        """
        Inicia un nuevo trabajo escaneando un código QR.

        Args:
            qr_code: Código QR único de la unidad
            fabricacion_id: ID de la fabricación
            producto_codigo: Código del producto

        Returns:
            Diccionario con información del trabajo creado, o None si falla
        """
        try:
            trabajador_id = self.current_user.get('id')

            if not trabajador_id:
                self.logger.error("No se puede iniciar trabajo: ID de trabajador no disponible")
                return None

            self.logger.info(
                f"Iniciando trabajo: QR={qr_code}, Fabricacion={fabricacion_id}, "
                f"Producto={producto_codigo}, Trabajador={trabajador_id}"
            )

            # Registrar inicio de trabajo en la base de datos
            trabajo_log = self.tracking_repo.iniciar_trabajo(
                qr_code=qr_code,
                trabajador_id=trabajador_id,
                fabricacion_id=fabricacion_id,
                producto_codigo=producto_codigo
            )

            if trabajo_log:
                self.logger.info(f"Trabajo iniciado exitosamente: ID={trabajo_log.id}")

                # Recargar trabajos activos
                self._load_active_trabajos()

                # Notificar a la ventana
                self.main_window.show_message(
                    "Trabajo Iniciado",
                    f"Trabajo iniciado para QR: {qr_code}",
                    "info"
                )

                return trabajo_log
            else:
                self.logger.warning("No se pudo iniciar el trabajo")
                return None

        except Exception as e:
            self.logger.error(f"Error iniciando trabajo: {e}", exc_info=True)
            self.main_window.show_message(
                "Error",
                f"No se pudo iniciar el trabajo: {e}",
                "error"
            )
            return None

    def finalizar_trabajo(self, trabajo_log_id: int) -> bool:
        """
        Finaliza un trabajo activo.

        Args:
            trabajo_log_id: ID del trabajo a finalizar

        Returns:
            True si se finalizó correctamente, False en caso contrario
        """
        try:
            self.logger.info(f"Finalizando trabajo ID: {trabajo_log_id}")

            # Finalizar trabajo en la base de datos
            # Ahora devuelve el objeto actualizado o None
            resultado = self.tracking_repo.finalizar_trabajo_log(trabajo_log_id)

            if resultado:
                self.logger.info(f"Trabajo {trabajo_log_id} finalizado exitosamente")

                # Recargar trabajos activos
                self._load_active_trabajos()

                # Notificar a la ventana
                self.main_window.show_message(
                    "Trabajo Finalizado",
                    "El trabajo ha sido completado",
                    "info"
                )

                return True
            else:
                self.logger.warning(f"No se pudo finalizar trabajo {trabajo_log_id}")
                return False

        except Exception as e:
            self.logger.error(f"Error finalizando trabajo: {e}", exc_info=True)
            self.main_window.show_message(
                "Error",
                f"No se pudo finalizar el trabajo: {e}",
                "error"
            )
            return False

    def registrar_incidencia(
            self,
            trabajo_log_id: int,
            tipo_incidencia: str,
            descripcion: str,
            fotos_paths: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Registra una incidencia para un trabajo específico.

        Args:
            trabajo_log_id: ID del trabajo donde ocurrió la incidencia
            tipo_incidencia: Tipo de incidencia (defecto, pausa, etc.)
            descripcion: Descripción detallada de la incidencia
            fotos_paths: Lista de rutas a fotografías (opcional)

        Returns:
            Diccionario con información de la incidencia creada, o None si falla
        """
        try:
            trabajador_id = self.current_user.get('id')

            if not trabajador_id:
                self.logger.error("No se puede registrar incidencia: ID de trabajador no disponible")
                return None

            self.logger.info(
                f"Registrando incidencia: Trabajo={trabajo_log_id}, "
                f"Tipo={tipo_incidencia}, Trabajador={trabajador_id}"
            )

            # Llamamos al repositorio con los argumentos correctos (incluyendo fotos si las hay)
            incidencia = self.tracking_repo.registrar_incidencia(
                trabajo_log_id=trabajo_log_id,
                trabajador_id=trabajador_id,
                tipo_incidencia=tipo_incidencia,
                descripcion=descripcion,
                rutas_fotos=fotos_paths or []
            )
            # --- FIN DE LA CORRECCIÓN ---

            if incidencia:
                self.logger.info(f"Incidencia registrada exitosamente: ID={incidencia.id}")

                # Notificar a la ventana
                self.main_window.show_message(
                    "Incidencia Registrada",
                    "La incidencia ha sido registrada correctamente",
                    "info"
                )

                # TODO: Aquí iría la lógica futura para subir/guardar las fotos
                # usando el 'incidencia.get('id')' y los 'fotos_paths'.

                return incidencia
            else:
                self.logger.warning("No se pudo registrar la incidencia")
                return None

        except Exception as e:
            self.logger.error(f"Error registrando incidencia: {e}", exc_info=True)
            self.main_window.show_message(
                "Error",
                f"No se pudo registrar la incidencia: {e}",
                "error"
            )
            return None

    def get_estadisticas_trabajador(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene las estadísticas del trabajador actual.

        Returns:
            Diccionario con estadísticas, o None si falla
        """
        try:
            trabajador_id = self.current_user.get('id')

            if not trabajador_id:
                self.logger.warning("ID de trabajador no disponible")
                return None

            self.logger.debug(f"Obteniendo estadísticas para trabajador ID: {trabajador_id}")

            # Obtener estadísticas desde el repositorio
            stats = self.tracking_repo.obtener_estadisticas_trabajador(trabajador_id)

            self.logger.info("Estadísticas obtenidas correctamente")

            return stats

        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}", exc_info=True)
            return None

    def _handle_logout(self):
        """
        Maneja el cierre de sesión del trabajador.

        Limpia los datos en cache y cierra la aplicación.
        """
        try:
            self.logger.info(
                f"Cerrando sesión de trabajador: {self.current_user.get('nombre')}"
            )

            # Limpiar cache
            self._fabricaciones_asignadas = []
            self._trabajos_activos = []

            # Cerrar la aplicación
            import sys
            sys.exit(0)

        except Exception as e:
            self.logger.error(f"Error durante logout: {e}", exc_info=True)

    def refresh_data(self):
        """
        Recarga todos los datos desde la base de datos.

        Útil para actualizar la interfaz con los últimos cambios.
        """
        try:
            self.logger.info("Recargando datos...")

            self._load_assigned_fabricaciones()
            self._load_active_trabajos()

            self.logger.info("Datos recargados correctamente")

        except Exception as e:
            self.logger.error(f"Error recargando datos: {e}", exc_info=True)

        # ========================================================================
        # MANEJADORES DE SEÑALES DE LA VISTA (BOTONES DE ACCIÓN)
        # ========================================================================

    def _handle_task_selected(self, task_data: Dict[str, Any]):
        """
        Se llama cuando el usuario selecciona una tarea en la lista.
        Actualiza el estado de la UI comprobando si el trabajador actual
        tiene un paso activo relacionado con esa tarea.

        MODIFICADO: Llama a update_task_state con el nombre de estado correcto.
        """
        if not task_data:
            self.main_window.update_task_state("pendiente", None)  # Estado por defecto
            return

        self.logger.info(f"Tarea activa cambiada a: {task_data.get('codigo')}")
        trabajador_id = self.current_user.get('id')
        fabricacion_id_seleccionada = task_data.get('id')

        # Habilitar el botón de etiquetas siempre que se selecciona una tarea
        self.main_window.generate_labels_btn.setEnabled(True)

        try:
            # 1. Buscar si este trabajador tiene CUALQUIER paso activo
            paso_activo = self.tracking_repo.get_paso_activo_por_trabajador(trabajador_id)

            if not paso_activo:
                # El trabajador está libre
                self.logger.info(f"El trabajador {trabajador_id} está libre. Estado: pendiente.")
                self.main_window.update_task_state("pendiente", None)
                return

            # 2. El trabajador tiene un paso activo. ¿Corresponde a la tarea seleccionada?
            # Para saberlo, necesitamos el TrabajoLog (pasaporte) de ese paso.

            # --- INICIO DE CORRECCIÓN ---
            # Es más eficiente obtener el trabajo_log_id directamente del paso_activo
            trabajo_log_id_activo = paso_activo.trabajo_log_id

            # Consultamos la fabricación de ese TrabajoLog
            trabajo_log_activo = self.tracking_repo.obtener_trabajo_por_id(paso_activo.trabajo_log_id)

            if trabajo_log_activo and trabajo_log_activo.fabricacion_id == fabricacion_id_seleccionada:
                # El paso activo SÍ es de esta fabricación
                self.logger.info(f"El trabajador tiene un paso activo ('{paso_activo.paso_nombre}') para esta tarea.")

                # --- CORRECCIÓN CLAVE ---
                # Usar "en_proceso" en lugar de "en_proceso_propio"
                self.main_window.update_task_state("en_proceso", paso_activo.paso_nombre)
                # --- FIN CORRECCIÓN CLAVE ---

            else:
                # El trabajador tiene un paso activo, PERO de OTRA tarea
                # Obtenemos el código de la fabricación en la que SÍ está trabajando
                codigo_otra_tarea = "otra tarea"
                if trabajo_log_activo:
                    fab_otra_tarea = self.db_manager.get_fabricacion_by_id(
                        trabajo_log_activo.fabricacion_id)  # Asumiendo que db_manager tiene esta función
                    if fab_otra_tarea:
                        codigo_otra_tarea = fab_otra_tarea.codigo

                self.logger.info(f"El trabajador está ocupado en OTRA tarea ({codigo_otra_tarea}). Estado: pendiente.")
                self.main_window.update_task_state("pendiente", None)

                # Mostramos un aviso no bloqueante al usuario
                self.main_window.show_message(
                    "Aviso",
                    f"Estás trabajando en '{codigo_otra_tarea}'.\nDebes finalizarla antes de empezar esta.",
                    "warning"
                )

        except Exception as e:
            self.logger.error(f"Error al comprobar estado de tarea: {e}", exc_info=True)
            self.main_window.update_task_state("pendiente", None)

    def _handle_generate_labels(self, task_data: Dict[str, Any]):
        """
        Maneja la solicitud de generar e imprimir etiquetas QR.
        MODIFICADO: Usa el repositorio de contadores (etiquetas.db) y
        cuenta los placeholders en la plantilla para generar QRs únicos y secuenciales.
        """
        if not self.label_manager or not self.qr_generator:
            self.logger.error("LabelManager o QrGenerator no están disponibles.")
            self.main_window.show_message("Error", "El gestor de etiquetas no está configurado.", "error")
            return

        # --- INICIO DE LA LÓGICA DE CONTADORES (Paso 18) ---

        # 1. Obtener los datos de la tarea (Fabricación)
        try:
            fabricacion_id = task_data.get('id')
            producto_codigo = task_data.get('producto_codigo')

            if not fabricacion_id or not producto_codigo:
                self.logger.error("Datos de tarea incompletos (falta id o codigo).")
                self.main_window.show_message("Error", "Datos de tarea incompletos.", "error")
                return

            # 2. Definir la plantilla a usar
            plantilla_nombre = 'qr.docx'
            plantilla_formato = 'A5'  # O 'A4', según tu configuración

            # 3. Contar cuántos QRs caben en UNA hoja de esa plantilla
            qrs_por_hoja = self.label_manager.count_qr_placeholders(plantilla_nombre, plantilla_formato)

            if qrs_por_hoja == 0:
                self.logger.error(f"La plantilla {plantilla_nombre} no contiene placeholders '{{qr}}'.")
                self.main_window.show_message("Error de Plantilla",
                                              f"La plantilla '{plantilla_nombre}' no contiene ningún placeholder '{{qr}}'.",
                                              "error")
                return

            self.logger.info(f"La plantilla '{plantilla_nombre}' tiene {qrs_por_hoja} QRs por hoja.")

            # 4. Preguntar al usuario cuántas HOJAS quiere
            num_hojas, ok = QInputDialog.getInt(
                self.main_window,
                "Generar Etiquetas",
                f"Cada hoja contiene {qrs_por_hoja} etiquetas.\n\n¿Cuántas HOJAS deseas generar?",
                value=1,
                min=1,
                max=100
            )

            if not ok:
                self.logger.info("Generación de etiquetas cancelada por el usuario.")
                return

            cantidad_total_qrs = num_hojas * qrs_por_hoja
            self.main_window.show_message("Impresión", f"Generando {cantidad_total_qrs} etiquetas únicas...", "info")

            # 5. Pedir el rango de números al repositorio de contadores
            # (Accedemos al repo que creamos en el AppController en el Paso 16)
            rango_unidades = self.label_counter_repo.get_next_unit_range(fabricacion_id, cantidad_total_qrs)

            if rango_unidades is None:
                self.logger.error("No se pudo obtener el rango de unidades desde etiquetas.db.")
                self.main_window.show_message("Error de Base de Datos",
                                              "No se pudo obtener el contador desde 'etiquetas.db'.", "error")
                return

            # 6. Generar la lista de QRs únicos
            datos_qr_unicos = []
            # CORRECCIÓN: Iterar sobre el rango numérico, no sobre el DTO
            for unit_number in range(rango_unidades.start, rango_unidades.end + 1):
                # Generar el ID único usando el formato FAB-PROD-UNIT-TS-HASH
                qr_data_string = self.qr_generator.generate_unique_id(
                    fabricacion_id=fabricacion_id,
                    producto_codigo=producto_codigo,
                    unit_number=unit_number
                )

                # El label_manager espera un diccionario
                datos_etiqueta = {
                    'codigo': qr_data_string,  # El QR contendrá el ID único
                    'producto': producto_codigo,
                    'descripcion': task_data.get('descripcion', ''),
                    'qr': 'placeholder'  # Clave para activar el reemplazo de imagen
                }
                datos_qr_unicos.append(datos_etiqueta)

            # 7. Generar el documento
            doc_path = self.label_manager.generate_labels(
                plantilla=plantilla_nombre,
                formato=plantilla_formato,
                datos_lista=datos_qr_unicos  # Pasamos la lista completa de QRs únicos
            )

            if not doc_path:
                self.main_window.show_message("Error", "No se pudo generar el documento Word.", "error")
                return

            # 8. Comprobar si hay impresora, intentar imprimir, y si falla, ofrecer guardar.
            self.logger.info(f"Documento generado: {doc_path}")
            
            # Verificar si hay impresora predeterminada (Detectando español e inglés)
            import subprocess
            import shutil
            
            has_printer = False
            try:
                result = subprocess.run(['lpstat', '-d'], capture_output=True, text=True, timeout=5)
                output = result.stdout.lower()
                
                # Criterios para determinar que NO hay impresora
                no_printer_signals = [
                    'no system default destination',
                    'no hay destino predeterminado',
                    'sin destino por omisión'
                ]
                
                # Si ninguna de las señales de "no impresora" está presente, asumimos que SI hay.
                if not any(signal in output for signal in no_printer_signals):
                    has_printer = True
                    
            except Exception:
                # Si falla lpstat (ej: Windows sin configurar), asumimos False para estar seguros
                has_printer = False
            
            print_success = False
            
            if has_printer:
                # Hay impresora, intentar imprimir
                self.logger.info(f"Enviando documento a la cola de impresión: {doc_path}")
                success, _ = self.label_manager.print_document(doc_path)
                
                if success:
                    print_success = True
                    self.main_window.show_message("Impresión", "Documento enviado a la impresora.", "info")
                else:
                    self.logger.warning("Fallo al imprimir a pesar de detectar impresora.")
            
            # Si no se imprimió (ya sea porque no había impresora o porque falló el intento)
            if not print_success:
                # Mostrar diálogo para guardar
                msg_titulo = "Guardar Etiquetas"
                msg_intro = "No se detectó impresora configurada." 
                
                if has_printer:
                    msg_intro = "Hubo un error al intentar imprimir."
                
                self.logger.info(f"{msg_intro} Mostrando diálogo de guardar...")
                
                from PyQt6.QtWidgets import QFileDialog
                from pathlib import Path
                from datetime import datetime
                
                # Nombre de archivo por defecto
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                default_name = f"etiquetas_QR_{timestamp}.docx"
                default_path = str(Path.home() / "Documents" / default_name)
                
                # Mostrar diálogo de guardar
                save_path, _ = QFileDialog.getSaveFileName(
                    self.main_window,
                    f"{msg_titulo} - {msg_intro}",
                    default_path,
                    "Documento Word (*.docx);;Todos los archivos (*)"
                )
                
                if save_path:
                    # Copiar archivo a la ubicación elegida
                    try:
                        shutil.copy2(doc_path, save_path)
                        self.logger.info(f"Documento guardado en: {save_path}")
                        self.main_window.show_message(
                            "Etiquetas Guardadas",
                            f"El documento se ha guardado en:\n{save_path}\n\nPuedes copiarlo a un USB o llevarlo a un ordenador con impresora.",
                            "info"
                        )
                        
                        # Abrir la ubicación en Finder
                        subprocess.run(['open', '-R', save_path])
                        
                    except Exception as e:
                        self.logger.error(f"Error guardando documento: {e}")
                        self.main_window.show_message("Error", f"No se pudo guardar el documento: {e}", "error")
                else:
                    self.logger.info("Usuario canceló el guardado del documento.")
                    if not has_printer:
                        self.main_window.show_message("Cancelado", "No se guardó el documento.", "warning")

        except Exception as e:
            self.logger.error(f"Error al generar etiquetas: {e}", exc_info=True)
            self.main_window.show_message("Error Crítico", f"Ocurrió un error: {e}", "error")

    def _handle_consult_qr(self):
        """
        Maneja la solicitud de consultar un QR.
        Abre el escáner, valida el formato y comprueba si ya está en uso.
        """
        if not self.qr_scanner:
            self.logger.error("QR Scanner no está disponible")
            self.main_window.show_message("Error", "El escáner de QR no está configurado", "error")
            return

        self.logger.info("Iniciando escaneo de QR para consulta...")
        self.main_window.show_message("Escáner", "Acerca el código QR a la cámara para consultarlo...", "info")

        try:
            # 1. Escanear el código
            qr_data = self.qr_scanner.scan_once(timeout=30)
            if not qr_data:
                self.logger.info("Escaneo cancelado o tiempo de espera agotado.")
                return

            # 2. Validar el formato del QR
            parsed_data = self.qr_scanner.parse_qr_data(qr_data)
            if not parsed_data:
                self.logger.warning(f"QR escaneado con formato inválido: {qr_data}")
                self.main_window.show_message(
                    "QR Inválido",
                    f"El código escaneado no tiene el formato de trazabilidad esperado.\n\nContenido: {qr_data}",
                    "warning"
                )
                return

            # 3. Consultar la base de datos (Usando el método que SÍ existe)
            self.logger.debug(f"Consultando base de datos para QR: {qr_data}")
            trabajo_existente_obj = self.tracking_repo.obtener_trabajo_por_qr(qr_data)

            if trabajo_existente_obj:
                # El QR ya está en la base de datos
                fecha_inicio = trabajo_existente_obj.tiempo_inicio.strftime('%d/%m/%Y %H:%M')
                estado = trabajo_existente_obj.estado.upper()
                orden_fab = trabajo_existente_obj.orden_fabricacion or "N/A"
                trabajador = trabajo_existente_obj.trabajador_nombre or "Desconocido"
                
                # Intentar obtener el último paso para dar más info
                ultimo_paso = self.tracking_repo.get_ultimo_paso_para_qr(trabajo_existente_obj.id)
                info_paso = "Ninguno"
                if ultimo_paso:
                    info_paso = f"{ultimo_paso.paso_nombre} ({ultimo_paso.estado_paso})"
                
                # Formatear incidencias si existen
                incidencias_str = ""
                if trabajo_existente_obj.incidencias:
                    incidencias_str = "\n\n⚠️ INCIDENCIAS REGISTRADAS:"
                    for inc in trabajo_existente_obj.incidencias:
                        fecha_inc = inc.fecha_reporte.strftime('%d/%m/%Y')
                        estado_inc = inc.estado.upper()
                        incidencias_str += f"\n- [{fecha_inc}] ({estado_inc}) {inc.tipo_incidencia}: {inc.descripcion}"

                self.main_window.show_message(
                    f"QR EN USO - {estado}",
                    f"Información del Código QR:\n\n"
                    f"Producto: {trabajo_existente_obj.producto_codigo}\n"
                    f"Orden Prod (OF): {orden_fab}\n"
                    f"Trabajador: {trabajador}\n"
                    f"Fecha Inicio: {fecha_inicio}\n"
                    f"Estado Global: {estado}\n"
                    f"Último Paso: {info_paso}"
                    f"{incidencias_str}",
                    "warning" if estado == "EN_PROCESO" else "info"
                )
            else:
                self.main_window.show_message(
                    "QR DISPONIBLE",
                    f"Este código QR está libre y listo para usarse.\n\nCódigo: {qr_data}",
                    "info"
                )


        except Exception as e:
            self.logger.error(f"Error durante la consulta de QR: {e}", exc_info=True)
            self.main_window.show_message("Error Crítico", f"Ocurrió un error al consultar el QR: {e}", "error")

    def _handle_start_task(self, task_data: Dict[str, Any]):
        """
        Maneja la solicitud de INICIAR un paso de trabajo escaneando un QR.

        Lógica:
        1. Comprueba si el trabajador ya tiene un paso activo (error).
        2. Escanea QR.
        3. Valida el formato del QR.
        4. PREGUNTA por la OF si el QR es nuevo.
        5. Obtiene/Crea el TrabajoLog ("pasaporte") para ese QR (ya con la OF).
        6. Comprueba el último paso ("sello") de ese pasaporte.
        7. Inicia el nuevo paso (`PasoTrazabilidad`).
        """
        if not self.qr_scanner or not self.tracking_repo:
            self.logger.error("QR Scanner o Tracking Repository no están disponibles")
            return

        trabajador_id = self.current_user.get('id')
        fabricacion_id = task_data.get('id')

        try:
            # --- 1. Comprobar si este trabajador ya tiene un paso activo ---
            paso_ya_activo = self.tracking_repo.get_paso_activo_por_trabajador(trabajador_id)
            if paso_ya_activo:
                self.main_window.show_message("Acción Requerida",
                                              f"Ya tienes un paso 'en_proceso'.\n\nFinaliza '{paso_ya_activo.paso_nombre}' antes de iniciar uno nuevo.",
                                              "warning")
                return

            # --- 2. Escanear QR ---
            self.logger.info(f"Iniciando escaneo para comenzar/continuar la tarea: {task_data.get('codigo')}")
            self.main_window.show_message("Escáner", "Acerque el QR de la UNIDAD para INICIAR el siguiente paso...",
                                          "info")

            qr_data = self.qr_scanner.scan_once(timeout=30)
            if not qr_data:
                self.logger.info("Escaneo cancelado.")
                return

            # --- 3. Validar formato QR y Tarea ---
            parsed_data = self.qr_scanner.parse_qr_data(qr_data)
            if not parsed_data:
                self.main_window.show_message("QR Inválido",
                                              f"El formato del QR no es válido.\nContenido: {qr_data}",
                                              "warning")
                return

            # Obtenemos AMBOS códigos de producto para compararlos
            producto_qr_codigo = parsed_data.get('producto_codigo')
            producto_tarea_codigo = task_data.get('producto_codigo')

            # Validación: Asegurarse de que el QR escaneado pertenece a la tarea seleccionada
            if producto_qr_codigo != producto_tarea_codigo:
                self.logger.warning(f"QR ({producto_qr_codigo}) no coincide con Tarea ({producto_tarea_codigo})")
                self.main_window.show_message(
                    "QR Incorrecto",
                    f"El QR escaneado ({producto_qr_codigo}) no corresponde al producto de la tarea seleccionada ({producto_tarea_codigo}).",
                    "error"
                )
                return

            # --- 4. PREGUNTAR por la OF si el QR es nuevo ---
            numero_of_para_guardar = None

            # Buscamos primero si el "pasaporte" ya existe
            trabajo_log_existente = self.tracking_repo.obtener_trabajo_por_qr(qr_data)

            if not trabajo_log_existente:
                self.logger.info(f"Es un QR nuevo. Solicitando Orden de Fabricación (Pedido)...")

                # Mostramos el pop-up para pedir el número de pedido
                numero_of_para_guardar, ok = QInputDialog.getText(
                    self.main_window,
                    "Orden de Fabricación (Pedido)",
                    "Es la primera vez que se escanea esta unidad.\n\nIntroduce el Nº de Pedido (OF) asociado:"
                )

                if not ok:
                    self.logger.info("El usuario canceló la introducción de la OF.")
                    return  # El usuario pulsó "Cancelar"

                if not numero_of_para_guardar or not numero_of_para_guardar.strip():
                    self.main_window.show_message("Error",
                                                  "El número de Orden de Fabricación (Pedido) es obligatorio para iniciar una nueva unidad.",
                                                  "error")
                    return  # El usuario dejó el campo vacío

                numero_of_para_guardar = numero_of_para_guardar.strip().upper()
                self.logger.info(f"OF introducida: {numero_of_para_guardar}")

            # --- 5. Obtener/Crear el "Pasaporte" (TrabajoLog) ---
            trabajo_log = self.tracking_repo.obtener_o_crear_trabajo_log_por_qr(
                qr_code=qr_data,
                trabajador_id=trabajador_id,
                fabricacion_id=fabricacion_id,
                producto_codigo=producto_tarea_codigo,
                orden_fabricacion=numero_of_para_guardar  # Pasamos la OF (o None si ya existía)
            )

            if not trabajo_log:
                self.main_window.show_message("Error de Base de Datos",
                                              "No se pudo obtener o crear el registro (pasaporte) para este QR.",
                                              "error")
                return

            # --- 6. Comprobar el último "Sello" (PasoTrazabilidad) ---
            ultimo_paso = self.tracking_repo.get_ultimo_paso_para_qr(trabajo_log.id)

            if ultimo_paso and ultimo_paso.estado_paso == 'en_proceso':
                if ultimo_paso.trabajador_id == trabajador_id:
                    self.main_window.show_message("Paso en Proceso",
                                                  f"Ya tienes este paso '{ultimo_paso.paso_nombre}' en proceso.\n\n"
                                                  "Pulsa 'Finalizar Tarea' para completarlo.",
                                                  "info")
                else:
                    self.main_window.show_message("QR en Uso",
                                                  "Esta unidad está siendo trabajada por otro operario en este momento.",
                                                  "error")
                return

            # --- 7. Buscar el siguiente paso a realizar ---
            # (Esta es la parte que requiere la configuración del producto)

            # TODO: Esta lógica debe implementarse. Por ahora, creamos un paso genérico.

            # --- Lógica de ejemplo (temporal) ---
            paso_nombre_siguiente = "Paso Genérico"
            tipo_paso_siguiente = "generico"
            maquina_id_siguiente = None
            es_paso_final = False

            num_paso_actual = 0
            if ultimo_paso:
                try:
                    num_paso_actual = int(ultimo_paso.paso_nombre.split(" ")[-1])
                except:
                    num_paso_actual = 0

            paso_nombre_siguiente = f"Paso Genérico {num_paso_actual + 1}"
            if num_paso_actual + 1 >= 3:
                es_paso_final = True
            # --- Fin lógica de ejemplo ---

            # --- 8. Iniciar el nuevo paso (crear el "sello") ---
            self.logger.info(f"Iniciando nuevo paso: {paso_nombre_siguiente}")
            nuevo_paso = self.tracking_repo.iniciar_nuevo_paso(
                trabajo_log_id=trabajo_log.id,
                trabajador_id=trabajador_id,
                paso_nombre=paso_nombre_siguiente,
                tipo_paso=tipo_paso_siguiente,
                maquina_id=maquina_id_siguiente
            )

            if nuevo_paso:
                # Recargar trabajos activos
                self._load_active_trabajos()

                # Actualizar estado de la interfaz
                self.main_window.update_task_state("en_proceso", paso_nombre_siguiente)

                # Habilitar botones de finalizar e incidencia
                self.main_window.enable_action_buttons(True)

                self.main_window.show_message(
                    "Paso Iniciado",
                    f"Has iniciado el paso: {paso_nombre_siguiente}\n"
                    f"OF: {trabajo_log.orden_fabricacion}\n"
                    f"Unidad QR: {qr_data}",
                    "info"
                )
            else:
                self.main_window.show_message("Error", "No se pudo registrar el inicio del nuevo paso.", "error")

        except Exception as e:
            self.logger.error(f"Error crítico al iniciar paso: {e}", exc_info=True)
            self.main_window.show_message("Error Crítico", f"Ocurrió un error al iniciar el paso: {e}", "error")

    def _handle_end_task(self, task_data: Dict[str, Any]):
        """
        Maneja la solicitud de FINALIZAR el paso de trabajo activo.
        MODIFICADO: Ahora requiere escanear el QR para confirmar.

        Lógica:
        1. Comprueba si el trabajador tiene un paso activo. Si no, error.
        2. Escanea QR.
        3. Valida que el QR escaneado es el MISMO que el del paso activo.
        4. Finaliza el PasoTrazabilidad (el "sello").
        5. Comprueba si era el último paso del producto.
        6. Si era el último, finaliza el TrabajoLog (el "pasaporte").
        """
        if not self.qr_scanner or not self.tracking_repo:
            self.logger.error("QR Scanner o Tracking Repository no están disponibles")
            return

        trabajador_id = self.current_user.get('id')

        try:
            # --- 1. Buscar el paso activo de este trabajador ---
            paso_activo = self.tracking_repo.get_paso_activo_por_trabajador(trabajador_id)

            if not paso_activo:
                self.main_window.show_message("Error", "No tienes ningún paso 'en_proceso' para finalizar.", "warning")
                return

            # Obtener el QR del pasaporte asociado a este paso activo
            # Usar el trabajo_log_id para buscar el TrabajoLog
            trabajo_log_activo = self.tracking_repo.obtener_trabajo_por_id(paso_activo.trabajo_log_id)
            if not trabajo_log_activo:
                self.main_window.show_message("Error de Sincronización",
                                              "No se encuentra el 'pasaporte' de tu tarea activa.", "error")
                return

            qr_de_la_tarea_activa = trabajo_log_activo.qr_code

            self.logger.info(
                f"Finalizando paso ID: {paso_activo.id} ({paso_activo.paso_nombre}). Se espera QR: {qr_de_la_tarea_activa}")

            # --- 2. Escanear QR para confirmar ---
            self.main_window.show_message("Escáner",
                                          f"Acerque el QR ({qr_de_la_tarea_activa[:10]}...) para FINALIZAR el paso...",
                                          "info")

            qr_data_escaneado = self.qr_scanner.scan_once(timeout=30)
            if not qr_data_escaneado:
                self.logger.info("Escaneo cancelado.")
                return

            # --- 3. Validar que el QR es el correcto ---
            if qr_data_escaneado != qr_de_la_tarea_activa:
                self.logger.warning(
                    f"QR incorrecto. Se esperaba '{qr_de_la_tarea_activa}' pero se escaneó '{qr_data_escaneado}'")
                self.main_window.show_message(
                    "QR Incorrecto",
                    "El QR escaneado no coincide con la unidad que tienes 'en_proceso'.",
                    "error"
                )
                return

            self.logger.info("Confirmación de QR exitosa.")

            # --- 4. Finalizar el "Sello" (PasoTrazabilidad) ---
            paso_finalizado = self.tracking_repo.finalizar_paso(paso_activo.id)

            if not paso_finalizado:
                self.main_window.show_message("Error", "No se pudo guardar la finalización del paso.", "error")
                return

            # --- 5. Comprobar si era el último paso ---
            # (Se mantiene la lógica de ejemplo temporal)

            # TODO: Esta lógica debe implementarse.
            # Aquí deberías consultar el Producto y ver si 'paso_finalizado.paso_nombre'
            # era la última subfabricacion / proceso.

            es_paso_final = False
            if "Paso Genérico" in paso_finalizado.paso_nombre:
                # Para este test, un producto simple solo tiene un paso.
                # TODO: Reemplazar esto con lógica real de subfabricaciones
                es_paso_final = True

            # --- 6. Si era el último, finalizar el "Pasaporte" (TrabajoLog) ---
            if es_paso_final:
                self.logger.info(
                    f"Era el último paso. Finalizando el TrabajoLog (Pasaporte) ID: {paso_finalizado.trabajo_log_id}")
                trabajo_log_finalizado = self.tracking_repo.finalizar_trabajo_log(
                    paso_finalizado.trabajo_log_id,
                    notas_finalizacion="Completado último paso."
                )
                if trabajo_log_finalizado:
                    self.main_window.show_message(
                        "Unidad Completada",
                        f"¡Has completado el último paso!\n\nDuración total unidad: {trabajo_log_finalizado.duracion_segundos}s",
                        "info"
                    )
            else:
                self.main_window.show_message(
                    "Paso Finalizado",
                    f"Paso '{paso_finalizado.paso_nombre}' completado en {paso_finalizado.duracion_paso_segundos} segundos.",
                    "info"
                )

            # --- 7. Actualizar UI ---
            self._load_active_trabajos()  # Recargar caché
            self.main_window.update_task_state("pendiente", None)  # Volver a estado "listo"
            self.main_window.enable_action_buttons(False)  # Deshabilitar botones de acción

        except Exception as e:
            self.logger.error(f"Error crítico al finalizar paso: {e}", exc_info=True)
            self.main_window.show_message("Error Crítico", f"Ocurrió un error al finalizar el paso: {e}", "error")

    def _handle_register_incidence(self, task_data: Dict[str, Any]):
        """
        Maneja la solicitud de registrar una incidencia para el PASO activo.
        MODIFICADO: Ahora requiere escanear el QR de la unidad activa para confirmar.
        """
        if not self.qr_scanner or not self.tracking_repo:
            self.logger.error("QR Scanner o Tracking Repository no están disponibles")
            return

        trabajador_id = self.current_user.get('id')

        try:
            # 1. Buscar el paso activo de este trabajador
            paso_activo = self.tracking_repo.get_paso_activo_por_trabajador(trabajador_id)

            if not paso_activo:
                self.logger.warning(
                    f"Intento de registrar incidencia sin un paso activo (Trabajador ID: {trabajador_id})")
                self.main_window.show_message("Error",
                                              "Debe tener un paso 'en_proceso' para poder registrar una incidencia.",
                                              "warning")
                return

            # 2. Obtener el QR del pasaporte asociado a este paso activo
            # Usar el trabajo_log_id en lugar de acceder a la relación
            trabajo_log_activo = self.tracking_repo.obtener_trabajo_por_id(paso_activo.trabajo_log_id)
            if not trabajo_log_activo:
                self.main_window.show_message("Error de Sincronización",
                                              "No se encuentra el 'pasaporte' de tu tarea activa.", "error")
                return

            qr_de_la_tarea_activa = trabajo_log_activo.qr_code
            trabajo_log_id = trabajo_log_activo.id

            self.logger.info(
                f"Registrando incidencia para el Trabajo Log ID: {trabajo_log_id}. Se espera QR: {qr_de_la_tarea_activa}")

            # 3. Escanear QR para confirmar
            self.main_window.show_message("Escáner",
                                          f"Acerque el QR ({qr_de_la_tarea_activa[:10]}...) para REGISTRAR INCIDENCIA...",
                                          "info")

            qr_data_escaneado = self.qr_scanner.scan_once(timeout=30)
            if not qr_data_escaneado:
                self.logger.info("Escaneo cancelado.")
                return

            # 4. Validar que el QR es el correcto
            if qr_data_escaneado != qr_de_la_tarea_activa:
                self.logger.warning(
                    f"QR incorrecto. Se esperaba '{qr_de_la_tarea_activa}' pero se escaneó '{qr_data_escaneado}'")
                self.main_window.show_message(
                    "QR Incorrecto",
                    "El QR escaneado no coincide con la unidad que tienes 'en_proceso'.",
                    "error"
                )
                return

            self.logger.info("Confirmación de QR exitosa.")

            # 5. Mostrar el diálogo para rellenar la incidencia
            dialog = IncidenceDialog(self.main_window)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_data()

                if not data:
                    self.main_window.show_message("Datos Faltantes", "El título y la descripción son obligatorios.",
                                                  "warning")
                    return

                # 6. Llamar al método 'registrar_incidencia' del REPOSITORIO
                incidencia = self.tracking_repo.registrar_incidencia(
                    trabajo_log_id=trabajo_log_id,
                    trabajador_id=trabajador_id,
                    tipo_incidencia=data["tipo_incidencia"],
                    descripcion=data["descripcion"],
                    rutas_fotos=data["fotos_paths"]
                )

                if incidencia:
                    self.logger.info(f"Incidencia registrada exitosamente: ID={incidencia.id}")
                    self.main_window.show_message(
                        "Incidencia Registrada",
                        "La incidencia ha sido registrada correctamente",
                        "info"
                    )
                else:
                    self.logger.warning("No se pudo registrar la incidencia")
                    self.main_window.show_message(
                        "Error",
                        "No se pudo registrar la incidencia en la base de datos.",
                        "error"
                    )
            else:
                self.logger.info("Registro de incidencia cancelado por el usuario.")

        except Exception as e:
            self.logger.error(f"Error crítico al registrar incidencia: {e}", exc_info=True)
            self.main_window.show_message("Error Crítico", f"Ocurrió un error al registrar la incidencia: {e}", "error")

    def _handle_export_data(self):
        """
        Maneja la exportación de datos de trabajo a un archivo JSON.
        """
        import json

        trabajador_id = self.current_user.get('id')
        trabajador_nombre = self.current_user.get('nombre', 'trabajador').replace(' ', '_')

        # 1. Obtener la fecha de la última exportación
        # Asumimos que el db_manager tiene config_repo (lo cual es cierto según database_manager.py)
        if not hasattr(self.db_manager, 'config_repo'):
            self.main_window.show_message("Error", "El repositorio de configuración no está disponible.", "error")
            return

        try:
            last_export_str = self.db_manager.config_repo.get_setting('last_export_date', '2000-01-01T00:00:00Z')
            last_export_date = datetime.fromisoformat(last_export_str.replace('Z', '+00:00'))
            self.logger.info(f"Última exportación: {last_export_date}")

            # 2. Obtener los datos nuevos desde el repositorio
            data_to_export = self.tracking_repo.get_data_for_export(trabajador_id, last_export_date)

            if not data_to_export:
                self.main_window.show_message("Nada que Exportar",
                                              "No hay datos de trabajo nuevos desde la última exportación.", "info")
                return

            # 3. Pedir al usuario dónde guardar el archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            default_filename = f"export_{trabajador_nombre}_{timestamp}.json"

            save_path, _ = QFileDialog.getSaveFileName(
                self.main_window,
                "Guardar Exportación de Datos",
                default_filename,
                "Archivos JSON (*.json)"
            )

            if not save_path:
                self.logger.info("Exportación cancelada por el usuario.")
                return

            # 4. Escribir el archivo JSON
            self.main_window.show_message("Exportando", "Guardando datos...", "info")
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_export, f, indent=4)

            # 5. Actualizar la fecha de última exportación
            new_export_time = datetime.now().isoformat()
            self.db_manager.config_repo.set_setting('last_export_date', new_export_time)

            self.logger.info(f"Datos exportados a {save_path}. Nueva fecha de exportación: {new_export_time}")
            self.main_window.show_message("Éxito", f"Se han exportado {len(data_to_export)} registros a:\n{save_path}",
                                          "info")

        except Exception as e:
            self.logger.error(f"Error durante la exportación de datos: {e}", exc_info=True)
            self.main_window.show_message("Error Crítico", f"No se pudo exportar: {e}", "error")

    def _handle_camera_config(self):
        """
        Muestra el diálogo de configuración de cámara.
        Permite al trabajador resolver problemas sin cambiar de usuario.
        """
        try:
            self.logger.info("Abriendo diálogo de configuración de cámara...")

            # Importar el diálogo
            from ui.worker.camera_config_dialog import CameraConfigDialog

            # Obtener índice de cámara actual
            current_camera_index = self.qr_scanner.camera_index if self.qr_scanner else 0

            # Crear y mostrar el diálogo
            dialog = CameraConfigDialog(
                camera_manager=self.camera_manager,
                current_camera_index=current_camera_index,
                parent=self.main_window
            )

            # Si el usuario acepta (presiona "Guardar y Usar")
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_camera_index = dialog.get_selected_camera()

                if new_camera_index is not None and new_camera_index >= 0:
                    self.logger.info(f"Usuario seleccionó cámara {new_camera_index}")

                    try:
                        # Importar QrScanner
                        from core.qr_scanner import QrScanner

                        # 1. Liberar scanner anterior si existe
                        if self.qr_scanner:
                            self.qr_scanner.release_camera()
                            self.logger.info("Scanner anterior liberado")

                        # ----------------------------------------------------------
                        # INICIO DE MEJORA (HD + AUTOFOCUS)
                        # ----------------------------------------------------------

                        # 2. Abrir el hardware de la nueva cámara
                        self.logger.info(f"Abriendo hardware de cámara {new_camera_index}...")

                        # Usar el backend adecuado según el sistema
                        backend_enum = self.camera_manager.get_system_backend()
                        backend_to_use = backend_enum.value
                        camera_object = cv2.VideoCapture(new_camera_index, backend_to_use)

                        if camera_object and camera_object.isOpened():
                            self.logger.info(f"Conexión exitosa con backend {backend_enum.name} para cámara {new_camera_index}.")

                            self.logger.info("Solicitando resolución HD (1280x720)...")
                            camera_object.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                            camera_object.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

                            self.logger.info("Activando autofocus (AUTOFOCUS=1)...")
                            camera_object.set(cv2.CAP_PROP_AUTOFOCUS, 1)  # 0=Manual, 1=Auto

                            # Loguear la resolución real obtenida
                            width = camera_object.get(cv2.CAP_PROP_FRAME_WIDTH)
                            height = camera_object.get(cv2.CAP_PROP_FRAME_HEIGHT)
                            self.logger.info(f"Resolución real obtenida: {int(width)}x{int(height)}")
                        # ----------------------------------------------------------
                        # FIN DE MEJORA
                        # ----------------------------------------------------------

                        if not camera_object or not camera_object.isOpened():
                            self.logger.error(
                                f"No se pudo abrir hardware de cámara {new_camera_index} con backend {backend_enum.name}.")
                            raise Exception(f"No se pudo abrir el hardware de la cámara {new_camera_index}.")

                        self.logger.info(f"Hardware de cámara {new_camera_index} abierto y listo.")

                        # 3. Crear nuevo scanner con TODOS los argumentos requeridos
                        self.qr_scanner = QrScanner(
                            camera_manager=self.camera_manager,
                            camera_index=new_camera_index,
                            camera_object=camera_object
                        )

                        if not self.qr_scanner.is_camera_ready:
                            raise Exception("QrScanner reportó que la cámara no está lista después de la creación.")

                        # 4. Guardar configuración en la base de datos
                        self.db_manager.config_repo.set_setting('camera_index', str(new_camera_index))
                        self.logger.info(f"Configuración guardada en DB: camera_index = {new_camera_index}")

                        # 5. Notificar al usuario
                        QMessageBox.information(
                            self.main_window,
                            "✅ Configuración Guardada",
                            f"Cámara actualizada correctamente.\n\n"
                            f"Ahora usando cámara {new_camera_index}.\n\n"
                            "Los próximos escaneos de QR usarán esta cámara."
                        )

                        self.logger.info("Configuración de cámara completada exitosamente")

                    except Exception as e:
                        self.logger.error(f"Error actualizando scanner: {e}", exc_info=True)
                        QMessageBox.critical(
                            self.main_window,
                            "Error",
                            f"No se pudo actualizar la configuración de cámara:\n\n{str(e)}"
                        )

                else:
                    self.logger.warning("No se seleccionó una cámara válida")

            else:
                self.logger.info("Usuario canceló la configuración de cámara")

        except ImportError as e:
            self.logger.error(f"Error importando diálogo de cámara: {e}", exc_info=True)
            QMessageBox.critical(
                self.main_window,
                "Error",
                f"No se pudo cargar el diálogo de configuración:\n\n{str(e)}\n\n"
                "Verifica que el archivo 'camera_config_dialog.py' esté en el directorio correcto."
            )

        except Exception as e:
            self.logger.error(f"Error en configuración de cámara: {e}", exc_info=True)
            QMessageBox.critical(
                self.main_window,
                "Error",
                f"Error inesperado al configurar la cámara:\n\n{str(e)}"
            )



