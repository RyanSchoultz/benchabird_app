# tests/test_models.py
def test_all_models_count(test_db):
    from models import ALL_MODELS
    assert len(ALL_MODELS) == 17

def test_exhibitor_create(test_db):
    from models.exhibitor import Exhibitor
    e = Exhibitor.create(name="Smith, J.", exh_no=1, town="Cape Town")
    assert Exhibitor.get_by_id(e.id).town == "Cape Town"

def test_show_entry_create(test_db):
    from models.show_entry import ShowEntry
    se = ShowEntry.create(auto_num=100, exh_no=1, class_code="SC01")
    assert ShowEntry.get_by_id(se.auto_num).class_code == "SC01"

def test_class_def_create(test_db):
    from models.class_def import ClassDef
    cd = ClassDef.create(class_code="G82", bird_type="CANARY", class_seq=10)
    assert ClassDef.get(ClassDef.class_code == "G82").bird_type == "CANARY"

def test_special_winner_create(test_db):
    from models.special import SpecialWinner
    sw = SpecialWinner.create(special_nr="RF05", exhibit_no=407, result="Special")
    assert SpecialWinner.get(SpecialWinner.special_nr == "RF05").exhibit_no == 407
