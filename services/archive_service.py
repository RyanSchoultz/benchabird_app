# services/archive_service.py
"""Save and restore named DB snapshots for show archiving."""
import shutil
from datetime import datetime
from pathlib import Path
from config import DB_PATH, DATA_DIR

ARCHIVES_DIR = DATA_DIR / "archives"


def save_snapshot(name: str) -> Path:
    """Copy current DB to archives/<name>_<timestamp>.db. Returns destination path."""
    ARCHIVES_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name).strip()
    dest = ARCHIVES_DIR / f"{safe_name}_{ts}.db"
    shutil.copy2(str(DB_PATH), str(dest))
    return dest


def list_snapshots() -> list:
    """Return list of snapshot Paths sorted newest-first."""
    if not ARCHIVES_DIR.exists():
        return []
    return sorted(ARCHIVES_DIR.glob("*.db"), key=lambda p: p.stat().st_mtime, reverse=True)


def restore_snapshot(archive_path: Path) -> None:
    """
    Replace the live DB with the given archive.
    Closes and reconnects the Peewee database so the running app picks up the new data.
    """
    from models.database import database
    from main import init_db
    database.close()
    shutil.copy2(str(archive_path), str(DB_PATH))
    init_db()


def delete_snapshot(archive_path: Path) -> None:
    archive_path.unlink(missing_ok=True)
