"""Database backup and restore (NFR 16).

Uses SQLite's online backup API so a copy is consistent even while the
site is running.
"""
import os
import sqlite3
import tempfile

REQUIRED_TABLES = {
    "admins", "health_categories", "health_articles", "service_categories",
    "facilities", "facility_services", "emergency_contacts", "audit_log",
}
SQLITE_HEADER = b"SQLite format 3\x00"


class BackupError(Exception):
    """Raised when a backup file cannot be used."""


def write_backup(db_path, destination):
    src = sqlite3.connect(db_path)
    dst = sqlite3.connect(destination)
    try:
        with dst:
            src.backup(dst)
    finally:
        src.close()
        dst.close()


def backup_to_bytes(db_path):
    fd, tmp = tempfile.mkstemp(suffix=".sqlite3")
    os.close(fd)
    try:
        write_backup(db_path, tmp)
        with open(tmp, "rb") as f:
            return f.read()
    finally:
        os.remove(tmp)


def validate_backup(path):
    """Check the file is a SQLite database with every Konektya table."""
    try:
        with open(path, "rb") as f:
            header = f.read(len(SQLITE_HEADER))
    except OSError:
        raise BackupError("The backup file could not be read.")
    if header != SQLITE_HEADER:
        raise BackupError("The file is not a valid Konektya database backup.")
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise BackupError("The backup file is corrupted.")
            names = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'")}
            missing = REQUIRED_TABLES - names
            if missing:
                raise BackupError("The backup is missing required tables: "
                                  + ", ".join(sorted(missing)) + ".")
            if conn.execute("SELECT COUNT(*) FROM admins").fetchone()[0] == 0:
                raise BackupError("The backup has no administrator accounts, "
                                  "so restoring it would lock everyone out.")
        finally:
            conn.close()
    except sqlite3.DatabaseError:
        raise BackupError("The file is not a valid Konektya database backup.")


def restore_backup(source, db_path):
    validate_backup(source)
    src = sqlite3.connect(source)
    dst = sqlite3.connect(db_path)
    try:
        with dst:
            src.backup(dst)
    finally:
        src.close()
        dst.close()


def restore_from_upload(file_storage, db_path):
    fd, tmp = tempfile.mkstemp(suffix=".sqlite3")
    os.close(fd)
    try:
        file_storage.save(tmp)
        restore_backup(tmp, db_path)
    finally:
        os.remove(tmp)
