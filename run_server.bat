@echo off
rem ===== Starts the Delivery Challan app on port 8000 =====
cd /d %~dp0
call venv\Scripts\activate
echo Delivery Challan is running. Open http://localhost:8000 in the browser.
echo Other PCs: http://THIS-PC-IP:8000   (keep this window open)
waitress-serve --listen=0.0.0.0:8000 --threads=8 dcproject.wsgi:application
pause
