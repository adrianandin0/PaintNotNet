import os
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QImage, QTransform, QPainterPath, QBrush, QCursor, QPixmap, QMouseEvent
from PyQt6.QtCore import Qt, QPoint, QRect, QPointF, QRectF

from core.layers import LayerManager
from core.history import HistoryManager
from core.selection import SelectionEngine
from tools.pencil import PencilTool
from tools.text import TextTool


class CanvasWidget(QWidget):
    def __init__(self, width=800, height=600, parent=None):
        super().__init__(parent)
        self.MARGIN = 0
        self.scale_factor = 1.0

        # Módulos principales del core
        self.layer_mgr = LayerManager(width, height)
        self._ajustar_tamano_widget(width, height)
        self.history_mgr = HistoryManager()
        self.selection_engine = SelectionEngine()

        # Instancia de la herramienta activa
        self.active_tool_obj = PencilTool()
        self.herramienta_actual = "Lápiz"

        # --- Atributos de Estado ---
        self.scale_factor = 1.0
        self.grosor_pincel = 3
        self.opacidad_pincel = 255
        self.suavizado_pincel = True
        self.forma_pincel = "Redondo"
        self.tolerancia_balde = 30
        self.config_texto = {}

        # Colores
        self._color_primario = QColor(0, 0, 0, 255)
        self._color_secundario = QColor(255, 255, 255, 255)

        self.callback_modificado = None
        self.drawing = False
        self.last_point = QPoint()
        self.cursor_pos = None
        self.setMouseTracking(True)

        # --- CAPA TEMPORAL PARA TRAZOS TRANSPARENTES PERFECTOS ---
        self.capa_trazo_temp = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)
        self.trayectoria_actual = None

    def obtener_offset_canvas(self):
        content_w = int(self.layer_mgr.width * self.scale_factor) if hasattr(self, 'layer_mgr') else 800
        content_h = int(self.layer_mgr.height * self.scale_factor) if hasattr(self, 'layer_mgr') else 600
        widget_w = self.width()
        widget_h = self.height()
        off_x = max(0, (widget_w - content_w) // 2)
        off_y = max(0, (widget_h - content_h) // 2)
        return off_x, off_y

    def _ajustar_tamano_widget(self, w=None, h=None):
        if w is None:
            w = self.layer_mgr.width if hasattr(self, 'layer_mgr') else 800
        if h is None:
            h = self.layer_mgr.height if hasattr(self, 'layer_mgr') else 600

        content_w = int(w * self.scale_factor)
        content_h = int(h * self.scale_factor)

        vw = 0
        vh = 0
        p = self.parent()
        if p:
            vw = p.width()
            vh = p.height()

        total_w = max(vw, content_w)
        total_h = max(vh, content_h)

        self.setMinimumSize(total_w, total_h)
        self.setFixedSize(total_w, total_h)

    def eventFilter(self, watched, event):
        from PyQt6.QtCore import QEvent
        if hasattr(self, 'layer_mgr') and self.layer_mgr:
            if event.type() == QEvent.Type.Resize:
                self._ajustar_tamano_widget()
        return super().eventFilter(watched, event)

    def _canvas_event(self, event):
        off_x, off_y = self.obtener_offset_canvas()
        raw = event.position() - QPointF(float(off_x), float(off_y))
        sf = self.scale_factor if self.scale_factor > 0 else 1.0
        pos_mapped = QPointF(raw.x() / sf, raw.y() / sf)
        return QMouseEvent(
            event.type(),
            pos_mapped,
            event.button(),
            event.buttons(),
            event.modifiers()
        )

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

    def set_zoom(self, scale):
        self.scale_factor = max(0.01, min(3.0, scale))
        self._ajustar_tamano_widget()
        if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'top_toolbar'):
            self.main_window.top_toolbar.sync_zoom_from_canvas(self.scale_factor)
        self.update()

    def set_active_tool(self, tool_object):
        if hasattr(self, 'active_tool_obj') and isinstance(self.active_tool_obj, TextTool):
            self.active_tool_obj.commit_text(self, self.color_primario)

        if hasattr(self, 'selection_engine') and self.selection_engine.floating_image:
            from tools.move_select_pixels import MoveSelectPixelsTool
            if not isinstance(tool_object, MoveSelectPixelsTool):
                MoveSelectPixelsTool.commit_floating_image(self)

        self.active_tool_obj = tool_object
        self.herramienta_actual = getattr(tool_object, 'name', 'Herramienta')

        from tools.blur import BlurTool
        if isinstance(tool_object, BlurTool) and hasattr(self, 'selection_engine') and self.selection_engine.has_selection():
            self.actualizar_preview_difuminado_seleccion()

        if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'top_toolbar'):
            self.main_window.top_toolbar.update_tool_states(tool_object)

        if hasattr(tool_object, 'icon_path') and tool_object.icon_path:
            self.actualizar_cursor_herramienta(tool_object.icon_path)
        else:
            self.unsetCursor()

    def actualizar_cursor_herramienta(self, icon_path):
        self.unsetCursor()

    def actualizar_config_texto(self, config):
        self.config_texto = config
        self.update()

    def keyPressEvent(self, event):
        color_activo = self.color_primario
        if hasattr(self.active_tool_obj, 'key_press'):
            if self.active_tool_obj.key_press(self, event, color_activo):
                return
        super().keyPressEvent(event)

    @property
    def ancho(self):
        return self.layer_mgr.width

    @property
    def alto(self):
        return self.layer_mgr.height

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Fondo uniforme sin recuadro ni borde delimitador exterior
        painter.fillRect(self.rect(), QColor(45, 45, 45))

        off_x, off_y = self.obtener_offset_canvas()
        painter.save()
        painter.translate(off_x, off_y)

        if self.scale_factor != 1.0:
            painter.scale(self.scale_factor, self.scale_factor)

        # Dimensiones reales del lienzo/capa
        l_width = self.layer_mgr.width
        l_height = self.layer_mgr.height

        # --- DIBUJAR FONDO CUADRICULADO DEL LIENZO ---
        tamano_cuadro = 16
        for y in range(0, l_height, tamano_cuadro):
            for x in range(0, l_width, tamano_cuadro):
                if (x // tamano_cuadro + y // tamano_cuadro) % 2 == 0:
                    color = QColor(200, 200, 200)
                else:
                    color = QColor(255, 255, 255)

                w = min(tamano_cuadro, l_width - x)
                h = min(tamano_cuadro, l_height - y)
                painter.fillRect(x, y, w, h, color)

        # Callback para dibujar la previsualización del contenido en el orden Z de la capa activa
        def _dibujar_preview_capa_activa(p_capa):
            if hasattr(self.active_tool_obj, 'draw_preview'):
                self.active_tool_obj.draw_preview(p_capa, self)

        # 1. Dibujar lienzo real (componiendo las capas de abajo hacia arriba e insertando el trazo/previsualización en la capa activa)
        sel_path = self.selection_engine.active_path if (self.selection_engine.has_selection() and not self.selection_engine.active_path.isEmpty()) else None
        pixmap = self.layer_mgr.get_qpixmap(
            capa_trazo_temp=self.capa_trazo_temp,
            draw_layer_preview_callback=_dibujar_preview_capa_activa,
            selection_path=sel_path
        )
        painter.drawPixmap(0, 0, pixmap)

        # 1b. Dibujar capa flotante si se está moviendo contenido o mostrando preview de difuminado
        if self.selection_engine.floating_image and not self.selection_engine.floating_image.isNull():
            painter.save()
            painter.setClipRect(0, 0, l_width, l_height)
            painter.drawImage(self.selection_engine.original_image_pos, self.selection_engine.floating_image)
            painter.restore()

        # 3. Tiradores y controles interactivos de herramientas (visibles en primer plano)
        if hasattr(self.active_tool_obj, 'draw_handles'):
            self.active_tool_obj.draw_handles(painter, self)

        # 4. Marco de selección activo y tiradores (VISIBLES INCLUSO FUERA DEL LIENZO)
        if self.selection_engine.has_selection():
            pen = QPen(QColor(0, 120, 215), 1, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            if not self.selection_engine.active_path.isEmpty():
                painter.drawPath(self.selection_engine.active_path)
            else:
                painter.drawRect(self.selection_engine.active_rect)

            # Dibujar los 8 tiradores de selección (visibles en el área externa)
            handles = self.selection_engine.get_handles()
            painter.setPen(QPen(QColor(0, 120, 215), 1, Qt.PenStyle.SolidLine))
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            for handle_rect in handles.values():
                painter.drawRect(handle_rect)

        # 5. Previsualización del cursor del pincel (forma, tamaño real y color)
        if hasattr(self, 'cursor_pos') and self.cursor_pos is not None:
            tool_name = getattr(self.active_tool_obj, 'nombre', '')
            if tool_name in ("Pincel", "Lápiz", "Goma de Borrar", "Línea"):
                w = max(1, getattr(self, 'grosor_pincel', getattr(self, 'ancho_pincel', 3)))
                w2 = w / 2.0
                cx, cy = self.cursor_pos.x(), self.cursor_pos.y()
                rect = QRectF(cx - w2, cy - w2, w, w)

                color_stroke = QColor(0, 0, 0, 180) if tool_name != "Goma de Borrar" else QColor(255, 255, 255, 220)
                pen_preview = QPen(color_stroke, 1, Qt.PenStyle.DashLine)
                painter.setPen(pen_preview)

                if tool_name == "Goma de Borrar":
                    painter.setBrush(QBrush(QColor(255, 255, 255, 60)))
                else:
                    col_p = self.color_primario
                    painter.setBrush(QBrush(QColor(col_p.red(), col_p.green(), col_p.blue(), 60)))

                forma = getattr(self, 'forma_pincel', 'Redondo')
                if forma == 'Cuadrado' or tool_name == 'Lápiz':
                    painter.drawRect(rect)
                else:
                    painter.drawEllipse(rect)

        # 6. DIBUJAR ESQUINAS, GUÍAS MEDIAS Y COORDENADAS DEL CURSOR (FUERA DEL LIENZO)
        pen_guias = QPen(QColor(180, 180, 180), 1.5, Qt.PenStyle.SolidLine)
        painter.setPen(pen_guias)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        gap = 3
        arm = 8
        tick = 6

        # --- ESQUINAS (CORNER BRACKETS) ---
        # Top-Left
        painter.drawLine(int(-gap - arm), int(-gap), int(-gap), int(-gap))
        painter.drawLine(int(-gap), int(-gap - arm), int(-gap), int(-gap))

        # Top-Right
        painter.drawLine(int(l_width + gap), int(-gap), int(l_width + gap + arm), int(-gap))
        painter.drawLine(int(l_width + gap), int(-gap - arm), int(l_width + gap), int(-gap))

        # Bottom-Left
        painter.drawLine(int(-gap - arm), int(l_height + gap), int(-gap), int(l_height + gap))
        painter.drawLine(int(-gap), int(l_height + gap), int(-gap), int(l_height + gap + arm))

        # Bottom-Right
        painter.drawLine(int(l_width + gap), int(l_height + gap), int(l_width + gap + arm), int(l_height + gap))
        painter.drawLine(int(l_width + gap), int(l_height + gap), int(l_width + gap), int(l_height + gap + arm))

        # --- MARCAS DE PUNTO MEDIO (MIDPOINT TICKS) ---
        mid_x = l_width // 2
        mid_y = l_height // 2

        # Superior
        painter.drawLine(mid_x, int(-gap - tick), mid_x, int(-gap))
        # Inferior
        painter.drawLine(mid_x, int(l_height + gap), mid_x, int(l_height + gap + tick))
        # Izquierda
        painter.drawLine(int(-gap - tick), mid_y, int(-gap), mid_y)
        # Derecha
        painter.drawLine(int(l_width + gap), mid_y, int(l_width + gap + tick), mid_y)

        # --- TEXTO DE COORDENADAS DEL CURSOR (ABAJO A LA DERECHA) ---
        font_coords = QFont("SansSerif", 9)
        painter.setFont(font_coords)
        painter.setPen(QColor(180, 180, 180))

        if hasattr(self, 'cursor_pos') and self.cursor_pos is not None:
            cx, cy = int(self.cursor_pos.x()), int(self.cursor_pos.y())
            if 0 <= cx <= l_width and 0 <= cy <= l_height:
                texto_pos = f"({cx}, {cy})"
            else:
                texto_pos = f"({l_width}, {l_height})"
        else:
            texto_pos = f"({l_width}, {l_height})"

        metrics = painter.fontMetrics()
        txt_width = metrics.horizontalAdvance(texto_pos)
        txt_x = l_width + gap + arm - txt_width
        txt_y = l_height + gap + arm + 14
        painter.drawText(int(txt_x), int(txt_y), texto_pos)

        painter.restore()


    # ==========================================
    # MANEJO DE MOUSE Y DESPACHO A HERRAMIENTAS
    # ==========================================
    def leaveEvent(self, event):
        self.cursor_pos = None
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        ev = self._canvas_event(event)
        self.cursor_pos = ev.position()
        from tools.placeholder import PlaceholderTool
        if isinstance(self.active_tool_obj, PlaceholderTool):
            return

        if hasattr(self.selection_engine, 'original_selection_region'):
            self.selection_engine.original_selection_region = None

        if ev.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self.drawing = True
            color_activo = self.color_primario if ev.button() == Qt.MouseButton.LeftButton else self.color_secundario

            if hasattr(self.active_tool_obj, 'mouse_press'):
                try:
                    self.active_tool_obj.mouse_press(self, ev, color_activo)
                except TypeError:
                    self.active_tool_obj.mouse_press(self, ev)
            self.update()

    def mouseMoveEvent(self, event):
        ev = self._canvas_event(event)
        self.cursor_pos = ev.position()
        if self.drawing:
            color_activo = self.color_primario if (ev.buttons() & Qt.MouseButton.LeftButton) else self.color_secundario

            if hasattr(self.active_tool_obj, 'mouse_move'):
                try:
                    self.active_tool_obj.mouse_move(self, ev, color_activo)
                except TypeError:
                    self.active_tool_obj.mouse_move(self, ev)

            if self.callback_modificado:
                self.callback_modificado()

        self.update()

    def mouseReleaseEvent(self, event):
        ev = self._canvas_event(event)
        if self.drawing:
            color_activo = self.color_primario if ev.button() == Qt.MouseButton.LeftButton else self.color_secundario

            if hasattr(self.active_tool_obj, 'mouse_release'):
                try:
                    self.active_tool_obj.mouse_release(self, ev, color_activo)
                except TypeError:
                    self.active_tool_obj.mouse_release(self, ev)

            self.drawing = False
            tool_name = getattr(self.active_tool_obj, 'name', None) or getattr(self.active_tool_obj, 'nombre', None) or getattr(self, 'herramienta_actual', 'Trazo')
            self.push_document_state(tool_name)
            self.update()


    # ==========================================
    # FUNCIONES DE MENÚS (ARCHIVO, EDITAR, IMAGEN)
    # ==========================================
    def crear_nuevo_lienzo(self, ancho, alto, es_transparente=False):
        self._ajustar_tamano_widget(ancho, alto)

        self.layer_mgr = LayerManager(ancho, alto)
        if es_transparente:
            self.layer_mgr.buffer.fill(Qt.GlobalColor.transparent)
        else:
            self.layer_mgr.buffer.fill(Qt.GlobalColor.white)

        self.capa_trazo_temp = QImage(ancho, alto, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

        self.selection_engine.clear_selection()
        self.floating_initial_canvas = None
        if hasattr(self, 'floating_sub_history'):
            self.floating_sub_history.clear()
        self.floating_sub_index = -1

        self.history_mgr.clear()
        if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'layers_panel'):
            self.main_window.layers_panel.reconstruir_lista_capas()
        self.update()

    def guardar_imagen(self, ruta):
        _, ext = os.path.splitext(ruta)
        if ext.lower() == '.pnn':
            from core.pnn_format import guardar_proyecto_pnn
            return guardar_proyecto_pnn(self, ruta)

        img_a_guardar = self.layer_mgr.get_qimage()
        if ext.lower() in ['.jpg', '.jpeg']:
            img_jpg = QImage(img_a_guardar.size(), QImage.Format.Format_RGB32)
            img_jpg.fill(Qt.GlobalColor.white)

            painter = QPainter(img_jpg)
            painter.drawImage(0, 0, img_a_guardar)
            painter.end()

            return img_jpg.save(ruta)

        return img_a_guardar.save(ruta)

    def invertir_seleccion(self):
        w, h = self.layer_mgr.width, self.layer_mgr.height
        rect_total = QRectF(0, 0, w, h)
        full_path = QPainterPath()
        full_path.addRect(rect_total)

        if self.selection_engine.has_selection():
            inverted_path = full_path.subtracted(self.selection_engine.active_path)
            self.selection_engine.set_path(inverted_path)
        else:
            self.selection_engine.set_rectangle(rect_total)

        self.marcar_modificado()
        self.update()

    def cargar_imagen(self, ruta):
        _, ext = os.path.splitext(ruta)
        if ext.lower() == '.pnn':
            from core.pnn_format import cargar_proyecto_pnn
            res = cargar_proyecto_pnn(self, ruta)
            if res and hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'layers_panel'):
                self.main_window.layers_panel.reconstruir_lista_capas()
            return res

        img_temp = QImage(ruta)
        if img_temp.isNull(): return False

        img_format = img_temp.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
        w, h = img_format.width(), img_format.height()

        self._ajustar_tamano_widget(w, h)

        self.layer_mgr = LayerManager(w, h)
        self.layer_mgr.buffer = img_format.copy()

        self.capa_trazo_temp = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

        self.selection_engine.clear_selection()
        self.floating_initial_canvas = None
        if hasattr(self, 'floating_sub_history'):
            self.floating_sub_history.clear()
        self.floating_sub_index = -1

        self.history_mgr.clear()

        if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'layers_panel'):
            self.main_window.layers_panel.reconstruir_lista_capas()

        self.update()
        return True

    def borrar_todo(self):
        self.layer_mgr.get_qimage().fill(Qt.GlobalColor.transparent)
        self.update()

    def redimensionar_lienzo(self, nuevo_ancho, nuevo_alto, anchor="top-left"):
        """Redimensiona el lienzo expandiendo con fondo transparente en todas las capas y registrando en el historial."""
        old_w = self.layer_mgr.width
        old_h = self.layer_mgr.height

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

        # Redimensionar cada capa manteniendo su contenido intacto y rellenando lo nuevo con transparente
        for capa in self.layer_mgr.capas:
            new_img = QImage(nuevo_ancho, nuevo_alto, QImage.Format.Format_ARGB32_Premultiplied)
            new_img.fill(Qt.GlobalColor.transparent)

            painter = QPainter(new_img)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.drawImage(dest_x, dest_y, capa.image)
            painter.end()

            capa.image = new_img

        self.layer_mgr.width = nuevo_ancho
        self.layer_mgr.height = nuevo_alto
        self._ajustar_tamano_widget(nuevo_ancho, nuevo_alto)

        # Reajustar la capa temporal de trazos
        self.capa_trazo_temp = QImage(nuevo_ancho, nuevo_alto, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

        # Registrar el cambio en el historial
        self.push_document_state("Tamaño del lienzo")
        self.update()

    def escalar_imagen(self, nuevo_ancho, nuevo_alto):
        """Escala proporcional/suavemente el contenido de todas las capas al nuevo tamaño y lo registra en el historial."""
        for capa in self.layer_mgr.capas:
            scaled = capa.image.scaled(
                nuevo_ancho, nuevo_alto,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            capa.image = scaled

        self.layer_mgr.width = nuevo_ancho
        self.layer_mgr.height = nuevo_alto
        self._ajustar_tamano_widget(nuevo_ancho, nuevo_alto)

        self.capa_trazo_temp = QImage(nuevo_ancho, nuevo_alto, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

        # Registrar el cambio en el historial
        self.push_document_state("Tamaño de la imagen")
        self.update()

    def actualizar_historial_gui(self):
        if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'history_panel'):
            self.main_window.history_panel.actualizar_historial()

    def push_floating_sub_state(self, label):
        if not hasattr(self, 'floating_sub_history') or self.floating_sub_history is None:
            self.floating_sub_history = []

        engine = self.selection_engine
        if not engine.floating_image or engine.floating_image.isNull():
            return

        snapshot = {
            'floating_image': engine.floating_image.copy(),
            'unscaled_floating_image': engine.unscaled_floating_image.copy() if engine.unscaled_floating_image else engine.floating_image.copy(),
            'active_rect': QRectF(engine.active_rect),
            'active_path': QPainterPath(engine.active_path),
            'rotation_angle': float(engine.rotation_angle),
            'original_image_pos': QPointF(engine.original_image_pos),
            'label': label
        }

        if hasattr(self, 'floating_sub_index') and self.floating_sub_index < len(self.floating_sub_history) - 1:
            self.floating_sub_history = self.floating_sub_history[:self.floating_sub_index + 1]

        self.floating_sub_history.append(snapshot)
        self.floating_sub_index = len(self.floating_sub_history) - 1
        self.actualizar_historial_gui()
        self.marcar_modificado(True)

    def restaurar_sub_estado_flotante(self, snapshot):
        engine = self.selection_engine
        engine.floating_image = snapshot['floating_image'].copy()
        engine.unscaled_floating_image = snapshot['unscaled_floating_image'].copy()
        engine.active_rect = QRectF(snapshot['active_rect'])
        engine.active_path = QPainterPath(snapshot['active_path'])
        engine.rotation_angle = float(snapshot['rotation_angle'])
    def empaquetar_paquete_flotante(self):
        if not hasattr(self, 'floating_initial_canvas') or self.floating_initial_canvas is None:
            return None
        sub_hist = getattr(self, 'floating_sub_history', [])
        sub_idx = getattr(self, 'floating_sub_index', 0)
        return {
            'initial_canvas': self.floating_initial_canvas.copy(),
            'sub_history': [
                {
                    'floating_image': snap['floating_image'].copy(),
                    'unscaled_floating_image': snap['unscaled_floating_image'].copy(),
                    'active_rect': QRectF(snap['active_rect']),
                    'active_path': QPainterPath(snap['active_path']),
                    'rotation_angle': float(snap['rotation_angle']),
                    'original_image_pos': QPointF(snap['original_image_pos']),
                    'label': snap['label']
                } for snap in sub_hist
            ],
            'sub_index': sub_idx
        }

    def restaurar_paquete_flotante(self, pkg):
        self.floating_initial_canvas = pkg['initial_canvas'].copy()
        self.floating_sub_history = [
            {
                'floating_image': snap['floating_image'].copy(),
                'unscaled_floating_image': snap['unscaled_floating_image'].copy(),
                'active_rect': QRectF(snap['active_rect']),
                'active_path': QPainterPath(snap['active_path']),
                'rotation_angle': float(snap['rotation_angle']),
                'original_image_pos': QPointF(snap['original_image_pos']),
                'label': snap['label']
            } for snap in pkg['sub_history']
        ]
        self.floating_sub_index = pkg['sub_index']
        self.restaurar_sub_estado_flotante(self.floating_sub_history[self.floating_sub_index])
        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.activar_herramienta_mover()

    def asegurar_imagen_flotante(self):
        engine = self.selection_engine
        if not engine.has_selection():
            return False

        if engine.floating_image is None or engine.floating_image.isNull():
            rect = engine.active_rect.toRect().intersected(QRect(0, 0, self.layer_mgr.width, self.layer_mgr.height))
            if rect.width() > 0 and rect.height() > 0:
                buffer = self.layer_mgr.buffer

                if not hasattr(self, 'floating_initial_canvas') or self.floating_initial_canvas is None:
                    self.floating_initial_canvas = buffer.copy()

                engine.floating_image = buffer.copy(rect)
                engine.unscaled_floating_image = engine.floating_image.copy()
                engine.original_image_pos = QPointF(rect.topLeft())

                self.floating_sub_history = []
                self.floating_sub_index = -1
                self.push_floating_sub_state("Selección")

                painter = QPainter(buffer)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                if not engine.active_path.isEmpty():
                    painter.setClipPath(engine.active_path)
                painter.fillRect(rect, Qt.GlobalColor.transparent)
                painter.end()

        return bool(engine.floating_image and not engine.floating_image.isNull())

    def voltear_contenido(self, horizontal=True):
        if self.asegurar_imagen_flotante():
            mirrored_fl = self.selection_engine.floating_image.mirrored(horizontal, not horizontal)
            self.selection_engine.floating_image = mirrored_fl
            if self.selection_engine.unscaled_floating_image and not self.selection_engine.unscaled_floating_image.isNull():
                self.selection_engine.unscaled_floating_image = self.selection_engine.unscaled_floating_image.mirrored(horizontal, not horizontal)
            self.push_floating_sub_state("Voltear Horizontal" if horizontal else "Voltear Vertical")
            self.update()
            return

        self.push_document_state("Voltear Horizontal" if horizontal else "Voltear Vertical")
        old_buffer = self.layer_mgr.buffer.copy()
        mirrored = old_buffer.mirrored(horizontal, not horizontal)
        self.layer_mgr.buffer = mirrored
        self.actualizar_historial_gui()
        self.update()

    def rotar_contenido(self, grados):
        if self.asegurar_imagen_flotante():
            self.selection_engine.rotate_floating_image(grados)
            self.push_floating_sub_state(f"Rotar {grados}°")
            self.update()
            return

        self.push_document_state(f"Rotar {grados}°")
        old_qimg = self.layer_mgr.get_qimage()
        t = QTransform().rotate(grados)
        rotated = old_qimg.transformed(t, Qt.TransformationMode.SmoothTransformation)

        nuevo_ancho = rotated.width()
        nuevo_alto = rotated.height()
        self._ajustar_tamano_widget(nuevo_ancho, nuevo_alto)

        self.layer_mgr = LayerManager(nuevo_ancho, nuevo_alto)
        self.layer_mgr.buffer = rotated

        self.capa_trazo_temp = QImage(nuevo_ancho, nuevo_alto, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

        self.actualizar_historial_gui()
        self.update()

    # --- HISTORIAL Y CAPAS MULTIPLE ---
    def obtener_snapshot_documento(self):
        """Genera una captura completa e independiente del estado de todas las capas del documento."""
        capas_copy = []
        for c in self.layer_mgr.capas:
            capas_copy.append({
                'name': c.name,
                'visible': c.visible,
                'image': c.image.copy()
            })
        return {
            'width': self.layer_mgr.width,
            'height': self.layer_mgr.height,
            'layers': capas_copy,
            'active_index': self.layer_mgr.indice_activo,
            'floating_pkg': self.empaquetar_paquete_flotante() if (self.selection_engine.floating_image and not self.selection_engine.floating_image.isNull()) else None
        }

    def marcar_modificado(self, val=True):
        self.lienzo_modificado = val
        if hasattr(self, 'callback_modificado') and callable(self.callback_modificado):
            self.callback_modificado()
        elif hasattr(self, 'main_window') and self.main_window:
            self.main_window.actualizar_titulo_ventana()

    def push_document_state(self, action_name="Acción"):
        """Guarda un estado completo del documento en el historial."""
        snap = self.obtener_snapshot_documento()
        self.history_mgr.push_state(snap, action_name=action_name)
        self.actualizar_historial_gui()
        if action_name != "Lienzo inicial":
            self.marcar_modificado(True)

    def restaurar_snapshot_documento(self, snap):
        """Restaura completamente todas las capas, dimensiones del lienzo y selección del documento a partir de un snapshot."""
        if not snap:
            return

        if isinstance(snap, QImage):
            self.layer_mgr.buffer = snap.copy()
            self.update()
            return

        if isinstance(snap, tuple) and len(snap) == 2 and isinstance(snap[0], QImage):
            base_canvas, pkg = snap
            self.layer_mgr.buffer = base_canvas.copy()
            self.restaurar_paquete_flotante(pkg)
            self.update()
            return

        if isinstance(snap, dict) and 'layers' in snap:
            from core.layers import Layer

            snap_w = snap.get('width', self.layer_mgr.width)
            snap_h = snap.get('height', self.layer_mgr.height)

            if snap_w != self.layer_mgr.width or snap_h != self.layer_mgr.height:
                self.layer_mgr.width = snap_w
                self.layer_mgr.height = snap_h
                self._ajustar_tamano_widget(snap_w, snap_h)
                self.capa_trazo_temp = QImage(snap_w, snap_h, QImage.Format.Format_ARGB32_Premultiplied)
                self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

            nuevas_capas = []
            for l_info in snap['layers']:
                capa = Layer(l_info['name'], snap_w, snap_h, transparent=True)
                capa.visible = l_info.get('visible', True)
                capa.image = l_info['image'].copy()
                nuevas_capas.append(capa)

            self.layer_mgr.capas = nuevas_capas
            idx = max(0, min(snap.get('active_index', 0), len(self.layer_mgr.capas) - 1))
            self.layer_mgr.indice_activo = idx

            floating_pkg = snap.get('floating_pkg')
            if floating_pkg:
                self.restaurar_paquete_flotante(floating_pkg)
            else:
                if self.selection_engine.floating_image:
                    self.selection_engine.floating_image = None
                    self.selection_engine.unscaled_floating_image = None
                    self.floating_sub_history = []
                    self.floating_sub_index = -1

            if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'layers_panel'):
                self.main_window.layers_panel.reconstruir_lista_capas()
            self.actualizar_historial_gui()
            self.update()

    def jump_to_history_index(self, index):
        snap = self.history_mgr.jump_to_index(index)
        if snap is not None:
            self.restaurar_snapshot_documento(snap)

    def deshacer(self): self.undo()
    def rehacer(self): self.redo()

    def undo(self):
        if self.selection_engine.floating_image and hasattr(self, 'floating_sub_history') and self.floating_sub_history:
            if hasattr(self, 'floating_sub_index') and self.floating_sub_index > 0:
                self.floating_sub_index -= 1
                self.restaurar_sub_estado_flotante(self.floating_sub_history[self.floating_sub_index])
                self.actualizar_historial_gui()
                self.update()
                return

        prev_state = self.history_mgr.undo()
        if prev_state is not None:
            self.restaurar_snapshot_documento(prev_state)

    def redo(self):
        if self.selection_engine.floating_image and hasattr(self, 'floating_sub_history') and self.floating_sub_history:
            if hasattr(self, 'floating_sub_index') and self.floating_sub_index < len(self.floating_sub_history) - 1:
                self.floating_sub_index += 1
                self.restaurar_sub_estado_flotante(self.floating_sub_history[self.floating_sub_index])
                self.actualizar_historial_gui()
                self.update()
                return

        next_state = self.history_mgr.redo()
        if next_state is not None:
            self.restaurar_snapshot_documento(next_state)

    def cancelar_o_deseleccionar(self):
        engine = self.selection_engine
        if engine.floating_image and not engine.floating_image.isNull():
            pkg = None
            if hasattr(self, 'floating_initial_canvas') and self.floating_initial_canvas:
                pkg = {
                    'initial_canvas': self.floating_initial_canvas.copy(),
                    'sub_history': [
                        {
                            'floating_image': snap['floating_image'].copy(),
                            'unscaled_floating_image': snap['unscaled_floating_image'].copy(),
                            'active_rect': QRectF(snap['active_rect']),
                            'active_path': QPainterPath(snap['active_path']),
                            'rotation_angle': float(snap['rotation_angle']),
                            'original_image_pos': QPointF(snap['original_image_pos']),
                            'label': snap['label']
                        } for snap in getattr(self, 'floating_sub_history', [])
                    ],
                    'sub_index': getattr(self, 'floating_sub_index', 0)
                }
                base_canvas = self.floating_initial_canvas.copy()
            else:
                base_canvas = self.layer_mgr.buffer.copy()

            from tools.move_select_pixels import MoveSelectPixelsTool
            MoveSelectPixelsTool.commit_floating_image(self)

            if pkg:
                self.history_mgr.push_state((base_canvas, pkg), "Mover Contenido")
            else:
                self.history_mgr.push_state(self.layer_mgr.buffer.copy(), "Mover Contenido")

            self.floating_initial_canvas = None
            if hasattr(self, 'floating_sub_history'):
                self.floating_sub_history.clear()
            self.floating_sub_index = -1

        if engine.has_selection():
            engine.clear_selection()
            self.actualizar_historial_gui()
            self.update()

    def mouseReleaseEvent(self, event):
        ev = self._canvas_event(event)
        if self.drawing:
            color_activo = self.color_primario if ev.button() == Qt.MouseButton.LeftButton else self.color_secundario

            if hasattr(self.active_tool_obj, 'mouse_release'):
                try:
                    self.active_tool_obj.mouse_release(self, ev, color_activo)
                except TypeError:
                    self.active_tool_obj.mouse_release(self, ev)

            self.drawing = False
            from tools.bucket import BucketTool
            from tools.eyedropper import EyedropperTool
            from tools.zoom import ZoomTool
            from tools.placeholder import PlaceholderTool

            if not isinstance(self.active_tool_obj, (BucketTool, EyedropperTool, ZoomTool, PlaceholderTool)):
                tool_name = getattr(self.active_tool_obj, 'name', None) or getattr(self.active_tool_obj, 'nombre', None) or getattr(self, 'herramienta_actual', 'Trazo')
                self.push_document_state(tool_name)

            self.update()


    # ==========================================
    # FUNCIONES DE MENÚS (ARCHIVO, EDITAR, IMAGEN)
    # ==========================================
    def crear_nuevo_lienzo(self, ancho, alto, es_transparente=False):
        self._ajustar_tamano_widget(ancho, alto)

        self.layer_mgr = LayerManager(ancho, alto)
        if es_transparente:
            self.layer_mgr.buffer.fill(Qt.GlobalColor.transparent)
        else:
            self.layer_mgr.buffer.fill(Qt.GlobalColor.white)

        self.capa_trazo_temp = QImage(ancho, alto, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)
        self.history_mgr.clear()

        self.push_document_state("Lienzo inicial")
        self.update()

    def seleccionar_todo(self):
        from tools.move_select_pixels import MoveSelectPixelsTool
        MoveSelectPixelsTool.commit_floating_image(self)
        rect = QRect(0, 0, self.layer_mgr.width, self.layer_mgr.height)
        self.selection_engine.set_rectangle(rect)
        self.update()

    def copiar_seleccion(self):
        from PyQt6.QtWidgets import QApplication
        if self.selection_engine.floating_image and not self.selection_engine.floating_image.isNull():
            QApplication.clipboard().setImage(self.selection_engine.floating_image.copy())
        elif self.selection_engine.has_selection():
            rect = self.selection_engine.active_rect.toRect().intersected(
                QRect(0, 0, self.layer_mgr.width, self.layer_mgr.height)
            )
            if rect.width() > 0 and rect.height() > 0:
                extracted = QImage(rect.width(), rect.height(), QImage.Format.Format_ARGB32_Premultiplied)
                extracted.fill(Qt.GlobalColor.transparent)

                p = QPainter(extracted)
                if not self.selection_engine.active_path.isEmpty():
                    path_shifted = self.selection_engine.active_path.translated(-rect.x(), -rect.y())
                    p.setClipPath(path_shifted)
                p.drawImage(0, 0, self.layer_mgr.buffer, rect.x(), rect.y(), rect.width(), rect.height())
                p.end()

                QApplication.clipboard().setImage(extracted)
        else:
            QApplication.clipboard().setImage(self.layer_mgr.buffer.copy())

    def cortar_seleccion(self):
        if self.selection_engine.has_selection():
            self.push_document_state("Cortar")
            self.copiar_seleccion()
            if self.selection_engine.floating_image:
                self.selection_engine.floating_image = None
                self.selection_engine.unscaled_floating_image = None
            else:
                rect = self.selection_engine.active_rect.toRect()
                capa_activa = self.layer_mgr.capas[self.layer_mgr.indice_activo]
                painter = QPainter(capa_activa.image)
                if not self.selection_engine.active_path.isEmpty():
                    painter.setClipPath(self.selection_engine.active_path)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                painter.fillRect(rect, Qt.GlobalColor.transparent)
                painter.end()
            self.update()

    def borrar_seleccion(self):
        if self.selection_engine.has_selection():
            self.push_document_state("Borrar Selección")
            if self.selection_engine.floating_image:
                self.selection_engine.floating_image = None
                self.selection_engine.unscaled_floating_image = None
            else:
                rect = self.selection_engine.active_rect.toRect()
                capa_activa = self.layer_mgr.capas[self.layer_mgr.indice_activo]
                painter = QPainter(capa_activa.image)
                if not self.selection_engine.active_path.isEmpty():
                    painter.setClipPath(self.selection_engine.active_path)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                painter.fillRect(rect, Qt.GlobalColor.transparent)
                painter.end()
            self.update()

    def aplicar_clip_seleccion(self, painter):
        if hasattr(self, 'selection_engine') and self.selection_engine.has_selection() and not self.selection_engine.active_path.isEmpty():
            painter.setClipPath(self.selection_engine.active_path)

    def actualizar_preview_difuminado_seleccion(self, modo=None, val=None):
        if not hasattr(self, 'selection_engine') or not self.selection_engine.has_selection() or self.selection_engine.active_path.isEmpty():
            return

        if modo is None or val is None:
            if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'top_toolbar'):
                tb = self.main_window.top_toolbar
                modo = tb.combo_blur_modo.currentData() or "Pixelado"
                val = tb.slider_blur.value()
            else:
                modo = "Pixelado"
                val = 10

        if val is None or val <= 0:
            self.selection_engine.floating_image = None
            self.update()
            return

        import math
        import cv2
        import numpy as np

        rect = self.selection_engine.active_path.boundingRect()
        rx = max(0, int(math.floor(rect.x())))
        ry = max(0, int(math.floor(rect.y())))
        rw = max(1, int(math.ceil(rect.right())) - rx)
        rh = max(1, int(math.ceil(rect.bottom())) - ry)

        w, h = self.layer_mgr.width, self.layer_mgr.height
        rw = min(w - rx, rw)
        rh = min(h - ry, rh)

        if rw <= 0 or rh <= 0:
            return

        # Para capturar los píxeles limpios originales del lienzo sin el preview difuminado actual
        temp_float = self.selection_engine.floating_image
        self.selection_engine.floating_image = None
        comp_image = self.layer_mgr.get_qimage()
        self.selection_engine.floating_image = temp_float

        base_region = comp_image.copy(rx, ry, rw, rh)
        if base_region.isNull():
            self.selection_engine.floating_image = None
            self.update()
            return

        sub_img = base_region.convertToFormat(QImage.Format.Format_ARGB32)
        ptr = sub_img.bits()
        ptr.setsize(rh * sub_img.bytesPerLine())
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((rh, sub_img.bytesPerLine() // 4, 4))[:, :rw, :].copy()

        rgb = arr[:, :, :3]
        alpha = arr[:, :, 3]

        mask_transparent = (alpha == 0).astype(np.uint8) * 255
        if np.any(mask_transparent) and np.any(alpha > 0):
            rgb_filled = cv2.inpaint(rgb, mask_transparent, 3, cv2.INPAINT_TELEA)
        else:
            rgb_filled = rgb

        if modo == "Pixelado":
            factor = max(2, int((val / 100.0) * 35))
            sw = max(1, rw // factor)
            sh = max(1, rh // factor)

            small_rgb = cv2.resize(rgb_filled, (sw, sh), interpolation=cv2.INTER_NEAREST)
            small_alpha = cv2.resize((alpha > 0).astype(np.uint8) * 255, (sw, sh), interpolation=cv2.INTER_AREA)
            small_alpha = np.where(small_alpha > 0, 255, 0).astype(np.uint8)

            blurred_rgb = cv2.resize(small_rgb, (rw, rh), interpolation=cv2.INTER_NEAREST)
            blurred_alpha = cv2.resize(small_alpha, (rw, rh), interpolation=cv2.INTER_NEAREST)

            blurred_arr = np.dstack((blurred_rgb, blurred_alpha))
        else:
            ksize = max(3, (int((val / 100.0) * 45) // 2) * 2 + 1)

            blurred_rgb = cv2.GaussianBlur(rgb_filled, (ksize, ksize), 0, borderType=cv2.BORDER_REPLICATE)
            blurred_alpha = cv2.GaussianBlur(alpha, (ksize, ksize), 0, borderType=cv2.BORDER_REPLICATE)

            blurred_alpha = np.where(blurred_alpha > 0, 255, 0).astype(np.uint8)
            blurred_arr = np.dstack((blurred_rgb, blurred_alpha))

        blurred_img = QImage(blurred_arr.data, rw, rh, rw * 4, QImage.Format.Format_ARGB32).copy()

        masked_img = QImage(rw, rh, QImage.Format.Format_ARGB32_Premultiplied)
        masked_img.fill(Qt.GlobalColor.transparent)

        painter = QPainter(masked_img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        path_local = QPainterPath(self.selection_engine.active_path)
        path_local.translate(-rx, -ry)
        painter.setClipPath(path_local)
        painter.drawImage(0, 0, blurred_img)
        painter.end()

        self.selection_engine.floating_image = masked_img
        self.selection_engine.original_image_pos = QPointF(rx, ry)
        self.update()

    def aplicar_difuminado(self, modo="Pixelado", val=10):
        if val <= 0 or not hasattr(self, 'layer_mgr') or not self.layer_mgr.capas:
            return
        import cv2
        import numpy as np

        capa = self.layer_mgr.capas[self.layer_mgr.indice_activo]
        img = capa.image
        w, h = img.width(), img.height()
        if w <= 0 or h <= 0:
            return

        self.push_document_state("Difuminar")

        img_argb = img.convertToFormat(QImage.Format.Format_ARGB32)
        ptr = img_argb.bits()
        ptr.setsize(h * img_argb.bytesPerLine())
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((h, img_argb.bytesPerLine() // 4, 4))[:, :w, :].copy()

        if modo == "Pixelado":
            factor = max(2, int((val / 100.0) * 35))
            small_w = max(1, w // factor)
            small_h = max(1, h // factor)
            small = cv2.resize(arr, (small_w, small_h), interpolation=cv2.INTER_NEAREST)
            blurred_arr = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
        else:
            ksize = max(3, (int((val / 100.0) * 45) // 2) * 2 + 1)
            blurred_arr = cv2.GaussianBlur(arr, (ksize, ksize), 0)

        result_img = QImage(blurred_arr.data, w, h, w * 4, QImage.Format.Format_ARGB32).copy()

        painter = QPainter(capa.image)
        if self.selection_engine.has_selection() and not self.selection_engine.active_path.isEmpty():
            painter.setClipPath(self.selection_engine.active_path)
        painter.drawImage(0, 0, result_img)
        painter.end()

        self.update()

    def borrar_todo(self):
        self.push_document_state("Borrar Todo")
        from tools.move_select_pixels import MoveSelectPixelsTool
        MoveSelectPixelsTool.commit_floating_image(self)
        self.selection_engine.clear_selection()
        self.layer_mgr.buffer.fill(Qt.GlobalColor.transparent)
        self.update()

    def pegar_portapapeles(self):
        from PyQt6.QtWidgets import QApplication
        img = QApplication.clipboard().image()
        if not img.isNull():
            from tools.move_select_pixels import MoveSelectPixelsTool
            MoveSelectPixelsTool.commit_floating_image(self)

            self.push_document_state("Pegar")
            img_format = img.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
            self.selection_engine.unscaled_floating_image = img_format.copy()
            self.selection_engine.floating_image = img_format.copy()

            img_w = img_format.width()
            img_h = img_format.height()
            pos_x = (self.layer_mgr.width - img_w) / 2.0 if img_w > self.layer_mgr.width else 0.0
            pos_y = (self.layer_mgr.height - img_h) / 2.0 if img_h > self.layer_mgr.height else 0.0

            self.selection_engine.original_image_pos = QPointF(pos_x, pos_y)
            self.selection_engine.set_rectangle(QRectF(pos_x, pos_y, img_w, img_h))
            if hasattr(self, 'main_window') and self.main_window:
                self.main_window.activar_herramienta_mover()
            self.update()

    def insertar_imagen(self, ruta):
        if not ruta or not os.path.exists(ruta):
            return False
        img = QImage(ruta)
        if img.isNull():
            return False

        from tools.move_select_pixels import MoveSelectPixelsTool
        MoveSelectPixelsTool.commit_floating_image(self)

        self.push_document_state("Insertar Imagen")
        img_format = img.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
        self.selection_engine.unscaled_floating_image = img_format.copy()
        self.selection_engine.floating_image = img_format.copy()

        img_w = img_format.width()
        img_h = img_format.height()
        pos_x = (self.layer_mgr.width - img_w) / 2.0 if img_w > self.layer_mgr.width else 0.0
        pos_y = (self.layer_mgr.height - img_h) / 2.0 if img_h > self.layer_mgr.height else 0.0

        self.selection_engine.original_image_pos = QPointF(pos_x, pos_y)
        self.selection_engine.set_rectangle(QRectF(pos_x, pos_y, img_w, img_h))
        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.activar_herramienta_mover()
        self.update()
        return True

    def escalar_seleccion(self, nuevo_ancho, nuevo_alto):
        """Escala la selección activa o elemento flotante al nuevo tamaño y lo centra en el lienzo."""
        engine = self.selection_engine
        if not engine.has_selection():
            return

        # 1. Si no hay capa flotante extraída aún (ej. selección realizada sobre la capa), extraer la capa flotante primero
        if engine.floating_image is None or engine.floating_image.isNull():
            rect = engine.active_rect.toRect().intersected(
                QRect(0, 0, self.layer_mgr.width, self.layer_mgr.height)
            )
            if rect.width() > 0 and rect.height() > 0:
                buffer = self.layer_mgr.buffer
                self.floating_initial_canvas = buffer.copy()

                engine.floating_image = buffer.copy(rect)
                engine.unscaled_floating_image = engine.floating_image.copy()
                engine.original_image_pos = QPointF(rect.topLeft())

                painter = QPainter(buffer)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                if not engine.active_path.isEmpty():
                    painter.setClipPath(engine.active_path)
                painter.fillRect(rect, Qt.GlobalColor.transparent)
                painter.end()

        # 2. Escalar la imagen flotante al nuevo tamaño
        if engine.unscaled_floating_image and not engine.unscaled_floating_image.isNull():
            scaled = engine.unscaled_floating_image.scaled(
                nuevo_ancho, nuevo_alto,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            engine.floating_image = scaled

        # 3. Centrar la selección en el lienzo (sea cual sea el tamaño del lienzo o de la selección)
        cx = self.layer_mgr.width / 2.0
        cy = self.layer_mgr.height / 2.0
        new_left = cx - nuevo_ancho / 2.0
        new_top = cy - nuevo_alto / 2.0

        engine.original_image_pos = QPointF(new_left, new_top)
        engine.set_rectangle(QRectF(new_left, new_top, nuevo_ancho, nuevo_alto))

        # 4. Cambiar herramienta activa a "Mover Contenido"
        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.activar_herramienta_mover()

        # 5. Guardar estado en el historial y actualizar
        self.push_floating_sub_state("Tamaño de la Selección")
        self.update()
        return True
