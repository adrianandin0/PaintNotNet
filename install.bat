@echo off
chcp 65001 > NUL
setlocal enabledelayedexpansion

echo ==============================================================
echo         Instalador de PaintNotNet v1.0.6 para Windows
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

:: 2. Limpiar caché previa de PyInstaller y compilar ejecutable (.exe)
echo [i] Limpiando carpetas de compilación anteriores...
if exist "build_pkg" rmdir /s /q "build_pkg" 2>nul
if exist "dist_pkg" rmdir /s /q "dist_pkg" 2>nul

echo [i] Compilando PaintNotNet con PyInstaller...
if exist "venv\Scripts\pyinstaller.exe" (
    venv\Scripts\pyinstaller.exe --noconfirm --clean --workpath build_pkg --distpath dist_pkg PaintNotNet.spec
) else (
    pyinstaller --noconfirm --clean --workpath build_pkg --distpath dist_pkg PaintNotNet.spec
)

:: 3. Definir carpeta de instalación del usuario (%LOCALAPPDATA%\PaintNotNet)
set "INSTALL_DIR=%LOCALAPPDATA%\PaintNotNet"
echo.
echo [i] Instalando archivos en: %INSTALL_DIR%...

mkdir "%INSTALL_DIR%" 2>nul
xcopy /E /Y /I "dist_pkg\PaintNotNet\*" "%INSTALL_DIR%\"

:: Copiar expresamente el archivo de icono .ico a la raíz, gui/ y gui/iconos/
mkdir "%INSTALL_DIR%\gui" 2>nul
mkdir "%INSTALL_DIR%\gui\iconos" 2>nul
if exist "gui\paintdotnet.ico" (
    copy /Y "gui\paintdotnet.ico" "%INSTALL_DIR%\paintdotnet.ico"
    copy /Y "gui\paintdotnet.ico" "%INSTALL_DIR%\gui\paintdotnet.ico"
    copy /Y "gui\paintdotnet.ico" "%INSTALL_DIR%\gui\iconos\paintdotnet.ico"
) else if exist "%~dp0gui\paintdotnet.ico" (
    copy /Y "%~dp0gui\paintdotnet.ico" "%INSTALL_DIR%\paintdotnet.ico"
    copy /Y "%~dp0gui\paintdotnet.ico" "%INSTALL_DIR%\gui\paintdotnet.ico"
    copy /Y "%~dp0gui\paintdotnet.ico" "%INSTALL_DIR%\gui\iconos\paintdotnet.ico"
)

:: 4. Eliminar accesos directos viejos con caché congelada
del /F /Q "%USERPROFILE%\Desktop\PaintNotNet.lnk" 2>nul
del /F /Q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\PaintNotNet.lnk" 2>nul

:: 5. Crear accesos directos resolviendo rutas absolutas completas con $env:LOCALAPPDATA
powershell -NoProfile -ExecutionPolicy Bypass -Command "$appDir = \"$env:LOCALAPPDATA\PaintNotNet\"; $iconPath = \"$appDir\paintdotnet.ico,0\"; $exePath = \"$appDir\PaintNotNet.exe\"; $deskPath = [System.Environment]::GetFolderPath('Desktop') + '\PaintNotNet.lnk'; $startPath = [System.Environment]::GetFolderPath('StartMenu') + '\Programs\PaintNotNet.lnk'; $s1 = (New-Object -COM WScript.Shell).CreateShortcut($deskPath); $s1.TargetPath = $exePath; $s1.IconLocation = $iconPath; $s1.WorkingDirectory = $appDir; $s1.Save(); $s2 = (New-Object -COM WScript.Shell).CreateShortcut($startPath); $s2.TargetPath = $exePath; $s2.IconLocation = $iconPath; $s2.WorkingDirectory = $appDir; $s2.Save()"

:: 6. Pre-configurar el idioma en el archivo de preferencias de usuario
set "CONFIG_FILE=%INSTALL_DIR%\PaintNotNet.conf"
if not exist "%CONFIG_FILE%" (
    (
        echo [General]
        echo language=%SELECTED_LANG%
    ) > "%CONFIG_FILE%"
)

:: 7. Refrescar la caché de íconos de Windows Explorer
if exist "%LOCALAPPDATA%\IconCache.db" del /F /Q /A "%LOCALAPPDATA%\IconCache.db" 2>nul
ie4uinit.exe -ClearIconCache >nul 2>&1
ie4uinit.exe -show >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -Command "$code = '[DllImport(\"shell32.dll\")] public static extern void SHChangeNotify(int wEventId, int uFlags, System.IntPtr dwItem1, System.IntPtr dwItem2);'; $type = Add-Type -MemberDefinition $code -Name Win32Utils -Namespace Win32API -PassThru; $type::SHChangeNotify(0x08000000, 0, [System.IntPtr]::Zero, [System.IntPtr]::Zero)" 2>nul

echo.
echo ==============================================================
echo      ¡PaintNotNet se ha instalado exitosamente en Windows!
echo ==============================================================
echo Puedes iniciar la aplicación desde:
echo   1. El acceso directo creado en tu Escritorio
echo   2. El menú Inicio de Windows
echo.
pause
