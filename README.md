<p align="center">
  <img src="gui/icono.png" width="128" alt="Logo PaintNotNet">
</p>

<h1 align="center">PaintNotNet</h1>

<p align="center">
  <b>Un editor de imágenes liviano, potente y moderno para Linux e inspirado en Paint.NET</b>
</p>

<p align="center">
  <a href="https://github.com/adrianandin0/PaintNotNet/stargazers"><img src="https://img.shields.io/github/stars/adrianandin0/PaintNotNet?style=flat-square&color=64B4FF" alt="Stars"></a>
  <a href="https://github.com/adrianandin0/PaintNotNet/issues"><img src="https://img.shields.io/github/issues/adrianandin0/PaintNotNet?style=flat-square&color=00AAFF" alt="Issues"></a>
  <a href="https://github.com/adrianandin0/PaintNotNet/blob/main/LICENSE"><img src="https://img.shields.io/github/license/adrianandin0/PaintNotNet?style=flat-square&color=64B4FF" alt="License"></a>
  <a href="https://x.com/adrian_and_ino"><img src="https://img.shields.io/badge/X-@adrian__and__ino-black?style=flat-square&logo=x" alt="X Profile"></a>
</p>

---

## 🎨 Acerca del Proyecto

**PaintNotNet** es una aplicación de edición de imágenes desarrollada en Python 3 y PyQt6. Diseñada para ofrecer una experiencia fluida, rápida y familiar para los usuarios que buscan una alternativa intuitiva a software como Paint.NET en entornos Linux.

---

## ✨ Características Principales

### 🛠️ Herramientas de Dibujo y Selección
- **Herramientas de Selección**: Selección Rectangular, Elíptica y Lasso Libre con transformación e interacción completa en el área del viewport sin recortes.
- **Herramientas de Movimiento**: Mover Contenido (`Mover Selección Pixels`) y Mover Selección (`Marco`). Permite rotar, escalar y desplazar selecciones de forma fluida.
- **Herramientas de Pintura**: Lápiz, Pincel con grosor y suavizado, Goma de Borrar, Balde de Pintura (Relleno por tolerancia) y Herramienta de Líneas/Curvas.
- **Herramientas de Texto**: Inserción de texto dinámico con fuente personalizada, tamaño, estilo (Negrita, Cursiva, Subrayado), bordes y sombras configurables.
- **Selector de Color / Cuentagotas**: Selector de colores rápido y Panel de Color Avanzado con ruedas cromáticas, sliders RGB/HSV/CMYK e historial de colores guardados.

### 📚 Manejo de Capas e Historial
- **Sistema de Capas Completo**: Creación, duplicación, reordenamiento, combinación hacia abajo, eliminación y alternado de visibilidad de capas.
- **Historial Completo (Undo / Redo)**: Motor de snapshots para deshacer (`Ctrl+Z`) y rehacer (`Ctrl+Y`) cualquier acción o modificación de tamaño.
- **Formato Nativo `.pnn`**: Guarda y carga proyectos completos preservando capas, transparencias y estructuras de trabajo.

### 🖼️ Manejo de Lienzo e Imágenes
- **Área de Trabajo Ilimitada**: Manipulación de tiradores y marcos de selección extendidos por todo el espacio oscuro del viewport.
- **Redimensionado Inteligente**: "Tamaño del Lienzo..." y "Tamaño de la Imagen..." (adaptativo a la selección o al lienzo entero con opción de centrado).
- **Ajustes de Imagen**: Inversión de colores, escala de grises (blanco y negro), brillo/contraste y tono/saturación.
- **Detección del Portapapeles**: Sugiere automáticamente las dimensiones de imágenes copiadas en el portapapeles al crear nuevos lienzos (`Ctrl+N`).

---

## 🚀 Instalación y Uso

### Requisitos Previos
- Python 3.10 o superior
- PyQt6

### Ejecutar desde el Código Fuente

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/adrianandin0/PaintNotNet.git
   cd PaintNotNet
   ```

2. **Crear y activar un entorno virtual:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación:**
   ```bash
   python main.py
   ```

---

## 🤝 Colaboración y Sugerencias

¡Todas las contribuciones, sugerencias de características y reportes de errores son más que bienvenidos!

- **Reportar un error o sugerir una mejora**: Abre un [Issue en GitHub](https://github.com/adrianandin0/PaintNotNet/issues).
- **Enviar código**: Haz un fork del repositorio, crea una rama con tus cambios y envía un Pull Request.

---

## 👤 Autor y Contacto

- **Desarrollador**: Adrian
- **X (Twitter)**: [@adrian_and_ino](https://x.com/adrian_and_ino)
- **GitHub**: [adrianandin0/PaintNotNet](https://github.com/adrianandin0/PaintNotNet)

Desarrollado en Python con la asistencia de **Google Gemini** y **Google Antigravity**.

---

## 📜 Créditos de Recursos Gráficos

Agradecimientos a los creadores e ilustradores del material gráfico e íconos utilizados en la aplicación:

- [Flaticon](https://www.flaticon.com/)
- Autor [Magnific](https://www.flaticon.com/authors/magnific)
- Autor [Uniconlabs](https://www.flaticon.com/authors/uniconlabs)
- Autor [Balraj Chana](https://www.flaticon.com/authors/balraj-chana)
- Autor [Gajah Mada](https://www.flaticon.com/authors/gajah-mada)

---

<p align="center">⭐ Si te gusta el proyecto, ¡no olvides darle una estrella en GitHub! ⭐</p>
