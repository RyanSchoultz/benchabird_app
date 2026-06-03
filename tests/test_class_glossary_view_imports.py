def test_class_glossary_view_imports(test_db):
    from views.notes_view import NotesView

    assert NotesView.__name__ == "NotesView"


def test_sidebar_uses_class_glossary_label(test_db):
    from views.main_window import NAV

    assert ("Class Glossary", "notes") in NAV
    assert ("Notes", "notes") not in NAV
