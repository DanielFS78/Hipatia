# -*- coding: utf-8 -*-
"""
Nombre del Módulo: qt_log_handler
Descripcion: Handler de logging de Python que integra el sistema de registro
             estándar con el hilo de interfaz de Qt. Captura mensajes de nivel
             WARNING, ERROR y CRITICAL y los reenvía a la UI mediante señales
             Qt (thread-safe) para su visualización en tiempo real.

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
    Handler de logging que reenvía mensajes WARNING/ERROR/CRITICAL a la UI de Qt.

    Conecta el sistema de logging de Python con un widget de visualización en la
    interfaz gráfica de forma thread-safe: usa una señal Qt para cruzar
    desde hilos de fondo al event-loop del hilo principal.

    Incorpora un buffer interno que almacena mensajes mientras la UI no está
    lista (antes e incluso durante el proceso de login). Al llamar a
    ``connect_to_widget()``, el buffer se reproduce completo y a partir de
    ese momento los mensajes llegan en tiempo real.

    Uso típico::

        handler = QtLogHandler()
        logging.getLogger().addHandler(handler)
        # ... más tarde, una vez creado el HomeWidget ...
        handler.connect_to_widget(home_widget.append_log)

    Attributes:
        emitter: instancia de ``_SignalEmitter`` cuya señal ``log_emitted``
                 puede conectarse manualmente al slot del widget de destino.
    """

    def __init__(self) -> None:
        """
        Inicializa el handler con nivel WARNING, formatter estándar y buffer vacío.

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

        Debe llamarse una sola vez, una vez que el ``HomeWidget`` ha sido creado
        y mostrado. A partir de este momento los mensajes fluyen en tiempo real
        y no se buferizan más.

        Args:
            slot: Callable del widget de destino que acepta un único argumento
                  de tipo ``str`` (el mensaje formateado). Típicamente
                  ``LogTerminalWidget.append_log``.
        """
        self._widget_slot = slot
        self.emitter.log_emitted.connect(slot)

        # Reproducir mensajes almacenados durante el arranque
        for buffered_msg in self._buffer:
            self.emitter.log_emitted.emit(buffered_msg)
        self._buffer.clear()
