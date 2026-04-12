# -*- coding: utf-8 -*-
"""
Nombre del Módulo: connection_dialog
Descripción: Diálogo de arranque para elegir modo de base de datos local (SQLite) o
             servidor (PostgreSQL), antes de abrir la aplicación principal.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QRadioButton, 
    QButtonGroup, QCheckBox, QHBoxLayout, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont
from typing import Any

class ConnectionDialog(QDialog):
    """
    Ventana modal que captura la preferencia de conexión a datos (fichero local vs motor servidor).
    """
    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Modo de Conexión - Tiempos de Fabricación")
        self.setFixedSize(400, 350)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        
        # Styles
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
            }
            QLabel#title {
                font-size: 18px;
                font-weight: bold;
                color: #333;
                margin-bottom: 20px;
            }
            QFrame#option_frame {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 8px;
                padding: 15px;
            }
            QRadioButton {
                font-size: 14px;
                spacing: 10px;
                padding: 5px;
            }
            QPushButton#connect_btn {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton#connect_btn:hover {
                background-color: #0056b3;
            }
            QCheckBox {
                font-size: 12px;
                color: #666;
                spacing: 5px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        title = QLabel("Seleccione Modo de Conexión", self)
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Options Container
        frame = QFrame(self)
        frame.setObjectName("option_frame")
        frame_layout = QVBoxLayout(frame)
        
        # Radio Buttons
        self.group = QButtonGroup(self)
        
        self.rb_local = QRadioButton("📂 Modo Local (Standalone)")
        self.rb_local.setToolTip("Usa la base de datos local (SQLite). Ideal para usar sin internet.")
        self.rb_local.setChecked(True)
        
        self.rb_server = QRadioButton("🌐 Modo Servidor (PostgreSQL)")
        self.rb_server.setToolTip("Conecta al servidor central. Requiere conexión a la red.")

        self.group.addButton(self.rb_local, 1)
        self.group.addButton(self.rb_server, 2)
        
        frame_layout.addWidget(self.rb_local)
        frame_layout.addSpacing(10)
        frame_layout.addWidget(self.rb_server)
        
        layout.addWidget(frame)

        # Remember Choice
        self.chk_remember = QCheckBox("Recordar mi elección en este equipo")
        layout.addWidget(self.chk_remember)
        
        layout.addStretch()

        # Connect Button
        self.btn_connect = QPushButton("Conectar e Iniciar", self)
        self.btn_connect.setObjectName("connect_btn")
        self.btn_connect.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_connect.clicked.connect(self.accept)
        layout.addWidget(self.btn_connect)

    def get_selection(self) -> tuple[str, bool]:
        """
        Returns a tuple: (mode_string, remember_bool)
        mode_string: 'sqlite' or 'postgresql'
        """
        mode = 'sqlite' if self.rb_local.isChecked() else 'postgresql'
        return mode, self.chk_remember.isChecked()

if __name__ == "__main__":  # pragma: no cover
    from PyQt6.QtWidgets import QApplication
    import sys
    import logging
    
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    app = QApplication(sys.argv)
    dialog = ConnectionDialog()
    if dialog.exec():
        logging.getLogger(__name__).info("Selected: %s", dialog.get_selection())
    sys.exit()
