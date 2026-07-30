@echo off
chcp 65001 > NUL
setlocal enabledelayedexpansion

echo ==============================================================
echo         Instalador de PaintNotNet para Windows
echo ==============================================================
echo.

:: 1. Selección de Idioma / Language Selection
echo Language / Idioma:
echo   01 - Español
echo   02 - English
echo.
set /p LANG_CHOICE="Elija una opción / Choose an option [01]: "

if "%LANG_CHOICE%"=="2" set SELECTED_LANG=English
if "%LANG_CHOICE%"=="02" set SELECTED_LANG=English
if "%LANG_CHOICE%"=="en" set SELECTED_LANG=English
if "%LANG_CHOICE%"=="EN" set SELECTED_LANG=English
if not defined SELECTED_LANG set SELECTED_LANG=Español

echo.
echo [i] Idioma seleccionado: %SELECTED_LANG%
echo.

:: 2. Compilar ejecutable ejecutable (.exe) usando gui/paintdotnet.ico
echo [i] Compilando PaintNotNet con PyInstaller...
pyinstaller --noconfirm --name PaintNotNet --windowed --icon=gui/paintdotnet.ico --add-data "gui/iconos;gui/iconos" --add-data "gui/icono.png;gui" --add-data "locales;locales" main.py

:: 3. Definir carpeta de instalación del usuario (%LOCALAPPDATA%\PaintNotNet)
set "INSTALL_DIR=%LOCALAPPDATA%\PaintNotNet"
echo.
echo [i] Instalando archivos en: %INSTALL_DIR%...

mkdir "%INSTALL_DIR%" 2>nul
xcopy /E /Y /I "dist\PaintNotNet\*" "%INSTALL_DIR%\"

:: 4. Crear Accesos Directos con el icono .ico (Escritorio y Menú Inicio)
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\PaintNotNet.lnk'); $s.TargetPath='%INSTALL_DIR%\PaintNotNet.exe'; $s.IconLocation='%INSTALL_DIR%\gui\paintdotnet.ico'; $s.Save()"
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\PaintNotNet.lnk'); $s.TargetPath='%INSTALL_DIR%\PaintNotNet.exe'; $s.IconLocation='%INSTALL_DIR%\gui\paintdotnet.ico'; $s.Save()"

:: 5. Pre-configurar el idioma en el archivo de preferencias de usuario
set "CONFIG_FILE=%INSTALL_DIR%\PaintNotNet.conf"
if not exist "%CONFIG_FILE%" (
    (
        echo [General]
        echo language=%SELECTED_LANG%
    ) > "%CONFIG_FILE%"
)

echo.
echo ==============================================================
echo      ¡PaintNotNet se ha instalado exitosamente en Windows!
echo ==============================================================
echo Puedes iniciar la aplicación desde:
echo   1. El acceso directo creado en tu Escritorio
echo   2. El menú Inicio de Windows
echo.
pause
