@echo off
chcp 65001 > NUL
setlocal enabledelayedexpansion

echo ==============================================================
echo       Desinstalador de PaintNotNet / Uninstaller
echo ==============================================================
echo.

set "INSTALL_DIR=%LOCALAPPDATA%\PaintNotNet"

echo [i] Eliminando archivos de la aplicación en: %INSTALL_DIR%...
if exist "%INSTALL_DIR%" (
    rmdir /S /Q "%INSTALL_DIR%"
)

echo [i] Eliminando accesos directos...
del /F /Q "%USERPROFILE%\Desktop\PaintNotNet.lnk" 2>nul
del /F /Q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\PaintNotNet.lnk" 2>nul

echo [i] Refrescando caché de íconos...
ie4uinit.exe -show >nul 2>&1

echo.
echo ==============================================================
echo   ¡PaintNotNet ha sido desinstalado por completo de Windows!
echo   PaintNotNet has been completely uninstalled from Windows!
echo ==============================================================
echo.
pause
