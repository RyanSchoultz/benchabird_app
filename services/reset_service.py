# services/reset_service.py
"""Clear all show-year data without touching reference tables."""
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry, CalculatedEntry, LateEntry
from models.results import Result, NotBenched
from models.special import SpecialWinner


def reset_show_data() -> dict:
    """
    Delete all entries, results, and special winners.
    Clears ExhNo from all exhibitors — ExhNo is per-show and must be reassigned each season.
    Returns dict of table -> row count affected.
    Class defs, hall of fame, and brochure notes are NOT affected.
    """
    with ShowEntry._meta.database.atomic():
        return {
            'entries':         ShowEntry.delete().execute(),
            'calculated':      CalculatedEntry.delete().execute(),
            'late_entries':    LateEntry.delete().execute(),
            'results':         Result.delete().execute(),
            'not_benched':     NotBenched.delete().execute(),
            'special_winners': SpecialWinner.delete().execute(),
            'exh_nos_cleared':  Exhibitor.update(exh_no=None).where(
                Exhibitor.exh_no.is_null(False)
            ).execute(),
            'entrants_cleared': Exhibitor.update(is_entrant=False).where(
                Exhibitor.is_entrant == True
            ).execute(),
        }
