import math
from PyQt6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QWidget, QGridLayout, QFrame)
from PyQt6.QtGui import (QPainter, QColor, QPen, QIntValidator, QRegularExpressionValidator,
                         QConicalGradient, QRadialGradient)
from PyQt6.QtCore import Qt, QPointF, QRegularExpression, pyqtSignal

class RuedaColor(QWidget):
    colorCambiado = pyqtSignal(QColor, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 100)
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
        painter.drawEllipse(QPointF(px, py), 3, 3)
        painter.setPen(QPen(Qt.GlobalColor.white, 1))
        painter.drawEllipse(QPointF(px, py), 4, 4)

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
        self.setFixedSize(40, 40)
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
        painter.setPen(QPen(QColor(180, 180, 180), 1))
        painter.drawRect(14, 14, 22, 22)

        painter.setBrush(self.color_principal)
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawRect(4, 4, 22, 22)


class MuestraColor(QFrame):
    def __init__(self, color_hex, callback_clic, vacio=False):
        super().__init__()
        self.color = QColor(color_hex) if color_hex else QColor(0, 0, 0, 0)
        self.vacio = vacio
        self.callback_clic = callback_clic
        self.setFixedSize(18, 18)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.actualizar_aspecto()

    def actualizar_aspecto(self):
        if self.vacio and self.color.alpha() == 0:
            self.setStyleSheet("""
                QFrame {
                    background-color: transparent;
                    border: 1px dashed #555555;
                    margin: 0px;
                }
                QFrame:hover {
                    border: 1px solid #2a82da;
                    background-color: rgba(42, 130, 218, 0.2);
                }
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.color.name()};
                    border: 1px solid #2b2b2b;
                    margin: 0px;
                }}
                QFrame:hover {{
                    border: 1px solid #ffffff;
                }}
            """)

    def set_color(self, color):
        self.color = color
        self.vacio = False
        self.actualizar_aspecto()

    def mousePressEvent(self, event):
        btn_code = 1 if event.button() == Qt.MouseButton.LeftButton else 2
        self.callback_clic(self, btn_code)


class PanelColores(QGroupBox):
    def __init__(self, callback_color_cambiado):
        super().__init__("COLORES")
        self.callback_color_cambiado = callback_color_cambiado
        self.color_principal = QColor(255, 50, 50)
        self.color_secundario = QColor(255, 255, 255)
        self.bloquear_señales = False

        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(1)
        layout_principal.setContentsMargins(2, 8, 2, 2)

        layout_rueda_y_muestra = QHBoxLayout()
        layout_rueda_y_muestra.setSpacing(4)
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
        grid_preset.setSpacing(0)
        grid_preset.setContentsMargins(0, 0, 0, 0)
        for i, color_hex in enumerate(colores_preset):
            col_box = MuestraColor(color_hex, self.al_seleccionar_preset)
            grid_preset.addWidget(col_box, i // 9, i % 9)

        layout_principal.addLayout(grid_preset)

        linea_sep = QFrame()
        linea_sep.setFrameShape(QFrame.Shape.HLine)
        linea_sep.setFrameShadow(QFrame.Shadow.Sunken)
        linea_sep.setStyleSheet("border: 1px solid #444444; margin-top: 2px; margin-bottom: 2px;")
        layout_principal.addWidget(linea_sep)

        lbl_guardados = QLabel("GUARDADOS")
        lbl_guardados.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_guardados.setStyleSheet("font-size: 9px; font-weight: bold; color: #2a82da;")
        layout_principal.addWidget(lbl_guardados)

        self.slots_usuario = []
        grid_usuario = QGridLayout()
        grid_usuario.setSpacing(0)
        grid_usuario.setContentsMargins(0, 0, 0, 0)
        for i in range(9):
            col_box = MuestraColor(None, self.al_clic_slot_guardado, vacio=True)
            self.slots_usuario.append(col_box)
            grid_usuario.addWidget(col_box, 0, i)

        layout_principal.addLayout(grid_usuario)

        grid_inputs = QGridLayout()
        grid_inputs.setSpacing(2)

        validator_rgb = QIntValidator(0, 255)
        regex_hex = QRegularExpression("^#?([a-fA-F0-9]{6})$")
        validator_hex = QRegularExpressionValidator(regex_hex)

        self.input_r = QLineEdit()
        self.input_r.setValidator(validator_rgb)
        self.input_r.setFixedWidth(32)
        self.input_r.textChanged.connect(self.al_cambiar_inputs_rgb)

        self.input_g = QLineEdit()
        self.input_g.setValidator(validator_rgb)
        self.input_g.setFixedWidth(32)
        self.input_g.textChanged.connect(self.al_cambiar_inputs_rgb)

        self.input_b = QLineEdit()
        self.input_b.setValidator(validator_rgb)
        self.input_b.setFixedWidth(32)
        self.input_b.textChanged.connect(self.al_cambiar_inputs_rgb)

        self.input_hex = QLineEdit()
        self.input_hex.setValidator(validator_hex)
        self.input_hex.setFixedWidth(54)
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

    def al_seleccionar_preset(self, widget, boton):
        self.rueda.set_color(widget.color)
        self.aplicar_cambio_color(widget.color, boton)

    def al_clic_slot_guardado(self, widget, boton):
        if widget.vacio:
            color_a_guardar = self.color_principal if boton == 1 else self.color_secundario
            widget.set_color(color_a_guardar)
        else:
            self.rueda.set_color(widget.color)
            self.aplicar_cambio_color(widget.color, boton)

    def aplicar_cambio_color(self, color, boton):
        if boton == 1:
            self.color_principal = color
            self.actualizar_inputs_desde_color(color)
        else:
            self.color_secundario = color

        self.muestra_dual.set_colores(self.color_principal, self.color_secundario)
        self.callback_color_cambiado(self.color_principal, self.color_secundario)

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
