from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QScrollArea, QWidget
from PyQt6.QtCore import Qt
from core.i18n import t


class DialogoAcerca(QDialog):
    """Diálogo 'Acerca de' de PaintNotNet con i18n y scroll adaptable."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("Acerca de PaintNotNet"))
        self.setFixedSize(540, 480)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        lbl_titulo = QLabel(t("PaintNotNet (Versión Beta)"))
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #00AAFF;")
        layout.addWidget(lbl_titulo)

        # Scroll Area para permitir lectura completa en cualquier DPI / resolución
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(4, 4, 4, 4)

        html_content = t("ACERCA_BODY_HTML")

        lbl_body = QLabel(html_content)
        lbl_body.setWordWrap(True)
        lbl_body.setOpenExternalLinks(True)
        lbl_body.setAlignment(Qt.AlignmentFlag.AlignLeft)
        scroll_layout.addWidget(lbl_body)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        btn_cerrar = QPushButton(t("Cerrar"))
        btn_cerrar.setFixedWidth(100)
        btn_cerrar.setStyleSheet("padding: 5px 15px; font-weight: bold;")
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)
