# -*- coding: utf-8 -*-
from .base import *

class HomeWidget(QWidget):
    """Widget para la pantalla de inicio."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Título de bienvenida
        welcome_label = QLabel("Bienvenido a la Calculadora de Tiempos")
        welcome_font = QFont()
        welcome_font.setPointSize(28)
        welcome_font.setBold(True)
        welcome_label.setFont(welcome_font)
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_label)

        layout.addSpacing(30)

        # Contenedor principal de la frase (Card layout)
        quote_container = QFrame()
        quote_container.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 15px;
                border: 1px solid #e1e4e8;
            }
        """)
        quote_layout = QHBoxLayout(quote_container)
        quote_layout.setContentsMargins(20, 20, 20, 20)
        quote_layout.setSpacing(20)

        # Imagen del autor
        self.author_image = QLabel()
        self.author_image.setFixedSize(120, 150)
        self.author_image.setStyleSheet("border: 1px solid #ccc; background-color: #eee; border-radius: 5px;")
        self.author_image.setScaledContents(True)
        self.author_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.author_image.setText("Sin foto")
        quote_layout.addWidget(self.author_image)

        # Texto y Bio
        text_layout = QVBoxLayout()
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.quote_text = QLabel("Cargando frase...")
        font_quote = QFont()
        font_quote.setPointSize(18)
        font_quote.setItalic(True)
        self.quote_text.setFont(font_quote)
        self.quote_text.setWordWrap(True)
        self.quote_text.setStyleSheet("color: #2c3e50;")
        text_layout.addWidget(self.quote_text)

        text_layout.addSpacing(10)

        self.author_text = QLabel("")
        font_author = QFont()
        font_author.setPointSize(14)
        font_author.setBold(True)
        self.author_text.setFont(font_author)
        self.author_text.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.author_text.setStyleSheet("color: #34495e;")
        text_layout.addWidget(self.author_text)

        self.author_bio = QLabel("")
        font_bio = QFont()
        font_bio.setPointSize(10)
        self.author_bio.setFont(font_bio)
        self.author_bio.setWordWrap(True)
        self.author_bio.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.author_bio.setStyleSheet("color: #7f8c8d;")
        text_layout.addWidget(self.author_bio)

        quote_layout.addLayout(text_layout)
        layout.addWidget(quote_container)
        
        layout.addStretch()

    def set_quote(self, quote, author, author_info=None):
        self.quote_text.setText(f"« {quote} »")
        self.author_text.setText(f"— {author}")
        
        if author_info:
            summary = author_info.get("summary", "")
            image_url = author_info.get("image_url", None)
            
            if summary:
                self.author_bio.setText(summary)
            else:
                self.author_bio.clear()

            if image_url:
                # Cargar imagen de forma asíncrona idealmente, pero aquí usaremos requests básico
                # En un entorno real, esto debería ir en un hilo aparte
                import requests
                from PyQt6.QtGui import QPixmap
                try:
                    # Wikimedia requiere un User-Agent válido
                    headers = {'User-Agent': 'CalculadorTiempos/1.0 (daniel@example.com)'}
                    response = requests.get(image_url, timeout=5, headers=headers)
                    if response.status_code == 200 and len(response.content) > 1000:  # Validar que no sea un placeholder
                        pixmap = QPixmap()
                        if pixmap.loadFromData(response.content):
                            self.author_image.setPixmap(pixmap.scaled(120, 150, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
                            self.author_image.setText("")  # Borrar texto placeholder
                        else:
                            self.author_image.setText("Sin foto")
                    else:
                        self.author_image.setText("Sin foto")
                except Exception as e:
                    logging.warning(f"No se pudo cargar imagen del autor: {e}")
                    self.author_image.setText("Sin foto")
            else:
                self.author_image.clear()
                self.author_image.setText("Sin foto")
        
        logging.info(f"Frase actualizada en la UI: '{quote}' - {author}")
