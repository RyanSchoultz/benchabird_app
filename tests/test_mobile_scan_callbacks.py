from types import SimpleNamespace


class DummyLabel:
    def __init__(self):
        self.kwargs = {}

    def configure(self, **kwargs):
        self.kwargs.update(kwargs)


class DummyEntry:
    def __init__(self, value=""):
        self.value = value
        self.deleted = False
        self.inserted = None
        self.focused = False

    def get(self):
        return self.value

    def delete(self, *_args):
        self.deleted = True
        self.value = ""

    def insert(self, _index, value):
        self.inserted = value
        self.value = value

    def focus(self):
        self.focused = True


def test_results_mobile_saved_event_refreshes_without_focusing_desktop():
    from views.results_view import ResultsView

    view = object.__new__(ResultsView)
    view._msg = DummyLabel()
    view._reload_count = 0
    view._result_combo = SimpleNamespace(focused=False, focus=lambda: setattr(view._result_combo, "focused", True))
    view._exh_entry = DummyEntry()
    view._reload_table = lambda: setattr(view, "_reload_count", view._reload_count + 1)
    view._resolve_scan_text = lambda payload: 42

    accepted = ResultsView._accept_mobile_payload(view, "AutoNum:42", "1st")

    assert accepted is True
    assert view._reload_count == 1
    assert view._msg.kwargs["text"] == "Mobile saved: #42 as 1st"
    assert view._exh_entry.deleted is False
    assert view._result_combo.focused is False


def test_judge_mode_mobile_saved_event_updates_recent_without_scan_entry_focus(monkeypatch):
    import views._judge_mode_dialog as dialog_module
    from views._judge_mode_dialog import JudgeModeDialog

    ctx = SimpleNamespace(auto_num=42, class_code="SC01")
    monkeypatch.setattr(dialog_module, "resolve_judge_entry", lambda payload, class_filter=None: ctx)

    dialog = object.__new__(JudgeModeDialog)
    dialog._class_entry = DummyEntry("SC01")
    dialog._scan_entry = DummyEntry()
    dialog.after_change_args = None
    dialog._after_change = lambda passed_ctx, label, focus_scan=True: setattr(
        dialog, "after_change_args", (passed_ctx, label, focus_scan)
    )

    accepted = JudgeModeDialog._accept_payload(dialog, "AutoNum:42", "NB")

    assert accepted is True
    assert dialog.after_change_args == (ctx, "NB", False)
    assert dialog._scan_entry.deleted is False
    assert dialog._scan_entry.focused is False
