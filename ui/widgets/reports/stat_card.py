"""Tarjeta reutilizable de estadísticas para reportes."""

from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout


class StatCard(QFrame):
    """Tarjeta de estadística individual."""

    STYLE = """
        QFrame {
            background-color: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
        }
    """

    def __init__(self, title: str, value: str, subtitle: str = "", color: str = "#2563eb") -> None:
        super().__init__()
        self.setStyleSheet(self.STYLE)
        self.setMinimumWidth(150)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
        layout.addWidget(value_label)

        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setStyleSheet("color: #94a3b8; font-size: 10px;")
            layout.addWidget(sub_label)

