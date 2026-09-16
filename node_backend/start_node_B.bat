@echo off
:: ============================================================
::  IIA Node Backend Starter — Laptop B
::  Owns: insurance.db + registration.db
::  Port: 8001
:: ============================================================

title IIA Node B — Insurance + Registration (port 8001)
color 0A

echo.
echo  ==========================================
echo   IIA Node Backend — LAPTOP B
echo   Databases: insurance + registration
echo   Port:      8001
echo  ==========================================
echo.

:: Set environment variables for this node
set NODE_DATABASES=insurance,registration
set NODE_PORT=8001
set NODE_HOST=0.0.0.0
set DEBUG=true

:: Install dependencies if not already installed
echo [1/2] Checking dependencies...
pip install -q -r requirements.txt

echo [2/2] Starting node server...
echo.
echo  Open browser: http://localhost:8001/docs
echo  Master laptop connects to: http://THIS_IP:8001
echo  (Replace THIS_IP with the IP shown below)
echo.
ipconfig | findstr "IPv4"
echo.

python main.py

pause
