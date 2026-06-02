import pytest

from models.exhibitor import Exhibitor
from models.results import Result
from models.show_entry import CalculatedEntry, LateEntry, ShowEntry
from services.reports.exhibitor_bundle import (
    ExhibitorBundleError,
    generate_exhibitor_bundle,
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
