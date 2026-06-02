# Webcam QR Scanner Stage 2 Implementation Plan

## Goal

Add a desktop `Scan QR` action in Results that opens a webcam preview, detects ticket QR payloads, and feeds the payload into the existing scan parser.

## Task 1: RED Tests

- Create `tests/test_webcam_scan_service.py`.
- Cover decode helper returning payload text from an injected detector.
- Cover decode helper returning `None` when no QR is found.
- Cover backend factory raising a friendly error when OpenCV is missing.
- Cover backend factory raising a friendly error when the camera cannot open.

Run:

`python -m pytest tests/test_webcam_scan_service.py -v`

Expected: import failure for `services.webcam_scan_service`.

## Task 2: Scanner Service

- Create `services/webcam_scan_service.py`.
- Add `WebcamScanError`.
- Add `decode_qr_payload(frame, detector)` with OpenCV-compatible detector injection.
- Add `OpenCvWebcamScanner` with `read()`, `release()`, and optional import behavior.

Run:

`python -m pytest tests/test_webcam_scan_service.py -v`

Expected: tests pass.

Commit:

`feat: add webcam QR scanner backend`

## Task 3: Results UI Integration

- Add `Scan QR` button beside the quick entry controls.
- Add a scanner dialog using `CTkToplevel`.
- Poll the backend on a short timer, update the preview when frames are available, and stop/release on close.
- On scan success, parse payload through the existing Results entry path, fill `Exhibit #`, and focus Result.

Run:

`python -m py_compile views/results_view.py services/webcam_scan_service.py`
`python -m pytest tests/test_scan_parser_service.py tests/test_webcam_scan_service.py -v`

Commit:

`feat: add webcam QR scanner to results`

## Task 4: Packaging And Docs

- Add `opencv-python` to `requirements.txt`.
- Add `cv2` to `benchabird.spec` hidden imports.
- Update README and Help text.

Run:

`python -m pytest tests/ -v --tb=short`

Commit:

`docs: document webcam QR scanning`
