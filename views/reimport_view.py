# views/reimport_view.py
import threading
import customtkinter as ctk
from config import MDB_PATH
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry
from models.class_def import ClassDef


class ReImportView(ctk.CTkFrame):
    """
    Re-import all tables from the Access MDB at any time.
    Shows current record counts before and status after import.
    """
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Import / Re-Import Data",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(16, 4)
        )

        ctk.CTkLabel(self, text=f"Source: {MDB_PATH}",
                     font=ctk.CTkFont(size=11),
                     text_color=("gray40", "gray60"),
                     wraplength=700, justify="left").grid(
            row=1, column=0, sticky="w", padx=16, pady=(0, 16)
        )

        # Current counts
        counts_frame = ctk.CTkFrame(self, fg_color=("gray88", "gray20"), corner_radius=8)
        counts_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))
        counts_frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(counts_frame, text="Current database counts:",
                     font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=16, pady=(12, 4)
        )

        counts = [
            ("Exhibitors", Exhibitor.select().count()),
            ("Show Entries", ShowEntry.select().count()),
            ("Classes", ClassDef.select().count()),
        ]
        for col_i, (label, count) in enumerate(counts):
            ctk.CTkLabel(counts_frame, text=str(count),
                         font=ctk.CTkFont(size=28, weight="bold")).grid(
                row=1, column=col_i, padx=16, pady=(4, 2)
            )
            ctk.CTkLabel(counts_frame, text=label,
                         font=ctk.CTkFont(size=11),
                         text_color=("gray50", "gray55")).grid(
                row=2, column=col_i, padx=16, pady=(0, 12)
            )

        # Warning
        ctk.CTkLabel(self,
                     text="Re-importing will overwrite all table data. Results and calculated entries are preserved only if the MDB contains them.",
                     font=ctk.CTkFont(size=11),
                     text_color=("orange3", "orange"),
                     wraplength=700, justify="left").grid(
            row=3, column=0, sticky="w", padx=16, pady=(0, 12)
        )

        if not MDB_PATH.exists():
            ctk.CTkLabel(self, text=f"⚠ MDB file not found at: {MDB_PATH}",
                         text_color=("red4", "tomato")).grid(
                row=4, column=0, sticky="w", padx=16, pady=(0, 12)
            )

        self.grid_rowconfigure(5, weight=1)
        self._log = ctk.CTkTextbox(
            self, state="disabled", height=180,
            font=ctk.CTkFont(family="Courier New", size=11),
            fg_color=("gray95", "gray10"),
        )
        self._log.grid(row=5, column=0, sticky="nsew", padx=16, pady=(0, 8))

        self._bar = ctk.CTkProgressBar(self, mode="indeterminate")
        self._bar.grid(row=6, column=0, padx=80, sticky="ew", pady=(0, 8))
        self._bar.stop()
        self._bar.set(0)

        self._btn = ctk.CTkButton(
            self, text="Import from MDB", width=200, height=40,
            state="normal" if MDB_PATH.exists() else "disabled",
            command=self._start,
        )
        self._btn.grid(row=7, column=0, pady=(0, 16))

    def _log_append(self, msg: str):
        self._log.configure(state="normal")
        self._log.insert("end", msg + "\n")
        self._log.configure(state="disabled")
        self._log.see("end")

    def _start(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")
        self._btn.configure(state="disabled")
        self._bar.configure(mode="indeterminate")
        self._bar.start()
        self._log_append("Starting import...")
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            from services.import_service import import_from_mdb
            results = import_from_mdb(
                progress=lambda msg: self.after(0, lambda m=msg: self._log_append(m))
            )
            total = sum(results.values())
            self.after(0, lambda: self._on_done(results, total))
        except Exception as e:
            self.after(0, lambda: self._on_error(str(e)))

    def _on_done(self, results: dict, total: int):
        self._bar.stop()
        self._bar.configure(mode="determinate")
        self._bar.set(1.0)
        exhibitors = results.get('exhibitors', 0)
        entries = results.get('show_entries', 0)
        self._log_append(
            f"\nDone — {total} records imported. "
            f"Exhibitors: {exhibitors}, Entries: {entries}."
        )
        self._btn.configure(state="normal", text="Import Again")

    def _on_error(self, msg: str):
        self._bar.stop()
        self._bar.set(0)
        self._log_append(f"\nError: {msg}")
        self._btn.configure(state="normal")
