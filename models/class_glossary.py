from peewee import CharField, IntegerField, TextField

from models.database import BaseModel


class ClassGlossary(BaseModel):
    class_code = CharField(max_length=50, null=True, index=True)
    bird_type = CharField(max_length=50, null=True, index=True)
    species_seq = IntegerField(null=True, index=True)
    species_heading = CharField(max_length=100, null=True, index=True)
    species_subheading = CharField(max_length=100, null=True)
    main_class = CharField(max_length=250, null=True)
    description = CharField(max_length=500, null=True)
    extra = CharField(max_length=250, null=True)
    class_seq = IntegerField(null=True, index=True)
    search_text = TextField(null=True)

    class Meta:
        table_name = "class_glossary"
