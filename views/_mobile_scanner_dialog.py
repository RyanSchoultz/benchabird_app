import customtkinter as ctk
from PIL import Image
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
        self.after(50, self.lift)

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
        self._status.configure(
            text="⚠ Browser will show a security warning (self-signed cert).\n"
                 "Tap 'Advanced' → 'Proceed' once — then the camera will work.",
            text_color=("orange3", "orange"),
        )
        self._show_qr(url)
        self._poll()

    def _show_qr(self, url):
        img = qrcode.make(url).convert("RGB")
        img = img.resize((260, 260), Image.Resampling.NEAREST)
        self._qr_image = ctk.CTkImage(light_image=img, dark_image=img, size=(260, 260))
        self._qr_label.configure(image=self._qr_image, text="")

    def _poll(self):
        if not self._receiver:
            return

        scan = self._receiver.pop_scan()
        if scan is not None:
            accepted = self._on_scan(scan.payload)
            if accepted:
                self._status.configure(
                    text=f"Accepted scan #{scan.exhibit_no}.",
                    text_color=("gray10", "gray90"),
                )
                self._last_scan.configure(text=f"Last scan: #{scan.exhibit_no}")
            else:
                self._status.configure(
                    text="Scan received, but Results rejected it.",
                    text_color=("gray10", "gray90"),
                )

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
