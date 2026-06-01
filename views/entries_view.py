# views/entries_view.py
import customtkinter as ctk
from controllers.entry_ctrl import get_all_entries, get_calculated, run_calculate, delete_by_auto_num
from views._paginated_table import PaginatedTable

COLS_RAW = ["AutoNum", "ExhNo", "Class"]
COLS_CALC = ["#", "ExhNo", "Name", "Class"]


def _matches(cells: list, q: str) -> bool:
    return any(q in c.lower() for c in cells)


class EntriesView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._mode = ctk.StringVar(value="raw")
        self._selected_auto_num = None
        self._all_raw: list = []
        self._all_calc: list = []
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
        ctk.CTkButton(toolbar, text="Export", width=80,
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=self._export).pack(side="right", padx=4)
        ctk.CTkButton(toolbar, text="Bulk Edit…", width=100,
                      command=self._open_bulk).pack(side="right", padx=4)
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

        # Filter bar
        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 2))
        self._filter_var = ctk.StringVar()
        self._filter_var.trace_add("write", lambda *_: self._apply_filter())
        ctk.CTkEntry(
            filter_bar, textvariable=self._filter_var,
            placeholder_text="Filter by ExhNo, class code, or name…", width=300,
        ).pack(side="left")
        ctk.CTkButton(
            filter_bar, text="✕", width=28, height=28,
            fg_color="transparent", text_color=("gray40", "gray60"),
            command=lambda: self._filter_var.set(""),
        ).pack(side="left", padx=4)

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
            self._all_calc = [
                (r.auto_num, [str(r.auto_num), str(r.exh_no or ""), r.name or "", r.class_code or ""])
                for r in rows
            ]
            self._raw_table.grid_remove()
            self._calc_table.grid(row=2, column=0, sticky="nsew", padx=16, pady=(4, 16))
        else:
            rows = get_all_entries()
            self._all_raw = [
                (r.auto_num, [str(r.auto_num), str(r.exh_no or ""), r.class_code or ""])
                for r in rows
            ]
            self._calc_table.grid_remove()
            self._raw_table.grid(row=2, column=0, sticky="nsew", padx=16, pady=(4, 16))
        self._apply_filter()

    def _apply_filter(self):
        q = self._filter_var.get().strip().lower()
        if self._mode.get() == "calc":
            data = [row for row in self._all_calc if not q or _matches(row[1], q)]
            self._calc_table.load(data)
        else:
            data = [row for row in self._all_raw if not q or _matches(row[1], q)]
            self._raw_table.load(data)
        total = len(self._all_calc if self._mode.get() == "calc" else self._all_raw)
        shown = len(data)
        self._status.configure(
            text=f"{shown} of {total}" if q else f"{total} rows"
        )

    def _select(self, auto_num: int):
        self._selected_auto_num = auto_num

    def _open_add(self):
        from views._entry_dialog import EntryDialog
        dlg = EntryDialog(self)
        self.wait_window(dlg)
        self._reload_table()

    def _open_bulk(self):
        from views._bulk_edit_dialog import BulkEditDialog
        dlg = BulkEditDialog(self)
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

    def _export(self):
        from services.export_service import export_data
        if self._mode.get() == "calc":
            rows = [[str(k), c[1], c[2], c[3]] for k, c in self._all_calc]
            export_data(rows, ["AutoNum", "ExhNo", "Name", "Class"], "calculated_entries.csv")
        else:
            rows = [[str(k), c[1], c[2]] for k, c in self._all_raw]
            export_data(rows, ["AutoNum", "ExhNo", "Class"], "show_entries.csv")
