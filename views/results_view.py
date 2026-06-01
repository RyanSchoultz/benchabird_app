# views/results_view.py
import customtkinter as ctk
from tkinter import messagebox
from repository.results_repo import ResultsRepo
from services.results_service import record_result, clear_results
from services.not_benched_service import (
    mark_not_benched, unmark_not_benched, get_not_benched_set, is_not_benched,
)
from views._paginated_table import PaginatedTable

_repo = ResultsRepo()

RESULT_OPTIONS = ["1st", "2nd", "3rd", "4th", "5th", "BOB", "R/U BOB", "Champion", "Reserve"]


class ResultsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        ctk.CTkLabel(toolbar, text="Results",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(toolbar, text="Clear All Results",
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=self._clear_all).pack(side="right", padx=(4, 0))

        form = ctk.CTkFrame(self, fg_color=("gray88", "gray20"), corner_radius=8)
        form.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))

        ctk.CTkLabel(form, text="Exhibit #:").pack(side="left", padx=(12, 4), pady=8)
        self._exh_entry = ctk.CTkEntry(form, width=80, placeholder_text="e.g. 42")
        self._exh_entry.pack(side="left", padx=4, pady=8)

        ctk.CTkLabel(form, text="Result:").pack(side="left", padx=(12, 4))
        self._result_combo = ctk.CTkComboBox(form, values=RESULT_OPTIONS, width=140)
        self._result_combo.set("1st")
        self._result_combo.pack(side="left", padx=4, pady=8)

        ctk.CTkButton(form, text="Save Result", width=110,
                      command=self._save_result).pack(side="left", padx=(8, 4), pady=8)
        ctk.CTkButton(form, text="Not Benched", width=110,
                      fg_color=("gray75", "gray35"), text_color=("gray10", "gray90"),
                      command=self._toggle_not_benched).pack(side="left", padx=4, pady=8)
        self._msg = ctk.CTkLabel(form, text="", font=ctk.CTkFont(size=11),
                                  text_color=("gray40", "gray60"))
        self._msg.pack(side="left", padx=12)

        self.grid_rowconfigure(2, weight=1)
        self._table = PaginatedTable(
            self,
            headers=["Exhibit No", "Result", "Not Benched"],
            col_weights=[1, 1, 1],
            selectable=False,
        )
        self._table.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self._reload_table()

    def _reload_table(self):
        results = _repo.get_all_results()
        nb_set = get_not_benched_set()
        data = [(r.exhibit_no, [str(r.exhibit_no), r.result or ""]) for r in results]

        def nb_render(exhibit_no, row_i, frame):
            bg = ("gray88", "gray18") if row_i % 2 == 0 else ("gray92", "gray16")
            ctk.CTkLabel(
                frame, text="NB" if exhibit_no in nb_set else "",
                fg_color=bg, anchor="center",
                font=ctk.CTkFont(size=11),
                text_color=("red4", "tomato"),
            ).grid(row=row_i, column=2, sticky="ew", padx=2, pady=1)

        self._table.load(data, row_render=nb_render)

    def _save_result(self):
        raw = self._exh_entry.get().strip()
        result_val = self._result_combo.get().strip()
        if not raw.isdigit():
            self._msg.configure(text="Enter a numeric exhibit number.")
            return
        record_result(int(raw), result_val)
        self._msg.configure(text=f"Saved: #{raw} → {result_val}")
        self._exh_entry.delete(0, "end")
        self._reload_table()

    def _toggle_not_benched(self):
        raw = self._exh_entry.get().strip()
        if not raw.isdigit():
            self._msg.configure(text="Enter a numeric exhibit number.")
            return
        exh = int(raw)
        if is_not_benched(exh):
            unmark_not_benched(exh)
            self._msg.configure(text=f"#{raw}: Not Benched removed.")
        else:
            mark_not_benched(exh)
            self._msg.configure(text=f"#{raw}: Marked Not Benched.")
        self._reload_table()

    def _clear_all(self):
        if not messagebox.askyesno("Clear All Results",
                                   "This will remove all recorded results. Continue?"):
            return
        clear_results()
        self._msg.configure(text="All results cleared.")
        self._reload_table()
