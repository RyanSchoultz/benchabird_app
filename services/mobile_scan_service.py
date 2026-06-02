"""Local HTTPS receiver for mobile companion QR scanning.

Serves over HTTPS using a per-session self-signed certificate so that
Android/Chrome will allow camera access (getUserMedia is blocked on plain
HTTP LAN addresses).  Users will see a one-time "Your connection is not
private" warning and must tap Advanced → Proceed (or equivalent).
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import html
import ipaddress
import queue
import secrets
import socket
import ssl
import tempfile
import threading
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

from services.scan_parser_service import ScanParseError, parse_scan_to_auto_num


def _generate_self_signed_cert(ip: str) -> tuple[Path, Path]:
    """Generate a temporary self-signed cert for *ip* and return (cert_path, key_path)."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    import datetime

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "Benchabird Mobile"),
    ])
    san_list = [x509.DNSName("localhost")]
    try:
        san_list.append(x509.IPAddress(ipaddress.ip_address(ip)))
    except ValueError:
        pass

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1))
        .add_extension(x509.SubjectAlternativeName(san_list), critical=False)
        .sign(key, hashes.SHA256())
    )

    cert_bytes = cert.public_bytes(serialization.Encoding.PEM)
    key_bytes = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )

    tmp_dir = Path(tempfile.mkdtemp(prefix="benchabird_ssl_"))
    cert_path = tmp_dir / "cert.pem"
    key_path = tmp_dir / "key.pem"
    try:
        cert_path.write_bytes(cert_bytes)
        key_path.write_bytes(key_bytes)
    except OSError:
        try:
            tmp_dir.rmdir()
        except OSError:
            pass
        raise
    return cert_path, key_path


class MobileScanError(RuntimeError):
    """Raised when the mobile scanner receiver cannot run."""


@dataclass(frozen=True)
class MobileScanEvent:
    payload: str
    exhibit_no: int
    result: str | None = None


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
  <title>Benchabird Mobile Companion</title>
  <style>
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f3f4f6;
      color: #1f2937;
      padding-bottom: 40px;
    }}
    main {{
      max-width: 500px;
      margin: 0 auto;
      padding: 16px;
    }}
    h1 {{
      font-size: 22px;
      margin: 0 0 4px;
      color: #1e3a8a;
    }}
    .badge-connected {{
      display: inline-block;
      font-size: 12px;
      background: #dcfce7;
      color: #15803d;
      padding: 4px 8px;
      border-radius: 9999px;
      font-weight: 600;
      margin-bottom: 12px;
    }}
    .panel {{
      background: white;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      padding: 16px;
      margin-top: 16px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    .panel-header {{
      font-size: 14px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #4b5563;
      margin-bottom: 12px;
      border-bottom: 1px solid #f3f4f6;
      padding-bottom: 8px;
    }}
    video {{
      width: 100%;
      max-height: 280px;
      background: #111827;
      border-radius: 8px;
      object-fit: cover;
    }}
    label {{
      display: block;
      font-size: 13px;
      font-weight: 600;
      color: #374151;
      margin-bottom: 6px;
    }}
    input[type="text"] {{
      box-sizing: border-box;
      width: 100%;
      min-height: 44px;
      padding: 10px 12px;
      border: 1px solid #d1d5db;
      border-radius: 8px;
      font-size: 16px;
      background: #f9fafb;
    }}
    input[type="text"]:focus {{
      outline: none;
      border-color: #2563eb;
      background: white;
      box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
    }}
    .details-grid {{
      display: grid;
      grid-template-columns: 100px 1fr;
      row-gap: 8px;
      font-size: 15px;
      background: #f9fafb;
      padding: 12px;
      border-radius: 8px;
      border: 1px solid #f3f4f6;
    }}
    .detail-val {{
      font-weight: 500;
    }}
    .awards-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      margin-bottom: 12px;
    }}
    .btn-award {{
      min-height: 44px;
      padding: 8px;
      border: 1px solid #d1d5db;
      border-radius: 8px;
      background: white;
      color: #374151;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .btn-award.selected {{
      background: #2563eb;
      color: white;
      border-color: #2563eb;
      box-shadow: 0 2px 4px rgba(37,99,235,0.2);
    }}
    .actions-row {{
      display: flex;
      gap: 8px;
      margin-bottom: 16px;
    }}
    .btn-outline-danger {{
      flex: 1;
      min-height: 40px;
      background: white;
      color: #dc2626;
      border: 1px solid #fca5a5;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
    }}
    .btn-outline-danger.selected {{
      background: #dc2626;
      color: white;
      border-color: #dc2626;
    }}
    .btn-outline-secondary {{
      flex: 1;
      min-height: 40px;
      background: white;
      color: #4b5563;
      border: 1px solid #d1d5db;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
    }}
    .btn-primary {{
      background: #2563eb;
      color: white;
      font-weight: 600;
      border: 0;
      border-radius: 8px;
      cursor: pointer;
      min-height: 44px;
      width: 100%;
    }}
    .btn-secondary {{
      background: #e5e7eb;
      color: #374151;
      font-weight: 600;
      border: 0;
      border-radius: 8px;
      cursor: pointer;
      min-height: 44px;
    }}
    #status {{
      margin-top: 8px;
      font-size: 13px;
      color: #6b7280;
      text-align: center;
    }}
    .alert-banner {{
      padding: 12px;
      border-radius: 8px;
      margin-top: 12px;
      font-size: 14px;
      font-weight: 500;
      text-align: center;
      animation: fadeIn 0.2s ease;
    }}
    .alert-success {{
      background: #dcfce7;
      color: #15803d;
      border: 1px solid #bbf7d0;
    }}
    .alert-error {{
      background: #fee2e2;
      color: #b91c1c;
      border: 1px solid #fecaca;
    }}
    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(-5px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
  </style>
</head>
<body>
  <main>
    <h1>Benchabird Mobile</h1>
    <div id="connection-status" class="badge-connected">✓ Connected to Desktop</div>
    
    <div id="alert-banner" class="alert-banner" style="display: none;"></div>

    <section class="panel" id="scanner-section">
      <div class="panel-header">Scan Cage Ticket</div>
      <video id="preview" playsinline muted></video>
      <div id="status">Starting camera scanner...</div>
    </section>

    <section class="panel" id="details-section" style="display: none;">
      <div class="panel-header">Exhibit Details</div>
      <div class="details-grid">
        <div><strong>Exhibit #</strong></div>
        <div id="detail-exhibit-no" class="detail-val">-</div>
        
        <div><strong>Class</strong></div>
        <div id="detail-class-code" class="detail-val">-</div>
        
        <div><strong>Exhibitor</strong></div>
        <div id="detail-name" class="detail-val">-</div>
        
        <div><strong>Current</strong></div>
        <div id="detail-current-result" class="detail-val">-</div>
      </div>

      <label style="margin-top: 16px;">Placing Award</label>
      <div class="awards-grid">
        <button type="button" class="btn-award" data-val="1st">1st</button>
        <button type="button" class="btn-award" data-val="2nd">2nd</button>
        <button type="button" class="btn-award" data-val="3rd">3rd</button>
        <button type="button" class="btn-award" data-val="4th">4th</button>
        <button type="button" class="btn-award" data-val="5th">5th</button>
        <button type="button" class="btn-award" data-val="BOB">BOB</button>
        <button type="button" class="btn-award" data-val="R/U BOB">R/U BOB</button>
        <button type="button" class="btn-award" data-val="Champion">Champ</button>
        <button type="button" class="btn-award" data-val="Reserve">Res</button>
      </div>

      <div class="actions-row">
        <button type="button" id="btn-toggle-nb" class="btn-outline-danger">Not Benched (NB)</button>
        <button type="button" id="btn-clear-placing" class="btn-outline-secondary">Clear Placing</button>
      </div>

      <div id="confirmation-zone" style="margin-top: 20px; padding: 12px; background: #eff6ff; border-radius: 6px; border: 1px dashed #bfdbfe;">
        <div style="font-size: 13px; color: #1e3a8a; margin-bottom: 8px;">
          Saving: <span id="confirm-summary" style="font-weight: bold;">(No award selected)</span>
        </div>
        <div style="display: flex; gap: 8px;">
          <button type="button" id="btn-save-confirm" class="btn-primary" style="flex: 1; margin-top: 0;">Save Result</button>
          <button type="button" id="btn-cancel" class="btn-secondary" style="flex: 0 0 80px; margin-top: 0; background: #e5e7eb; color: #374151;">Cancel</button>
        </div>
      </div>

      <div style="margin-top: 12px; display: flex; gap: 8px;">
        <button type="button" id="btn-send-raw" class="btn-secondary" style="width: 100%; font-size: 13px; min-height: 36px; margin-top: 0; background: #f3f4f6; color: #4b5563; border: 1px solid #d1d5db;">Send Raw Scan to Desktop</button>
      </div>
    </section>

    <section class="panel">
      <div class="panel-header">Manual Search / Entry</div>
      <form id="scan-form">
        <input type="hidden" name="token" value="{safe_token}">
        <label for="payload">Ticket QR or Exhibit #</label>
        <input id="payload" name="payload" type="text" autocomplete="off" placeholder="e.g. 42 or ticket QR code">
        <button type="submit" id="btn-lookup" style="width: 100%;">Lookup Exhibit</button>
      </form>
    </section>
  </main>
  <script>
    const statusEl = document.getElementById("status");
    const form = document.getElementById("scan-form");
    const payloadEl = document.getElementById("payload");
    const video = document.getElementById("preview");
    const alertBanner = document.getElementById("alert-banner");
    
    // Details El
    const detailsSection = document.getElementById("details-section");
    const detailExhibitNo = document.getElementById("detail-exhibit-no");
    const detailClassCode = document.getElementById("detail-class-code");
    const detailName = document.getElementById("detail-name");
    const detailCurrentResult = document.getElementById("detail-current-result");
    const confirmSummary = document.getElementById("confirm-summary");
    
    // Buttons
    const btnToggleNb = document.getElementById("btn-toggle-nb");
    const btnClearPlacing = document.getElementById("btn-clear-placing");
    const btnSaveConfirm = document.getElementById("btn-save-confirm");
    const btnCancel = document.getElementById("btn-cancel");
    const btnSendRaw = document.getElementById("btn-send-raw");
    
    let lastPayload = "";
    let detector = null;
    let isScanning = true;
    
    // State of current entry being edited
    let currentPayload = "";
    let currentExhibitNo = null;
    let selectedPlacing = "";
    let isNotBenched = false;
    
    function showAlert(message, type) {{
      alertBanner.textContent = message;
      alertBanner.className = "alert-banner alert-" + type;
      alertBanner.style.display = "block";
    }}
    
    function hideAlert() {{
      alertBanner.style.display = "none";
    }}
    
    // Setup Placing award buttons
    document.querySelectorAll(".btn-award").forEach(btn => {{
      btn.addEventListener("click", () => {{
        // Deselect all
        document.querySelectorAll(".btn-award").forEach(b => b.classList.remove("selected"));
        btn.classList.add("selected");
        selectedPlacing = btn.getAttribute("data-val");
        
        // Deselect NB if selected
        isNotBenched = false;
        btnToggleNb.classList.remove("selected");
        
        updateConfirmSummary();
      }});
    }});
    
    btnToggleNb.addEventListener("click", () => {{
      isNotBenched = !isNotBenched;
      if (isNotBenched) {{
        btnToggleNb.classList.add("selected");
        // Deselect placing
        document.querySelectorAll(".btn-award").forEach(b => b.classList.remove("selected"));
        selectedPlacing = "";
      }} else {{
        btnToggleNb.classList.remove("selected");
      }}
      updateConfirmSummary();
    }});
    
    btnClearPlacing.addEventListener("click", () => {{
      document.querySelectorAll(".btn-award").forEach(b => b.classList.remove("selected"));
      selectedPlacing = "";
      isNotBenched = false;
      btnToggleNb.classList.remove("selected");
      updateConfirmSummary();
    }});
    
    function updateConfirmSummary() {{
      if (isNotBenched) {{
        confirmSummary.textContent = "Mark as Not Benched (NB)";
      }} else if (selectedPlacing) {{
        confirmSummary.textContent = selectedPlacing;
      }} else {{
        confirmSummary.textContent = "Clear Placing (None)";
      }}
    }}
    
    async function lookup(payload) {{
      hideAlert();
      try {{
        const response = await fetch("/lookup?token={safe_token}&payload=" + encodeURIComponent(payload));
        const data = await response.json();
        if (!response.ok || !data.success) {{
          throw new Error(data.error || "Lookup failed");
        }}
        
        // Show details panel
        currentPayload = payload;
        currentExhibitNo = data.exhibit_no;
        selectedPlacing = data.current_result || "";
        isNotBenched = data.not_benched || false;
        
        detailExhibitNo.textContent = "#" + data.exhibit_no;
        detailClassCode.textContent = data.class_code || "(None)";
        detailName.textContent = data.exhibitor_name || "(None)";
        
        let currText = "(None)";
        if (data.not_benched) currText = "Not Benched (NB)";
        else if (data.current_result) currText = data.current_result;
        detailCurrentResult.textContent = currText;
        
        // Set button states
        document.querySelectorAll(".btn-award").forEach(b => {{
          if (b.getAttribute("data-val") === selectedPlacing) {{
            b.classList.add("selected");
          }} else {{
            b.classList.remove("selected");
          }}
        }});
        
        if (isNotBenched) {{
          btnToggleNb.classList.add("selected");
        }} else {{
          btnToggleNb.classList.remove("selected");
        }}
        
        updateConfirmSummary();
        
        detailsSection.style.display = "block";
        isScanning = false;
        statusEl.textContent = "Judging Exhibit #" + currentExhibitNo;
      }} catch (error) {{
        showAlert(error.message, "error");
        isScanning = true;
        scanLoop();
      }}
    }}
    
    // Save confirmation handler
    btnSaveConfirm.addEventListener("click", async () => {{
      try {{
        btnSaveConfirm.disabled = true;
        btnSaveConfirm.textContent = "Saving...";
        
        const params = new URLSearchParams();
        params.append("token", "{safe_token}");
        params.append("payload", currentPayload);
        params.append("result", selectedPlacing);
        params.append("not_benched", isNotBenched ? "true" : "false");
        
        const response = await fetch("/save", {{
          method: "POST",
          headers: {{"Content-Type": "application/x-www-form-urlencoded"}},
          body: params
        }});
        const data = await response.json();
        if (!response.ok || !data.success) {{
          throw new Error(data.error || "Save failed");
        }}
        
        showAlert(data.message || "Saved successfully!", "success");
        setTimeout(hideAlert, 3000);
        
        // Reset details
        detailsSection.style.display = "none";
        payloadEl.value = "";
        isScanning = true;
        statusEl.textContent = "Looking for ticket QR code...";
        scanLoop();
      }} catch (error) {{
        showAlert(error.message, "error");
      }} finally {{
        btnSaveConfirm.disabled = false;
        btnSaveConfirm.textContent = "Save Result";
      }}
    }});
    
    // Send raw scan directly to desktop
    btnSendRaw.addEventListener("click", async () => {{
      try {{
        btnSendRaw.disabled = true;
        btnSendRaw.textContent = "Sending...";
        
        const params = new URLSearchParams();
        params.append("token", "{safe_token}");
        params.append("payload", currentPayload);
        
        const response = await fetch("/scan", {{
          method: "POST",
          headers: {{"Content-Type": "application/x-www-form-urlencoded"}},
          body: params
        }});
        const text = await response.text();
        if (!response.ok) {{
          throw new Error(text || "Send failed");
        }}
        
        showAlert("Sent scan to desktop!", "success");
        setTimeout(hideAlert, 3000);
        
        detailsSection.style.display = "none";
        payloadEl.value = "";
        isScanning = true;
        statusEl.textContent = "Looking for ticket QR code...";
        scanLoop();
      }} catch(error) {{
        showAlert(error.message, "error");
      }} finally {{
        btnSendRaw.disabled = false;
        btnSendRaw.textContent = "Send Raw Scan to Desktop";
      }}
    }});
    
    btnCancel.addEventListener("click", () => {{
      detailsSection.style.display = "none";
      payloadEl.value = "";
      isScanning = true;
      statusEl.textContent = "Looking for ticket QR code...";
      scanLoop();
    }});

    form.addEventListener("submit", async (event) => {{
      event.preventDefault();
      const val = payloadEl.value.trim();
      if (val) {{
        await lookup(val);
      }}
    }});

    async function scanLoop() {{
      if (!isScanning) return;
      if (!detector || video.readyState < 2) {{
        requestAnimationFrame(scanLoop);
        return;
      }}
      try {{
        const codes = await detector.detect(video);
        if (codes.length && codes[0].rawValue && codes[0].rawValue !== lastPayload) {{
          lastPayload = codes[0].rawValue;
          isScanning = false;
          await lookup(lastPayload);
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
        self._ssl_cert: Path | None = None
        self._ssl_key: Path | None = None
        self._scheme = "https"

    @property
    def is_running(self) -> bool:
        return self._server is not None

    @property
    def base_url(self) -> str:
        if self._server is None:
            raise MobileScanError("Mobile scanner receiver is not running.")
        port = self._server.server_address[1]
        return f"{self._scheme}://{self.display_host}:{port}"

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
        # Wrap with SSL so the browser allows camera access.
        try:
            self._ssl_cert, self._ssl_key = _generate_self_signed_cert(self.display_host)
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ctx.load_cert_chain(str(self._ssl_cert), str(self._ssl_key))
            self._server.socket = ctx.wrap_socket(
                self._server.socket, server_side=True
            )
            self._scheme = "https"
        except Exception as exc:
            # SSL unavailable — fall back to plain HTTP with a warning
            self._ssl_cert = self._ssl_key = None
            self._scheme = "http"
            self._errors.put(
                f"SSL unavailable ({exc}); camera will be blocked by the browser. "
                "Use the text field instead."
            )
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
        self._scheme = "https"
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None and thread.is_alive():
            thread.join(timeout=2)
        # Clean up temporary cert files
        for p in (self._ssl_cert, self._ssl_key):
            if p and p.exists():
                try:
                    p.unlink()
                    p.parent.rmdir()
                except OSError:
                    pass
        self._ssl_cert = self._ssl_key = None

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
                if parsed.path == "/":
                    body = build_companion_html(receiver.token).encode("utf-8")
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return

                if parsed.path == "/lookup":
                    params = parse_qs(parsed.query)
                    token = params.get("token", [""])[0]
                    payload = params.get("payload", [""])[0]

                    if token != receiver.token:
                        self._send_json(HTTPStatus.FORBIDDEN, {"success": False, "error": "Invalid pairing token."})
                        return

                    try:
                        exhibit_no = parse_scan_to_auto_num(payload)
                    except ScanParseError as exc:
                        self._send_json(HTTPStatus.BAD_REQUEST, {"success": False, "error": str(exc)})
                        return

                    from models.show_entry import CalculatedEntry
                    from models.results import Result
                    from services.not_benched_service import is_not_benched

                    db = CalculatedEntry._meta.database
                    with db.connection_context():
                        entry = CalculatedEntry.get_or_none(CalculatedEntry.auto_num == exhibit_no)
                        if not entry:
                            self._send_json(HTTPStatus.NOT_FOUND, {
                                "success": False,
                                "error": f"Exhibit #{exhibit_no} not found. Ensure Entries are calculated."
                            })
                            return

                        result_row = Result.get_or_none(Result.exhibit_no == exhibit_no)
                        curr_res = result_row.result if result_row else None
                        nb = is_not_benched(exhibit_no)

                        self._send_json(HTTPStatus.OK, {
                            "success": True,
                            "exhibit_no": entry.auto_num,
                            "class_code": entry.class_code or "",
                            "exhibitor_name": entry.name or "",
                            "current_result": curr_res or "",
                            "not_benched": nb
                        })
                    return

                self._send_text(HTTPStatus.NOT_FOUND, "Not found")

            def do_POST(self):
                parsed = urlparse(self.path)
                if parsed.path == "/scan":
                    length = int(self.headers.get("Content-Length", "0"))
                    raw = self.rfile.read(length).decode("utf-8")
                    fields = parse_qs(raw, keep_blank_values=True)
                    status, message = receiver._handle_payload(
                        fields.get("token", [""])[0],
                        fields.get("payload", [""])[0],
                    )
                    self._send_text(status, message)
                    return

                if parsed.path == "/save":
                    length = int(self.headers.get("Content-Length", "0"))
                    raw = self.rfile.read(length).decode("utf-8")
                    fields = parse_qs(raw, keep_blank_values=True)
                    token = fields.get("token", [""])[0]
                    payload = fields.get("payload", [""])[0]
                    result = fields.get("result", [""])[0].strip()
                    not_benched_str = fields.get("not_benched", [""])[0].strip()

                    if token != receiver.token:
                        self._send_json(HTTPStatus.FORBIDDEN, {"success": False, "error": "Invalid pairing token."})
                        return

                    try:
                        exhibit_no = parse_scan_to_auto_num(payload)
                    except ScanParseError as exc:
                        self._send_json(HTTPStatus.BAD_REQUEST, {"success": False, "error": str(exc)})
                        return

                    from models.show_entry import CalculatedEntry
                    from services.results_service import record_result
                    from services.not_benched_service import mark_not_benched, unmark_not_benched

                    db = CalculatedEntry._meta.database
                    with db.connection_context():
                        if not_benched_str == "true":
                            mark_not_benched(exhibit_no)
                            record_result(exhibit_no, None)
                            res_val = "NB"
                        else:
                            unmark_not_benched(exhibit_no)
                            if result:
                                record_result(exhibit_no, result)
                                res_val = result
                            else:
                                record_result(exhibit_no, None)
                                res_val = "Cleared"

                        receiver._scans.put(MobileScanEvent(payload=payload, exhibit_no=exhibit_no, result=res_val))
                        self._send_json(HTTPStatus.OK, {"success": True, "message": f"Saved #{exhibit_no} as {res_val}."})
                    return

                self._send_text(HTTPStatus.NOT_FOUND, "Not found")

            def _send_text(self, status, message):
                body = str(message).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _send_json(self, status, data):
                import json
                body = json.dumps(data).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        return Handler
