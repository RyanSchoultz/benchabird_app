from models.class_def import ClassDef, MainClass, Species
from models.results import NotBenched, Result
from models.show_entry import CalculatedEntry


def seed_class_data():
    Species.create(seq=2, bird_type="Red Factor", type2="Red Factor", type3="Red")
    Species.create(seq=1, bird_type="Gloster", type2="Gloster", type3="Gloster")
    MainClass.create(main_class="Champion", mc_seq=1)
    MainClass.create(main_class="Novice", mc_seq=2)
    ClassDef.create(
        class_code="RF01",
        bird_type="Red Factor",
        type_b="Red Factor Type",
        main_class="Champion",
        colour="Red cock",
        class_seq=10,
    )
    ClassDef.create(
        class_code="GL01",
        bird_type="Gloster",
        type_b="Gloster Type",
        main_class="Novice",
        colour="Corona hen",
        class_seq=5,
    )


def test_list_judging_categories_orders_by_species_sequence(test_db):
    from services.judging_catalogue_service import list_judging_categories

    seed_class_data()
    CalculatedEntry.create(auto_num=20, exh_no=2, name="B", class_code="RF01")
    CalculatedEntry.create(auto_num=10, exh_no=1, name="A", class_code="GL01")

    categories = list_judging_categories()

    assert [(c.key, c.label, c.entry_count) for c in categories] == [
        ("Gloster", "Gloster", 1),
        ("Red Factor", "Red Factor", 1),
    ]


def test_get_judging_entries_for_category_preserves_access_inspired_order(test_db):
    from services.judging_catalogue_service import get_judging_entries

    seed_class_data()
    CalculatedEntry.create(auto_num=21, exh_no=2, name="B", class_code="RF01")
    CalculatedEntry.create(auto_num=20, exh_no=1, name="A", class_code="RF01")
    CalculatedEntry.create(auto_num=10, exh_no=3, name="C", class_code="GL01")

    rows = get_judging_entries("Red Factor")

    assert [r.auto_num for r in rows] == [20, 21]
    assert rows[0].category == "Red Factor"
    assert rows[0].main_class == "Champion"
    assert rows[0].class_code == "RF01"
    assert rows[0].colour == "Red cock"


def test_get_judging_entries_includes_existing_result_and_nb(test_db):
    from services.judging_catalogue_service import get_judging_entries

    seed_class_data()
    CalculatedEntry.create(auto_num=20, exh_no=1, name="A", class_code="RF01")
    Result.create(exhibit_no=20, result="1st")
    NotBenched.create(exhibit_no=20, not_benched="Not Benched", nb="NB")

    rows = get_judging_entries("Red Factor")

    assert rows[0].current_result == "1st"
    assert rows[0].not_benched is True


def test_save_category_results_records_placing_and_clears_nb(test_db):
    from services.judging_catalogue_service import save_category_results

    CalculatedEntry.create(auto_num=20, exh_no=1, name="A", class_code="RF01")
    NotBenched.create(exhibit_no=20, not_benched="Not Benched", nb="NB")

    saved = save_category_results({20: "BOB"})

    assert saved == 1
    assert Result.get(Result.exhibit_no == 20).result == "BOB"
    assert NotBenched.get_or_none(NotBenched.exhibit_no == 20) is None


def test_save_category_results_records_nb_and_clears_result(test_db):
    from services.judging_catalogue_service import save_category_results

    CalculatedEntry.create(auto_num=20, exh_no=1, name="A", class_code="RF01")
    Result.create(exhibit_no=20, result="1st")

    saved = save_category_results({20: "NB"})

    assert saved == 1
    assert Result.get(Result.exhibit_no == 20).result is None
    assert NotBenched.get_or_none(NotBenched.exhibit_no == 20) is not None


def test_save_category_results_clear_removes_result_and_nb(test_db):
    from services.judging_catalogue_service import save_category_results

    CalculatedEntry.create(auto_num=20, exh_no=1, name="A", class_code="RF01")
    Result.create(exhibit_no=20, result="1st")
    NotBenched.create(exhibit_no=20, not_benched="Not Benched", nb="NB")

    saved = save_category_results({20: "Clear"})

    assert saved == 1
    assert Result.get(Result.exhibit_no == 20).result is None
    assert NotBenched.get_or_none(NotBenched.exhibit_no == 20) is None


def test_list_class_options_orders_with_context(test_db):
    from services.judging_catalogue_service import list_class_options

    seed_class_data()

    options = list_class_options()

    assert [(o.class_code, o.category, o.main_class, o.colour) for o in options] == [
        ("GL01", "Gloster", "Novice", "Corona hen"),
        ("RF01", "Red Factor", "Champion", "Red cock"),
    ]


def test_save_category_results_reallocates_class_and_preserves_auto_num(test_db):
    from services.judging_catalogue_service import save_category_results

    seed_class_data()
    CalculatedEntry.create(auto_num=20, exh_no=1, name="A", class_code="GL01")

    saved = save_category_results({20: {"class_code": "RF01"}})

    row = CalculatedEntry.get_by_id(20)
    assert saved == 1
    assert row.auto_num == 20
    assert row.class_code == "RF01"


def test_save_category_results_reallocates_class_and_records_result(test_db):
    from services.judging_catalogue_service import save_category_results

    seed_class_data()
    CalculatedEntry.create(auto_num=20, exh_no=1, name="A", class_code="GL01")

    saved = save_category_results({20: {"class_code": "RF01", "result": "BOB"}})

    row = CalculatedEntry.get_by_id(20)
    assert saved == 1
    assert row.class_code == "RF01"
    assert Result.get(Result.exhibit_no == 20).result == "BOB"


def test_save_category_results_rejects_invalid_class_without_result_side_effect(test_db):
    from services.judging_catalogue_service import JudgingCatalogueError, save_category_results

    seed_class_data()
    CalculatedEntry.create(auto_num=20, exh_no=1, name="A", class_code="GL01")

    try:
        save_category_results({20: {"class_code": "BAD", "result": "BOB"}})
    except JudgingCatalogueError as exc:
        assert "Select a valid class" in str(exc)
    else:
        raise AssertionError("Expected invalid class to raise JudgingCatalogueError")

    row = CalculatedEntry.get_by_id(20)
    assert row.class_code == "GL01"
    assert Result.get_or_none(Result.exhibit_no == 20) is None


def test_reallocated_class_moves_row_to_new_category(test_db):
    from services.judging_catalogue_service import get_judging_entries, save_category_results

    seed_class_data()
    CalculatedEntry.create(auto_num=20, exh_no=1, name="A", class_code="GL01")

    save_category_results({20: {"class_code": "RF01"}})

    assert [r.auto_num for r in get_judging_entries("Gloster")] == []
    assert [r.auto_num for r in get_judging_entries("Red Factor")] == [20]
