import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QToolBar, QColorDialog, QLabel, QSpinBox,
                             QScrollArea, QFileDialog, QMessageBox, QInputDialog, QFontDialog)
from PyQt6.QtGui import QPainter, QImage, QColor, QPen, QAction, QFont
from PyQt6.QtCore import Qt, QPoint, QRect

class Lienzo(QWidget):
    def __init__(self, ancho, alto):
        super().__init__()
        self.setFixedSize(ancho, alto)
        
        self.capa_activa = QImage(ancho, alto, QImage.Format.Format_ARGB32_Premultiplied)
        self.capa_activa.fill(Qt.GlobalColor.transparent)
        
        self.ultimo_punto = None
        self.color_pincel = QColor(255, 50, 50)
        self.grosor_pincel = 4
        
        # EL CEREBRO: ¿Qué herramienta estamos usando ahora?
        self.herramienta = "lapiz" 

    def cargar_imagen(self, ruta):
        imagen_temporal = QImage(ruta)
        if imagen_temporal.isNull(): return False
        self.capa_activa = imagen_temporal.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
        self.setFixedSize(self.capa_activa.width(), self.capa_activa.height())
        self.update()
        return True

    def guardar_imagen(self, ruta):
        return self.capa_activa.save(ruta)

    def paintEvent(self, event):
        painter = QPainter(self)
        # Fondo cuadriculado
        tamano_cuadro = 16
        for y in range(0, self.height(), tamano_cuadro):
            for x in range(0, self.width(), tamano_cuadro):
                color = QColor(200, 200, 200) if (x // tamano_cuadro + y // tamano_cuadro) % 2 == 0 else QColor(255, 255, 255)
                painter.fillRect(x, y, tamano_cuadro, tamano_cuadro, color)
        
        # Dibujamos la imagen
        painter.drawImage(0, 0, self.capa_activa)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.ultimo_punto = event.pos()
            
            # Si tocamos con el balde, texto o selección, la lógica irá acá en el futuro
            if self.herramienta == "balde":
                print("¡Clic con el balde! (Próximamente)")
            elif self.herramienta == "texto":
                print("¡Clic para texto! (Próximamente)")

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton) and self.ultimo_punto:
            painter = QPainter(self.capa_activa)
            
            if self.herramienta == "lapiz":
                # Pincel normal
                pen = QPen(self.color_pincel, self.grosor_pincel, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                painter.drawLine(self.ultimo_punto, event.pos())
                self.ultimo_punto = event.pos()
                
            elif self.herramienta == "goma":
                # MODO GOMA DE BORRAR: Destruye los píxeles (los vuelve transparentes)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                # El color no importa en modo Clear, pero el RoundCap hace que la goma sea circular
                pen = QPen(Qt.GlobalColor.transparent, self.grosor_pincel, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
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
        
        # --- BOTONES DE HERRAMIENTAS ---
        btn_lapiz = barra.addAction("✏️ Lápiz")
        btn_lapiz.triggered.connect(lambda: self.set_herramienta("lapiz"))
        
        btn_goma = barra.addAction("🧽 Goma")
        btn_goma.triggered.connect(lambda: self.set_herramienta("goma"))
        
        btn_balde = barra.addAction("🪣 Balde")
        btn_balde.triggered.connect(lambda: self.set_herramienta("balde"))
        
        btn_texto = barra.addAction("🅰️ Texto")
        btn_texto.triggered.connect(lambda: self.set_herramienta("texto"))
        
        btn_seleccion = barra.addAction("⬚ Selección")
        btn_seleccion.triggered.connect(lambda: self.set_herramienta("seleccion"))
        
        barra.addSeparator()
        
        # --- COLOR Y GROSOR ---
        btn_color = barra.addAction("🎨 Color")
        btn_color.triggered.connect(self.abrir_selector_color)
        
        label_grosor = QLabel(" Grosor: ")
        barra.addWidget(label_grosor)
        
        self.spin_grosor = QSpinBox()
        self.spin_grosor.setRange(1, 100)
        self.spin_grosor.setValue(self.lienzo.grosor_pincel)
        self.spin_grosor.valueChanged.connect(self.cambiar_grosor)
        barra.addWidget(self.spin_grosor)
        
        # Etiqueta para mostrar qué herramienta está activa
        barra.addSeparator()
        self.label_estado = QLabel(" Herramienta: Lápiz")
        barra.addWidget(self.label_estado)

    def set_herramienta(self, nombre):
        self.lienzo.herramienta = nombre
        self.label_estado.setText(f" Herramienta: {nombre.capitalize()}")

    def abrir_selector_color(self):
        color = QColorDialog.getColor(self.lienzo.color_pincel, self, "Seleccionar Color")
        if color.isValid():
            self.lienzo.color_pincel = color

    def cambiar_grosor(self, valor):
        self.lienzo.grosor_pincel = valor

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
    paleta_oscura.setColor(paleta_oscura.ColorRole.Base, QColor(30, 30, 30))
    paleta_oscura.setColor(paleta_oscura.ColorRole.Button, QColor(45, 45, 45))
    paleta_oscura.setColor(paleta_oscura.ColorRole.WindowText, Qt.GlobalColor.white)
    paleta_oscura.setColor(paleta_oscura.ColorRole.Text, Qt.GlobalColor.white)
    paleta_oscura.setColor(paleta_oscura.ColorRole.ButtonText, Qt.GlobalColor.white)
    paleta_oscura.setColor(paleta_oscura.ColorRole.Highlight, QColor(42, 130, 218))
    paleta_oscura.setColor(paleta_oscura.ColorRole.HighlightedText, Qt.GlobalColor.white)
    app.setPalette(paleta_oscura)
    
    ventana = PaintNotNet()
    ventana.show()
    sys.exit(app.exec())
