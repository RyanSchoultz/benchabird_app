from models.class_def import ClassDef
from models.results import NotBenched, Result
from models.show_entry import CalculatedEntry
from models.special import SpecialList, SpecialWinner


def test_generate_special_lists_empty_returns_pdf(test_db):
    from services.reports.special_lists import generate_special_lists

    pdf = generate_special_lists()

    assert pdf[:4] == b"%PDF"


def test_generate_special_lists_with_data_returns_pdf(test_db):
    from services.reports.special_lists import generate_special_lists

    SpecialList.create(
        special_nr="S001",
        bird_type="CANARY SECTION",
        description="Best Canary",
        prize1="Trophy",
        cash=100,
        kind="Open",
        kind_sequence="1",
    )

    pdf = generate_special_lists()

    assert pdf[:4] == b"%PDF"
    assert b"Special Lists" in pdf
    assert len(pdf) > 1500


def test_generate_marked_catalogue_empty_returns_pdf(test_db):
    from services.reports.marked_catalogue import generate_marked_catalogue

    pdf = generate_marked_catalogue()

    assert pdf[:4] == b"%PDF"


def test_generate_marked_catalogue_with_results_nb_and_specials_returns_pdf(test_db):
    from services.reports.marked_catalogue import generate_marked_catalogue

    ClassDef.create(class_code="SC01", bird_type="Canary", class_seq=1)
    CalculatedEntry.create(auto_num=1, exh_no=10, name="Alice", class_code="SC01")
    CalculatedEntry.create(auto_num=2, exh_no=11, name="Bob", class_code="SC01")
    Result.create(exhibit_no=1, result="1")
    NotBenched.create(exhibit_no=2, not_benched="Not Benched", nb="NB")
    SpecialList.create(special_nr="S001", description="Best Canary")
    SpecialWinner.create(special_nr="S001", exhibit_no=1, result="Winner")

    pdf = generate_marked_catalogue()

    assert pdf[:4] == b"%PDF"
    assert b"Marked Catalogue" in pdf
    assert len(pdf) > 1500
