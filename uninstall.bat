@echo off
chcp 65001 > NUL
setlocal enabledelayedexpansion

echo ==============================================================
echo       Desinstalador de PaintNotNet / PaintNotNet Uninstaller
echo ==============================================================
echo.

set "INSTALL_DIR=%LOCALAPPDATA%\PaintNotNet"

echo [1/4] Eliminando archivos de la aplicación en: %INSTALL_DIR%...
if exist "%INSTALL_DIR%" (
    rmdir /S /Q "%INSTALL_DIR%"
)

echo [2/4] Eliminando accesos directos de Escritorio y Menú Inicio...
del /F /Q "%USERPROFILE%\Desktop\PaintNotNet.lnk" 2>nul
del /F /Q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\PaintNotNet.lnk" 2>nul
if exist "%PUBLIC%\Desktop\PaintNotNet.lnk" del /F /Q "%PUBLIC%\Desktop\PaintNotNet.lnk" 2>nul
if exist "%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs\PaintNotNet.lnk" del /F /Q "%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs\PaintNotNet.lnk" 2>nul

echo [3/4] Eliminando asociaciones de archivos del Registro...
reg delete "HKCU\Software\Classes\.pnn" /f 2>nul
reg delete "HKCU\Software\Classes\PaintNotNet.Project" /f 2>nul

echo [4/4] Refrescando la caché de íconos de Windows Explorer...
if exist "%LOCALAPPDATA%\IconCache.db" del /F /Q /A "%LOCALAPPDATA%\IconCache.db" 2>nul
ie4uinit.exe -ClearIconCache >nul 2>&1
ie4uinit.exe -show >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -Command "$code = '[DllImport(\"shell32.dll\")] public static extern void SHChangeNotify(int wEventId, int uFlags, System.IntPtr dwItem1, System.IntPtr dwItem2);'; $type = Add-Type -MemberDefinition $code -Name Win32Utils -Namespace Win32API -PassThru; $type::SHChangeNotify(0x08000000, 0, [System.IntPtr]::Zero, [System.IntPtr]::Zero)" 2>nul

echo.
echo ==============================================================
echo   ¡PaintNotNet ha sido desinstalado por completo de Windows!
echo   PaintNotNet has been completely uninstalled from Windows!
echo ==============================================================
echo.
pause
