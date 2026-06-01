# views/entries_view.py
import customtkinter as ctk
from controllers.entry_ctrl import get_all_entries, get_calculated, run_calculate, delete_by_auto_num
from views._paginated_table import PaginatedTable

COLS_RAW = ["AutoNum", "ExhNo", "Class"]
COLS_CALC = ["#", "ExhNo", "Name", "Class"]


class EntriesView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._mode = ctk.StringVar(value="raw")
        self._selected_auto_num = None
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

        self._raw_table = PaginatedTable(
            self, headers=COLS_RAW, on_select=self._select,
        )
        self._raw_table.grid(row=2, column=0, sticky="nsew", padx=16, pady=(4, 16))

        self._calc_table = PaginatedTable(
            self, headers=COLS_CALC, on_select=self._select,
        )

    def _reload_table(self):
        self._selected_auto_num = None
        if self._mode.get() == "calc":
            rows = get_calculated()
            data = [
                (r.auto_num, [str(r.auto_num), str(r.exh_no or ""), r.name or "", r.class_code or ""])
                for r in rows
            ]
            self._raw_table.grid_remove()
            self._calc_table.grid(row=2, column=0, sticky="nsew", padx=16, pady=(4, 16))
            self._calc_table.load(data)
        else:
            rows = get_all_entries()
            data = [
                (r.auto_num, [str(r.auto_num), str(r.exh_no or ""), r.class_code or ""])
                for r in rows
            ]
            self._calc_table.grid_remove()
            self._raw_table.grid(row=2, column=0, sticky="nsew", padx=16, pady=(4, 16))
            self._raw_table.load(data)
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
