# tests/test_special_service.py
import pytest
from models.special import SpecialList
from services.special_service import (
    get_all_special_lists, save_special_list, delete_special_list,
)


def test_save_special_list_creates_new(test_db):
    sp = save_special_list("S001", "Best in Show", "Trophy")
    assert sp.special_nr == "S001"
    assert SpecialList.select().count() == 1


def test_save_special_list_updates_existing(test_db):
    save_special_list("S001", "Best in Show", "Trophy")
    sp = save_special_list("S001", "Champion", "Medal")
    assert SpecialList.select().count() == 1
    assert sp.description == "Champion"


def test_save_special_list_with_cash(test_db):
    sp = save_special_list("S001", "Cash Prize", "R500", cash=500)
    assert sp.cash == 500


def test_delete_special_list(test_db):
    save_special_list("S001", "Best in Show", "Trophy")
    delete_special_list("S001")
    assert SpecialList.select().count() == 0


def test_delete_special_list_nonexistent_is_noop(test_db):
    delete_special_list("NOPE")
    assert SpecialList.select().count() == 0


def test_get_all_special_lists_returns_all(test_db):
    save_special_list("S002", "Second", "Medal")
    save_special_list("S001", "First", "Trophy")
    result = get_all_special_lists()
    assert len(result) == 2


def test_get_all_special_lists_empty(test_db):
    assert get_all_special_lists() == []
