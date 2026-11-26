APEX DELIVERY CHALLAN - COMPLETE WINDOWS APPLICATION

This package includes the complete Django application, based on the year-wise
bulk-delete and multi-challan Word-import build, plus the Returnable/Non
Returnable colour theme and Apex red wordmark.

Included:
- Create, edit, view, print and delete delivery challans
- Returnable (green) and Non Returnable (red) form/print themes
- Apex wordmark remains red
- Word import, including multiple challans per DOCX where supported by importer
- Duplicate detection by DC Number + calendar year
- Year-wise bulk delete (staff users only)
- SQLite database support, backup/restore and Windows batch setup scripts
- Animated login page

IMPORTANT - BULK DELETE ACCESS:
The "Bulk delete by year" panel is intentionally restricted to staff users.
If it is not visible after login, the logged-in Django user is not marked as
staff. Sign in with a staff/superuser account, or run:

    python manage.py createsuperuser

For an existing account, use Django admin at /admin/, open Users, select the
account and enable "Staff status". Save and sign in again.

WINDOWS UPDATE / INSTALL:
1. Stop the running Django server.
2. Make a backup copy of the entire current project folder, especially db.sqlite3.
3. Extract this ZIP. The project folder inside is dc_app.
4. Copy the extracted dc_app contents into your existing project folder.
   Do NOT overwrite or delete your existing db.sqlite3, secret.key, or media/
   data if present.
5. Open Command Prompt in the project folder.
6. Activate the existing virtual environment:
       venv\Scripts\activate
7. Install dependencies:
       python -m pip install -r requirements.txt
8. Apply migrations:
       python manage.py migrate
9. Collect static files:
       python manage.py collectstatic --noinput
10. Start the application:
       run_server.bat
   or:
       python manage.py runserver

Open http://127.0.0.1:8000/ and press Ctrl+F5.

DATABASE SAFETY:
The ZIP does not include your live db.sqlite3. Keep your existing database file
to preserve existing challans and user accounts. Back it up before replacing
application files.

NOTE:
This is a source-code package. Verify Word import results using Preview only
before importing a large historical DOCX file. Review any challan type warnings
before relying on imported Returnable/Non Returnable classifications.
