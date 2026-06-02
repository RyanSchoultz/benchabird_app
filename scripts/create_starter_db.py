"""Create the clean release starter database."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peewee import SqliteDatabase

from models import ALL_MODELS
from models.exhibitor import Exhibitor
from models.reference import ShowDetails

DEFAULT_SOURCE = ROOT / "benchabird.db"
DEFAULT_DEST = ROOT / "release" / "benchabird.db"

REFERENCE_TABLES = ("class_def", "species", "main_class")
EMPTY_TABLES = (
    "show_entry",
    "calculated_entry",
    "late_entry",
    "result",
    "not_benched",
    "special_winner",
    "special_list",
    "hall_of_fame",
    "ticket_number",
    "brochure_sequence",
    "notes_brochure",
    "number_seq",
)
DEMO_EXHIBITORS = (
    {"exh_no": 1, "name": "Alpha_Demo", "town": "Demo Town", "club": "Demo Club"},
    {"exh_no": 2, "name": "Beta_Demo", "town": "Demo Town", "club": "Demo Club"},
    {"exh_no": 3, "name": "Gamma_Demo", "town": "Demo Town", "club": "Demo Club"},
)


def _connect_readonly(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def _copy_table(source: sqlite3.Connection, dest: sqlite3.Connection, table: str) -> int:
    if not _table_exists(source, table):
        return 0

    columns = [row[1] for row in source.execute(f"PRAGMA table_info({table})")]
    if not columns:
        return 0

    quoted_columns = ", ".join(f'"{col}"' for col in columns)
    placeholders = ", ".join("?" for _ in columns)
    rows = source.execute(f"SELECT {quoted_columns} FROM {table}").fetchall()
    if rows:
        dest.executemany(
            f"INSERT INTO {table} ({quoted_columns}) VALUES ({placeholders})",
            rows,
        )
    return len(rows)


def _create_schema(dest: Path) -> None:
    db = SqliteDatabase(str(dest))
    with db.bind_ctx(ALL_MODELS):
        db.connect()
        db.create_tables(ALL_MODELS)
        ShowDetails.create(
            show_eng="Benchabird Demo Show",
            show_afr="Benchabird Demo Show",
            club_eng="Demo Club",
            club_eng_full="Demo Club",
            club_afr="Demo Club",
            club_afr_full="Demo Club",
            association="Demo Association",
        )
        for exhibitor in DEMO_EXHIBITORS:
            Exhibitor.create(**exhibitor)
        db.close()


def _validate(dest: Path) -> None:
    with sqlite3.connect(dest) as conn:
        names = [row[0] for row in conn.execute("SELECT name FROM exhibitor")]
        if not names:
            raise RuntimeError("Starter DB must contain synthetic demo exhibitors.")
        bad_names = [name for name in names if not name.endswith("_Demo")]
        if bad_names:
            raise RuntimeError(f"Starter DB contains non-demo exhibitors: {bad_names}")

        for table in EMPTY_TABLES:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            if count:
                raise RuntimeError(f"Starter DB table {table} must be empty; found {count}.")


def create_starter_db(source: Path | str = DEFAULT_SOURCE, dest: Path | str = DEFAULT_DEST) -> Path:
    source = Path(source).resolve()
    dest = Path(dest).resolve()

    if not source.exists():
        raise FileNotFoundError(f"Source database not found: {source}")
    if source == dest:
        raise ValueError("Starter destination must not be the source development database.")

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()

    _create_schema(dest)

    with _connect_readonly(source) as src, sqlite3.connect(dest) as dst:
        for table in REFERENCE_TABLES:
            _copy_table(src, dst, table)
        dst.commit()

    _validate(dest)
    return dest


def main() -> int:
    dest = create_starter_db()
    with sqlite3.connect(dest) as conn:
        demo_count = conn.execute("SELECT COUNT(*) FROM exhibitor").fetchone()[0]
        class_count = conn.execute("SELECT COUNT(*) FROM class_def").fetchone()[0]
        species_count = conn.execute("SELECT COUNT(*) FROM species").fetchone()[0]
        main_class_count = conn.execute("SELECT COUNT(*) FROM main_class").fetchone()[0]

    print(f"Created starter DB: {dest}")
    print(f"Demo exhibitors: {demo_count}")
    print(f"Class definitions: {class_count}")
    print(f"Species rows: {species_count}")
    print(f"Main class rows: {main_class_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
