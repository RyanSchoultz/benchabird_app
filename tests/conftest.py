# tests/conftest.py
import pytest
from peewee import SqliteDatabase
from models import ALL_MODELS

@pytest.fixture(autouse=True)
def test_db():
    db = SqliteDatabase(':memory:')
    with db.bind_ctx(ALL_MODELS):
        db.create_tables(ALL_MODELS)
        yield db
        db.drop_tables(ALL_MODELS)
