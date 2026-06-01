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
        self._build()
        self._reload_table()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        ctk.CTkLabel(toolbar, text="Late Entries",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        ctk.CTkButton(toolbar, text="Delete Selected", width=110,
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=self._delete_selected).pack(side="right", padx=4)
        ctk.CTkButton(toolbar, text="+ Add Late Entry", width=130,
                      command=self._open_add).pack(side="right", padx=4)

        self._status = ctk.CTkLabel(toolbar, text="",
                                    font=ctk.CTkFont(size=11),
                                    text_color=("gray40", "gray60"))
        self._status.pack(side="left", padx=12)

        self._table = PaginatedTable(
            self,
            headers=["AutoNum", "ExhNo", "Name", "Class"],
            on_select=self._select,
        )
        self._table.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 16))

    def _reload_table(self):
        self._selected_auto_num = None
        entries = _repo.get_late()
        data = [
            (e.auto_num, [str(e.auto_num), str(e.exh_no or ""), e.name or "", e.class_code or ""])
            for e in entries
        ]
        self._table.load(data)
        self._status.configure(text=f"{len(data)} rows")

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
