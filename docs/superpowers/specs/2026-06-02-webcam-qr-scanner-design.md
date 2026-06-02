# Webcam QR Scanner Design

## Goal

Add a desktop webcam scanner for Results entry. The scanner should read the QR code printed on cage tickets, resolve it through the existing scan parser, and fill the Results exhibit number without changing how results are stored.

## Scope

Stage 2 covers a local webcam button in the Results screen only. It does not include the mobile companion or network receiver; those remain Stage 3.

## Recommended Approach

Use OpenCV (`opencv-python`) for webcam capture and QR decoding. OpenCV includes `QRCodeDetector`, which avoids requiring a separate native barcode runtime. The scanner should be optional at runtime: if OpenCV is missing, the camera cannot open, or no QR is visible, the app should show a clear message and keep manual/USB entry available.

## User Flow

1. User opens Results.
2. User clicks `Scan QR`.
3. A small scanner window opens with a live camera preview.
4. When a QR payload is detected, the window closes.
5. The payload is parsed by `parse_scan_to_auto_num`.
6. The resolved exhibit number is inserted into `Exhibit #`, focus moves to Result, and the user chooses/saves the placing.

## Components

- `services/webcam_scan_service.py`: optional OpenCV backend, QR decode helper, and clear scanner errors.
- `views/results_view.py`: `Scan QR` button, scanner window, scan callback into the existing Results parser path.
- `requirements.txt` and `benchabird.spec`: add OpenCV for source and packaged builds.
- Docs: README and Help text should describe webcam scanning as optional and local.

## Error Handling

- Missing OpenCV: show "Webcam scanning requires opencv-python."
- Camera unavailable: show "Could not open webcam."
- Decode failures during preview are not errors; the scanner continues polling.
- Invalid QR payloads use the existing parser error messages.
- Closing the scanner window releases the camera.

## Testing

Automated tests should cover QR decode helper behavior and backend error handling without touching a real camera. UI behavior is verified by import/compile tests and the existing full test suite.
