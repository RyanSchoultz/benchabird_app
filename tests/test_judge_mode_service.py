import pytest

from models.results import Result
from models.show_entry import CalculatedEntry
from services.judge_mode_service import (
    JudgeModeError,
    resolve_judge_entry,
    save_judge_result,
    toggle_judge_not_benched,
)


def test_resolve_judge_entry_returns_context(test_db):
    CalculatedEntry.create(auto_num=42, exh_no=7, name="Alice Bird", class_code="A1")

    ctx = resolve_judge_entry("AutoNum:42 ExhNo:7 Class:A1")

    assert ctx.auto_num == 42
    assert ctx.exh_no == 7
    assert ctx.name == "Alice Bird"
    assert ctx.class_code == "A1"
    assert ctx.result is None
    assert ctx.not_benched is False


def test_resolve_judge_entry_includes_existing_result_and_nb(test_db):
    CalculatedEntry.create(auto_num=42, exh_no=7, name="Alice Bird", class_code="A1")
    save_judge_result(42, "1st")
    toggle_judge_not_benched(42)

    ctx = resolve_judge_entry("42")

    assert ctx.result == "1st"
    assert ctx.not_benched is True


def test_resolve_judge_entry_rejects_unknown_calculated_entry(test_db):
    with pytest.raises(JudgeModeError, match="No calculated entry"):
        resolve_judge_entry("42")


def test_resolve_judge_entry_blocks_class_filter_mismatch(test_db):
    CalculatedEntry.create(auto_num=42, exh_no=7, name="Alice Bird", class_code="A1")

    with pytest.raises(JudgeModeError, match="outside selected class"):
        resolve_judge_entry("42", class_filter="B2")


def test_save_judge_result_records_and_clears_not_benched(test_db):
    CalculatedEntry.create(auto_num=42, exh_no=7, name="Alice Bird", class_code="A1")
    toggle_judge_not_benched(42)

    ctx = save_judge_result(42, "BOB")

    assert Result.get(Result.exhibit_no == 42).result == "BOB"
    assert ctx.result == "BOB"
    assert ctx.not_benched is False


def test_toggle_judge_not_benched_marks_then_unmarks(test_db):
    CalculatedEntry.create(auto_num=42, exh_no=7, name="Alice Bird", class_code="A1")

    marked = toggle_judge_not_benched(42)
    unmarked = toggle_judge_not_benched(42)

    assert marked.not_benched is True
    assert unmarked.not_benched is False


def test_judge_mode_dialog_imports():
    from views._judge_mode_dialog import JudgeModeDialog

    assert JudgeModeDialog.__name__ == "JudgeModeDialog"
