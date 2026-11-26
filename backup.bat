@echo off
rem ===== Creates a database backup in the "backups" folder =====
cd /d %~dp0
call venv\Scripts\activate
python manage.py backup_db --keep 60
