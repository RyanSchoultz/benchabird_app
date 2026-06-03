# models/show_entry.py
from peewee import IntegerField, CharField
from models.database import BaseModel

class ShowEntry(BaseModel):
    auto_num = IntegerField(primary_key=True)
    exh_no = IntegerField(null=True, index=True)
    class_code = CharField(max_length=50, null=True, index=True)

    class Meta:
        table_name = 'show_entry'

class CalculatedEntry(BaseModel):
    """Output of the 0010 Calculate_Entries_M workflow."""
    auto_num = IntegerField(primary_key=True)
    source_entry_auto_num = IntegerField(null=True, index=True)
    source_late_entry_auto_num = IntegerField(null=True, index=True)
    exh_no = IntegerField(null=True, index=True)
    name = CharField(max_length=75, null=True)
    class_code = CharField(max_length=50, null=True)

    class Meta:
        table_name = 'calculated_entry'

class LateEntry(BaseModel):
    auto_num = IntegerField(primary_key=True)
    exh_no = IntegerField(null=True, index=True)
    name = CharField(max_length=75, null=True)
    class_code = CharField(max_length=50, null=True)

    class Meta:
        table_name = 'late_entry'
