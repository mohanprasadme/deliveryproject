@echo off
rem ===== Run after copying new project files over the old ones =====
cd /d %~dp0
call venv\Scripts\activate
call backup.bat
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
echo Update finished. Restart the server / service.
pause
