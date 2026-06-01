# models/database.py
from peewee import SqliteDatabase, Model
from config import DB_PATH

database = SqliteDatabase(str(DB_PATH), pragmas={
    'journal_mode': 'wal',
    'cache_size': -64 * 1024,
    'foreign_keys': 1,
    'synchronous': 0,
})

class BaseModel(Model):
    class Meta:
        database = database
