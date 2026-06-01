# views/results_view.py
import customtkinter as ctk
from repository.results_repo import ResultsRepo

_repo = ResultsRepo()


class ResultsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        ctk.CTkLabel(toolbar, text="Results", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(toolbar, text="Clear All Results",
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=self._clear).pack(side="right")

        table = ctk.CTkScrollableFrame(self, fg_color=("gray92", "gray16"))
        table.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        for col_i, hdr in enumerate(["Exhibit No", "Result"]):
            table.grid_columnconfigure(col_i, weight=1)
            ctk.CTkLabel(table, text=hdr, font=ctk.CTkFont(weight="bold"),
                         fg_color=("gray82", "gray22")).grid(row=0, column=col_i, sticky="ew", padx=2, pady=(0, 2))

        for row_i, r in enumerate(_repo.get_all_results(), start=1):
            bg = ("gray88", "gray18") if row_i % 2 == 0 else ("gray92", "gray16")
            for col_i, val in enumerate([str(r.exhibit_no), r.result or ""]):
                ctk.CTkLabel(table, text=val, fg_color=bg, anchor="w",
                             font=ctk.CTkFont(size=12)).grid(row=row_i, column=col_i, sticky="ew", padx=2, pady=1)

    def _clear(self):
        from services.results_service import clear_results
        clear_results()
        for w in self.winfo_children():
            w.destroy()
        self._build()
