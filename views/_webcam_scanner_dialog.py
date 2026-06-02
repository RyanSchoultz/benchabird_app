import customtkinter as ctk
from PIL import Image

from services.webcam_scan_service import OpenCvWebcamScanner, WebcamScanError


class WebcamScannerDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_scan):
        super().__init__(parent)
        self._on_scan = on_scan
        self._scanner = None
        self._after_id = None
        self._ctk_img = None

        self.title("Scan QR")
        self.geometry("560x500")
        self.minsize(420, 360)
        self.protocol("WM_DELETE_WINDOW", self._close)
        self._build()
        self._start()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self,
            text="Hold the cage-ticket QR code in front of the webcam.",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))

        self._preview = ctk.CTkLabel(
            self,
            text="Starting camera...",
            fg_color=("gray88", "gray16"),
            corner_radius=8,
        )
        self._preview.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 14))

        self._status = ctk.CTkLabel(
            bottom,
            text="Looking for QR code...",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
        )
        self._status.pack(side="left")

        ctk.CTkButton(
            bottom,
            text="Cancel",
            width=90,
            fg_color=("gray75", "gray35"),
            text_color=("gray10", "gray90"),
            command=self._close,
        ).pack(side="right")

    def _start(self):
        try:
            self._scanner = OpenCvWebcamScanner()
        except WebcamScanError as exc:
            self._status.configure(text=str(exc))
            self._preview.configure(text="Camera unavailable")
            return
        self._poll()

    def _poll(self):
        if not self._scanner:
            return
        try:
            payload, frame = self._scanner.read()
        except WebcamScanError as exc:
            self._status.configure(text=str(exc))
            self._close_camera()
            return

        self._show_frame(frame)
        if payload:
            accepted = self._on_scan(payload)
            if accepted:
                self._close()
                return
            self._status.configure(text="QR found, but it was not a valid ticket scan.")
        else:
            self._status.configure(text="Looking for QR code...")
        self._after_id = self.after(120, self._poll)

    def _show_frame(self, frame):
        img = Image.fromarray(frame)
        img.thumbnail((520, 360))
        self._ctk_img = ctk.CTkImage(
            light_image=img,
            dark_image=img,
            size=img.size,
        )
        self._preview.configure(image=self._ctk_img, text="")

    def _close_camera(self):
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None
        if self._scanner:
            self._scanner.release()
            self._scanner = None

    def _close(self):
        self._close_camera()
        self.destroy()
