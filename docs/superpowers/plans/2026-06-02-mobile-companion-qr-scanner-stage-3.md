# Mobile Companion QR Scanner Stage 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a lightweight phone companion scanner that sends ticket QR payloads from a local/shared network back to the desktop Results screen.

**Architecture:** Add a pure standard-library local HTTP receiver with a short pairing token and a self-contained companion HTML page. Results owns the UI action and consumes accepted payloads through the same parser path used by USB and webcam scanning. The phone never saves results or reads database data.

**Tech Stack:** Python, `http.server`, `threading`, `queue`, `secrets`, `qrcode`, CustomTkinter, pytest

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `tests/test_mobile_scan_service.py` | Create | Validate receiver token, HTML, request handling, payload validation, and lifecycle behavior |
| `services/mobile_scan_service.py` | Create | Provide mobile scan receiver, URL/token generation, companion HTML, local IP helper, and accepted/error queues |
| `views/_mobile_scanner_dialog.py` | Create | Show pairing QR/URL/status and poll receiver for accepted scans/errors |
| `views/results_view.py` | Modify | Add `Mobile Scan` button and scan callback into existing Results parser path |
| `views/help_view.py` | Modify | Document mobile companion scanner and fallback behavior |
| `README.md` | Modify | Document Stage 3 mobile scanning, network/firewall notes, and browser camera fallback |
| `benchabird.spec` | Inspect | Confirm no new bundled assets are needed; service uses standard library and generated HTML |

## Design Notes

- Use `ThreadingHTTPServer` with a request handler factory so tests can call handler logic through real local requests.
- Bind to `0.0.0.0` by default so another device on the network can reach the desktop.
- Generate a token per receiver session with `secrets.token_urlsafe(8)`.
- Companion URLs should use the best local LAN address when available, falling back to `127.0.0.1`.
- Serve one HTML page at `/`.
- Accept scan submissions at `/scan`.
- Require `token` and `payload` in `application/x-www-form-urlencoded` POST bodies.
- Validate submitted payload by calling `parse_scan_to_auto_num(payload)` inside the service, then queue the raw payload plus resolved exhibit number.
- Results should still call its existing `_resolve_scan_text(payload)` path so UI behavior remains identical to USB/webcam scans.
- The companion page should attempt `BarcodeDetector` when available and always keep a manual text field.

---

## Task 1: RED Tests For Mobile Scan Service

**Files:**
- Create: `tests/test_mobile_scan_service.py`

- [ ] **Step 1: Write service tests**

Create `tests/test_mobile_scan_service.py` with these tests:

```python
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
        status, body = post_scan(receiver.base_url, "abc123", "AutoNum:42 ExhNo:5 Class:SC01")
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
```

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_mobile_scan_service.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'services.mobile_scan_service'`.

- [ ] **Step 3: Commit RED tests**

Run:

```bash
git add tests/test_mobile_scan_service.py
git commit -m "test: add mobile scanner receiver coverage"
```

---

## Task 2: Mobile Scan Receiver Service

**Files:**
- Create: `services/mobile_scan_service.py`
- Test: `tests/test_mobile_scan_service.py`

- [ ] **Step 1: Implement service data types and helper functions**

Create `services/mobile_scan_service.py` with:

```python
"""Local HTTP receiver for mobile companion QR scanning."""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import html
import queue
import secrets
import socket
import threading
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

from services.scan_parser_service import ScanParseError, parse_scan_to_auto_num


class MobileScanError(RuntimeError):
    """Raised when the mobile scanner receiver cannot run."""


@dataclass(frozen=True)
class MobileScanEvent:
    payload: str
    exhibit_no: int


def choose_lan_ip(socket_module: Any = socket) -> str:
    try:
        sock = socket_module.socket(socket_module.AF_INET, socket_module.SOCK_DGRAM)
        try:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
        finally:
            sock.close()
    except OSError:
        return "127.0.0.1"
```

- [ ] **Step 2: Add self-contained companion HTML**

Append:

```python
def build_companion_html(token: str) -> str:
    safe_token = html.escape(token, quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Benchabird Mobile Scanner</title>
  <style>
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f6f7f8;
      color: #1f2933;
    }}
    main {{
      max-width: 680px;
      margin: 0 auto;
      padding: 20px;
    }}
    h1 {{
      font-size: 24px;
      margin: 0 0 8px;
    }}
    .panel {{
      background: white;
      border: 1px solid #d8dee4;
      border-radius: 8px;
      padding: 16px;
      margin-top: 16px;
    }}
    video {{
      width: 100%;
      max-height: 420px;
      background: #111827;
      border-radius: 8px;
    }}
    label {{
      display: block;
      font-weight: 650;
      margin-bottom: 6px;
    }}
    input[type="text"] {{
      box-sizing: border-box;
      width: 100%;
      min-height: 44px;
      padding: 10px;
      border: 1px solid #b7c0cc;
      border-radius: 6px;
      font-size: 16px;
    }}
    button {{
      min-height: 44px;
      margin-top: 10px;
      padding: 0 16px;
      border: 0;
      border-radius: 6px;
      background: #2563eb;
      color: white;
      font-size: 16px;
      font-weight: 650;
    }}
    #status {{
      margin-top: 12px;
      min-height: 24px;
      color: #4b5563;
    }}
  </style>
</head>
<body>
  <main>
    <h1>Benchabird Mobile Scanner</h1>
    <p>Scan a cage-ticket QR code. Results are still selected and saved on the desktop.</p>
    <section class="panel">
      <video id="preview" playsinline muted></video>
      <div id="status">Starting camera scanner...</div>
    </section>
    <section class="panel">
      <form id="scan-form" method="post" action="/scan">
        <input type="hidden" name="token" value="{safe_token}">
        <label for="payload">Ticket QR payload</label>
        <input id="payload" name="payload" type="text" autocomplete="off"
               placeholder="AutoNum:42 ExhNo:5 Class:SC01">
        <button type="submit">Send Scan</button>
      </form>
    </section>
  </main>
  <script>
    const statusEl = document.getElementById("status");
    const form = document.getElementById("scan-form");
    const payloadEl = document.getElementById("payload");
    const video = document.getElementById("preview");
    let lastPayload = "";
    let detector = null;

    async function submitPayload(payload) {{
      const body = new URLSearchParams(new FormData(form));
      body.set("payload", payload);
      const response = await fetch("/scan", {{
        method: "POST",
        headers: {{"Content-Type": "application/x-www-form-urlencoded"}},
        body
      }});
      const text = await response.text();
      statusEl.textContent = text;
      if (!response.ok) {{
        throw new Error(text);
      }}
      payloadEl.value = "";
    }}

    form.addEventListener("submit", async (event) => {{
      event.preventDefault();
      try {{
        await submitPayload(payloadEl.value.trim());
      }} catch (error) {{}}
    }});

    async function scanLoop() {{
      if (!detector || video.readyState < 2) {{
        requestAnimationFrame(scanLoop);
        return;
      }}
      try {{
        const codes = await detector.detect(video);
        if (codes.length && codes[0].rawValue && codes[0].rawValue !== lastPayload) {{
          lastPayload = codes[0].rawValue;
          await submitPayload(lastPayload);
        }}
      }} catch (error) {{
        statusEl.textContent = "Camera scanning is unavailable. Use the text field below.";
        return;
      }}
      requestAnimationFrame(scanLoop);
    }}

    async function startCamera() {{
      if (!("BarcodeDetector" in window) || !navigator.mediaDevices?.getUserMedia) {{
        statusEl.textContent = "Camera scanning is unavailable. Use the text field below.";
        return;
      }}
      detector = new BarcodeDetector({{formats: ["qr_code"]}});
      const stream = await navigator.mediaDevices.getUserMedia({{
        video: {{facingMode: "environment"}}
      }});
      video.srcObject = stream;
      await video.play();
      statusEl.textContent = "Looking for ticket QR code...";
      scanLoop();
    }}

    startCamera().catch(() => {{
      statusEl.textContent = "Camera access was blocked or unavailable. Use the text field below.";
    }});
  </script>
</body>
</html>"""
```

- [ ] **Step 3: Add receiver class and request handler**

Append:

```python
class MobileScanReceiver:
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 0,
        token: str | None = None,
        display_host: str | None = None,
    ):
        self.host = host
        self.port = port
        self.token = token or secrets.token_urlsafe(8)
        self.display_host = display_host or (
            choose_lan_ip() if host == "0.0.0.0" else host
        )
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._scans: queue.Queue[MobileScanEvent] = queue.Queue()
        self._errors: queue.Queue[str] = queue.Queue()

    @property
    def is_running(self) -> bool:
        return self._server is not None

    @property
    def base_url(self) -> str:
        if self._server is None:
            raise MobileScanError("Mobile scanner receiver is not running.")
        port = self._server.server_address[1]
        return f"http://{self.display_host}:{port}"

    @property
    def url(self) -> str:
        return f"{self.base_url}/?{urlencode({'token': self.token})}"

    def start(self) -> None:
        if self._server is not None:
            return
        handler = self._make_handler()
        try:
            self._server = ThreadingHTTPServer((self.host, self.port), handler)
        except OSError as exc:
            raise MobileScanError(
                f"Could not start mobile scanner receiver: {exc}"
            ) from exc
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="BenchabirdMobileScanReceiver",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        server = self._server
        thread = self._thread
        self._server = None
        self._thread = None
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None and thread.is_alive():
            thread.join(timeout=2)

    def pop_scan(self) -> MobileScanEvent | None:
        try:
            return self._scans.get_nowait()
        except queue.Empty:
            return None

    def pop_error(self) -> str | None:
        try:
            return self._errors.get_nowait()
        except queue.Empty:
            return None

    def _queue_error(self, message: str) -> None:
        self._errors.put(message)

    def _handle_payload(self, token: str, payload: str) -> tuple[int, str]:
        if token != self.token:
            message = "Invalid pairing token."
            self._queue_error(message)
            return HTTPStatus.FORBIDDEN, message
        payload = (payload or "").strip()
        try:
            exhibit_no = parse_scan_to_auto_num(payload)
        except ScanParseError as exc:
            message = str(exc)
            self._queue_error(message)
            return HTTPStatus.BAD_REQUEST, message
        self._scans.put(MobileScanEvent(payload=payload, exhibit_no=exhibit_no))
        return HTTPStatus.OK, f"Accepted #{exhibit_no}"

    def _make_handler(self):
        receiver = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, _format, *_args):
                return

            def do_GET(self):
                parsed = urlparse(self.path)
                if parsed.path != "/":
                    self._send_text(HTTPStatus.NOT_FOUND, "Not found")
                    return
                body = build_companion_html(receiver.token).encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                parsed = urlparse(self.path)
                if parsed.path != "/scan":
                    self._send_text(HTTPStatus.NOT_FOUND, "Not found")
                    return
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length).decode("utf-8")
                fields = parse_qs(raw, keep_blank_values=True)
                status, message = receiver._handle_payload(
                    fields.get("token", [""])[0],
                    fields.get("payload", [""])[0],
                )
                self._send_text(status, message)

            def _send_text(self, status, message):
                body = str(message).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        return Handler
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
python -m pytest tests/test_mobile_scan_service.py -v
```

Expected: all tests in `tests/test_mobile_scan_service.py` pass.

- [ ] **Step 5: Commit service**

Run:

```bash
git add services/mobile_scan_service.py tests/test_mobile_scan_service.py
git commit -m "feat: add mobile QR scan receiver"
```

---

## Task 3: Mobile Scanner Dialog

**Files:**
- Create: `views/_mobile_scanner_dialog.py`
- Modify: `views/results_view.py`
- Test: `tests/test_mobile_scan_service.py`

- [ ] **Step 1: Add compile/import smoke test**

Append to `tests/test_mobile_scan_service.py`:

```python
def test_mobile_scanner_dialog_imports():
    from views._mobile_scanner_dialog import MobileScannerDialog

    assert MobileScannerDialog.__name__ == "MobileScannerDialog"
```

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_mobile_scan_service.py::test_mobile_scanner_dialog_imports -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'views._mobile_scanner_dialog'`.

- [ ] **Step 3: Create dialog**

Create `views/_mobile_scanner_dialog.py`:

```python
import customtkinter as ctk
from PIL import Image, ImageTk
import qrcode

from services.mobile_scan_service import MobileScanError, MobileScanReceiver


class MobileScannerDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_scan):
        super().__init__(parent)
        self._on_scan = on_scan
        self._receiver = None
        self._after_id = None
        self._qr_image = None

        self.title("Mobile Scan")
        self.geometry("520x560")
        self.minsize(420, 460)
        self.protocol("WM_DELETE_WINDOW", self._close)
        self._build()
        self._start_receiver()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text="Scan this pairing QR with a phone on the same network.",
            font=ctk.CTkFont(size=13, weight="bold"),
            wraplength=440,
        ).grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))

        self._qr_label = ctk.CTkLabel(
            self,
            text="Starting receiver...",
            fg_color=("gray88", "gray16"),
            corner_radius=8,
            width=260,
            height=260,
        )
        self._qr_label.grid(row=1, column=0, padx=16, pady=8)

        self._url_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray35", "gray65"),
            wraplength=460,
        )
        self._url_label.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 8))

        self._status = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            wraplength=460,
        )
        self._status.grid(row=3, column=0, sticky="ew", padx=16, pady=8)

        self._last_scan = ctk.CTkLabel(
            self,
            text="No scans received yet.",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
            wraplength=460,
        )
        self._last_scan.grid(row=4, column=0, sticky="ew", padx=16, pady=8)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=5, column=0, sticky="ew", padx=16, pady=(8, 16))
        ctk.CTkButton(
            buttons,
            text="Close",
            width=90,
            fg_color=("gray75", "gray35"),
            text_color=("gray10", "gray90"),
            command=self._close,
        ).pack(side="right")

    def _start_receiver(self):
        self._receiver = MobileScanReceiver()
        try:
            self._receiver.start()
        except MobileScanError as exc:
            self._receiver = None
            self._status.configure(text=str(exc))
            self._qr_label.configure(text="Receiver unavailable")
            return

        url = self._receiver.url
        self._url_label.configure(
            text=f"{url}\nIf the phone cannot connect, check Wi-Fi and Windows Firewall."
        )
        self._status.configure(text="Waiting for phone scans...")
        self._show_qr(url)
        self._poll()

    def _show_qr(self, url):
        img = qrcode.make(url).convert("RGB")
        img = img.resize((260, 260), Image.Resampling.NEAREST)
        self._qr_image = ImageTk.PhotoImage(img)
        self._qr_label.configure(image=self._qr_image, text="")

    def _poll(self):
        if not self._receiver:
            return

        scan = self._receiver.pop_scan()
        if scan is not None:
            accepted = self._on_scan(scan.payload)
            if accepted:
                self._status.configure(text=f"Accepted scan #{scan.exhibit_no}.")
                self._last_scan.configure(text=f"Last scan: #{scan.exhibit_no}")
            else:
                self._status.configure(text="Scan received, but Results rejected it.")

        error = self._receiver.pop_error()
        if error:
            self._last_scan.configure(text=f"Last error: {error}")

        self._after_id = self.after(250, self._poll)

    def _stop_receiver(self):
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None
        if self._receiver:
            self._receiver.stop()
            self._receiver = None

    def _close(self):
        self._stop_receiver()
        self.destroy()
```

- [ ] **Step 4: Run dialog import test**

Run:

```bash
python -m pytest tests/test_mobile_scan_service.py::test_mobile_scanner_dialog_imports -v
```

Expected: PASS.

- [ ] **Step 5: Commit dialog**

Run:

```bash
git add views/_mobile_scanner_dialog.py tests/test_mobile_scan_service.py
git commit -m "feat: add mobile scanner pairing dialog"
```

---

## Task 4: Results UI Wiring

**Files:**
- Modify: `views/results_view.py`
- Test: `tests/test_mobile_scan_service.py`

- [ ] **Step 1: Add Results import smoke test**

Append to `tests/test_mobile_scan_service.py`:

```python
def test_results_view_imports_with_mobile_scanner():
    from views.results_view import ResultsView

    assert ResultsView.__name__ == "ResultsView"
```

- [ ] **Step 2: Verify RED or existing import state**

Run:

```bash
python -m pytest tests/test_mobile_scan_service.py::test_results_view_imports_with_mobile_scanner -v
```

Expected before wiring may PASS because `ResultsView` already imports. If it passes, continue; this smoke test still protects the new import after wiring.

- [ ] **Step 3: Import mobile dialog**

In `views/results_view.py`, add:

```python
from views._mobile_scanner_dialog import MobileScannerDialog
```

near the existing `WebcamScannerDialog` import.

- [ ] **Step 4: Add Mobile Scan button**

In `_build`, immediately after the `Scan QR` button, add:

```python
        ctk.CTkButton(form, text="Mobile Scan", width=105,
                      fg_color=("gray75", "gray35"), text_color=("gray10", "gray90"),
                      command=self._open_mobile_scanner).pack(side="left", padx=4, pady=8)
```

- [ ] **Step 5: Add mobile dialog callback**

In `ResultsView`, after `_accept_webcam_payload`, add:

```python
    def _open_mobile_scanner(self):
        MobileScannerDialog(self, self._accept_mobile_payload)

    def _accept_mobile_payload(self, payload):
        exhibit_no = self._resolve_scan_text(payload)
        if exhibit_no is None:
            return False
        self._set_resolved_exhibit(exhibit_no)
        return True
```

- [ ] **Step 6: Run compile and smoke tests**

Run:

```bash
python -m py_compile views/results_view.py views/_mobile_scanner_dialog.py services/mobile_scan_service.py
python -m pytest tests/test_mobile_scan_service.py tests/test_scan_parser_service.py -v
```

Expected: compile succeeds and focused tests pass.

- [ ] **Step 7: Commit Results wiring**

Run:

```bash
git add views/results_view.py tests/test_mobile_scan_service.py
git commit -m "feat: wire mobile scanner into results"
```

---

## Task 5: Docs, Help, And Packaging Check

**Files:**
- Modify: `README.md`
- Modify: `views/help_view.py`
- Inspect: `benchabird.spec`

- [ ] **Step 1: Update README Results scanner section**

In `README.md`, replace the planned mobile companion bullet under **QR / scanner entry** with:

```markdown
- Click `Mobile Scan` to start a local companion receiver. Scan the pairing QR
  with a phone on the same Wi-Fi/network, then scan ticket QRs from the phone
  companion page. Accepted scans fill `Exhibit #` on the desktop and move focus
  to Result
- Mobile live camera scanning depends on phone/browser security rules. If the
  browser blocks camera access over the local network, use the companion page's
  text field with a phone QR scanner app or pasted payload
- If the phone cannot connect, check that both devices are on the same network
  and that Windows Firewall allows the Benchabird app to accept local
  connections
```

- [ ] **Step 2: Update README project layout**

In `README.md`, add the mobile service and dialog entries:

```markdown
│   ├── mobile_scan_service.py   # Local HTTP receiver for mobile QR scanning
```

under `services/`, and:

```markdown
│   ├── _mobile_scanner_dialog.py # Pairing QR/status dialog for phone scanner
```

under `views/`.

- [ ] **Step 3: Update README tech stack**

Add a Tech Stack row:

```markdown
| Python stdlib HTTP server | bundled | Local mobile companion scan receiver |
```

- [ ] **Step 4: Update in-app Help QR Scanner Entry**

In `views/help_view.py`, extend the `"QR Scanner Entry"` text to include:

```python
            "Mobile companion scanner:\n"
            "1. Click Mobile Scan\n"
            "2. Scan the pairing QR with a phone on the same Wi-Fi/network\n"
            "3. Use the phone page to scan or submit a ticket QR payload\n"
            "4. When the desktop accepts the scan, choose the result and press Enter to save\n\n"
            "Phone browser camera support depends on browser security rules. "
            "If camera scanning is blocked, use the text field on the phone page "
            "with a phone QR scanner app or pasted payload.\n\n"
```

- [ ] **Step 5: Confirm packaging needs**

Inspect `benchabird.spec` and confirm no change is needed. Stage 3 uses the Python standard library plus `qrcode` and `PIL`, which are already present in `requirements.txt` and `hiddenimports`.

- [ ] **Step 6: Run focused verification**

Run:

```bash
python -m py_compile views/help_view.py views/results_view.py views/_mobile_scanner_dialog.py services/mobile_scan_service.py
python -m pytest tests/test_mobile_scan_service.py tests/test_scan_parser_service.py tests/test_webcam_scan_service.py -v
```

Expected: compile succeeds and focused tests pass.

- [ ] **Step 7: Commit docs**

Run:

```bash
git add README.md views/help_view.py
git commit -m "docs: document mobile companion QR scanning"
```

---

## Task 6: Final Verification

**Files:**
- No new code files unless verification exposes a defect

- [ ] **Step 1: Run full tests**

Run:

```bash
python -m pytest tests/ -v --tb=short
```

Expected: all tests pass.

- [ ] **Step 2: Generate starter DB**

Run:

```bash
python scripts/create_starter_db.py
```

Expected: command completes and regenerates `release/benchabird.db`.

- [ ] **Step 3: Run release build**

Run:

```bash
python -m PyInstaller benchabird.spec --clean
```

Expected: build succeeds and writes `dist/benchabird.exe`.

- [ ] **Step 4: Record build hash**

Run:

```bash
powershell -NoProfile -Command "Get-FileHash dist\\benchabird.exe -Algorithm SHA256"
```

Expected: prints a SHA256 hash for `dist\benchabird.exe`.

- [ ] **Step 5: Check working tree**

Run:

```bash
git status --short --branch
```

Expected: clean working tree, except generated release/build artifacts if the repo intentionally leaves them untracked or modified.

- [ ] **Step 6: Commit verification-related tracked changes**

If `scripts/create_starter_db.py` changed tracked starter DB content, commit it:

```bash
git add release/benchabird.db
git commit -m "chore: refresh starter database for mobile scanning release"
```

If no tracked files changed, do not create an empty commit.
