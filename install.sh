#!/usr/bin/env bash
# ==============================================================================
# PaintNotNet v1.0.9dev - Instalador Universal para Distribuciones Linux
# (Debian, Ubuntu, Linux Mint, Fedora, RHEL, CentOS, Arch, Manjaro, openSUSE, etc.)
# ==============================================================================

set -e

COLOR_BLUE='\033[0;34m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_RESET='\033[0m'

# 1. Verificar permisos de superusuario
if [ "$EUID" -ne 0 ]; then
    echo -e "${COLOR_RED}[!] Error: Este instalador requiere permisos de administrador (root).${COLOR_RESET}"
    echo -e "${COLOR_RED}[!] Error: This installer requires root privileges.${COLOR_RESET}"
    echo -e "    Por favor ejecuta el comando con sudo / Please run with sudo:"
    echo -e "    ${COLOR_YELLOW}sudo ./install.sh${COLOR_RESET}"
    exit 1
fi

echo -e "${COLOR_BLUE}==============================================================${COLOR_RESET}"
echo -e "${COLOR_BLUE}        PaintNotNet v1.0.9dev - Linux Installer / Instalador ${COLOR_RESET}"
echo -e "${COLOR_BLUE}==============================================================${COLOR_RESET}"
echo ""

# 2. Selección de Idioma / Language Selection
echo -e "${COLOR_YELLOW}Language / Idioma:${COLOR_RESET}"
echo "  01 - Español"
echo "  02 - English"
echo "  03 - Português"
echo "  04 - Français"
echo ""
read -rp "Elija una opción / Choose an option [01]: " LANG_CHOICE

case "$LANG_CHOICE" in
    2|02|[Ee][Nn]|[Ee][Nn][Gg][Ll][Ii][Ss][Hh]|[Ii][Nn][Gg][Ll][Ee][Ss]|[Ii][Nn][Gg][Ll][Éé][Ss])
        SELECTED_LANG="English"
        ;;
    3|03|[Pp][Tt]|[Pp][Oo][Rr][Tt][Uu][Gg][Uu][ÊêEe][Ss])
        SELECTED_LANG="Português"
        ;;
    4|04|[Ff][Rr]|[Ff][Rr][Aa][Nn][ÇçCc][Aa][Ii][Ss]|[Ff][Rr][Aa][Nn][Cc][ÉéEe][Ss])
        SELECTED_LANG="Français"
        ;;
    *)
        SELECTED_LANG="Español"
        ;;
esac

echo ""
if [ "$SELECTED_LANG" = "English" ]; then
    HEADER_TITLE="         PaintNotNet Installer for Linux                    "
    MSG_COMPILING="[i] Compiling the latest version of PaintNotNet..."
    MSG_NO_PYINSTALLER="[i] Installing Python dependencies & PyInstaller..."
    MSG_STEP1="[1/4] Checking system dependencies (Python / Pip / Qt6 / OpenGL)..."
    MSG_DISTRO_DEBIAN="      Debian/Ubuntu based distribution detected (apt)."
    MSG_DISTRO_FEDORA="      Fedora/RedHat based distribution detected (dnf)."
    MSG_DISTRO_ARCH="      Arch Linux/Manjaro based distribution detected (pacman)."
    MSG_DISTRO_SUSE="      openSUSE based distribution detected (zypper)."
    MSG_STEP2="[2/4] Installing application files in"
    MSG_STEP3="[3/4] Creating desktop shortcuts and installing system icons..."
    MSG_STEP4="[4/4] Finalizing installation..."
    MSG_SUCCESS="      PaintNotNet installed successfully!                   "
    MSG_LAUNCH=" You can launch the application from:"
    MSG_LAUNCH_1="   1. Your system application menu (Graphics -> PaintNotNet)"
    MSG_LAUNCH_2="   2. Or typing in any terminal:"
    MSG_UNINSTALL=" To uninstall the program in the future, run:"
    MSG_UNINSTALL_DONE="PaintNotNet has been completely uninstalled from the system."
    MSG_DESKTOP_COMMENT="Lightweight, powerful, and modern image editor for Linux"
    MSG_MIME_COMMENT="PaintNotNet Image Project"
elif [ "$SELECTED_LANG" = "Português" ]; then
    HEADER_TITLE="         Instalador do PaintNotNet para Linux                "
    MSG_COMPILING="[i] Compilando a versão mais recente do PaintNotNet..."
    MSG_NO_PYINSTALLER="[i] Instalando dependências do Python e PyInstaller..."
    MSG_STEP1="[1/4] Verificando dependências do sistema (Python / Pip / Qt6 / OpenGL)..."
    MSG_DISTRO_DEBIAN="      Distribuição baseada em Debian/Ubuntu detectada (apt)."
    MSG_DISTRO_FEDORA="      Distribuição baseada em Fedora/RedHat detectada (dnf)."
    MSG_DISTRO_ARCH="      Distribuição baseada em Arch Linux/Manjaro detectada (pacman)."
    MSG_DISTRO_SUSE="      Distribuição baseada em openSUSE detectada (zypper)."
    MSG_STEP2="[2/4] Instalando arquivos do programa em"
    MSG_STEP3="[3/4] Criando atalhos na área de trabalho e ícones do sistema..."
    MSG_STEP4="[4/4] Finalizando instalação..."
    MSG_SUCCESS="      O PaintNotNet foi instalado com sucesso!               "
    MSG_LAUNCH=" Você pode iniciar o aplicativo a partir de:"
    MSG_LAUNCH_1="   1. Menu de aplicativos do sistema (Gráficos -> PaintNotNet)"
    MSG_LAUNCH_2="   2. Ou digitando em qualquer terminal:"
    MSG_UNINSTALL=" Para desinstalar o programa no futuro, execute:"
    MSG_UNINSTALL_DONE="O PaintNotNet foi completamente desinstalado do sistema."
    MSG_DESKTOP_COMMENT="Editor de imagens leve, potente e moderno para Linux"
    MSG_MIME_COMMENT="Projeto de Imagem PaintNotNet"
elif [ "$SELECTED_LANG" = "Français" ]; then
    HEADER_TITLE="         Installeur de PaintNotNet pour Linux                "
    MSG_COMPILING="[i] Compilation de la dernière version de PaintNotNet..."
    MSG_NO_PYINSTALLER="[i] Installation des dépendances Python et PyInstaller..."
    MSG_STEP1="[1/4] Vérification des dépendances système (Python / Pip / Qt6 / OpenGL)..."
    MSG_DISTRO_DEBIAN="      Distribution basée sur Debian/Ubuntu détectée (apt)."
    MSG_DISTRO_FEDORA="      Distribution basée sur Fedora/RedHat détectée (dnf)."
    MSG_DISTRO_ARCH="      Distribution basée sur Arch Linux/Manjaro détectée (pacman)."
    MSG_DISTRO_SUSE="      Distribution basée sur openSUSE détectée (zypper)."
    MSG_STEP2="[2/4] Installation des fichiers de l'application dans"
    MSG_STEP3="[3/4] Création des raccourcis et installation des icônes du système..."
    MSG_STEP4="[4/4] Finalisation de l'installation..."
    MSG_SUCCESS="      PaintNotNet a été installé avec succès !               "
    MSG_LAUNCH=" Vous pouvez lancer l'application depuis :"
    MSG_LAUNCH_1="   1. Le menu d'applications système (Graphisme -> PaintNotNet)"
    MSG_LAUNCH_2="   2. Ou en tapant dans n'importe quel terminal :"
    MSG_UNINSTALL=" Pour désinstaller le programme à l'avenir, exécutez :"
    MSG_UNINSTALL_DONE="PaintNotNet a été complètement désinstallé du système."
    MSG_DESKTOP_COMMENT="Éditeur d'images léger, puissant et moderne pour Linux"
    MSG_MIME_COMMENT="Projet d'image PaintNotNet"
else
    HEADER_TITLE="         Instalador de PaintNotNet para Linux                "
    MSG_COMPILING="[i] Compilando la versión más reciente de PaintNotNet..."
    MSG_NO_PYINSTALLER="[i] Instalando dependencias de Python y PyInstaller..."
    MSG_STEP1="[1/4] Verificando dependencias del sistema (Python / Pip / Qt6 / OpenGL)..."
    MSG_DISTRO_DEBIAN="      Distribución basada en Debian/Ubuntu detectada (apt)."
    MSG_DISTRO_FEDORA="      Distribución basada en Fedora/RedHat detectada (dnf)."
    MSG_DISTRO_ARCH="      Distribución basada en Arch Linux/Manjaro detectada (pacman)."
    MSG_DISTRO_SUSE="      Distribución basada en openSUSE detectada (zypper)."
    MSG_STEP2="[2/4] Instalando archivos del programa en"
    MSG_STEP3="[3/4] Creando accesos directos e instalando íconos del sistema..."
    MSG_STEP4="[4/4] Finalizando instalación..."
    MSG_SUCCESS="      ¡PaintNotNet se ha instalado exitosamente!             "
    MSG_LAUNCH=" Puedes iniciar la aplicación desde:"
    MSG_LAUNCH_1="   1. El menú de aplicaciones de tu sistema (Gráficos -> PaintNotNet)"
    MSG_LAUNCH_2="   2. O escribiendo en cualquier terminal:"
    MSG_UNINSTALL=" Para desinstalar el programa en el futuro, ejecuta:"
    MSG_UNINSTALL_DONE="PaintNotNet ha sido desinstalado por completo del sistema."
    MSG_DESKTOP_COMMENT="Editor de imágenes liviano, potente y moderno para Linux"
    MSG_MIME_COMMENT="Proyecto de Imagen PaintNotNet"
fi

echo -e "${COLOR_BLUE}==============================================================${COLOR_RESET}"
echo -e "${COLOR_BLUE}${HEADER_TITLE}${COLOR_RESET}"
echo -e "${COLOR_BLUE}==============================================================${COLOR_RESET}"
echo ""

# Ubicación actual del script y paquete fuente
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_SOURCE="${SCRIPT_DIR}/dist_pkg/PaintNotNet"

# Limpiar carpetas de compilaciones antiguas que requerían root
rm -rf "${SCRIPT_DIR}/build" "${SCRIPT_DIR}/dist" "${SCRIPT_DIR}/build_pkg" "${SCRIPT_DIR}/dist_pkg"

# 3. Diagnóstico e instalación de dependencias del sistema según la distribución
echo -e "${COLOR_YELLOW}${MSG_STEP1}${COLOR_RESET}"

if command -v apt-get &> /dev/null; then
    echo -e "${MSG_DISTRO_DEBIAN}"
    apt-get update -qq
    apt-get install -y -qq python3 python3-pip python3-venv build-essential \
        libxcb-cursor0 libegl1 libgl1 libdbus-1-3 \
        libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 \
        libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxcb-xfixes0 &> /dev/null

elif command -v dnf &> /dev/null; then
    echo -e "${MSG_DISTRO_FEDORA}"
    dnf install -y -q python3 python3-pip gcc gcc-c++ \
        libxcb libX11-xcb mesa-libEGL mesa-libGL dbus-libs &> /dev/null

elif command -v pacman &> /dev/null; then
    echo -e "${MSG_DISTRO_ARCH}"
    pacman -Sy --needed --noconfirm python python-pip base-devel \
        libxcb libegl libgl dbus &> /dev/null

elif command -v zypper &> /dev/null; then
    echo -e "${MSG_DISTRO_SUSE}"
    zypper install -y -q python3 python3-pip gcc \
        libxcb-cursor0 libEGL1 libGL1 libdbus-1-3 &> /dev/null
fi

# 4. Verificación y preparación del entorno de Python + PyInstaller
PYINSTALLER_BIN=""

if [ -f "${SCRIPT_DIR}/venv/bin/pyinstaller" ]; then
    PYINSTALLER_BIN="${SCRIPT_DIR}/venv/bin/pyinstaller"
elif command -v pyinstaller &> /dev/null; then
    PYINSTALLER_BIN="$(command -v pyinstaller)"
fi

if [ -z "$PYINSTALLER_BIN" ]; then
    echo -e "${COLOR_YELLOW}${MSG_NO_PYINSTALLER}${COLOR_RESET}"
    if [ ! -d "${SCRIPT_DIR}/venv" ]; then
        python3 -m venv "${SCRIPT_DIR}/venv" || python -m venv "${SCRIPT_DIR}/venv"
    fi
    "${SCRIPT_DIR}/venv/bin/python" -m pip install --upgrade pip &> /dev/null || true
    if [ -f "${SCRIPT_DIR}/requirements_linux.txt" ]; then
        "${SCRIPT_DIR}/venv/bin/python" -m pip install -r "${SCRIPT_DIR}/requirements_linux.txt"
    elif [ -f "${SCRIPT_DIR}/requirements.txt" ]; then
        "${SCRIPT_DIR}/venv/bin/python" -m pip install -r "${SCRIPT_DIR}/requirements.txt"
    else
        "${SCRIPT_DIR}/venv/bin/python" -m pip install PyQt6 numpy opencv-python Pillow requests pyinstaller
    fi
    PYINSTALLER_BIN="${SCRIPT_DIR}/venv/bin/pyinstaller"
fi

echo -e "${COLOR_YELLOW}${MSG_COMPILING}${COLOR_RESET}"
"$PYINSTALLER_BIN" --noconfirm --clean --workpath "${SCRIPT_DIR}/build_pkg" --distpath "${SCRIPT_DIR}/dist_pkg" "${SCRIPT_DIR}/PaintNotNet.spec"

# 4. Copiar la aplicación a /opt/paintnotnet
INSTALL_DIR="/opt/paintnotnet"
echo -e "${COLOR_YELLOW}${MSG_STEP2} ${INSTALL_DIR}...${COLOR_RESET}"

rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cp -r "${APP_SOURCE}"/* "$INSTALL_DIR"/

chmod +x "${INSTALL_DIR}/PaintNotNet"

# Crear enlace simbólico en /usr/local/bin y limpiar accesos antiguos en sbin
rm -f /usr/local/sbin/paintnotnet
mkdir -p /usr/local/bin
ln -sf "${INSTALL_DIR}/PaintNotNet" /usr/local/bin/paintnotnet

# 5. Integración con el escritorio (.desktop, iconos y mime)
echo -e "${COLOR_YELLOW}${MSG_STEP3}${COLOR_RESET}"

# Copiar icono a las rutas de iconos estándar del sistema freedesktop (hicolor y pixmaps)
mkdir -p /usr/share/pixmaps
cp "${SCRIPT_DIR}/gui/icono.png" /usr/share/pixmaps/paintnotnet.png

for sz in 16x16 32x32 48x48 64x64 128x128 256x256 512x512; do
    mkdir -p "/usr/share/icons/hicolor/${sz}/apps"
    cp "${SCRIPT_DIR}/gui/icono.png" "/usr/share/icons/hicolor/${sz}/apps/paintnotnet.png"
done

# Registrar MIME Type .pnn en el sistema
mkdir -p /usr/share/mime/packages
cat <<EOF > /usr/share/mime/packages/paintnotnet.xml
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="application/x-paintnotnet">
    <comment>${MSG_MIME_COMMENT}</comment>
    <glob pattern="*.pnn"/>
    <glob pattern="*.PNN"/>
    <icon name="paintnotnet"/>
  </mime-type>
</mime-info>
EOF

DESKTOP_FILE="/usr/share/applications/PaintNotNet.desktop"
cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Name=PaintNotNet
Comment=${MSG_DESKTOP_COMMENT}
Exec=/usr/local/bin/paintnotnet %F
Icon=paintnotnet
Terminal=false
Type=Application
Categories=Graphics;2DGraphics;RasterGraphics;GTK;Qt;
MimeType=image/png;image/jpeg;image/bmp;image/webp;application/x-paintnotnet;
Keywords=paint;editor;image;drawing;dibujo;capas;pnn;
EOF

chmod 644 "$DESKTOP_FILE"

# Actualizar cachés de menú, íconos y tipos MIME del sistema (KDE / GNOME / XFCE)
if command -v update-mime-database &> /dev/null; then
    update-mime-database /usr/share/mime &> /dev/null || true
fi
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications &> /dev/null || true
fi
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor &> /dev/null || true
fi
touch /usr/share/icons/hicolor &> /dev/null || true

# Actualización de la caché de servicios / menú de KDE Plasma
if command -v kbuildsycoca6 &> /dev/null; then
    kbuildsycoca6 --noincremental &> /dev/null || true
elif command -v kbuildsycoca5 &> /dev/null; then
    kbuildsycoca5 --noincremental &> /dev/null || true
fi

REAL_USER="${SUDO_USER:-$USER}"
if [ -n "$REAL_USER" ] && [ "$REAL_USER" != "root" ]; then
    su - "$REAL_USER" -c "kbuildsycoca6 --noincremental &> /dev/null || kbuildsycoca5 --noincremental &> /dev/null || true" &> /dev/null || true
fi

# Configurar PaintNotNet como la aplicación predeterminada para archivos .pnn
if command -v xdg-mime &> /dev/null; then
    xdg-mime default PaintNotNet.desktop application/x-paintnotnet &> /dev/null || true
    xdg-mime default PaintNotNet.desktop image/pnn &> /dev/null || true

    REAL_USER="${SUDO_USER:-$USER}"
    if [ -n "$REAL_USER" ] && [ "$REAL_USER" != "root" ]; then
        su - "$REAL_USER" -c "xdg-mime default PaintNotNet.desktop application/x-paintnotnet &> /dev/null || true" &> /dev/null || true
        su - "$REAL_USER" -c "xdg-mime default PaintNotNet.desktop image/pnn &> /dev/null || true" &> /dev/null || true
    fi
fi

# Configurar el idioma seleccionado en las preferencias del usuario (~/.config/PaintNotNet/PaintNotNet.conf)
REAL_USER="${SUDO_USER:-$USER}"
if [ -n "$REAL_USER" ] && [ "$REAL_USER" != "root" ]; then
    USER_HOME="$(eval echo "~$REAL_USER")"
    CONFIG_DIR="${USER_HOME}/.config/PaintNotNet"
    CONFIG_FILE="${CONFIG_DIR}/PaintNotNet.conf"

    mkdir -p "$CONFIG_DIR"

    if [ -f "$CONFIG_FILE" ]; then
        if grep -q "^language=" "$CONFIG_FILE"; then
            sed -i "s/^language=.*/language=${SELECTED_LANG}/" "$CONFIG_FILE"
        elif grep -q "^\[General\]" "$CONFIG_FILE"; then
            sed -i "/^\[General\]/a language=${SELECTED_LANG}" "$CONFIG_FILE"
        else
            echo -e "[General]\nlanguage=${SELECTED_LANG}" >> "$CONFIG_FILE"
        fi
    else
        cat <<EOF > "$CONFIG_FILE"
[General]
language=${SELECTED_LANG}
EOF
    fi
    chown -R "${REAL_USER}:${REAL_USER}" "$CONFIG_DIR"
fi

# 6. Generar desinstalador
UNINSTALL_SCRIPT="${INSTALL_DIR}/uninstall.sh"
cat <<EOF > "$UNINSTALL_SCRIPT"
#!/usr/bin/env bash
# ==============================================================================
# PaintNotNet - Desinstalador Completo para Linux / Complete Linux Uninstaller
# ==============================================================================

COLOR_BLUE='\033[0;34m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_RESET='\033[0m'

if [ "\$EUID" -ne 0 ]; then
    echo -e "\${COLOR_RED}[!] Error: Este desinstalador requiere permisos de administrador (root).\${COLOR_RESET}"
    echo -e "\${COLOR_RED}[!] Error: This uninstaller requires root privileges.\${COLOR_RESET}"
    echo -e "    Ejecuta el comando con sudo / Please run with sudo:"
    echo -e "    \${COLOR_YELLOW}sudo \$0\${COLOR_RESET}"
    exit 1
fi

echo -e "\${COLOR_BLUE}==============================================================\${COLOR_RESET}"
echo -e "\${COLOR_BLUE}      Desinstalador de PaintNotNet / PaintNotNet Uninstaller  \${COLOR_RESET}"
echo -e "\${COLOR_BLUE}==============================================================\${COLOR_RESET}"
echo ""

echo -e "\${COLOR_YELLOW}[1/3] Eliminando archivos de la aplicación y ejecutables...\${COLOR_RESET}"
rm -rf /opt/paintnotnet
rm -f /usr/local/bin/paintnotnet
rm -f /usr/local/sbin/paintnotnet

echo -e "\${COLOR_YELLOW}[2/3] Eliminando accesos directos, íconos y asociaciones MIME...\${COLOR_RESET}"
rm -f /usr/share/applications/PaintNotNet.desktop
rm -f /usr/share/pixmaps/paintnotnet.png
rm -f /usr/share/mime/packages/paintnotnet.xml

for sz in 16x16 32x32 48x48 64x64 128x128 256x256 512x512; do
    rm -f "/usr/share/icons/hicolor/\${sz}/apps/paintnotnet.png"
done

echo -e "\${COLOR_YELLOW}[3/3] Actualizando caché del sistema (MIME, escritorio e íconos)...\${COLOR_RESET}"
if command -v update-mime-database &> /dev/null; then
    update-mime-database /usr/share/mime &> /dev/null || true
fi
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications &> /dev/null || true
fi
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor &> /dev/null || true
fi
touch /usr/share/icons/hicolor &> /dev/null || true

if command -v kbuildsycoca6 &> /dev/null; then
    kbuildsycoca6 --noincremental &> /dev/null || true
elif command -v kbuildsycoca5 &> /dev/null; then
    kbuildsycoca5 --noincremental &> /dev/null || true
fi

REAL_USER="\${SUDO_USER:-\$USER}"
if [ -n "\$REAL_USER" ] && [ "\$REAL_USER" != "root" ]; then
    su - "\$REAL_USER" -c "kbuildsycoca6 --noincremental &> /dev/null || kbuildsycoca5 --noincremental &> /dev/null || true" &> /dev/null || true
fi

echo ""
echo -e "\${COLOR_GREEN}==============================================================\${COLOR_RESET}"
echo -e "\${COLOR_GREEN}  ${MSG_UNINSTALL_DONE}\${COLOR_RESET}"
echo -e "\${COLOR_GREEN}==============================================================\${COLOR_RESET}"
echo ""
EOF
chmod +x "$UNINSTALL_SCRIPT"
cp "$UNINSTALL_SCRIPT" "${SCRIPT_DIR}/uninstall.sh"

echo -e "${COLOR_YELLOW}${MSG_STEP4}${COLOR_RESET}"
echo ""
echo -e "${COLOR_GREEN}==============================================================${COLOR_RESET}"
echo -e "${COLOR_GREEN}${MSG_SUCCESS}${COLOR_RESET}"
echo -e "${COLOR_GREEN}==============================================================${COLOR_RESET}"
echo -e "${MSG_LAUNCH}"
echo -e "${MSG_LAUNCH_1}"
echo -e "${MSG_LAUNCH_2} ${COLOR_YELLOW}paintnotnet${COLOR_RESET}"
echo -e ""
echo -e "${MSG_UNINSTALL}"
echo -e "   ${COLOR_YELLOW}sudo /opt/paintnotnet/uninstall.sh${COLOR_RESET}"
echo ""
