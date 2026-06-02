# Mobile Companion QR Scanner Design

## Goal

Add a lightweight mobile companion scanner for Results entry. A phone on the
same local/shared network should be able to scan cage-ticket QR codes and send
the payload to the desktop app, where Results continues to parse, display, and
save the result.

## Scope

Stage 3 adds a local companion receiver and phone web page. It does not move
result selection or saving to the phone. The desktop Results screen remains the
source of truth: the phone only submits ticket QR payloads, and the desktop
fills `Exhibit #`, focuses Result, and lets the operator choose/save the placing.

The companion should be optional. Manual entry, USB scanner entry, and desktop
webcam scanning must continue to work when the mobile receiver is stopped,
blocked by firewall settings, or unavailable on the phone.

## Recommended Approach

Use a desktop-hosted local HTTP receiver with a short pairing token.

The Results view should add a `Mobile Scan` action near `Scan QR`. Starting it
creates a small local server, generates a token, and opens a dialog showing a
pairing URL plus QR code. A phone scans that pairing QR to open the companion
page. The page submits ticket QR payloads back to the desktop with the token.

This keeps Benchabird offline-first and avoids cloud accounts or hosted
services. It also avoids changing the ticket QR format, because the phone sends
the same `AutoNum:<ticket> ExhNo:<exhibitor> Class:<code>` payload already used
by USB and webcam scanning.

## User Flow

1. User opens Results on the desktop.
2. User clicks `Mobile Scan`.
3. Desktop starts the local receiver and shows a pairing dialog.
4. User scans the pairing QR with the phone.
5. Phone opens the companion page.
6. Phone scans a cage-ticket QR or submits pasted/scanned payload text.
7. Desktop validates the token and parses the payload with
   `parse_scan_to_auto_num`.
8. Desktop fills `Exhibit #`, focuses Result, and shows the accepted scan.
9. User selects/saves the result on the desktop.
10. Closing the pairing dialog stops the receiver.

## Components

- `services/mobile_scan_service.py`: local receiver lifecycle, pairing token,
  URL generation, request handling, payload validation, and callback/queue for
  accepted scans.
- `views/_mobile_scanner_dialog.py`: CustomTkinter dialog showing pairing QR,
  URL, receiver status, last accepted scan, last error, and Stop/Close action.
- `views/results_view.py`: `Mobile Scan` button and scan callback into the
  existing Results parser path.
- Companion HTML: served by the receiver, containing a browser QR scanner when
  supported and a plain text fallback submit form.
- Packaging/docs: include any required pure-Python/static assets in
  `benchabird.spec`, `README.md`, and Help.

## Companion Page

The page should be deliberately small and self-contained:

- Show connection status and the desktop app name.
- Try to start a camera scanner using browser APIs.
- If camera access fails or is unsupported, show a clear message.
- Always provide a text field and Submit button for pasted/scanned payloads.
- POST submitted payloads to the desktop receiver with the pairing token.
- Show accepted/error responses from the desktop.

Important uncertainty: mobile browsers usually require a secure context for
camera access. `localhost` is normally trusted, but a phone visiting
`http://desktop-ip:<port>` may not be. Because Benchabird is offline-first, Stage
3 should ship the fallback submit form and document that live in-browser camera
scanning depends on the phone/browser/network combination.

## Security And Network Boundaries

- Bind only for local/shared network use.
- Generate a short random token for each receiver session.
- Require the token on all scan submissions.
- Do not expose database reads or writes through the companion.
- Do not allow result selection, save, clear, archive, import, or SQL actions
  from the phone.
- Stop the receiver when the dialog closes.
- Treat firewall/network failures as recoverable user-facing errors.

## Error Handling

- Receiver cannot start: show a clear dialog/status and leave existing scan
  methods available.
- Phone cannot reach desktop: companion page will not load; desktop dialog
  should show the URL and a note to check Wi-Fi/firewall.
- Bad or missing token: reject the request and do not update Results.
- Invalid ticket payload: return the parser error and show it in the desktop
  dialog/status.
- Browser camera unavailable: companion page keeps the manual payload submit
  field available.

## Testing

Automated tests should cover the service without requiring a real phone:

- Token generation and URL construction.
- Companion HTML includes scanner and fallback form hooks.
- Valid token plus valid payload invokes the accepted scan path.
- Missing/wrong token is rejected.
- Invalid payload reports a parser error and does not update Results.
- Receiver start/stop releases the server cleanly.

UI integration can be verified with import/compile checks, focused service
tests, and the full pytest suite. Manual verification should include loading the
pairing URL from another device on the same network when available.

