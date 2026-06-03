# models/exhibitor.py
from peewee import IntegerField, CharField, BooleanField
from models.database import BaseModel

class Exhibitor(BaseModel):
    exh_no = IntegerField(null=True, index=True)
    name = CharField(max_length=75, unique=True)
    address = CharField(max_length=100, null=True)
    suburb = CharField(max_length=50, null=True)
    town = CharField(max_length=50, null=True)
    zip_code = CharField(max_length=10, null=True)
    tel_home = CharField(max_length=50, null=True)
    tel_work = CharField(max_length=50, null=True)
    cell_no = CharField(max_length=50, null=True)
    fax_no = CharField(max_length=50, null=True)
    email = CharField(max_length=100, null=True)
    club = CharField(max_length=50, null=True)
    club1 = CharField(max_length=255, null=True)
    print_address = BooleanField(default=False)
    is_entrant = BooleanField(default=False)

    class Meta:
        table_name = 'exhibitor'
