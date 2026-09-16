@echo off
:: ============================================================
::  IIA Node Backend Starter — Laptop C
::  Owns: theft.db + ministry.db
::  Port: 8002
:: ============================================================

title IIA Node C — Theft + Ministry (port 8002)
color 0B

echo.
echo  ==========================================
echo   IIA Node Backend — LAPTOP C
echo   Databases: theft + ministry
echo   Port:      8002
echo  ==========================================
echo.

:: Set environment variables for this node
set NODE_DATABASES=theft,ministry
set NODE_PORT=8002
set NODE_HOST=0.0.0.0
set DEBUG=true

:: Install dependencies if not already installed
echo [1/2] Checking dependencies...
pip install -q -r requirements.txt

echo [2/2] Starting node server...
echo.
echo  Open browser: http://localhost:8002/docs
echo  Master laptop connects to: http://THIS_IP:8002
echo  (Replace THIS_IP with the IP shown below)
echo.
ipconfig | findstr "IPv4"
echo.

python main.py

pause
