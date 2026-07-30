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

:: 2. Compilar ejecutable ejecutable (.exe) usando PaintNotNet.spec
echo [i] Compilando PaintNotNet con PyInstaller...
if exist "venv\Scripts\pyinstaller.exe" (
    venv\Scripts\pyinstaller.exe --noconfirm --workpath build_pkg --distpath dist_pkg PaintNotNet.spec
) else (
    pyinstaller --noconfirm --workpath build_pkg --distpath dist_pkg PaintNotNet.spec
)

:: 3. Definir carpeta de instalación del usuario (%LOCALAPPDATA%\PaintNotNet)
set "INSTALL_DIR=%LOCALAPPDATA%\PaintNotNet"
echo.
echo [i] Instalando archivos en: %INSTALL_DIR%...

mkdir "%INSTALL_DIR%" 2>nul
xcopy /E /Y /I "dist_pkg\PaintNotNet\*" "%INSTALL_DIR%\" >nul

:: Copiar expresamente el archivo de icono .ico a la raíz de instalación
copy /Y "%~dp0gui\paintdotnet.ico" "%INSTALL_DIR%\paintdotnet.ico" >nul

:: 4. Eliminar accesos directos viejos para forzar a Windows Explorer a refrescar la caché
del /F /Q "%USERPROFILE%\Desktop\PaintNotNet.lnk" 2>nul
del /F /Q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\PaintNotNet.lnk" 2>nul

:: 5. Crear accesos directos con asignación limpia de IconLocation
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut([System.Environment]::GetFolderPath('Desktop') + '\PaintNotNet.lnk'); $s.TargetPath='%INSTALL_DIR%\PaintNotNet.exe'; $s.IconLocation='%INSTALL_DIR%\paintdotnet.ico'; $s.WorkingDirectory='%INSTALL_DIR%'; $s.Save()"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut([System.Environment]::GetFolderPath('StartMenu') + '\Programs\PaintNotNet.lnk'); $s.TargetPath='%INSTALL_DIR%\PaintNotNet.exe'; $s.IconLocation='%INSTALL_DIR%\paintdotnet.ico'; $s.WorkingDirectory='%INSTALL_DIR%'; $s.Save()"

:: 6. Pre-configurar el idioma en el archivo de preferencias de usuario
set "CONFIG_FILE=%INSTALL_DIR%\PaintNotNet.conf"
if not exist "%CONFIG_FILE%" (
    (
        echo [General]
        echo language=%SELECTED_LANG%
    ) > "%CONFIG_FILE%"
)

:: 7. Forzar actualización de la caché de íconos del sistema
ie4uinit.exe -show >nul 2>&1

echo.
echo ==============================================================
echo      ¡PaintNotNet se ha instalado exitosamente en Windows!
echo ==============================================================
echo Puedes iniciar la aplicación desde:
echo   1. El acceso directo creado en tu Escritorio
echo   2. El menú Inicio de Windows
echo.
pause
