@echo off
echo.
echo ================================
echo Installing Cloudflare cloudflared
echo ================================
echo.

:: Check if winget exists
where winget >nul 2>&1
if errorlevel 1 (
    echo Error: winget is not installed.
    echo Please install App Installer from Microsoft Store.
    pause
    exit /b 1
)

:: Install cloudflared
winget install --id Cloudflare.cloudflared --accept-source-agreements --accept-package-agreements

echo.
echo ================================
echo Installing Python requirements
echo ================================
echo.

:: Check if Python is installed
where python >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH.
    pause
    exit /b 1
)

:: Check if requirements.txt exists
if not exist requirements.txt (
    echo Error: requirements.txt not found in current directory.
    pause
    exit /b 1
)

:: Install pip packages
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo ================================
echo All installations completed.
echo ================================
pause
