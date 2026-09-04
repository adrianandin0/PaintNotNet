from PyQt6.QtWidgets import QWidget, QGridLayout
from PyQt6.QtCore import Qt
from gui.ruler_widget import RulerCornerWidget, RulerWidget


class CanvasContainerWidget(QWidget):
    """
    Contenedor principal que envuelve el QScrollArea del lienzo y agrega
    opcionalmente las reglas graduadas en los bordes superior e izquierdo.
    """
    def __init__(self, area_scroll, canvas, main_window=None, parent=None):
        super().__init__(parent)
        self.area_scroll = area_scroll
        self.canvas = canvas
        self.main_window = main_window

        self.corner = RulerCornerWidget(self)
        self.top_ruler = RulerWidget(Qt.Orientation.Horizontal, canvas=canvas, scroll_area=area_scroll, parent=self)
        self.left_ruler = RulerWidget(Qt.Orientation.Vertical, canvas=canvas, scroll_area=area_scroll, parent=self)

        # Vincular contenedor al lienzo para refrescos rápidos
        if hasattr(self.canvas, 'container'):
            self.canvas.container = self
        else:
            setattr(self.canvas, 'container', self)

        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)

        grid.addWidget(self.corner, 0, 0)
        grid.addWidget(self.top_ruler, 0, 1)
        grid.addWidget(self.left_ruler, 1, 0)
        grid.addWidget(self.area_scroll, 1, 1)

        # Ocultas por defecto hasta que se active el checkbox "Reglas"
        self.set_rulers_visible(False)

    def set_rulers_visible(self, visible: bool):
        self.corner.setVisible(visible)
        self.top_ruler.setVisible(visible)
        self.left_ruler.setVisible(visible)
        if visible:
            self.top_ruler.update()
            self.left_ruler.update()

    def update_rulers(self):
        if self.top_ruler.isVisible():
            self.top_ruler.update()
        if self.left_ruler.isVisible():
            self.left_ruler.update()

    def widget(self):
        """Mantiene compatibilidad total con llamadas 'area.widget()' en main.py"""
        return self.canvas
