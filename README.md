<p align="center">
  <img src="gui/icono.png" width="128" alt="PaintNotNet Logo">
</p>

<h1 align="center">PaintNotNet</h1>

<p align="center">
  <b>A Paint.NET tribute image editor primarily focused on Linux.</b>
</p>

<p align="center">
  <a href="https://github.com/adrianandin0/PaintNotNet/stargazers"><img src="https://img.shields.io/github/stars/adrianandin0/PaintNotNet?style=flat-square&color=64B4FF" alt="Stars"></a>
  <a href="https://github.com/adrianandin0/PaintNotNet/issues"><img src="https://img.shields.io/github/issues/adrianandin0/PaintNotNet?style=flat-square&color=00AAFF" alt="Issues"></a>
  <a href="https://github.com/adrianandin0/PaintNotNet/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-64B4FF?style=flat-square" alt="License"></a>
  <a href="https://x.com/adrian_and_ino"><img src="https://img.shields.io/badge/X-@adrian__and__ino-black?style=flat-square&logo=x" alt="X Profile"></a>
</p>

<p align="center">
  <img src="gui/screenshot.png" alt="PaintNotNet Screenshot" width="90%">
</p>

---

## Table of Contents
- [About the Project](#about-the-project)
- [Key Features](#key-features)
- [Tools](#tools)
- [Technical Details](#technical-details)
- [Installation Guide](#installation-guide)
  - [Linux Installation (Primary Platform)](#linux-installation-primary-platform)
  - [Optional Windows Installation](#optional-windows-installation)
  - [Direct Execution from Source Code](#direct-execution-from-source-code)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Author & Contact](#author--contact)
- [Credits](#credits)

---

## About the Project

**PaintNotNet** is an image editor built with **Python 3** and **PyQt6** as a tribute to **Paint.NET**. It was created to fill the gap left by the absence of an official Linux release, providing a fast, smooth, and familiar experience for **Linux** users. While cross-platform Python allows it to run on Windows, its design and development are primarily aimed at the Linux community.

---

## Key Features

- **Modern UI**: Light and dark themes (including a theme-aware transparency checkerboard).
- **Multi-language Support (i18n)**: Spanish, English, French, and Portuguese, with live switching from *Options → User Preferences* (no restart required).
- **Layers**: Thumbnails, visibility, opacity, reordering, duplication, and merging.
- **Full History (Undo / Redo)**: Immutable document snapshots powered by Copy-on-Write.
- **Native `.pnn` Format**: Layered project format with transparency support; automatic MIME association for double-click opening.
- **Customizable Keyboard Shortcuts**: Rebind hotkeys for all tools from *Options → Keyboard Shortcuts…*.
- **Printing and PDF Export**: Direct canvas printing support and PDF document generation.
- **Online Image Search and Insert**: Search and insert images directly from Pexels, Unsplash, Pixabay, Wikimedia, etc.
- **Export Formats**: PNG, JPG, BMP, WEBP, GIF, TIFF, ICO, TGA, PDF, and native `.pnn`.
- **Image and Color Adjustments**: Exposure, color temperature, levels (input/output black & white points), sepia, posterize, brightness, contrast, hue/saturation, invert, and desaturate.
- **Advanced Color Panel**: Color wheel, RGB/HSV/CMYK sliders, and saved palette history.

---

## Tools

### Selection
| Tool | Description |
|---|---|
| Rectangle select | Select rectangular areas |
| Ellipse select | Select elliptical areas |
| Freeform lasso | Freehand contour selection |
| Magic wand | Color tolerance area selection |
| Move pixels | Move selected pixel content |
| Move selection | Move selection border frame only |
| Transform | Scale, rotate, and adjust with control handles |

### Drawing & Paint
| Tool | Description |
|---|---|
| Pencil | Precise pixel drawing; realistic mode with hardness and dust controls |
| Brush | Custom stroke width, smoothing, and tip shape |
| Eraser | Erase with configurable size and tip shape |
| Spray | Spray paint with density and dripping effects |
| Smudge | Drag and blend pixels across the canvas |
| Clone stamp | Sample a reference area and duplicate pixels elsewhere |
| Paint bucket | Fill areas by color tolerance |
| Gradient | Fill with linear or radial gradients |
| Line / Curves | Draw lines and curves with Bézier control handles |
| Shapes | Geometric shapes (Rectangles, Ellipses, Stars, Polygons, Sun, Sparkle, Diamond, etc.) |
| Text | Add text with font selection, stroke, glow, and shadow effects |
| Eyedropper | Sample color directly from the canvas |
| Zoom | Zoom in/out or select a specific area to focus |

---

## Technical Details

### Architecture (v2)

PaintNotNet is structured into modular components:

| Module | Role |
|--------|------|
| `core/canvas.py` | Main canvas widget (`CanvasWidget`): document state, history, file/image operations |
| `core/canvas_input_handler.py` | Mouse input mapping & dispatching (single event processing path) |
| `core/canvas_renderer.py` | Layer composition, transparency checkerboard, and pixel grid rendering |
| `core/opengl_canvas.py` | Optional OpenGL-accelerated canvas widget (`QOpenGLWidget`) |
| `core/layers.py` | Layer manager, composition caching, and Copy-on-Write handler |
| `core/history.py` | Undo / Redo history stack |
| `core/selection.py` | Selection engine and floating image content |
| `core/stroke_smoother.py` | Stroke smoothing (Bézier interpolation / filtering) |
| `core/theme.py` | Light/Dark theme manager and transparency pattern palette |
| `core/pnn_format.py` | Loader and saver for the native `.pnn` file format |
| `core/pexels.py` + `gui/dialogo_pexels.py` | Online image search engine and selection dialog |
| `tools/` | Individual tool classes adhering to a common event interface (`mouse_press`, `move`, `release`) |
| `gui/` | UI panels, dialogs, status bar, and layout builders |

### Key System Behaviors

- **Unified Input Pipeline**: All canvas mouse events are delegated to `CanvasInputHandler`, which handles coordinate mapping (zoom/offset), enforces Copy-on-Write only during editing tools, and registers history states when appropriate.
- **Immutable History**: Document snapshots create deep copies (`.copy()`) of every layer's `QImage`, preventing subsequent drawing operations from corrupting the undo stack.
- **Theme Consistency**: Transparency checkerboard backgrounds on the main canvas, layer thumbnails, and online search preview cards consume a single palette definition (`ThemeManager.colores_checkerboard()`).
- **Layer Management**: Opacity blending, temporary stroke layers, and floating selection overlays; thumbnails dynamically refresh on theme switches.
- **Primary Dependencies**: PyQt6, NumPy, OpenCV, Pillow, Requests (online search). Optional executable packaging via PyInstaller.

### Platforms

- **Linux** (Debian/Ubuntu, Fedora, Arch Linux, openSUSE, and derivatives)

---

## Installation Guide

Before running installers or building from source, make sure **Python 3** and **Git** are installed on your system.

---

### Linux Installation (Primary Platform)

#### Step 1: Install Python, Git, and System Dependencies
Open your terminal and run the command corresponding to your distribution:

- **Debian / Ubuntu / Linux Mint / Pop!_OS**:
  ```bash
  sudo apt update
  sudo apt install -y python3 python3-pip python3-venv git build-essential libxcb-cursor0 libegl1 libgl1 libdbus-1-3
  ```

- **Fedora / RedHat / RHEL / CentOS / AlmaLinux**:
  ```bash
  sudo dnf install -y python3 python3-pip git gcc gcc-c++ libxcb mesa-libEGL mesa-libGL dbus-libs
  ```

- **Arch Linux / Manjaro / EndeavourOS**:
  ```bash
  sudo pacman -Sy --needed --noconfirm python python-pip git base-devel libxcb libegl libgl dbus
  ```

- **openSUSE / SUSE Linux Enterprise**:
  ```bash
  sudo zypper install -y python3 python3-pip git gcc libxcb-cursor0 libEGL1 libGL1 libdbus-1-3
  ```

#### Step 2: Clone the Repository
Once Python and Git are installed, download the repository:
```bash
git clone https://github.com/adrianandin0/PaintNotNet.git
cd PaintNotNet
```

#### Step 3: Run the Automated Installer (`install.sh`)
The `install.sh` script sets up a virtual environment, installs dependencies, compiles the binary via PyInstaller, and creates desktop shortcuts:
```bash
sudo ./install.sh
```
Select your preferred language (01 - Spanish / 02 - English / 03 - French / 04 - Portuguese). Once finished, launch PaintNotNet from your application menu or by running:
```bash
paintnotnet
```

---

### Optional Windows Installation

> [!NOTE]
> **Note for Windows users**:  
> If you are on Windows, we strongly encourage you to use the official **[Paint.NET](https://www.getpaint.net/)** application. PaintNotNet was created as a tribute dedicated to the Linux community. While Python allows it to run on Windows, we encourage supporting the original software on its native platform.

#### Step 1: Install Python and Git via Winget
Open **Command Prompt (CMD)** or **PowerShell** and run:
```cmd
winget install --id Python.Python.3.12 -e & winget install --id Git.Git -e
```
*IMPORTANT*: Close your current terminal window and open a new one after installation so environment variables are refreshed.

*(Alternative without Winget)*: Download Python manually from [python.org/downloads](https://www.python.org/downloads/) (make sure to check **"Add python.exe to PATH"** during setup) and Git from [git-scm.com](https://git-scm.com/).

#### Step 2: Clone the Repository
In your **new terminal window**, run:
```cmd
git clone https://github.com/adrianandin0/PaintNotNet.git
cd PaintNotNet
```

#### Step 3: Set Up Virtual Environment & Dependencies
```cmd
python -m venv venv
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements_windows.txt pyinstaller
```

#### Step 4: Run the Windows Installer (`install.bat`)
```cmd
install.bat
```
This builds the native executable, installs it to `%LOCALAPPDATA%\PaintNotNet`, and creates shortcuts on your **Desktop** and **Start Menu**.

---

### Direct Execution from Source Code

If you prefer not to compile or install system packages, run PaintNotNet directly with Python (after completing Step 1 for your OS):

#### Linux:
```bash
git clone https://github.com/adrianandin0/PaintNotNet.git
cd PaintNotNet
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements_linux.txt
python main.py
```

#### Windows:
```cmd
git clone https://github.com/adrianandin0/PaintNotNet.git
cd PaintNotNet
python -m venv venv
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements_windows.txt
python main.py
```

---

## Troubleshooting

### 1. `python3: command not found` or `python is not recognized`
- **Cause**: Python is not installed or not added to your system's PATH variable.
- **Linux Solution**: Complete Step 1 by running `sudo apt install python3 python3-pip python3-venv` (or your distro's equivalent).
- **Windows Solution**: Run `winget install --id Python.Python.3.12 -e` and **restart your terminal**.

### 2. `git is not recognized`
- **Cause**: Git is missing or was installed without restarting the command prompt.
- **Solution**: Install Git (`winget install --id Git.Git -e` on Windows or `sudo apt install git` on Linux) and **restart your terminal**.

### 3. `pip: command not found`
- **Linux Solution**: Install pip via `sudo apt install python3-pip` (Debian/Ubuntu) or `sudo dnf install python3-pip` (Fedora).
- **Windows Solution**: Run `python -m ensurepip --upgrade`.

### 4. `externally-managed-environment` Error on Modern Linux (Debian 12+, Ubuntu 23.04+, Arch)
- **Cause**: Modern Linux distros prevent global `pip` package installation outside virtual environments.
- **Solution**: Always use a virtual environment (`python3 -m venv venv` and `source venv/bin/activate`) or run `sudo ./install.sh`, which manages environment isolation automatically.

### 5. `pyinstaller: command not found`
- **Cause**: PyInstaller is not installed inside the active virtual environment.
- **Solution**: Activate your virtual environment and run `pip install pyinstaller`.

### 6. `winget is not recognized` on Windows
- **Cause**: Older Windows 10 versions without App Installer.
- **Solution**: Manually download Python from [python.org](https://www.python.org/downloads/) (checking **"Add python.exe to PATH"**) and Git from [git-scm.com](https://git-scm.com/).

---

## Contributing

Contributions, translations, and bug reports are welcome!

- **Report a Bug**: Open an issue on [GitHub Issues](https://github.com/adrianandin0/PaintNotNet/issues).
- **Submit Code**: Fork the repository, create a feature branch, and open a Pull Request.

---

## Author & Contact

- **Developer**: Adrian
- **X (Twitter)**: [@adrian_and_ino](https://x.com/adrian_and_ino)
- **GitHub**: [adrianandin0/PaintNotNet](https://github.com/adrianandin0/PaintNotNet)

Developed in Python with assistance from **Google Gemini** and **Google Antigravity**.

---

## Credits

Special thanks to Flaticon icon creators:

| Author | Link |
|---|---|
| Flaticon | [flaticon.com](https://www.flaticon.com/) |
| Nuion | [authors/nuion](https://www.flaticon.com/authors/nuion) |
| Gungyoga04 | [authors/gungyoga04](https://www.flaticon.com/authors/gungyoga04) |
| Gulraiz | [authors/gulraiz](https://www.flaticon.com/authors/gulraiz) |
| Smashicons | [authors/smashicons](https://www.flaticon.com/authors/smashicons) |
| Magnific | [authors/magnific](https://www.flaticon.com/authors/magnific) |
| Pixel perfect | [authors/pixel-perfect](https://www.flaticon.com/authors/pixel-perfect) |
| Designspace team | [authors/designspace-team](https://www.flaticon.com/authors/designspace-team) |

---

<p align="center">If you like the project, give it a star on GitHub!</p>
