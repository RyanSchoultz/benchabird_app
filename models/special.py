# models/special.py
from peewee import IntegerField, CharField
from models.database import BaseModel

class SpecialList(BaseModel):
    bird_type = CharField(max_length=50, null=True)      # Access: TYPE
    show = CharField(max_length=50, null=True)
    special_nr = CharField(max_length=50, null=True, unique=True, index=True)
    description = CharField(max_length=250, null=True)
    cash = IntegerField(null=True)
    prize1 = CharField(max_length=250, null=True)
    cashby = CharField(max_length=250, null=True)
    special_for = CharField(max_length=50, null=True)
    afrbesk = CharField(max_length=50, null=True)
    kind = CharField(max_length=50, null=True)
    kind_sequence = CharField(max_length=50, null=True)

    class Meta:
        table_name = 'special_list'

class SpecialWinner(BaseModel):
    special_nr = CharField(max_length=50, null=True, unique=True, index=True)
    exhibit_no = IntegerField(null=True)
    result = CharField(max_length=50, null=True)

    class Meta:
        table_name = 'special_winner'
