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

        lbl_titulo = QLabel("PaintNotNet")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #00AAFF;")
        layout.addWidget(lbl_titulo)

        lbl_version = QLabel(t("Versión: 1.0.8"))
        lbl_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_version.setStyleSheet("font-size: 13px; font-weight: normal; color: #999999;")
        layout.addWidget(lbl_version)

        from core.theme import ThemeManager
        tm = ThemeManager()
        is_light = (tm.resolver_nombre_tema(tm.current_theme) == "Claro")

        bg_col  = "#DFDFDF" if is_light else "#2D2D2D"
        txt_col = "#222222" if is_light else "#EDEDED"

        self.setStyleSheet(f"QDialog {{ background-color: {bg_col}; color: {txt_col}; }}")

        # Scroll Area para permitir lectura completa en cualquier DPI / resolución
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea, QScrollArea > QWidget > QWidget {{ border: none; background-color: {bg_col}; color: {txt_col}; }}")

        scroll_content = QWidget()
        scroll_content.setStyleSheet(f"background-color: {bg_col}; color: {txt_col};")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(4, 4, 4, 4)

        html_content = t("ACERCA_BODY_HTML")
        if is_light:
            html_content = (html_content
                .replace("#DDDDDD", "#222222")
                .replace("#EDEDED", "#222222")
                .replace("#FFFFFF", "#222222")
                .replace("#b8b8b8", "#444444")
                .replace("#aaaaaa", "#555555")
                .replace("#64B4FF", "#0066CC")
            )

        lbl_body = QLabel(html_content)
        lbl_body.setStyleSheet(f"color: {txt_col}; background-color: {bg_col};")
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
