import uuid
from pathlib import Path

import pandas as pd

from models.exhibitor import Exhibitor
from services.exhibitor_import_service import import_exhibitors_from_spreadsheet


def _path(suffix: str) -> Path:
    scratch = Path("tmp")
    scratch.mkdir(exist_ok=True)
    return scratch / f"exhibitors-{uuid.uuid4().hex}{suffix}"


def _cleanup(path: Path) -> None:
    if path.exists():
        try:
            path.unlink()
        except PermissionError:
            pass


def test_csv_import_creates_exhibitors(test_db):
    path = _path(".csv")
    try:
        pd.DataFrame([
            {"ExhNo": 10, "Name": "Alice Smith", "Town": "Cape Town"},
            {"ExhNo": 11, "Name": "Bob Jones", "Town": "Durban"},
        ]).to_csv(path, index=False)

        summary = import_exhibitors_from_spreadsheet(path)

        assert summary.created == 2
        assert summary.updated == 0
        assert summary.skipped == 0
        assert Exhibitor.select().count() == 2
        assert Exhibitor.get(Exhibitor.exh_no == 10).town == "Cape Town"
    finally:
        _cleanup(path)


def test_xlsx_import_creates_exhibitors(test_db):
    path = _path(".xlsx")
    try:
        pd.DataFrame([
            {"Exhibitor #": 20, "Full Name": "Carol Green", "Email": "carol@example.com"},
        ]).to_excel(path, index=False)

        summary = import_exhibitors_from_spreadsheet(path)

        assert summary.created == 1
        assert Exhibitor.get(Exhibitor.exh_no == 20).email == "carol@example.com"
    finally:
        _cleanup(path)


def test_aliases_and_boolean_fields_are_normalized(test_db):
    path = _path(".csv")
    try:
        pd.DataFrame([
            {
                "Exhibitor #": "30",
                "Full Name": "Dana Blue",
                "Cell": "0820000000",
                "E-mail": "dana@example.com",
                "Print Address": "yes",
                "Zip": "1234",
            },
        ]).to_csv(path, index=False)

        summary = import_exhibitors_from_spreadsheet(path)

        exhibitor = Exhibitor.get(Exhibitor.exh_no == 30)
        assert summary.created == 1
        assert exhibitor.name == "Dana Blue"
        assert exhibitor.cell_no == "0820000000"
        assert exhibitor.email == "dana@example.com"
        assert exhibitor.zip_code == "1234"
        assert exhibitor.print_address is True
    finally:
        _cleanup(path)


def test_reimport_updates_existing_exhibitor_without_duplicate(test_db):
    path = _path(".csv")
    try:
        Exhibitor.create(exh_no=40, name="Evan Old", town="Old Town")
        pd.DataFrame([
            {"ExhNo": 40, "Name": "Evan New", "Town": "New Town"},
        ]).to_csv(path, index=False)

        summary = import_exhibitors_from_spreadsheet(path)

        assert summary.created == 0
        assert summary.updated == 1
        assert Exhibitor.select().count() == 1
        exhibitor = Exhibitor.get(Exhibitor.exh_no == 40)
        assert exhibitor.name == "Evan New"
        assert exhibitor.town == "New Town"
    finally:
        _cleanup(path)


def test_bad_rows_are_reported_without_crashing(test_db):
    path = _path(".csv")
    try:
        pd.DataFrame([
            {"ExhNo": "bad", "Name": "Frank Number"},
            {"ExhNo": 51, "Name": ""},
        ]).to_csv(path, index=False)

        summary = import_exhibitors_from_spreadsheet(path)

        assert summary.created == 1
        assert summary.skipped == 1
        assert len(summary.errors) == 2
        assert Exhibitor.get(Exhibitor.name == "Frank Number").exh_no is None
    finally:
        _cleanup(path)
