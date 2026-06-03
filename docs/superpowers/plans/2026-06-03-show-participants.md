# Show Participants Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the separate Entries, Check-in, and Late Entries pages with a unified Show Participants page that handles the full show workflow for each exhibitor in one place.

**Architecture:** A new `show_participants_service.py` handles all data queries (participants list, per-exhibitor entries with bench status, orphan detection, ExhNo assignment). A new `show_participants_view.py` two-panel view consumes this service. The calculate macro is replaced with a smart `auto_calculate_if_safe()` helper that runs silently pre-show and surfaces a manual control once benching starts. Late entry benching requires a new `source_late_entry_auto_num` field on `CalculatedEntry` to avoid namespace collision with `ShowEntry` auto_nums.

**Tech Stack:** Python 3.14, customtkinter, peewee ORM, SQLite, pytest (in-memory DB via conftest.py)

---

## File Map

| Action | File | Responsibility |
|---|---|---|
| Modify | `models/show_entry.py` | Add `source_late_entry_auto_num` to `CalculatedEntry` |
| Modify | `main.py` | Add migration for new column |
| Modify | `services/calculate_service.py` | Add `_benching_started`, `_results_recorded`, `auto_calculate_if_safe` |
| Create | `services/show_participants_service.py` | All data queries for the new page |
| Modify | `services/checkin_service.py` | Add `bench_late_entries`, `unbench_late_entries` |
| Modify | `views/_entry_dialog.py` | Accept optional pre-filled `exh_no` |
| Modify | `views/_late_entry_dialog.py` | Accept optional pre-filled `exh_no` and `name` |
| Create | `views/show_participants_view.py` | Two-panel view |
| Modify | `views/main_window.py` | Update NAV, `_make_view`, shortcuts |
| Delete | `views/entries_view.py` | Replaced |
| Delete | `views/checkin_view.py` | Replaced |
| Delete | `views/late_entries_view.py` | Replaced |
| Delete | `tests/test_checkin_view_imports.py` | Replaced by new import test |
| Create | `tests/test_show_participants_service.py` | Service unit tests |
| Create | `tests/test_calculate_service_auto.py` | Auto-calculate unit tests |
| Create | `tests/test_bench_late_entries.py` | Late entry benching tests |
| Create | `tests/test_show_participants_view_imports.py` | View smoke test |

---

## Task 1: Extend CalculatedEntry for late-entry benching

Late entries live in their own table (`late_entry`) with auto_nums starting at 1 — independent of `show_entry` auto_nums. Adding `source_late_entry_auto_num` keeps the two namespaces separate and makes the link explicit.

**Files:**
- Modify: `models/show_entry.py`
- Modify: `main.py`
- Test: `tests/test_models.py` (extend existing)

- [ ] **Step 1: Write a failing test**

Add to `tests/test_models.py`:

```python
def test_calculated_entry_has_source_late_entry_auto_num(test_db):
    from models.show_entry import CalculatedEntry
    CalculatedEntry.create(auto_num=1, source_late_entry_auto_num=99, exh_no=5, class_code="SC01")
    row = CalculatedEntry.get(CalculatedEntry.auto_num == 1)
    assert row.source_late_entry_auto_num == 99
```

- [ ] **Step 2: Run to verify it fails**

```
cd benchabird_app
pytest tests/test_models.py::test_calculated_entry_has_source_late_entry_auto_num -v
```

Expected: `FAILED` — `CalculatedEntry has no field source_late_entry_auto_num`

- [ ] **Step 3: Add the field to the model**

In `models/show_entry.py`, update `CalculatedEntry`:

```python
class CalculatedEntry(BaseModel):
    """Output of the 0010 Calculate_Entries_M workflow."""
    auto_num = IntegerField(primary_key=True)
    source_entry_auto_num = IntegerField(null=True, index=True)
    source_late_entry_auto_num = IntegerField(null=True, index=True)
    exh_no = IntegerField(null=True, index=True)
    name = CharField(max_length=75, null=True)
    class_code = CharField(max_length=50, null=True)

    class Meta:
        table_name = 'calculated_entry'
```

- [ ] **Step 4: Add the migration in `main.py`**

In `main.py`, inside `_migrate_db()`, add to the sql list:

```python
"ALTER TABLE calculated_entry ADD COLUMN source_late_entry_auto_num INTEGER",
```

- [ ] **Step 5: Run to verify it passes**

```
pytest tests/test_models.py::test_calculated_entry_has_source_late_entry_auto_num -v
```

Expected: `PASSED`

- [ ] **Step 6: Run the full suite to check nothing is broken**

```
pytest tests/ -v --tb=short
```

Expected: all previously passing tests still pass.

- [ ] **Step 7: Commit**

```bash
git add models/show_entry.py main.py tests/test_models.py
git commit -m "feat: add source_late_entry_auto_num to CalculatedEntry"
```

---

## Task 2: Auto-calculate helpers in calculate_service

The `auto_calculate_if_safe()` function replaces the manual Calculate button. It checks show state and either runs silently, returns a `"warning"` signal, or returns `"blocked"`.

**Files:**
- Modify: `services/calculate_service.py`
- Create: `tests/test_calculate_service_auto.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_calculate_service_auto.py`:

```python
from models.show_entry import ShowEntry, CalculatedEntry
from models.class_def import ClassDef
from models.exhibitor import Exhibitor
from models.results import Result


def _seed(test_db):
    Exhibitor.create(exh_no=1, name="Adams, A.")
    ClassDef.create(class_code="SC01", class_seq=10)
    ShowEntry.create(auto_num=10, exh_no=1, class_code="SC01")


def test_auto_calculate_runs_silently_when_no_calculated_entries(test_db):
    from services.calculate_service import auto_calculate_if_safe
    _seed(test_db)
    result = auto_calculate_if_safe()
    assert result == "done"
    assert CalculatedEntry.select().count() == 1


def test_auto_calculate_runs_silently_when_only_full_calculate_rows_exist(test_db):
    from services.calculate_service import auto_calculate_if_safe
    _seed(test_db)
    # Full calculate row has source_entry_auto_num = NULL
    CalculatedEntry.create(auto_num=1, exh_no=1, class_code="SC01")
    result = auto_calculate_if_safe()
    assert result == "done"


def test_auto_calculate_warns_when_individual_benching_started(test_db):
    from services.calculate_service import auto_calculate_if_safe
    _seed(test_db)
    CalculatedEntry.create(auto_num=1, source_entry_auto_num=10, exh_no=1, class_code="SC01")
    result = auto_calculate_if_safe()
    assert result == "warning"
    # Should NOT have recalculated
    assert CalculatedEntry.select().count() == 1


def test_auto_calculate_blocked_when_results_recorded(test_db):
    from services.calculate_service import auto_calculate_if_safe
    _seed(test_db)
    CalculatedEntry.create(auto_num=1, source_entry_auto_num=10, exh_no=1, class_code="SC01")
    Result.create(exhibit_no=1, result="1st")
    result = auto_calculate_if_safe()
    assert result == "blocked"
```

- [ ] **Step 2: Run to verify they fail**

```
pytest tests/test_calculate_service_auto.py -v
```

Expected: all 4 `FAILED` — `auto_calculate_if_safe` does not exist yet.

- [ ] **Step 3: Add helpers to `services/calculate_service.py`**

Append to `services/calculate_service.py`:

```python
def _benching_started() -> bool:
    """True if any CalculatedEntry was created via individual check-in (not full Calculate)."""
    return CalculatedEntry.select().where(
        CalculatedEntry.source_entry_auto_num.is_null(False)
    ).exists()


def _results_recorded() -> bool:
    """True if any result has been recorded — show is in progress or complete."""
    from models.results import Result
    return Result.select().where(Result.result.is_null(False)).exists()


def auto_calculate_if_safe() -> str:
    """
    Run calculate_entries() if safe to do so silently.

    Returns:
        "done"    — ran successfully
        "warning" — benching started; caller should show manual recalculate notice
        "blocked" — results recorded; recalculate is not permitted
    """
    if _results_recorded():
        return "blocked"
    if _benching_started():
        return "warning"
    calculate_entries()
    return "done"
```

- [ ] **Step 4: Run to verify they pass**

```
pytest tests/test_calculate_service_auto.py -v
```

Expected: all 4 `PASSED`

- [ ] **Step 5: Run full suite**

```
pytest tests/ -v --tb=short
```

- [ ] **Step 6: Commit**

```bash
git add services/calculate_service.py tests/test_calculate_service_auto.py
git commit -m "feat: add auto_calculate_if_safe to calculate_service"
```

---

## Task 3: ShowParticipantsService — participants list

All data queries for the left panel live here. The service returns typed dataclasses so the view has no SQL knowledge.

**Files:**
- Create: `services/show_participants_service.py`
- Create: `tests/test_show_participants_service.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_show_participants_service.py`:

```python
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry, LateEntry, CalculatedEntry


def _seed(test_db):
    Exhibitor.create(id=1, exh_no=1, name="Adams, A.", email="a@test.com", town="Cape Town")
    Exhibitor.create(id=2, exh_no=2, name="Botha, B.", email="b@test.com", town="Durban")
    Exhibitor.create(id=3, exh_no=None, name="Cupido, C.", email="c@test.com")
    ShowEntry.create(auto_num=10, exh_no=1, class_code="SC01")
    ShowEntry.create(auto_num=11, exh_no=1, class_code="SC02")
    ShowEntry.create(auto_num=12, exh_no=2, class_code="SC01")
    LateEntry.create(auto_num=1, exh_no=2, name="Botha, B.", class_code="SC03")


def test_get_participants_returns_only_exhibitors_with_entries(test_db):
    from services.show_participants_service import get_participants
    _seed(test_db)
    rows = get_participants()
    assert [r.exh_no for r in rows] == [1, 2]


def test_get_participants_counts_entries_and_late(test_db):
    from services.show_participants_service import get_participants
    _seed(test_db)
    rows = get_participants()
    a = next(r for r in rows if r.exh_no == 1)
    b = next(r for r in rows if r.exh_no == 2)
    assert a.entry_count == 2 and a.late_count == 0
    assert b.entry_count == 2 and b.late_count == 1


def test_get_participants_counts_benched(test_db):
    from services.show_participants_service import get_participants
    _seed(test_db)
    CalculatedEntry.create(auto_num=100, source_entry_auto_num=10, exh_no=1, class_code="SC01")
    rows = get_participants()
    a = next(r for r in rows if r.exh_no == 1)
    assert a.benched_count == 1


def test_get_participants_filter_unbenched(test_db):
    from services.show_participants_service import get_participants
    _seed(test_db)
    CalculatedEntry.create(auto_num=100, source_entry_auto_num=10, exh_no=1, class_code="SC01")
    CalculatedEntry.create(auto_num=101, source_entry_auto_num=11, exh_no=1, class_code="SC02")
    rows = get_participants(filter="unbenched")
    assert [r.exh_no for r in rows] == [2]


def test_get_participants_filter_late(test_db):
    from services.show_participants_service import get_participants
    _seed(test_db)
    rows = get_participants(filter="late")
    assert [r.exh_no for r in rows] == [2]


def test_search_registry_finds_by_name(test_db):
    from services.show_participants_service import search_registry
    _seed(test_db)
    results = search_registry("Cupido")
    assert len(results) == 1 and results[0].name == "Cupido, C."


def test_get_orphaned_exh_nos_detects_missing_exhibitor(test_db):
    from services.show_participants_service import get_orphaned_exh_nos
    _seed(test_db)
    ShowEntry.create(auto_num=99, exh_no=99, class_code="SC01")
    orphans = get_orphaned_exh_nos()
    assert 99 in orphans
    assert 1 not in orphans


def test_next_available_exh_no(test_db):
    from services.show_participants_service import next_available_exh_no
    _seed(test_db)
    assert next_available_exh_no() == 3


def test_assign_exh_no_sets_and_validates_uniqueness(test_db):
    from services.show_participants_service import assign_exh_no
    import pytest
    _seed(test_db)
    assign_exh_no(exhibitor_id=3, exh_no=5)
    assert Exhibitor.get_by_id(3).exh_no == 5
    with pytest.raises(ValueError, match="already assigned"):
        assign_exh_no(exhibitor_id=3, exh_no=1)
```

- [ ] **Step 2: Run to verify they fail**

```
pytest tests/test_show_participants_service.py -v
```

Expected: all `FAILED` — module does not exist yet.

- [ ] **Step 3: Create `services/show_participants_service.py`**

```python
# services/show_participants_service.py
from __future__ import annotations
from dataclasses import dataclass
from peewee import fn
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry, LateEntry, CalculatedEntry


@dataclass(frozen=True)
class ParticipantRow:
    exhibitor_id: int
    exh_no: int | None
    name: str
    email: str | None
    entry_count: int
    benched_count: int
    late_count: int


@dataclass(frozen=True)
class ParticipantEntryRow:
    source_auto_num: int
    is_late: bool
    class_code: str | None
    class_desc: str | None
    auto_num: int | None
    status: str
    blocked_reason: str | None


def get_participants(filter: str = "all") -> list[ParticipantRow]:
    db = Exhibitor._meta.database
    cursor = db.execute_sql("""
        SELECT
            e.id,
            e.exh_no,
            e.name,
            e.email,
            (SELECT COUNT(*) FROM show_entry WHERE exh_no = e.exh_no) +
            (SELECT COUNT(*) FROM late_entry  WHERE exh_no = e.exh_no) AS entry_count,
            (SELECT COUNT(*) FROM calculated_entry
                WHERE source_entry_auto_num IN
                    (SELECT auto_num FROM show_entry WHERE exh_no = e.exh_no)) +
            (SELECT COUNT(*) FROM calculated_entry
                WHERE source_late_entry_auto_num IN
                    (SELECT auto_num FROM late_entry WHERE exh_no = e.exh_no)) AS benched_count,
            (SELECT COUNT(*) FROM late_entry WHERE exh_no = e.exh_no) AS late_count
        FROM exhibitor e
        WHERE e.exh_no IS NOT NULL
          AND (
            EXISTS (SELECT 1 FROM show_entry WHERE exh_no = e.exh_no)
            OR EXISTS (SELECT 1 FROM late_entry WHERE exh_no = e.exh_no)
          )
        ORDER BY e.exh_no
    """)
    rows = [
        ParticipantRow(
            exhibitor_id=r[0], exh_no=r[1], name=r[2] or "",
            email=r[3], entry_count=r[4], benched_count=r[5], late_count=r[6],
        )
        for r in cursor.fetchall()
    ]
    if filter == "unbenched":
        return [r for r in rows if r.entry_count > r.benched_count]
    if filter == "late":
        return [r for r in rows if r.late_count > 0]
    return rows


def search_registry(query: str) -> list[Exhibitor]:
    """Search the full Exhibitor master registry (all members, not just current show)."""
    q = (query or "").strip()
    if not q:
        return []
    return list(
        Exhibitor.select().where(
            Exhibitor.name.contains(q) | Exhibitor.email.contains(q)
        ).order_by(Exhibitor.name).limit(20)
    )


def get_orphaned_exh_nos() -> list[int]:
    """ExhNos in ShowEntry that have no matching Exhibitor record."""
    db = ShowEntry._meta.database
    cursor = db.execute_sql("""
        SELECT DISTINCT se.exh_no
        FROM show_entry se
        LEFT JOIN exhibitor e ON se.exh_no = e.exh_no
        WHERE e.id IS NULL AND se.exh_no IS NOT NULL
    """)
    return [row[0] for row in cursor.fetchall()]


def next_available_exh_no() -> int:
    max_no = Exhibitor.select(fn.MAX(Exhibitor.exh_no)).scalar() or 0
    return max_no + 1


def assign_exh_no(exhibitor_id: int, exh_no: int) -> None:
    if Exhibitor.select().where(
        (Exhibitor.exh_no == exh_no) & (Exhibitor.id != exhibitor_id)
    ).exists():
        raise ValueError(f"ExhNo {exh_no} is already assigned to another exhibitor.")
    exhibitor = Exhibitor.get_by_id(exhibitor_id)
    exhibitor.exh_no = exh_no
    exhibitor.save()
```

- [ ] **Step 4: Run to verify they pass**

```
pytest tests/test_show_participants_service.py -v
```

Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add services/show_participants_service.py tests/test_show_participants_service.py
git commit -m "feat: add ShowParticipantsService participants list queries"
```

---

## Task 4: ShowParticipantsService — per-exhibitor entries

`get_participant_entries` merges `ShowEntry` and `LateEntry` rows for one exhibitor, annotating each with bench status and class description.

**Files:**
- Modify: `services/show_participants_service.py`
- Modify: `tests/test_show_participants_service.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_show_participants_service.py`:

```python
from models.class_glossary import ClassGlossary
from models.results import Result, NotBenched


def test_get_participant_entries_show_entry_not_benched(test_db):
    from services.show_participants_service import get_participant_entries
    Exhibitor.create(exh_no=1, name="Adams, A.")
    ShowEntry.create(auto_num=10, exh_no=1, class_code="SC01")
    rows = get_participant_entries(1)
    assert len(rows) == 1
    assert rows[0].source_auto_num == 10
    assert rows[0].is_late is False
    assert rows[0].auto_num is None
    assert rows[0].status == "Not benched"


def test_get_participant_entries_show_entry_benched(test_db):
    from services.show_participants_service import get_participant_entries
    Exhibitor.create(exh_no=1, name="Adams, A.")
    ShowEntry.create(auto_num=10, exh_no=1, class_code="SC01")
    CalculatedEntry.create(auto_num=55, source_entry_auto_num=10, exh_no=1, class_code="SC01")
    rows = get_participant_entries(1)
    assert rows[0].auto_num == 55
    assert rows[0].status == "Benched #55"


def test_get_participant_entries_late_entry_not_benched(test_db):
    from services.show_participants_service import get_participant_entries
    Exhibitor.create(exh_no=1, name="Adams, A.")
    LateEntry.create(auto_num=1, exh_no=1, name="Adams, A.", class_code="SC02")
    rows = get_participant_entries(1)
    assert rows[0].is_late is True
    assert rows[0].status == "LATE · Not benched"


def test_get_participant_entries_late_entry_benched(test_db):
    from services.show_participants_service import get_participant_entries
    Exhibitor.create(exh_no=1, name="Adams, A.")
    LateEntry.create(auto_num=1, exh_no=1, name="Adams, A.", class_code="SC02")
    CalculatedEntry.create(auto_num=77, source_late_entry_auto_num=1, exh_no=1, class_code="SC02")
    rows = get_participant_entries(1)
    assert rows[0].auto_num == 77
    assert rows[0].status == "LATE · Benched #77"


def test_get_participant_entries_blocked_by_result(test_db):
    from services.show_participants_service import get_participant_entries
    Exhibitor.create(exh_no=1, name="Adams, A.")
    ShowEntry.create(auto_num=10, exh_no=1, class_code="SC01")
    CalculatedEntry.create(auto_num=55, source_entry_auto_num=10, exh_no=1, class_code="SC01")
    Result.create(exhibit_no=55, result="1st")
    rows = get_participant_entries(1)
    assert rows[0].blocked_reason == "Has result"
    assert rows[0].status == "Has result"


def test_get_participant_entries_includes_class_description(test_db):
    from services.show_participants_service import get_participant_entries
    Exhibitor.create(exh_no=1, name="Adams, A.")
    ShowEntry.create(auto_num=10, exh_no=1, class_code="SC01")
    ClassGlossary.create(class_code="SC01", description="Open Cock")
    rows = get_participant_entries(1)
    assert rows[0].class_desc == "Open Cock"
```

- [ ] **Step 2: Run to verify they fail**

```
pytest tests/test_show_participants_service.py::test_get_participant_entries_show_entry_not_benched -v
```

Expected: `FAILED` — `get_participant_entries` not defined yet.

- [ ] **Step 3: Add `get_participant_entries` to `services/show_participants_service.py`**

Append after the existing imports and `assign_exh_no` function:

```python
def get_participant_entries(exh_no: int) -> list[ParticipantEntryRow]:
    from models.class_glossary import ClassGlossary
    from services.checkin_service import _blocked_reason

    class_desc_map = {
        g.class_code: g.description
        for g in ClassGlossary.select()
        if g.class_code
    }

    calc_by_source = {
        ce.source_entry_auto_num: ce
        for ce in CalculatedEntry.select().where(
            (CalculatedEntry.exh_no == exh_no)
            & CalculatedEntry.source_entry_auto_num.is_null(False)
        )
    }
    calc_by_late = {
        ce.source_late_entry_auto_num: ce
        for ce in CalculatedEntry.select().where(
            (CalculatedEntry.exh_no == exh_no)
            & CalculatedEntry.source_late_entry_auto_num.is_null(False)
        )
    }

    rows: list[ParticipantEntryRow] = []

    for entry in ShowEntry.select().where(ShowEntry.exh_no == exh_no).order_by(ShowEntry.auto_num):
        ce = calc_by_source.get(entry.auto_num)
        auto_num = ce.auto_num if ce else None
        blocked = _blocked_reason(auto_num) if auto_num else None
        if auto_num is None:
            status = "Not benched"
        elif blocked:
            status = blocked
        else:
            status = f"Benched #{auto_num}"
        rows.append(ParticipantEntryRow(
            source_auto_num=entry.auto_num,
            is_late=False,
            class_code=entry.class_code,
            class_desc=class_desc_map.get(entry.class_code or "", "") or "",
            auto_num=auto_num,
            status=status,
            blocked_reason=blocked,
        ))

    for entry in LateEntry.select().where(LateEntry.exh_no == exh_no).order_by(LateEntry.auto_num):
        ce = calc_by_late.get(entry.auto_num)
        auto_num = ce.auto_num if ce else None
        blocked = _blocked_reason(auto_num) if auto_num else None
        if auto_num:
            status = f"LATE · Benched #{auto_num}"
        else:
            status = "LATE · Not benched"
        rows.append(ParticipantEntryRow(
            source_auto_num=entry.auto_num,
            is_late=True,
            class_code=entry.class_code,
            class_desc=class_desc_map.get(entry.class_code or "", "") or "",
            auto_num=auto_num,
            status=status,
            blocked_reason=blocked,
        ))

    return rows
```

- [ ] **Step 4: Run to verify they pass**

```
pytest tests/test_show_participants_service.py -v
```

Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add services/show_participants_service.py tests/test_show_participants_service.py
git commit -m "feat: add get_participant_entries to show_participants_service"
```

---

## Task 5: Bench and unbench late entries in checkin_service

`bench_late_entries` mirrors `bench_entries` but reads from `LateEntry` and sets `source_late_entry_auto_num`. `unbench_late_entries` mirrors `unbench_entries` with the same field.

**Files:**
- Modify: `services/checkin_service.py`
- Create: `tests/test_bench_late_entries.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_bench_late_entries.py`:

```python
from models.exhibitor import Exhibitor
from models.show_entry import LateEntry, CalculatedEntry
from models.results import Result, NotBenched


def _seed(test_db):
    Exhibitor.create(exh_no=7, name="Alice Canary")
    LateEntry.create(auto_num=1, exh_no=7, name="Alice Canary", class_code="GL01")
    LateEntry.create(auto_num=2, exh_no=7, name="Alice Canary", class_code="RF01")


def test_bench_late_entries_creates_calculated_entries(test_db):
    from services.checkin_service import bench_late_entries
    _seed(test_db)
    result = bench_late_entries([1, 2])
    assert result.created == [1, 2]
    assert result.skipped == []
    rows = list(CalculatedEntry.select().order_by(CalculatedEntry.auto_num))
    assert [(r.auto_num, r.source_late_entry_auto_num, r.class_code) for r in rows] == [
        (1, 1, "GL01"),
        (2, 2, "RF01"),
    ]


def test_bench_late_entries_skips_already_benched(test_db):
    from services.checkin_service import bench_late_entries
    _seed(test_db)
    CalculatedEntry.create(auto_num=10, source_late_entry_auto_num=1, exh_no=7, class_code="GL01")
    result = bench_late_entries([1, 2])
    assert result.created == [11]
    assert result.skipped == [1]


def test_unbench_late_entries_removes_safe_row(test_db):
    from services.checkin_service import unbench_late_entries
    _seed(test_db)
    CalculatedEntry.create(auto_num=10, source_late_entry_auto_num=1, exh_no=7, class_code="GL01")
    result = unbench_late_entries([1])
    assert result.removed == [10]
    assert CalculatedEntry.get_or_none(CalculatedEntry.auto_num == 10) is None


def test_unbench_late_entries_blocks_when_result_exists(test_db):
    from services.checkin_service import unbench_late_entries
    _seed(test_db)
    CalculatedEntry.create(auto_num=10, source_late_entry_auto_num=1, exh_no=7, class_code="GL01")
    Result.create(exhibit_no=10, result="1st")
    result = unbench_late_entries([1])
    assert result.blocked == {1: "Has result"}
    assert CalculatedEntry.get_or_none(CalculatedEntry.auto_num == 10) is not None
```

- [ ] **Step 2: Run to verify they fail**

```
pytest tests/test_bench_late_entries.py -v
```

Expected: all `FAILED` — `bench_late_entries` not defined yet.

- [ ] **Step 3: Add functions to `services/checkin_service.py`**

Add the following imports at the top of `checkin_service.py` (after existing imports):

```python
from models.show_entry import LateEntry
```

Append to the end of `services/checkin_service.py`:

```python
def bench_late_entries(late_entry_auto_nums: list[int]) -> BenchResult:
    if not late_entry_auto_nums:
        return BenchResult()
    db = CalculatedEntry._meta.database
    created: list[int] = []
    skipped: list[int] = []
    with db.atomic():
        max_auto_num = CalculatedEntry.select(fn.MAX(CalculatedEntry.auto_num)).scalar() or 0
        for source_auto_num in late_entry_auto_nums:
            existing = CalculatedEntry.get_or_none(
                CalculatedEntry.source_late_entry_auto_num == source_auto_num
            )
            if existing is not None:
                skipped.append(source_auto_num)
                continue
            entry = LateEntry.get_or_none(LateEntry.auto_num == source_auto_num)
            if entry is None:
                skipped.append(source_auto_num)
                continue
            exhibitor = Exhibitor.get_or_none(Exhibitor.exh_no == entry.exh_no)
            max_auto_num += 1
            CalculatedEntry.create(
                auto_num=max_auto_num,
                source_late_entry_auto_num=entry.auto_num,
                exh_no=entry.exh_no,
                name=exhibitor.name if exhibitor else entry.name,
                class_code=entry.class_code,
            )
            created.append(max_auto_num)
    return BenchResult(created=created, skipped=skipped)


def unbench_late_entries(late_entry_auto_nums: list[int]) -> UnbenchResult:
    removed: list[int] = []
    blocked: dict[int, str] = {}
    missing: list[int] = []
    db = CalculatedEntry._meta.database
    with db.atomic():
        for source_auto_num in late_entry_auto_nums:
            calc = CalculatedEntry.get_or_none(
                CalculatedEntry.source_late_entry_auto_num == source_auto_num
            )
            if calc is None:
                missing.append(source_auto_num)
                continue
            reason = _blocked_reason(calc.auto_num)
            if reason:
                blocked[source_auto_num] = reason
                continue
            auto_num = calc.auto_num
            calc.delete_instance()
            removed.append(auto_num)
    return UnbenchResult(removed=removed, blocked=blocked, missing=missing)
```

- [ ] **Step 4: Run to verify they pass**

```
pytest tests/test_bench_late_entries.py -v
```

Expected: all `PASSED`

- [ ] **Step 5: Run full suite**

```
pytest tests/ -v --tb=short
```

- [ ] **Step 6: Commit**

```bash
git add services/checkin_service.py tests/test_bench_late_entries.py
git commit -m "feat: add bench_late_entries and unbench_late_entries to checkin_service"
```

---

## Task 6: Extend entry dialogs to accept pre-filled ExhNo

When opened from Show Participants, the dialogs receive the exhibitor's ExhNo (and name for late entries) so the user doesn't need to type them. The field is pre-filled and disabled.

**Files:**
- Modify: `views/_entry_dialog.py`
- Modify: `views/_late_entry_dialog.py`

No new tests needed — these are UI-only changes. The existing service tests cover validation.

- [ ] **Step 1: Update `views/_entry_dialog.py`**

Replace the class definition and `__init__`:

```python
class EntryDialog(ctk.CTkToplevel):
    """Add a single show entry. Pass exh_no to pre-fill and lock the exhibitor field."""
    def __init__(self, parent, exh_no: int | None = None):
        super().__init__(parent)
        self.title("Add Show Entry")
        self.geometry("360x240")
        self.resizable(False, False)
        self.grab_set()
        self.after(50, self.lift)
        self._preset_exh_no = exh_no
        self._class_codes = _load_class_codes()
        self._build()
```

Replace the ExhNo field build block inside `_build` (the `ctk.CTkLabel` + `ctk.CTkEntry` for "Exhibitor #:"):

```python
        ctk.CTkLabel(form, text="Exhibitor #:", anchor="e").grid(
            row=0, column=0, sticky="e", padx=(0, 8), pady=6
        )
        self._exh_entry = ctk.CTkEntry(form, placeholder_text="e.g. 42")
        if self._preset_exh_no is not None:
            self._exh_entry.insert(0, str(self._preset_exh_no))
            self._exh_entry.configure(state="disabled")
        self._exh_entry.grid(row=0, column=1, sticky="ew", pady=6)
        self._exh_entry.bind("<Return>", lambda e: self._class_combo.focus())
        self._exh_entry.bind("<Tab>", lambda e: (self._class_combo.focus(), "break"))
```

- [ ] **Step 2: Update `views/_late_entry_dialog.py`**

Replace `__init__`:

```python
class LateEntryDialog(ctk.CTkToplevel):
    """Add a single late entry. Pass exh_no and name to pre-fill and lock those fields."""
    def __init__(self, parent, exh_no: int | None = None, name: str | None = None):
        super().__init__(parent)
        self.title("Add Late Entry")
        self.geometry("340x240")
        self.resizable(False, False)
        self.grab_set()
        self.after(50, self.lift)
        self._preset_exh_no = exh_no
        self._preset_name = name
        self._build()
```

Replace the fields build loop inside `_build`:

```python
        fields = [
            ("Exhibitor #:", "_exh_entry",  "e.g. 42"),
            ("Name:",        "_name_entry",  "e.g. Smith, J."),
            ("Class Code:",  "_class_entry", "e.g. SC01"),
        ]
        presets = {
            "_exh_entry":  str(self._preset_exh_no) if self._preset_exh_no is not None else None,
            "_name_entry": self._preset_name,
        }
        for row_i, (label, attr, ph) in enumerate(fields):
            ctk.CTkLabel(form, text=label, anchor="e").grid(
                row=row_i, column=0, sticky="e", padx=(0, 8), pady=6
            )
            entry = ctk.CTkEntry(form, placeholder_text=ph)
            preset = presets.get(attr)
            if preset:
                entry.insert(0, preset)
                entry.configure(state="disabled")
            entry.grid(row=row_i, column=1, sticky="ew", pady=6)
            setattr(self, attr, entry)
```

- [ ] **Step 3: Run full suite to confirm no regressions**

```
pytest tests/ -v --tb=short
```

- [ ] **Step 4: Commit**

```bash
git add views/_entry_dialog.py views/_late_entry_dialog.py
git commit -m "feat: pre-fill ExhNo/name in entry dialogs when opened from Show Participants"
```

---

## Task 7: ShowParticipantsView — left panel

The left panel shows filtered participants, the orphan warning banner, and the registry search / "+Add to show" flow.

**Files:**
- Create: `views/show_participants_view.py`
- Create: `tests/test_show_participants_view_imports.py`

- [ ] **Step 1: Write smoke test**

Create `tests/test_show_participants_view_imports.py`:

```python
def test_show_participants_view_imports(test_db):
    from views.show_participants_view import ShowParticipantsView
    assert ShowParticipantsView.__name__ == "ShowParticipantsView"
```

- [ ] **Step 2: Run to verify it fails**

```
pytest tests/test_show_participants_view_imports.py -v
```

Expected: `FAILED` — module does not exist.

- [ ] **Step 3: Create `views/show_participants_view.py` with left panel**

```python
# views/show_participants_view.py
import customtkinter as ctk

from services.show_participants_service import (
    ParticipantRow, ParticipantEntryRow,
    get_participants, search_registry, get_orphaned_exh_nos,
    next_available_exh_no, assign_exh_no, get_participant_entries,
)
from services.checkin_service import (
    bench_entries, bench_late_entries,
    unbench_entries, unbench_late_entries,
)
from services.calculate_service import auto_calculate_if_safe
from services.entry_service import add_entry
from services.late_entry_service import add_late_entry


class ShowParticipantsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._participants: list[ParticipantRow] = []
        self._selected: ParticipantRow | None = None
        self._entry_rows: list[ParticipantEntryRow] = []
        self._entry_vars: dict[tuple[int, bool], ctk.BooleanVar] = {}
        self._active_filter = "all"
        self._needs_recalc = False
        self._build()
        self._refresh_left()

    # ── Layout ──────────────────────────────────────────────────────

    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_left()
        self._build_right()

    def _build_left(self):
        left = ctk.CTkFrame(self, corner_radius=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        left.grid_rowconfigure(4, weight=1)
        left.grid_columnconfigure(0, weight=1)
        self._left = left

        ctk.CTkLabel(
            left, text="Show Participants",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 4))

        # Search
        search_frame = ctk.CTkFrame(left, fg_color="transparent")
        search_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 4))
        search_frame.grid_columnconfigure(0, weight=1)
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search_change())
        ctk.CTkEntry(
            search_frame, textvariable=self._search_var,
            placeholder_text="Name, ExhNo, email, class…",
        ).grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(
            search_frame, text="✕", width=28, height=28,
            fg_color="transparent", text_color=("gray40", "gray60"),
            command=lambda: self._search_var.set(""),
        ).grid(row=0, column=1, padx=(4, 0))

        # Filter chips
        self._filter_seg = ctk.CTkSegmentedButton(
            left,
            values=["All", "Unbenched", "Late"],
            command=self._on_filter_change,
        )
        self._filter_seg.set("All")
        self._filter_seg.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 6))

        # Orphan warning (hidden until needed)
        self._orphan_btn = ctk.CTkButton(
            left, text="",
            fg_color=("orange3", "darkorange"),
            text_color="white",
            anchor="w",
            height=32,
            command=self._show_orphaned,
        )

        # Participant list
        self._list_frame = ctk.CTkScrollableFrame(left, width=290)
        self._list_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def _build_right(self):
        right = ctk.CTkFrame(self, corner_radius=8)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(4, weight=1)
        self._right = right

        self._right_header = ctk.CTkLabel(
            right, text="Select an exhibitor.",
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
        )
        self._right_header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))

        # Recalculate notice (hidden until needed)
        self._recalc_frame = ctk.CTkFrame(right, fg_color=("orange3", "darkorange"), corner_radius=6)
        ctk.CTkLabel(
            self._recalc_frame,
            text="  Entries changed — bench numbers may be stale.",
            font=ctk.CTkFont(size=11), text_color="white",
        ).pack(side="left", pady=6)
        ctk.CTkButton(
            self._recalc_frame, text="Recalculate", width=100,
            fg_color=("white", "gray20"), text_color=("gray10", "white"),
            command=self._on_recalculate,
        ).pack(side="right", padx=8, pady=6)

        # Action bar
        act = ctk.CTkFrame(right, fg_color="transparent")
        act.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 4))
        ctk.CTkButton(act, text="Select Unbenched",
                      command=self._select_all_unbenched).pack(side="left", padx=(0, 4))
        ctk.CTkButton(act, text="Clear",
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=self._clear_selection).pack(side="left", padx=4)
        ctk.CTkButton(act, text="Bench Selected",
                      command=self._bench_selected).pack(side="right")
        ctk.CTkButton(act, text="Unbench Selected",
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=self._unbench_selected).pack(side="right", padx=(0, 4))

        # Add entry bar
        add_bar = ctk.CTkFrame(right, fg_color="transparent")
        add_bar.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 6))
        ctk.CTkButton(add_bar, text="+ Add Entry", width=110,
                      command=self._open_add_entry).pack(side="left", padx=(0, 4))
        ctk.CTkButton(add_bar, text="+ Add Late Entry", width=130,
                      command=self._open_add_late_entry).pack(side="left")

        self._status = ctk.CTkLabel(
            right, text="", font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
        )
        self._status.grid(row=3, column=0, sticky="e", padx=12)

        # Entries list
        self._entries_frame = ctk.CTkScrollableFrame(right)
        self._entries_frame.grid(row=4, column=0, sticky="nsew", padx=12, pady=(0, 12))

    # ── Left panel logic ─────────────────────────────────────────────

    def _refresh_left(self):
        self._participants = get_participants(filter=self._active_filter)
        self._render_participant_list(self._participants)
        self._check_orphans()

    def _on_search_change(self):
        q = self._search_var.get().strip()
        if not q:
            self._refresh_left()
            return
        # Search current participants by name/ExhNo/email
        lower_q = q.lower()
        filtered = [
            p for p in get_participants()
            if lower_q in (p.name or "").lower()
            or lower_q in str(p.exh_no or "")
            or lower_q in (p.email or "").lower()
        ]
        # Also search the master registry for non-participants
        registry_hits = [
            e for e in search_registry(q)
            if e.exh_no not in {p.exh_no for p in filtered}
        ]
        self._render_participant_list(filtered, registry_extras=registry_hits)

    def _on_filter_change(self, value: str):
        filter_map = {"All": "all", "Unbenched": "unbenched", "Late": "late"}
        self._active_filter = filter_map.get(value, "all")
        self._search_var.set("")
        self._refresh_left()

    def _check_orphans(self):
        orphans = get_orphaned_exh_nos()
        if orphans:
            self._orphan_btn.configure(
                text=f"  ⚠ {len(orphans)} entries have no matching exhibitor"
            )
            self._orphan_btn.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 4))
        else:
            self._orphan_btn.grid_remove()

    def _show_orphaned(self):
        self._search_var.set("")
        self._active_filter = "all"
        self._filter_seg.set("All")
        orphan_nos = set(get_orphaned_exh_nos())
        all_p = get_participants()
        orphaned = [p for p in all_p if p.exh_no in orphan_nos]
        self._render_participant_list(orphaned)

    def _render_participant_list(self, rows: list[ParticipantRow], registry_extras=None):
        for child in self._list_frame.winfo_children():
            child.destroy()

        if not rows and not registry_extras:
            ctk.CTkLabel(
                self._list_frame, text="No participants found.",
                text_color=("gray45", "gray60"),
            ).pack(anchor="w", padx=4, pady=8)
            return

        for p in rows:
            sub = f"{p.entry_count} entries · {p.benched_count} benched"
            if p.late_count:
                sub += f" · {p.late_count} late"
            btn = ctk.CTkButton(
                self._list_frame,
                text=f"#{p.exh_no}  {p.name}\n{sub}",
                anchor="w", height=52,
                fg_color=("gray82", "gray24"),
                text_color=("gray10", "gray90"),
                command=lambda _p=p: self._select_participant(_p),
            )
            btn.pack(fill="x", padx=2, pady=3)

        if registry_extras:
            ctk.CTkLabel(
                self._list_frame, text="Registry (not in show):",
                font=ctk.CTkFont(size=10), text_color=("gray50", "gray55"),
            ).pack(anchor="w", padx=4, pady=(8, 2))
            for e in registry_extras:
                label = f"+ {e.name}"
                if e.exh_no:
                    label = f"#{e.exh_no}  {e.name}"
                btn = ctk.CTkButton(
                    self._list_frame,
                    text=label,
                    anchor="w", height=36,
                    fg_color=("gray88", "gray20"),
                    text_color=("gray30", "gray60"),
                    command=lambda _e=e: self._add_registry_exhibitor(_e),
                )
                btn.pack(fill="x", padx=2, pady=2)

    def _add_registry_exhibitor(self, exhibitor):
        if exhibitor.exh_no is None:
            self._prompt_assign_exh_no(exhibitor)
        else:
            fake_row = ParticipantRow(
                exhibitor_id=exhibitor.id,
                exh_no=exhibitor.exh_no,
                name=exhibitor.name,
                email=exhibitor.email,
                entry_count=0, benched_count=0, late_count=0,
            )
            self._select_participant(fake_row)

    def _prompt_assign_exh_no(self, exhibitor):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Assign Exhibitor Number")
        dlg.geometry("340x160")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.after(50, dlg.lift)

        ctk.CTkLabel(
            dlg, text=f"Assign a show number for:\n{exhibitor.name}",
            font=ctk.CTkFont(size=12),
        ).pack(padx=20, pady=(16, 8))

        frame = ctk.CTkFrame(dlg, fg_color="transparent")
        frame.pack(fill="x", padx=20)
        ctk.CTkLabel(frame, text="ExhNo:").pack(side="left", padx=(0, 8))
        var = ctk.StringVar(value=str(next_available_exh_no()))
        entry = ctk.CTkEntry(frame, textvariable=var, width=80)
        entry.pack(side="left")
        msg = ctk.CTkLabel(dlg, text="", font=ctk.CTkFont(size=11),
                           text_color=("red4", "tomato"))
        msg.pack(pady=4)

        def _confirm():
            val = var.get().strip()
            if not val.isdigit():
                msg.configure(text="Must be a number.")
                return
            try:
                assign_exh_no(exhibitor.id, int(val))
            except ValueError as exc:
                msg.configure(text=str(exc))
                return
            dlg.destroy()
            self._refresh_left()
            updated = next(
                (p for p in self._participants if p.exh_no == int(val)), None
            )
            if updated:
                self._select_participant(updated)

        ctk.CTkButton(dlg, text="Assign & Open", command=_confirm).pack(pady=(4, 12))

    # ── Right panel logic ─────────────────────────────────────────────

    def _select_participant(self, p: ParticipantRow):
        self._selected = p
        self._right_header.configure(
            text=f"#{p.exh_no}  {p.name}  ·  {p.entry_count} entries · {p.benched_count} benched"
        )
        self._load_entries()

    def _load_entries(self):
        for child in self._entries_frame.winfo_children():
            child.destroy()
        self._entry_vars = {}
        if self._selected is None:
            return

        self._entry_rows = get_participant_entries(self._selected.exh_no)

        if not self._entry_rows:
            ctk.CTkLabel(
                self._entries_frame, text="No entries yet. Use '+ Add Entry' to begin.",
                text_color=("gray45", "gray60"),
            ).pack(anchor="w", padx=8, pady=8)
            return

        # Header row
        headers = [("Bench", 56), ("Class", 80), ("Description", 0), ("Status", 180)]
        for col, (h, w) in enumerate(headers):
            ctk.CTkLabel(
                self._entries_frame, text=h,
                width=w if w else 1,
                font=ctk.CTkFont(size=11, weight="bold"),
                anchor="w",
            ).grid(row=0, column=col, sticky="ew" if w == 0 else "w", padx=4, pady=4)
        self._entries_frame.grid_columnconfigure(2, weight=1)

        for row_i, row in enumerate(self._entry_rows, start=1):
            key = (row.source_auto_num, row.is_late)
            var = ctk.BooleanVar(value=False)
            self._entry_vars[key] = var
            disabled = row.blocked_reason is not None
            ctk.CTkCheckBox(
                self._entries_frame, text="", variable=var, width=48,
                state="disabled" if disabled else "normal",
            ).grid(row=row_i, column=0, sticky="w", padx=4, pady=2)
            ctk.CTkLabel(
                self._entries_frame,
                text=row.class_code or "", width=80, anchor="w",
            ).grid(row=row_i, column=1, sticky="w", padx=4, pady=2)
            ctk.CTkLabel(
                self._entries_frame,
                text=(row.class_desc or "")[:40], anchor="w",
            ).grid(row=row_i, column=2, sticky="ew", padx=4, pady=2)
            ctk.CTkLabel(
                self._entries_frame,
                text=row.status, width=180, anchor="w",
                text_color=self._status_color(row.status),
            ).grid(row=row_i, column=3, sticky="w", padx=4, pady=2)

        # Show/hide recalculate notice
        if self._needs_recalc:
            self._recalc_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 4))
        else:
            self._recalc_frame.grid_remove()

    def _status_color(self, status: str) -> tuple:
        if "Benched" in status:
            return ("green4", "lightgreen")
        if "LATE" in status and "Benched" not in status:
            return ("orange3", "orange")
        if status in ("Has result", "NB", "Special winner"):
            return ("red4", "tomato")
        return ("gray40", "gray60")

    def _select_all_unbenched(self):
        for row in self._entry_rows:
            if row.auto_num is None and row.blocked_reason is None:
                self._entry_vars[(row.source_auto_num, row.is_late)].set(True)

    def _clear_selection(self):
        for var in self._entry_vars.values():
            var.set(False)

    def _bench_selected(self):
        show_keys = [k[0] for k, v in self._entry_vars.items() if v.get() and not k[1]]
        late_keys = [k[0] for k, v in self._entry_vars.items() if v.get() and k[1]]
        if show_keys:
            bench_entries(show_keys)
        if late_keys:
            bench_late_entries(late_keys)
        self._after_entry_change()

    def _unbench_selected(self):
        show_keys = [k[0] for k, v in self._entry_vars.items() if v.get() and not k[1]]
        late_keys = [k[0] for k, v in self._entry_vars.items() if v.get() and k[1]]
        if show_keys:
            unbench_entries(show_keys)
        if late_keys:
            unbench_late_entries(late_keys)
        self._after_entry_change()

    def _open_add_entry(self):
        if self._selected is None:
            return
        from views._entry_dialog import EntryDialog
        dlg = EntryDialog(self, exh_no=self._selected.exh_no)
        self.wait_window(dlg)
        self._after_entry_change()

    def _open_add_late_entry(self):
        if self._selected is None:
            return
        from views._late_entry_dialog import LateEntryDialog
        dlg = LateEntryDialog(
            self,
            exh_no=self._selected.exh_no,
            name=self._selected.name,
        )
        self.wait_window(dlg)
        self._after_entry_change()

    def _after_entry_change(self):
        calc_result = auto_calculate_if_safe()
        self._needs_recalc = calc_result == "warning"
        self._refresh_left()
        if self._selected:
            updated = next(
                (p for p in self._participants if p.exh_no == self._selected.exh_no),
                self._selected,
            )
            self._select_participant(updated)

    def _on_recalculate(self):
        from tkinter import messagebox
        ok = messagebox.askyesno(
            "Recalculate",
            "This will reassign bench numbers for all unbenched entries.\nContinue?",
            parent=self,
        )
        if ok:
            from services.calculate_service import calculate_entries
            calculate_entries()
            self._needs_recalc = False
            self._after_entry_change()
```

- [ ] **Step 4: Run smoke test**

```
pytest tests/test_show_participants_view_imports.py -v
```

Expected: `PASSED`

- [ ] **Step 5: Run full suite**

```
pytest tests/ -v --tb=short
```

- [ ] **Step 6: Commit**

```bash
git add views/show_participants_view.py tests/test_show_participants_view_imports.py
git commit -m "feat: add ShowParticipantsView"
```

---

## Task 8: Update navigation — wire in new view, remove old pages

Remove Entries, Check-in, and Late Entries from the nav. Add Show Participants. Delete the three old view files and their associated test.

**Files:**
- Modify: `views/main_window.py`
- Delete: `views/entries_view.py`
- Delete: `views/checkin_view.py`
- Delete: `views/late_entries_view.py`
- Delete: `tests/test_checkin_view_imports.py`

- [ ] **Step 1: Update `views/main_window.py` — NAV list**

Replace the `NAV` list:

```python
NAV = [
    ("Dashboard",         "dashboard"),
    ("Search",            "search"),
    ("Show Setup",        "setup"),
    ("Exhibitors",        "exhibitors"),
    ("Show Participants", "participants"),
    ("Results",           "results"),
    ("Special Winners",   "special"),
    ("Special Prizes",    "special_list"),
    ("Tickets",           "tickets"),
    ("Reports",           "reports"),
    ("Hall of Fame",      "hall_of_fame"),
    ("Class Glossary",    "notes"),
    ("Help",              "help"),
]
```

- [ ] **Step 2: Update `_bind_shortcuts` in `views/main_window.py`**

Replace the shortcuts block:

```python
    def _bind_shortcuts(self):
        for seq, key in [
            ("<Control-f>", "search"),        ("<Control-F>", "search"),
            ("<Control-h>", "help"),           ("<Control-H>", "help"),
            ("<Control-b>", "participants"),   ("<Control-B>", "participants"),
            ("<Control-e>", "participants"),   ("<Control-E>", "participants"),
            ("<Control-r>", "results"),        ("<Control-R>", "results"),
            ("<Control-t>", "tickets"),        ("<Control-T>", "tickets"),
            ("<Control-x>", "exhibitors"),     ("<Control-X>", "exhibitors"),
        ]:
            self.bind(seq, lambda e, k=key: self.navigate(k))
```

- [ ] **Step 3: Update `_make_view` in `views/main_window.py`**

Replace the import block and view_map inside `_make_view`:

```python
    def _make_view(self, key: str):
        from views.dashboard import DashboardView
        from views.setup_view import SetupView
        from views.exhibitors_view import ExhibitorsView
        from views.show_participants_view import ShowParticipantsView
        from views.results_view import ResultsView
        from views.special_view import SpecialView
        from views.special_list_view import SpecialListView
        from views.tickets_view import TicketsView
        from views.reports_view import ReportsView
        from views.hall_of_fame_view import HallOfFameView
        from views.notes_view import NotesView
        from views.reimport_view import ReImportView
        from views.reset_view import ResetView
        from views.help_view import HelpView
        from views.search_view import SearchView
        from views.archive_view import ArchiveView
        from views.sql_editor_view import SQLEditorView
        from views.welcome_view import WelcomeView

        view_map = {
            "welcome":       WelcomeView,
            "dashboard":     DashboardView,
            "search":        SearchView,
            "setup":         SetupView,
            "exhibitors":    ExhibitorsView,
            "participants":  ShowParticipantsView,
            "results":       ResultsView,
            "special":       SpecialView,
            "special_list":  SpecialListView,
            "tickets":       TicketsView,
            "reports":       ReportsView,
            "hall_of_fame":  HallOfFameView,
            "notes":         NotesView,
            "help":          HelpView,
            "import":        ReImportView,
            "reset":         ResetView,
            "sql_editor":    SQLEditorView,
        }
        cls = view_map.get(key)
        return cls(self._content) if cls else None
```

- [ ] **Step 4: Delete old view files**

```bash
rm views/entries_view.py
rm views/checkin_view.py
rm views/late_entries_view.py
```

- [ ] **Step 5: Delete old import test**

```bash
rm tests/test_checkin_view_imports.py
```

- [ ] **Step 6: Run full suite**

```
pytest tests/ -v --tb=short
```

Expected: all pass. Verify `test_show_participants_view_imports.py` passes.

- [ ] **Step 7: Commit**

```bash
git add views/main_window.py
git rm views/entries_view.py views/checkin_view.py views/late_entries_view.py
git rm tests/test_checkin_view_imports.py
git commit -m "feat: replace Entries + Check-in + Late Entries with Show Participants in nav"
```

---

## Self-Review Checklist

- **Spec coverage:**
  - [x] Nav changes (Entries/Check-in/Late Entries removed, Show Participants added) → Task 8
  - [x] Left panel: search, filter chips, participant list → Task 7
  - [x] Right panel: entries list with status badges, bench/unbench → Task 7
  - [x] Late entries as LATE badge inline → Task 7 (view), Task 4 (service)
  - [x] Auto-calculate: silent pre-show, warning once benching starts, blocked when results exist → Task 2
  - [x] ExhNo assignment inline flow → Task 7 (`_prompt_assign_exh_no`)
  - [x] ExhNo orphan validation banner → Task 7 (`_check_orphans`)
  - [x] Late entry benching → Tasks 1, 5
  - [x] Pre-filled dialogs → Task 6
  - [x] Recalculate confirmation dialog → Task 7 (`_on_recalculate`)
  - [x] Keyboard shortcuts Ctrl+B and Ctrl+E → Task 8

- **No placeholders:** All steps contain complete code.

- **Type consistency:** `ParticipantRow` and `ParticipantEntryRow` defined in Task 3, used identically in Tasks 4 and 7. `bench_late_entries` / `unbench_late_entries` defined in Task 5, imported in Task 7. `auto_calculate_if_safe` defined in Task 2, imported in Task 7.
