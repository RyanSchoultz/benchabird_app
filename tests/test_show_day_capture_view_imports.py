def test_show_day_capture_view_imports(test_db):
    from views.show_day_capture_view import ShowDayCaptureView

    assert ShowDayCaptureView.__name__ == "ShowDayCaptureView"


def test_show_day_capture_publish_reports_are_declared(test_db):
    from views.show_day_capture_view import PUBLISH_REPORTS

    labels = [row[0] for row in PUBLISH_REPORTS]

    assert labels == [
        "Marked Catalogue",
        "Results Sheet",
        "Special Winners",
        "Prize Money",
        "Results by Exhibitor",
        "4.4 Marked Catalogue",
    ]


def test_main_window_nav_exposes_show_day_capture_without_removing_fallbacks(test_db):
    from views.main_window import NAV

    labels = [label for label, _ in NAV]
    keys = [key for _, key in NAV]

    assert "Show Day Capture" in labels
    assert "Results" in labels
    assert "Special Winners" in labels
    assert keys.index("capture") < keys.index("results")


def test_judging_stage_empty_state_message_points_to_benching(test_db):
    from views.show_day_capture_view import judging_stage_empty_state

    state = judging_stage_empty_state([])

    assert state.has_categories is False
    assert "Show Participants" in state.message
    assert state.primary_action == "Go to Show Participants"
