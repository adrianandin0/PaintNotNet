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
- **Pintura y Efectos**: Lápiz, Pincel (con grosor y suavizado), Goma de Borrar, Balde de Pintura, Degradado, Herramienta de Líneas/Curvas, Aerosol, Difuminado y Estampa.
- **Ajustes de Imagen y Color**: Exposición, Temperatura de Color, Niveles (puntos negro/blanco de entrada y salida), Sepia, Posterizado, Brillo, Contraste, Tono/Saturación, Invertir Colores y Desaturar.
- **Inserción de Texto y Formas**: Formas geométricas ajustables (Rectángulos, Elipses, Estrellas, Polígonos con bordes redondeados) y motor de texto dinámico.
- **Selector de Color**: Panel de Color Avanzado (rueda cromática, sliders RGB/HSV/CMYK e historial de paletas).

#### 📚 Capas, Historial y Formato Nativo `.pnn`
- **Gestión de Capas**: Creación, duplicación, reordenamiento, combinación hacia abajo, eliminación y alternado de visibilidad.
- **Historial Completo (Undo / Redo)**: Deshacer (`Ctrl+Z`) y rehacer (`Ctrl+Y`) con previsualización en vivo.
- **Formato Nativo `.pnn`**: Guarda proyectos preservando capas, transparencias y estados de trabajo. Asociación automática al hacer doble clic en archivos `.pnn`.

#### ⌨️ Atajos de Teclado Personalizables
- **Configuración de Atajos**: Personaliza las teclas de acceso rápido para todas las 18 herramientas desde *Opciones -> Atajos de teclado...* con actualización de insignias en tiempo real.

### 🆕 Novedades en la Versión 1.0.6
- 🎛️ **Nuevos Ajustes de Imagen y Color**:
  - **Exposición**: Control preciso de luminancia y sobreexposición sin saturar blancos.
  - **Temperatura de Color**: Ajuste de balance de blancos térmico para lograr tonos cálidos o fríos.
  - **Niveles de Color (Input/Output Levels)**: Calibración independiente de puntos de entrada/salida (*Input Black/White*, *Output Black/White*) con previsualización directa.
  - **Efecto Sepia**: Aplicación de virado sepia fotográfico vintage con ajuste de intensidad.
  - **Posterizado**: Reducción de niveles de cuantización por canal cromático para estilos retro/arte pop.
- 🎨 **Diálogo Selector de Color Integrado (`SingleColorPickerDialog`)**:
  - Selector de color independiente para efectos de texto (**Borde**, **Resplandor** y **Sombra**).
  - Muestra de color con transparencia y slider de Alfa ($0$ a $255$), Rueda de Color HSV (`ColorWheel`), paleta fija de 70 colores ($7\times 10$) y campos numéricos/sliders para RGB, Hexadecimal y HSV.
  - Sincronización persistente en tiempo real de los 21 slots de colores guardados de usuario entre el menú lateral y los diálogos de efectos.
  - Previsualización en vivo en el lienzo con botones de **Aceptar** y **Cancelar** (restauración inmediata del color original al cancelar).
- 🎯 **Sincronización Completa de Alineación de Selección**:
  - Corrección en `align_selection()` para desplazar coordinadamente el área seleccionada, la imagen flotante, la ruta vectorial, el centro de rotación y los 8 tiradores de control (*handles*).
  - Solución al problema de desfasaje de coordenadas `QPointF(0,0)` en evaluaciones booleanas de PyQt6 al alinear secuencialmente (*Arriba* $\rightarrow$ *Izquierda* $\rightarrow$ *Abajo*).
- ⌨️ **Movimiento de Selección por Teclado e Historial**:
  - Movimiento preciso de la selección píxel a píxel usando las flechas del teclado (con o sin contenido flotante).
  - Integración total con el historial de deshacer (`Ctrl+Z`) para revertir desplazamientos por teclado paso a paso sin perder la selección ni alterar el contenido del lienzo.
- 💬 **Notificaciones del Sistema e Interfaz**:
  - Aviso flotante *"Autoguardado"* / *"Autosaved"* en la barra de estado inferior en texto itálico sin negrita al completarse el autoguardado de seguridad.
  - Formato de 11px uniforme para menús de ajustes (*Niveles*, *Posterizar*, *Ajustes de Color*), centrado de encabezados e inspección visual mejorada para botones de reinicio (*reset*) en tema claro.
  - Diálogo **Acerca de PaintNotNet** actualizado e integración del nuevo logo oficial de la aplicación en el instalador y sistema Freedesktop / KDE.

### 🆕 Novedades en la Versión 1.0.5
- 🆘 **Autoguardado de Emergencia Multicapa (.pnn)**:
  - Sistema de respaldo automático silencioso que guarda periódicamente los lienzos abiertos en formato nativo `.pnn` (`{lienzo}_{DDMMAAAA}_{HHMMSS}.pnn`).
  - Preserva **todas las capas individuales** con sus metadatos (nombre, visibilidad, opacidad) y contenido transparente sin acoplar para continuar trabajando exactamente en el mismo estado tras un cierre inesperado.
  - Diálogo interactivo al iniciar la aplicación tras una falla para restaurar o descartar permanentemente los borradores de emergencia.
  - Eliminación automática de respaldos temporales al guardar formalmente la imagen o al cerrar la aplicación normalmente.
- 🔄 **Motor de Transformación de Selección Compuesta**:
  - Re-arquitectura del motor de selección (`SelectionEngine`) usando transformaciones afines compuestas de pasada única directamente desde la imagen original pura sin pérdida incremental de calidad.
  - Solución al bucle de retroalimentación exponencial al escalar selecciones rotadas.
  - Sincronización perfecta de los 8 tiradores de control en el historial de deshacer (`Ctrl+Z`) y eliminación total de copias de imagen fantasma en el lienzo.
- 🖌️ **Suavizado de Trazo y Uniones Redondeadas en Pincel**:
  - Filtrado de puntos duplicados/cercanos (< 1.5px) y configuración de `RoundJoin` con `miterLimit = 2.0` para eliminar picos y cortes triangulares en giros cerrados.
- 🌐 **Internacionalización y Limpieza de Interfaz**:
  - Traducción al español e inglés de diálogos de Redimensionar Imagen, Redimensionar Lienzo, Restauración de Emergencia y notificaciones del sistema.
  - Desactivación del menú contextual por defecto al hacer clic derecho sobre la barra superior de menú/herramientas o selector de paneles.

### 🆕 Novedades en la Versión 1.0.4
- 🎨 **3 Nuevas Herramientas**:
  - **Aerosol (Spray Paint)**: Pinta en un área circular con efecto aerosol, afectado por tamaño, alfa y suavizado.
  - **Difuminar (Smudge)**: Difumina y arrastra píxeles en el lienzo con intensidad regulable.
  - **Estampa (Stamp)**: Estampa y mecha patrones o muestras sobre el lienzo.
- 📐 **Mejoras en Creación de Lienzo**:
  - **Perfiles de Color y DPI**: Selector de espacio de color (*sRGB*, *Display P3*, *Adobe RGB*) y densidad de píxeles (*72, 96, 150, 300 DPI*).
  - **Guardado Predeterminado**: *"Establecer como predeterminado"* guarda dimensiones del lienzo, color de fondo, perfil de color y DPI.
  - **Formas Geométricas**: Nueva forma vectorizada de **Mano** (*pointing hand*) añadida junto a Rectángulo, Triángulo, Elipse, Nube, Corazón, Chat, Estrella y Flor.
  - **Forma de Pincel en Barra Superior**: Alterna entre forma **Circular** y **Cuadrada** directo desde la barra de herramientas.
  - **Alineación de Texto y Cuadros**: Justificado de texto y botones de alineación en la barra inferior para reubicar cuadros de texto activos.
  - **Degradado Transparente**: Modo de degradado desde color sólido hasta transparencia de alfa 0.
  - **Inserción Inteligente de Imágenes**: Opciones de *"Ajustar lienzo"*, *"Adaptar imagen"* e *"Insertar sin cambios"* para imágenes de archivo e internet.
  - **Interfaz Liviana**: Eliminación de paneles laterales redundantes.

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
- **Paint & FX Tools**: Pencil, Paintbrush (with width and smoothing), Eraser, Paint Bucket, Gradient, Line/Curve Tool, Spray Paint, Smudge, and Stamp.
- **Image & Color Adjustments**: Exposure, Color Temperature, Color Levels (Input/Output Black & White points), Sepia, Posterize, Brightness, Contrast, Hue/Saturation, Invert Colors, and Desaturate.
- **Text & Shapes**: Adjustable geometric shapes (Rectangles, Ellipses, Stars, Polygons with rounded corners) and dynamic text layer engine.
- **Color Picker**: Advanced Color Panel (color wheel, RGB/HSV/CMYK sliders, and saved palette history).

#### 📚 Layers, History & Native `.pnn` Format
- **Layer Management**: Create, duplicate, reorder, merge down, delete, and toggle layer visibility.
- **Complete History (Undo / Redo)**: Undo (`Ctrl+Z`) and Redo (`Ctrl+Y`) with live snapshot previews.
- **Native `.pnn` Project Format**: Save projects preserving layers, transparency, and structure. Automatic MIME file association for double-clicking `.pnn` files.

#### ⌨️ Customizable Keyboard Shortcuts
- **Shortcut Configuration**: Customize keyboard shortcut keys for all 21 tools from *Options -> Keyboard Shortcuts...* with real-time badge updates.

### 🆕 What's New in Version 1.0.6
- 🎛️ **New Color & Image Adjustments**:
  - **Exposure**: Fine luminance and overexposure control without clipping highlights.
  - **Color Temperature**: Thermal white balance adjustment for warm or cool tones.
  - **Color Levels (Input/Output Levels)**: Independent calibration of Input/Output Black/White points with real-time canvas preview.
  - **Sepia Effect**: Vintage photographic sepia toning with adjustable intensity.
  - **Posterize**: Color channel quantization level reduction for retro/pop-art styling.
- 🎨 **Dedicated Single Color Picker Dialog (`SingleColorPickerDialog`)**:
  - Integrated color selection dialog for text effects (**Border**, **Glow**, and **Shadow**).
  - Features alpha transparency preview swatch and slider ($0$ to $255$), HSV Color Wheel (`ColorWheel`), 70-color standard palette grid ($7\times 10$), and RGB/Hex/HSV numeric inputs and sliders.
  - Real-time persistent synchronization of 21 custom saved user slots across the side panel and text effect dialogs.
  - Live canvas preview with **OK** and **Cancel** buttons (instant reversion to original color upon cancellation).
- 🎯 **Synchronized Selection Alignment & Handles**:
  - Fixes `align_selection()` to shift the selection rect, floating content, vector clip path, rotation center, and all 8 control handles in unison.
  - Resolves coordinate evaluation edge cases (`QPointF(0,0)` PyQt6 boolean check) during sequential canvas alignments (*Top* $\rightarrow$ *Left* $\rightarrow$ *Bottom*).
- ⌨️ **Keyboard Selection Movement & Undo Support**:
  - Precise pixel-by-pixel arrow key movement for active selections and floating pixel content.
  - Full integration with the Undo stack (`Ctrl+Z`) to revert step-by-step arrow key movements without dropping active selections.
- 💬 **System Notifications & UI Polish**:
  - Floating italic *"Autoguardado"* / *"Autosaved"* status bar notifications upon background emergency save completion.
  - Standardized 11px font across all adjustment dialogs (*Levels*, *Posterize*, etc.), centered header titles, and improved hover contrast for slider reset buttons in light theme.
  - Redesigned **About PaintNotNet** dialog and system-wide Freedesktop / KDE desktop integration with the new application logo.

### 🆕 What's New in Version 1.0.5
- 🆘 **Multi-layer Emergency Auto-Save (.pnn)**: Background auto-save of active open canvases in native `.pnn` format (`{canvas}_{DDMMAAAA}_{HHMMSS}.pnn`). Preserves **all individual layers** with complete metadata (name, visibility, opacity) and un-flattened structure. Interactive recovery dialog on startup. Auto-cleanup upon formal save or clean exit.
- 🔄 **Single-Pass Compound Selection Transformations**: Re-architected `SelectionEngine` using single-pass compound affine matrix transformations operating directly on original raw image data with zero loss. Synchronized handle positions during Undo (`Ctrl+Z`) and eliminated ghost image artifacts.
- 🖌️ **Brush Stroke Smoothing & Clean Joins**: Point distance filtering (< 1.5px) and `RoundJoin` with `miterLimit = 2.0` to eliminate triangular miter spikes on sharp turns.
- 🌐 **Full i18n & Interface Polish**: Complete Spanish and English translations for Resize Canvas, Resize Image, and Emergency Recovery dialogs. Disabled default right-click context menus on top toolbars and panel titles.

### 🆕 What's New in Version 1.0.4
- 🎨 **3 New Tools**: **Spray Paint**, **Smudge Tool**, and **Stamp Tool**.
- 📐 **Enhanced Canvas Setup**: Color profile selection (*sRGB*, *Display P3*, *Adobe RGB*), DPI density controls, and unified *"Set as default"* preset persistence.
- ✨ **Tool & UI Polish**: Top toolbar brush shape toggle (**Circular** / **Square**), text box canvas alignment from bottom bar, transparency gradient mode, and smart image import dialog (*"Expand Canvas"*, *"Fit Image"*, *"Keep Original Size"*).

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
