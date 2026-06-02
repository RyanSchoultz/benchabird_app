import sqlite3
import uuid
from pathlib import Path

from peewee import SqliteDatabase

from models import ALL_MODELS
from models.class_def import ClassDef, MainClass, Species
from models.exhibitor import Exhibitor
from models.reference import HallOfFame, ShowDetails, TicketNumber
from models.results import NotBenched, Result
from models.show_entry import CalculatedEntry, LateEntry, ShowEntry
from models.special import SpecialList, SpecialWinner
from scripts.create_starter_db import DEMO_EXHIBITORS, create_starter_db


def _paths():
    scratch = Path("tmp")
    scratch.mkdir(exist_ok=True)
    token = uuid.uuid4().hex
    return scratch / f"source-{token}.db", scratch / f"starter-{token}.db"


def _cleanup(*paths):
    for path in paths:
        for suffix in ("", "-wal", "-shm"):
            target = Path(str(path) + suffix)
            if target.exists():
                try:
                    target.unlink()
                except PermissionError:
                    pass


def _create_source_db(path):
    db = SqliteDatabase(str(path))
    with db.bind_ctx(ALL_MODELS):
        db.create_tables(ALL_MODELS)
        ClassDef.create(class_code="SC01", main_class="Canary", colour="Yellow")
        Species.create(seq=1, bird_type="Canary", main_tcode="CAN", cat="Type")
        MainClass.create(main_class="Canary", mc_seq=1)
        ShowDetails.create(show_eng="Legacy Show", club_eng_full="Legacy Club")
        Exhibitor.create(exh_no=99, name="Real Person", town="Pretoria")
        ShowEntry.create(auto_num=1, exh_no=99, class_code="SC01")
        CalculatedEntry.create(auto_num=1, exh_no=99, name="Real Person", class_code="SC01")
        LateEntry.create(auto_num=2, exh_no=99, name="Real Person", class_code="SC01")
        Result.create(exhibit_no=1, result="1st")
        NotBenched.create(exhibit_no=2)
        SpecialList.create(special_nr="SP01", description="Legacy Prize", cash=100)
        SpecialWinner.create(special_nr="SP01", exhibit_no=1, result="Winner")
        HallOfFame.create(type_abbr="CAN", year="2023", name="Historical Winner")
        TicketNumber.create(ticket_number=123)
        db.close()


def _count(path, table):
    with sqlite3.connect(path) as conn:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def _names(path, table):
    with sqlite3.connect(path) as conn:
        return [row[0] for row in conn.execute(f"SELECT name FROM {table} ORDER BY name")]


def test_create_starter_db_copies_reference_data_and_demo_exhibitors():
    source, dest = _paths()
    try:
        _create_source_db(source)

        result = create_starter_db(source, dest)

        assert result == dest.resolve()
        assert dest.exists()
        assert _count(dest, "class_def") == 1
        assert _count(dest, "species") == 1
        assert _count(dest, "main_class") == 1
        assert _count(dest, "show_details") == 1
        assert _count(dest, "exhibitor") == len(DEMO_EXHIBITORS)
        assert all(name.endswith("_Demo") for name in _names(dest, "exhibitor"))
    finally:
        _cleanup(source, dest)


def test_create_starter_db_excludes_historical_and_show_data():
    source, dest = _paths()
    try:
        _create_source_db(source)

        create_starter_db(source, dest)

        assert _count(dest, "show_entry") == 0
        assert _count(dest, "calculated_entry") == 0
        assert _count(dest, "late_entry") == 0
        assert _count(dest, "result") == 0
        assert _count(dest, "not_benched") == 0
        assert _count(dest, "special_list") == 0
        assert _count(dest, "special_winner") == 0
        assert _count(dest, "hall_of_fame") == 0
        assert _count(dest, "ticket_number") == 0
        assert "Real Person" not in _names(dest, "exhibitor")
    finally:
        _cleanup(source, dest)


def test_create_starter_db_does_not_mutate_source_db():
    source, dest = _paths()
    try:
        _create_source_db(source)
        before = source.read_bytes()

        create_starter_db(source, dest)

        assert source.read_bytes() == before
        assert _count(source, "exhibitor") == 1
        assert _names(source, "exhibitor") == ["Real Person"]
    finally:
        _cleanup(source, dest)
