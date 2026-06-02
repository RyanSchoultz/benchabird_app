import urllib.error
import urllib.parse
import urllib.request
import ssl

import pytest
from peewee import SqliteDatabase

from models import ALL_MODELS
from models.results import NotBenched, Result
from models.show_entry import CalculatedEntry
from services.mobile_scan_service import (
    MobileScanError,
    MobileScanReceiver,
    build_companion_html,
    choose_lan_ip,
)


_SSL_CONTEXT = ssl._create_unverified_context()


@pytest.fixture
def threaded_db():
    db = SqliteDatabase(
        "file:benchabird_mobile_scan_tests?mode=memory&cache=shared",
        uri=True,
        check_same_thread=False,
    )
    with db.bind_ctx(ALL_MODELS):
        db.connect()
        db.create_tables(ALL_MODELS)
        yield db
        db.drop_tables(ALL_MODELS)
        db.close()


def pop_meaningful_error(receiver):
    while True:
        error = receiver.pop_error()
        if error is None or not error.startswith("SSL unavailable"):
            return error


def post_scan(url, token, payload):
    data = urllib.parse.urlencode({
        "token": token,
        "payload": payload,
    }).encode("utf-8")
    request = urllib.request.Request(
        f"{url}/scan",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(request, timeout=2, context=_SSL_CONTEXT) as response:
        return response.status, response.read().decode("utf-8")


def post_save(url, token, payload, result="", not_benched=False):
    data = urllib.parse.urlencode({
        "token": token,
        "payload": payload,
        "result": result,
        "not_benched": "true" if not_benched else "false",
    }).encode("utf-8")
    request = urllib.request.Request(
        f"{url}/save",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(request, timeout=2, context=_SSL_CONTEXT) as response:
        return response.status, response.read().decode("utf-8")


def get_json(url):
    with urllib.request.urlopen(url, timeout=2, context=_SSL_CONTEXT) as response:
        import json

        return response.status, json.loads(response.read().decode("utf-8"))


def test_build_companion_html_contains_scanner_and_fallback_hooks():
    html = build_companion_html("abc123")

    assert "Benchabird Mobile" in html
    assert "BarcodeDetector" in html
    assert "getUserMedia" in html
    assert 'name="payload"' in html
    assert 'name="token" value="abc123"' in html
    assert "/lookup" in html
    assert "/save" in html


def test_choose_lan_ip_falls_back_to_loopback_when_socket_fails():
    class BrokenSocketModule:
        AF_INET = object()
        SOCK_DGRAM = object()

        def socket(self, *_args):
            raise OSError("network unavailable")

    assert choose_lan_ip(socket_module=BrokenSocketModule()) == "127.0.0.1"


def test_receiver_url_uses_host_port_and_token():
    receiver = MobileScanReceiver(host="127.0.0.1", port=0, token="abc123")
    receiver.start()
    try:
        assert (
            receiver.url.startswith("https://127.0.0.1:")
            or receiver.url.startswith("http://127.0.0.1:")
        )
        assert "token=abc123" in receiver.url
    finally:
        receiver.stop()


def test_receiver_serves_companion_html():
    receiver = MobileScanReceiver(host="127.0.0.1", port=0, token="abc123")
    receiver.start()
    try:
        with urllib.request.urlopen(receiver.url, timeout=2, context=_SSL_CONTEXT) as response:
            html = response.read().decode("utf-8")
        assert "Benchabird Mobile" in html
        assert 'name="token" value="abc123"' in html
    finally:
        receiver.stop()


def test_receiver_accepts_valid_token_and_valid_payload(test_db):
    receiver = MobileScanReceiver(host="127.0.0.1", port=0, token="abc123")
    receiver.start()
    try:
        status, body = post_scan(
            receiver.base_url,
            "abc123",
            "AutoNum:42 ExhNo:5 Class:SC01",
        )
        event = receiver.pop_scan()

        assert status == 200
        assert "Accepted #42" in body
        assert event is not None
        assert event.payload == "AutoNum:42 ExhNo:5 Class:SC01"
        assert event.exhibit_no == 42
    finally:
        receiver.stop()


def test_receiver_rejects_wrong_token(test_db):
    receiver = MobileScanReceiver(host="127.0.0.1", port=0, token="abc123")
    receiver.start()
    try:
        with pytest.raises(urllib.error.HTTPError) as excinfo:
            post_scan(receiver.base_url, "wrong", "AutoNum:42")

        assert excinfo.value.code == 403
        assert receiver.pop_scan() is None
        error = pop_meaningful_error(receiver)
        assert error is not None
        assert "Invalid pairing token" in error
    finally:
        receiver.stop()


def test_receiver_rejects_invalid_payload(test_db):
    receiver = MobileScanReceiver(host="127.0.0.1", port=0, token="abc123")
    receiver.start()
    try:
        with pytest.raises(urllib.error.HTTPError) as excinfo:
            post_scan(receiver.base_url, "abc123", "not a ticket")

        assert excinfo.value.code == 400
        assert receiver.pop_scan() is None
        error = pop_meaningful_error(receiver)
        assert error is not None
        assert "Scan did not include AutoNum" in error
    finally:
        receiver.stop()


def test_receiver_lookup_returns_calculated_entry_details(threaded_db):
    CalculatedEntry.create(auto_num=42, exh_no=5, name="Jane Bird", class_code="SC01")
    Result.create(exhibit_no=42, result="2nd")

    receiver = MobileScanReceiver(host="127.0.0.1", port=0, token="abc123")
    receiver.start()
    try:
        status, data = get_json(
            f"{receiver.base_url}/lookup?token=abc123&payload="
            + urllib.parse.quote("AutoNum:42 ExhNo:5 Class:SC01")
        )

        assert status == 200
        assert data == {
            "success": True,
            "exhibit_no": 42,
            "class_code": "SC01",
            "exhibitor_name": "Jane Bird",
            "current_result": "2nd",
            "not_benched": False,
        }
    finally:
        receiver.stop()


def test_receiver_lookup_rejects_unknown_exhibit(threaded_db):
    receiver = MobileScanReceiver(host="127.0.0.1", port=0, token="abc123")
    receiver.start()
    try:
        with pytest.raises(urllib.error.HTTPError) as excinfo:
            get_json(f"{receiver.base_url}/lookup?token=abc123&payload=AutoNum%3A42")

        assert excinfo.value.code == 404
    finally:
        receiver.stop()


def test_receiver_save_records_result_and_queues_saved_event(threaded_db):
    CalculatedEntry.create(auto_num=42, exh_no=5, name="Jane Bird", class_code="SC01")

    receiver = MobileScanReceiver(host="127.0.0.1", port=0, token="abc123")
    receiver.start()
    try:
        status, body = post_save(receiver.base_url, "abc123", "AutoNum:42", result="1st")
        event = receiver.pop_scan()

        assert status == 200
        assert "Saved #42 as 1st" in body
        assert Result.get(Result.exhibit_no == 42).result == "1st"
        assert event is not None
        assert event.payload == "AutoNum:42"
        assert event.exhibit_no == 42
        assert event.result == "1st"
    finally:
        receiver.stop()


def test_receiver_save_marks_not_benched_and_clears_result(threaded_db):
    CalculatedEntry.create(auto_num=42, exh_no=5, name="Jane Bird", class_code="SC01")
    Result.create(exhibit_no=42, result="1st")

    receiver = MobileScanReceiver(host="127.0.0.1", port=0, token="abc123")
    receiver.start()
    try:
        status, body = post_save(receiver.base_url, "abc123", "AutoNum:42", not_benched=True)
        event = receiver.pop_scan()

        assert status == 200
        assert "Saved #42 as NB" in body
        assert Result.get(Result.exhibit_no == 42).result is None
        assert NotBenched.get_or_none(NotBenched.exhibit_no == 42) is not None
        assert event is not None
        assert event.result == "NB"
    finally:
        receiver.stop()


def test_receiver_save_clears_result_and_not_benched(threaded_db):
    CalculatedEntry.create(auto_num=42, exh_no=5, name="Jane Bird", class_code="SC01")
    Result.create(exhibit_no=42, result="1st")
    NotBenched.create(exhibit_no=42, not_benched="NB", nb="NB")

    receiver = MobileScanReceiver(host="127.0.0.1", port=0, token="abc123")
    receiver.start()
    try:
        status, body = post_save(receiver.base_url, "abc123", "AutoNum:42")
        event = receiver.pop_scan()

        assert status == 200
        assert "Saved #42 as Cleared" in body
        assert Result.get(Result.exhibit_no == 42).result is None
        assert NotBenched.get_or_none(NotBenched.exhibit_no == 42) is None
        assert event is not None
        assert event.result == "Cleared"
    finally:
        receiver.stop()


def test_receiver_stop_is_idempotent():
    receiver = MobileScanReceiver(host="127.0.0.1", port=0, token="abc123")
    receiver.start()

    receiver.stop()
    receiver.stop()

    assert receiver.is_running is False


def test_receiver_raises_clear_error_when_start_fails():
    receiver = MobileScanReceiver(host="127.0.0.1", port=-1, token="abc123")

    with pytest.raises(MobileScanError, match="Could not start mobile scanner receiver"):
        receiver.start()


def test_mobile_scanner_dialog_imports():
    from views._mobile_scanner_dialog import MobileScannerDialog

    assert MobileScannerDialog.__name__ == "MobileScannerDialog"


def test_results_view_imports_with_mobile_scanner():
    from views.results_view import ResultsView

    assert ResultsView.__name__ == "ResultsView"
