import math
from PyQt6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFontComboBox,
                             QSpinBox, QToolButton, QWidget, QLineEdit, QCheckBox,
                             QSlider, QLabel, QFrame)
from PyQt6.QtGui import QFont, QFontMetrics, QColor, QPainter, QPen
from PyQt6.QtCore import Qt, QPoint, QPointF, pyqtSignal


class PadFuenteLuz(QWidget):
    posicionCambiada = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(36, 36)
        self.vec_x = 0.5
        self.vec_y = 0.5
        self.setCursor(Qt.CursorShape.CrossCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        radio = self.width() / 2.0
        centro = QPointF(radio, radio)

        painter.setBrush(QColor(35, 35, 35))
        painter.setPen(QPen(QColor(90, 90, 90), 1))
        painter.drawEllipse(1, 1, self.width() - 2, self.height() - 2)

        painter.setPen(QPen(QColor(70, 70, 70), 1, Qt.PenStyle.DashLine))
        painter.drawLine(int(radio), 4, int(radio), int(self.height() - 4))
        painter.drawLine(4, int(radio), int(self.width() - 4), int(radio))

        px = centro.x() + (self.vec_x * (radio - 4))
        py = centro.y() + (self.vec_y * (radio - 4))

        painter.setBrush(QColor(230, 50, 50))
        painter.setPen(QPen(Qt.GlobalColor.white, 1))
        painter.drawEllipse(QPointF(px, py), 3.5, 3.5)

    def mousePressEvent(self, event):
        self.procesar_mouse(event.pos())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.procesar_mouse(event.pos())

    def procesar_mouse(self, pos):
        radio = self.width() / 2.0
        dx = (pos.x() - radio) / (radio - 4)
        dy = (pos.y() - radio) / (radio - 4)

        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 1.0 and dist > 0:
            dx /= dist
            dy /= dist

        self.vec_x = dx
        self.vec_y = dy
        self.posicionCambiada.emit(self.vec_x, self.vec_y)
        self.update()


class CajaTextoInteractiva(QWidget):
    def __init__(self, parent, x, y, color, fuente, config_borde, config_sombra):
        super().__init__(parent)
        self.color = color
        self.fuente = fuente
        self.config_borde = config_borde
        self.config_sombra = config_sombra
        self.arrastrando = False
        self.offset_arrastre = QPoint()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.input_texto = QLineEdit(self)
        self.input_texto.setFont(fuente)
        self.input_texto.setPlaceholderText("Escribí acá...")
        self.input_texto.textChanged.connect(self.al_cambiar_texto)

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

    def al_cambiar_texto(self):
        self.ajustar_tamano()
        if self.parent(): self.parent().update()

    def actualizar_estilo(self):
        self.input_texto.setFont(self.fuente)

        # Hacemos el texto del input 100% transparente y sin fondo opaco
        # para que se vea UNICAMENTE el renderizado real del lienzo sin sombras dobles
        self.input_texto.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: 1px dashed #2a82da;
                border-radius: 2px;
                color: transparent;
                selection-background-color: rgba(42, 130, 218, 0.4);
                padding: 0px 4px;
            }
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
            if self.parent(): self.parent().update()

    def soltar_arrastre(self, event):
        self.arrastrando = False


class MuestraColorMini(QFrame):
    def __init__(self, color):
        super().__init__()
        self.setFixedSize(14, 14)
        self.set_color(color)

    def set_color(self, color):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color.name()};
                border: 1px solid #ffffff;
                border-radius: 2px;
            }}
        """)


class PanelTexto(QGroupBox):
    def __init__(self, fuente_inicial, callback_cambio_fuente, color_secundario_ini):
        super().__init__("TEXTO")
        self.callback_cambio_fuente = callback_cambio_fuente
        self.color_secundario = color_secundario_ini

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 12, 4, 6)
        layout.setSpacing(3)

        self.combo_fuente = QFontComboBox()
        self.combo_fuente.setCurrentFont(fuente_inicial)
        self.combo_fuente.currentFontChanged.connect(self.emitir_cambio)
        layout.addWidget(self.combo_fuente)

        linea2 = QHBoxLayout()
        linea2.setSpacing(1)

        self.spin_tamano = QSpinBox()
        self.spin_tamano.setRange(6, 200)
        self.spin_tamano.setValue(fuente_inicial.pointSize())
        self.spin_tamano.valueChanged.connect(self.emitir_cambio)
        linea2.addWidget(self.spin_tamano)

        self.btn_bold = QToolButton()
        self.btn_bold.setText("B")
        self.btn_bold.setCheckable(True)
        self.btn_bold.setStyleSheet("font-weight: bold;")
        self.btn_bold.toggled.connect(self.emitir_cambio)

        self.btn_italic = QToolButton()
        self.btn_italic.setText("I")
        self.btn_italic.setCheckable(True)
        self.btn_italic.setStyleSheet("font-style: italic;")
        self.btn_italic.toggled.connect(self.emitir_cambio)

        self.btn_underline = QToolButton()
        self.btn_underline.setText("U")
        self.btn_underline.setCheckable(True)
        self.btn_underline.setStyleSheet("text-decoration: underline;")
        self.btn_underline.toggled.connect(self.emitir_cambio)

        self.btn_strike = QToolButton()
        self.btn_strike.setText("S")
        self.btn_strike.setCheckable(True)
        self.btn_strike.setStyleSheet("text-decoration: line-through;")
        self.btn_strike.toggled.connect(self.emitir_cambio)

        linea2.addWidget(self.btn_bold)
        linea2.addWidget(self.btn_italic)
        linea2.addWidget(self.btn_underline)
        linea2.addWidget(self.btn_strike)
        layout.addLayout(linea2)

        linea_borde = QHBoxLayout()
        linea_borde.setSpacing(2)

        self.chk_borde = QCheckBox("BORDE")
        self.chk_borde.setStyleSheet("font-size: 8px; font-weight: bold;")
        self.chk_borde.toggled.connect(self.emitir_cambio)

        self.spin_grosor_borde = QSpinBox()
        self.spin_grosor_borde.setRange(1, 9999)
        self.spin_grosor_borde.setValue(2)
        self.spin_grosor_borde.setFixedWidth(40)
        self.spin_grosor_borde.valueChanged.connect(self.emitir_cambio)

        self.muestra_color_borde = MuestraColorMini(self.color_secundario)

        linea_borde.addWidget(self.chk_borde)
        linea_borde.addWidget(self.spin_grosor_borde)
        linea_borde.addWidget(self.muestra_color_borde)
        linea_borde.addStretch()
        layout.addLayout(linea_borde)

        linea_sombra = QHBoxLayout()
        linea_sombra.setSpacing(2)

        self.chk_sombra = QCheckBox("SOMBRA")
        self.chk_sombra.setStyleSheet("font-size: 8px; font-weight: bold;")
        self.chk_sombra.toggled.connect(self.emitir_cambio)

        self.pad_luz = PadFuenteLuz()
        self.pad_luz.posicionCambiada.connect(lambda x, y: self.emitir_cambio())

        self.slider_ext_sombra = QSlider(Qt.Orientation.Horizontal)
        self.slider_ext_sombra.setRange(1, 30)
        self.slider_ext_sombra.setValue(6)
        self.slider_ext_sombra.valueChanged.connect(self.emitir_cambio)

        linea_sombra.addWidget(self.chk_sombra)
        linea_sombra.addWidget(self.pad_luz)
        linea_sombra.addWidget(self.slider_ext_sombra)
        layout.addLayout(linea_sombra)

    def set_color_secundario(self, color):
        self.color_secundario = color
        self.muestra_color_borde.set_color(color)
        self.emitir_cambio()

    def obtener_configuraciones(self):
        borde = {
            'activo': self.chk_borde.isChecked(),
            'grosor': self.spin_grosor_borde.value(),
            'color': self.color_secundario
        }
        sombra = {
            'activo': self.chk_sombra.isChecked(),
            'vec_x': self.pad_luz.vec_x,
            'vec_y': self.pad_luz.vec_y,
            'dist': self.slider_ext_sombra.value()
        }
        return borde, sombra

    def emitir_cambio(self):
        fuente = self.combo_fuente.currentFont()
        fuente.setPointSize(self.spin_tamano.value())
        fuente.setBold(self.btn_bold.isChecked())
        fuente.setItalic(self.btn_italic.isChecked())
        fuente.setUnderline(self.btn_underline.isChecked())
        fuente.setStrikeOut(self.btn_strike.isChecked())
        self.callback_cambio_fuente(fuente)
