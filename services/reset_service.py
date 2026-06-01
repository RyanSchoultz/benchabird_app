# services/reset_service.py
"""Clear all show-year data without touching reference tables."""
from models.show_entry import ShowEntry, CalculatedEntry, LateEntry
from models.results import Result, NotBenched
from models.special import SpecialWinner


def reset_show_data() -> dict:
    """
    Delete all entries, results, and special winners.
    Returns dict of table -> row count deleted.
    Exhibitors, class defs, hall of fame, and brochure notes are NOT affected.
    """
    with ShowEntry._meta.database.atomic():
        return {
            'entries':         ShowEntry.delete().execute(),
            'calculated':      CalculatedEntry.delete().execute(),
            'late_entries':    LateEntry.delete().execute(),
            'results':         Result.delete().execute(),
            'not_benched':     NotBenched.delete().execute(),
            'special_winners': SpecialWinner.delete().execute(),
        }
