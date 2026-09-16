@echo off
:: ============================================================
::  Laptop B — Node Backend + ngrok Tunnel
::  Owns: insurance.db + registration.db
::  Works across ANY network (different WiFi, SIM data, etc.)
:: ============================================================

title IIA Node B — Insurance + Registration (ngrok tunnel)
color 0A

echo.
echo  ==========================================
echo   IIA Node Backend — LAPTOP B
echo   Databases: insurance + registration
echo   Mode:      CROSS-NETWORK (ngrok tunnel)
echo  ==========================================
echo.

:: Set environment variables
set NODE_DATABASES=insurance,registration
set NODE_PORT=8001
set NODE_HOST=0.0.0.0
set DEBUG=true

:: ── Step 1: Install Python dependencies ─────────────────────
echo [1/4] Installing Python dependencies...
pip install -q fastapi uvicorn requests
echo     Done.
echo.

:: ── Step 2: Check ngrok ──────────────────────────────────────
echo [2/4] Checking ngrok...
where ngrok >nul 2>&1
if errorlevel 1 (
    echo.
    echo  *** ngrok not found! ***
    echo.
    echo  Install ngrok using ONE of these methods:
    echo.
    echo  Option A - winget (Windows 10/11):
    echo    winget install ngrok.ngrok
    echo.
    echo  Option B - Manual:
    echo    1. Go to https://ngrok.com/download
    echo    2. Download ngrok for Windows
    echo    3. Extract ngrok.exe to C:\Windows\System32\
    echo.
    echo  After installing, run:
    echo    ngrok config add-authtoken YOUR_TOKEN
    echo  (Get your token free from https://dashboard.ngrok.com)
    echo.
    pause
    exit /b 1
)
echo     ngrok found!
echo.

:: ── Step 3: Start the node server in background ──────────────
echo [3/4] Starting node server on port 8001...
start "Node B - Server" cmd /k "set NODE_DATABASES=insurance,registration && set NODE_PORT=8001 && cd /d "%~dp0" && python main.py"
timeout /t 3 /nobreak >nul
echo     Server started.
echo.

:: ── Step 4: Start ngrok tunnel ───────────────────────────────
echo [4/4] Starting ngrok tunnel for port 8001...
echo.
echo  =====================================================
echo   IMPORTANT — READ THIS CAREFULLY!
echo.
echo   ngrok will show a URL like:
echo     Forwarding: https://xxxx-xx-xx.ngrok-free.app -> localhost:8001
echo.
echo   COPY that https://xxxx... URL and send it to the
echo   MASTER LAPTOP operator. They need it to connect.
echo  =====================================================
echo.
echo  Starting ngrok now...
echo.

ngrok http 8001 --log=stdout

pause
