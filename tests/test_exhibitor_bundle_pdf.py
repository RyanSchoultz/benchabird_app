import pytest

from models.exhibitor import Exhibitor
from models.results import Result
from models.show_entry import CalculatedEntry, LateEntry, ShowEntry
from services.reports.exhibitor_bundle import (
    ExhibitorBundleError,
    generate_exhibitor_bundle,
    generate_exhibitor_bundle_for_exhibitor,
    search_exhibitors_for_bundle,
)


def test_missing_exhibitor_raises_clear_error(test_db):
    with pytest.raises(ExhibitorBundleError, match="No exhibitor"):
        generate_exhibitor_bundle(99)


def test_no_entry_exhibitor_returns_valid_pdf(test_db):
    Exhibitor.create(exh_no=7, name="Alice Bird", email="alice@example.test")

    pdf = generate_exhibitor_bundle(7)

    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 1000


def test_bundle_includes_calculated_entries(test_db):
    Exhibitor.create(exh_no=7, name="Alice Bird")
    CalculatedEntry.create(auto_num=42, exh_no=7, name="Alice Bird", class_code="A1")

    pdf = generate_exhibitor_bundle(7)

    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 1500


def test_bundle_falls_back_to_raw_entries_before_calculate(test_db):
    Exhibitor.create(exh_no=7, name="Alice Bird")
    ShowEntry.create(auto_num=5, exh_no=7, class_code="A1")

    pdf = generate_exhibitor_bundle(7)

    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 1200


def test_bundle_grows_with_late_entries(test_db):
    Exhibitor.create(exh_no=7, name="Alice Bird")
    CalculatedEntry.create(auto_num=42, exh_no=7, name="Alice Bird", class_code="A1")
    LateEntry.create(auto_num=77, exh_no=7, name="Alice Bird", class_code="L1")

    without_late = generate_exhibitor_bundle(7, include_late=False)
    with_late = generate_exhibitor_bundle(7, include_late=True)

    assert len(with_late) > len(without_late)


def test_bundle_grows_with_results(test_db):
    Exhibitor.create(exh_no=7, name="Alice Bird")
    CalculatedEntry.create(auto_num=42, exh_no=7, name="Alice Bird", class_code="A1")
    Result.create(exhibit_no=42, result="1st")

    without_results = generate_exhibitor_bundle(7, include_results=False)
    with_results = generate_exhibitor_bundle(7, include_results=True)

    assert len(with_results) > len(without_results)


def test_bundle_grows_with_address_label_when_flagged(test_db):
    Exhibitor.create(
        exh_no=7,
        name="Alice Bird",
        address="1 Main Road",
        town="Cape Town",
        zip_code="8000",
        print_address=True,
    )

    without_label = generate_exhibitor_bundle(7, include_address_label=False)
    with_label = generate_exhibitor_bundle(7, include_address_label=True)

    assert len(with_label) > len(without_label)


def test_bundle_for_exhibitor_handles_missing_exhibitor_number_by_name(test_db):
    exhibitor = Exhibitor.create(name="Barnard, Andre.")
    CalculatedEntry.create(
        auto_num=42,
        exh_no=None,
        name="Barnard, Andre.",
        class_code="A1",
    )

    pdf = generate_exhibitor_bundle_for_exhibitor(exhibitor.id)

    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 1500


def test_search_bundle_exhibitors_matches_name_and_exhibit_number(test_db):
    alice = Exhibitor.create(exh_no=7, name="Alice Bird")
    barnard = Exhibitor.create(name="Barnard, Andre.")
    CalculatedEntry.create(auto_num=42, exh_no=None, name="Barnard, Andre.", class_code="A1")

    name_matches = search_exhibitors_for_bundle("barnard")
    exhibit_matches = search_exhibitors_for_bundle("42")

    assert [row.exhibitor.id for row in name_matches] == [barnard.id]
    assert [row.exhibitor.id for row in exhibit_matches] == [barnard.id]
    assert alice.id not in [row.exhibitor.id for row in exhibit_matches]


def test_exhibitor_bundle_dialog_imports():
    from views._exhibitor_bundle_dialog import ExhibitorBundleDialog

    assert ExhibitorBundleDialog.__name__ == "ExhibitorBundleDialog"


def test_reports_view_imports_with_exhibitor_bundle():
    from views.reports_view import ReportsView

    assert ReportsView.__name__ == "ReportsView"


def test_bundle_dialog_selection_text_never_shows_none(test_db):
    from views._exhibitor_bundle_dialog import format_selected_summary

    exhibitor = Exhibitor.create(name="Barnard, Andre.")
    match = search_exhibitors_for_bundle("barnard")[0]

    text = format_selected_summary(match)

    assert exhibitor.name in text
    assert "#None" not in text
    assert "not assigned" in text
