from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QFileDialog

class MenuArchivo:
    def __init__(self, ventana_principal):
        self.ventana = ventana_principal

    def crear_menu(self, menu_bar):
        menu = menu_bar.addMenu("Archivo")

        accion_nuevo = QAction("Nuevo", self.ventana)
        accion_nuevo.triggered.connect(self.nuevo)
        menu.addAction(accion_nuevo)

        accion_abrir = QAction("Abrir...", self.ventana)
        accion_abrir.triggered.connect(self.abrir)
        menu.addAction(accion_abrir)

        accion_guardar = QAction("Guardar", self.ventana)
        accion_guardar.triggered.connect(self.guardar)
        menu.addAction(accion_guardar)

        accion_guardar_como = QAction("Guardar como...", self.ventana)
        accion_guardar_como.triggered.connect(self.guardar_como)
        menu.addAction(accion_guardar_como)

        menu.addSeparator()
        accion_salir = QAction("Salir", self.ventana)
        accion_salir.triggered.connect(self.ventana.close)
        menu.addAction(accion_salir)

    def nuevo(self):
        self.ventana.lienzo.capa_activa.fill(0)
        self.ventana.lienzo.update()
        self.ventana.archivo_actual = None
        self.ventana.setWindowTitle("PaintNotNet - Nuevo Archivo")

    def abrir(self):
        ruta, _ = QFileDialog.getOpenFileName(self.ventana, "Abrir Imagen", "", "Imágenes (*.png *.jpg *.jpeg *.bmp)")
        if ruta and self.ventana.lienzo.cargar_imagen(ruta):
            self.ventana.archivo_actual = ruta
            self.ventana.setWindowTitle(f"PaintNotNet - {ruta}")

    def guardar(self):
        if self.ventana.archivo_actual:
            self.ventana.lienzo.guardar_imagen(self.ventana.archivo_actual)
        else:
            self.guardar_como()

    def guardar_como(self):
        ruta, _ = QFileDialog.getSaveFileName(self.ventana, "Guardar Imagen", "", "Imágenes PNG (*.png);;Imágenes JPEG (*.jpg)")
        if ruta:
            if not ruta.lower().endswith(('.png', '.jpg', '.jpeg')): ruta += '.png'
            if self.ventana.lienzo.guardar_imagen(ruta):
                self.ventana.archivo_actual = ruta
                self.ventana.setWindowTitle(f"PaintNotNet - {ruta}")
