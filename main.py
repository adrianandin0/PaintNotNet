import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QToolBar, QColorDialog, QLabel, QSpinBox,
                             QScrollArea, QFileDialog, QMessageBox)
from PyQt6.QtGui import QPainter, QImage, QColor, QPen, QAction
from PyQt6.QtCore import Qt, QPoint

class Lienzo(QWidget):
    def __init__(self, ancho, alto):
        super().__init__()
        self.setFixedSize(ancho, alto)
        
        self.capa_activa = QImage(ancho, alto, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_activa.fill(Qt.GlobalColor.transparent)
        
        self.ultimo_punto = None
        self.color_pincel = QColor(255, 50, 50)
        self.grosor_pincel = 4

    def cargar_imagen(self, ruta):
        # Cargamos la imagen temporalmente para ver si existe y es válida
        imagen_temporal = QImage(ruta)
        if imagen_temporal.isNull():
            return False
            
        # La convertimos al formato con soporte de transparencias (Alfa)
        self.capa_activa = imagen_temporal.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
        # Redimensionamos el lienzo (widget) al tamaño de la imagen que acabamos de abrir
        self.setFixedSize(self.capa_activa.width(), self.capa_activa.height())
        self.update()
        return True

    def guardar_imagen(self, ruta):
        # Guardamos la imagen en la ruta especificada
        return self.capa_activa.save(ruta)

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Fondo cuadriculado
        tamano_cuadro = 16
        for y in range(0, self.height(), tamano_cuadro):
            for x in range(0, self.width(), tamano_cuadro):
                color = QColor(200, 200, 200) if (x // tamano_cuadro + y // tamano_cuadro) % 2 == 0 else QColor(255, 255, 255)
                painter.fillRect(x, y, tamano_cuadro, tamano_cuadro, color)
                
        # Capa de dibujo / imagen
        painter.drawImage(0, 0, self.capa_activa)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.ultimo_punto = event.pos()

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton) and self.ultimo_punto:
            painter = QPainter(self.capa_activa)
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
        self.setWindowTitle("PaintNotNet - Nuevo Archivo")
        self.setGeometry(100, 100, 1024, 768)
        
        # Variable para saber si estamos trabajando sobre un archivo existente
        self.archivo_actual = None
        
        # EL ESPACIO DE TRABAJO (ScrollArea)
        # Esto reemplaza al contenedor simple y nos da el "recuadro" de edición
        self.area_scroll = QScrollArea()
        self.area_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.area_scroll.setWidgetResizable(False) # Fundamental para que el lienzo mantenga su tamaño real
        
        self.lienzo = Lienzo(800, 600)
        self.area_scroll.setWidget(self.lienzo)
        self.setCentralWidget(self.area_scroll)
        
        self.crear_barra_herramientas()
        self.crear_menu()

    def crear_menu(self):
        menu_principal = self.menuBar()
        menu_archivo = menu_principal.addMenu("Archivo")
        
        # Abrir
        accion_abrir = QAction("Abrir...", self)
        accion_abrir.setShortcut("Ctrl+O")
        accion_abrir.triggered.connect(self.abrir_archivo)
        menu_archivo.addAction(accion_abrir)
        
        # Guardar
        accion_guardar = QAction("Guardar", self)
        accion_guardar.setShortcut("Ctrl+S")
        accion_guardar.triggered.connect(self.guardar_archivo)
        menu_archivo.addAction(accion_guardar)
        
        # Guardar como
        accion_guardar_como = QAction("Guardar como...", self)
        accion_guardar_como.setShortcut("Ctrl+Shift+S")
        accion_guardar_como.triggered.connect(self.guardar_como)
        menu_archivo.addAction(accion_guardar_como)
        
        menu_archivo.addSeparator()
        
        # Salir
        accion_salir = QAction("Salir", self)
        accion_salir.setShortcut("Ctrl+Q")
        accion_salir.triggered.connect(self.close)
        menu_archivo.addAction(accion_salir)

    def crear_barra_herramientas(self):
        barra = QToolBar("Herramientas Principales")
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, barra)
        
        btn_color = barra.addAction("🎨 Color")
        btn_color.triggered.connect(self.abrir_selector_color)
        
        barra.addSeparator()
        
        label_grosor = QLabel(" Grosor: ")
        barra.addWidget(label_grosor)
        
        self.spin_grosor = QSpinBox()
        self.spin_grosor.setRange(1, 100)
        self.spin_grosor.setValue(self.lienzo.grosor_pincel)
        self.spin_grosor.valueChanged.connect(self.cambiar_grosor)
        
        barra.addWidget(self.spin_grosor)

    def abrir_selector_color(self):
        color = QColorDialog.getColor(self.lienzo.color_pincel, self, "Seleccionar Color")
        if color.isValid():
            self.lienzo.color_pincel = color

    def cambiar_grosor(self, valor):
        self.lienzo.grosor_pincel = valor

    # --- LÓGICA DE ARCHIVOS ---
    def abrir_archivo(self):
        # QFileDialog invoca la ventana nativa de KDE
        ruta, _ = QFileDialog.getOpenFileName(self, "Abrir Imagen", "", "Imágenes (*.png *.jpg *.jpeg *.bmp)")
        if ruta:
            if self.lienzo.cargar_imagen(ruta):
                self.archivo_actual = ruta
                self.setWindowTitle(f"PaintNotNet - {ruta}")

    def guardar_archivo(self):
        if self.archivo_actual:
            self.lienzo.guardar_imagen(self.archivo_actual)
        else:
            # Si es un dibujo nuevo, lo mandamos a Guardar Como
            self.guardar_como()

    def guardar_como(self):
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar Imagen", "", "Imágenes PNG (*.png);;Imágenes JPEG (*.jpg)")
        if ruta:
            # Forzamos la extensión PNG por defecto si el usuario no pone nada
            if not ruta.lower().endswith(('.png', '.jpg', '.jpeg')):
                ruta += '.png'
                
            if self.lienzo.guardar_imagen(ruta):
                self.archivo_actual = ruta
                self.setWindowTitle(f"PaintNotNet - {ruta}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Forzar modo oscuro COMPLETO
    app.setStyle("Fusion")
    paleta_oscura = app.palette()
    
    # Fondos
    paleta_oscura.setColor(paleta_oscura.ColorRole.Window, QColor(45, 45, 45))
    paleta_oscura.setColor(paleta_oscura.ColorRole.Base, QColor(30, 30, 30))
    paleta_oscura.setColor(paleta_oscura.ColorRole.Button, QColor(45, 45, 45))
    
    # Textos
    paleta_oscura.setColor(paleta_oscura.ColorRole.WindowText, Qt.GlobalColor.white)
    paleta_oscura.setColor(paleta_oscura.ColorRole.Text, Qt.GlobalColor.white)
    paleta_oscura.setColor(paleta_oscura.ColorRole.ButtonText, Qt.GlobalColor.white)
    
    # Colores de selección (cuando resaltás algo en un menú)
    paleta_oscura.setColor(paleta_oscura.ColorRole.Highlight, QColor(42, 130, 218)) # Un azul lindo
    paleta_oscura.setColor(paleta_oscura.ColorRole.HighlightedText, Qt.GlobalColor.white)
    
    app.setPalette(paleta_oscura)
    
    ventana = PaintNotNet()
    ventana.show()
    sys.exit(app.exec())
