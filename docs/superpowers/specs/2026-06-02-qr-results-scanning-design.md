# QR Results Scanning Design

## Goal

Speed up results entry by allowing ticket QR/barcode scans to populate the Results screen exhibit number. The scanning foundation should support USB scanner input immediately, then grow to desktop webcam and mobile companion scanning.

## Stage 1: USB Scanner And QR Payload

USB barcode/QR scanners usually behave like keyboards. Stage 1 uses the existing Results exhibit number field as the scan target.

Ticket QR payloads should include the result key:

`AutoNum:<auto_num> ExhNo:<exh_no> Class:<class_code>`

This is a correction to the existing payload, which only contains exhibitor number and class. Results are stored by exhibit/ticket number, so `AutoNum` must be present for reliable scan-to-result entry.

The scan parser should accept:

- New QR payloads with `AutoNum`.
- Old QR payloads with only `ExhNo` and `Class`, resolving through `calculated_entry` when possible.
- Plain numeric scanner input such as `42`.

Results screen behavior:

- Scanning or typing a payload into Exhibit # and pressing Enter parses the scan.
- If an exhibit number is resolved, the field is replaced with that number and focus moves to Result.
- If the scan cannot be resolved, a clear status message is shown.

## Stage 2: Desktop Webcam Scanner

Add a `Scan QR` button on Results that opens a small scanner window. The window uses the desktop webcam to detect QR payloads and passes successful scans into the same parser used by Stage 1.

This stage may require a new dependency such as `opencv-python`. It should fail gracefully if the dependency or camera is unavailable.

## Stage 3: Mobile Companion Scanner

Prefer a lightweight HTML companion over Bluetooth for the first mobile version.

Proposed flow:

1. Desktop starts a local scan receiver with a short pairing token.
2. Desktop shows a pairing QR containing receiver URL plus token.
3. Phone opens a companion page.
4. Phone scans ticket QR codes and submits payloads to desktop over local/shared network.
5. Desktop uses the same parser and fills Results.

Important uncertainty: mobile browser camera access usually requires a secure context. A plain `http://desktop-ip` page may not allow camera access on all phones. The mobile companion stage should test browser security constraints before committing to a hosted/static implementation.

## Testing

Stage 1 tests should cover:

- New QR payload parses directly from `AutoNum`.
- Plain numeric input parses directly.
- Old QR payload resolves from `calculated_entry`.
- Old QR payload reports a clear error when no matching calculated entry exists.
- Ticket QR payload generation includes `AutoNum`, `ExhNo`, and `Class`.

Stages 2 and 3 need separate specs/plans before implementation because they involve camera permissions, packaging dependencies, and network pairing.
