def test_show_participants_view_imports(test_db):
    from views.show_participants_view import ShowParticipantsView
    assert ShowParticipantsView.__name__ == "ShowParticipantsView"


def test_enrol_dialog_imports(test_db):
    from views._enrol_dialog import EnrolDialog
    assert EnrolDialog.__name__ == "EnrolDialog"
