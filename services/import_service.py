# services/import_service.py
"""
Imports all core tables from the Access MDB into SQLite via pyodbc.
Each _import_* function is idempotent (deletes then re-inserts).
"""
import pyodbc
from config import MDB_CONN_STR
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry, LateEntry
from models.class_def import ClassDef, Species, MainClass
from models.results import Result
from models.special import SpecialList, SpecialWinner
from models.reference import (
    ShowDetails, HallOfFame, TicketNumber, BrochureSequence, NotesBrochure
)


def import_from_mdb(progress=None) -> dict:
    """Import all tables. Returns {table_name: row_count}."""
    conn = pyodbc.connect(MDB_CONN_STR, autocommit=True)
    out = {}
    try:
        with Exhibitor._meta.database.atomic():
            out['exhibitors']      = _exhibitors(conn, progress)
            out['classes']         = _classes(conn, progress)
            out['species']         = _species(conn, progress)
            out['main_classes']    = _main_classes(conn, progress)
            out['show_entries']    = _show_entries(conn, progress)
            out['late_entries']    = _late_entries(conn, progress)
            out['special_lists']   = _special_lists(conn, progress)
            out['special_winners'] = _special_winners(conn, progress)
            out['show_details']    = _show_details(conn, progress)
            out['hall_of_fame']    = _hall_of_fame(conn, progress)
            out['ticket_numbers']  = _ticket_numbers(conn, progress)
            out['brochure_seq']    = _brochure_seq(conn, progress)
            out['notes_brochure']  = _notes_brochure(conn, progress)
    finally:
        conn.close()
    return out


def _fetch(conn, table: str) -> list:
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM [{table}]")
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _n(val):
    return None if val is None else val


def _bulk(model, data: list, chunk=200) -> int:
    model.delete().execute()
    for i in range(0, len(data), chunk):
        model.insert_many(data[i:i+chunk]).execute()
    return len(data)


def _notify(cb, msg):
    if cb:
        cb(msg)


def _exhibitors(conn, cb) -> int:
    _notify(cb, "Importing exhibitors (199)...")
    rows = _fetch(conn, "Exhibitors_T")
    return _bulk(Exhibitor, [{
        'exh_no':        _n(r.get('ExhNo')),
        'name':          r.get('Name') or '',
        'address':       _n(r.get('Address')),
        'suburb':        _n(r.get('Suburb')),
        'town':          _n(r.get('Town')),
        'zip_code':      _n(r.get('ZipCode')),
        'tel_home':      _n(r.get('TelH')),
        'tel_work':      _n(r.get('TelW')),
        'cell_no':       _n(r.get('CellNo')),
        'fax_no':        _n(r.get('FaxNo')),
        'email':         _n(r.get('E-mail')),
        'club':          _n(r.get('Club')),
        'club1':         _n(r.get('Club1')),
        'print_address': bool(r.get('Print Address', False)),
    } for r in rows])


def _classes(conn, cb) -> int:
    _notify(cb, "Importing class definitions (4807)...")
    rows = _fetch(conn, "Classes_T")
    return _bulk(ClassDef, [{
        'bird_type':  _n(r.get('TYPE')),
        'tabbr':      _n(r.get('TABBR')),
        'class_seq':  _n(r.get('ClASSSEQ')),
        'type_b':     _n(r.get('TYPEB')),
        'class_code': _n(r.get('CLASS')),
        'main_class': _n(r.get('MAINCLASS')),
        'colour':     _n(r.get('COLOUR')),
        'afrbesk':    _n(r.get('AFRBESK')),
    } for r in rows])


def _species(conn, cb) -> int:
    _notify(cb, "Importing species (36)...")
    rows = _fetch(conn, "Species_T")
    return _bulk(Species, [{
        'seq':        _n(r.get('Seq')),
        'bird_type':  _n(r.get('Type')),
        'main_tcode': _n(r.get('MainTCode')),
        'type2':      _n(r.get('Type2')),
        'type3':      _n(r.get('Type3')),
        'tcode':      _n(r.get('TCode')),
        'cat':        _n(r.get('Cat')),
        'scat1':      _n(r.get('SCat1')),
        'scat2':      _n(r.get('SCat2')),
    } for r in rows])


def _main_classes(conn, cb) -> int:
    _notify(cb, "Importing main classes...")
    rows = _fetch(conn, "Main_Classes_T")
    return _bulk(MainClass, [
        {'main_class': _n(r.get('MainClass')), 'mc_seq': _n(r.get('MCSeq'))}
        for r in rows
    ])


def _show_entries(conn, cb) -> int:
    _notify(cb, "Importing show entries (559)...")
    rows = _fetch(conn, "Show_Entries_T")
    data = [{
        'auto_num':   r['AutoNum'],
        'exh_no':     _n(r.get('ExhNo')),
        'class_code': _n(r.get('Class')),
    } for r in rows if r.get('AutoNum') is not None]
    return _bulk(ShowEntry, data)


def _late_entries(conn, cb) -> int:
    _notify(cb, "Importing late entries...")
    rows = _fetch(conn, "0040T Late_Entries_T")
    data = [{
        'auto_num':   r['AutoNum'],
        'exh_no':     _n(r.get('ExhNo')),
        'name':       _n(r.get('Name')),
        'class_code': _n(r.get('Class')),
    } for r in rows if r.get('AutoNum') is not None]
    return _bulk(LateEntry, data)


def _special_lists(conn, cb) -> int:
    _notify(cb, "Importing special prize lists (244)...")
    rows = _fetch(conn, "Special_Lists_T")
    return _bulk(SpecialList, [{
        'bird_type':     _n(r.get('TYPE')),
        'show':          _n(r.get('SHOW')),
        'special_nr':    _n(r.get('SPECIAL NR')),
        'description':   _n(r.get('DESCRIPTION')),
        'cash':          _n(r.get('CASH')),
        'prize1':        _n(r.get('PRIZE1')),
        'cashby':        _n(r.get('CASHBY')),
        'special_for':   _n(r.get('SPECIAL FOR')),
        'afrbesk':       _n(r.get('AFRBESK')),
        'kind':          _n(r.get('KIND')),
        'kind_sequence': _n(r.get('KIND SEQUENCE')),
    } for r in rows])


def _special_winners(conn, cb) -> int:
    _notify(cb, "Importing special winners (244)...")
    rows = _fetch(conn, "Special_Winners_T")
    return _bulk(SpecialWinner, [{
        'special_nr': _n(r.get('Special Number')),
        'exhibit_no': _n(r.get('Exhibit Number')),
        'result':     _n(r.get('Result')),
    } for r in rows])


def _show_details(conn, cb) -> int:
    _notify(cb, "Importing show details...")
    rows = _fetch(conn, "Show_and_Club_Details_T")
    ShowDetails.delete().execute()
    if rows:
        r = rows[0]
        ShowDetails.create(
            show_afr=      _n(r.get('SkouA')),
            show_eng=      _n(r.get('ShowE')),
            date_afr=      _n(r.get('DatumA')),
            date_eng=      _n(r.get('DateE')),
            club_afr=      _n(r.get('KlubA')),
            club_afr_full= _n(r.get('KlubAV')),
            club_eng=      _n(r.get('ClubE')),
            club_eng_full= _n(r.get('ClubEF')),
            association=   _n(r.get('Ass')),
        )
    return len(rows)


def _hall_of_fame(conn, cb) -> int:
    _notify(cb, "Importing Hall of Fame (25)...")
    rows = _fetch(conn, "Hall_of_Fame_T")
    return _bulk(HallOfFame, [{
        'type_abbr':  _n(r.get('Type Abbr')),
        'year':       _n(r.get('Year')),
        'name':       _n(r.get('Name')),
        'class_name': _n(r.get('Class')),
        'colour':     _n(r.get('Colour')),
        'judge':      _n(r.get('Judge')),
        'pta_record': _n(r.get('PTA Record')),
        'sa_record':  _n(r.get('SARecord')),
    } for r in rows])


def _ticket_numbers(conn, cb) -> int:
    _notify(cb, "Importing ticket numbers (25)...")
    rows = _fetch(conn, "0030T Ticket_Number(s)_T")
    return _bulk(TicketNumber, [
        {'ticket_number': _n(r.get('Ticket Number'))} for r in rows
    ])


def _brochure_seq(conn, cb) -> int:
    _notify(cb, "Importing brochure sequence...")
    rows = _fetch(conn, "Brochure_Sequence_T")
    return _bulk(BrochureSequence, [
        {'b_seq': _n(r.get('BSeq')), 's_des': _n(r.get('SDes'))} for r in rows
    ])


def _notes_brochure(conn, cb) -> int:
    _notify(cb, "Importing brochure notes...")
    rows = _fetch(conn, "Notes_to_Brochure_T")
    return _bulk(NotesBrochure, [
        {'type_abbr': _n(r.get('TypeAbbr')), 'notes': _n(r.get('Notes'))} for r in rows
    ])
