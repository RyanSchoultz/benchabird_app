# tests/test_address_tags_pdf.py
import pytest
from models.exhibitor import Exhibitor
from services.reports.address_tags import generate_address_tags


def test_generate_address_tags_empty(test_db):
    pdf = generate_address_tags()
    assert pdf[:4] == b'%PDF'


def test_generate_address_tags_with_exhibitors(test_db):
    for i in range(1, 6):
        Exhibitor.create(
            exh_no=i, name=f"Exhibitor {i}",
            address=f"{i} Main St", suburb="Gardens",
            town="Cape Town", zip_code="8001",
        )
    pdf = generate_address_tags()
    assert pdf[:4] == b'%PDF'
    assert len(pdf) > 2000


def test_generate_address_tags_multipage(test_db):
    for i in range(1, 35):
        Exhibitor.create(exh_no=i, name=f"Exhibitor {i}",
                         address=f"{i} Test Road", suburb="Suburb",
                         town="Town", zip_code="0000")
    pdf = generate_address_tags()
    assert pdf[:4] == b'%PDF'
