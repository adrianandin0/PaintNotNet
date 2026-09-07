from PyQt6.QtGui import QImage, QPixmap, QPainter
from PyQt6.QtCore import Qt
from core.i18n import t


class Layer:
    """Representa una capa individual con su propia imagen y estado."""
    def __init__(self, name, width, height, transparent=True):
        self.name = name
        self.visible = True
        self.locked = False
        self.opacity = 1.0
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
        self.active_stroke_alpha = 1.0

        nombre_inicial = t("Capa %1").replace("%1", "1")
        capa_base = Layer(nombre_inicial, width, height, transparent=True)
        self.capas = [capa_base]
        self.indice_activo = 0

    def get_active_layer(self):
        if 0 <= self.indice_activo < len(self.capas):
            return self.capas[self.indice_activo]
        return None

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
            capa = self.capas[idx]
            op = getattr(capa, 'opacity', 1.0)
            painter.setOpacity(op)
            painter.drawImage(0, 0, capa.image)
        painter.end()

        min_idx = indices_ordenados[0]
        self.capas[min_idx] = capa_combinada

        for idx in reversed(indices_ordenados[1:]):
            self.capas.pop(idx)

        self.indice_activo = min_idx

    def invalidate_cache(self):
        self._cached_pixmap = None
        self._cached_pixmap_img_id = None
        self._cached_active_stroke_base = None

    def get_qimage(self, capa_trazo_temp=None, draw_layer_preview_callback=None, selection_path=None):
        has_temp_stroke = bool(capa_trazo_temp and not capa_trazo_temp.isNull())
        has_preview_callback = bool(draw_layer_preview_callback)

        if not has_temp_stroke and not has_preview_callback:
            self._cached_active_stroke_base = None

        # Si sólo hay 1 capa visible, opacidad 1.0, sin trazo temporal ni preview, devolver directamente el buffer de esa capa
        if (len(self.capas) == 1 and self.capas[0].visible and
            getattr(self.capas[0], 'opacity', 1.0) == 1.0 and
            not has_temp_stroke and not has_preview_callback):
            return self.capas[0].image

        # Reutilizar el lienzo base compuesto si estamos en medio de un trazo activo continuo
        if has_temp_stroke and getattr(self, '_cached_active_stroke_base', None) is not None:
            imagen_final = self._cached_active_stroke_base.copy()
            painter = QPainter(imagen_final)
            if selection_path and not selection_path.isEmpty():
                painter.setClipPath(selection_path)
            alpha_trazo = float(getattr(self, 'active_stroke_alpha', 1.0))
            painter.setOpacity(alpha_trazo)
            painter.drawImage(0, 0, capa_trazo_temp)
            if has_preview_callback:
                draw_layer_preview_callback(painter)
            painter.end()
            return imagen_final

        imagen_final = QImage(self.width, self.height, QImage.Format.Format_ARGB32_Premultiplied)
        imagen_final.fill(Qt.GlobalColor.transparent)

        painter = QPainter(imagen_final)
        for i, capa in enumerate(reversed(self.capas)):
            if capa.visible:
                op = float(getattr(capa, 'opacity', 1.0))
                painter.setOpacity(op)
                painter.drawImage(0, 0, capa.image)
                idx_real = len(self.capas) - 1 - i
                if idx_real == self.indice_activo:
                    if has_temp_stroke:
                        painter.save()
                        if selection_path and not selection_path.isEmpty():
                            painter.setClipPath(selection_path)
                        alpha_trazo = float(getattr(self, 'active_stroke_alpha', 1.0))
                        painter.setOpacity(alpha_trazo)
                        painter.drawImage(0, 0, capa_trazo_temp)
                        painter.restore()
                    if has_preview_callback:
                        painter.save()
                        if selection_path and not selection_path.isEmpty():
                            painter.setClipPath(selection_path)
                        draw_layer_preview_callback(painter)
                        painter.restore()
        painter.end()

        if has_temp_stroke:
            base_img = QImage(self.width, self.height, QImage.Format.Format_ARGB32_Premultiplied)
            base_img.fill(Qt.GlobalColor.transparent)
            p_base = QPainter(base_img)
            for i, capa in enumerate(reversed(self.capas)):
                if capa.visible:
                    p_base.setOpacity(float(getattr(capa, 'opacity', 1.0)))
                    p_base.drawImage(0, 0, capa.image)
            p_base.end()
            self._cached_active_stroke_base = base_img

        return imagen_final

    def get_qpixmap(self, capa_trazo_temp=None, draw_layer_preview_callback=None, selection_path=None):
        img = self.get_qimage(capa_trazo_temp=capa_trazo_temp, draw_layer_preview_callback=draw_layer_preview_callback, selection_path=selection_path)
        has_transient = bool(capa_trazo_temp or draw_layer_preview_callback)
        if not has_transient and getattr(self, '_cached_pixmap', None) is not None and getattr(self, '_cached_pixmap_img_id', None) == id(img):
            return self._cached_pixmap

        pixmap = QPixmap.fromImage(img)
        if not has_transient:
            self._cached_pixmap = pixmap
            self._cached_pixmap_img_id = id(img)
        return pixmap

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
