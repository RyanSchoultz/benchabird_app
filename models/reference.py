# models/reference.py
from peewee import IntegerField, CharField, TextField, BlobField
from models.database import BaseModel

class ShowDetails(BaseModel):
    show_afr = CharField(max_length=50, null=True)
    show_eng = CharField(max_length=50, null=True)
    date_afr = CharField(max_length=50, null=True)
    date_eng = CharField(max_length=50, null=True)
    club_afr = CharField(max_length=50, null=True)
    club_afr_full = CharField(max_length=50, null=True)
    club_eng = CharField(max_length=50, null=True)
    club_eng_full = CharField(max_length=50, null=True)
    association = CharField(max_length=50, null=True)
    logo_path = CharField(max_length=500, null=True)
    logo_data = BlobField(null=True)  # raw image bytes stored in DB

    class Meta:
        table_name = 'show_details'

class HallOfFame(BaseModel):
    type_abbr = CharField(max_length=50, null=True)
    year = CharField(max_length=50, null=True)
    name = CharField(max_length=50, null=True)
    class_name = CharField(max_length=50, null=True)    # Access: Class
    colour = CharField(max_length=50, null=True)
    judge = CharField(max_length=50, null=True)
    pta_record = CharField(max_length=50, null=True)
    sa_record = CharField(max_length=100, null=True)

    class Meta:
        table_name = 'hall_of_fame'

class TicketNumber(BaseModel):
    ticket_number = IntegerField(null=True)

    class Meta:
        table_name = 'ticket_number'

class BrochureSequence(BaseModel):
    b_seq = CharField(max_length=50, null=True)
    s_des = CharField(max_length=50, null=True)

    class Meta:
        table_name = 'brochure_sequence'

class NotesBrochure(BaseModel):
    type_abbr = CharField(max_length=50, null=True)
    notes = TextField(null=True)

    class Meta:
        table_name = 'notes_brochure'

class NumberSeq(BaseModel):
    """Working table for exhibit number sequences (NumberSeq_T). Not an import target from MDB."""
    exhibit_number = IntegerField(null=True)
    exh_no_seq = CharField(max_length=10, null=True)

    class Meta:
        table_name = 'number_seq'
