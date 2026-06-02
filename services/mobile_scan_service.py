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
        except (OSError, OverflowError) as exc:
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
