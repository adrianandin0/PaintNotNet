from PyQt6.QtGui import QImage, QPixmap, QPainter
from PyQt6.QtCore import Qt

class Layer:
    """Representa una capa individual con su propia imagen y estado."""
    def __init__(self, name, width, height, transparent=True):
        self.name = name
        self.visible = True
        self.image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        if transparent:
            self.image.fill(Qt.GlobalColor.transparent)
        else:
            self.image.fill(Qt.GlobalColor.white)


class LayerManager:
    """Maneja el sistema de múltiples capas y su composición visual."""
    def __init__(self, width=800, height=600):
        self.width = width
        self.height = height

        # Inicializamos con la Capa 1 por defecto
        capa_base = Layer("Capa 1", width, height, transparent=True)
        self.capas = [capa_base]
        self.indice_activo = 0

    @property
    def buffer(self):
        """
        Escudo de compatibilidad para canvas.py.
        Devuelve siempre la imagen de la capa ACTIVA para que los trazos vayan ahí.
        """
        return self.capas[self.indice_activo].image

    @buffer.setter
    def buffer(self, nueva_imagen):
        """Permite que el Historial y los Menús sigan sobrescribiendo la capa activa sin crashear."""
        self.capas[self.indice_activo].image = nueva_imagen

    def agregar_capa(self, nombre="Nueva Capa"):
        """Crea una capa garantizando que sea 100% transparente y la vuelve la activa."""
        nueva_capa = Layer(nombre, self.width, self.height, transparent=True)
        self.capas.append(nueva_capa)
        self.indice_activo = len(self.capas) - 1

    def get_qimage(self):
        """
        Magia de composición: Apila todas las capas visibles (de abajo hacia arriba)
        y devuelve una única imagen aplanada para mostrar en pantalla.
        """
        imagen_final = QImage(self.width, self.height, QImage.Format.Format_ARGB32_Premultiplied)
        imagen_final.fill(Qt.GlobalColor.transparent)

        painter = QPainter(imagen_final)
        for capa in self.capas:
            if capa.visible:
                painter.drawImage(0, 0, capa.image)
        painter.end()

        return imagen_final

    def get_qpixmap(self):
        return QPixmap.fromImage(self.get_qimage())

    def resize_canvas(self, new_width, new_height):
        """Redimensiona el lienzo afectando a todas las capas por igual."""
        for capa in self.capas:
            nuevo_buffer = QImage(new_width, new_height, QImage.Format.Format_ARGB32_Premultiplied)
            nuevo_buffer.fill(Qt.GlobalColor.transparent)

            painter = QPainter(nuevo_buffer)
            painter.drawImage(0, 0, capa.image)
            painter.end()

            capa.image = nuevo_buffer

        self.width = new_width
        self.height = new_height
