# models/reference.py
from peewee import IntegerField, CharField, TextField
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
    exhibit_number = IntegerField(null=True)
    exh_no_seq = CharField(max_length=10, null=True)

    class Meta:
        table_name = 'number_seq'
