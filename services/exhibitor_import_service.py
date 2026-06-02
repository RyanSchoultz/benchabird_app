"""Import exhibitors from CSV or Excel spreadsheets."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from models.exhibitor import Exhibitor


@dataclass
class ImportSummary:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)


_ALIASES = {
    "exh_no": {
        "exhno",
        "exh no",
        "exhibitor #",
        "exhibitor no",
        "exhibitor number",
        "number",
    },
    "name": {"name", "full name", "exhibitor", "exhibitor name"},
    "address": {"address", "addr"},
    "suburb": {"suburb"},
    "town": {"town", "city"},
    "zip_code": {"zipcode", "zip code", "zip", "postal code", "postcode"},
    "tel_home": {"telhome", "tel home", "telh", "home phone", "phone", "telephone"},
    "tel_work": {"telwork", "tel work", "telw", "work phone"},
    "cell_no": {"cell", "cellno", "cell no", "mobile", "mobile phone"},
    "fax_no": {"fax", "faxno", "fax no"},
    "email": {"email", "e-mail", "mail"},
    "club": {"club", "club code"},
    "club1": {"club1", "club name"},
    "print_address": {"printaddress", "print address", "labels", "print labels"},
}


def _clean_header(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().replace("_", " ").split())


def _column_map(columns) -> dict[str, str]:
    mapped = {}
    for column in columns:
        cleaned = _clean_header(column)
        compact = cleaned.replace(" ", "")
        for field_name, aliases in _ALIASES.items():
            if cleaned in aliases or compact in aliases:
                mapped[str(column)] = field_name
                break
    return mapped


def _is_blank(value: Any) -> bool:
    return value is None or pd.isna(value) or str(value).strip() == ""


def _as_text(value: Any) -> str | None:
    if _is_blank(value):
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _as_int(value: Any) -> int | None:
    if _is_blank(value):
        return None
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


def _as_bool(value: Any) -> bool:
    if _is_blank(value):
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "x"}


def _read(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path, dtype=object)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path, dtype=object)
    raise ValueError("Unsupported file type. Choose a .csv, .xlsx, or .xls file.")


def _row_data(row, mapping: dict[str, str], row_num: int, summary: ImportSummary) -> dict:
    data = {}
    for column, field_name in mapping.items():
        value = row[column]
        if field_name == "exh_no":
            parsed = _as_int(value)
            if parsed is None and not _is_blank(value):
                summary.errors.append(f"Row {row_num}: invalid exhibitor number '{value}'.")
            data[field_name] = parsed
        elif field_name == "print_address":
            data[field_name] = _as_bool(value)
        else:
            data[field_name] = _as_text(value)
    return data


def _find_existing(data: dict):
    exh_no = data.get("exh_no")
    if exh_no is not None:
        existing = Exhibitor.get_or_none(Exhibitor.exh_no == exh_no)
        if existing:
            return existing

    name = data.get("name")
    if name:
        return Exhibitor.get_or_none(Exhibitor.name == name)
    return None


def import_exhibitors_from_spreadsheet(path: str | Path) -> ImportSummary:
    path = Path(path)
    df = _read(path)
    mapping = _column_map(df.columns)
    if "name" not in mapping.values():
        raise ValueError("Spreadsheet must include a Name or Full Name column.")

    summary = ImportSummary()

    with Exhibitor._meta.database.atomic():
        for index, row in df.iterrows():
            row_num = int(index) + 2
            data = _row_data(row, mapping, row_num, summary)
            if not data.get("name"):
                summary.skipped += 1
                summary.errors.append(f"Row {row_num}: missing exhibitor name.")
                continue

            existing = _find_existing(data)
            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
                existing.save()
                summary.updated += 1
            else:
                Exhibitor.create(**data)
                summary.created += 1

    return summary
