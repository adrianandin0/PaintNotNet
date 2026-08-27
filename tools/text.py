"""
text.py — Rich Text Tool con formato por segmento y text-box por drag.

Comportamiento del mouse:
  - Clic simple     → cursor de texto en ese punto (modo punto)
  - Clic + drag     → crea un rectángulo de texto (modo rect); el texto se
                      justifica automáticamente en ese ancho y hace word-wrap
  - Draggear esquina o borde del rect → redimensionar el text-box

Correcciones clave:
  - _line_height usa fuente BASE (sin bold/italic) → bold no cambia interlineado
  - _pos_from_point usa avance de substring (kerning-aware) → cursor exacto
  - _apply_fmt_to_range divide spans en los bordes de la selección
  - WA_InputMethodEnabled + inputMethodEvent en canvas → á é ñ ü funcionan
"""
from __future__ import annotations
from dataclasses import dataclass, field
from PyQt6.QtGui import (
    QPainter, QFont, QPen, QColor, QFontMetrics,
    QPainterPath, QBrush, QCursor
)
from PyQt6.QtCore import Qt, QPoint, QRect, QObject, QEvent
from tools.base_tool import BaseTool


# ─────────────────────────────────────────────────────────────────────────────
#  Modelo de datos
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CharFormat:
    font_family: str              = "Arial"
    font_size:   int              = 24
    bold:        bool             = False
    italic:      bool             = False
    underline:   bool             = False
    strike:      bool             = False
    color:       QColor           = field(default_factory=lambda: QColor(0, 0, 0))
    alignment:   Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft

    def build_font(self) -> QFont:
        f = QFont(self.font_family, self.font_size)
        f.setBold(self.bold)
        f.setItalic(self.italic)
        f.setUnderline(self.underline)
        f.setStrikeOut(self.strike)
        return f

    def build_base_font(self) -> QFont:
        """Fuente sin bold/italic → para cálculo de interlineado consistente."""
        return QFont(self.font_family, self.font_size)

    def copy(self) -> "CharFormat":
        return CharFormat(
            font_family=self.font_family,
            font_size=self.font_size,
            bold=self.bold, italic=self.italic,
            underline=self.underline, strike=self.strike,
            color=QColor(self.color), alignment=self.alignment,
        )

    def eq(self, other: "CharFormat") -> bool:
        return (self.font_family == other.font_family and
                self.font_size   == other.font_size   and
                self.bold        == other.bold         and
                self.italic      == other.italic       and
                self.underline   == other.underline    and
                self.strike      == other.strike       and
                self.color.rgba()== other.color.rgba() and
                self.alignment   == other.alignment)


@dataclass
class TextSpan:
    text: str
    fmt:  CharFormat = field(default_factory=CharFormat)


RichLine = list[TextSpan]

# ─────────────────────────────────────────────────────────────────────────────
#  Helpers de modelo
# ─────────────────────────────────────────────────────────────────────────────

def _line_text(line: RichLine) -> str:
    return "".join(s.text for s in line)


def _fmt_at(line: RichLine, col: int) -> CharFormat:
    pos = 0
    for span in line:
        if pos + len(span.text) > col:
            return span.fmt.copy()
        pos += len(span.text)
    return line[-1].fmt.copy() if line else CharFormat()


def _merge_spans(line: RichLine):
    i = 0
    while i < len(line) - 1:
        if line[i].fmt.eq(line[i + 1].fmt):
            line[i].text += line[i + 1].text
            del line[i + 1]
        else:
            i += 1


def _empty_line(fmt: CharFormat) -> RichLine:
    return [TextSpan("", fmt.copy())]


def _apply_dict_to_fmt(fmt: CharFormat, d: dict):
    if "font_family" in d: fmt.font_family = d["font_family"]
    if "font_size"   in d: fmt.font_size   = int(d["font_size"])
    if "bold"        in d: fmt.bold        = bool(d["bold"])
    if "italic"      in d: fmt.italic      = bool(d["italic"])
    if "underline"   in d: fmt.underline   = bool(d["underline"])
    if "strike"      in d: fmt.strike      = bool(d["strike"])
    if "alignment"   in d: fmt.alignment   = d["alignment"]
    if "color"       in d: fmt.color       = QColor(d["color"])


def _apply_fmt_to_range(line: RichLine, col_start: int, col_end: int, fmt_dict: dict):
    """Aplica fmt_dict EXACTAMENTE a [col_start, col_end), dividiendo spans."""
    if col_start >= col_end:
        return
    new_spans: RichLine = []
    pos = 0
    for span in line:
        l, s_end = len(span.text), pos + len(span.text)
        if s_end <= col_start or pos >= col_end:
            new_spans.append(TextSpan(span.text, span.fmt.copy()))
        elif pos >= col_start and s_end <= col_end:
            nf = span.fmt.copy(); _apply_dict_to_fmt(nf, fmt_dict)
            new_spans.append(TextSpan(span.text, nf))
        else:
            if pos < col_start:
                new_spans.append(TextSpan(span.text[:col_start - pos], span.fmt.copy()))
            ms = max(pos, col_start) - pos
            me = min(s_end, col_end) - pos
            if me > ms:
                nf = span.fmt.copy(); _apply_dict_to_fmt(nf, fmt_dict)
                new_spans.append(TextSpan(span.text[ms:me], nf))
            if s_end > col_end:
                new_spans.append(TextSpan(span.text[col_end - pos:], span.fmt.copy()))
        pos += l
    if not new_spans:
        base = line[-1].fmt.copy() if line else CharFormat()
        _apply_dict_to_fmt(base, fmt_dict); new_spans = [TextSpan("", base)]
    line[:] = new_spans
    _merge_spans(line)


def _delete_range_in_line(line: RichLine, col_start: int, col_end: int):
    result: RichLine = []
    pos = 0
    for span in line:
        l, s_end = len(span.text), pos + len(span.text)
        if s_end <= col_start or pos >= col_end:
            result.append(TextSpan(span.text, span.fmt.copy()))
        else:
            keep_l = max(0, col_start - pos)
            keep_r = max(0, s_end - col_end)
            new_t  = span.text[:keep_l] + (span.text[l - keep_r:] if keep_r else "")
            if new_t: result.append(TextSpan(new_t, span.fmt.copy()))
        pos += l
    if not result:
        result = [TextSpan("", line[-1].fmt.copy() if line else CharFormat())]
    line[:] = result


def _insert_text_at(line: RichLine, col: int, text: str, fmt: CharFormat) -> int:
    pos = 0
    for i, span in enumerate(line):
        l = len(span.text)
        if pos + l >= col:
            offset = col - pos
            if span.fmt.eq(fmt):
                span.text = span.text[:offset] + text + span.text[offset:]
            else:
                left  = TextSpan(span.text[:offset], span.fmt.copy())
                mid   = TextSpan(text, fmt.copy())
                right = TextSpan(span.text[offset:], span.fmt.copy())
                line[i:i+1] = [s for s in [left, mid, right] if s.text or s is mid]
            _merge_spans(line)
            return col + len(text)
        pos += l
    if line and line[-1].fmt.eq(fmt):
        line[-1].text += text
    else:
        line.append(TextSpan(text, fmt.copy()))
    _merge_spans(line)
    return col + len(text)


# ─────────────────────────────────────────────────────────────────────────────
#  TextTool
# ─────────────────────────────────────────────────────────────────────────────

_HANDLE_SIZE = 8   # px de los handles de resize


class TextTool(BaseTool, QObject):

    def __init__(self):
        BaseTool.__init__(self, "Texto", "gui/iconos/text.png")
        QObject.__init__(self)

        self.is_editing     = False
        self._default_fmt   = CharFormat()
        self.rich_lines: list[RichLine] = [_empty_line(self._default_fmt)]

        # Cursor y selección
        self.cursor_line: int           = 0
        self.cursor_col:  int           = 0
        self.sel_line:    int | None    = None
        self.sel_col:     int | None    = None

        # Modo punto vs modo rect
        self.pos        = QPoint(100, 100)   # modo punto: baseline de línea 0
        self.text_rect: QRect | None = None  # modo rect: bounding box

        self.current_canvas   = None
        self._mouse_selecting = False        # drag de selección de texto
        self._drag_start      = None         # punto inicial de drag al crear rect
        self._drag_handle: int | None = None # handle de resize activo (0-7)

    # ── helpers de dimensión ──────────────────────────────────────────────

    def _line_height(self, li: int) -> int:
        """
        Altura de línea basada en la fuente BASE (sin bold/italic).
        Bold/italic no cambia el interlineado — solo el peso visual.
        """
        h = 0
        for span in self.rich_lines[li]:
            m = QFontMetrics(span.fmt.build_base_font())
            h = max(h, m.height())
        return h if h else 20

    def _line_ascent(self, li: int) -> int:
        """Ascent de la fuente BASE para posición de cursor coherente."""
        a = 0
        for span in self.rich_lines[li]:
            m = QFontMetrics(span.fmt.build_base_font())
            a = max(a, m.ascent())
        return a if a else 16

    def _line_width(self, li: int) -> int:
        w = 0
        for span in self.rich_lines[li]:
            m = QFontMetrics(span.fmt.build_font())
            w += m.horizontalAdvance(span.text)
        return w

    def _max_line_width(self) -> int:
        return max((self._line_width(i) for i in range(len(self.rich_lines))), default=100)

    def _effective_width(self) -> int:
        """Ancho efectivo para wrap/justify: rect.width() o max_line_width."""
        return self.text_rect.width() if self.text_rect else self._max_line_width()

    def _origin(self) -> QPoint:
        """Punto superior-izquierdo del área de texto."""
        if self.text_rect:
            return self.text_rect.topLeft()
        return QPoint(self.pos.x(), self.pos.y() - self._line_ascent(0))

    # ─── helper: métricas del span que contiene col ───────────────────────

    def _fm_at(self, li: int, col: int) -> QFontMetrics:
        pos = 0
        for span in self.rich_lines[li]:
            if pos + len(span.text) > col:
                return QFontMetrics(span.fmt.build_font())
            pos += len(span.text)
        last = self.rich_lines[li][-1] if self.rich_lines[li] else None
        return QFontMetrics(last.fmt.build_font() if last else QFont())

    # ── word-wrap para modo rect ──────────────────────────────────────────

    def _wrap_line(self, li: int) -> list[tuple[int, int]]:
        """
        Divide la línea lógica li en segmentos visuales que caben en el
        ancho del text_rect.  Corta SIEMPRE en espacios (word-wrap real);
        solo hace corte forzado en la mitad de una palabra si una sola
        palabra no cabe en el ancho disponible.
        En modo punto devuelve [(0, len_total)].
        """
        line = self.rich_lines[li]
        text = _line_text(line)
        if not self.text_rect or not text:
            return [(0, len(text))]

        max_w = max(self.text_rect.width(), 1)
        segs  = []
        n     = len(text)
        start = 0

        while start < n:
            x          = 0.0
            last_break = -1   # posición de corte del último espacio
            i          = start

            while i < n:
                m  = self._fm_at(li, i)
                cw = m.horizontalAdvance(text[i])

                if x + cw > max_w:
                    if last_break > start:
                        # Cortar justo después del espacio anterior
                        seg_end = last_break
                        segs.append((start, seg_end))
                        # Saltar espacios iniciales de la siguiente línea visual
                        start = seg_end
                        while start < n and text[start] == ' ':
                            start += 1
                    else:
                        # Ni un espacio encontrado → corte forzado aquí
                        seg_end = max(i, start + 1)
                        segs.append((start, seg_end))
                        start = seg_end
                    break

                # Registrar el INICIO del próximo token (después del espacio)
                if text[i] == ' ':
                    last_break = i + 1   # punto de corte: carácter tras el espacio

                x += cw
                i += 1
            else:
                # Todo el texto restante cabe
                segs.append((start, n))
                break

        return segs if segs else [(0, n)]

    # ── alineación horizontal de una línea visual ─────────────────────────

    def _visual_line_x(self, li: int, seg_start: int, seg_end: int,
                        is_last_visual: bool) -> int:
        """X de inicio de una línea visual, según alignment."""
        line      = self.rich_lines[li]
        alignment = line[0].fmt.alignment if line else Qt.AlignmentFlag.AlignLeft
        ox        = self.text_rect.left() if self.text_rect else self.pos.x()

        if alignment == Qt.AlignmentFlag.AlignLeft:
            return ox
        if not self.text_rect:
            return ox

        max_w = self.text_rect.width()
        # Medir ancho del segmento
        seg_txt = _line_text(line)[seg_start:seg_end]
        lw = self._measure_text_width(li, seg_start, seg_end)

        if alignment == Qt.AlignmentFlag.AlignHCenter:
            return ox + (max_w - lw) // 2
        if alignment == Qt.AlignmentFlag.AlignRight:
            return ox + max_w - lw
        if alignment == Qt.AlignmentFlag.AlignJustify:
            if is_last_visual:
                return ox  # última línea → alinear izq
            return ox
        return ox

    def _measure_text_width(self, li: int, col_s: int, col_e: int) -> int:
        line = self.rich_lines[li]
        pos  = 0
        w    = 0
        for span in line:
            l = len(span.text)
            if pos + l <= col_s or pos >= col_e:
                pos += l; continue
            clip_s = max(col_s, pos) - pos
            clip_e = min(col_e, pos + l) - pos
            m = QFontMetrics(span.fmt.build_font())
            w += m.horizontalAdvance(span.text[clip_s:clip_e])
            pos += l
        return w

    # ── selección ──────────────────────────────────────────────────────────

    def _has_selection(self) -> bool:
        if self.sel_line is None: return False
        return (self.sel_line, self.sel_col) != (self.cursor_line, self.cursor_col)

    def _sel_range(self):
        al, ac = self.sel_line, self.sel_col
        bl, bc = self.cursor_line, self.cursor_col
        return (al, ac, bl, bc) if (al, ac) <= (bl, bc) else (bl, bc, al, ac)

    def _clear_sel(self):     self.sel_line = self.sel_col = None
    def _set_sel_anchor(self): self.sel_line = self.cursor_line; self.sel_col = self.cursor_col

    def _get_selected_text(self) -> str:
        if not self._has_selection(): return ""
        sl, sc, el, ec = self._sel_range()
        if sl == el:
            return _line_text(self.rich_lines[sl])[sc:ec]
        parts = [_line_text(self.rich_lines[sl])[sc:]]
        for i in range(sl + 1, el):
            parts.append(_line_text(self.rich_lines[i]))
        parts.append(_line_text(self.rich_lines[el])[:ec])
        return "\n".join(parts)

    def _delete_selection(self):
        if not self._has_selection(): return
        sl, sc, el, ec = self._sel_range()
        if sl == el:
            _delete_range_in_line(self.rich_lines[sl], sc, ec)
        else:
            _delete_range_in_line(self.rich_lines[sl], sc,
                                   len(_line_text(self.rich_lines[sl])))
            _delete_range_in_line(self.rich_lines[el], 0, ec)
            self.rich_lines[sl].extend(self.rich_lines[el])
            _merge_spans(self.rich_lines[sl])
            del self.rich_lines[sl + 1: el + 1]
        self.cursor_line, self.cursor_col = sl, sc
        self._clear_sel()

    # ── formato por selección ─────────────────────────────────────────────

    def apply_format_to_selection(self, fmt_dict: dict):
        _apply_dict_to_fmt(self._default_fmt, fmt_dict)
        if not self._has_selection():
            return
        sl, sc, el, ec = self._sel_range()
        for li in range(sl, el + 1):
            line = self.rich_lines[li]
            cs   = sc if li == sl else 0
            ce   = ec if li == el else len(_line_text(line))
            _apply_fmt_to_range(line, cs, ce, fmt_dict)
        if self.current_canvas:
            self.current_canvas.update()

    def on_format_changed(self, canvas, fmt_dict: dict):
        self.current_canvas = canvas
        if "alignment" in fmt_dict:
            align_val = fmt_dict["alignment"]
            for line in self.rich_lines:
                for span in line:
                    span.fmt.alignment = align_val
            self._default_fmt.alignment = align_val

        self.apply_format_to_selection(fmt_dict)
        if canvas:
            canvas.update()

    def align_text_box(self, canvas, alignment: str):
        if not self.is_editing or not canvas:
            return

        cw = canvas.layer_mgr.width
        ch = canvas.layer_mgr.height
        r = self._get_content_rect()
        w, h = r.width(), r.height()

        target_x = float(r.left())
        target_y = float(r.top())

        if alignment == "left":
            target_x = 0.0
        elif alignment == "right":
            target_x = float(cw - w)
        elif alignment == "top":
            target_y = 0.0
        elif alignment == "bottom":
            target_y = float(ch - h)
        elif alignment == "center":
            target_x = float(cw - w) / 2.0
            target_y = float(ch - h) / 2.0
        else:
            return

        dx = int(round(target_x - r.left()))
        dy = int(round(target_y - r.top()))

        if self.text_rect:
            self.text_rect.translate(dx, dy)
        self.pos = QPoint(self.pos.x() + dx, self.pos.y() + dy)

        canvas.update()

    def _update_panel_ui(self, canvas):
        if not canvas: return
        mw = getattr(canvas, 'main_window', None)
        if mw and hasattr(mw, 'text_panel') and mw.text_panel:
            fmt = _fmt_at(self.rich_lines[self.cursor_line], self.cursor_col)
            mw.text_panel.actualizar_desde_formato(fmt)

    def _calc_extra_per_space(self, li: int, seg_s: int, seg_e: int, is_last_v: bool) -> float:
        line = self.rich_lines[li]
        alignment = line[0].fmt.alignment if line else Qt.AlignmentFlag.AlignLeft
        if alignment == Qt.AlignmentFlag.AlignJustify and not is_last_v and self.text_rect:
            seg_txt = _line_text(line)[seg_s:seg_e]
            lw = self._measure_text_width(li, seg_s, seg_e)
            n_spaces = seg_txt.count(" ")
            if n_spaces > 0 and self.text_rect.width() > lw:
                return (self.text_rect.width() - lw) / n_spaces
        return 0.0

    # ── hit-test KERNING-AWARE ─────────────────────────────────────────────

    def _pos_from_point(self, canvas, click: QPoint):
        """Devuelve (line_idx, col_idx) para un punto del canvas.
        Usa avance de substring (kerning-aware) para precisión máxima."""

        # 1. Identificar línea visual → línea lógica + segmento
        ox       = self._origin().x()
        oy       = self._origin().y()
        y        = oy
        target_li = len(self.rich_lines) - 1

        for li in range(len(self.rich_lines)):
            segs = self._wrap_line(li)
            lh   = self._line_height(li)
            for vi, (seg_s, seg_e) in enumerate(segs):
                is_last_v = (vi == len(segs) - 1)
                is_last_line_seg = (li == len(self.rich_lines) - 1 and is_last_v)
                if click.y() <= y + lh or is_last_line_seg:
                    target_li = li
                    # 2. Identificar columna dentro del segmento
                    bx    = self._visual_line_x(li, seg_s, seg_e, is_last_v)
                    rel_x = click.x() - bx
                    return li, self._col_from_x(li, seg_s, seg_e, rel_x, is_last_v)
                y += lh

        return target_li, len(_line_text(self.rich_lines[target_li]))

    def _col_from_x(self, li: int, seg_s: int, seg_e: int, rel_x: float, is_last_v: bool = True) -> int:
        """Columna lógica más cercana a rel_x dentro del segmento [seg_s, seg_e)."""
        line = self.rich_lines[li]
        extra_space = self._calc_extra_per_space(li, seg_s, seg_e, is_last_v)
        pos  = 0
        x    = 0.0
        for span in line:
            l = len(span.text)
            if pos + l <= seg_s:
                pos += l; continue
            m       = QFontMetrics(span.fmt.build_font())
            t_start = max(seg_s, pos) - pos
            t_end   = min(seg_e, pos + l) - pos
            for i in range(t_start, t_end):
                sub_prev = span.text[t_start:i]
                sub_curr = span.text[t_start:i + 1]
                cw_prev = m.horizontalAdvance(sub_prev) + (sub_prev.count(" ") * extra_space)
                cw_curr = m.horizontalAdvance(sub_curr) + (sub_curr.count(" ") * extra_space)
                mid = x + (cw_prev + cw_curr) / 2.0
                if rel_x < mid:
                    return pos + i
            x   += m.horizontalAdvance(span.text[t_start:t_end]) + (span.text[t_start:t_end].count(" ") * extra_space)
            pos += l
            if pos >= seg_e:
                break
        return min(seg_e, len(_line_text(line)))

    # ── offset X de col en una línea lógica ──────────────────────────────

    def _col_x_offset(self, li: int, col: int,
                       seg_s: int = 0, seg_e: int | None = None, is_last_v: bool = True) -> float:
        """Offset X desde el inicio del segmento [seg_s, ...) hasta col."""
        line = self.rich_lines[li]
        if seg_e is None:
            seg_e = len(_line_text(line))
        extra_space = self._calc_extra_per_space(li, seg_s, seg_e, is_last_v)
        pos, x = 0, 0.0
        for span in line:
            l = len(span.text)
            if pos + l <= seg_s:
                pos += l; continue
            m       = QFontMetrics(span.fmt.build_font())
            t_start = max(seg_s, pos) - pos
            t_end   = min(seg_e, pos + l) - pos
            col_in  = col - pos
            if t_start <= col_in <= t_end:
                sub = span.text[t_start:col_in]
                x += m.horizontalAdvance(sub) + (sub.count(" ") * extra_space)
                return x
            sub = span.text[t_start:t_end]
            x   += m.horizontalAdvance(sub) + (sub.count(" ") * extra_space)
            pos += l
            if pos >= seg_e: break
        return x

    # ── handles del text-box ──────────────────────────────────────────────

    def _get_content_rect(self) -> QRect:
        if self.text_rect:
            return QRect(self.text_rect)
        total_h = max(sum(self._line_height(i) for i in range(len(self.rich_lines))), 24)
        asc0 = self._line_ascent(0)
        max_w = max(self._max_line_width(), 60)
        return QRect(self.pos.x(), self.pos.y() - asc0, max_w, total_h)

    def _handle_rects(self) -> list[tuple[int, QRect]]:
        r = self._get_content_rect()
        cx = r.center().x()
        cy = r.center().y()
        hs = _HANDLE_SIZE // 2

        pts = [
            r.topLeft(),                     # 0: TL
            QPoint(cx, r.top()),            # 1: TC
            r.topRight(),                    # 2: TR
            QPoint(r.right(), cy),          # 3: RC
            r.bottomRight(),                 # 4: BR
            QPoint(cx, r.bottom()),         # 5: BC
            r.bottomLeft(),                  # 6: BL
            QPoint(r.left(), cy),           # 7: LC
        ]
        resizes = [(i, QRect(p.x() - hs, p.y() - hs, _HANDLE_SIZE, _HANDLE_SIZE)) for i, p in enumerate(pts)]

        # Handle 8: Cuadradito de Mover (12x12px) al centro arriba del cuadro de texto
        move_sz = 12
        move_rect = QRect(cx - move_sz // 2, r.top() - move_sz - 4, move_sz, move_sz)
        resizes.append((8, move_rect))

        return resizes

    def _hit_handle(self, pt: QPoint) -> int | None:
        for idx, hr in self._handle_rects():
            if hr.contains(pt):
                return idx
        return None

    def _get_cursor_for_handle(self, handle: int) -> Qt.CursorShape:
        cursors = {
            0: Qt.CursorShape.SizeFDiagCursor, # TL
            1: Qt.CursorShape.SizeVerCursor,   # TC
            2: Qt.CursorShape.SizeBDiagCursor, # TR
            3: Qt.CursorShape.SizeHorCursor,   # RC
            4: Qt.CursorShape.SizeFDiagCursor, # BR
            5: Qt.CursorShape.SizeVerCursor,   # BC
            6: Qt.CursorShape.SizeBDiagCursor, # BL
            7: Qt.CursorShape.SizeHorCursor,   # LC
            8: Qt.CursorShape.SizeAllCursor,   # MV
        }
        return cursors.get(handle, Qt.CursorShape.IBeamCursor)

    def _resize_or_move_by_handle(self, handle: int, pt: QPoint):
        if not hasattr(self, '_drag_start_rect') or not self._drag_start_rect:
            return

        dx = pt.x() - self._drag_click_pos.x()
        dy = pt.y() - self._drag_click_pos.y()

        if handle == 8:
            # Move handle: desplaza la caja de texto completa sin alterar su tamaño
            self.pos = self._drag_start_pos + QPoint(dx, dy)
            if self.text_rect:
                self.text_rect = QRect(self._drag_start_rect.translated(dx, dy))
            return

        # Handles 0..7: Redimensión
        if not self.text_rect:
            self.text_rect = QRect(self._drag_start_rect)

        sr = self._drag_start_rect
        l, t = sr.left(), sr.top()
        w, h = sr.width(), sr.height()
        r_edge, b_edge = sr.right(), sr.bottom()
        min_w, min_h = 40, 20

        # Eje Horizontal (Izquierda: 0,6,7 / Derecha: 2,3,4)
        if handle in (0, 6, 7):
            l = min(sr.left() + dx, r_edge - min_w)
            w = r_edge - l + 1
        elif handle in (2, 3, 4):
            w = max(min_w, sr.width() + dx)

        # Eje Vertical (Superior: 0,1,2 / Inferior: 4,5,6)
        if handle in (0, 1, 2):
            t = min(sr.top() + dy, b_edge - min_h)
            h = b_edge - t + 1
        elif handle in (4, 5, 6):
            h = max(min_h, sr.height() + dy)

        new_rect = QRect(l, t, w, h)
        self.text_rect = new_rect
        self.pos = new_rect.topLeft()

    # ── mouse ──────────────────────────────────────────────────────────────

    def mouse_press(self, canvas, event, color_activo):
        self.current_canvas = canvas
        canvas.setFocus()
        canvas.removeEventFilter(self)
        canvas.installEventFilter(self)

        click = event.position().toPoint()

        if not self.is_editing:
            self._drag_start      = click
            self._mouse_selecting = False
            self._drag_handle     = None
            return

        # Ya editando → ¿clic en handle (resize o move)?
        h = self._hit_handle(click)
        if h is not None:
            self._drag_handle = h
            self._drag_click_pos = click
            self._drag_start_pos = QPoint(self.pos)
            self._drag_start_rect = QRect(self._get_content_rect())
            canvas.setCursor(self._get_cursor_for_handle(h))
            return

        # ¿Clic dentro del bounding rect?
        br = self._get_bounding_rect(canvas)
        if br.contains(click):
            li, ci = self._pos_from_point(canvas, click)
            shift  = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
            if shift:
                if self.sel_line is None:
                    self._set_sel_anchor()
            else:
                self._clear_sel()
                self._sel_anchor = (li, ci)
            self.cursor_line, self.cursor_col = li, ci
            self._mouse_selecting = True
            self._drag_handle     = None
            self._update_panel_ui(canvas)
        else:
            # Clic fuera → confirmar texto actual e iniciar nuevo
            self.commit_text(canvas, color_activo)
            self._drag_start      = click
            self._mouse_selecting = False
            self._drag_handle     = None

        canvas.update()

    def mouse_move(self, canvas, event, color_activo):
        click = event.position().toPoint()

        # Resize / Move de text_rect
        if self._drag_handle is not None:
            self._resize_or_move_by_handle(self._drag_handle, click)
            canvas.setCursor(self._get_cursor_for_handle(self._drag_handle))
            canvas.update()
            return

        # Drag para crear text_rect inicial
        if (not self.is_editing and self._drag_start is not None and
                (event.buttons() & Qt.MouseButton.LeftButton)):
            dx = abs(click.x() - self._drag_start.x())
            dy = abs(click.y() - self._drag_start.y())
            if dx > 5 or dy > 5:
                self._preview_rect = QRect(
                    min(click.x(), self._drag_start.x()),
                    min(click.y(), self._drag_start.y()),
                    abs(click.x() - self._drag_start.x()),
                    abs(click.y() - self._drag_start.y()))
                canvas.update()
            return

        # Selección de texto con drag
        if self.is_editing and self._mouse_selecting and (
                event.buttons() & Qt.MouseButton.LeftButton):
            li, ci = self._pos_from_point(canvas, click)
            self.cursor_line, self.cursor_col = li, ci
            if hasattr(self, '_sel_anchor') and self._sel_anchor:
                if (self.cursor_line, self.cursor_col) != self._sel_anchor:
                    self.sel_line, self.sel_col = self._sel_anchor
                else:
                    self._clear_sel()
            self._update_panel_ui(canvas)
            canvas.update()
            return

        # Hovering cursor feedback (siempre IBeam excepto sobre tiradores)
        if self.is_editing:
            h_hover = self._hit_handle(click)
            if h_hover is not None:
                canvas.setCursor(self._get_cursor_for_handle(h_hover))
            else:
                canvas.setCursor(Qt.CursorShape.IBeamCursor)

    def mouse_release(self, canvas, event, color_activo):
        click = event.position().toPoint()
        self._drag_handle     = None
        self._mouse_selecting = False

        if self.is_editing:
            canvas.setCursor(Qt.CursorShape.IBeamCursor)

        if not self._has_selection():
            self._clear_sel()
        if hasattr(self, '_sel_anchor'):
            del self._sel_anchor

        if not self.is_editing and self._drag_start is not None:
            dx = click.x() - self._drag_start.x()
            dy = click.y() - self._drag_start.y()

            if abs(dx) > 15 and abs(dy) > 15:
                # Crear text-box
                rect = QRect(
                    min(click.x(), self._drag_start.x()),
                    min(click.y(), self._drag_start.y()),
                    abs(dx), abs(dy))
                self._start_editing_rect(canvas, rect, color_activo)
            else:
                # Clic simple → modo punto
                self._start_editing_point(canvas, self._drag_start, color_activo)

            self._drag_start      = None
            if hasattr(self, '_preview_rect'):
                del self._preview_rect
            canvas.update()

    def _start_editing_point(self, canvas, pos: QPoint, color_activo):
        self.is_editing   = True
        self.text_rect    = None
        self._default_fmt = self._fmt_from_canvas(canvas, color_activo)
        self.rich_lines   = [_empty_line(self._default_fmt)]
        self.cursor_line  = self.cursor_col = 0
        self._clear_sel()
        self.pos = QPoint(pos.x(), pos.y() + self._line_ascent(0))

    def _start_editing_rect(self, canvas, rect: QRect, color_activo):
        self.is_editing   = True
        self.text_rect    = rect
        self._default_fmt = self._fmt_from_canvas(canvas, color_activo)
        self._default_fmt.alignment = Qt.AlignmentFlag.AlignLeft
        self.rich_lines   = [_empty_line(self._default_fmt)]
        self.cursor_line  = self.cursor_col = 0
        self._clear_sel()
        self.pos = rect.topLeft()

    def _fmt_from_canvas(self, canvas, color_activo) -> CharFormat:
        cfg = getattr(canvas, 'config_texto', {})
        if callable(cfg):
            try: cfg = cfg()
            except Exception: cfg = {}
        if not isinstance(cfg, dict): cfg = {}
        font_obj = cfg.get("font", None)
        return CharFormat(
            font_family = cfg.get("font_family", font_obj.family() if font_obj else "Arial"),
            font_size   = int(cfg.get("size", cfg.get("font_size", 24))),
            bold        = bool(cfg.get("bold",      False)),
            italic      = bool(cfg.get("italic",    False)),
            underline   = bool(cfg.get("underline", False)),
            strike      = bool(cfg.get("strike",    False)),
            color       = QColor(color_activo) if color_activo else QColor(0, 0, 0),
            alignment   = cfg.get("alignment", Qt.AlignmentFlag.AlignLeft),
        )

    # ── teclado ────────────────────────────────────────────────────────────

    def key_press(self, canvas, event, color_activo):
        if not self.is_editing: return False

        key   = event.key()
        mods  = event.modifiers()
        text  = event.text()
        shift = bool(mods & Qt.KeyboardModifier.ShiftModifier)
        ctrl  = bool(mods & Qt.KeyboardModifier.ControlModifier)

        if ctrl and key == Qt.Key.Key_A:
            self.sel_line = self.sel_col = 0
            self.cursor_line = len(self.rich_lines) - 1
            self.cursor_col  = len(_line_text(self.rich_lines[-1]))
            canvas.update(); return True

        if ctrl and key == Qt.Key.Key_C:
            from PyQt6.QtWidgets import QApplication
            sel = self._get_selected_text()
            if sel: QApplication.clipboard().setText(sel)
            return True

        if ctrl and key == Qt.Key.Key_X:
            from PyQt6.QtWidgets import QApplication
            sel = self._get_selected_text()
            if sel:
                QApplication.clipboard().setText(sel)
                self._delete_selection(); canvas.update()
            return True

        if ctrl and key == Qt.Key.Key_V:
            from PyQt6.QtWidgets import QApplication
            paste = QApplication.clipboard().text()
            if paste:
                if self._has_selection(): self._delete_selection()
                self._insert_text(paste); canvas.update()
            return True

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self._has_selection(): self._delete_selection()
            self._split_line(); self._clear_sel()

        elif key == Qt.Key.Key_Backspace:
            if self._has_selection():
                self._delete_selection()
            elif self.cursor_col > 0:
                _delete_range_in_line(self.rich_lines[self.cursor_line],
                                      self.cursor_col - 1, self.cursor_col)
                self.cursor_col -= 1
            elif self.cursor_line > 0:
                prev = len(_line_text(self.rich_lines[self.cursor_line - 1]))
                self.rich_lines[self.cursor_line - 1].extend(self.rich_lines[self.cursor_line])
                _merge_spans(self.rich_lines[self.cursor_line - 1])
                del self.rich_lines[self.cursor_line]
                self.cursor_line -= 1; self.cursor_col = prev

        elif key == Qt.Key.Key_Delete:
            if self._has_selection():
                self._delete_selection()
            else:
                lt = _line_text(self.rich_lines[self.cursor_line])
                if self.cursor_col < len(lt):
                    _delete_range_in_line(self.rich_lines[self.cursor_line],
                                          self.cursor_col, self.cursor_col + 1)
                elif self.cursor_line < len(self.rich_lines) - 1:
                    self.rich_lines[self.cursor_line].extend(
                        self.rich_lines[self.cursor_line + 1])
                    _merge_spans(self.rich_lines[self.cursor_line])
                    del self.rich_lines[self.cursor_line + 1]

        elif key == Qt.Key.Key_Left:
            if shift and self.sel_line is None: self._set_sel_anchor()
            elif not shift: self._clear_sel()
            if self.cursor_col > 0: self.cursor_col -= 1
            elif self.cursor_line > 0:
                self.cursor_line -= 1
                self.cursor_col = len(_line_text(self.rich_lines[self.cursor_line]))

        elif key == Qt.Key.Key_Right:
            if shift and self.sel_line is None: self._set_sel_anchor()
            elif not shift: self._clear_sel()
            ll = len(_line_text(self.rich_lines[self.cursor_line]))
            if self.cursor_col < ll: self.cursor_col += 1
            elif self.cursor_line < len(self.rich_lines) - 1:
                self.cursor_line += 1; self.cursor_col = 0

        elif key == Qt.Key.Key_Up:
            if shift and self.sel_line is None: self._set_sel_anchor()
            elif not shift: self._clear_sel()
            if self.cursor_line > 0:
                self.cursor_line -= 1
                self.cursor_col = min(self.cursor_col,
                                      len(_line_text(self.rich_lines[self.cursor_line])))

        elif key == Qt.Key.Key_Down:
            if shift and self.sel_line is None: self._set_sel_anchor()
            elif not shift: self._clear_sel()
            if self.cursor_line < len(self.rich_lines) - 1:
                self.cursor_line += 1
                self.cursor_col = min(self.cursor_col,
                                      len(_line_text(self.rich_lines[self.cursor_line])))

        elif key == Qt.Key.Key_Home:
            if shift and self.sel_line is None: self._set_sel_anchor()
            elif not shift: self._clear_sel()
            self.cursor_col = 0

        elif key == Qt.Key.Key_End:
            if shift and self.sel_line is None: self._set_sel_anchor()
            elif not shift: self._clear_sel()
            self.cursor_col = len(_line_text(self.rich_lines[self.cursor_line]))

        elif text and not ctrl and (text.isprintable() or ord(text[0]) > 127):
            # Acepta ASCII imprimible + caracteres Unicode (á é ñ ü ...)
            if self._has_selection(): self._delete_selection()
            self.cursor_col = _insert_text_at(
                self.rich_lines[self.cursor_line],
                self.cursor_col, text, self._default_fmt)
            self._clear_sel()
        else:
            return False

        self._update_panel_ui(canvas)
        canvas.update()
        return True

    def _insert_text(self, text: str):
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        fmt   = self._default_fmt.copy()
        for i, ln in enumerate(lines):
            if i > 0: self._split_line()
            if ln:
                self.cursor_col = _insert_text_at(
                    self.rich_lines[self.cursor_line], self.cursor_col, ln, fmt)

    def _split_line(self):
        line = self.rich_lines[self.cursor_line]
        txt  = _line_text(line)
        col  = self.cursor_col
        fmt  = _fmt_at(line, col)
        _delete_range_in_line(line, col, len(txt))
        new_line = [TextSpan(txt[col:], fmt.copy())] if txt[col:] else [TextSpan("", fmt.copy())]
        self.rich_lines.insert(self.cursor_line + 1, new_line)
        self.cursor_line += 1; self.cursor_col = 0

    # ── eventFilter ───────────────────────────────────────────────────────

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape and self.is_editing and self.current_canvas:
                self.commit_text(self.current_canvas, self.current_canvas.color_primario)
                return True
        return super().eventFilter(obj, event)

    # ── rendering ─────────────────────────────────────────────────────────

    def _get_effects_cfg(self, canvas) -> dict:
        mw = getattr(canvas, 'main_window', None)
        if mw and hasattr(mw, 'effects_panel'):
            return mw.effects_panel.obtener_config()
        return {}

    def draw_preview(self, painter: QPainter, canvas):
        if not self.is_editing:
            if hasattr(self, '_preview_rect'):
                painter.setPen(QPen(QColor(80, 140, 220), 1, Qt.PenStyle.DashLine))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(self._preview_rect)
            return

        self._render(painter, canvas, is_commit=False)

        # Contorno delimitador del cuadro de texto
        rect = self._get_content_rect()
        painter.setPen(QPen(QColor(0, 120, 215), 1, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)

        # Dibujar tiradores 0..7 (Resize) y 8 (Move)
        for idx, hr in self._handle_rects():
            if idx == 8:
                # Handle de mover: Cuadradito de mover un poco más grande (azul con borde blanco)
                painter.setPen(QPen(QColor(255, 255, 255), 1.5))
                painter.setBrush(QBrush(QColor(26, 95, 168)))
                painter.drawRect(hr)
            else:
                # Tiradores de redimensión (cuadritos blancos con borde azul)
                painter.setPen(QPen(QColor(0, 120, 215), 1))
                painter.setBrush(QBrush(QColor(255, 255, 255)))
                painter.drawRect(hr)

    def _render(self, painter: QPainter, canvas, is_commit: bool = False):
        eff       = self._get_effects_cfg(canvas)
        borde_en  = eff.get("borde_enabled",  False)
        borde_w   = max(1, int(eff.get("borde_width", 4)))
        borde_col = eff.get("borde_color",  QColor(255, 255, 255))
        glow_en   = eff.get("glow_enabled",  False)
        glow_r    = max(1, int(eff.get("glow_width", 10)))
        glow_col  = eff.get("glow_color",   QColor(255, 200, 0))
        shadow_en = eff.get("shadow_enabled", False)
        shadow_w  = max(1, int(eff.get("shadow_width", 10)))
        shadow_col= eff.get("shadow_color", QColor(0, 0, 0, 180))
        off_x     = int(float(eff.get("shadow_dx", 0.5)) * shadow_w * 0.5)
        off_y     = int(float(eff.get("shadow_dy", 0.5)) * shadow_w * 0.5)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        oy = self._origin().y()

        # Clipear al text_rect solo si NO hay efectos activos (borde, resplandor, sombra)
        has_effects = (borde_en or glow_en or shadow_en)
        clip_applied = False
        if self.text_rect and not has_effects:
            painter.setClipRect(self.text_rect)
            clip_applied = True

        # ── Selección ────────────────────────────────────────────────────
        if not is_commit and self._has_selection():
            sl, sc, el, ec = self._sel_range()
            sel_color = QColor(0, 120, 215, 100)
            y = oy
            for li in range(len(self.rich_lines)):
                lh   = self._line_height(li)
                segs = self._wrap_line(li)
                for vi, (seg_s, seg_e) in enumerate(segs):
                    is_last_v = (vi == len(segs) - 1)
                    txt_len   = len(_line_text(self.rich_lines[li]))
                    # Comprobar si este segmento está (parcialmente) seleccionado
                    if sl <= li <= el:
                        cs2 = sc if li == sl else 0
                        ce2 = ec if li == el else txt_len
                        # Intersección del segmento con la selección
                        hs  = max(cs2, seg_s)
                        he  = min(ce2, seg_e)
                        if hs < he:
                            bx  = self._visual_line_x(li, seg_s, seg_e, is_last_v)
                            xs  = bx + self._col_x_offset(li, hs, seg_s, seg_e)
                            xe  = bx + self._col_x_offset(li, he, seg_s, seg_e)
                            asc = self._line_ascent(li)
                            painter.fillRect(QRect(int(xs), int(y), int(xe - xs), lh), sel_color)
                    y += lh

        # ── Texto ─────────────────────────────────────────────────────────
        y = oy
        for li, rich_line in enumerate(self.rich_lines):
            lh   = self._line_height(li)
            asc  = self._line_ascent(li)
            segs = self._wrap_line(li)
            for vi, (seg_s, seg_e) in enumerate(segs):
                is_last_v = (vi == len(segs) - 1)
                bx = self._visual_line_x(li, seg_s, seg_e, is_last_v)
                baseline = y + asc

                # Calcular justify extra_space_per_gap si aplica
                alignment = rich_line[0].fmt.alignment if rich_line else Qt.AlignmentFlag.AlignLeft
                extra_per_space = 0.0
                if (alignment == Qt.AlignmentFlag.AlignJustify and not is_last_v and
                        self.text_rect):
                    seg_txt = _line_text(rich_line)[seg_s:seg_e]
                    lw      = self._measure_text_width(li, seg_s, seg_e)
                    n_spaces = seg_txt.count(" ")
                    if n_spaces > 0:
                        extra_per_space = (self.text_rect.width() - lw) / n_spaces

                # Renderizar spans dentro del segmento
                x_acc = 0.0
                pos   = 0
                for span in rich_line:
                    l = len(span.text)
                    if pos + l <= seg_s:
                        pos += l; continue
                    if pos >= seg_e:
                        break
                    font = span.fmt.build_font()
                    m    = QFontMetrics(font)
                    t_s  = max(seg_s, pos) - pos
                    t_e  = min(seg_e, pos + l) - pos
                    sub  = span.text[t_s:t_e]
                    painter.setFont(font)

                    if extra_per_space > 0:
                        for ch in sub:
                            path = QPainterPath()
                            path.addText(bx + x_acc, baseline, font, ch)
                            self._draw_path(painter, path, span.fmt.color,
                                            borde_en, borde_w, borde_col,
                                            glow_en, glow_r, glow_col,
                                            shadow_en, shadow_w, shadow_col, off_x, off_y)
                            cw = m.horizontalAdvance(ch)
                            x_acc += cw + (extra_per_space if ch == " " else 0)
                    else:
                        path = QPainterPath()
                        path.addText(bx + x_acc, baseline, font, sub)
                        self._draw_path(painter, path, span.fmt.color,
                                        borde_en, borde_w, borde_col,
                                        glow_en, glow_r, glow_col,
                                        shadow_en, shadow_w, shadow_col, off_x, off_y)
                        x_acc += m.horizontalAdvance(sub)
                    pos += l

                # Cursor
                if not is_commit and li == self.cursor_line:
                    # ¿El cursor está en este segmento?
                    cur_in_seg = seg_s <= self.cursor_col <= seg_e
                    if cur_in_seg:
                        cx  = bx + self._col_x_offset(li, self.cursor_col, seg_s, seg_e)
                        painter.setPen(QPen(QColor(30, 30, 30), 2))
                        painter.drawLine(int(cx), int(y), int(cx), int(y + lh))

                y += lh

        # Restaurar clip
        if clip_applied:
            painter.setClipping(False)

    def _draw_path(self, painter, path, color,
                   borde_en, borde_w, borde_col,
                   glow_en, glow_r, glow_col,
                   shadow_en, shadow_w, shadow_col, off_x, off_y):
        if shadow_en:
            sp = QPainterPath(path)
            sp.translate(off_x, off_y)
            for r in range(shadow_w, 0, -max(1, shadow_w // 8)):
                alpha = int(180 * (1 - r / shadow_w) ** 1.2)
                sc = QColor(shadow_col.red(), shadow_col.green(),
                            shadow_col.blue(), min(255, alpha))
                painter.strokePath(sp, QPen(sc, r * 2, Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        if glow_en:
            for r in range(glow_r, 0, -max(1, glow_r // 20)):
                alpha = int(200 * (1 - r / glow_r) ** 1.5)
                gc = QColor(glow_col.red(), glow_col.green(),
                            glow_col.blue(), min(255, alpha))
                painter.strokePath(path, QPen(gc, r * 2, Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        if borde_en:
            painter.strokePath(path, QPen(borde_col, borde_w * 2, Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.fillPath(path, QBrush(color))

    def commit_text(self, canvas, color_activo):
        if not self.is_editing: return
        if any(any(s.text.strip() for s in line) for line in self.rich_lines):
            qimg    = canvas.layer_mgr.buffer
            painter = QPainter(qimg)
            canvas.aplicar_clip_seleccion(painter)
            self._render(painter, canvas, is_commit=True)
            painter.end()
            canvas.actualizar_historial_gui()
        if self.current_canvas:
            self.current_canvas.removeEventFilter(self)
        self.is_editing = False
        self.text_rect  = None
        self.rich_lines = [_empty_line(self._default_fmt)]
        self._clear_sel()
        canvas.update()

    def _get_bounding_rect(self, canvas) -> QRect:
        if self.text_rect:
            return self.text_rect.adjusted(-5, -5, 5, 5)
        eff     = self._get_effects_cfg(canvas)
        total_h = sum(self._line_height(i) for i in range(len(self.rich_lines)))
        asc0    = self._line_ascent(0)
        max_w   = self._max_line_width()
        margin  = 20
        if eff.get("glow_enabled"):   margin += min(int(eff.get("glow_width", 10)) * 2, 200)
        if eff.get("shadow_enabled"): margin += min(int(eff.get("shadow_width", 10)), 100)
        return QRect(self.pos.x() - margin // 2,
                     self.pos.y() - asc0 - margin // 2,
                     max_w + margin, total_h + margin)
