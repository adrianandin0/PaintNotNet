import sys
import math
import numpy as np
import cv2
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QToolBar, QColorDialog, QLabel, QSpinBox, QLineEdit,
                             QScrollArea, QFileDialog, QFontComboBox, QToolButton,
                             QHBoxLayout, QGridLayout, QGroupBox, QFrame, QSlider)
from PyQt6.QtGui import (QPainter, QImage, QColor, QPen, QAction, QFont,
                         QFontMetrics, QIntValidator, QRegularExpressionValidator,
                         QConicalGradient, QRadialGradient, QIcon, QPixmap)
from PyQt6.QtCore import Qt, QPoint, QPointF, QRegularExpression, pyqtSignal

def crear_icono_herramienta(tipo):
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(Qt.GlobalColor.white, 2)
    painter.setPen(pen)

    if tipo == "lapiz":
        painter.drawLine(4, 20, 18, 6)
        painter.drawLine(18, 6, 20, 4)
        painter.drawLine(4, 20, 4, 17)
    elif tipo == "goma":
        painter.drawRoundedRect(4, 8, 16, 10, 2, 2)
        painter.drawLine(12, 8, 12, 18)
    elif tipo == "balde":
        painter.drawRect(5, 10, 12, 10)
        painter.drawLine(5, 10, 11, 4)
        painter.drawLine(17, 10, 11, 4)
    elif tipo == "texto":
        font = QFont("Sans Serif", 14, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "A")
    elif tipo == "seleccion":
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawRect(3, 3, 18, 18)

    painter.end()
    return QIcon(pixmap)


class RuedaColor(QWidget):
    colorCambiado = pyqtSignal(QColor, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(110, 110)
        self.hue = 0.0
        self.sat = 1.0
        self.val = 1.0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        radio = self.width() / 2.0
        centro = QPointF(radio, radio)

        cg = QConicalGradient(centro, 0.0)
        for deg in range(0, 360, 30):
            cg.setColorAt(deg / 360.0, QColor.fromHsvF(deg / 360.0, 1.0, 1.0))
        cg.setColorAt(1.0, QColor.fromHsvF(0.0, 1.0, 1.0))

        painter.setBrush(cg)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self.width(), self.height())

        rg = QRadialGradient(centro, radio)
        rg.setColorAt(0.0, QColor(255, 255, 255, 255))
        rg.setColorAt(1.0, QColor(255, 255, 255, 0))

        painter.setBrush(rg)
        painter.drawEllipse(0, 0, self.width(), self.height())

        angulo_rad = math.radians(self.hue * 360)
        dist = self.sat * radio
        px = int(centro.x() + dist * math.cos(angulo_rad))
        py = int(centro.y() - dist * math.sin(angulo_rad))

        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPoint(px, py), 4, 4)
        painter.setPen(QPen(Qt.GlobalColor.white, 1))
        painter.drawEllipse(QPoint(px, py), 5, 5)

    def mousePressEvent(self, event):
        self.procesar_mouse(event.pos(), event.button())

    def mouseMoveEvent(self, event):
        if event.buttons() & (Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton):
            btn = Qt.MouseButton.LeftButton if (event.buttons() & Qt.MouseButton.LeftButton) else Qt.MouseButton.RightButton
            self.procesar_mouse(event.pos(), btn)

    def procesar_mouse(self, pos, boton):
        radio = self.width() / 2.0
        dx = pos.x() - radio
        dy = radio - pos.y()

        dist = math.sqrt(dx * dx + dy * dy)
        self.sat = min(1.0, dist / radio)

        angulo = math.atan2(dy, dx)
        if angulo < 0:
            angulo += 2 * math.pi
        self.hue = angulo / (2 * math.pi)

        color = QColor.fromHsvF(self.hue, self.sat, self.val)
        btn_code = 1 if boton == Qt.MouseButton.LeftButton else 2
        self.colorCambiado.emit(color, btn_code)
        self.update()

    def set_color(self, color):
        h, s, v, _ = color.getHsvF()
        if h >= 0: self.hue = h
        self.sat = s
        self.val = v if v > 0 else 1.0
        self.update()


class MuestraColoresActuales(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(48, 48)
        self.color_principal = QColor(255, 50, 50)
        self.color_secundario = QColor(255, 255, 255)

    def set_colores(self, principal, secundario):
        self.color_principal = principal
        self.color_secundario = secundario
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(self.color_secundario)
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRect(16, 16, 28, 28)

        painter.setBrush(self.color_principal)
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawRect(4, 4, 28, 28)


class CajaTextoInteractiva(QWidget):
    def __init__(self, parent, x, y, color, fuente):
        super().__init__(parent)
        self.color = color
        self.fuente = fuente
        self.arrastrando = False
        self.offset_arrastre = QPoint()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.input_texto = QLineEdit(self)
        self.input_texto.setFont(fuente)
        self.input_texto.setPlaceholderText("Escribí acá...")
        self.input_texto.textChanged.connect(self.ajustar_tamano)

        self.btn_manija = QToolButton(self)
        self.btn_manija.setText("✥")
        self.btn_manija.setCursor(Qt.CursorShape.SizeAllCursor)

        self.btn_manija.mousePressEvent = self.iniciar_arrastre
        self.btn_manija.mouseMoveEvent = self.mover_arrastre
        self.btn_manija.mouseReleaseEvent = self.soltar_arrastre

        layout.addWidget(self.input_texto)
        layout.addWidget(self.btn_manija)

        self.move(x, y)
        self.actualizar_estilo()
        self.show()
        self.input_texto.setFocus()

    def actualizar_estilo(self):
        self.input_texto.setFont(self.fuente)
        r, g, b, a = self.color.red(), self.color.green(), self.color.blue(), self.color.alpha()

        self.input_texto.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(0, 0, 0, 0.25);
                border: 1px dashed #2a82da;
                border-radius: 2px;
                color: rgba({r}, {g}, {b}, {a/255});
                padding: 2px;
            }}
        """)
        self.btn_manija.setStyleSheet("""
            QToolButton {
                background-color: rgba(42, 130, 218, 0.6);
                color: white;
                border: 1px solid #1e5fa0;
                border-radius: 3px;
                font-weight: bold;
                padding: 1px 4px;
            }
        """)
        self.ajustar_tamano()

    def ajustar_tamano(self):
        fm = QFontMetrics(self.fuente)
        texto = self.input_texto.text() if self.input_texto.text() else self.input_texto.placeholderText()
        ancho_input = max(160, fm.horizontalAdvance(texto) + 24)
        alto_input = fm.height() + 16

        self.input_texto.setFixedSize(ancho_input, alto_input)
        self.btn_manija.setFixedHeight(alto_input)
        self.resize(ancho_input + 35, alto_input)

    def iniciar_arrastre(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.arrastrando = True
            self.offset_arrastre = event.pos()

    def mover_arrastre(self, event):
        if self.arrastrando and (event.buttons() & Qt.MouseButton.LeftButton):
            nueva_pos = self.mapToParent(event.pos() - self.offset_arrastre)
            self.move(nueva_pos)

    def soltar_arrastre(self, event):
        self.arrastrando = False


class MuestraColor(QFrame):
    def __init__(self, color_hex, callback_clic):
        super().__init__()
        self.color = QColor(color_hex)
        self.callback_clic = callback_clic
        self.setFixedSize(16, 16)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.actualizar_aspecto()

    def actualizar_aspecto(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.color.name()};
                border: 1px solid #555555;
                border-radius: 2px;
            }}
            QFrame:hover {{
                border: 2px solid #ffffff;
            }}
        """)

    def set_color(self, color):
        self.color = color
        self.actualizar_aspecto()

    def mousePressEvent(self, event):
        btn_code = 1 if event.button() == Qt.MouseButton.LeftButton else 2
        self.callback_clic(self.color, btn_code)


class PanelColores(QGroupBox):
    def __init__(self, callback_color_cambiado):
        super().__init__("COLORES")
        self.callback_color_cambiado = callback_color_cambiado
        self.color_principal = QColor(255, 50, 50)
        self.color_secundario = QColor(255, 255, 255)
        self.bloquear_señales = False

        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(6)
        layout_principal.setContentsMargins(6, 14, 6, 6)

        layout_rueda_y_muestra = QHBoxLayout()
        layout_rueda_y_muestra.setSpacing(6)
        layout_rueda_y_muestra.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.muestra_dual = MuestraColoresActuales()
        self.rueda = RuedaColor()
        self.rueda.colorCambiado.connect(self.al_cambiar_rueda)

        layout_rueda_y_muestra.addWidget(self.muestra_dual)
        layout_rueda_y_muestra.addWidget(self.rueda)
        layout_principal.addLayout(layout_rueda_y_muestra)

        colores_preset = [
            "#000000", "#333333", "#666666", "#999999", "#CCCCCC", "#FFFFFF", "#4A2E19", "#8B5A2B", "#D2B48C",
            "#800000", "#FF0000", "#FF4500", "#FF7F00", "#FFA500", "#FFD700", "#FFFF00", "#B8860B", "#D2691E",
            "#006400", "#008000", "#00FF00", "#32CD32", "#00F5FF", "#00FFFF", "#00CED1", "#20B2AA", "#008B8B",
            "#000080", "#0000FF", "#1E90FF", "#4169E1", "#8A2BE2", "#9400D3", "#FF00FF", "#C71585", "#FF69B4"
        ]

        grid_preset = QGridLayout()
        grid_preset.setSpacing(2)
        for i, color_hex in enumerate(colores_preset):
            col_box = MuestraColor(color_hex, self.al_seleccionar_preset)
            grid_preset.addWidget(col_box, i // 9, i % 9)

        layout_principal.addLayout(grid_preset)

        self.slots_usuario = []
        grid_usuario = QGridLayout()
        grid_usuario.setSpacing(2)
        for i in range(9):
            col_box = MuestraColor("#1e1e1e", self.al_seleccionar_preset)
            self.slots_usuario.append(col_box)
            grid_usuario.addWidget(col_box, 0, i)

        layout_principal.addLayout(grid_usuario)

        btn_guardar = QToolButton()
        btn_guardar.setText("➕ Guardar Color")
        btn_guardar.clicked.connect(self.guardar_color_personalizado)
        layout_principal.addWidget(btn_guardar)

        grid_inputs = QGridLayout()
        grid_inputs.setSpacing(3)

        validator_rgb = QIntValidator(0, 255)
        regex_hex = QRegularExpression("^#?([a-fA-F0-9]{6})$")
        validator_hex = QRegularExpressionValidator(regex_hex)

        self.input_r = QLineEdit()
        self.input_r.setValidator(validator_rgb)
        self.input_r.setFixedWidth(34)
        self.input_r.textChanged.connect(self.al_cambiar_inputs_rgb)

        self.input_g = QLineEdit()
        self.input_g.setValidator(validator_rgb)
        self.input_g.setFixedWidth(34)
        self.input_g.textChanged.connect(self.al_cambiar_inputs_rgb)

        self.input_b = QLineEdit()
        self.input_b.setValidator(validator_rgb)
        self.input_b.setFixedWidth(34)
        self.input_b.textChanged.connect(self.al_cambiar_inputs_rgb)

        self.input_hex = QLineEdit()
        self.input_hex.setValidator(validator_hex)
        self.input_hex.setFixedWidth(56)
        self.input_hex.textChanged.connect(self.al_cambiar_input_hex)

        grid_inputs.addWidget(QLabel("R:"), 0, 0)
        grid_inputs.addWidget(self.input_r, 0, 1)
        grid_inputs.addWidget(QLabel("G:"), 0, 2)
        grid_inputs.addWidget(self.input_g, 0, 3)
        grid_inputs.addWidget(QLabel("B:"), 1, 0)
        grid_inputs.addWidget(self.input_b, 1, 1)
        grid_inputs.addWidget(QLabel("HEX:"), 1, 2)
        grid_inputs.addWidget(self.input_hex, 1, 3)

        layout_principal.addLayout(grid_inputs)
        self.actualizar_inputs_desde_color(self.color_principal)

    def al_cambiar_rueda(self, color, boton):
        self.aplicar_cambio_color(color, boton)

    def al_seleccionar_preset(self, color, boton):
        self.rueda.set_color(color)
        self.aplicar_cambio_color(color, boton)

    def aplicar_cambio_color(self, color, boton):
        if boton == 1:
            self.color_principal = color
            self.actualizar_inputs_desde_color(color)
        else:
            self.color_secundario = color

        self.muestra_dual.set_colores(self.color_principal, self.color_secundario)
        self.callback_color_cambiado(self.color_principal, self.color_secundario)

    def guardar_color_personalizado(self):
        for i in range(8, 0, -1):
            self.slots_usuario[i].set_color(self.slots_usuario[i-1].color)
        self.slots_usuario[0].set_color(self.color_principal)

    def actualizar_inputs_desde_color(self, color):
        self.bloquear_señales = True
        self.input_r.setText(str(color.red()))
        self.input_g.setText(str(color.green()))
        self.input_b.setText(str(color.blue()))
        self.input_hex.setText(color.name().upper())
        self.bloquear_señales = False

    def al_cambiar_inputs_rgb(self):
        if self.bloquear_señales: return
        r = int(self.input_r.text()) if self.input_r.text() else 0
        g = int(self.input_g.text()) if self.input_g.text() else 0
        b = int(self.input_b.text()) if self.input_b.text() else 0
        self.color_principal = QColor(r, g, b)
        self.rueda.set_color(self.color_principal)
        self.muestra_dual.set_colores(self.color_principal, self.color_secundario)

        self.bloquear_señales = True
        self.input_hex.setText(self.color_principal.name().upper())
        self.bloquear_señales = False

        self.callback_color_cambiado(self.color_principal, self.color_secundario)

    def al_cambiar_input_hex(self):
        if self.bloquear_señales: return
        hex_val = self.input_hex.text()
        if not hex_val.startswith("#"): hex_val = "#" + hex_val
        if len(hex_val) == 7:
            color = QColor(hex_val)
            if color.isValid():
                self.color_principal = color
                self.rueda.set_color(color)
                self.muestra_dual.set_colores(self.color_principal, self.color_secundario)
                self.bloquear_señales = True
                self.input_r.setText(str(color.red()))
                self.input_g.setText(str(color.green()))
                self.input_b.setText(str(color.blue()))
                self.bloquear_señales = False
                self.callback_color_cambiado(self.color_principal, self.color_secundario)


class Lienzo(QWidget):
    def __init__(self, ancho, alto):
        super().__init__()
        self.setFixedSize(ancho, alto)

        self.capa_activa = QImage(ancho, alto, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_activa.fill(Qt.GlobalColor.transparent)

        # Capa temporal para acumular el trazo actual de forma uniforme
        self.capa_trazo_temp = QImage(ancho, alto, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

        self.ultimo_punto = None
        self.color_principal = QColor(255, 50, 50)
        self.color_secundario = QColor(255, 255, 255)
        self.color_actual_uso = self.color_principal

        self.grosor_pincel = 4
        self.opacidad_pincel = 255  # 255 = 100% Opaco (Opacidad elegida)
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

        # 1. Fondo de ajedrez (Transparencia)
        tamano_cuadro = 16
        for y in range(0, self.height(), tamano_cuadro):
            for x in range(0, self.width(), tamano_cuadro):
                color = QColor(200, 200, 200) if (x // tamano_cuadro + y // tamano_cuadro) % 2 == 0 else QColor(255, 255, 255)
                painter.fillRect(x, y, tamano_cuadro, tamano_cuadro, color)

        # 2. Dibujamos la imagen acumulada hasta el momento
        painter.drawImage(0, 0, self.capa_activa)

        # 3. Dibujamos la capa del trazo actual con la opacidad exacta seleccionada
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
                # Dibujamos en la capa temporal con color 100% sólido (sin parches)
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
            # Al soltar el clic, fundimos la capa temporal en la capa activa
            if self.herramienta == "lapiz":
                painter = QPainter(self.capa_activa)
                painter.setOpacity(self.opacidad_pincel / 255.0)
                painter.drawImage(0, 0, self.capa_trazo_temp)
                painter.end()

                self.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

            self.ultimo_punto = None
            self.update()


class PaintNotNet(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PaintNotNet - Nuevo Archivo")
        self.setGeometry(100, 100, 1100, 800)
        self.archivo_actual = None

        self.area_scroll = QScrollArea()
        self.area_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.area_scroll.setWidgetResizable(False)

        self.lienzo = Lienzo(800, 600)
        self.area_scroll.setWidget(self.lienzo)
        self.setCentralWidget(self.area_scroll)

        self.crear_barra_herramientas()
        self.crear_menu()

    def crear_menu(self):
        menu_principal = self.menuBar()
        menu_archivo = menu_principal.addMenu("Archivo")

        accion_abrir = QAction("Abrir...", self)
        accion_abrir.triggered.connect(self.abrir_archivo)
        menu_archivo.addAction(accion_abrir)

        accion_guardar = QAction("Guardar", self)
        accion_guardar.triggered.connect(self.guardar_archivo)
        menu_archivo.addAction(accion_guardar)

        accion_guardar_como = QAction("Guardar como...", self)
        accion_guardar_como.triggered.connect(self.guardar_como)
        menu_archivo.addAction(accion_guardar_como)

        menu_archivo.addSeparator()
        accion_salir = QAction("Salir", self)
        accion_salir.triggered.connect(self.close)
        menu_archivo.addAction(accion_salir)

    def crear_barra_herramientas(self):
        barra = QToolBar("Herramientas")
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, barra)

        # 1. PANEL "HERRAMIENTAS"
        group_herramientas = QGroupBox("HERRAMIENTAS")
        grid_herramientas = QGridLayout(group_herramientas)
        grid_herramientas.setContentsMargins(4, 12, 4, 4)
        grid_herramientas.setSpacing(2)

        herramientas_info = [
            ("lapiz", "lapiz", "Lápiz"),
            ("goma", "goma", "Goma"),
            ("balde", "balde", "Balde de Pintura"),
            ("texto", "texto", "Texto"),
            ("seleccion", "seleccion", "Selección Rectangular")
        ]

        self.botones_herramientas = {}
        for i, (nombre, tipo_icono, tooltip) in enumerate(herramientas_info):
            btn = QToolButton()
            btn.setIcon(crear_icono_herramienta(tipo_icono))
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.setFixedSize(32, 32)
            btn.clicked.connect(lambda checked, n=nombre: self.set_herramienta(n))
            grid_herramientas.addWidget(btn, i // 2, i % 2)
            self.botones_herramientas[nombre] = btn

        self.botones_herramientas["lapiz"].setChecked(True)
        barra.addWidget(group_herramientas)

        # 2. PANEL "PROPIEDADES"
        group_propiedades = QGroupBox("PROPIEDADES")
        layout_prop = QVBoxLayout(group_propiedades)
        layout_prop.setContentsMargins(6, 12, 6, 6)
        layout_prop.setSpacing(4)

        layout_grosor = QHBoxLayout()
        lbl_grosor = QLabel("Grosor:")
        self.spin_grosor = QSpinBox()
        self.spin_grosor.setRange(1, 100)
        self.spin_grosor.setValue(self.lienzo.grosor_pincel)
        self.spin_grosor.valueChanged.connect(self.cambiar_grosor)
        layout_grosor.addWidget(lbl_grosor)
        layout_grosor.addWidget(self.spin_grosor)

        layout_transp = QVBoxLayout()
        self.lbl_transp_val = QLabel(f"Opacidad: {int(self.lienzo.opacidad_pincel / 255 * 100)}%")

        self.slider_transp = QSlider(Qt.Orientation.Horizontal)
        self.slider_transp.setRange(0, 100)
        self.slider_transp.setValue(100)
        self.slider_transp.valueChanged.connect(self.cambiar_opacidad)

        layout_transp.addWidget(self.lbl_transp_val)
        layout_transp.addWidget(self.slider_transp)

        layout_prop.addLayout(layout_grosor)
        layout_prop.addLayout(layout_transp)
        barra.addWidget(group_propiedades)

        # 3. PANEL "TEXTO"
        self.group_texto = QGroupBox("TEXTO")
        layout_texto_panel = QVBoxLayout(self.group_texto)
        layout_texto_panel.setContentsMargins(4, 12, 4, 4)
        layout_texto_panel.setSpacing(4)

        self.combo_fuente = QFontComboBox()
        self.combo_fuente.setCurrentFont(self.lienzo.fuente_texto)
        self.combo_fuente.currentFontChanged.connect(self.actualizar_fuente_texto)
        layout_texto_panel.addWidget(self.combo_fuente)

        linea2 = QHBoxLayout()
        linea2.setSpacing(2)

        self.spin_tamano_texto = QSpinBox()
        self.spin_tamano_texto.setRange(6, 200)
        self.spin_tamano_texto.setValue(self.lienzo.fuente_texto.pointSize())
        self.spin_tamano_texto.valueChanged.connect(self.actualizar_fuente_texto)
        linea2.addWidget(self.spin_tamano_texto)

        self.btn_bold = QToolButton()
        self.btn_bold.setText("B")
        self.btn_bold.setCheckable(True)
        self.btn_bold.setStyleSheet("font-weight: bold;")
        self.btn_bold.toggled.connect(self.actualizar_fuente_texto)

        self.btn_italic = QToolButton()
        self.btn_italic.setText("I")
        self.btn_italic.setCheckable(True)
        self.btn_italic.setStyleSheet("font-style: italic;")
        self.btn_italic.toggled.connect(self.actualizar_fuente_texto)

        self.btn_underline = QToolButton()
        self.btn_underline.setText("U")
        self.btn_underline.setCheckable(True)
        self.btn_underline.setStyleSheet("text-decoration: underline;")
        self.btn_underline.toggled.connect(self.actualizar_fuente_texto)

        self.btn_strike = QToolButton()
        self.btn_strike.setText("S")
        self.btn_strike.setCheckable(True)
        self.btn_strike.setStyleSheet("text-decoration: line-through;")
        self.btn_strike.toggled.connect(self.actualizar_fuente_texto)

        linea2.addWidget(self.btn_bold)
        linea2.addWidget(self.btn_italic)
        linea2.addWidget(self.btn_underline)
        linea2.addWidget(self.btn_strike)

        layout_texto_panel.addLayout(linea2)

        barra.addWidget(self.group_texto)
        self.group_texto.setVisible(False)

        # 4. PANEL "COLORES"
        self.panel_colores = PanelColores(self.al_cambiar_color_paleta)
        barra.addWidget(self.panel_colores)

    def set_herramienta(self, nombre):
        if nombre != "texto":
            self.lienzo.fijar_texto_si_existe()
            self.group_texto.setVisible(False)
        else:
            self.group_texto.setVisible(True)

        for n, btn in self.botones_herramientas.items():
            btn.setChecked(n == nombre)

        self.lienzo.herramienta = nombre

    def al_cambiar_color_paleta(self, principal, secundario):
        self.lienzo.color_principal = principal
        self.lienzo.color_secundario = secundario
        if self.lienzo.editor_texto:
            self.lienzo.editor_texto.color = principal
            self.lienzo.editor_texto.actualizar_estilo()

    def cambiar_grosor(self, valor):
        self.lienzo.grosor_pincel = valor

    def cambiar_opacidad(self, valor_porcentaje):
        alfa = int((valor_porcentaje / 100.0) * 255)
        self.lienzo.opacidad_pincel = alfa
        self.lbl_transp_val.setText(f"Opacidad: {valor_porcentaje}%")

    def actualizar_fuente_texto(self):
        fuente = self.combo_fuente.currentFont()
        fuente.setPointSize(self.spin_tamano_texto.value())
        fuente.setBold(self.btn_bold.isChecked())
        fuente.setItalic(self.btn_italic.isChecked())
        fuente.setUnderline(self.btn_underline.isChecked())
        fuente.setStrikeOut(self.btn_strike.isChecked())

        self.lienzo.fuente_texto = fuente
        if self.lienzo.editor_texto:
            self.lienzo.editor_texto.fuente = fuente
            self.lienzo.editor_texto.actualizar_estilo()

    def abrir_archivo(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Abrir Imagen", "", "Imágenes (*.png *.jpg *.jpeg *.bmp)")
        if ruta:
            if self.lienzo.cargar_imagen(ruta):
                self.archivo_actual = ruta
                self.setWindowTitle(f"PaintNotNet - {ruta}")

    def guardar_archivo(self):
        if self.archivo_actual:
            self.lienzo.guardar_imagen(self.archivo_actual)
        else:
            self.guardar_como()

    def guardar_como(self):
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar Imagen", "", "Imágenes PNG (*.png);;Imágenes JPEG (*.jpg)")
        if ruta:
            if not ruta.lower().endswith(('.png', '.jpg', '.jpeg')): ruta += '.png'
            if self.lienzo.guardar_imagen(ruta):
                self.archivo_actual = ruta
                self.setWindowTitle(f"PaintNotNet - {ruta}")

if __name__ == '__main__':
    app = QApplication(sys.argv)

    app.setStyle("Fusion")
    paleta_oscura = app.palette()
    paleta_oscura.setColor(paleta_oscura.ColorRole.Window, QColor(45, 45, 45))
    paleta_oscura.setColor(paleta_oscura.ColorRole.WindowText, Qt.GlobalColor.white)
    paleta_oscura.setColor(paleta_oscura.ColorRole.Base, QColor(30, 30, 30))
    paleta_oscura.setColor(paleta_oscura.ColorRole.AlternateBase, QColor(45, 45, 45))
    paleta_oscura.setColor(paleta_oscura.ColorRole.Text, Qt.GlobalColor.white)
    paleta_oscura.setColor(paleta_oscura.ColorRole.Button, QColor(45, 45, 45))
    paleta_oscura.setColor(paleta_oscura.ColorRole.ButtonText, Qt.GlobalColor.white)
    paleta_oscura.setColor(paleta_oscura.ColorRole.Highlight, QColor(42, 130, 218))
    paleta_oscura.setColor(paleta_oscura.ColorRole.HighlightedText, Qt.GlobalColor.white)
    app.setPalette(paleta_oscura)

    app.setStyleSheet("""
        QWidget {
            color: #ffffff;
        }
        QGroupBox {
            font-weight: bold;
            font-size: 11px;
            border: 1px solid #5a5a5a;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 4px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 4px;
            color: #2a82da;
        }
        QComboBox, QSpinBox, QFontComboBox, QLineEdit {
            background-color: #2b2b2b;
            color: #ffffff;
            border: 1px solid #4a4a4a;
            padding: 2px;
            border-radius: 3px;
        }
        QToolButton {
            background-color: #3a3a3a;
            color: #ffffff;
            border: 1px solid #5a5a5a;
            padding: 2px;
            border-radius: 3px;
        }
        QToolButton:checked {
            background-color: #2a82da;
            border-color: #1e5fa0;
        }
    """)

    ventana = PaintNotNet()
    ventana.show()
    sys.exit(app.exec())
