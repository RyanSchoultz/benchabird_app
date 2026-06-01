# models/class_def.py
from peewee import CharField
from models.database import BaseModel

class ClassDef(BaseModel):
    bird_type = CharField(max_length=50, null=True)     # Access: TYPE
    tabbr = CharField(max_length=50, null=True)          # Access: TABBR
    class_seq = CharField(max_length=50, null=True)      # Access: ClASSSEQ
    type_b = CharField(max_length=50, null=True)         # Access: TYPEB
    class_code = CharField(max_length=50, null=True,     # Access: CLASS
                           unique=True, index=True)
    main_class = CharField(max_length=250, null=True)    # Access: MAINCLASS
    colour = CharField(max_length=250, null=True)        # Access: COLOUR
    afrbesk = CharField(max_length=50, null=True)        # Access: AFRBESK

    class Meta:
        table_name = 'class_def'

class Species(BaseModel):
    seq = CharField(max_length=50, null=True)
    bird_type = CharField(max_length=50, null=True)     # Access: Type
    main_tcode = CharField(max_length=50, null=True)
    type2 = CharField(max_length=50, null=True)
    type3 = CharField(max_length=50, null=True)
    tcode = CharField(max_length=50, null=True)
    cat = CharField(max_length=50, null=True)
    scat1 = CharField(max_length=50, null=True)
    scat2 = CharField(max_length=50, null=True)

    class Meta:
        table_name = 'species'

class MainClass(BaseModel):
    main_class = CharField(max_length=50, null=True, unique=True)
    mc_seq = CharField(max_length=50, null=True)

    class Meta:
        table_name = 'main_class'
