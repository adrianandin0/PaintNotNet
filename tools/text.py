from PyQt6.QtGui import QPainter, QFont, QPen, QColor, QFontMetrics, QPainterPath
from PyQt6.QtCore import Qt, QPoint, QRect, QObject, QEvent
from tools.base_tool import BaseTool

class TextTool(BaseTool, QObject):
    def __init__(self):
        BaseTool.__init__(self, "Texto", "gui/iconos/text.png")
        QObject.__init__(self)

        self.is_editing = False
        self.text_lines = [""]
        self.cursor_line = 0
        self.cursor_col = 0
        self.pos = QPoint(100, 100)

        self.is_dragging = False
        self.drag_offset = QPoint()
        self.current_canvas = None

    def eventFilter(self, obj, event):
        """Intercepta la tecla Escape antes que cualquier widget de la app."""
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape and self.is_editing and self.current_canvas:
                self.commit_text(self.current_canvas, self.current_canvas.color_primario)
                return True  # Evento consumido
        return super().eventFilter(obj, event)

    def mouse_press(self, canvas, event, color_activo):
        self.current_canvas = canvas
        canvas.setFocus()

        # Instalar el filtro de eventos en el lienzo la primera vez
        canvas.removeEventFilter(self)
        canvas.installEventFilter(self)

        pos_click = event.position().toPoint()

        if not self.is_editing:
            self.is_editing = True
            self.text_lines = [""]
            self.cursor_line = 0
            self.cursor_col = 0
            self.pos = pos_click
        else:
            rect_caja = self._get_bounding_rect(canvas)
            if rect_caja.contains(pos_click):
                self.is_dragging = True
                self.drag_offset = pos_click - self.pos
            else:
                self.commit_text(canvas, color_activo)
                self.is_editing = True
                self.text_lines = [""]
                self.cursor_line = 0
                self.cursor_col = 0
                self.pos = pos_click

    def mouse_move(self, canvas, event, color_activo):
        if self.is_dragging and self.is_editing:
            self.pos = event.position().toPoint() - self.drag_offset
            canvas.update()

    def mouse_release(self, canvas, event, color_activo):
        self.is_dragging = False

    def key_press(self, canvas, event, color_activo):
        if not self.is_editing:
            return False

        key = event.key()

        # ESCAPE -> Estampar texto y cerrar cuadro de edición
        if key == Qt.Key.Key_Escape:
            self.commit_text(canvas, color_activo)
            return True

        key = event.key()
        text = event.text()

        # ESCAPE -> Estampar texto y cerrar cuadro de edición
        if key == Qt.Key.Key_Escape:
            self.commit_text(canvas, color_activo)
            return True

        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            linea_actual = self.text_lines[self.cursor_line]
            resto = linea_actual[self.cursor_col:]
            self.text_lines[self.cursor_line] = linea_actual[:self.cursor_col]

            self.cursor_line += 1
            self.text_lines.insert(self.cursor_line, resto)
            self.cursor_col = 0

        elif key == Qt.Key.Key_Backspace:
            if self.cursor_col > 0:
                linea = self.text_lines[self.cursor_line]
                self.text_lines[self.cursor_line] = linea[:self.cursor_col - 1] + linea[self.cursor_col:]
                self.cursor_col -= 1
            elif self.cursor_line > 0:
                linea_borrada = self.text_lines.pop(self.cursor_line)
                self.cursor_line -= 1
                self.cursor_col = len(self.text_lines[self.cursor_line])
                self.text_lines[self.cursor_line] += linea_borrada

        elif key == Qt.Key.Key_Left:
            if self.cursor_col > 0:
                self.cursor_col -= 1
            elif self.cursor_line > 0:
                self.cursor_line -= 1
                self.cursor_col = len(self.text_lines[self.cursor_line])

        elif key == Qt.Key.Key_Right:
            if self.cursor_col < len(self.text_lines[self.cursor_line]):
                self.cursor_col += 1
            elif self.cursor_line < len(self.text_lines) - 1:
                self.cursor_line += 1
                self.cursor_col = 0

        elif key == Qt.Key.Key_Up and self.cursor_line > 0:
            self.cursor_line -= 1
            self.cursor_col = min(self.cursor_col, len(self.text_lines[self.cursor_line]))
        elif key == Qt.Key.Key_Down and self.cursor_line < len(self.text_lines) - 1:
            self.cursor_line += 1
            self.cursor_col = min(self.cursor_col, len(self.text_lines[self.cursor_line]))

        elif text and text.isprintable():
            linea = self.text_lines[self.cursor_line]
            self.text_lines[self.cursor_line] = linea[:self.cursor_col] + text + linea[self.cursor_col:]
            self.cursor_col += len(text)

        canvas.update()
        return True

    def _get_config_dict(self, canvas):
        cfg = getattr(canvas, 'config_texto', {})
        if callable(cfg):
            try:
                cfg = cfg()
            except Exception:
                cfg = {}
        if not isinstance(cfg, dict):
            cfg = {}
        return cfg

    def _render_text_effects(self, painter, canvas, color_primario, is_commit=False):
        cfg = self._get_config_dict(canvas)

        font = QFont(
            cfg.get("font_family", "Arial"),
            cfg.get("font_size", 24),
            QFont.Weight.Bold if cfg.get("bold", False) else QFont.Weight.Normal,
            cfg.get("italic", False)
        )
        font.setUnderline(cfg.get("underline", False))
        font.setStrikeOut(cfg.get("strike", False))

        painter.setFont(font)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        metrics = QFontMetrics(font)
        line_height = metrics.height()

        # Config de Borde
        borde_enabled = cfg.get("borde_enabled", False)
        borde_size = cfg.get("borde_size", 3)
        color_secundario = getattr(canvas, 'color_secundario', QColor(255, 255, 255))

        # Config de Resplandor / Glow Sombra
        sombra_enabled = cfg.get("sombra_enabled", False)
        off_x = int(cfg.get("sombra_offset_x", 0))
        off_y = int(cfg.get("sombra_offset_y", 0))

        y = self.pos.y()
        for idx, line in enumerate(self.text_lines):
            x = self.pos.x()

            if line:
                # 1. RESPLANDOR EXTERNO / OUTER GLOW (Capas concéntricas para difusión suave)
                if sombra_enabled:
                    glow_steps = 4
                    base_alpha = 120 // glow_steps
                    for step in range(glow_steps, 0, -1):
                        glow_path = QPainterPath()
                        # Si off_x y off_y son 0 (luz al centro), el glow se expande parejo a todos los lados
                        glow_path.addText(x + (off_x * step / glow_steps), y + (off_y * step / glow_steps), font, line)

                        glow_pen = QPen(
                            QColor(0, 0, 0, base_alpha),
                            step * 2,
                            Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap,
                            Qt.PenJoinStyle.RoundJoin
                        )
                        painter.strokePath(glow_path, glow_pen)

                # 2. BORDE CON COLOR SECUNDARIO
                if borde_enabled:
                    path = QPainterPath()
                    path.addText(x, y, font, line)
                    pen_borde = QPen(color_secundario, borde_size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                    painter.strokePath(path, pen_borde)

                # 3. TEXTO PRINCIPAL
                painter.setPen(color_primario)
                painter.drawText(x, y, line)

            # 4. CURSOR INTERACTIVO
            if not is_commit and idx == self.cursor_line:
                sub_text = line[:self.cursor_col]
                cursor_x = x + metrics.horizontalAdvance(sub_text)
                painter.setPen(QPen(Qt.GlobalColor.black, 2))
                painter.drawLine(cursor_x, y - metrics.ascent(), cursor_x, y + metrics.descent())

            y += line_height

    def draw_preview(self, painter, canvas):
        if not self.is_editing:
            return

        self._render_text_effects(painter, canvas, canvas.color_primario, is_commit=False)

        rect = self._get_bounding_rect(canvas)
        pen_punteado = QPen(QColor(100, 100, 100), 1, Qt.PenStyle.DashLine)
        painter.setPen(pen_punteado)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)

    def commit_text(self, canvas, color_activo):
        if not self.is_editing:
            return

        texto_completo = "".join(self.text_lines).strip()
        if texto_completo:
            qimg = canvas.layer_mgr.buffer
            painter = QPainter(qimg)
            self._render_text_effects(painter, canvas, color_activo, is_commit=True)
            painter.end()

        # Quitar el filtro de eventos al salir de edición
        if self.current_canvas:
            self.current_canvas.removeEventFilter(self)

        self.is_editing = False
        self.text_lines = [""]
        canvas.update()

    def _get_bounding_rect(self, canvas):
        cfg = self._get_config_dict(canvas)
        font = QFont(cfg.get("font_family", "Arial"), cfg.get("font_size", 24))
        metrics = QFontMetrics(font)

        max_width = 100
        for line in self.text_lines:
            max_width = max(max_width, metrics.horizontalAdvance(line))

        total_height = max(metrics.height(), len(self.text_lines) * metrics.height())
        return QRect(self.pos.x() - 10, self.pos.y() - metrics.ascent() - 10, max_width + 20, total_height + 20)
