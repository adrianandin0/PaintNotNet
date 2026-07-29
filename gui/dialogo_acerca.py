from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QScrollArea, QWidget
from PyQt6.QtCore import Qt


class DialogoAcerca(QDialog):
    """Diálogo 'Acerca de' de PaintNotNet con scroll adaptable."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Acerca de PaintNotNet")
        self.setFixedSize(540, 480)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        lbl_titulo = QLabel("PaintNotNet (Versión Beta)")
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

        html_content = (
            "<div style='font-size: 11px; color: #DDDDDD; line-height: 1.5;'>"
            "PaintNotNet es un software de diseño y edición de imágenes sencillo pero potente, desarrollado para Linux e inspirado en el clásico Paint.NET.<br><br>"
            "Ofrece características clave para el trabajo con imágenes, tales como manejo de capas, historial de acciones y la posibilidad de guardar tus proyectos para continuarlos en cualquier momento.<br><br>"
            "Desarrollado en Python con la asistencia de <b>Google Gemini</b> y <b>Google Antigravity</b>.<br><br>"
            "<b>Autor:</b> Adrian &nbsp;|&nbsp; "
            "<b>X:</b> <a href='https://www.x.com/adrian_and_ino' style='color: #64B4FF; text-decoration: underline;'>@adrian_and_ino</a> &nbsp;|&nbsp; "
            "<b>GitHub:</b> <a href='https://github.com/adrianandin0/PaintNotNet/' style='color: #64B4FF; text-decoration: underline;'>PaintNotNet Repository</a><br><br>"
            "El proyecto se encuentra en constante desarrollo. Todos son bienvenidos a colaborar o reportar errores.<br><br>"
            "<b>Créditos de Íconos y Recursos Gráficos:</b><br>"
            "<a href='https://www.flaticon.com/' style='color: #64B4FF; text-decoration: underline;'>Flaticon</a> &bull; "
            "<a href='https://www.flaticon.com/authors/magnific' style='color: #64B4FF; text-decoration: underline;'>Magnific</a> &bull; "
            "<a href='https://www.flaticon.com/authors/uniconlabs' style='color: #64B4FF; text-decoration: underline;'>Uniconlabs</a> &bull; "
            "<a href='https://www.flaticon.com/authors/balraj-chana' style='color: #64B4FF; text-decoration: underline;'>Balraj Chana</a> &bull; "
            "<a href='https://www.flaticon.com/authors/gajah-mada' style='color: #64B4FF; text-decoration: underline;'>Gajah Mada</a>"
            "</div>"
        )

        lbl_body = QLabel(html_content)
        lbl_body.setWordWrap(True)
        lbl_body.setOpenExternalLinks(True)
        lbl_body.setAlignment(Qt.AlignmentFlag.AlignLeft)
        scroll_layout.addWidget(lbl_body)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setFixedWidth(100)
        btn_cerrar.setStyleSheet("padding: 5px 15px; font-weight: bold;")
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)
