from models.class_def import ClassDef, MainClass, Species
from models.show_entry import CalculatedEntry


def test_generate_judges_catalogue_empty_returns_pdf(test_db):
    from services.reports.judges_catalogue import generate_judges_catalogue

    pdf = generate_judges_catalogue()

    assert pdf[:4] == b"%PDF"
    assert b"Judges Catalogue" in pdf
    assert b"Show Participants" in pdf


def test_generate_judges_catalogue_with_entries_returns_pdf(test_db):
    from services.reports.judges_catalogue import generate_judges_catalogue

    Species.create(seq=1, bird_type="Gloster", type2="Gloster", type3="Gloster")
    MainClass.create(main_class="Novice", mc_seq=1)
    ClassDef.create(
        class_code="GL01",
        bird_type="Gloster",
        type_b="Gloster Type",
        main_class="Novice",
        colour="Corona hen",
        class_seq=5,
    )
    CalculatedEntry.create(auto_num=10, exh_no=1, name="A", class_code="GL01")

    pdf = generate_judges_catalogue()

    assert pdf[:4] == b"%PDF"
    assert b"Judges Catalogue" in pdf
    assert b"GL01" in pdf
    assert b"BOB" in pdf
    assert b"NB" in pdf
