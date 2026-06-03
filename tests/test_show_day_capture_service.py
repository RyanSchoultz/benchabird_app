from models.class_def import ClassDef, MainClass, Species
from models.results import NotBenched, Result
from models.show_entry import CalculatedEntry
from models.special import SpecialList, SpecialWinner


def seed_capture_data():
    Species.create(seq=1, bird_type="Gloster", type2="Gloster")
    Species.create(seq=2, bird_type="Red Factor", type2="Red Factor")
    MainClass.create(main_class="Open", mc_seq=1)
    ClassDef.create(
        class_code="GL01",
        bird_type="Gloster",
        main_class="Open",
        colour="Corona hen",
        class_seq=1,
    )
    ClassDef.create(
        class_code="GL02",
        bird_type="Gloster",
        main_class="Open",
        colour="Consort cock",
        class_seq=2,
    )
    ClassDef.create(
        class_code="RF01",
        bird_type="Red Factor",
        main_class="Open",
        colour="Red cock",
        class_seq=1,
    )
    CalculatedEntry.create(auto_num=1, exh_no=10, name="Alice", class_code="GL01")
    CalculatedEntry.create(auto_num=2, exh_no=11, name="Bob", class_code="GL01")
    CalculatedEntry.create(auto_num=3, exh_no=12, name="Cara", class_code="GL02")
    CalculatedEntry.create(auto_num=4, exh_no=13, name="Dan", class_code="RF01")
    SpecialList.create(special_nr="S001", description="Best Gloster", prize1="Rosette")
    SpecialList.create(special_nr="S002", description="Best Red Factor", prize1="Medal")


def test_get_capture_summary_counts_and_next_action(test_db):
    from services.show_day_capture_service import get_capture_summary

    seed_capture_data()
    Result.create(exhibit_no=1, result="1st")
    NotBenched.create(exhibit_no=2, not_benched="Not Benched", nb="NB")
    SpecialWinner.create(special_nr="S001", exhibit_no=1, result="Special")

    summary = get_capture_summary()

    assert summary.total_categories == 2
    assert summary.results_entered == 1
    assert summary.not_benched == 1
    assert summary.specials_assigned == 1
    assert summary.issue_count >= 1
    assert summary.next_action


def test_get_category_statuses_tracks_not_started_in_progress_and_complete(test_db):
    from services.show_day_capture_service import get_category_statuses

    seed_capture_data()
    Result.create(exhibit_no=1, result="1st")
    NotBenched.create(exhibit_no=2, not_benched="Not Benched", nb="NB")
    Result.create(exhibit_no=3, result="2nd")

    rows = get_category_statuses()

    assert [(row.category, row.entry_count, row.completed_count, row.status) for row in rows] == [
        ("Gloster", 3, 3, "Complete"),
        ("Red Factor", 1, 0, "Not started"),
    ]


def test_validate_capture_detects_duplicates_missing_specials_and_orphans(test_db):
    from services.show_day_capture_service import validate_capture

    seed_capture_data()
    Result.create(exhibit_no=1, result="1st")
    Result.create(exhibit_no=2, result="1st")
    Result.create(exhibit_no=999, result="BOB")
    NotBenched.create(exhibit_no=1, not_benched="Not Benched", nb="NB")
    SpecialWinner.create(special_nr="S001", exhibit_no=1, result="Special")

    issues = validate_capture()
    issue_keys = {issue.kind for issue in issues}

    assert "duplicate-placing" in issue_keys
    assert "special-missing-winner" in issue_keys
    assert "special-assigned-nb" in issue_keys
    assert "result-unbenched" in issue_keys
    assert "category-incomplete" in issue_keys


def test_search_special_candidates_prefers_result_rows(test_db):
    from services.show_day_capture_service import search_special_candidates

    seed_capture_data()
    Result.create(exhibit_no=1, result="1st")

    rows = search_special_candidates("alice")

    assert rows[0].auto_num == 1
    assert rows[0].name == "Alice"
    assert rows[0].result == "1st"
