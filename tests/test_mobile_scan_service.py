import urllib.error
import urllib.parse
import urllib.request

import pytest

from services.mobile_scan_service import (
    MobileScanError,
    MobileScanReceiver,
    build_companion_html,
    choose_lan_ip,
)


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
    with urllib.request.urlopen(request, timeout=2) as response:
        return response.status, response.read().decode("utf-8")


def test_build_companion_html_contains_scanner_and_fallback_hooks():
    html = build_companion_html("abc123")

    assert "Benchabird Mobile Scanner" in html
    assert "BarcodeDetector" in html
    assert "getUserMedia" in html
    assert 'name="payload"' in html
    assert 'name="token" value="abc123"' in html


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
        assert receiver.url.startswith("http://127.0.0.1:")
        assert "token=abc123" in receiver.url
    finally:
        receiver.stop()


def test_receiver_serves_companion_html():
    receiver = MobileScanReceiver(host="127.0.0.1", port=0, token="abc123")
    receiver.start()
    try:
        with urllib.request.urlopen(receiver.url, timeout=2) as response:
            html = response.read().decode("utf-8")
        assert "Benchabird Mobile Scanner" in html
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
        error = receiver.pop_error()
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
        error = receiver.pop_error()
        assert error is not None
        assert "Scan did not include AutoNum" in error
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
