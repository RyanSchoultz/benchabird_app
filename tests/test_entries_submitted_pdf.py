from models.class_def import ClassDef
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry


def test_entries_submitted_generates_pdf_with_no_data(test_db):
    from services.reports.entries_submitted import generate_entries_submitted

    pdf = generate_entries_submitted()

    assert isinstance(pdf, bytes)
    assert len(pdf) > 0
    assert pdf[:4] == b"%PDF"


def test_entries_submitted_generates_pdf_with_data(test_db):
    from services.reports.entries_submitted import generate_entries_submitted

    Exhibitor.create(exh_no=1, name="Adams, A.", club="KVK")
    ClassDef.create(
        class_code="N1",
        bird_type="NORWICH CANARY",
        main_class="OPEN COCKS",
        colour="Yellow Clear",
        class_seq=1,
    )
    ShowEntry.create(auto_num=1, exh_no=1, class_code="N1")

    pdf = generate_entries_submitted()

    assert isinstance(pdf, bytes)
    assert len(pdf) > 1000
    assert pdf[:4] == b"%PDF"
