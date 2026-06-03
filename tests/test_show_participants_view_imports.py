def test_show_participants_view_imports(test_db):
    from views.show_participants_view import ShowParticipantsView
    assert ShowParticipantsView.__name__ == "ShowParticipantsView"
