# views/late_entries_view.py
import customtkinter as ctk
from repository.entry_repo import EntryRepo
from services.late_entry_service import remove_late_entry
from views._paginated_table import PaginatedTable

_repo = EntryRepo()


class LateEntriesView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._selected_auto_num = None
        self._all_data: list = []
        self._build()
        self._reload_table()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        ctk.CTkLabel(toolbar, text="Late Entries",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(toolbar, text="Delete Selected", width=110,
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=self._delete_selected).pack(side="right", padx=4)
        ctk.CTkButton(toolbar, text="+ Add Late Entry", width=130,
                      command=self._open_add).pack(side="right", padx=4)
        self._status = ctk.CTkLabel(toolbar, text="", font=ctk.CTkFont(size=11),
                                    text_color=("gray40", "gray60"))
        self._status.pack(side="left", padx=12)

        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 2))
        self._filter_var = ctk.StringVar()
        self._filter_var.trace_add("write", lambda *_: self._apply_filter())
        ctk.CTkEntry(filter_bar, textvariable=self._filter_var,
                     placeholder_text="Filter by ExhNo, name, or class…", width=280).pack(side="left")
        ctk.CTkButton(filter_bar, text="✕", width=28, height=28,
                      fg_color="transparent", text_color=("gray40", "gray60"),
                      command=lambda: self._filter_var.set("")).pack(side="left", padx=4)

        self._table = PaginatedTable(self, headers=["AutoNum", "ExhNo", "Name", "Class"],
                                     on_select=self._select)
        self._table.grid(row=2, column=0, sticky="nsew", padx=16, pady=(4, 16))

    def _reload_table(self):
        self._selected_auto_num = None
        entries = _repo.get_late()
        self._all_data = [
            (e.auto_num, [str(e.auto_num), str(e.exh_no or ""), e.name or "", e.class_code or ""])
            for e in entries
        ]
        self._apply_filter()

    def _apply_filter(self):
        q = self._filter_var.get().strip().lower()
        data = [r for r in self._all_data if not q or any(q in c.lower() for c in r[1])]
        self._table.load(data)
        total = len(self._all_data)
        self._status.configure(text=f"{len(data)} of {total}" if q else f"{total} rows")

    def _select(self, auto_num: int):
        self._selected_auto_num = auto_num

    def _open_add(self):
        from views._late_entry_dialog import LateEntryDialog
        dlg = LateEntryDialog(self)
        self.wait_window(dlg)
        self._reload_table()

    def _delete_selected(self):
        if self._selected_auto_num is None:
            return
        remove_late_entry(self._selected_auto_num)
        self._reload_table()
