from services.class_glossary_service import ClassGlossaryRow


def make_row(index: int) -> ClassGlossaryRow:
    return ClassGlossaryRow(
        class_code=f"C{index:04d}",
        bird_type="Type",
        species_heading="Section",
        species_subheading="Subsection",
        main_class="Main",
        description="Description",
        extra="Extra",
        class_seq=index,
    )


def test_glossary_view_limits_rows_rendered_at_once(test_db):
    from views.notes_view import MAX_GLOSSARY_RENDER_ROWS, visible_glossary_rows

    rows = [make_row(index) for index in range(MAX_GLOSSARY_RENDER_ROWS + 50)]

    visible = visible_glossary_rows(rows)

    assert len(visible) == MAX_GLOSSARY_RENDER_ROWS
    assert visible == rows[:MAX_GLOSSARY_RENDER_ROWS]
