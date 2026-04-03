"""Diálogo modal para registrar incidencias del operario."""

from __future__ import annotations

from typing import Any, Optional

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class IncidenceDialog(QDialog):
    """
    Diálogo modal para que el trabajador registre una incidencia,
    incluyendo título, descripción y la posibilidad de adjuntar fotos.
    """

    def __init__(self, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Registrar Nueva Incidencia")
        self.setModal(True)
        self.setMinimumSize(450, 400)

        self.fotos_paths: list[str] = []

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.tipo_incidencia_edit = QLineEdit()
        self.tipo_incidencia_edit.setPlaceholderText("Ej: 'Material defectuoso', 'Parada de máquina'...")

        self.descripcion_edit = QTextEdit()
        self.descripcion_edit.setPlaceholderText("Explica qué ha ocurrido...")

        form_layout.addRow("Título/Tipo de Incidencia:", self.tipo_incidencia_edit)
        form_layout.addRow("Descripción detallada:", self.descripcion_edit)

        layout.addLayout(form_layout)
        layout.addWidget(QLabel("Fotos (Opcional):"))

        self.fotos_list_widget = QListWidget()
        self.fotos_list_widget.setFixedHeight(80)
        layout.addWidget(self.fotos_list_widget)

        self.add_foto_btn = QPushButton("📷 Adjuntar Foto...")
        self.add_foto_btn.clicked.connect(self._on_add_foto)
        layout.addWidget(self.add_foto_btn)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _on_add_foto(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar Fotos",
            "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp)",
        )
        for file_path in files:
            self.fotos_paths.append(file_path)
            self.fotos_list_widget.addItem(file_path.split("/")[-1])

    def get_data(self) -> dict[str, Any] | None:
        tipo_incidencia = self.tipo_incidencia_edit.text().strip()
        descripcion = self.descripcion_edit.toPlainText().strip()
        if not tipo_incidencia or not descripcion:
            return None
        return {
            "tipo_incidencia": tipo_incidencia,
            "descripcion": descripcion,
            "fotos_paths": self.fotos_paths,
        }

