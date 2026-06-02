import customtkinter as ctk

from services.judge_mode_service import (
    JudgeModeError,
    resolve_judge_entry,
    save_judge_result,
    toggle_judge_not_benched,
)
from views._mobile_scanner_dialog import MobileScannerDialog
from views._webcam_scanner_dialog import WebcamScannerDialog

RESULT_OPTIONS = ["1st", "2nd", "3rd", "4th", "5th", "BOB", "R/U BOB", "Champion", "Reserve"]


class JudgeModeDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_changed=None):
        super().__init__(parent)
        self._on_changed = on_changed
        self._current_auto_num = None
        self._recent = []
        self.title("Judge Mode")
        self.geometry("760x540")
        self.minsize(620, 420)
        self._build()
        self._scan_entry.focus()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            self,
            text="Judge Mode",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))

        top = ctk.CTkFrame(self, fg_color=("gray88", "gray20"), corner_radius=8)
        top.grid(row=1, column=0, sticky="ew", padx=16, pady=8)

        ctk.CTkLabel(top, text="Class filter").pack(side="left", padx=(12, 4), pady=10)
        self._class_entry = ctk.CTkEntry(top, width=100, placeholder_text="optional")
        self._class_entry.pack(side="left", padx=4, pady=10)

        ctk.CTkLabel(top, text="Scan / Exhibit #").pack(side="left", padx=(16, 4), pady=10)
        self._scan_entry = ctk.CTkEntry(top, width=180)
        self._scan_entry.pack(side="left", padx=4, pady=10)
        self._scan_entry.bind("<Return>", lambda _e: self._resolve_scan())

        ctk.CTkButton(top, text="Accept", width=80, command=self._resolve_scan).pack(
            side="left", padx=8, pady=10
        )
        ctk.CTkButton(
            top,
            text="Scan QR",
            width=82,
            fg_color=("gray75", "gray35"),
            text_color=("gray10", "gray90"),
            command=self._open_webcam_scanner,
        ).pack(side="left", padx=4, pady=10)
        ctk.CTkButton(
            top,
            text="Mobile Scan",
            width=105,
            fg_color=("gray75", "gray35"),
            text_color=("gray10", "gray90"),
            command=self._open_mobile_scanner,
        ).pack(side="left", padx=4, pady=10)

        self._context = ctk.CTkLabel(
            self,
            text="Scan a ticket QR or type an exhibit number.",
            anchor="w",
            justify="left",
            font=ctk.CTkFont(size=13),
        )
        self._context.grid(row=2, column=0, sticky="ew", padx=16, pady=8)

        result_panel = ctk.CTkFrame(self, fg_color="transparent")
        result_panel.grid(row=3, column=0, sticky="nsew", padx=16, pady=8)

        for index, result in enumerate(RESULT_OPTIONS):
            ctk.CTkButton(
                result_panel,
                text=result,
                width=110,
                command=lambda value=result: self._save(value),
            ).grid(row=index // 3, column=index % 3, padx=5, pady=5)

        ctk.CTkButton(
            result_panel,
            text="Not Benched",
            width=110,
            fg_color=("gray75", "gray35"),
            text_color=("gray10", "gray90"),
            command=self._toggle_nb,
        ).grid(row=3, column=0, padx=5, pady=5)

        self._recent_label = ctk.CTkLabel(
            self,
            text="Recent: none",
            anchor="w",
            justify="left",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
        )
        self._recent_label.grid(row=4, column=0, sticky="ew", padx=16, pady=(4, 16))

    def _resolve_scan(self):
        try:
            ctx = resolve_judge_entry(
                self._scan_entry.get(),
                class_filter=self._class_entry.get(),
            )
        except JudgeModeError as exc:
            self._current_auto_num = None
            self._context.configure(text=str(exc))
            return "break"
        self._show_context(ctx)
        return "break"

    def _accept_payload(self, payload):
        self._scan_entry.delete(0, "end")
        self._scan_entry.insert(0, payload)
        self._resolve_scan()
        return self._current_auto_num is not None

    def _open_webcam_scanner(self):
        WebcamScannerDialog(self, self._accept_payload)

    def _open_mobile_scanner(self):
        MobileScannerDialog(self, self._accept_payload)

    def _show_context(self, ctx):
        self._current_auto_num = ctx.auto_num
        status = "NB" if ctx.not_benched else (ctx.result or "No result yet")
        self._context.configure(
            text=(
                f"Exhibit #{ctx.auto_num}  Class: {ctx.class_code or ''}\n"
                f"Exhibitor #{ctx.exh_no or ''}  {ctx.name or ''}\n"
                f"Current: {status}"
            )
        )

    def _save(self, result):
        if self._current_auto_num is None:
            self._context.configure(text="Scan an exhibit before saving a result.")
            return
        ctx = save_judge_result(self._current_auto_num, result)
        self._after_change(ctx, result)

    def _toggle_nb(self):
        if self._current_auto_num is None:
            self._context.configure(text="Scan an exhibit before marking Not Benched.")
            return
        ctx = toggle_judge_not_benched(self._current_auto_num)
        self._after_change(ctx, "NB" if ctx.not_benched else "NB removed")

    def _after_change(self, ctx, label):
        self._show_context(ctx)
        self._recent.insert(0, f"#{ctx.auto_num} {ctx.class_code or ''}: {label}")
        self._recent = self._recent[:6]
        self._recent_label.configure(text="Recent:\n" + "\n".join(self._recent))
        self._scan_entry.delete(0, "end")
        self._scan_entry.focus()
        if self._on_changed:
            self._on_changed()
