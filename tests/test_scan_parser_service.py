import pytest

from models.show_entry import CalculatedEntry
from services.scan_parser_service import ScanParseError, parse_scan_to_auto_num


def test_parse_new_qr_payload_uses_auto_num(test_db):
    assert parse_scan_to_auto_num("AutoNum:42 ExhNo:5 Class:SC01") == 42


def test_parse_plain_numeric_input(test_db):
    assert parse_scan_to_auto_num(" 42 ") == 42


def test_parse_legacy_qr_payload_resolves_calculated_entry(test_db):
    CalculatedEntry.create(auto_num=77, exh_no=5, name="Alice", class_code="SC01")
    assert parse_scan_to_auto_num("ExhNo:5 Class:SC01") == 77


def test_parse_legacy_qr_payload_missing_match_raises(test_db):
    with pytest.raises(ScanParseError, match="No calculated entry"):
        parse_scan_to_auto_num("ExhNo:5 Class:SC01")


def test_parse_legacy_qr_payload_ambiguous_match_raises(test_db):
    CalculatedEntry.create(auto_num=77, exh_no=5, name="Alice", class_code="SC01")
    CalculatedEntry.create(auto_num=78, exh_no=5, name="Alice", class_code="SC01")
    with pytest.raises(ScanParseError, match="multiple"):
        parse_scan_to_auto_num("ExhNo:5 Class:SC01")
