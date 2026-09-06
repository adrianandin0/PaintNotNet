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

        from PyQt6.QtCore import QSettings
        settings = QSettings("PaintNotNet", "PaintNotNet")
        saved_unit = str(settings.value("ruler_unit", "cm"))
        if saved_unit not in ["cm", "in", "px"]:
            saved_unit = "cm"

        self.corner = RulerCornerWidget(self)
        self.top_ruler = RulerWidget(Qt.Orientation.Horizontal, canvas=canvas, scroll_area=area_scroll, parent=self)
        self.left_ruler = RulerWidget(Qt.Orientation.Vertical, canvas=canvas, scroll_area=area_scroll, parent=self)

        self.corner.set_unit(saved_unit)
        self.top_ruler.set_unit(saved_unit)
        self.left_ruler.set_unit(saved_unit)

        # Cuando el usuario cambia la unidad en el corner, ambas reglas se actualizan y se propaga la preferencia
        self.corner.unit_changed.connect(self._on_unit_changed)

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

    def _on_unit_changed(self, new_unit: str):
        from PyQt6.QtCore import QSettings
        QSettings("PaintNotNet", "PaintNotNet").setValue("ruler_unit", new_unit)
        self.top_ruler.set_unit(new_unit)
        self.left_ruler.set_unit(new_unit)
        if self.main_window and hasattr(self.main_window, 'tab_widget'):
            for i in range(self.main_window.tab_widget.count()):
                cont = self.main_window.tab_widget.widget(i)
                if cont and cont != self:
                    if hasattr(cont, 'corner'):
                        cont.corner.blockSignals(True)
                        cont.corner.set_unit(new_unit)
                        cont.corner.blockSignals(False)
                    if hasattr(cont, 'top_ruler'):
                        cont.top_ruler.set_unit(new_unit)
                    if hasattr(cont, 'left_ruler'):
                        cont.left_ruler.set_unit(new_unit)

    def widget(self):
        """Mantiene compatibilidad total con llamadas 'area.widget()' en main.py"""
        return self.canvas
