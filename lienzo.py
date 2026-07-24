import numpy as np
import cv2
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QImage, QColor, QPen, QFont, QFontMetrics
from PyQt6.QtCore import Qt
from herramientas.panel_texto import CajaTextoInteractiva

class Lienzo(QWidget):
    def __init__(self, ancho, alto):
        super().__init__()
        self.setFixedSize(ancho, alto)

        self.capa_activa = QImage(ancho, alto, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_activa.fill(Qt.GlobalColor.transparent)

        self.capa_trazo_temp = QImage(ancho, alto, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

        self.ultimo_punto = None
        self.color_principal = QColor(255, 50, 50)
        self.color_secundario = QColor(255, 255, 255)
        self.color_actual_uso = self.color_principal
        
        self.grosor_pincel = 4
        self.opacidad_pincel = 255
        self.herramienta = "lapiz"

        self.fuente_texto = QFont("Sans Serif", 20)
        self.editor_texto = None

    def cargar_imagen(self, ruta):
        imagen_temporal = QImage(ruta)
        if imagen_temporal.isNull(): return False
        self.capa_activa = imagen_temporal.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp = QImage(self.capa_activa.width(), self.capa_activa.height(), QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)
        self.setFixedSize(self.capa_activa.width(), self.capa_activa.height())
        self.update()
        return True

    def guardar_imagen(self, ruta):
        self.fijar_texto_si_existe()
        return self.capa_activa.save(ruta)

    def aplicar_balde(self, x, y, color_a_usar):
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

    def fijar_texto_si_existe(self):
        if self.editor_texto:
            texto = self.editor_texto.input_texto.text().strip()
            if texto:
                painter = QPainter(self.capa_activa)
                painter.setFont(self.editor_texto.fuente)
                
                color_con_alfa = QColor(self.color_actual_uso)
                color_con_alfa.setAlpha(self.opacidad_pincel)
                painter.setPen(color_con_alfa)

                fm = QFontMetrics(self.editor_texto.fuente)
                pos_x = self.editor_texto.x() + 4
                pos_y = self.editor_texto.y() + fm.ascent() + 4

                painter.drawText(pos_x, pos_y, texto)
                painter.end()

            self.editor_texto.deleteLater()
            self.editor_texto = None
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
            painter.setOpacity(self.opacidad_pincel / 255.0)
            painter.drawImage(0, 0, self.capa_trazo_temp)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.color_actual_uso = self.color_principal
        elif event.button() == Qt.MouseButton.RightButton:
            self.color_actual_uso = self.color_secundario
        else:
            return

        pos = event.pos()

        if self.editor_texto:
            rect_editor = self.editor_texto.geometry()
            if not rect_editor.contains(pos):
                self.fijar_texto_si_existe()
                if self.herramienta != "texto":
                    return

        self.ultimo_punto = pos
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

        if self.herramienta == "balde":
            self.aplicar_balde(pos.x(), pos.y(), self.color_actual_uso)
        elif self.herramienta == "texto":
            if not self.editor_texto:
                self.editor_texto = CajaTextoInteractiva(self, pos.x(), pos.y(), self.color_actual_uso, self.fuente_texto)

    def mouseMoveEvent(self, event):
        if (event.buttons() & (Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton)) and self.ultimo_punto:
            if self.herramienta == "lapiz":
                painter = QPainter(self.capa_trazo_temp)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                
                pen = QPen(self.color_actual_uso, self.grosor_pincel, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                painter.drawLine(self.ultimo_punto, event.pos())
                painter.end()
                
                self.ultimo_punto = event.pos()

            elif self.herramienta == "goma":
                painter = QPainter(self.capa_activa)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                pen = QPen(Qt.GlobalColor.transparent, self.grosor_pincel, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                painter.drawLine(self.ultimo_punto, event.pos())
                painter.end()
                self.ultimo_punto = event.pos()

            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            if self.herramienta == "lapiz":
                painter = QPainter(self.capa_activa)
                painter.setOpacity(self.opacidad_pincel / 255.0)
                painter.drawImage(0, 0, self.capa_trazo_temp)
                painter.end()
                
                self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

            self.ultimo_punto = None
            self.update()
