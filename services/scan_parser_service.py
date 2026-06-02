"""Parse QR/barcode scanner input into result exhibit numbers."""
from __future__ import annotations

import re

from models.show_entry import CalculatedEntry


class ScanParseError(ValueError):
    pass


def _pairs(text: str) -> dict[str, str]:
    pairs = {}
    for key, value in re.findall(r"([A-Za-z]+)\s*:\s*([^\s]+)", text):
        pairs[key.strip().lower()] = value.strip()
    return pairs


def _int_or_error(value: str, label: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ScanParseError(f"Invalid {label}: {value!r}.")


def _resolve_legacy(exh_no: int, class_code: str) -> int:
    rows = list(
        CalculatedEntry.select()
        .where(
            (CalculatedEntry.exh_no == exh_no)
            & (CalculatedEntry.class_code == class_code)
        )
        .order_by(CalculatedEntry.auto_num)
    )
    if not rows:
        raise ScanParseError(
            f"No calculated entry found for exhibitor {exh_no}, class {class_code}."
        )
    if len(rows) > 1:
        raise ScanParseError(
            f"Legacy scan matched multiple entries for exhibitor {exh_no}, class {class_code}."
        )
    return rows[0].auto_num


def parse_scan_to_auto_num(text: str) -> int:
    raw = (text or "").strip()
    if not raw:
        raise ScanParseError("Scan is empty.")
    if raw.isdigit():
        return int(raw)

    pairs = _pairs(raw)
    auto_num = pairs.get("autonum") or pairs.get("auto")
    if auto_num:
        return _int_or_error(auto_num, "AutoNum")

    exh_no = pairs.get("exhno") or pairs.get("exh")
    class_code = pairs.get("class") or pairs.get("classcode")
    if exh_no and class_code:
        return _resolve_legacy(_int_or_error(exh_no, "ExhNo"), class_code)

    raise ScanParseError("Scan did not include AutoNum, or legacy ExhNo/Class data.")
