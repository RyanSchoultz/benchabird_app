# views/entries_view.py
import customtkinter as ctk
from controllers.entry_ctrl import get_all_entries, get_calculated, run_calculate, delete_by_auto_num

COLS_RAW = ["AutoNum", "ExhNo", "Class"]
COLS_CALC = ["#", "ExhNo", "Name", "Class"]


class EntriesView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._mode = ctk.StringVar(value="raw")
        self._selected_auto_num = None
        self._table_frame = None
        self._build()
        self._reload_table()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        ctk.CTkLabel(toolbar, text="Show Entries",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        ctk.CTkButton(toolbar, text="Run Calculate (0010)",
                      command=self._run_calculate).pack(side="right", padx=(4, 0))
        ctk.CTkButton(toolbar, text="Delete Selected", width=110,
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=self._delete_selected).pack(side="right", padx=4)
        ctk.CTkButton(toolbar, text="+ Add Entry", width=100,
                      command=self._open_add).pack(side="right", padx=4)

        seg = ctk.CTkSegmentedButton(
            toolbar,
            values=["Show Entries", "Calculated"],
            command=lambda v: (
                self._mode.set("calc" if v == "Calculated" else "raw"),
                self._reload_table(),
            ),
        )
        seg.set("Show Entries")
        seg.pack(side="right", padx=8)

        self._status = ctk.CTkLabel(toolbar, text="",
                                    font=ctk.CTkFont(size=11),
                                    text_color=("gray40", "gray60"))
        self._status.pack(side="left", padx=12)

    def _reload_table(self):
        self._selected_auto_num = None
        if self._table_frame:
            self._table_frame.destroy()

        self._table_frame = ctk.CTkScrollableFrame(self, fg_color=("gray92", "gray16"))
        self._table_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(4, 16))

        if self._mode.get() == "calc":
            rows = get_calculated()
            cols = COLS_CALC
            data = [(r.auto_num, [str(r.auto_num), str(r.exh_no or ""), r.name or "", r.class_code or ""])
                    for r in rows]
        else:
            rows = get_all_entries()
            cols = COLS_RAW
            data = [(r.auto_num, [str(r.auto_num), str(r.exh_no or ""), r.class_code or ""])
                    for r in rows]

        for col_i, col in enumerate(cols):
            self._table_frame.grid_columnconfigure(col_i, weight=1)
            ctk.CTkLabel(self._table_frame, text=col,
                         font=ctk.CTkFont(weight="bold"),
                         fg_color=("gray82", "gray22"), corner_radius=4).grid(
                row=0, column=col_i, sticky="ew", padx=2, pady=(0, 2)
            )

        for row_i, (auto_num, row_vals) in enumerate(data, start=1):
            bg = ("gray88", "gray18") if row_i % 2 == 0 else ("gray92", "gray16")
            for col_i, val in enumerate(row_vals):
                ctk.CTkButton(
                    self._table_frame, text=val, anchor="w",
                    fg_color=bg, text_color=("gray10", "gray90"),
                    hover_color=("gray80", "gray25"),
                    corner_radius=0, height=28,
                    font=ctk.CTkFont(size=12),
                    command=lambda an=auto_num: self._select(an),
                ).grid(row=row_i, column=col_i, sticky="ew", padx=2, pady=1)

        self._status.configure(text=f"{len(data)} rows")

    def _select(self, auto_num: int):
        self._selected_auto_num = auto_num

    def _open_add(self):
        from views._entry_dialog import EntryDialog
        dlg = EntryDialog(self)
        self.wait_window(dlg)
        self._reload_table()

    def _delete_selected(self):
        if self._selected_auto_num is None:
            return
        delete_by_auto_num(self._selected_auto_num)
        self._reload_table()

    def _run_calculate(self):
        count = run_calculate()
        self._mode.set("calc")
        self._reload_table()
        self._status.configure(text=f"Calculate complete — {count} entries assigned")
