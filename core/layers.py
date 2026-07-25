from PyQt6.QtGui import QImage, QPixmap, QPainter
from PyQt6.QtCore import Qt

class LayerManager:
    """Maneja el buffer gráfico de la imagen."""
    def __init__(self, width=800, height=600):
        self.width = width
        self.height = height
        # Volvemos a usar QImage nativo como en tu código original
        self.buffer = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        self.buffer.fill(Qt.GlobalColor.white)

    def resize_canvas(self, new_width, new_height):
        new_buffer = QImage(new_width, new_height, QImage.Format.Format_ARGB32_Premultiplied)
        new_buffer.fill(Qt.GlobalColor.transparent)

        painter = QPainter(new_buffer)
        painter.drawImage(0, 0, self.buffer)
        painter.end()

        self.buffer = new_buffer
        self.width = new_width
        self.height = new_height

    def get_qimage(self):
        # Ahora devuelve directamente el buffer real, no una copia temporal
        return self.buffer

    def get_qpixmap(self):
        return QPixmap.fromImage(self.buffer)
