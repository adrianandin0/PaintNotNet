import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QToolBar, QColorDialog, QLabel, QSpinBox)
from PyQt6.QtGui import QPainter, QImage, QColor, QPen
from PyQt6.QtCore import Qt, QPoint

class Lienzo(QWidget):
    def __init__(self, ancho, alto):
        super().__init__()
        self.setFixedSize(ancho, alto)
        
        self.capa_activa = QImage(ancho, alto, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_activa.fill(Qt.GlobalColor.transparent)
        
        self.ultimo_punto = None
        
        # Nuevas variables dinámicas para la herramienta actual
        self.color_pincel = QColor(255, 50, 50) # Arranca en rojo
        self.grosor_pincel = 4 # Arranca en 4px

    def paintEvent(self, event):
        painter = QPainter(self)
        
        tamano_cuadro = 16
        for y in range(0, self.height(), tamano_cuadro):
            for x in range(0, self.width(), tamano_cuadro):
                color = QColor(200, 200, 200) if (x // tamano_cuadro + y // tamano_cuadro) % 2 == 0 else QColor(255, 255, 255)
                painter.fillRect(x, y, tamano_cuadro, tamano_cuadro, color)
                
        painter.drawImage(0, 0, self.capa_activa)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.ultimo_punto = event.pos()

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton) and self.ultimo_punto:
            painter = QPainter(self.capa_activa)
            
            # Ahora usamos nuestras variables dinámicas en lugar de valores fijos
            pen = QPen(self.color_pincel, self.grosor_pincel, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            
            painter.drawLine(self.ultimo_punto, event.pos())
            self.ultimo_punto = event.pos()
            
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.ultimo_punto = None


class PaintNotNet(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PaintNotNet")
        self.setGeometry(100, 100, 900, 700)
        
        self.contenedor = QWidget()
        self.setCentralWidget(self.contenedor)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lienzo = Lienzo(800, 600)
        layout.addWidget(self.lienzo)
        self.contenedor.setLayout(layout)
        
        # Inicializamos la interfaz
        self.crear_barra_herramientas()

    def crear_barra_herramientas(self):
        # Creamos la barra y la ubicamos a la izquierda
        barra = QToolBar("Herramientas Principales")
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, barra)
        
        # 1. Botón de Color
        btn_color = barra.addAction("🎨 Elegir Color")
        btn_color.triggered.connect(self.abrir_selector_color)
        
        barra.addSeparator()
        
        # 2. Etiqueta y Selector de Grosor
        label_grosor = QLabel(" Grosor: ")
        barra.addWidget(label_grosor)
        
        self.spin_grosor = QSpinBox()
        self.spin_grosor.setRange(1, 100) # De 1 a 100 píxeles
        self.spin_grosor.setValue(self.lienzo.grosor_pincel)
        self.spin_grosor.valueChanged.connect(self.cambiar_grosor)
        
        barra.addWidget(self.spin_grosor)

    def abrir_selector_color(self):
        # Abre la ventana nativa de KDE para elegir colores
        color = QColorDialog.getColor(self.lienzo.color_pincel, self, "Seleccionar Color de Pincel")
        if color.isValid():
            self.lienzo.color_pincel = color

    def cambiar_grosor(self, valor):
        self.lienzo.grosor_pincel = valor


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    app.setStyle("Fusion")
    paleta_oscura = app.palette()
    paleta_oscura.setColor(paleta_oscura.ColorRole.Window, QColor(45, 45, 45))
    paleta_oscura.setColor(paleta_oscura.ColorRole.WindowText, Qt.GlobalColor.white)
    paleta_oscura.setColor(paleta_oscura.ColorRole.Base, QColor(30, 30, 30))
    app.setPalette(paleta_oscura)
    
    ventana = PaintNotNet()
    ventana.show()
    sys.exit(app.exec())
