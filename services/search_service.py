# services/search_service.py
"""Cross-entity search used by the global Search view."""
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry, CalculatedEntry
from models.results import Result
from models.special import SpecialList

_MAX = 8


def global_search(query: str) -> dict:
    """Search all entities. Returns dict of result lists (each capped at _MAX)."""
    q = query.strip()
    if not q:
        return _empty()

    is_num = q.isdigit()

    # Exhibitors
    exh_q = Exhibitor.select()
    if is_num:
        exh_q = exh_q.where(
            (Exhibitor.exh_no == int(q)) | Exhibitor.name.contains(q)
        )
    else:
        exh_q = exh_q.where(
            Exhibitor.name.contains(q)
            | Exhibitor.town.contains(q)
            | Exhibitor.email.contains(q)
            | Exhibitor.club.contains(q)
        )
    exh_total = exh_q.count()
    exhibitors = [
        {"id": e.id, "exh_no": e.exh_no, "name": e.name or "",
         "town": e.town or "", "email": e.email or ""}
        for e in exh_q.limit(_MAX)
    ]

    # ShowEntry (raw)
    se_q = ShowEntry.select()
    if is_num:
        se_q = se_q.where(
            (ShowEntry.exh_no == int(q)) | (ShowEntry.auto_num == int(q))
        )
    else:
        se_q = se_q.where(ShowEntry.class_code.contains(q))
    se_total = se_q.count()
    entries = [
        {"auto_num": e.auto_num, "exh_no": e.exh_no, "class_code": e.class_code or ""}
        for e in se_q.limit(_MAX)
    ]

    # CalculatedEntry
    ce_q = CalculatedEntry.select()
    if is_num:
        ce_q = ce_q.where(
            (CalculatedEntry.exh_no == int(q)) | (CalculatedEntry.auto_num == int(q))
        )
    else:
        ce_q = ce_q.where(
            CalculatedEntry.class_code.contains(q) | CalculatedEntry.name.contains(q)
        )
    ce_total = ce_q.count()
    calc_entries = [
        {"auto_num": e.auto_num, "exh_no": e.exh_no,
         "name": e.name or "", "class_code": e.class_code or ""}
        for e in ce_q.limit(_MAX)
    ]

    # Results
    res_q = Result.select().where(Result.result.is_null(False))
    if is_num:
        res_q = res_q.where(Result.exhibit_no == int(q))
    else:
        res_q = res_q.where(Result.result.contains(q))
    res_total = res_q.count()
    results = [
        {"exhibit_no": r.exhibit_no, "result": r.result or ""}
        for r in res_q.limit(_MAX)
    ]

    # Special prize list
    sp_q = SpecialList.select().where(
        SpecialList.description.contains(q) | SpecialList.special_nr.contains(q)
    )
    sp_total = sp_q.count()
    specials = [
        {"special_nr": s.special_nr or "", "description": s.description or "",
         "prize": s.prize1 or ""}
        for s in sp_q.limit(_MAX)
    ]

    return {
        "exhibitors": exhibitors, "exhibitors_total": exh_total,
        "entries": entries, "entries_total": se_total,
        "calc_entries": calc_entries, "calc_total": ce_total,
        "results": results, "results_total": res_total,
        "specials": specials, "specials_total": sp_total,
    }


def _empty():
    return {
        "exhibitors": [], "exhibitors_total": 0,
        "entries": [], "entries_total": 0,
        "calc_entries": [], "calc_total": 0,
        "results": [], "results_total": 0,
        "specials": [], "specials_total": 0,
    }
