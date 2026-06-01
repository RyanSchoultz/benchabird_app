# views/special_list_view.py
import customtkinter as ctk
from views._paginated_table import PaginatedTable


class SpecialListView(ctk.CTkFrame):
    """View and manage the Special Prize List (add/edit/delete prizes)."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._selected_nr = None
        self._all_data: list = []
        self._build()
        self._reload_table()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        ctk.CTkLabel(toolbar, text="Special Prize List",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(toolbar, text="+ Add", width=80,
                      command=self._open_add).pack(side="right", padx=(4, 0))
        ctk.CTkButton(toolbar, text="Edit", width=70,
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=self._open_edit).pack(side="right", padx=4)
        ctk.CTkButton(toolbar, text="Delete", width=70,
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=self._delete_selected).pack(side="right", padx=4)

        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 2))
        self._filter_var = ctk.StringVar()
        self._filter_var.trace_add("write", lambda *_: self._apply_filter())
        ctk.CTkEntry(filter_bar, textvariable=self._filter_var,
                     placeholder_text="Filter by description or prize…", width=280).pack(side="left")
        ctk.CTkButton(filter_bar, text="✕", width=28, height=28,
                      fg_color="transparent", text_color=("gray40", "gray60"),
                      command=lambda: self._filter_var.set("")).pack(side="left", padx=4)
        self._status = ctk.CTkLabel(filter_bar, text="", font=ctk.CTkFont(size=11),
                                    text_color=("gray40", "gray60"))
        self._status.pack(side="left", padx=8)

        self._table = PaginatedTable(
            self,
            headers=["Special #", "Description", "Prize", "Cash"],
            col_weights=[1, 3, 2, 1],
            on_select=self._select,
        )
        self._table.grid(row=2, column=0, sticky="nsew", padx=16, pady=(4, 16))

    def _reload_table(self):
        from services.special_service import get_all_special_lists
        specials = get_all_special_lists()
        self._all_data = [
            (sp.special_nr, [
                sp.special_nr or "",
                sp.description or "",
                sp.prize1 or "",
                str(sp.cash) if sp.cash is not None else "",
            ])
            for sp in specials
        ]
        self._apply_filter()

    def _apply_filter(self):
        q = self._filter_var.get().strip().lower()
        data = [r for r in self._all_data if not q or any(q in c.lower() for c in r[1])]
        self._table.load(data)
        total = len(self._all_data)
        self._status.configure(text=f"{len(data)} of {total}" if q else "")

    def _select(self, nr: str):
        self._selected_nr = nr

    def _open_add(self):
        from views._special_list_dialog import SpecialListDialog
        dlg = SpecialListDialog(self)
        self.wait_window(dlg)
        self._reload_table()

    def _open_edit(self):
        if not self._selected_nr:
            return
        from views._special_list_dialog import SpecialListDialog
        dlg = SpecialListDialog(self, self._selected_nr)
        self.wait_window(dlg)
        self._reload_table()

    def _delete_selected(self):
        if not self._selected_nr:
            return
        from services.special_service import delete_special_list
        delete_special_list(self._selected_nr)
        self._selected_nr = None
        self._reload_table()
