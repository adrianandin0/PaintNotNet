<p align="center">
  <img src="gui/icono.png" width="128" alt="PaintNotNet Logo">
</p>

<h1 align="center">PaintNotNet</h1>

<p align="center">
  <b>Un editor de imágenes liviano, potente y moderno para Linux e inspirado en Paint.NET</b><br>
  <b>A lightweight, powerful, and modern image editor for Linux inspired by Paint.NET</b>
</p>

<p align="center">
  <a href="https://github.com/adrianandin0/PaintNotNet/stargazers"><img src="https://img.shields.io/github/stars/adrianandin0/PaintNotNet?style=flat-square&color=64B4FF" alt="Stars"></a>
  <a href="https://github.com/adrianandin0/PaintNotNet/issues"><img src="https://img.shields.io/github/issues/adrianandin0/PaintNotNet?style=flat-square&color=00AAFF" alt="Issues"></a>
  <a href="https://github.com/adrianandin0/PaintNotNet/blob/main/LICENSE"><img src="https://img.shields.io/github/license/adrianandin0/PaintNotNet?style=flat-square&color=64B4FF" alt="License"></a>
  <a href="https://x.com/adrian_and_ino"><img src="https://img.shields.io/badge/X-@adrian__and__ino-black?style=flat-square&logo=x" alt="X Profile"></a>
</p>

<p align="center">
  <img src="gui/screenshot.png" alt="PaintNotNet Screenshot" width="90%">
</p>

---

## 🌐 Language / Idioma
- 🇪🇸 [Español](#-acerca-del-proyecto-español)
- 🇬🇧 [English](#-about-the-project-english)

---

## 🇪🇸 Acerca del Proyecto (Español)

**PaintNotNet** es una aplicación de edición de imágenes desarrollada en Python 3 y PyQt6. Diseñada para ofrecer una experiencia fluida, rápida y familiar para los usuarios que buscan una alternativa intuitiva a software como Paint.NET en entornos Linux y Windows.

### ✨ Características Principales

#### 🌐 Soporte Multi-Idioma (i18n)
- **Cambio de Idioma en Vivo**: Soporte nativo para **Español** e **Inglés**. Permite alternar el idioma de menús, herramientas y diálogos instantáneamente sin reiniciar desde *Opciones -> Preferencias de usuario*.
- **Instalador Interactivo en Linux**: `install.sh` consulta el idioma deseado al inicio y pre-configura la aplicación automáticamente.

#### 🛠️ Herramientas de Dibujo, Selección y Formas
- **Herramientas de Selección**: Selección Rectangular, Elíptica, Lasso Libre y Varita Mágica por tolerancia.
- **Transformación Libre**: Mover Contenido (`V`), Mover Selección (`M`) e Invertir Selección (`I`) sin límites de lienzo.
- **Pintura y Efectos**: Lápiz, Pincel (con grosor y suavizado), Goma de Borrar, Balde de Pintura, Degradado, Herramienta de Líneas/Curvas y Difuminado.
- **Inserción de Texto y Formas**: Formas geométricas ajustables (Rectángulos, Elipses, Estrellas, Polígonos con bordes redondeados) y motor de texto dinámico.
- **Selector de Color**: Panel de Color Avanzado (rueda cromática, sliders RGB/HSV/CMYK e historial de paletas).

#### 📚 Capas, Historial y Formato Nativo `.pnn`
- **Gestión de Capas**: Creación, duplicación, reordenamiento, combinación hacia abajo, eliminación y alternado de visibilidad.
- **Historial Completo (Undo / Redo)**: Deshacer (`Ctrl+Z`) y rehacer (`Ctrl+Y`) con previsualización en vivo.
- **Formato Nativo `.pnn`**: Guarda proyectos preservando capas, transparencias y estados de trabajo. Asociación automática al hacer doble clic en archivos `.pnn`.

#### ⌨️ Atajos de Teclado Personalizables
- **Configuración de Atajos**: Personaliza las teclas de acceso rápido para todas las 18 herramientas desde *Opciones -> Atajos de teclado...* con actualización de insignias en tiempo real.

---

## 🇬🇧 About the Project (English)

**PaintNotNet** is an image editing application built with Python 3 and PyQt6. Designed to deliver a smooth, fast, and familiar workflow for users seeking an intuitive alternative to tools like Paint.NET on Linux and Windows.

### ✨ Key Features

#### 🌐 Multi-Language Support (i18n)
- **Live Language Switcher**: Native support for **Spanish** and **English**. Switch menu titles, tooltips, and dialogs dynamically without restarting from *Options -> User Preferences*.
- **Interactive Linux Installer**: `install.sh` prompts for your preferred language upfront and sets it as the default automatically.

#### 🛠️ Drawing, Selection & Shape Tools
- **Selection Tools**: Rectangle, Ellipse, Freeform Lasso, and Magic Wand with tolerance selection.
- **Free Transformation**: Move Selected Pixels (`V`), Move Selection (`M`), and Invert Selection (`I`) beyond viewport boundaries.
- **Paint & FX Tools**: Pencil, Paintbrush (with width and smoothing), Eraser, Paint Bucket, Gradient, Line/Curve Tool, and Blur.
- **Text & Shapes**: Adjustable geometric shapes (Rectangles, Ellipses, Stars, Polygons with rounded corners) and dynamic text layer engine.
- **Color Picker**: Advanced Color Panel (color wheel, RGB/HSV/CMYK sliders, and saved palette history).

#### 📚 Layers, History & Native `.pnn` Format
- **Layer Management**: Create, duplicate, reorder, merge down, delete, and toggle layer visibility.
- **Complete History (Undo / Redo)**: Undo (`Ctrl+Z`) and Redo (`Ctrl+Y`) with live snapshot previews.
- **Native `.pnn` Project Format**: Save projects preserving layers, transparency, and structure. Automatic MIME file association for double-clicking `.pnn` files.

#### ⌨️ Customizable Keyboard Shortcuts
- **Shortcut Configuration**: Customize keyboard shortcut keys for all 18 tools from *Options -> Keyboard Shortcuts...* with real-time badge updates.

---

## 🚀 Instalación y Uso / Installation & Usage

### 🐧 Linux (Recomendado / Recommended)

#### Opción A: Instalador Automático / Automatic Installer
```bash
git clone https://github.com/adrianandin0/PaintNotNet.git
cd PaintNotNet
sudo ./install.sh
```
Una vez instalado, inicia PaintNotNet desde el menú de aplicaciones (**Gráficos -> PaintNotNet**) o desde la terminal:
```bash
paintnotnet
```

#### Opción B: Código Fuente en Linux / Source Code on Linux
```bash
git clone https://github.com/adrianandin0/PaintNotNet.git
cd PaintNotNet
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_linux.txt
python main.py
```

---

### 🪟 Windows

```cmd
git clone https://github.com/adrianandin0/PaintNotNet.git
cd PaintNotNet
python -m venv venv
venv\Scripts\activate
pip install -r requirements_windows.txt
python main.py
```

---

## 🤝 Colaboración / Contributing

¡Todas las contribuciones, traducciones y reportes de errores son bienvenidos!
Contributions, translations, and bug reports are welcome!

- **Reportar un error / Bug Report**: Abre un [Issue en GitHub](https://github.com/adrianandin0/PaintNotNet/issues).
- **Enviar código / Pull Request**: Haz un fork del repositorio, crea una rama con tus cambios y envía un Pull Request.

---

## 👤 Autor y Contacto / Author & Contact

- **Desarrollador / Developer**: Adrian
- **X (Twitter)**: [@adrian_and_ino](https://x.com/adrian_and_ino)
- **GitHub**: [adrianandin0/PaintNotNet](https://github.com/adrianandin0/PaintNotNet)

Desarrollado en Python con la asistencia de **Google Gemini** y **Google Antigravity**.

---

## 📜 Créditos / Credits

Agradecimientos a los ilustradores y diseñadores de íconos / Special thanks to Flaticon icon creators:

| Autor / Author | ES | EN |
|---|---|---|
| Flaticon | [flaticon.es](https://www.flaticon.es/) | [flaticon.com](https://www.flaticon.com/) |
| Nuion | [autores/nuion](https://www.flaticon.es/autores/nuion) | [authors/nuion](https://www.flaticon.com/authors/nuion) |
| Gungyoga04 | [autores/gungyoga04](https://www.flaticon.es/autores/gungyoga04) | [authors/gungyoga04](https://www.flaticon.com/authors/gungyoga04) |
| Gulraiz | [autores/gulraiz](https://www.flaticon.es/autores/gulraiz) | [authors/gulraiz](https://www.flaticon.com/authors/gulraiz) |
| Smashicons | [autores/smashicons](https://www.flaticon.es/autores/smashicons) | [authors/smashicons](https://www.flaticon.com/authors/smashicons) |
| Magnific | [autores/magnific](https://www.flaticon.es/autores/magnific) | [authors/magnific](https://www.flaticon.com/authors/magnific) |
| Pixel perfect | [autores/pixel-perfect](https://www.flaticon.es/autores/pixel-perfect) | [authors/pixel-perfect](https://www.flaticon.com/authors/pixel-perfect) |
| Designspace team | [autores/designspace-team](https://www.flaticon.es/autores/designspace-team) | [authors/designspace-team](https://www.flaticon.com/authors/designspace-team) |

---

<p align="center">⭐ Si te gusta el proyecto, ¡no olvides darle una estrella en GitHub! / If you like the project, give it a star on GitHub! ⭐</p>
