from PyQt6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFontComboBox, 
                             QSpinBox, QToolButton, QWidget, QLineEdit)
from PyQt6.QtGui import QFont, QFontMetrics
from PyQt6.QtCore import Qt, QPoint

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


class PanelTexto(QGroupBox):
    def __init__(self, fuente_inicial, callback_cambio_fuente):
        super().__init__("TEXTO")
        self.callback_cambio_fuente = callback_cambio_fuente

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 4)
        layout.setSpacing(2)

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

    def emitir_cambio(self):
        fuente = self.combo_fuente.currentFont()
        fuente.setPointSize(self.spin_tamano.value())
        fuente.setBold(self.btn_bold.isChecked())
        fuente.setItalic(self.btn_italic.isChecked())
        fuente.setUnderline(self.btn_underline.isChecked())
        fuente.setStrikeOut(self.btn_strike.isChecked())
        self.callback_cambio_fuente(fuente)
