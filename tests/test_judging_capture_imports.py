def test_judging_capture_dialog_imports(test_db):
    from views._judging_capture_dialog import JudgingCaptureDialog

    assert JudgingCaptureDialog.__name__ == "JudgingCaptureDialog"


def test_reports_view_imports_with_judges_catalogue(test_db):
    from views.reports_view import ReportsView

    assert ReportsView.__name__ == "ReportsView"


def test_results_view_imports_with_judging_capture(test_db):
    from views.results_view import ResultsView

    assert ResultsView.__name__ == "ResultsView"


def test_judging_capture_only_saves_changed_values(test_db):
    from views._judging_capture_dialog import JudgingCaptureDialog

    selections = JudgingCaptureDialog.changed_selections(
        {10: "1st", 11: "NB", 12: "Clear", 13: ""},
        {10: "1st", 11: "", 12: "2nd", 13: ""},
    )

    assert selections == {11: "NB", 12: "Clear"}


def test_judging_capture_builds_combined_save_payload(test_db):
    from views._judging_capture_dialog import JudgingCaptureDialog

    payload = JudgingCaptureDialog.changed_payload(
        current_results={10: "1st", 11: "", 12: "NB"},
        initial_results={10: "", 11: "", 12: "NB"},
        current_classes={10: "GL01", 11: "RF01", 12: "GL01"},
        initial_classes={10: "GL01", 11: "GL01", 12: "GL01"},
    )

    assert payload == {
        10: {"result": "1st"},
        11: {"class_code": "RF01"},
    }


def test_judging_capture_detects_cross_category_moves(test_db):
    from views._judging_capture_dialog import JudgingCaptureDialog

    moves = JudgingCaptureDialog.cross_category_moves(
        payload={10: {"class_code": "RF01"}, 11: {"class_code": "GL01"}},
        active_category="Gloster",
        class_categories={"RF01": "Red Factor", "GL01": "Gloster"},
    )

    assert moves == [(10, "Red Factor")]


def test_judging_capture_empty_category_state_is_operator_friendly(test_db):
    from views._judging_capture_dialog import JudgingCaptureDialog

    state = JudgingCaptureDialog.category_combo_state([])

    assert state.labels == ["No judging categories"]
    assert state.selected == "No judging categories"
    assert state.enabled is False
    assert "Show Participants" in state.message
