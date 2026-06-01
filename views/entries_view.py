# views/entries_view.py
import customtkinter as ctk
from controllers.entry_ctrl import get_all_entries, get_calculated, run_calculate

COLS_RAW = ["AutoNum", "ExhNo", "Class"]
COLS_CALC = ["#", "ExhNo", "Name", "Class"]


class EntriesView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._mode = ctk.StringVar(value="raw")
        self._build()
        self._load()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        ctk.CTkLabel(toolbar, text="Show Entries", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(toolbar, text="Run Calculate (0010)",
                      command=self._run_calculate).pack(side="right", padx=(4, 0))

        seg = ctk.CTkSegmentedButton(
            toolbar,
            values=["Show Entries", "Calculated"],
            command=lambda v: (self._mode.set("calc" if v == "Calculated" else "raw"), self._load()),
        )
        seg.set("Show Entries")
        seg.pack(side="right", padx=8)

        self._status = ctk.CTkLabel(toolbar, text="", font=ctk.CTkFont(size=11),
                                    text_color=("gray40", "gray60"))
        self._status.pack(side="left", padx=12)

        self._table = ctk.CTkScrollableFrame(self, fg_color=("gray92", "gray16"))
        self._table.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 16))

    def _load(self):
        for w in self._table.winfo_children():
            w.destroy()

        if self._mode.get() == "calc":
            rows = get_calculated()
            cols = COLS_CALC
            data = [[str(r.auto_num), str(r.exh_no or ""), r.name or "", r.class_code or ""] for r in rows]
        else:
            rows = get_all_entries()
            cols = COLS_RAW
            data = [[str(r.auto_num), str(r.exh_no or ""), r.class_code or ""] for r in rows]

        for col_i, col in enumerate(cols):
            self._table.grid_columnconfigure(col_i, weight=1)
            ctk.CTkLabel(self._table, text=col, font=ctk.CTkFont(weight="bold"),
                         fg_color=("gray82", "gray22"), corner_radius=4).grid(
                row=0, column=col_i, sticky="ew", padx=2, pady=(0, 2)
            )

        for row_i, row_data in enumerate(data, start=1):
            bg = ("gray88", "gray18") if row_i % 2 == 0 else ("gray92", "gray16")
            for col_i, val in enumerate(row_data):
                ctk.CTkLabel(self._table, text=val, fg_color=bg,
                             font=ctk.CTkFont(size=12), anchor="w").grid(
                    row=row_i, column=col_i, sticky="ew", padx=2, pady=1
                )

        self._status.configure(text=f"{len(data)} rows")

    def _run_calculate(self):
        count = run_calculate()
        self._mode.set("calc")
        self._load()
        self._status.configure(text=f"Calculate complete — {count} entries assigned")
