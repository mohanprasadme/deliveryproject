# Delivery Challan – Windows Deployment Guide

Apex Laboratories · Django + SQLite · runs on Windows 10 / 11 / Server 2016+

The app runs on one Windows PC (the "server PC"). Other computers on the office
network open it in a browser, e.g. `http://192.168.1.50:8000`.

---------------------------------------------------------------------------

## 1. What you get

| Feature | Where |
|---|---|
| Login / logout / change password | `/login/` |
| **Delivery Challan** form (From, To, DC No, date, items) | top menu → *Delivery Challan* |
| Save, Save & Print, Print, Delete | buttons on the form |
| **DC Records** – search, filter by year, open, print, delete individual challans, or bulk-delete a selected year (staff only) | top menu → *DC Records* |
| Import old Word challans (admin only) | top menu → *Import from Word* |
| Backup & Restore (admin only) | top menu → *Backup & Restore* |
| Create / disable users (admin only) | top menu → *Users* |

All challans are stored in one local file: `db.sqlite3` (inside the project folder).

---------------------------------------------------------------------------

## 2. Install Python (once)

1. Download **Python 3.12 (64-bit)** from https://www.python.org/downloads/windows/
2. Run the installer. **Tick “Add python.exe to PATH”** (bottom of the first screen),
   then click *Install Now*.
3. Open **Command Prompt** and check:
   ```
   python --version
   ```
   It must show `Python 3.10` or higher (3.12 recommended).

## 3. Copy the project

1. Unzip `dc_app.zip`.
2. Copy the folder to a permanent place, e.g. **`C:\DCApp`**
   (avoid Desktop/Downloads and avoid folders with spaces).

## 4. One-time setup (easy way)

Double-click **`C:\DCApp\setup.bat`**. It will:

1. create a virtual environment (`venv`),
2. install Django, Waitress and WhiteNoise,
3. create the database,
4. collect static files (CSS/JS),
5. ask you to create the **admin username and password** – type them in
   (the password is hidden while typing; press Enter, repeat it).

### Same steps done manually (if you prefer)

Open Command Prompt:
```
cd C:\DCApp
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

## 5. Start the app

Double-click **`run_server.bat`** and keep the black window open.

Open a browser on the same PC: **http://localhost:8000** and log in with the admin
account you created.

*(For quick testing only you can instead run `python manage.py runserver`, but
use `run_server.bat` – Waitress – for daily use.)*

## 6. Let other PCs use it

1. Find the server PC's IP address: Command Prompt → `ipconfig` → **IPv4 Address**
   (example `192.168.1.50`). Ask IT to give this PC a **fixed IP** so it never changes.
2. Allow port 8000 through Windows Firewall (Command Prompt **as Administrator**):
   ```
   netsh advfirewall firewall add rule name="DeliveryChallan" dir=in action=allow protocol=TCP localport=8000
   ```
3. On any other PC in the office open `http://192.168.1.50:8000`
   (use your real IP). Tip: save it as a browser bookmark.

## 7. Make it start automatically when Windows starts

Pick **one** option.

### Option A – Windows Service with NSSM (recommended)
1. Download NSSM from https://nssm.cc/download and copy `win64\nssm.exe` to `C:\DCApp`.
2. Command Prompt **as Administrator**:
   ```
   cd C:\DCApp
   nssm install DeliveryChallan
   ```
   In the window that opens:
   * **Path:** `C:\DCApp\venv\Scripts\waitress-serve.exe`
   * **Startup directory:** `C:\DCApp`
   * **Arguments:** `--listen=0.0.0.0:8000 --threads=8 dcproject.wsgi:application`
3. Click *Install service*, then:
   ```
   nssm start DeliveryChallan
   ```
   Manage later with `nssm stop|restart|remove DeliveryChallan` or `services.msc`.

### Option B – Task Scheduler (no extra download)
1. Start menu → **Task Scheduler** → *Create Task*.
2. *General*: name `DeliveryChallan`, tick **Run whether user is logged on or not**
   and **Run with highest privileges**.
3. *Triggers* → New → **At startup**.
4. *Actions* → New → Start a program → `C:\DCApp\run_server.bat`, Start in: `C:\DCApp`.
5. OK, enter the Windows password when asked, then right-click the task → *Run*.

## 8. Daily use

1. Log in.
2. Click **Delivery Challan**. DC No is filled automatically (001, 002 …) and can be edited.
   Fill *To* details, add items with **+ Add item** (remove with ×).
3. **Save** stores it in the database. **Save & Print** saves and opens the print page,
   which pops up the Windows print dialog (choose your printer, or *Microsoft Print to PDF*).
   In the print dialog turn **Headers and footers OFF** for a clean page.
4. **DC Records** lists every saved challan. Use the search box / date filter, then
   **Open** (edit), **Print** or **Delete**.
5. Returnable / Non-returnable is chosen with the two radio buttons at the top of the form;
   the printout shows the chosen one in bold.

## 9. Users

Log in as admin → top menu **Users** → *Add user*.
* Normal staff: leave *Staff status* **unticked** → can create/print/delete challans only.
* Another administrator: tick *Staff status* (and *Superuser status* if they should manage users).
* To stop someone logging in: untick **Active** (do not delete the user).

## 10. Backup

The database is the single file `C:\DCApp\db.sqlite3`.

### From the app
Admin → **Backup & Restore**
* **Download backup to this PC** – saves a `.sqlite3` file to your Downloads folder.
  Copy it to a USB drive / network share / cloud drive regularly.
* **Save a backup on the server** – stores a copy in `C:\DCApp\backups`.

### Automatic daily backup (recommended)
1. Task Scheduler → *Create Basic Task* → name `DC Backup` → **Daily** at e.g. 7:00 PM.
2. Action: Start a program → `C:\DCApp\backup.bat`, Start in: `C:\DCApp`.
3. The newest 60 backups are kept; older ones are removed automatically.
4. Also copy the `backups` folder to another drive/PC (the server PC's disk can fail).

## 11. Restore

### From the app
Admin → **Backup & Restore**
* choose a file in *Backups stored on the server* → **Restore**, or
* upload a `.sqlite3` file under **Restore** → tick the confirmation → **Restore from file**.

A safety copy of the current data is saved automatically as `pre_restore_….sqlite3`.
After restoring you are logged out – log in again (users come from the backup too).

### Manual restore (if the app cannot start)
1. Stop the service / close `run_server.bat`.
2. Copy the backup file over `C:\DCApp\db.sqlite3` (rename it to `db.sqlite3`).
3. Start the app again.

## 12. Moving to a new PC
1. Install Python and copy the project (steps 2–4) – at the question for the admin user
   you can press Ctrl+C to skip.
2. Copy your latest backup file over `db.sqlite3` in the new folder.
3. Start the app. All challans and users are back.

## 12A. Import your old Word challans

Your old challans in Word can be loaded into the database. A Word file may contain one challan or multiple challans. The importer splits a multi-challan document whenever it finds the next top-level `DC No` header, then reads that section’s own DC No, DC Date, From/To details and goods table. For example, the supplied `DC_2025.docx` contains 98 individual challans and is imported as 98 separate SQLite records.
The importer reads: DC No, DC Date, Returnable/Non-Returnable (the **bold** one, or the one
that is not struck-through), the From and To blocks, and every row of the items table.

**Step 1 - make sure the files are `.docx`.**
Old `.doc` files must be converted. Either open each in Word → *Save As → Word Document (.docx)*, or
for many files run in PowerShell (Word must be installed):
```
cd C:\DCApp
powershell -ExecutionPolicy Bypass -File convert_doc_to_docx.ps1 -Folder "C:\OldDC"
```

**Step 2 - install the new package** (only once, if you installed the app before):
```
cd C:\DCApp
venv\Scripts\activate
pip install -r requirements.txt
```

**Step 3a - few files: use the web page.**
Admin → **Import from Word** → select `DC_2025.docx` (or other `.docx` files) → tick
*Preview only* → **Import**. Confirm that the preview lists DC 001 through DC 098 and
review any warnings. Then select the same file again, leave *Preview only* unticked, and
click **Import** to save each challan as a separate record.

**Step 3b - many files: use the folder command.**
```
cd C:\DCApp
venv\Scripts\activate
python manage.py import_word_dc "C:\OldDC" --dry-run
python manage.py import_word_dc "C:\OldDC"
```
`--dry-run` only checks. The command prints one line per challan section: PREVIEW, IMPORTED, SKIPPED or FAILED. A single multi-challan DOCX therefore produces multiple result lines.

**Good to know**
* A file whose DC No already exists is **skipped** (never overwritten), so re-running is safe.
  DC No is unique in the database: if your old numbering restarts every year (001 again in a new year),
  tell your developer - the numbers must be made unique first (for example 001/2026).
* FAILED sections show the reason (items table not found, DC No missing, ...). Fix the Word file and import again.
* Read the "Details" column: a warning means the importer guessed (for example the Returnable type) - open that challan in *DC Records* and correct it.
* Take a backup (section 10) before a large import.

## 13. Updating the application later
Copy the new project files over `C:\DCApp` (do **not** overwrite `db.sqlite3`,
`secret.key` or the `backups` folder), then run **`update.bat`** and restart the service.

## 14. Offline / no-internet server PC
On a PC **with** internet:
```
cd C:\DCApp
pip download -r requirements.txt -d wheels
```
Copy the `wheels` folder to the server PC's `C:\DCApp`, and in `setup.bat` replace
`pip install -r requirements.txt` with
`pip install --no-index --find-links=wheels -r requirements.txt`.
(Use the same Python version on both PCs.)

## 15. Customising
* **Default “From” address** – `challan/models.py` (`from_dept`, `from_company`, `from_address`).
  After changing, run `venv\Scripts\python manage.py makemigrations` then `migrate`.
  (Old challans keep their saved values.)
* **Print layout** – `challan/templates/challan/dc_print.html`.
* **Logo** – the “apex” text logo is plain text in the templates; replace the
  `<div class="logo">apex</div>` lines with an `<img>` if you have a logo file
  (put it in `challan/static/img/`, then run `collectstatic` again).
* **Port** – change `8000` in `run_server.bat` / the service arguments (and the firewall rule).

## 16. Troubleshooting

| Problem | Fix |
|---|---|
| `python` is not recognized | Re-install Python and tick *Add to PATH*, then open a **new** Command Prompt |
| Page has no styling | Run `venv\Scripts\python manage.py collectstatic --noinput`, restart |
| Other PCs cannot open the site | Check the firewall rule (step 6), same network, correct IP, server window/service running |
| “CSRF verification failed” | Open the site using the IP/host name, not a stale bookmark; refresh the page and retry |
| Forgot admin password | `cd C:\DCApp` → `venv\Scripts\activate` → `python manage.py changepassword USERNAME` |
| “Port already in use” | Another copy is running – close it or change the port |
| Print dialog does not appear | Allow pop-ups for the site, or click **Print** on the print page |
| Restore says “not a Delivery Challan backup” | Use a `.sqlite3` file created by this app's Backup page |

## 17. Security notes
* Use strong passwords; change the first one via *Change password*.
* The app is meant for the **internal network** – do not expose port 8000 to the internet.
* `secret.key` (created automatically) must be kept private and is not part of the database.
* The database file contains the (hashed) user passwords – protect backup copies.


UPDATE: YEAR-WISE RECORD MANAGEMENT
- DC numbers are unique within a calendar year, not across all years. For example, DC 001 dated in 2025 and DC 001 dated in 2026 are both allowed.
- During Word import, duplicate detection checks the combination of DC No + year. The same DC number in a different year will be imported as a separate record.
- DC Records includes a year filter. Staff users can use Bulk delete by year to permanently delete all challans and their related item rows for a selected year. Take a database backup before bulk deletion.
- When updating an existing installation, keep your db.sqlite3 and secret.key. Run update.bat (or activate venv and run `python manage.py migrate`) to apply the database migration.


## 12. Year-wise records and bulk deletion

- DC No is unique within a calendar year. A DC No such as `001` can exist once in 2025 and once in 2026.
- Word import skips a challan only when the same DC No already exists for the same year. The same DC No in another year is imported as a new record.
- On **DC Records**, use the Year filter to view one year.
- Staff/admin users can select a year in **Bulk delete by year** and choose **Delete Entire Year**. This permanently removes all challans dated in that year and their associated goods rows. Take a backup first.

### Updating an existing installation

1. Stop the running Delivery Challan server/service.
2. Take a backup using the app or copy `db.sqlite3` to a safe location.
3. Extract this updated ZIP to a temporary folder. Copy the updated project files over the existing `C:\DCApp` folder. Do not overwrite your existing `db.sqlite3`, `secret.key`, `backups` folder, or `venv` folder.
4. Run `update.bat` from `C:\DCApp`. This creates a backup, installs requirements, applies the new database migration, and collects static files.
5. Restart the Delivery Challan server/service and verify records.
