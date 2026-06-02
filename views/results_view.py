# views/results_view.py
import customtkinter as ctk
from tkinter import messagebox
from repository.results_repo import ResultsRepo
from services.results_service import record_result, clear_results
from services.scan_parser_service import ScanParseError, parse_scan_to_auto_num
from services.not_benched_service import (
    mark_not_benched, unmark_not_benched, get_not_benched_set, is_not_benched,
)
from views._paginated_table import PaginatedTable
from views._webcam_scanner_dialog import WebcamScannerDialog
from views._mobile_scanner_dialog import MobileScannerDialog
from views._judge_mode_dialog import JudgeModeDialog

_repo = ResultsRepo()

RESULT_OPTIONS = ["1st", "2nd", "3rd", "4th", "5th", "BOB", "R/U BOB", "Champion", "Reserve"]


class ResultsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._all_results: list = []
        self._nb_set: set = set()
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, minsize=56)  # ensure form row never collapses
        self.grid_rowconfigure(3, weight=1)

        # ── Toolbar ──────────────────────────────────────────────────
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        ctk.CTkLabel(toolbar, text="Results",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(toolbar, text="Export", width=80,
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=self._export).pack(side="right", padx=4)
        ctk.CTkButton(toolbar, text="Clear All Results",
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=self._clear_all).pack(side="right", padx=(4, 4))
        ctk.CTkButton(toolbar, text="Judge Mode",
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=self._open_judge_mode).pack(side="right", padx=(4, 4))

        # ── Quick entry form ─────────────────────────────────────────
        form = ctk.CTkFrame(self, fg_color=("gray88", "gray20"), corner_radius=8)
        form.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 4))

        ctk.CTkLabel(form, text="Exhibit #:").pack(side="left", padx=(12, 4), pady=8)
        self._exh_entry = ctk.CTkEntry(form, width=80, placeholder_text="e.g. 42")
        self._exh_entry.pack(side="left", padx=4, pady=8)

        ctk.CTkLabel(form, text="Result:").pack(side="left", padx=(12, 4))
        self._result_combo = ctk.CTkComboBox(form, values=RESULT_OPTIONS, width=140)
        self._result_combo.set("1st")
        self._result_combo.pack(side="left", padx=4, pady=8)

        ctk.CTkButton(form, text="Save  ↵", width=100,
                      command=self._save_result).pack(side="left", padx=(8, 4), pady=8)
        ctk.CTkButton(form, text="Not Benched", width=110,
                      fg_color=("gray75", "gray35"), text_color=("gray10", "gray90"),
                      command=self._toggle_not_benched).pack(side="left", padx=4, pady=8)
        ctk.CTkButton(form, text="Scan QR", width=90,
                      fg_color=("gray75", "gray35"), text_color=("gray10", "gray90"),
                      command=self._open_webcam_scanner).pack(side="left", padx=4, pady=8)
        ctk.CTkButton(form, text="Mobile Scan", width=105,
                      fg_color=("gray75", "gray35"), text_color=("gray10", "gray90"),
                      command=self._open_mobile_scanner).pack(side="left", padx=4, pady=8)
        self._msg = ctk.CTkLabel(form, text="", font=ctk.CTkFont(size=11),
                                  text_color=("gray40", "gray60"))
        self._msg.pack(side="left", padx=12)

        # Keyboard shortcuts for rapid entry
        self._exh_entry.bind("<Return>", lambda e: self._accept_exhibit_entry())
        self._exh_entry.bind("<Tab>",    lambda e: self._accept_exhibit_entry())
        self._result_combo.bind("<Return>", lambda e: self._save_result())

        # ── Filter bar ───────────────────────────────────────────────
        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 2))
        self._filter_var = ctk.StringVar()
        self._filter_var.trace_add("write", lambda *_: self._apply_filter())
        ctk.CTkEntry(filter_bar, textvariable=self._filter_var,
                     placeholder_text="Filter by exhibit # or result…", width=260).pack(side="left")
        ctk.CTkButton(filter_bar, text="✕", width=28, height=28,
                      fg_color="transparent", text_color=("gray40", "gray60"),
                      command=lambda: self._filter_var.set("")).pack(side="left", padx=4)
        self._filter_status = ctk.CTkLabel(filter_bar, text="",
                                            font=ctk.CTkFont(size=11),
                                            text_color=("gray40", "gray60"))
        self._filter_status.pack(side="left", padx=8)

        # ── Results table ────────────────────────────────────────────
        self._table = PaginatedTable(
            self,
            headers=["Exhibit No", "Result", "NB"],
            col_weights=[1, 1, 1],
            selectable=False,
        )
        self._table.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self._reload_table()
        self._exh_entry.focus()

    def _reload_table(self):
        results = _repo.get_all_results()
        self._nb_set = get_not_benched_set()
        self._all_results = [(r.exhibit_no, [str(r.exhibit_no), r.result or ""]) for r in results]
        self._apply_filter()

    def _apply_filter(self):
        q = self._filter_var.get().strip().lower()
        data = [r for r in self._all_results if not q or any(q in c.lower() for c in r[1])]
        nb_set = self._nb_set

        def nb_render(exhibit_no, row_i, frame):
            bg = ("gray88", "gray18") if row_i % 2 == 0 else ("gray92", "gray16")
            ctk.CTkLabel(frame, text="NB" if exhibit_no in nb_set else "",
                         fg_color=bg, anchor="center", font=ctk.CTkFont(size=11),
                         text_color=("red4", "tomato")).grid(
                row=row_i, column=2, sticky="ew", padx=2, pady=1
            )

        self._table.load(data, row_render=nb_render)
        total = len(self._all_results)
        self._filter_status.configure(
            text=f"{len(data)} of {total}" if q else f"{total} results"
        )

    def _resolve_scan_text(self, raw):
        try:
            return parse_scan_to_auto_num(raw)
        except ScanParseError as exc:
            self._msg.configure(text=str(exc))
            return None

    def _set_resolved_exhibit(self, exhibit_no):
        if exhibit_no is None:
            return "break"
        self._exh_entry.delete(0, "end")
        self._exh_entry.insert(0, str(exhibit_no))
        self._msg.configure(text=f"Scan ready: #{exhibit_no}")
        self._result_combo.focus()
        return "break"

    def _parse_exhibit_entry(self):
        raw = self._exh_entry.get().strip()
        return self._resolve_scan_text(raw)

    def _accept_exhibit_entry(self):
        return self._set_resolved_exhibit(self._parse_exhibit_entry())

    def _open_webcam_scanner(self):
        WebcamScannerDialog(self, self._accept_webcam_payload)

    def _accept_webcam_payload(self, payload):
        exhibit_no = self._resolve_scan_text(payload)
        if exhibit_no is None:
            return False
        self._set_resolved_exhibit(exhibit_no)
        return True

    def _open_mobile_scanner(self):
        MobileScannerDialog(self, self._accept_mobile_payload)

    def _accept_mobile_payload(self, payload):
        exhibit_no = self._resolve_scan_text(payload)
        if exhibit_no is None:
            return False
        self._set_resolved_exhibit(exhibit_no)
        return True

    def _open_judge_mode(self):
        JudgeModeDialog(self, on_changed=self._reload_table)

    def _save_result(self):
        exhibit_no = self._parse_exhibit_entry()
        result_val = self._result_combo.get().strip()
        if exhibit_no is None:
            return
        raw = str(exhibit_no)
        record_result(int(raw), result_val)
        self._msg.configure(text=f"✓  #{raw} → {result_val}")
        self._exh_entry.delete(0, "end")
        self._exh_entry.focus()        # auto-focus back for rapid entry
        self._reload_table()

    def _toggle_not_benched(self):
        exhibit_no = self._parse_exhibit_entry()
        if exhibit_no is None:
            return
        raw = str(exhibit_no)
        exh = int(raw)
        if is_not_benched(exh):
            unmark_not_benched(exh)
            self._msg.configure(text=f"#{raw}: Not Benched removed.")
        else:
            mark_not_benched(exh)
            self._msg.configure(text=f"#{raw}: Marked Not Benched.")
        self._exh_entry.delete(0, "end")
        self._exh_entry.focus()
        self._reload_table()

    def _clear_all(self):
        if not messagebox.askyesno("Clear All Results",
                                   "This will remove all recorded results. Continue?"):
            return
        clear_results()
        self._msg.configure(text="All results cleared.")
        self._reload_table()

    def _export(self):
        from services.export_service import export_data
        nb_set = get_not_benched_set()
        results = _repo.get_all_results()
        rows = [
            [str(r.exhibit_no), r.result or "", "NB" if r.exhibit_no in nb_set else ""]
            for r in results
        ]
        export_data(rows, ["ExhibitNo", "Result", "NotBenched"], "results.csv")
