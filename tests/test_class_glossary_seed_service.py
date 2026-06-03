from models.class_def import ClassDef, Species


def seed_reference_rows():
    Species.create(seq=2, bird_type="Red Factor", type2="CANARY SECTION", type3="Red Factor", tcode="RF")
    Species.create(seq=1, bird_type="Gloster", type2="CANARY SECTION", type3="Gloster", tcode="G")
    ClassDef.create(
        class_code="RF02",
        bird_type="Red Factor",
        main_class="Champion",
        colour="Red cock",
        afrbesk="Open Cock",
        type_b="Red Factor Type",
        class_seq=2,
    )
    ClassDef.create(
        class_code="GL01",
        bird_type="Gloster",
        main_class="Novice",
        colour="Corona hen",
        afrbesk="Open Hen",
        type_b="Gloster Type",
        class_seq=1,
    )
    ClassDef.create(
        class_code="RF01",
        bird_type="Red Factor",
        main_class="Champion",
        colour="Red hen",
        afrbesk=None,
        type_b=None,
        class_seq=1,
    )


def test_seed_class_glossary_creates_denormalized_rows(test_db):
    from models.class_glossary import ClassGlossary
    from services.class_glossary_service import seed_class_glossary

    seed_reference_rows()

    assert seed_class_glossary() == 3

    first = ClassGlossary.get(ClassGlossary.class_code == "GL01")
    assert first.species_seq == 1
    assert first.species_heading == "CANARY SECTION"
    assert first.species_subheading == "Gloster"
    assert first.description == "Corona hen Open Hen"
    assert "gloster type" in first.search_text


def test_list_class_glossary_reads_seeded_table_in_species_order(test_db):
    from services.class_glossary_service import list_class_glossary, seed_class_glossary

    seed_reference_rows()
    seed_class_glossary()

    rows = list_class_glossary()

    assert [row.class_code for row in rows] == ["GL01", "RF01", "RF02"]
    assert rows[0].species_heading == "CANARY SECTION"


def test_class_glossary_filters_by_species_and_search_text(test_db):
    from services.class_glossary_service import list_class_glossary, list_species_filters, seed_class_glossary

    seed_reference_rows()
    seed_class_glossary()

    assert list_species_filters() == ["CANARY SECTION"]
    assert [row.class_code for row in list_class_glossary(species_heading="CANARY SECTION")] == [
        "GL01",
        "RF01",
        "RF02",
    ]
    assert [row.class_code for row in list_class_glossary(query="open cock")] == ["RF02"]
    assert [row.class_code for row in list_class_glossary(query="red factor type")] == ["RF02"]
