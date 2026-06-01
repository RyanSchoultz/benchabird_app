# views/import_wizard.py
import threading
import customtkinter as ctk
from config import MDB_PATH, APP_NAME


class ImportWizard(ctk.CTkToplevel):
    """
    Modal dialog shown on first launch (when Exhibitor table is empty).
    Imports all tables from the Access MDB in a background thread.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.title(f"{APP_NAME} — Import Data")
        self.geometry("520x340")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text="Welcome to Benchabird Show Manager",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, pady=(24, 4), padx=30)

        ctk.CTkLabel(
            self,
            text=(
                "No data found in the local database.\n"
                "Import from the Access MDB file now?"
            ),
            justify="center",
        ).grid(row=1, column=0, pady=(0, 16))

        ctk.CTkLabel(
            self,
            text=f"Source: {MDB_PATH.name}",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
        ).grid(row=2, column=0, pady=(0, 16))

        self._log = ctk.CTkTextbox(
            self, state="disabled", height=100,
            font=ctk.CTkFont(family="Courier New", size=11),
            fg_color=("gray95", "gray10"),
        )
        self._log.grid(row=3, column=0, padx=20, sticky="ew", pady=(0, 8))

        self._bar = ctk.CTkProgressBar(self, mode="indeterminate")
        self._bar.grid(row=4, column=0, padx=40, sticky="ew", pady=(0, 16))
        self._bar.stop()

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=5, column=0, pady=(0, 24))

        self._import_btn = ctk.CTkButton(
            btn_frame, text="Import from MDB", width=160,
            command=self._start_import,
        )
        self._import_btn.pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame, text="Skip (start empty)", width=160,
            fg_color="transparent",
            border_width=1,
            text_color=("gray30", "gray70"),
            command=self.destroy,
        ).pack(side="left", padx=8)

    def _log_append(self, msg: str):
        self._log.configure(state="normal")
        self._log.insert("end", msg + "\n")
        self._log.configure(state="disabled")
        self._log.see("end")

    def _start_import(self):
        if not MDB_PATH.exists():
            self._log_append(f"Error: MDB not found at {MDB_PATH}")
            return
        self._import_btn.configure(state="disabled")
        self._bar.start()
        threading.Thread(target=self._do_import, daemon=True).start()

    def _do_import(self):
        try:
            from services.import_service import import_from_mdb
            results = import_from_mdb(
                progress=lambda msg: self.after(0, lambda m=msg: self._log_append(m))
            )
            total = sum(results.values())
            self.after(0, lambda: self._on_done(total))
        except Exception as e:
            self.after(0, lambda: self._on_error(str(e)))

    def _on_done(self, total: int):
        self._bar.stop()
        self._bar.configure(mode="determinate")
        self._bar.set(1.0)
        self._log_append(f"\nImport complete — {total} records loaded.")
        self._import_btn.configure(text="Done", state="normal", command=self.destroy)

    def _on_error(self, msg: str):
        self._bar.stop()
        self._log_append(f"\nError: {msg}")
        self._import_btn.configure(state="normal")
