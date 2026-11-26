@echo off
rem ===== One-time setup for the Delivery Challan app =====
cd /d %~dp0
echo [1/5] Creating virtual environment...
python -m venv venv || goto :error
call venv\Scripts\activate
echo [2/5] Installing packages...
python -m pip install --upgrade pip
pip install -r requirements.txt || goto :error
echo [3/5] Creating database...
python manage.py migrate || goto :error
echo [4/5] Collecting static files...
python manage.py collectstatic --noinput || goto :error
echo [5/5] Create the ADMIN login (type a username and password when asked)
python manage.py createsuperuser
echo.
echo Setup finished. Start the app with run_server.bat
pause
exit /b 0
:error
echo.
echo Setup failed - read the message above.
pause
exit /b 1
