# views/late_entries_view.py
import customtkinter as ctk
from repository.entry_repo import EntryRepo

_repo = EntryRepo()


class LateEntriesView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self, text="Late Entries",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w", padx=16, pady=12)

        table = ctk.CTkScrollableFrame(self, fg_color=("gray92", "gray16"))
        table.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        for col_i, hdr in enumerate(["AutoNum", "ExhNo", "Name", "Class"]):
            table.grid_columnconfigure(col_i, weight=1)
            ctk.CTkLabel(table, text=hdr, font=ctk.CTkFont(weight="bold"),
                         fg_color=("gray82", "gray22")).grid(row=0, column=col_i, sticky="ew", padx=2, pady=(0, 2))

        for row_i, e in enumerate(_repo.get_late(), start=1):
            bg = ("gray88", "gray18") if row_i % 2 == 0 else ("gray92", "gray16")
            for col_i, val in enumerate([str(e.auto_num), str(e.exh_no or ""), e.name or "", e.class_code or ""]):
                ctk.CTkLabel(table, text=val, fg_color=bg, anchor="w",
                             font=ctk.CTkFont(size=12)).grid(row=row_i, column=col_i, sticky="ew", padx=2, pady=1)
