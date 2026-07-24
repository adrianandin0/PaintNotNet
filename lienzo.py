import numpy as np
import cv2
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QImage, QColor, QPen, QFont, QFontMetrics, QPainterPath
from PyQt6.QtCore import Qt, QRect, QPoint, QPointF


class Lienzo(QWidget):
    MARGEN_GRIP = 8

    def __init__(self, ancho, alto):
        super().__init__()
        self.setFixedSize(ancho, alto)
        self.setMouseTracking(True)

        self.capa_activa = QImage(ancho, alto, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_activa.fill(Qt.GlobalColor.transparent)

        self.capa_trazo_temp = QImage(ancho, alto, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

        self.ultimo_punto = None
        self.trayectoria_actual = None
        
        self.color_principal = QColor(0, 0, 0)
        self.color_secundario = QColor(255, 255, 255)
        self.color_actual_uso = self.color_principal
        
        self.grosor_pincel = 4
        self.opacidad_pincel = 255  # 255 Sólido, 0 Invisible
        self.suavizado_pincel = 100
        self.forma_pincel = "Circular"
        self.herramienta = "lapiz"

        self.fuente_texto = QFont("Sans Serif", 20)
        self.editor_texto = None

        # Configuraciones de Borde y Sombra/Halo
        self.config_borde = {'activo': False, 'grosor': 2, 'color': self.color_secundario}
        self.config_sombra = {'activo': False, 'vec_x': 0.5, 'vec_y': 0.5, 'dist': 6}

        # Selección
        self.rect_seleccion = None
        self.imagen_seleccionada = None
        self.punto_inicio_sel = None
        self.modo_transformacion = None
        self.offset_mover = QPoint()
        self.rect_original_transform = None

    def cargar_imagen(self, ruta):
        imagen_temporal = QImage(ruta)
        if imagen_temporal.isNull(): return False
        self.capa_activa = imagen_temporal.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp = QImage(self.capa_activa.width(), self.capa_activa.height(), QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)
        self.setFixedSize(self.capa_activa.width(), self.capa_activa.height())
        self.fijar_seleccion_flotante()
        self.update()
        return True

    def guardar_imagen(self, ruta):
        self.fijar_texto_si_existe()
        self.fijar_seleccion_flotante()
        return self.capa_activa.save(ruta)

    def fijar_seleccion_flotante(self):
        if self.imagen_seleccionada and self.rect_seleccion:
            painter = QPainter(self.capa_activa)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.drawImage(self.rect_seleccion, self.imagen_seleccionada)
            painter.end()
            self.imagen_seleccionada = None
            self.rect_seleccion = None
            self.update()

    def extraer_píxeles_seleccionados(self):
        if self.rect_seleccion and not self.rect_seleccion.isEmpty() and not self.imagen_seleccionada:
            self.imagen_seleccionada = self.capa_activa.copy(self.rect_seleccion)
            painter = QPainter(self.capa_activa)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(self.rect_seleccion, Qt.GlobalColor.transparent)
            painter.end()

    def copiar_seleccion(self):
        if not self.rect_seleccion or self.rect_seleccion.isEmpty(): return
        sub_img = self.imagen_seleccionada if self.imagen_seleccionada else self.capa_activa.copy(self.rect_seleccion)
        QApplication.clipboard().setImage(sub_img)

    def cortar_seleccion(self):
        if not self.rect_seleccion or self.rect_seleccion.isEmpty(): return
        self.copiar_seleccion()
        self.imagen_seleccionada = None
        self.rect_seleccion = None
        self.update()

    def borrar_seleccion(self):
        if not self.rect_seleccion or self.rect_seleccion.isEmpty(): return
        if not self.imagen_seleccionada:
            painter = QPainter(self.capa_activa)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(self.rect_seleccion, Qt.GlobalColor.transparent)
            painter.end()
        self.imagen_seleccionada = None
        self.rect_seleccion = None
        self.update()

    def pegar_portapapeles(self):
        self.fijar_seleccion_flotante()
        img = QApplication.clipboard().image()
        if not img.isNull():
            self.imagen_seleccionada = img.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
            self.rect_seleccion = QRect(0, 0, img.width(), img.height())
            self.herramienta = "seleccion"
            self.update()

    def aplicar_balde(self, x, y, color_a_usar):
        self.fijar_seleccion_flotante()
        ancho = self.capa_activa.width()
        alto = self.capa_activa.height()
        ptr = self.capa_activa.bits()
        ptr.setsize(alto * ancho * 4)
        arr = np.frombuffer(ptr, np.uint8).reshape((alto, ancho, 4))

        color_con_alfa = QColor(color_a_usar)
        color_con_alfa.setAlpha(self.opacidad_pincel)

        b, g, r, a = color_con_alfa.blue(), color_con_alfa.green(), color_con_alfa.red(), color_con_alfa.alpha()
        img_rgb = np.ascontiguousarray(arr[:, :, :3])
        mask = np.zeros((alto + 2, ancho + 2), dtype=np.uint8)

        cv2.floodFill(img_rgb, mask, (x, y), (b, g, r), flags=4 | (255 << 8) | cv2.FLOODFILL_FIXED_RANGE)

        region_rellenada = mask[1:alto+1, 1:ancho+1] > 0
        arr[region_rellenada, :3] = img_rgb[region_rellenada]
        arr[region_rellenada, 3] = a
        self.update()

    def renderizar_efectos_texto(self, painter, pos_x, pos_y, texto, fuente):
        """Renderiza Halo/Resplandor MÁS OSCURO Y DEFINIDO, Borde y Texto Principal"""
        path = QPainterPath()
        path.addText(QPointF(pos_x, pos_y), fuente, texto)

        # 1. RESPLANDOR / HALO SUAVE (MÁS OSCURO Y INTENSO)
        if self.config_sombra.get('activo', False):
            radio_ext = self.config_sombra.get('dist', 6)
            vx = self.config_sombra.get('vec_x', 0.5)
            vy = self.config_sombra.get('vec_y', 0.5)

            centro_off_x = vx * radio_ext
            centro_off_y = vy * radio_ext

            # Aumentamos opacidad por pasada para un halo más oscuro
            pasadas = max(4, int(radio_ext))
            for i in range(pasadas, 0, -1):
                radio_pasada = (i / float(pasadas)) * radio_ext
                opacidad_pasada = 0.22 / (i * 0.3 + 1.0) # Halo más denso/oscuro

                ox = pos_x + (centro_off_x * (i / float(pasadas)))
                oy = pos_y + (centro_off_y * (i / float(pasadas)))

                path_halo = QPainterPath()
                path_halo.addText(QPointF(ox, oy), fuente, texto)

                pen_halo = QPen(QColor(0, 0, 0, int(255 * opacidad_pasada)), radio_pasada * 2.2,
                                Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                
                painter.setPen(pen_halo)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(path_halo)

        # 2. BORDE (OUTLINE VECTORIAL)
        if self.config_borde.get('activo', False):
            grosor = self.config_borde.get('grosor', 2)
            # Usamos el color secundario actualizado en vivo
            color_borde = self.color_secundario if self.config_borde.get('color') is None else self.config_borde.get('color')

            color_borde_alfa = QColor(color_borde)
            color_borde_alfa.setAlpha(self.opacidad_pincel)

            pen_borde = QPen(color_borde_alfa, grosor, Qt.PenStyle.SolidLine,
                             Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen_borde)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

        # 3. TEXTO PRINCIPAL RELLENO CON TRANSPARENCIA REAL
        color_texto_alfa = QColor(self.color_actual_uso)
        color_texto_alfa.setAlpha(self.opacidad_pincel)
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color_texto_alfa)
        painter.drawPath(path)

    def fijar_texto_si_existe(self):
        if self.editor_texto:
            texto = self.editor_texto.input_texto.text().strip()
            if texto:
                painter = QPainter(self.capa_activa)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

                fm = QFontMetrics(self.editor_texto.fuente)
                pos_x = self.editor_texto.x() + 4
                pos_y = self.editor_texto.y() + fm.ascent() + 4

                self.renderizar_efectos_texto(painter, pos_x, pos_y, texto, self.editor_texto.fuente)
                painter.end()

            self.editor_texto.deleteLater()
            self.editor_texto = None
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Fondo ajedrez
        tamano_cuadro = 16
        for y in range(0, self.height(), tamano_cuadro):
            for x in range(0, self.width(), tamano_cuadro):
                color = QColor(200, 200, 200) if (x // tamano_cuadro + y // tamano_cuadro) % 2 == 0 else QColor(255, 255, 255)
                painter.fillRect(x, y, tamano_cuadro, tamano_cuadro, color)
                
        painter.drawImage(0, 0, self.capa_activa)

        # Capa de dibujo de trazo temporal (Mezclada con Alpha Puro)
        if not self.capa_trazo_temp.isNull():
            painter.drawImage(0, 0, self.capa_trazo_temp)

        # PREVIEW EN VIVO DEL TEXTO EDITÁNDOSE
        if self.editor_texto:
            texto = self.editor_texto.input_texto.text().strip()
            if texto:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                fm = QFontMetrics(self.editor_texto.fuente)
                pos_x = self.editor_texto.x() + 4
                pos_y = self.editor_texto.y() + fm.ascent() + 4
                self.renderizar_efectos_texto(painter, pos_x, pos_y, texto, self.editor_texto.fuente)

        # Capa flotante de la selección
        if self.imagen_seleccionada and self.rect_seleccion:
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.drawImage(self.rect_seleccion, self.imagen_seleccionada)

        # Manijas de Selección
        if self.rect_seleccion and not self.rect_seleccion.isEmpty():
            pen_negro = QPen(Qt.GlobalColor.black, 1, Qt.PenStyle.DashLine)
            pen_blanco = QPen(Qt.GlobalColor.white, 1, Qt.PenStyle.SolidLine)
            
            painter.setPen(pen_blanco)
            painter.drawRect(self.rect_seleccion)
            painter.setPen(pen_negro)
            painter.drawRect(self.rect_seleccion)

            if self.herramienta == "seleccion":
                r = self.rect_seleccion
                puntos = [
                    r.topLeft(), r.topRight(), r.bottomLeft(), r.bottomRight(),
                    QPoint(r.center().x(), r.top()), QPoint(r.center().x(), r.bottom()),
                    QPoint(r.left(), r.center().y()), QPoint(r.right(), r.center().y())
                ]
                painter.setBrush(Qt.GlobalColor.white)
                painter.setPen(QPen(Qt.GlobalColor.black, 1))
                for p in puntos:
                    painter.drawRect(p.x() - 3, p.y() - 3, 6, 6)

    def obtener_zona_grip(self, pos):
        if not self.rect_seleccion or self.rect_seleccion.isEmpty(): return None
        r = self.rect_seleccion
        m = self.MARGEN_GRIP

        if QRect(r.left() - m, r.top() - m, m * 2, m * 2).contains(pos): return "top-left"
        if QRect(r.right() - m, r.top() - m, m * 2, m * 2).contains(pos): return "top-right"
        if QRect(r.left() - m, r.bottom() - m, m * 2, m * 2).contains(pos): return "bottom-left"
        if QRect(r.right() - m, r.bottom() - m, m * 2, m * 2).contains(pos): return "bottom-right"

        if abs(pos.y() - r.top()) <= m and r.left() <= pos.x() <= r.right(): return "top"
        if abs(pos.y() - r.bottom()) <= m and r.left() <= pos.x() <= r.right(): return "bottom"
        if abs(pos.x() - r.left()) <= m and r.top() <= pos.y() <= r.bottom(): return "left"
        if abs(pos.x() - r.right()) <= m and r.top() <= pos.y() <= r.bottom(): return "right"

        if r.contains(pos): return "mover"
        return None

    def actualizar_cursor_mouse(self, pos):
        if self.herramienta != "seleccion":
            self.setCursor(Qt.CursorShape.CrossCursor)
            return

        zona = self.obtener_zona_grip(pos)
        if zona == "mover": self.setCursor(Qt.CursorShape.SizeAllCursor)
        elif zona in ("top-left", "bottom-right"): self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif zona in ("top-right", "bottom-left"): self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif zona in ("top", "bottom"): self.setCursor(Qt.CursorShape.SizeVerCursor)
        elif zona in ("left", "right"): self.setCursor(Qt.CursorShape.SizeHorCursor)
        else: self.setCursor(Qt.CursorShape.CrossCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.color_actual_uso = self.color_principal
        elif event.button() == Qt.MouseButton.RightButton:
            self.color_actual_uso = self.color_secundario
        else: return

        pos = event.pos()
        pos_f = QPointF(pos)

        if self.editor_texto:
            rect_editor = self.editor_texto.geometry()
            if not rect_editor.contains(pos):
                self.fijar_texto_si_existe()
                if self.herramienta != "texto": return

        self.ultimo_punto = pos
        
        self.trayectoria_actual = QPainterPath()
        self.trayectoria_actual.moveTo(pos_f)

        if self.herramienta == "seleccion":
            zona = self.obtener_zona_grip(pos)
            if zona:
                self.extraer_píxeles_seleccionados()
                self.modo_transformacion = zona
                self.punto_inicio_sel = pos
                self.rect_original_transform = QRect(self.rect_seleccion)
                if zona == "mover":
                    self.offset_mover = pos - self.rect_seleccion.topLeft()
            else:
                self.fijar_seleccion_flotante()
                self.modo_transformacion = "crear"
                self.punto_inicio_sel = pos
                self.rect_seleccion = QRect(pos, pos)
            self.update()

        elif self.herramienta == "balde":
            self.fijar_seleccion_flotante()
            self.aplicar_balde(pos.x(), pos.y(), self.color_actual_uso)
        elif self.herramienta == "texto":
            self.fijar_seleccion_flotante()
            if not self.editor_texto:
                from herramientas.panel_texto import CajaTextoInteractiva
                self.editor_texto = CajaTextoInteractiva(
                    self, pos.x(), pos.y(), self.color_actual_uso, self.fuente_texto, 
                    self.config_borde, self.config_sombra
                )
        else:
            self.fijar_seleccion_flotante()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        pos_f = QPointF(pos)
        self.actualizar_cursor_mouse(pos)

        if not (event.buttons() & (Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton)):
            return

        if self.herramienta == "seleccion" and self.modo_transformacion:
            if self.modo_transformacion == "crear":
                self.rect_seleccion = QRect(self.punto_inicio_sel, pos).normalized()
            elif self.modo_transformacion == "mover":
                self.rect_seleccion.moveTo(pos - self.offset_mover)
            else:
                r = QRect(self.rect_original_transform)
                left, top, right, bottom = r.left(), r.top(), r.right(), r.bottom()

                if "left" in self.modo_transformacion: left = pos.x()
                if "right" in self.modo_transformacion: right = pos.x()
                if "top" in self.modo_transformacion: top = pos.y()
                if "bottom" in self.modo_transformacion: bottom = pos.y()

                ancho = right - left
                alto = bottom - top

                if (event.modifiers() & Qt.KeyboardModifier.ShiftModifier) and r.width() > 0 and r.height() > 0:
                    aspect_ratio = r.width() / float(r.height())
                    if abs(ancho) > abs(alto): alto = int(ancho / aspect_ratio)
                    else: ancho = int(alto * aspect_ratio)

                self.rect_seleccion = QRect(left, top, ancho, alto).normalized()

            self.update()

        elif self.herramienta == "lapiz" and self.ultimo_punto:
            painter = QPainter(self.capa_trazo_temp)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            cap = Qt.PenCapStyle.SquareCap if self.forma_pincel == "Cuadrado" else Qt.PenCapStyle.RoundCap

            alfa_seguro = max(0, min(255, int(self.opacidad_pincel)))
            color_uso = QColor(self.color_actual_uso)
            color_uso.setAlpha(alfa_seguro)

            pen = QPen(color_uso, self.grosor_pincel, Qt.PenStyle.SolidLine, cap, Qt.PenJoinStyle.MiterJoin)
            painter.setPen(pen)
            painter.drawLine(self.ultimo_punto, pos)
            painter.end()
            self.ultimo_punto = pos
            self.update()

        elif self.herramienta == "pincel" and self.ultimo_punto:
            self.trayectoria_actual.lineTo(pos_f)

            self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)
            painter = QPainter(self.capa_trazo_temp)

            if self.suavizado_pincel > 0:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                painter.setRenderHint(QPainter.RenderHint.VerticalSubpixelPositioning, True)

            cap = Qt.PenCapStyle.SquareCap if self.forma_pincel == "Cuadrado" else Qt.PenCapStyle.RoundCap
            join = Qt.PenJoinStyle.MiterJoin if self.forma_pincel == "Cuadrado" else Qt.PenJoinStyle.RoundJoin

            alfa_seguro = max(0, min(255, int(self.opacidad_pincel)))
            color_uso = QColor(self.color_actual_uso)
            color_uso.setAlpha(alfa_seguro)

            pen = QPen(color_uso, self.grosor_pincel, Qt.PenStyle.SolidLine, cap, join)
            painter.setPen(pen)

            painter.drawPath(self.trayectoria_actual)
            painter.end()

            self.ultimo_punto = pos
            self.update()

        elif self.herramienta == "goma" and self.ultimo_punto:
            painter = QPainter(self.capa_activa)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            cap = Qt.PenCapStyle.SquareCap if self.forma_pincel == "Cuadrado" else Qt.PenCapStyle.RoundCap
            pen = QPen(Qt.GlobalColor.transparent, self.grosor_pincel, Qt.PenStyle.SolidLine, cap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self.ultimo_punto, pos)
            painter.end()
            self.ultimo_punto = pos
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            if self.herramienta in ("lapiz", "pincel"):
                painter = QPainter(self.capa_activa)
                # Volcamos la capa de trazo a la activa preservando la transparencia alfa real
                painter.drawImage(0, 0, self.capa_trazo_temp)
                painter.end()
                self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

            self.modo_transformacion = None
            self.ultimo_punto = None
            self.trayectoria_actual = None
            self.update()
