"""Optional OpenCV-backed webcam QR scanning."""

from __future__ import annotations

from typing import Any


class WebcamScanError(RuntimeError):
    """Raised when webcam scanning cannot start or read frames."""


def decode_qr_payload(frame: Any, detector: Any) -> str | None:
    """Return decoded QR text from a frame, or None when no QR is visible."""
    payload, _points, _straight = detector.detectAndDecode(frame)
    payload = (payload or "").strip()
    return payload or None


class OpenCvWebcamScanner:
    """Small wrapper around OpenCV camera capture and QR detection."""

    def __init__(self, camera_index: int = 0, cv2_module: Any = ...):
        if cv2_module is ...:
            try:
                import cv2 as cv2_module
            except ImportError as exc:
                raise WebcamScanError(
                    "Webcam scanning requires opencv-python. Install it and try again."
                ) from exc
        if cv2_module is None:
            raise WebcamScanError(
                "Webcam scanning requires opencv-python. Install it and try again."
            )

        self._cv2 = cv2_module
        self._capture = cv2_module.VideoCapture(camera_index)
        if not self._capture.isOpened():
            self._capture.release()
            raise WebcamScanError("Could not open webcam.")
        self._detector = cv2_module.QRCodeDetector()

    def read(self) -> tuple[str | None, Any]:
        ok, frame = self._capture.read()
        if not ok:
            raise WebcamScanError("Could not read from webcam.")
        payload = decode_qr_payload(frame, self._detector)
        preview_frame = self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2RGB)
        return payload, preview_frame

    def release(self) -> None:
        self._capture.release()
