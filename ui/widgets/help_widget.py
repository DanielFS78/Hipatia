# -*- coding: utf-8 -*-
from .base import *

class HelpWidget(QWidget):
    """Widget para mostrar la página de ayuda 'Cómo Funciona'."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        text_edit = QTextEdit(); text_edit.setReadOnly(True)
        help_html = """
        <h1>Guía de Usuario - Calculadora de Tiempos</h1>
        <p>Bienvenido a la guía de la aplicación. Aquí se explica el flujo de trabajo principal y el propósito de cada sección.</p>
        <h2>Flujo de Trabajo Principal</h2>
        <ol>
            <li><b>Configurar los Datos Base:</b> Ve a <b>Gestión de Datos</b> (Máquinas, Trabajadores, Productos).</li>
            <li><b>Crear un "Kit" de Fabricación:</b> Define productos y cantidades que se producirán juntos.</li>
            <li><b>Calcular la Planificación:</b> Ve a <b>OPERACIONES -> Calcular Tiempos</b>.</li>
            <li><b>Guardar y Consultar:</b> El resultado se guarda como una "Pila" para consulta posterior.</li>
        </ol>
        """
        text_edit.setHtml(help_html); layout.addWidget(text_edit)
