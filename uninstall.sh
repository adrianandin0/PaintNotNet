#!/usr/bin/env bash
if [ "$EUID" -ne 0 ]; then
    echo "Ejecuta con sudo: sudo $0 / Please run with sudo: sudo $0"
    exit 1
fi
rm -rf /opt/paintnotnet
rm -f /usr/local/bin/paintnotnet
rm -f /usr/local/sbin/paintnotnet
rm -f /usr/share/applications/PaintNotNet.desktop
rm -f /usr/share/pixmaps/paintnotnet.png
rm -f /usr/share/icons/hicolor/128x128/apps/paintnotnet.png
rm -f /usr/share/mime/packages/paintnotnet.xml
if command -v update-mime-database &> /dev/null; then
    update-mime-database /usr/share/mime &> /dev/null || true
fi
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications &> /dev/null || true
fi
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor &> /dev/null || true
fi
echo "PaintNotNet ha sido desinstalado por completo del sistema."
