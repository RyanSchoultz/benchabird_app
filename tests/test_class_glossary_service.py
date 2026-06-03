from models.class_def import ClassDef


def seed_classes():
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


def test_class_description_combines_colour_and_afrbesk(test_db):
    from services.class_glossary_service import class_description

    assert class_description("Red cock", "Open Cock") == "Red cock Open Cock"
    assert class_description("Red hen", None) == "Red hen"
    assert class_description(None, "Open Hen") == "Open Hen"
    assert class_description(None, None) == ""


def test_list_class_glossary_orders_by_type_main_sequence_and_code(test_db):
    from services.class_glossary_service import list_class_glossary

    seed_classes()

    rows = list_class_glossary()

    assert [row.class_code for row in rows] == ["GL01", "RF01", "RF02"]
    assert rows[0].description == "Corona hen Open Hen"
    assert rows[0].extra == "Gloster Type"


def test_list_class_glossary_filters_across_class_fields(test_db):
    from services.class_glossary_service import list_class_glossary

    seed_classes()

    assert [row.class_code for row in list_class_glossary("GL01")] == ["GL01"]
    assert [row.class_code for row in list_class_glossary("gloster")] == ["GL01"]
    assert [row.class_code for row in list_class_glossary("champion")] == ["RF01", "RF02"]
    assert [row.class_code for row in list_class_glossary("open cock")] == ["RF02"]
    assert [row.class_code for row in list_class_glossary("red factor type")] == ["RF02"]
    assert list_class_glossary("missing") == []
