"""
brushes_panel.py — Panel de formas de pincel/goma
2 botones: Círculo y Cuadrado.
"""
from PyQt6.QtCore import Qt, QRectF, QSize
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPixmap, QIcon
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QToolButton, QButtonGroup, QVBoxLayout, QSizePolicy
)
from core.i18n import t

FORMAS = [
    ("Redondo",  "Círculo"),
    ("Cuadrado", "Cuadrado"),
]

ICON_SIZE = 36


def _make_icon(forma: str) -> QPixmap:
    pm = QPixmap(ICON_SIZE, ICON_SIZE)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    cx, cy = ICON_SIZE / 2, ICON_SIZE / 2
    pen = QPen(QColor(220, 220, 220), 2)
    brush = QBrush(QColor(180, 180, 180))
    p.setPen(pen)
    p.setBrush(brush)

    if forma == "Redondo":
        r = ICON_SIZE * 0.36
        p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))
    elif forma == "Cuadrado":
        s = ICON_SIZE * 0.60
        p.drawRect(QRectF(cx - s / 2, cy - s / 2, s, s))

    p.end()
    return pm


class BrushesPanelWidget(QWidget):
    """Panel lateral con botones de selección de forma de pincel."""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)
        self._btns: dict[str, QToolButton] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(3)
        self.setStyleSheet("BrushesPanelWidget { background-color: #2D2D2D; }")
        self.setAutoFillBackground(True)

        row_layout = QHBoxLayout()
        row_layout.setSpacing(4)
        row_layout.setContentsMargins(0, 0, 0, 0)

        for forma, label_key in FORMAS:
            btn = QToolButton()
            btn.setCheckable(True)
            btn.setFixedSize(34, 34)
            btn.setIconSize(QSize(28, 28))
            btn.setIcon(QIcon(_make_icon(forma)))
            btn.setToolTip(t(label_key))
            btn.setProperty("forma", forma)
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            btn.setStyleSheet("""
                QToolButton {
                    background: #2D2D2D;
                    border: 1px solid #686868;
                    border-radius: 4px;
                }
                QToolButton:hover {
                    background: #5C5C5C;
                    border: 1px solid #686868;
                }
                QToolButton:checked {
                    background: #1a5fa8;
                    border: 1px solid #3d8ef0;
                }
            """)
            btn.toggled.connect(lambda checked, f=forma: self._on_forma_changed(f, checked))
            row_layout.addWidget(btn)
            self._btn_group.addButton(btn)
            self._btns[forma] = btn

        layout.addLayout(row_layout)
        layout.addStretch()
        self.setLayout(layout)

        # Seleccionar por defecto
        forma_actual = "Redondo"
        if main_window and hasattr(main_window, 'canvas'):
            forma_actual = getattr(main_window.canvas, 'forma_pincel', 'Redondo')
        self._set_activo(forma_actual)

    def _on_forma_changed(self, forma: str, checked: bool):
        if not checked:
            return
        if not self.main_window:
            return
        if hasattr(self.main_window, 'tab_widget'):
            for i in range(self.main_window.tab_widget.count()):
                area = self.main_window.tab_widget.widget(i)
                canvas = area.widget() if (area and hasattr(area, 'widget')) else area
                if canvas and hasattr(canvas, 'forma_pincel'):
                    canvas.forma_pincel = forma
                    canvas.update()
        elif hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.forma_pincel = forma
            self.main_window.lienzo.update()

    def _set_activo(self, forma: str):
        btn = self._btns.get(forma)
        if btn:
            btn.setChecked(True)

    def sincronizar_con_canvas(self, canvas):
        forma = getattr(canvas, 'forma_pincel', 'Redondo')
        self._set_activo(forma)

    def retraducir_panel(self):
        for forma, label_key in FORMAS:
            btn = self._btns.get(forma)
            if btn:
                btn.setToolTip(t(label_key))
