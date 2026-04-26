@echo off
cd /d "C:\Users\emanu\OneDrive\Desktop\fefi-app"

start "Servidor Web" cmd /k py -m http.server 8000
start "Servidor Guardado" cmd /k py server.py
timeout /t 2 >nul
start "" "http://localhost:8000/admin.html"
