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
