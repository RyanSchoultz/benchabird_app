import pytest

from services.webcam_scan_service import (
    WebcamScanError,
    OpenCvWebcamScanner,
    decode_qr_payload,
)


class FakeDetector:
    def __init__(self, payload):
        self.payload = payload

    def detectAndDecode(self, frame):
        return self.payload, None, None


class FakeCapture:
    def __init__(self, opened=True, frame="frame"):
        self.opened = opened
        self.frame = frame
        self.released = False

    def isOpened(self):
        return self.opened

    def read(self):
        return True, self.frame

    def release(self):
        self.released = True


class FakeCv2:
    COLOR_BGR2RGB = 4

    def __init__(self, capture):
        self.capture = capture

    def VideoCapture(self, camera_index):
        return self.capture

    def QRCodeDetector(self):
        return FakeDetector("AutoNum:42 ExhNo:5 Class:SC01")

    def cvtColor(self, frame, color_code):
        return f"converted:{frame}:{color_code}"


def test_decode_qr_payload_returns_detected_text():
    assert decode_qr_payload("frame", FakeDetector("AutoNum:42")) == "AutoNum:42"


def test_decode_qr_payload_returns_none_when_blank():
    assert decode_qr_payload("frame", FakeDetector("")) is None


def test_scanner_read_returns_payload_and_rgb_frame():
    capture = FakeCapture()
    scanner = OpenCvWebcamScanner(cv2_module=FakeCv2(capture))

    payload, frame = scanner.read()

    assert payload == "AutoNum:42 ExhNo:5 Class:SC01"
    assert frame == "converted:frame:4"


def test_scanner_releases_capture():
    capture = FakeCapture()
    scanner = OpenCvWebcamScanner(cv2_module=FakeCv2(capture))

    scanner.release()

    assert capture.released is True


def test_scanner_raises_when_opencv_missing():
    with pytest.raises(WebcamScanError, match="opencv-python"):
        OpenCvWebcamScanner(cv2_module=None)


def test_scanner_raises_when_camera_unavailable():
    with pytest.raises(WebcamScanError, match="Could not open webcam"):
        OpenCvWebcamScanner(cv2_module=FakeCv2(FakeCapture(opened=False)))
