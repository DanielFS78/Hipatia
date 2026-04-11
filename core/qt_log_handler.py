# -*- coding: utf-8 -*-
"""
Nombre del Módulo: qt_log_handler
Descripcion: Handler de logging de Python que integra el registro estándar con
             el hilo de la interfaz Qt. Por defecto el nivel del handler es
             ``INFO``, por lo que los mensajes ``INFO`` y superiores se reenvían
             a la UI mediante señales Qt (apto para uso desde otros hilos).

             Diseño:
             - ``QtLogHandler`` hereda de ``logging.Handler`` (no puede ser
               QObject simultáneamente, por eso se delega la señal a
               ``_SignalEmitter``).
             - ``_SignalEmitter`` es un ``QObject`` mínimo que expone la señal
               ``log_emitted(str)``.  Al conectar esa señal a un slot del hilo
               principal, Qt garantiza que la ejecución del slot ocurre en el
               event-loop correcto aunque ``emit()`` se invoque desde otro hilo.
             - Almacena en un buffer interno los mensajes que llegan antes de que
               la UI esté lista.  Cuando ``connect_to_widget()`` se invoca,
               reproduce el buffer completo para que el usuario vea también los
               warnings de arranque generados antes del login.
"""
from __future__ import annotations

import logging
from typing import Callable

from PyQt6.QtCore import QObject, pyqtSignal


class _SignalEmitter(QObject):
    """
    Objeto Qt auxiliar que alberga la señal de log.

    Se separa en su propia clase porque ``logging.Handler`` no puede heredar
    de ``QObject`` (herencia múltiple incompatible con la metaclase de Qt).

    Signals:
        log_emitted: emitida por cada registro de log procesado.
                     Transporta el mensaje ya formateado como cadena.
    """

    log_emitted: pyqtSignal = pyqtSignal(str)


class QtLogHandler(logging.Handler):
    """
    Handler que reenvía a la UI de Qt los registros desde el nivel del handler
    (por defecto ``INFO``) en adelante.

    Conexión thread-safe vía señal ``log_emitted``. Buffer interno hasta la
    primera llamada a ``connect_to_widget()`` (arranque y login sin terminal).

    En la aplicación, ``app.py`` delega en ``HomeWidget.connect_log_handler`` o
    ``WorkerMainWindow.connect_log_handler``, que a su vez llaman a este método
    con el ``append_log`` del ``LogTerminalWidget`` correspondiente.

    Attributes:
        emitter: ``_SignalEmitter`` con la señal ``log_emitted(str)``.
    """

    def __init__(self) -> None:
        """
        Inicializa el handler con nivel ``INFO``, formatter estándar y buffer vacío.

        El formatter incluye hora, nivel y nombre del logger para facilitar
        la identificación del origen del mensaje en la terminal visual.
        """
        super().__init__(level=logging.INFO)
        self.emitter = _SignalEmitter()
        formatter = logging.Formatter(
            "%(asctime)s  [%(levelname)8s]  %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
        self.setFormatter(formatter)
        self._buffer: list[str] = []
        self._widget_slot: Callable[[str], None] | None = None

    def emit(self, record: logging.LogRecord) -> None:
        """
        Procesa un registro de log y emite la señal Qt con el mensaje formateado.

        Si el widget de destino aún no está conectado, el mensaje se almacena
        en el buffer interno para ser reproducido posteriormente.

        Llamado automáticamente por el sistema de logging cada vez que se
        genera un mensaje cuyo nivel supera el mínimo del handler.

        Args:
            record: Registro de log generado por el framework estándar de Python.
        """
        try:
            msg = self.format(record)
            if self._widget_slot is None:
                # UI aún no lista — almacenar para reproducir después
                self._buffer.append(msg)
            else:
                self.emitter.log_emitted.emit(msg)
        except Exception:
            self.handleError(record)

    def connect_to_widget(self, slot: Callable[[str], None]) -> None:
        """
        Conecta el handler al slot del widget y reproduce el buffer acumulado.

        Debe llamarse **una sola vez por sesión**, cuando ya existe el widget de
        destino: terminal de ``HomeWidget`` (vista principal) o de
        ``WorkerMainWindow`` (pestaña Log). A partir de aquí los mensajes van en
        tiempo real al slot y dejan de acumularse solo en memoria.

        Args:
            slot: Callable que recibe el mensaje ya formateado; habitualmente
                  ``LogTerminalWidget.append_log``.
        """
        self._widget_slot = slot
        self.emitter.log_emitted.connect(slot)

        # Reproducir mensajes almacenados durante el arranque
        for buffered_msg in self._buffer:
            self.emitter.log_emitted.emit(buffered_msg)
        self._buffer.clear()
