# models/__init__.py
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry, CalculatedEntry, LateEntry
from models.class_def import ClassDef, Species, MainClass
from models.class_glossary import ClassGlossary
from models.results import Result, NotBenched
from models.special import SpecialList, SpecialWinner
from models.reference import (
    ShowDetails, HallOfFame, TicketNumber,
    BrochureSequence, NotesBrochure, NumberSeq,
)

ALL_MODELS = [
    Exhibitor,
    ShowEntry, CalculatedEntry, LateEntry,
    ClassDef, Species, MainClass,
    ClassGlossary,
    Result, NotBenched,
    SpecialList, SpecialWinner,
    ShowDetails, HallOfFame, TicketNumber,
    BrochureSequence, NotesBrochure, NumberSeq,
]
