# services/calculate_service.py
"""
0010 Calculate_Entries_M service.

Assigns sequential AutoNum values to all show entries, sorted by
exhibitor number (ExhNo) then class sequence (ClassDef.class_seq numeric).
Result stored in CalculatedEntry, replacing any previous run.
"""
from models.show_entry import ShowEntry, CalculatedEntry


def calculate_entries() -> int:
    """
    Rebuild CalculatedEntry from ShowEntry.
    Returns number of calculated entries created.
    """
    sql = """
        SELECT
            ROW_NUMBER() OVER (
                ORDER BY se.exh_no, CAST(cd.class_seq AS REAL)
            ) AS new_auto_num,
            se.exh_no,
            e.name,
            se.class_code
        FROM show_entry se
        LEFT JOIN exhibitor e ON se.exh_no = e.exh_no
        LEFT JOIN class_def cd ON se.class_code = cd.class_code
        ORDER BY se.exh_no, CAST(cd.class_seq AS REAL)
    """
    db = CalculatedEntry._meta.database
    cursor = db.execute_sql(sql)
    rows = [
        {
            'auto_num':   r[0],
            'exh_no':     r[1],
            'name':       r[2],
            'class_code': r[3],
        }
        for r in cursor.fetchall()
    ]
    with db.atomic():
        CalculatedEntry.delete().execute()
        for i in range(0, len(rows), 200):
            CalculatedEntry.insert_many(rows[i:i+200]).execute()
    return len(rows)


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
