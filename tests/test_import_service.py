# tests/test_import_service.py
# NOTE: requires real MDB and pyodbc — skipped automatically if MDB not present
import pytest
from pathlib import Path
from config import MDB_PATH

pytestmark = pytest.mark.skipif(
    not MDB_PATH.exists(),
    reason="MDB file not available"
)

def test_import_counts(test_db):
    from services.import_service import import_from_mdb
    results = import_from_mdb()
    assert results['exhibitors'] == 199
    assert results['show_entries'] == 559
    assert results['classes'] == 4807
    assert results['species'] == 36
    assert results['special_lists'] == 244
    assert results['special_winners'] == 244

def test_import_show_details(test_db):
    from services.import_service import import_from_mdb
    from models.reference import ShowDetails
    import_from_mdb()
    sd = ShowDetails.get_by_id(1)
    assert sd.show_eng == "Open Show"
    assert sd.club_eng_full == "Cape Town Bird Club"
