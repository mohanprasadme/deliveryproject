"""SQLite backup / restore helpers (safe to run while the site is in use)."""
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.db import connections


def db_path():
    return Path(settings.DATABASES["default"]["NAME"])


def backup_dir():
    d = Path(settings.BACKUP_DIR)
    d.mkdir(parents=True, exist_ok=True)
    return d


def make_backup(prefix="dc_backup"):
    target = backup_dir() / f"{prefix}_{datetime.now():%Y%m%d_%H%M%S}.sqlite3"
    with closing(sqlite3.connect(str(db_path()))) as src, \
            closing(sqlite3.connect(str(target))) as dst:
        src.backup(dst)
    return target


def list_backups():
    files = sorted(backup_dir().glob("*.sqlite3"), key=lambda p: p.stat().st_mtime,
                   reverse=True)
    return [{
        "name": f.name,
        "size_kb": round(f.stat().st_size / 1024, 1),
        "modified": datetime.fromtimestamp(f.stat().st_mtime),
    } for f in files]


def prune_backups(keep=30):
    files = sorted(backup_dir().glob("dc_backup_*.sqlite3"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    for old in files[keep:]:
        old.unlink()


def validate_backup(path):
    """Return (ok, message). Checks that the file is a real DC database."""
    try:
        with closing(sqlite3.connect(str(path))) as con:
            if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                return False, "The file is damaged (integrity check failed)."
            tables = {r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
    except sqlite3.DatabaseError:
        return False, "This is not a valid database backup file."
    needed = {"challan_deliverychallan", "challan_dcitem", "auth_user"}
    if not needed <= tables:
        return False, "This file is not a Delivery Challan backup."
    return True, "ok"


def restore_backup(path):
    ok, msg = validate_backup(path)
    if not ok:
        raise ValueError(msg)
    make_backup("pre_restore")          # safety copy of the current data
    connections.close_all()
    with closing(sqlite3.connect(str(path))) as src, \
            closing(sqlite3.connect(str(db_path()))) as dst:
        src.backup(dst)
