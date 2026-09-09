#!/usr/bin/env bash
# ==============================================================================
# PaintNotNet - Desinstalador Completo para Linux / Complete Linux Uninstaller
# ==============================================================================

COLOR_BLUE='\033[0;34m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_RESET='\033[0m'

if [ "$EUID" -ne 0 ]; then
    echo -e "${COLOR_RED}[!] Error: Este desinstalador requiere permisos de administrador (root).${COLOR_RESET}"
    echo -e "${COLOR_RED}[!] Error: This uninstaller requires root privileges.${COLOR_RESET}"
    echo -e "    Ejecuta el comando con sudo / Please run with sudo:"
    echo -e "    ${COLOR_YELLOW}sudo $0${COLOR_RESET}"
    exit 1
fi

echo -e "${COLOR_BLUE}==============================================================${COLOR_RESET}"
echo -e "${COLOR_BLUE}      Desinstalador de PaintNotNet / PaintNotNet Uninstaller  ${COLOR_RESET}"
echo -e "${COLOR_BLUE}==============================================================${COLOR_RESET}"
echo ""

echo -e "${COLOR_YELLOW}[1/3] Eliminando archivos de la aplicación y ejecutables...${COLOR_RESET}"
rm -rf /opt/paintnotnet
rm -f /usr/local/bin/paintnotnet
rm -f /usr/local/sbin/paintnotnet

echo -e "${COLOR_YELLOW}[2/3] Eliminando accesos directos, íconos y asociaciones MIME...${COLOR_RESET}"
rm -f /usr/share/applications/PaintNotNet.desktop
rm -f /usr/share/pixmaps/paintnotnet.png
rm -f /usr/share/mime/packages/paintnotnet.xml

for sz in 16x16 32x32 48x48 64x64 128x128 256x256 512x512; do
    rm -f "/usr/share/icons/hicolor/${sz}/apps/paintnotnet.png"
done

echo -e "${COLOR_YELLOW}[3/3] Actualizando caché del sistema (MIME, escritorio e íconos)...${COLOR_RESET}"
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

REAL_USER="${SUDO_USER:-$USER}"
if [ -n "$REAL_USER" ] && [ "$REAL_USER" != "root" ]; then
    su - "$REAL_USER" -c "kbuildsycoca6 --noincremental &> /dev/null || kbuildsycoca5 --noincremental &> /dev/null || true" &> /dev/null || true
fi

echo ""
echo -e "${COLOR_GREEN}==============================================================${COLOR_RESET}"
echo -e "${COLOR_GREEN}  ¡PaintNotNet ha sido desinstalado por completo del sistema! ${COLOR_RESET}"
echo -e "${COLOR_GREEN}  PaintNotNet has been completely uninstalled from the system!${COLOR_RESET}"
echo -e "${COLOR_GREEN}==============================================================${COLOR_RESET}"
echo ""
