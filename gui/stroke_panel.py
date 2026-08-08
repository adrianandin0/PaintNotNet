from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QToolButton, QButtonGroup, QSlider, QSpinBox, QGroupBox, QAbstractSpinBox
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize, Qt

class StrokePanelWidget(QWidget):
    """Panel Pincel (Forma, Ancho y Suavizado) ajustado a 9px sin negritas en etiquetas."""
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        group_style = (
            "QGroupBox { font-size: 9px; font-weight: normal; margin-top: 8px; padding-top: 4px; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; background-color: transparent; }"
        )

        # --- Forma del Pincel ---
        group_forma = QGroupBox("Forma")
        group_forma.setStyleSheet(group_style)
        layout_forma = QHBoxLayout()
        layout_forma.setContentsMargins(4, 4, 4, 4)

        self.btn_circle = QToolButton()
        self.btn_circle.setCheckable(True)
        self.btn_circle.setToolTip("Redondo")
        self.btn_circle.setIcon(QIcon("gui/iconos/circle.png"))
        self.btn_circle.setIconSize(QSize(12, 12))
        self.btn_circle.setFixedSize(26, 26)
        self.btn_circle.setChecked(True)

        self.btn_square = QToolButton()
        self.btn_square.setCheckable(True)
        self.btn_square.setToolTip("Cuadrado")
        self.btn_square.setIcon(QIcon("gui/iconos/square.png"))
        self.btn_square.setIconSize(QSize(12, 12))
        self.btn_square.setFixedSize(26, 26)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.button_group.addButton(self.btn_circle)
        self.button_group.addButton(self.btn_square)
        self.button_group.buttonClicked.connect(self._on_forma_changed)

        layout_forma.addWidget(self.btn_circle)
        layout_forma.addWidget(self.btn_square)
        group_forma.setLayout(layout_forma)
        layout.addWidget(group_forma)

        # --- Ancho ---
        layout_ancho = QHBoxLayout()
        layout_ancho.setContentsMargins(2, 2, 2, 2)

        lbl_ancho = QLabel("Ancho:")
        lbl_ancho.setStyleSheet("font-size: 9px; font-weight: normal;")

        self.spin_ancho = QSpinBox()
        self.spin_ancho.setRange(1, 100)
        self.spin_ancho.setValue(3)
        self.spin_ancho.setFixedHeight(20)
        self.spin_ancho.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_ancho.setStyleSheet("font-size: 9px;")
        self.spin_ancho.valueChanged.connect(self._on_ancho_changed)

        layout_ancho.addWidget(lbl_ancho)
        layout_ancho.addWidget(self.spin_ancho)
        layout.addLayout(layout_ancho)

        # --- Suavizado ---
        group_suavizado = QGroupBox("Suavizado")
        group_suavizado.setStyleSheet(group_style)
        layout_suav = QVBoxLayout()
        layout_suav.setContentsMargins(4, 4, 4, 4)

        h_layout_suav = QHBoxLayout()
        self.slider_suavizado = QSlider(Qt.Orientation.Horizontal)
        self.slider_suavizado.setRange(0, 100)
        self.slider_suavizado.setValue(100)
        self.slider_suavizado.valueChanged.connect(self._on_suavizado_changed)

        self.lbl_suav_val = QLabel("100%")
        self.lbl_suav_val.setStyleSheet("font-size: 9px;")
        self.lbl_suav_val.setFixedWidth(36)

        h_layout_suav.addWidget(self.slider_suavizado)
        h_layout_suav.addWidget(self.lbl_suav_val)
        layout_suav.addLayout(h_layout_suav)
        group_suavizado.setLayout(layout_suav)
        layout.addWidget(group_suavizado)

        layout.addStretch()
        self.setLayout(layout)

    def _on_forma_changed(self, button):
        forma = "Redondo" if button == self.btn_circle else "Cuadrado"
        if self.main_window and hasattr(self.main_window, 'canvas'):
            self.main_window.canvas.forma_pincel = forma

    def _on_ancho_changed(self, val):
        if self.main_window and hasattr(self.main_window, 'canvas'):
            self.main_window.canvas.grosor_pincel = val

    def _on_suavizado_changed(self, val):
        self.lbl_suav_val.setText(f"{val}%")
        if self.main_window and hasattr(self.main_window, 'canvas'):
            canvas = self.main_window.canvas
            if val == 0:
                canvas.suavizado_pincel = False
                canvas.opacidad_pincel = 255
            else:
                canvas.suavizado_pincel = True
                canvas.opacidad_pincel = int(255 * (val / 100.0))
