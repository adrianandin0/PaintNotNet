import os
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QImage, QTransform, QPainterPath
from PyQt6.QtCore import Qt, QPoint, QRect, QPointF

from core.layers import LayerManager
from core.history import HistoryManager
from core.selection import SelectionEngine
from tools.pencil import PencilTool
from tools.text import TextTool


class CanvasWidget(QWidget):
    def __init__(self, width=800, height=600, parent=None):
        super().__init__(parent)
        self.setMinimumSize(width, height)
        self.resize(width, height)

        # Módulos principales del core
        self.layer_mgr = LayerManager(width, height)
        self.history_mgr = HistoryManager()
        self.selection_engine = SelectionEngine()

        # Instancia de la herramienta activa
        self.active_tool_obj = PencilTool()
        self.herramienta_actual = "Lápiz"

        # --- Atributos de Estado ---
        self.grosor_pincel = 3
        self.opacidad_pincel = 255
        self.suavizado_pincel = True
        self.forma_pincel = "Redondo"
        self.tolerancia_balde = 30
        self.config_texto = {}

        # Colores (variables privadas con setters/getters para tiempo real)
        self._color_primario = QColor(0, 0, 0, 255)
        self._color_secundario = QColor(255, 255, 255, 255)

        self.callback_modificado = None
        self.drawing = False
        self.last_point = QPoint()

        # --- CAPA TEMPORAL PARA TRAZOS TRANSPARENTES PERFECTOS ---
        self.capa_trazo_temp = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)
        self.trayectoria_actual = None

    @property
    def color_primario(self):
        return self._color_primario

    @color_primario.setter
    def color_primario(self, color):
        self._color_primario = color
        self.update()

    @property
    def color_secundario(self):
        return self._color_secundario

    @color_secundario.setter
    def color_secundario(self, color):
        self._color_secundario = color
        self.update()

    def __getattr__(self, name):
        def dummy_func(*args, **kwargs):
            pass
        return dummy_func

    def set_active_tool(self, tool_object):
        if hasattr(self, 'active_tool_obj') and isinstance(self.active_tool_obj, TextTool):
            self.active_tool_obj.commit_text(self, self.color_primario)

        self.active_tool_obj = tool_object
        self.herramienta_actual = getattr(tool_object, 'name', 'Herramienta')

    def actualizar_config_texto(self, config):
        self.config_texto = config
        self.update()

    def keyPressEvent(self, event):
        color_activo = self.color_primario
        if hasattr(self.active_tool_obj, 'key_press'):
            if self.active_tool_obj.key_press(self, event, color_activo):
                return
        super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)

        # Dimensiones reales del lienzo/capa
        l_width = self.layer_mgr.width
        l_height = self.layer_mgr.height

        # --- DIBUJAR FONDO CUADRICULADO (TRANSPARENCIA) HASTA EL TAMAÑO REAL DEL LIENZO ---
        tamano_cuadro = 16
        for y in range(0, l_height, tamano_cuadro):
            for x in range(0, l_width, tamano_cuadro):
                if (x // tamano_cuadro + y // tamano_cuadro) % 2 == 0:
                    color = QColor(200, 200, 200)  # Gris
                else:
                    color = QColor(255, 255, 255)  # Blanco

                w = min(tamano_cuadro, l_width - x)
                h = min(tamano_cuadro, l_height - y)
                painter.fillRect(x, y, w, h, color)

        # 1. Dibujar lienzo real (encima del cuadriculado)
        pixmap = self.layer_mgr.get_qpixmap()
        painter.drawPixmap(0, 0, pixmap)

        # 2. Dibujar trazo temporal por encima (si hay uno activo)
        if not self.capa_trazo_temp.isNull():
            painter.drawImage(0, 0, self.capa_trazo_temp)

        # 3. Previsualización de Texto Flotante
        if hasattr(self.active_tool_obj, 'draw_preview'):
            self.active_tool_obj.draw_preview(painter, self)

        # 4. Marco de selección activo
        if self.selection_engine.has_selection():
            pen = QPen(Qt.GlobalColor.black, 1, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            if not self.selection_engine.active_path.isEmpty():
                painter.drawPath(self.selection_engine.active_path)
            else:
                painter.drawRect(self.selection_engine.active_rect)

    # ==========================================
    # MANEJO DE MOUSE Y DIBUJO DIRECTO
    # ==========================================
    def mousePressEvent(self, event):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self.drawing = True
            self.last_point = event.position().toPoint()
            self.history_mgr.push_state(self.layer_mgr.buffer.copy())

            color_activo = self.color_primario if event.button() == Qt.MouseButton.LeftButton else self.color_secundario
            nombre_herramienta = getattr(self.active_tool_obj, 'name', '').lower()

            if nombre_herramienta in ['lápiz', 'lapiz', 'pincel']:
                self.trayectoria_actual = QPainterPath()
                self.trayectoria_actual.moveTo(event.position())

                if self.capa_trazo_temp.size() != self.layer_mgr.buffer.size():
                    self.capa_trazo_temp = QImage(self.layer_mgr.buffer.size(), QImage.Format.Format_ARGB32_Premultiplied)
                self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

            elif nombre_herramienta not in ['goma']:
                if hasattr(self.active_tool_obj, 'mouse_press'):
                    try:
                        self.active_tool_obj.mouse_press(self, event, color_activo)
                    except TypeError:
                        self.active_tool_obj.mouse_press(self, event)
            self.update()

    def mouseMoveEvent(self, event):
        if self.drawing:
            current_point = event.position().toPoint()
            color_activo = self.color_primario if (event.buttons() & Qt.MouseButton.LeftButton) else self.color_secundario
            nombre_herramienta = getattr(self.active_tool_obj, 'name', '').lower()

            if nombre_herramienta in ['lápiz', 'lapiz', 'pincel']:
                self.trayectoria_actual.lineTo(event.position())
                self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

                painter = QPainter(self.capa_trazo_temp)
                color = QColor(color_activo)

                if self.suavizado_pincel:
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

                painter.setPen(QPen(color, self.grosor_pincel, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                painter.drawPath(self.trayectoria_actual)
                painter.end()

            elif nombre_herramienta == 'goma':
                qimg = self.layer_mgr.buffer
                painter = QPainter(qimg)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)

                if self.suavizado_pincel:
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

                painter.setPen(QPen(Qt.GlobalColor.transparent, self.grosor_pincel, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                painter.drawLine(self.last_point, current_point)
                painter.end()
            else:
                if hasattr(self.active_tool_obj, 'mouse_move') and callable(self.active_tool_obj.mouse_move):
                    try:
                        self.active_tool_obj.mouse_move(self, event, color_activo)
                    except TypeError:
                        self.active_tool_obj.mouse_move(self, event)

            self.last_point = current_point

            if self.callback_modificado:
                self.callback_modificado()

            self.update()

    def mouseReleaseEvent(self, event):
        if self.drawing:
            color_activo = self.color_primario if event.button() == Qt.MouseButton.LeftButton else self.color_secundario
            nombre_herramienta = getattr(self.active_tool_obj, 'name', '').lower()

            if nombre_herramienta in ['lápiz', 'lapiz', 'pincel']:
                qimg = self.layer_mgr.buffer
                painter = QPainter(qimg)
                painter.drawImage(0, 0, self.capa_trazo_temp)
                painter.end()

                self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)
                self.trayectoria_actual = None

            elif nombre_herramienta not in ['goma']:
                if hasattr(self.active_tool_obj, 'mouse_release'):
                    try:
                        self.active_tool_obj.mouse_release(self, event, color_activo)
                    except TypeError:
                        self.active_tool_obj.mouse_release(self, event)

            self.drawing = False
            self.update()

    # ==========================================
    # FUNCIONES DE MENÚS (ARCHIVO, EDITAR, IMAGEN)
    # ==========================================
    def crear_nuevo_lienzo(self, ancho, alto, es_transparente=False):
        self.setMinimumSize(ancho, alto)
        self.resize(ancho, alto)

        self.layer_mgr = LayerManager(ancho, alto)
        qimg = self.layer_mgr.get_qimage()

        if es_transparente:
            qimg.fill(Qt.GlobalColor.transparent)
        else:
            qimg.fill(Qt.GlobalColor.white)

        # Ajustar capa temporal
        self.capa_trazo_temp = QImage(ancho, alto, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

        self.history_mgr.clear()
        self.update()

    def guardar_imagen(self, ruta):
        img_a_guardar = self.layer_mgr.get_qimage()
        _, ext = os.path.splitext(ruta)
        if ext.lower() in ['.jpg', '.jpeg']:
            img_jpg = QImage(img_a_guardar.size(), QImage.Format.Format_RGB32)
            img_jpg.fill(Qt.GlobalColor.white)

            painter = QPainter(img_jpg)
            painter.drawImage(0, 0, img_a_guardar)
            painter.end()

            return img_jpg.save(ruta)

        return img_a_guardar.save(ruta)

    def cargar_imagen(self, ruta):
        img_temp = QImage(ruta)
        if img_temp.isNull(): return False

        img_format = img_temp.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
        w, h = img_format.width(), img_format.height()

        self.setMinimumSize(w, h)
        self.resize(w, h)

        self.layer_mgr = LayerManager(w, h)
        qimg = self.layer_mgr.get_qimage()

        painter = QPainter(qimg)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.drawImage(0, 0, img_format)
        painter.end()

        self.capa_trazo_temp = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

        self.history_mgr.clear()
        self.update()
        return True

    def borrar_todo(self):
        self.layer_mgr.get_qimage().fill(Qt.GlobalColor.transparent)
        self.update()

    def redimensionar_lienzo(self, nuevo_ancho, nuevo_alto, anchor="top-left"):
        """Redimensiona el lienzo expandiendo con fondo transparente por defecto."""
        old_qimg = self.layer_mgr.buffer.copy()
        old_w = old_qimg.width()
        old_h = old_qimg.height()

        self.setMinimumSize(nuevo_ancho, nuevo_alto)
        self.resize(nuevo_ancho, nuevo_alto)

        # Crear nuevo gestor de capas con el nuevo tamaño
        self.layer_mgr = LayerManager(nuevo_ancho, nuevo_alto)
        new_qimg = self.layer_mgr.buffer

        # FONDO TRANSPARENTE POR DEFECTO PARA EL ESPACIO NUEVO
        new_qimg.fill(Qt.GlobalColor.transparent)

        # --- CÁLCULO DE POSICIÓN SEGÚN EL ANCLAJE ---
        dest_x = 0
        dest_y = 0

        # Eje X (Horizontal)
        if "center" in anchor or anchor in ["top-center", "bottom-center", "middle-center"]:
            dest_x = (nuevo_ancho - old_w) // 2
        elif "right" in anchor:
            dest_x = nuevo_ancho - old_w

        # Eje Y (Vertical)
        if "middle" in anchor or anchor == "center":
            dest_y = (nuevo_alto - old_h) // 2
        elif "bottom" in anchor:
            dest_y = nuevo_alto - old_h

        # Estampar la imagen previa conservando sus colores y transparencias
        painter = QPainter(new_qimg)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.drawImage(dest_x, dest_y, old_qimg)
        painter.end()

        # Reajustar la capa temporal de trazos
        self.capa_trazo_temp = QImage(nuevo_ancho, nuevo_alto, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

        self.update()

    def escalar_imagen(self, nuevo_ancho, nuevo_alto):
        old_qimg = self.layer_mgr.get_qimage()
        scaled = old_qimg.scaled(nuevo_ancho, nuevo_alto, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)

        self.setMinimumSize(nuevo_ancho, nuevo_alto)
        self.resize(nuevo_ancho, nuevo_alto)

        self.layer_mgr = LayerManager(nuevo_ancho, nuevo_alto)
        new_qimg = self.layer_mgr.get_qimage()

        painter = QPainter(new_qimg)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.drawImage(0, 0, scaled)
        painter.end()

        self.capa_trazo_temp = QImage(nuevo_ancho, nuevo_alto, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

        self.update()

    def voltear_contenido(self, horizontal=True):
        old_qimg = self.layer_mgr.get_qimage()
        mirrored = old_qimg.mirrored(horizontal, not horizontal)
        painter = QPainter(self.layer_mgr.get_qimage())
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.drawImage(0, 0, mirrored)
        painter.end()
        self.update()

    def rotar_contenido(self, grados):
        old_qimg = self.layer_mgr.get_qimage()
        t = QTransform().rotate(grados)
        rotated = old_qimg.transformed(t, Qt.TransformationMode.SmoothTransformation)

        nuevo_ancho = rotated.width()
        nuevo_alto = rotated.height()
        self.setMinimumSize(nuevo_ancho, nuevo_alto)
        self.resize(nuevo_ancho, nuevo_alto)

        self.layer_mgr = LayerManager(nuevo_ancho, nuevo_alto)
        new_qimg = self.layer_mgr.get_qimage()
        painter = QPainter(new_qimg)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.drawImage(0, 0, rotated)
        painter.end()

        self.capa_trazo_temp = QImage(nuevo_ancho, nuevo_alto, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

        self.update()

    # --- HISTORIAL Y PORTAPAPELES ---
    def deshacer(self): self.undo()
    def rehacer(self): self.redo()

    def undo(self):
        prev_state = self.history_mgr.undo(self.layer_mgr.buffer.copy())
        if prev_state is not None:
            self.layer_mgr.buffer = prev_state
            self.update()

    def redo(self):
        next_state = self.history_mgr.redo(self.layer_mgr.buffer.copy())
        if next_state is not None:
            self.layer_mgr.buffer = next_state
            self.update()

    def cancelar_o_deseleccionar(self):
        if self.selection_engine.has_selection():
            self.selection_engine.clear_selection()
            self.update()

    def seleccionar_todo(self):
        rect = QRect(0, 0, self.width(), self.height())
        self.selection_engine.set_selection(rect)
        self.update()

    def cortar_seleccion(self): pass
    def copiar_seleccion(self): pass
    def pegar_portapapeles(self): pass
    def borrar_seleccion(self): pass
    def insertar_imagen(self, ruta): pass
