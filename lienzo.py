import math
import numpy as np
import cv2
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QImage, QColor, QPen, QFont, QFontMetrics, QPainterPath, QTransform
from PyQt6.QtCore import Qt, QRect, QRectF, QPoint, QPointF


class Lienzo(QWidget):
    MARGEN_GRIP = 8
    MAX_HISTORIAL = 30

    def __init__(self, ancho, alto):
        super().__init__()
        self.setFixedSize(ancho, alto)
        self.setMouseTracking(True)

        self.capa_activa = QImage(ancho, alto, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_activa.fill(Qt.GlobalColor.transparent)

        self.capa_trazo_temp = QImage(ancho, alto, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

        # Selección y Transformación
        self.rect_seleccion = None
        self.imagen_seleccionada = None
        self.angulo_rotacion_sel = 0.0
        self.punto_inicio_sel = None
        self.modo_transformacion = None
        self.offset_mover = QPoint()
        self.rect_original_transform = None
        self.angulo_inicio_rot = 0.0

        # Historial de Undo / Redo
        self.historial_undo = []
        self.historial_redo = []
        self.guardar_estado_historial()

        self.ultimo_punto = None
        self.trayectoria_actual = None

        self.color_principal = QColor(0, 0, 0)
        self.color_secundario = QColor(255, 255, 255)
        self.color_actual_uso = self.color_principal

        self.grosor_pincel = 4
        self.opacidad_pincel = 255
        self.suavizado_pincel = 100
        self.forma_pincel = "Circular"
        self.herramienta = "lapiz"

        self.fuente_texto = QFont("Sans Serif", 20)
        self.editor_texto = None
        self.callback_modificado = None

        self.config_borde = {'activo': False, 'grosor': 2, 'color': self.color_secundario}
        self.config_sombra = {'activo': False, 'vec_x': 0.5, 'vec_y': 0.5, 'dist': 6}

    # --- HISTORIAL (UNDO / REDO) ---
    def guardar_estado_historial(self):
        """Guarda la capa activa Y el estado completo de la selección flotante"""
        rect_copy = QRect(self.rect_seleccion) if self.rect_seleccion else None
        img_copy = self.imagen_seleccionada.copy() if self.imagen_seleccionada else None

        estado = {
            'capa': self.capa_activa.copy(),
            'rect_sel': rect_copy,
            'img_sel': img_copy,
            'angulo_sel': self.angulo_rotacion_sel
        }
        self.historial_undo.append(estado)
        if len(self.historial_undo) > self.MAX_HISTORIAL:
            self.historial_undo.pop(0)
        self.historial_redo.clear()

    def deshacer(self):
        if self.editor_texto:
            self.editor_texto.deleteLater()
            self.editor_texto = None

        if len(self.historial_undo) > 1:
            estado_actual = self.historial_undo.pop()
            self.historial_redo.append(estado_actual)

            estado_previo = self.historial_undo[-1]
            self.capa_activa = estado_previo['capa'].copy()
            self.rect_seleccion = QRect(estado_previo['rect_sel']) if estado_previo['rect_sel'] else None
            self.imagen_seleccionada = estado_previo['img_sel'].copy() if estado_previo['img_sel'] else None
            self.angulo_rotacion_sel = estado_previo['angulo_sel']

            if self.capa_activa.size() != self.size():
                self.setFixedSize(self.capa_activa.size())

            if self.rect_seleccion:
                self.herramienta = "seleccion"

            if hasattr(self, 'callback_modificado') and self.callback_modificado:
                self.callback_modificado()
            self.update()

    def rehacer(self):
        if self.editor_texto:
            self.editor_texto.deleteLater()
            self.editor_texto = None

        if self.historial_redo:
            estado_siguiente = self.historial_redo.pop()
            self.historial_undo.append(estado_siguiente)

            self.capa_activa = estado_siguiente.copy()
            self.rect_seleccion = QRect(estado_siguiente['rect_sel']) if estado_siguiente['rect_sel'] else None
            self.imagen_seleccionada = estado_siguiente['img_sel'].copy() if estado_siguiente['img_sel'] else None
            self.angulo_rotacion_sel = estado_siguiente['angulo_sel']

            if self.capa_activa.size() != self.size():
                self.setFixedSize(self.capa_activa.size())

            if self.rect_seleccion:
                self.herramienta = "seleccion"

            if hasattr(self, 'callback_modificado') and self.callback_modificado:
                self.callback_modificado()
            self.update()

    # --- FUNCIONES DE MENU IMAGEN ---
    def redimensionar_lienzo(self, nuevo_ancho, nuevo_alto):
        self.fijar_texto_si_existe()
        self.fijar_seleccion_flotante()

        nueva_capa = QImage(nuevo_ancho, nuevo_alto, QImage.Format.Format_ARGB32_Premultiplied)
        es_transparente = self.capa_activa.hasAlphaChannel() and (self.capa_activa.pixelColor(0, 0).alpha() == 0)
        if es_transparente:
            nueva_capa.fill(Qt.GlobalColor.transparent)
        else:
            nueva_capa.fill(Qt.GlobalColor.white)

        painter = QPainter(nueva_capa)
        painter.drawImage(0, 0, self.capa_activa)
        painter.end()

        self.capa_activa = nueva_capa
        self.capa_trazo_temp = QImage(nuevo_ancho, nuevo_alto, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)
        self.setFixedSize(nuevo_ancho, nuevo_alto)

        self.guardar_estado_historial()

        if hasattr(self, 'callback_modificado') and self.callback_modificado:
            self.callback_modificado()
        self.update()

    def escalar_imagen(self, nuevo_ancho, nuevo_alto):
        self.fijar_texto_si_existe()
        self.fijar_seleccion_flotante()

        self.capa_activa = self.capa_activa.scaled(
            nuevo_ancho, nuevo_alto,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.capa_trazo_temp = QImage(nuevo_ancho, nuevo_alto, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)
        self.setFixedSize(nuevo_ancho, nuevo_alto)

        self.guardar_estado_historial()

        if hasattr(self, 'callback_modificado') and self.callback_modificado:
            self.callback_modificado()
        self.update()

    def voltear_contenido(self, horizontal=True):
        if self.rect_seleccion and not self.rect_seleccion.isEmpty():
            self.extraer_píxeles_seleccionados()
            if self.imagen_seleccionada:
                self.imagen_seleccionada = self.imagen_seleccionada.mirrored(horizontal, not horizontal)
        else:
            self.fijar_texto_si_existe()
            self.capa_activa = self.capa_activa.mirrored(horizontal, not horizontal)

        self.guardar_estado_historial()

        if hasattr(self, 'callback_modificado') and self.callback_modificado:
            self.callback_modificado()
        self.update()

    def rotar_contenido(self, grados):
        if self.rect_seleccion and not self.rect_seleccion.isEmpty():
            self.extraer_píxeles_seleccionados()
            if self.imagen_seleccionada:
                t = QTransform().rotate(grados)
                self.imagen_seleccionada = self.imagen_seleccionada.transformed(t, Qt.TransformationMode.SmoothTransformation)
                centro = self.rect_seleccion.center()
                self.rect_seleccion = QRect(0, 0, self.imagen_seleccionada.width(), self.imagen_seleccionada.height())
                self.rect_seleccion.moveCenter(centro)
        else:
            self.fijar_texto_si_existe()
            t = QTransform().rotate(grados)
            self.capa_activa = self.capa_activa.transformed(t, Qt.TransformationMode.SmoothTransformation)
            self.setFixedSize(self.capa_activa.width(), self.capa_activa.height())
            self.capa_trazo_temp = QImage(self.capa_activa.width(), self.capa_activa.height(), QImage.Format.Format_ARGB32_Premultiplied)
            self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

        self.guardar_estado_historial()

        if hasattr(self, 'callback_modificado') and self.callback_modificado:
            self.callback_modificado()
        self.update()

    # --- SELECCIÓN Y TEXTO ---
    def seleccionar_todo(self):
        self.fijar_texto_si_existe()
        self.fijar_seleccion_flotante()
        self.rect_seleccion = QRect(0, 0, self.capa_activa.width(), self.capa_activa.height())
        self.herramienta = "seleccion"
        self.extraer_píxeles_seleccionados()
        self.guardar_estado_historial()
        self.update()

    def borrar_todo(self):
        self.fijar_texto_si_existe()
        self.fijar_seleccion_flotante()

        self.capa_activa.fill(Qt.GlobalColor.transparent)
        self.guardar_estado_historial()

        if hasattr(self, 'callback_modificado') and self.callback_modificado:
            self.callback_modificado()
        self.update()

    def crear_nuevo_lienzo(self, ancho, alto, es_transparente=False):
        self.fijar_texto_si_existe()
        self.fijar_seleccion_flotante()

        self.capa_activa = QImage(ancho, alto, QImage.Format.Format_ARGB32_Premultiplied)
        if es_transparente:
            self.capa_activa.fill(Qt.GlobalColor.transparent)
        else:
            self.capa_activa.fill(Qt.GlobalColor.white)

        self.capa_trazo_temp = QImage(ancho, alto, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

        self.historial_undo.clear()
        self.historial_redo.clear()
        self.guardar_estado_historial()

        self.setFixedSize(ancho, alto)
        self.update()

    def cargar_imagen(self, ruta):
        imagen_temporal = QImage(ruta)
        if imagen_temporal.isNull(): return False
        self.capa_activa = imagen_temporal.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp = QImage(self.capa_activa.width(), self.capa_activa.height(), QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)
        self.setFixedSize(self.capa_activa.width(), self.capa_activa.height())

        self.historial_undo.clear()
        self.historial_redo.clear()
        self.guardar_estado_historial()

        self.fijar_seleccion_flotante()
        self.update()
        return True

    def insertar_imagen(self, ruta):
        self.fijar_texto_si_existe()
        self.fijar_seleccion_flotante()

        img_temp = QImage(ruta)
        if img_temp.isNull():
            return False

        img = img_temp.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
        ancho_lienzo, alto_lienzo = self.capa_activa.width(), self.capa_activa.height()
        ancho_img, alto_img = img.width(), img.height()

        if ancho_img > ancho_lienzo or alto_img > alto_lienzo:
            img = img.scaled(ancho_lienzo, alto_lienzo, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            ancho_img, alto_img = img.width(), img.height()

        pos_x = (ancho_lienzo - ancho_img) // 2
        pos_y = (alto_lienzo - alto_img) // 2

        self.imagen_seleccionada = img
        self.rect_seleccion = QRect(pos_x, pos_y, ancho_img, alto_img)
        self.angulo_rotacion_sel = 0.0
        self.herramienta = "seleccion"

        self.guardar_estado_historial()

        if hasattr(self, 'callback_modificado') and self.callback_modificado:
            self.callback_modificado()

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
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            if abs(self.angulo_rotacion_sel) > 0.01:
                centro = QPointF(self.rect_seleccion.center())
                painter.translate(centro)
                painter.rotate(self.angulo_rotacion_sel)
                r_local = QRectF(-self.rect_seleccion.width()/2.0, -self.rect_seleccion.height()/2.0,
                                 self.rect_seleccion.width(), self.rect_seleccion.height())
                painter.drawImage(r_local, self.imagen_seleccionada)
            else:
                painter.drawImage(self.rect_seleccion, self.imagen_seleccionada)
            painter.end()

        self.imagen_seleccionada = None
        self.rect_seleccion = None
        self.angulo_rotacion_sel = 0.0
        if hasattr(self, 'callback_modificado') and self.callback_modificado:
            self.callback_modificado()
        self.update()

    def extraer_píxeles_seleccionados(self):
        if self.rect_seleccion and not self.rect_seleccion.isEmpty() and self.imagen_seleccionada is None:
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

        if not self.imagen_seleccionada:
            painter = QPainter(self.capa_activa)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(self.rect_seleccion, Qt.GlobalColor.transparent)
            painter.end()

        self.imagen_seleccionada = None
        self.rect_seleccion = None
        self.angulo_rotacion_sel = 0.0

        self.guardar_estado_historial()

        if hasattr(self, 'callback_modificado') and self.callback_modificado:
            self.callback_modificado()
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
        self.angulo_rotacion_sel = 0.0

        self.guardar_estado_historial()

        if hasattr(self, 'callback_modificado') and self.callback_modificado:
            self.callback_modificado()
        self.update()

    def pegar_portapapeles(self):
        self.fijar_seleccion_flotante()
        img = QApplication.clipboard().image()
        if not img.isNull():
            img_format = img.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
            rect_dest = QRect(0, 0, img_format.width(), img_format.height())

            self.imagen_seleccionada = img_format
            self.rect_seleccion = rect_dest
            self.angulo_rotacion_sel = 0.0
            self.herramienta = "seleccion"

            self.guardar_estado_historial()

            if hasattr(self, 'callback_modificado') and self.callback_modificado:
                self.callback_modificado()
            self.update()

    def aplicar_balde(self, x, y, color_a_usar):
        if self.rect_seleccion and not self.rect_seleccion.contains(x, y):
            return

        color_con_alfa = QColor(color_a_usar)
        color_con_alfa.setAlpha(self.opacidad_pincel)

        if self.rect_seleccion and not self.rect_seleccion.isEmpty():
            r_sel = self.rect_seleccion.normalized()
            if self.imagen_seleccionada:
                self.fijar_seleccion_flotante()

            painter = QPainter(self.capa_activa)
            painter.setClipRect(r_sel)
            painter.fillRect(r_sel, color_con_alfa)
            painter.end()
        else:
            ancho, alto = self.capa_activa.width(), self.capa_activa.height()
            ptr = self.capa_activa.bits()
            ptr.setsize(alto * ancho * 4)
            arr = np.frombuffer(ptr, np.uint8).reshape((alto, ancho, 4))

            b, g, r, a = color_con_alfa.blue(), color_con_alfa.green(), color_con_alfa.red(), color_con_alfa.alpha()
            img_rgb = np.ascontiguousarray(arr[:, :, :3])
            mask = np.zeros((alto + 2, ancho + 2), dtype=np.uint8)

            cv2.floodFill(img_rgb, mask, (x, y), (int(b), int(g), int(r)), flags=4)

            region = mask[1:alto+1, 1:ancho+1] == 1
            arr[region, :3] = img_rgb[region]
            arr[region, 3] = a

        self.guardar_estado_historial()

        if hasattr(self, 'callback_modificado') and self.callback_modificado:
            self.callback_modificado()
        self.update()

    def renderizar_efectos_texto(self, painter, pos_x, pos_y, texto, fuente):
        path = QPainterPath()
        path.addText(QPointF(pos_x, pos_y), fuente, texto)

        if self.config_sombra.get('activo', False):
            radio_ext = self.config_sombra.get('dist', 6)
            vx, vy = self.config_sombra.get('vec_x', 0.5), self.config_sombra.get('vec_y', 0.5)
            centro_off_x, centro_off_y = vx * radio_ext, vy * radio_ext
            pasadas = max(4, int(radio_ext))
            for i in range(pasadas, 0, -1):
                radio_pasada = (i / float(pasadas)) * radio_ext
                opacidad_pasada = 0.22 / (i * 0.3 + 1.0)
                ox = pos_x + (centro_off_x * (i / float(pasadas)))
                oy = pos_y + (centro_off_y * (i / float(pasadas)))
                path_halo = QPainterPath()
                path_halo.addText(QPointF(ox, oy), fuente, texto)
                pen_halo = QPen(QColor(0, 0, 0, int(255 * opacidad_pasada)), radio_pasada * 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen_halo)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(path_halo)

        if self.config_borde.get('activo', False):
            grosor = self.config_borde.get('grosor', 2)
            color_borde = self.config_borde.get('color', self.color_secundario)
            color_borde_alfa = QColor(color_borde)
            color_borde_alfa.setAlpha(max(0, min(255, int(self.opacidad_pincel))))
            pen_borde = QPen(color_borde_alfa, grosor, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen_borde)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

        color_texto_alfa = QColor(self.color_actual_uso)
        color_texto_alfa.setAlpha(max(0, min(255, int(self.opacidad_pincel))))
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

                self.guardar_estado_historial()

                if hasattr(self, 'callback_modificado') and self.callback_modificado:
                    self.callback_modificado()

            self.editor_texto.deleteLater()
            self.editor_texto = None
            self.update()

    def cancelar_o_deseleccionar(self):
        if self.editor_texto:
            self.fijar_texto_si_existe()
        elif self.rect_seleccion:
            self.fijar_seleccion_flotante()
            self.rect_seleccion = None
            self.imagen_seleccionada = None
            self.angulo_rotacion_sel = 0.0
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        tamano_cuadro = 16
        for y in range(0, self.height(), tamano_cuadro):
            for x in range(0, self.width(), tamano_cuadro):
                color = QColor(200, 200, 200) if (x // tamano_cuadro + y // tamano_cuadro) % 2 == 0 else QColor(255, 255, 255)
                painter.fillRect(x, y, tamano_cuadro, tamano_cuadro, color)

        painter.drawImage(0, 0, self.capa_activa)

        if not self.capa_trazo_temp.isNull():
            painter.drawImage(0, 0, self.capa_trazo_temp)

        if self.editor_texto:
            texto = self.editor_texto.input_texto.text().strip()
            if texto:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                fm = QFontMetrics(self.editor_texto.fuente)
                pos_x = self.editor_texto.x() + 4
                pos_y = self.editor_texto.y() + fm.ascent() + 4
                self.renderizar_efectos_texto(painter, pos_x, pos_y, texto, self.editor_texto.fuente)

        # Dibujar Selección y Transformación
        if self.rect_seleccion and not self.rect_seleccion.isEmpty():
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            centro = QPointF(self.rect_seleccion.center())
            if abs(self.angulo_rotacion_sel) > 0.01:
                painter.translate(centro)
                painter.rotate(self.angulo_rotacion_sel)
                r_local = QRectF(-self.rect_seleccion.width()/2.0, -self.rect_seleccion.height()/2.0,
                                 self.rect_seleccion.width(), self.rect_seleccion.height())
                if self.imagen_seleccionada:
                    painter.drawImage(r_local, self.imagen_seleccionada)
            else:
                if self.imagen_seleccionada:
                    painter.drawImage(self.rect_seleccion, self.imagen_seleccionada)

            if abs(self.angulo_rotacion_sel) > 0.01:
                painter.translate(-centro)

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
            painter.restore()

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
        elif zona in ("top-left", "bottom-right", "top-right", "bottom-left"): self.setCursor(Qt.CursorShape.PointingHandCursor)
        elif zona in ("top", "bottom"): self.setCursor(Qt.CursorShape.SizeVerCursor)
        elif zona in ("left", "right"): self.setCursor(Qt.CursorShape.SizeHorCursor)
        else: self.setCursor(Qt.CursorShape.CrossCursor)

    def mousePressEvent(self, event):
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

            if event.button() == Qt.MouseButton.RightButton and zona in ("top-left", "top-right", "bottom-left", "bottom-right"):
                self.extraer_píxeles_seleccionados()
                self.modo_transformacion = "rotar"
                centro = QPointF(self.rect_seleccion.center())
                dx = pos.x() - centro.x()
                dy = pos.y() - centro.y()
                self.angulo_inicio_rot = math.degrees(math.atan2(dy, dx)) - self.angulo_rotacion_sel
                return

            if event.button() == Qt.MouseButton.LeftButton:
                self.color_actual_uso = self.color_principal
            elif event.button() == Qt.MouseButton.RightButton:
                self.color_actual_uso = self.color_secundario

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
                self.angulo_rotacion_sel = 0.0
            self.update()

        elif self.herramienta in ("lapiz", "pincel", "goma"):
            if event.button() == Qt.MouseButton.LeftButton: self.color_actual_uso = self.color_principal
            else: self.color_actual_uso = self.color_secundario
            self.fijar_seleccion_flotante()

        elif self.herramienta == "balde":
            if event.button() == Qt.MouseButton.LeftButton: self.color_actual_uso = self.color_principal
            else: self.color_actual_uso = self.color_secundario
            self.aplicar_balde(pos.x(), pos.y(), self.color_actual_uso)

        elif self.herramienta == "texto":
            if event.button() == Qt.MouseButton.LeftButton: self.color_actual_uso = self.color_principal
            else: self.color_actual_uso = self.color_secundario
            self.fijar_seleccion_flotante()
            if not self.editor_texto:
                from herramientas.panel_texto import CajaTextoInteractiva
                self.editor_texto = CajaTextoInteractiva(
                    self, pos.x(), pos.y(), self.color_actual_uso, self.fuente_texto,
                    self.config_borde, self.config_sombra
                )

    def mouseMoveEvent(self, event):
        pos = event.pos()
        pos_f = QPointF(pos)
        self.actualizar_cursor_mouse(pos)

        if not (event.buttons() & (Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton)):
            return

        if self.herramienta == "seleccion" and self.modo_transformacion:
            if self.modo_transformacion == "rotar":
                centro = QPointF(self.rect_seleccion.center())
                dx = pos.x() - centro.x()
                dy = pos.y() - centro.y()
                angulo_actual = math.degrees(math.atan2(dy, dx))
                self.angulo_rotacion_sel = (angulo_actual - self.angulo_inicio_rot) % 360

            elif self.modo_transformacion == "crear":
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
            if self.herramienta in ("lapiz", "pincel", "goma"):
                painter = QPainter(self.capa_activa)
                painter.drawImage(0, 0, self.capa_trazo_temp)
                painter.end()
                self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)
                self.guardar_estado_historial()

            elif self.herramienta == "seleccion" and self.modo_transformacion:
                # SI SE REESCALÓ DESDE LOS BORDES: Redimensionamos físicamente la imagen interna
                if self.modo_transformacion not in ("mover", "rotar", "crear") and self.imagen_seleccionada:
                    nw = max(1, self.rect_seleccion.width())
                    nh = max(1, self.rect_seleccion.height())
                    self.imagen_seleccionada = self.imagen_seleccionada.scaled(
                        nw, nh,
                        Qt.AspectRatioMode.IgnoreAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )

                if self.modo_transformacion in ("mover", "rotar", "top-left", "top-right", "bottom-left", "bottom-right", "top", "bottom", "left", "right"):
                    self.guardar_estado_historial()

            self.modo_transformacion = None
            self.ultimo_punto = None
            self.trayectoria_actual = None
            if hasattr(self, 'callback_modificado') and self.callback_modificado:
                self.callback_modificado()
            self.update()
