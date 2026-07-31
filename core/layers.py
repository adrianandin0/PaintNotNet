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

        capa_base = Layer("Capa 1", width, height, transparent=True)
        self.capas = [capa_base]
        self.indice_activo = 0

    @property
    def buffer(self):
        return self.capas[self.indice_activo].image

    @buffer.setter
    def buffer(self, nueva_imagen):
        self.capas[self.indice_activo].image = nueva_imagen

    def agregar_capa(self, nombre="Nueva Capa"):
        nueva_capa = Layer(nombre, self.width, self.height, transparent=True)
        idx = max(0, self.indice_activo)
        self.capas.insert(idx, nueva_capa)
        self.indice_activo = idx

    def combinar_capas_indices(self, indices):
        """
        Combina los índices de capas seleccionadas.
        Mantiene el nombre de la capa ubicada más arriba (menor índice en lista visual).
        """
        if not indices or len(indices) < 2:
            return

        indices_ordenados = sorted(indices)
        top_idx = indices_ordenados[0]
        nombre_final = self.capas[top_idx].name

        capa_combinada = Layer(nombre_final, self.width, self.height, transparent=True)
        painter = QPainter(capa_combinada.image)

        for idx in reversed(indices_ordenados):
            painter.drawImage(0, 0, self.capas[idx].image)
        painter.end()

        min_idx = indices_ordenados[0]
        self.capas[min_idx] = capa_combinada

        for idx in reversed(indices_ordenados[1:]):
            self.capas.pop(idx)

        self.indice_activo = min_idx

    def get_qimage(self, capa_trazo_temp=None, draw_layer_preview_callback=None, selection_path=None):
        imagen_final = QImage(self.width, self.height, QImage.Format.Format_ARGB32_Premultiplied)
        imagen_final.fill(Qt.GlobalColor.transparent)

        painter = QPainter(imagen_final)
        for i, capa in enumerate(reversed(self.capas)):
            if capa.visible:
                painter.drawImage(0, 0, capa.image)
                idx_real = len(self.capas) - 1 - i
                if idx_real == self.indice_activo:
                    if capa_trazo_temp and not capa_trazo_temp.isNull():
                        painter.save()
                        if selection_path and not selection_path.isEmpty():
                            painter.setClipPath(selection_path)
                        painter.drawImage(0, 0, capa_trazo_temp)
                        painter.restore()
                    if draw_layer_preview_callback:
                        painter.save()
                        if selection_path and not selection_path.isEmpty():
                            painter.setClipPath(selection_path)
                        draw_layer_preview_callback(painter)
                        painter.restore()
        painter.end()

        return imagen_final

    def get_qpixmap(self, capa_trazo_temp=None, draw_layer_preview_callback=None, selection_path=None):
        return QPixmap.fromImage(self.get_qimage(capa_trazo_temp=capa_trazo_temp, draw_layer_preview_callback=draw_layer_preview_callback, selection_path=selection_path))

    def resize_canvas(self, new_width, new_height):
        for capa in self.capas:
            nuevo_buffer = QImage(new_width, new_height, QImage.Format.Format_ARGB32_Premultiplied)
            nuevo_buffer.fill(Qt.GlobalColor.transparent)

            painter = QPainter(nuevo_buffer)
            painter.drawImage(0, 0, capa.image)
            painter.end()

            capa.image = nuevo_buffer

        self.width = new_width
        self.height = new_height
