import os
from PyQt6.QtWidgets import QWidget, QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QImage, QTransform, QPainterPath, QBrush, QCursor, QPixmap, QMouseEvent
from PyQt6.QtCore import Qt, QPoint, QRect, QPointF, QRectF

from core.layers import LayerManager
from core.history import HistoryManager
from core.selection import SelectionEngine
from tools.pencil import PencilTool
from tools.text import TextTool


class DialogoOpcionesInsercion(QDialog):
    """Diálogo personalizado para seleccionar cómo insertar una imagen más grande que el lienzo."""
    def __init__(self, parent=None, img_w=0, img_h=0, canvas_w=0, canvas_h=0):
        super().__init__(parent)
        from core.i18n import t
        self.setWindowTitle(t("Opciones de inserción"))
        self.setFixedWidth(390)

        self.opcion_elegida = "sin_cambios"

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        lbl_title = QLabel(t("La imagen que intentas insertar es más grande que el lienzo actual."))
        lbl_title.setWordWrap(True)
        lbl_title.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(lbl_title)

        lbl_sub = QLabel(t("¿Cómo deseas insertar la imagen?"))
        lbl_sub.setStyleSheet("font-size: 11px;")
        layout.addWidget(lbl_sub)

        layout_btns = QVBoxLayout()
        layout_btns.setSpacing(8)

        btn_ajustar_lienzo = QPushButton(t("Ajustar lienzo"))
        btn_ajustar_lienzo.setToolTip(t("Cambia el tamaño del lienzo al tamaño exacto de la imagen."))
        btn_ajustar_lienzo.setMinimumHeight(32)
        btn_ajustar_lienzo.clicked.connect(lambda: self._elegir("ajustar_lienzo"))

        btn_adaptar_imagen = QPushButton(t("Adaptar imagen"))
        btn_adaptar_imagen.setToolTip(t("Escala la imagen manteniendo proporciones para que quepa completa en el lienzo."))
        btn_adaptar_imagen.setMinimumHeight(32)
        btn_adaptar_imagen.clicked.connect(lambda: self._elegir("adaptar_imagen"))

        btn_sin_cambios = QPushButton(t("Insertar sin cambios"))
        btn_sin_cambios.setToolTip(t("Inserta la imagen con su tamaño original para que la modifiques manualmente."))
        btn_sin_cambios.setMinimumHeight(32)
        btn_sin_cambios.clicked.connect(lambda: self._elegir("sin_cambios"))

        layout_btns.addWidget(btn_ajustar_lienzo)
        layout_btns.addWidget(btn_adaptar_imagen)
        layout_btns.addWidget(btn_sin_cambios)

        layout.addLayout(layout_btns)

    def _elegir(self, opcion):
        self.opcion_elegida = opcion
        self.accept()


class CanvasWidget(QWidget):
    def __init__(self, width=800, height=600, parent=None):
        super().__init__(parent)
        self.MARGIN = 0
        self.scale_factor = 1.0

        # Módulos principales del core
        self.layer_mgr = LayerManager(width, height)
        self._ajustar_tamano_widget(width, height)
        self.history_mgr = HistoryManager(200)
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
        self.tolerancia = 50
        from tools.text import obtener_fuente_predeterminada_sistema
        self.text_config = {
            "font_family": obtener_fuente_predeterminada_sistema(),
            "font_size": 12,
            "size": 12,
            "bold": False,
            "italic": False,
            "underline": False,
            "strike": False,
            "alignment": Qt.AlignmentFlag.AlignLeft
        }
        self.config_texto = lambda: self.text_config

        # Colores
        self._color_primario = QColor(0, 0, 0, 255)
        self._color_secundario = QColor(255, 255, 255, 255)

        self.callback_modificado = None
        self.lienzo_modificado = False
        self.drawing = False
        self.last_point = QPoint()
        self.cursor_pos = None
        self.show_pixel_grid = False
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

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
        self.scale_factor = max(0.01, min(30.0, scale))
        self._ajustar_tamano_widget()
        if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'top_toolbar'):
            self.main_window.top_toolbar.sync_zoom_from_canvas(self.scale_factor)
        self.update()

    def set_active_tool(self, tool_object):
        from tools.text import TextTool
        from tools.line import LineTool
        from tools.shapes import ShapesTool
        if hasattr(self, 'active_tool_obj'):
            if isinstance(self.active_tool_obj, TextTool):
                self.active_tool_obj.commit_text(self, self.color_primario)
            elif isinstance(self.active_tool_obj, LineTool):
                self.active_tool_obj.commit_line(self)
            elif isinstance(self.active_tool_obj, ShapesTool):
                self.active_tool_obj.commit_shape(self)
        self.active_tool_obj = tool_object
        # Habilitar input method para composición de caracteres (dead keys, IME)
        enable_ime = isinstance(tool_object, TextTool)
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, enable_ime)

        if hasattr(self, 'selection_engine') and self.selection_engine.floating_image:
            from tools.move_select_pixels import MoveSelectPixelsTool
            if not isinstance(tool_object, MoveSelectPixelsTool):
                MoveSelectPixelsTool.commit_floating_image(self)

        self.herramienta_actual = getattr(tool_object, 'name', 'Herramienta')

        from tools.blur import BlurTool
        if isinstance(tool_object, BlurTool) and hasattr(self, 'selection_engine') and self.selection_engine.has_selection():
            self.actualizar_preview_difuminado_seleccion()

        if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'top_toolbar'):
            self.main_window.top_toolbar.update_tool_states(tool_object)

        self.actualizar_cursor_herramienta(tool_object)

    def obtener_cursor_custom_herramienta(self, tool_object=None):
        """Genera y devuelve el QCursor personalizado (32x32 con cruz y la insignia en escala de grises)."""
        if tool_object is None:
            tool_object = getattr(self, 'active_tool_obj', None)

        if not tool_object:
            return None

        badge_pixmap = self._obtener_icono_herramienta_gris(tool_object)
        if not badge_pixmap or badge_pixmap.isNull():
            return QCursor(Qt.CursorShape.CrossCursor)

        # Crear cursor de hardware compuesto (32x32) con la cruz fija en (6,6) y la insignia en (14,14) SIN RECUADRO
        pm = QPixmap(32, 32)
        pm.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        # 1. Puntero en cruz limpio con bordes de contraste
        painter.setPen(QPen(QColor(0, 0, 0, 220), 1))
        painter.drawLine(1, 6, 11, 6)
        painter.drawLine(6, 1, 6, 11)
        painter.setPen(QPen(QColor(255, 255, 255, 255), 1))
        painter.drawPoint(6, 6)

        # 2. Dibujar directamente la insignia de 16x16
        painter.drawPixmap(14, 14, badge_pixmap)
        painter.end()

        return QCursor(pm, 6, 6)

    def actualizar_cursor_herramienta(self, tool_object=None):
        if tool_object is None:
            tool_object = getattr(self, 'active_tool_obj', None)

        if not tool_object:
            self.unsetCursor()
            return

        cursor = self.obtener_cursor_custom_herramienta(tool_object)
        if cursor:
            self.setCursor(cursor)
        else:
            self.setCursor(Qt.CursorShape.CrossCursor)

    def actualizar_config_texto(self, config):
        self.config_texto = config
        self.update()

    def mover_seleccion_por_teclado(self, dx, dy):
        """Mueve la selección (y su contenido flotante si aplica) mediante las teclas de dirección."""
        engine = self.selection_engine
        if not engine.has_selection():
            return False

        from tools.move_select_pixels import MoveSelectPixelsTool
        # Si la herramienta activa es Mover Contenido y aún no se han levantado los píxeles, inicializarlos
        if isinstance(self.active_tool_obj, MoveSelectPixelsTool) and engine.floating_image is None:
            rect = engine.active_rect.toRect().intersected(QRect(0, 0, self.layer_mgr.width, self.layer_mgr.height))
            if rect.width() > 0 and rect.height() > 0:
                buffer = self.layer_mgr.buffer
                self.floating_initial_canvas = buffer.copy()
                engine.floating_image = buffer.copy(rect)

                if not engine.active_path.isEmpty():
                    masked = QImage(rect.size(), QImage.Format.Format_ARGB32_Premultiplied)
                    masked.fill(Qt.GlobalColor.transparent)
                    mpainter = QPainter(masked)
                    local_path = QPainterPath(engine.active_path)
                    local_path.translate(-QPointF(rect.topLeft()))
                    mpainter.setClipPath(local_path)
                    mpainter.drawImage(0, 0, engine.floating_image)
                    mpainter.end()
                    engine.floating_image = masked

                engine.unscaled_floating_image = engine.floating_image.copy()
                engine.init_raw_image(engine.floating_image)
                engine.original_image_pos = QPointF(rect.topLeft())
                engine.is_new_content = False
                self.floating_history = [engine.floating_image.copy()]

                painter = QPainter(buffer)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                if not engine.active_path.isEmpty():
                    painter.setClipPath(engine.active_path)
                painter.fillRect(rect, Qt.GlobalColor.transparent)
                painter.end()

        # Desplazar engine por (dx, dy)
        engine.translate(dx, dy)
        self._ajustar_tamano_widget()

        action_name = "Mover Contenido" if (engine.floating_image and not engine.floating_image.isNull()) else "Mover Selección"
        self.push_document_state(action_name)

        if self.callback_modificado:
            self.callback_modificado()
        self.update()
        return True

    def keyPressEvent(self, event):
        color_activo = self.color_primario
        if hasattr(self.active_tool_obj, 'key_press'):
            if self.active_tool_obj.key_press(self, event, color_activo):
                event.accept()
                return

        # Mover selección por teclado con las flechas (Up, Down, Left, Right)
        if self.selection_engine.has_selection() and event.key() in (
            Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down
        ):
            step = 10 if bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier) else 1
            dx = 0
            dy = 0
            if event.key() == Qt.Key.Key_Left:
                dx = -step
            elif event.key() == Qt.Key.Key_Right:
                dx = step
            elif event.key() == Qt.Key.Key_Up:
                dy = -step
            elif event.key() == Qt.Key.Key_Down:
                dy = step

            if self.mover_seleccion_por_teclado(dx, dy):
                event.accept()
                return

        super().keyPressEvent(event)

    def inputMethodEvent(self, event):
        """Forwarding para dead-key composition (á, é, ñ, etc.)"""
        from tools.text import TextTool
        if isinstance(self.active_tool_obj, TextTool) and self.active_tool_obj.is_editing:
            commit_str = event.commitString()
            if commit_str:
                if self.active_tool_obj._has_selection():
                    self.active_tool_obj._delete_selection()
                from tools.text import _insert_text_at
                tool = self.active_tool_obj
                tool.cursor_col = _insert_text_at(
                    tool.rich_lines[tool.cursor_line],
                    tool.cursor_col, commit_str, tool._default_fmt)
                tool._clear_sel()
                self.update()
            event.accept()
            return
        super().inputMethodEvent(event)

    @property
    def ancho(self):
        return self.layer_mgr.width

    @property
    def alto(self):
        return self.layer_mgr.height

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Fondo uniforme según el tema activo
        from core.theme import ThemeManager
        bg_col = ThemeManager().obtener_color_area_canvas()
        painter.fillRect(self.rect(), bg_col)

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
            if self.selection_engine.floating_image and not self.selection_engine.floating_image.isNull():
                p_capa.save()
                p_capa.setClipRect(0, 0, l_width, l_height)
                p_capa.drawImage(self.selection_engine.original_image_pos, self.selection_engine.floating_image)
                p_capa.restore()
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

        # 2. Dibujar cuadrícula de píxeles si está activada y el zoom es suficiente (>= 300%)
        if getattr(self, 'show_pixel_grid', False) and self.scale_factor >= 3.0:
            painter.save()
            from core.theme import ThemeManager
            tm = ThemeManager()
            res_nombre = tm.resolver_nombre_tema(tm.current_theme)
            is_dark = (res_nombre == "Oscuro")
            grid_color = QColor(255, 255, 255, 120) if is_dark else QColor(0, 0, 0, 120)
            pen_grid = QPen(grid_color, 1 / self.scale_factor, Qt.PenStyle.SolidLine)
            painter.setPen(pen_grid)
            for x in range(1, l_width):
                painter.drawLine(QPointF(float(x), 0.0), QPointF(float(x), float(l_height)))
            for y in range(1, l_height):
                painter.drawLine(QPointF(0.0, float(y)), QPointF(float(l_width), float(y)))
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

        painter.restore()

        # 5. Previsualización del tamaño de trazo pegada 1:1 al puntero del mouse (en coordenadas de pantalla del widget)
        if hasattr(self, 'widget_cursor_pos') and self.widget_cursor_pos is not None and getattr(self, 'active_tool_obj', None):
            tool_name = getattr(self.active_tool_obj, 'name', getattr(self.active_tool_obj, 'nombre', ''))
            if tool_name in ("Pincel", "Lápiz", "Goma de Borrar", "Línea"):
                w_doc = max(1, getattr(self, 'grosor_pincel', getattr(self, 'ancho_pincel', 3)))
                w_screen = w_doc * self.scale_factor
                w2 = w_screen / 2.0
                wx, wy = self.widget_cursor_pos.x(), self.widget_cursor_pos.y()
                rect = QRectF(wx - w2, wy - w2, w_screen, w_screen)

                painter.save()
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
                painter.restore()

    def _obtener_icono_herramienta_gris(self, tool_obj):
        """Devuelve un QPixmap de 16x16 en escala de grises para la herramienta activa."""
        if not tool_obj or not getattr(tool_obj, 'show_cursor_badge', True):
            return None

        if hasattr(tool_obj, 'get_icon_path'):
            icon_path = tool_obj.get_icon_path(self)
        else:
            icon_path = getattr(tool_obj, 'icon_path', getattr(tool_obj, 'icono', None))

        if not icon_path or not os.path.exists(icon_path):
            return None

        cache_key = f"_cached_gray_pix_{icon_path}"
        if hasattr(tool_obj, cache_key):
            return getattr(tool_obj, cache_key)

        img = QImage(icon_path)
        if img.isNull():
            return None

        img_scaled = img.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        img_gray = QImage(img_scaled.size(), QImage.Format.Format_ARGB32)
        for y in range(img_scaled.height()):
            for x in range(img_scaled.width()):
                col = img_scaled.pixelColor(x, y)
                if col.alpha() == 0:
                    img_gray.setPixelColor(x, y, QColor(0, 0, 0, 0))
                else:
                    gray = int(0.299 * col.red() + 0.587 * col.green() + 0.114 * col.blue())
                    img_gray.setPixelColor(x, y, QColor(gray, gray, gray, col.alpha()))

        pix = QPixmap.fromImage(img_gray)
        setattr(tool_obj, cache_key, pix)
        return pix

    def _notificar_posicion_cursor(self):
        if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'bottom_bar') and self.main_window.bottom_bar:
            if hasattr(self, 'cursor_pos') and self.cursor_pos is not None:
                cx, cy = int(self.cursor_pos.x()), int(self.cursor_pos.y())
                if 0 <= cx <= self.layer_mgr.width and 0 <= cy <= self.layer_mgr.height:
                    self.main_window.bottom_bar.actualizar_posicion_cursor(cx, cy)
                else:
                    self.main_window.bottom_bar.actualizar_posicion_cursor(None, None)
            else:
                self.main_window.bottom_bar.actualizar_posicion_cursor(None, None)

    # Manejo de mouse y despacho a herramientas
    def leaveEvent(self, event):
        self.cursor_pos = None
        self.widget_cursor_pos = None
        self._notificar_posicion_cursor()
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.setFocus()
        self.widget_cursor_pos = event.position()
        ev = self._canvas_event(event)
        self.cursor_pos = ev.position()
        self._notificar_posicion_cursor()
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
        self.widget_cursor_pos = event.position()
        ev = self._canvas_event(event)
        self.cursor_pos = ev.position()
        self._notificar_posicion_cursor()
        color_activo = self.color_primario if (ev.buttons() & Qt.MouseButton.LeftButton) else self.color_secundario

        if hasattr(self.active_tool_obj, 'mouse_move'):
            try:
                self.active_tool_obj.mouse_move(self, ev, color_activo)
            except TypeError:
                self.active_tool_obj.mouse_move(self, ev)

        if self.drawing and self.callback_modificado:
            self.callback_modificado()

        self.update()

    def mouseReleaseEvent(self, event):
        ev = self._canvas_event(event)
        self._notificar_posicion_cursor()
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

    # Funciones de Menús (Archivo, Editar, Imagen)
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
        self.push_document_state("Lienzo inicial")
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


    def redimensionar_lienzo(self, nuevo_ancho, nuevo_alto, anchor="top-left"):
        """Redimensiona el lienzo expandiendo con fondo transparente en todas las capas y registrando en el historial."""
        from tools.move_select_pixels import MoveSelectPixelsTool
        MoveSelectPixelsTool.commit_floating_image(self)

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
        from tools.move_select_pixels import MoveSelectPixelsTool
        MoveSelectPixelsTool.commit_floating_image(self)

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

    def recortar_a_seleccion(self):
        """Recorta el lienzo al bounding rect de la selección activa."""
        from PyQt6.QtCore import QRectF
        from PyQt6.QtGui import QImage, QPainter
        from tools.move_select_pixels import MoveSelectPixelsTool

        if not self.selection_engine.has_selection():
            return False

        # Bounding rect de la selección (en coordenadas del canvas)
        rect = self.selection_engine.active_path.boundingRect()
        if rect.isEmpty():
            rect = QRectF(self.selection_engine.active_rect)

        # Clampear al tamaño del canvas
        canvas_rect = QRectF(0, 0, self.layer_mgr.width, self.layer_mgr.height)
        rect = rect.intersected(canvas_rect)
        if rect.isEmpty():
            return False

        # Si hay una imagen flotante (insertada o pegada), fijarla sobre la capa activa ANTES de recortar
        if self.selection_engine.floating_image and not self.selection_engine.floating_image.isNull():
            MoveSelectPixelsTool.commit_floating_image(self)

        x, y = int(rect.x()), int(rect.y())
        w, h = max(1, int(rect.width())), max(1, int(rect.height()))

        # Recortar cada capa al rect
        for capa in self.layer_mgr.capas:
            new_img = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
            new_img.fill(Qt.GlobalColor.transparent)
            painter = QPainter(new_img)
            painter.drawImage(0, 0, capa.image, x, y, w, h)
            painter.end()
            capa.image = new_img

        self.layer_mgr.width = w
        self.layer_mgr.height = h
        self.selection_engine.clear_selection()
        self._ajustar_tamano_widget(w, h)
        self.capa_trazo_temp = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)
        self.push_document_state("Recortar")
        self.update()
        return True

    def actualizar_historial_gui(self):
        if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'history_panel'):
            self.main_window.history_panel.actualizar_historial()

    def push_floating_sub_state(self, label):
        self.push_document_state(label)

    def restaurar_sub_estado_flotante(self, snapshot):
        engine = self.selection_engine
        engine.floating_image = snapshot['floating_image'].copy()
        engine.unscaled_floating_image = snapshot['unscaled_floating_image'].copy()
        if 'original_raw_image' in snapshot and snapshot['original_raw_image']:
            engine.original_raw_image = snapshot['original_raw_image'].copy()
        else:
            engine.original_raw_image = engine.unscaled_floating_image.copy()

        engine.active_rect = QRectF(snapshot['active_rect'])
        engine.active_path = QPainterPath(snapshot['active_path'])

        tot_rot = float(snapshot.get('total_rotation', snapshot.get('rotation_angle', 0.0)))
        engine.total_rotation = tot_rot
        engine.rotation_angle = tot_rot
        engine.scale_x = float(snapshot.get('scale_x', 1.0))
        engine.scale_y = float(snapshot.get('scale_y', 1.0))

        if 'rotation_center' in snapshot and snapshot['rotation_center']:
            engine.rotation_center = QPointF(snapshot['rotation_center'])
        else:
            engine.rotation_center = QPointF(engine.active_rect.center())

        if 'initial_unrotated_path' in snapshot and snapshot['initial_unrotated_path']:
            engine.initial_unrotated_path = QPainterPath(snapshot['initial_unrotated_path'])
        else:
            engine.initial_unrotated_path = QPainterPath(engine.active_path)

        if 'initial_unrotated_rect' in snapshot and snapshot['initial_unrotated_rect']:
            engine.initial_unrotated_rect = QRectF(snapshot['initial_unrotated_rect'])
        else:
            engine.initial_unrotated_rect = QRectF(engine.active_rect)

        engine.original_image_pos = QPointF(snapshot['original_image_pos'])

    def empaquetar_paquete_flotante(self):
        engine = self.selection_engine
        if not engine.floating_image or engine.floating_image.isNull():
            return None
        initial_canvas = self.floating_initial_canvas.copy() if (hasattr(self, 'floating_initial_canvas') and self.floating_initial_canvas) else None
        return {
            'floating_image': engine.floating_image.copy(),
            'unscaled_floating_image': engine.unscaled_floating_image.copy() if engine.unscaled_floating_image else engine.floating_image.copy(),
            'original_raw_image': engine.original_raw_image.copy() if getattr(engine, 'original_raw_image', None) else (engine.unscaled_floating_image.copy() if engine.unscaled_floating_image else engine.floating_image.copy()),
            'active_rect': QRectF(engine.active_rect),
            'active_path': QPainterPath(engine.active_path),
            'rotation_angle': float(getattr(engine, 'rotation_angle', 0.0)),
            'total_rotation': float(getattr(engine, 'total_rotation', 0.0)),
            'scale_x': float(getattr(engine, 'scale_x', 1.0)),
            'scale_y': float(getattr(engine, 'scale_y', 1.0)),
            'rotation_center': QPointF(engine.rotation_center) if (hasattr(engine, 'rotation_center') and engine.rotation_center and not engine.rotation_center.isNull()) else QPointF(engine.active_rect.center()),
            'initial_unrotated_path': QPainterPath(engine.initial_unrotated_path) if getattr(engine, 'initial_unrotated_path', None) else QPainterPath(engine.active_path),
            'initial_unrotated_rect': QRectF(engine.initial_unrotated_rect) if getattr(engine, 'initial_unrotated_rect', None) else QRectF(engine.active_rect),
            'original_image_pos': QPointF(engine.original_image_pos),
            'initial_canvas': initial_canvas,
        }

    def restaurar_paquete_flotante(self, pkg):
        engine = self.selection_engine
        if not pkg or not isinstance(pkg, dict):
            engine.floating_image = None
            engine.unscaled_floating_image = None
            engine.original_raw_image = None
            self.floating_initial_canvas = None
            return

        # Formato de paquete flotante con sub_history (legado)
        if 'sub_history' in pkg and pkg['sub_history']:
            sub_hist = pkg['sub_history']
            sub_idx = max(0, min(pkg.get('sub_index', 0), len(sub_hist) - 1))
            pkg = sub_hist[sub_idx]

        # Formato moderno directo
        if 'floating_image' in pkg and pkg['floating_image'] and not pkg['floating_image'].isNull():
            engine.floating_image = pkg['floating_image'].copy()
            engine.unscaled_floating_image = pkg['unscaled_floating_image'].copy() if pkg.get('unscaled_floating_image') else pkg['floating_image'].copy()
            engine.original_raw_image = pkg['original_raw_image'].copy() if pkg.get('original_raw_image') else engine.unscaled_floating_image.copy()
            engine.active_rect = QRectF(pkg['active_rect']) if 'active_rect' in pkg else QRectF()
            engine.active_path = QPainterPath(pkg['active_path']) if 'active_path' in pkg else QPainterPath()

            tot_rot = float(pkg.get('total_rotation', pkg.get('rotation_angle', 0.0)))
            engine.total_rotation = tot_rot
            engine.rotation_angle = tot_rot
            engine.scale_x = float(pkg.get('scale_x', 1.0))
            engine.scale_y = float(pkg.get('scale_y', 1.0))

            if 'rotation_center' in pkg and pkg['rotation_center']:
                engine.rotation_center = QPointF(pkg['rotation_center'])
            else:
                engine.rotation_center = QPointF(engine.active_rect.center())

            if 'initial_unrotated_path' in pkg and pkg['initial_unrotated_path']:
                engine.initial_unrotated_path = QPainterPath(pkg['initial_unrotated_path'])
            else:
                engine.initial_unrotated_path = QPainterPath(engine.active_path)

            if 'initial_unrotated_rect' in pkg and pkg['initial_unrotated_rect']:
                engine.initial_unrotated_rect = QRectF(pkg['initial_unrotated_rect'])
            else:
                engine.initial_unrotated_rect = QRectF(engine.active_rect)

            engine.original_image_pos = QPointF(pkg['original_image_pos']) if 'original_image_pos' in pkg else QPointF()
            self.floating_initial_canvas = pkg['initial_canvas'].copy() if pkg.get('initial_canvas') else None
            if hasattr(self, 'main_window') and self.main_window:
                self.main_window.activar_herramienta_mover()
        else:
            engine.floating_image = None
            engine.unscaled_floating_image = None
            engine.original_raw_image = None
            self.floating_initial_canvas = None

    def asegurar_imagen_flotante(self):
        from tools.shapes import ShapesTool
        if isinstance(self.active_tool_obj, ShapesTool) and self.active_tool_obj.active_shape_rect:
            self.active_tool_obj.convert_to_selection(self)
            return True

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
                engine.init_raw_image(engine.floating_image)
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
            self.selection_engine.flip_floating_image(horizontal=horizontal, vertical=not horizontal)
            self.push_floating_sub_state("Voltear Horizontal" if horizontal else "Voltear Vertical")
            self.update()
            return

        self.push_document_state("Voltear Horizontal" if horizontal else "Voltear Vertical")
        for capa in self.layer_mgr.capas:
            capa.image = capa.image.mirrored(horizontal, not horizontal)
        self.actualizar_historial_gui()
        self.update()

    def rotar_contenido(self, grados):
        if self.asegurar_imagen_flotante():
            self.selection_engine.rotate_floating_image(grados)
            self.push_floating_sub_state(f"Rotar {grados}°")
            self.update()
            return

        self.push_document_state(f"Rotar {grados}°")
        t = QTransform().rotate(grados)

        for capa in self.layer_mgr.capas:
            capa.image = capa.image.transformed(t, Qt.TransformationMode.FastTransformation)

        if self.layer_mgr.capas:
            nuevo_ancho = self.layer_mgr.capas[0].image.width()
            nuevo_alto = self.layer_mgr.capas[0].image.height()
            self.layer_mgr.width = nuevo_ancho
            self.layer_mgr.height = nuevo_alto
            self._ajustar_tamano_widget(nuevo_ancho, nuevo_alto)

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
        path = QPainterPath(self.selection_engine.active_path) if (hasattr(self.selection_engine, 'active_path') and self.selection_engine.has_selection()) else None
        return {
            'width': self.layer_mgr.width,
            'height': self.layer_mgr.height,
            'layers': capas_copy,
            'active_index': self.layer_mgr.indice_activo,
            'floating_pkg': self.empaquetar_paquete_flotante() if (self.selection_engine.floating_image and not self.selection_engine.floating_image.isNull()) else None,
            'selection_path': path
        }

    def _snapshots_son_iguales(self, s1, s2):
        """Compara si dos snapshots del documento representan exactamente el mismo estado."""
        if not isinstance(s1, dict) or not isinstance(s2, dict):
            return False

        if s1.get('width') != s2.get('width') or s1.get('height') != s2.get('height'):
            return False
        if s1.get('active_index') != s2.get('active_index'):
            return False

        # Comparar ruta de selección
        p1 = s1.get('selection_path')
        p2 = s2.get('selection_path')
        p1_empty = (p1 is None or p1.isEmpty())
        p2_empty = (p2 is None or p2.isEmpty())
        if p1_empty != p2_empty:
            return False
        if not p1_empty and not p2_empty and p1 != p2:
            return False

        # Comparar paquete flotante (imagen flotante en movimiento/rotación)
        pkg1 = s1.get('floating_pkg')
        pkg2 = s2.get('floating_pkg')
        if (pkg1 is None) != (pkg2 is None):
            return False
        if pkg1 and pkg2:
            if pkg1.get('original_image_pos') != pkg2.get('original_image_pos'):
                return False
            if pkg1.get('active_rect') != pkg2.get('active_rect'):
                return False
            if pkg1.get('active_path') != pkg2.get('active_path'):
                return False
            if pkg1.get('rotation_angle') != pkg2.get('rotation_angle'):
                return False
            if pkg1.get('floating_image') != pkg2.get('floating_image'):
                return False

        # Comparar capas (visibilidad, nombre e imagen)
        l1 = s1.get('layers', [])
        l2 = s2.get('layers', [])
        if len(l1) != len(l2):
            return False

        for lay1, lay2 in zip(l1, l2):
            if lay1.get('name') != lay2.get('name') or lay1.get('visible') != lay2.get('visible'):
                return False
            img1 = lay1.get('image')
            img2 = lay2.get('image')
            if img1 != img2:
                return False

        return True

    def marcar_modificado(self, val=True):
        self.lienzo_modificado = val
        if hasattr(self, 'callback_modificado') and callable(self.callback_modificado):
            self.callback_modificado()
        elif hasattr(self, 'main_window') and self.main_window:
            self.main_window.actualizar_titulo_ventana()

    def push_document_state(self, action_name="Acción", force=False):
        """Guarda un estado completo del documento en el historial únicamente si se generaron cambios reales o si se fuerza."""
        snap = self.obtener_snapshot_documento()

        if not force and self.history_mgr.history_stack and self.history_mgr.current_index >= 0:
            last_snap, _ = self.history_mgr.history_stack[self.history_mgr.current_index]
            if self._snapshots_son_iguales(last_snap, snap):
                return

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
                self.selection_engine.floating_image = None
                self.selection_engine.unscaled_floating_image = None
                self.selection_engine.original_raw_image = None
                self.floating_initial_canvas = None

                selection_path = snap.get('selection_path')
                if selection_path and not selection_path.isEmpty():
                    self.selection_engine.set_path(QPainterPath(selection_path))
                else:
                    self.selection_engine.clear_selection()

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
        # Si la herramienta activa tiene una edición interactiva en curso (ej. Línea con tiradores activos)
        if hasattr(self, 'active_tool_obj') and self.active_tool_obj:
            if hasattr(self.active_tool_obj, 'cancel_or_reset'):
                if self.active_tool_obj.cancel_or_reset(self):
                    self.update()
                    return
            elif getattr(self.active_tool_obj, 'state', 0) in (1, 2):
                if hasattr(self.active_tool_obj, 'reset'):
                    self.active_tool_obj.reset()
                    self.update()
                    return

        prev_state = self.history_mgr.undo()
        if prev_state is not None:
            self.restaurar_snapshot_documento(prev_state)

    def redo(self):
        next_state = self.history_mgr.redo()
        if next_state is not None:
            self.restaurar_snapshot_documento(next_state)

    def cancelar_o_deseleccionar(self):
        engine = self.selection_engine
        tenia_flotante = bool(engine.floating_image and not engine.floating_image.isNull())
        tenia_seleccion = engine.has_selection() or tenia_flotante

        if not tenia_seleccion:
            return False

        if tenia_flotante:
            from tools.move_select_pixels import MoveSelectPixelsTool
            MoveSelectPixelsTool.commit_floating_image(self)
            self.floating_initial_canvas = None
            if hasattr(self, 'floating_sub_history'):
                self.floating_sub_history.clear()
            self.floating_sub_index = -1

        if engine.has_selection():
            engine.clear_selection()

        self.push_document_state("Cerrar selección", force=True)
        self.update()
        return True



    def seleccionar_todo(self):
        from tools.move_select_pixels import MoveSelectPixelsTool
        MoveSelectPixelsTool.commit_floating_image(self)
        rect = QRect(0, 0, self.layer_mgr.width, self.layer_mgr.height)
        self.selection_engine.set_rectangle(rect)
        self.update()

    def copiar_seleccion(self):
        from PyQt6.QtWidgets import QApplication
        from tools.shapes import ShapesTool
        if isinstance(self.active_tool_obj, ShapesTool) and self.active_tool_obj.active_shape_rect:
            self.active_tool_obj.copy_shape_to_clipboard(self)
            return

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
        from tools.shapes import ShapesTool
        if isinstance(self.active_tool_obj, ShapesTool) and self.active_tool_obj.active_shape_rect:
            self.push_document_state("Cortar")
            self.active_tool_obj.copy_shape_to_clipboard(self)
            self.active_tool_obj.clear_active_shape(self)
            return

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
        from tools.shapes import ShapesTool
        if isinstance(self.active_tool_obj, ShapesTool) and self.active_tool_obj.active_shape_rect:
            self.active_tool_obj.commit_shape(self)

        from PyQt6.QtWidgets import QApplication
        img = QApplication.clipboard().image()
        if not img.isNull():
            img_format = img.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
            return self._procesar_insercion_imagen(img_format, "Pegar")
        return False

    def _procesar_insercion_imagen(self, img_format: QImage, action_title: str = "Insertar Imagen"):
        from tools.move_select_pixels import MoveSelectPixelsTool
        from PyQt6.QtCore import QSize
        MoveSelectPixelsTool.commit_floating_image(self)

        img_w = img_format.width()
        img_h = img_format.height()
        lienzo_w = self.layer_mgr.width
        lienzo_h = self.layer_mgr.height

        opcion = "sin_cambios"
        if img_w > lienzo_w or img_h > lienzo_h:
            dlg = DialogoOpcionesInsercion(self, img_w, img_h, lienzo_w, lienzo_h)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                opcion = dlg.opcion_elegida
            else:
                return False

        self.push_document_state(action_title)

        if opcion == "ajustar_lienzo":
            nuevo_w = max(lienzo_w, img_w)
            nuevo_h = max(lienzo_h, img_h)
            self.redimensionar_lienzo(nuevo_w, nuevo_h, anchor="top-left")
            lienzo_w, lienzo_h = self.layer_mgr.width, self.layer_mgr.height
            pos_x = (lienzo_w - img_w) / 2.0 if img_w < lienzo_w else 0.0
            pos_y = (lienzo_h - img_h) / 2.0 if img_h < lienzo_h else 0.0
            self.selection_engine.set_rectangle(QRectF(pos_x, pos_y, img_w, img_h))
            self.selection_engine.original_image_pos = QPointF(pos_x, pos_y)
            self.selection_engine.init_raw_image(img_format)

        elif opcion == "adaptar_imagen":
            scaled_img = img_format.scaled(QSize(lienzo_w, lienzo_h), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            scaled_w = scaled_img.width()
            scaled_h = scaled_img.height()
            pos_x = (lienzo_w - scaled_w) / 2.0
            pos_y = (lienzo_h - scaled_h) / 2.0
            self.selection_engine.set_rectangle(QRectF(pos_x, pos_y, scaled_w, scaled_h))
            self.selection_engine.original_image_pos = QPointF(pos_x, pos_y)
            self.selection_engine.init_raw_image(scaled_img)

        else:  # "sin_cambios"
            pos_x = (lienzo_w - img_w) / 2.0 if img_w < lienzo_w else 0.0
            pos_y = (lienzo_h - img_h) / 2.0 if img_h < lienzo_h else 0.0
            self.selection_engine.set_rectangle(QRectF(pos_x, pos_y, img_w, img_h))
            self.selection_engine.original_image_pos = QPointF(pos_x, pos_y)
            self.selection_engine.init_raw_image(img_format)

        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.activar_herramienta_mover()
        self.update()
        return True

    def insertar_imagen(self, ruta):
        if not ruta or not os.path.exists(ruta):
            return False
        img = QImage(ruta)
        if img.isNull():
            return False
        img_format = img.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
        return self._procesar_insercion_imagen(img_format, "Insertar Imagen")

    def insertar_qimage(self, img: QImage):
        if not img or img.isNull():
            return False
        img_format = img.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
        return self._procesar_insercion_imagen(img_format, "Insertar Imagen desde Internet")
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

    def align_selection(self, alignment: str):
        """
        Alinea la selección activa, elemento flotante o cuadro de texto activo (Izquierda, Derecha, Arriba, Abajo, Centrar).
        """
        from tools.text import TextTool
        if isinstance(self.active_tool_obj, TextTool) and getattr(self.active_tool_obj, 'is_editing', False):
            self.active_tool_obj.align_text_box(self, alignment)
            return

        engine = self.selection_engine
        if not engine.has_selection():
            return

        # Si hay selección pero la imagen no se ha extraído a flotante aún, extraerla si aplica
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
                self.push_document_state("Alinear Selección")

        rect = engine.active_rect
        w, h = rect.width(), rect.height()
        cw, ch = float(self.layer_mgr.width), float(self.layer_mgr.height)

        if alignment == "left":
            new_x, new_y = 0.0, rect.top()
        elif alignment == "right":
            new_x, new_y = cw - w, rect.top()
        elif alignment == "top":
            new_x, new_y = rect.left(), 0.0
        elif alignment == "bottom":
            new_x, new_y = rect.left(), ch - h
        elif alignment == "center":
            new_x, new_y = (cw - w) / 2.0, (ch - h) / 2.0
        else:
            return

        dx = new_x - rect.left()
        dy = new_y - rect.top()

        if abs(dx) < 1e-4 and abs(dy) < 1e-4:
            return

        engine.translate(dx, dy)
        self.push_document_state("Alinear Selección")

        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.activar_herramienta_mover()

        self.update()
        if self.callback_modificado:
            self.callback_modificado()
