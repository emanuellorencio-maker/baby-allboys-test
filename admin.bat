@echo off
cd /d "C:\Users\emanu\OneDrive\Desktop\fefi-app"
start "" "http://localhost:8000/admin.html"
py -m http.server 8000
pause