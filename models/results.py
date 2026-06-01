# models/results.py
from peewee import IntegerField, CharField
from models.database import BaseModel

class Result(BaseModel):
    exhibit_no = IntegerField(null=True, unique=True, index=True)
    result = CharField(max_length=50, null=True)

    class Meta:
        table_name = 'result'

class NotBenched(BaseModel):
    exhibit_no = IntegerField(primary_key=True)
    not_benched = CharField(max_length=50, null=True)
    nb = CharField(max_length=50, null=True)

    class Meta:
        table_name = 'not_benched'
