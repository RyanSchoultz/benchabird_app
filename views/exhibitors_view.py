# views/exhibitors_view.py
import customtkinter as ctk
from controllers.exhibitor_ctrl import get_all, search, save, delete
from views._paginated_table import PaginatedTable


class ExhibitorsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._selected_pk = None
        self._build()
        self._load()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))

        ctk.CTkLabel(toolbar, text="Exhibitors",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(toolbar, text="+ Add Exhibitor", width=130,
                      command=self._open_edit_dialog).pack(side="right", padx=(4, 0))
        ctk.CTkButton(toolbar, text="Edit", width=70,
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=lambda: self._open_edit_dialog(self._selected_pk)).pack(side="right", padx=4)
        ctk.CTkButton(toolbar, text="Delete", width=70,
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=self._delete_selected).pack(side="right", padx=4)

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._load())
        ctk.CTkEntry(toolbar, textvariable=self._search_var,
                     placeholder_text="Search name / email...", width=220).pack(side="right", padx=(0, 8))

        self._table = PaginatedTable(
            self,
            headers=["Exh #", "Name", "Town", "Phone", "Email"],
            on_select=self._select,
        )
        self._table.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 16))

    def _load(self):
        exhibitors = search(self._search_var.get())
        data = [
            (e.id, [str(e.exh_no or ""), e.name or "", e.town or "",
                    e.tel_home or e.cell_no or "", e.email or ""])
            for e in exhibitors
        ]
        self._table.load(data)

    def _select(self, pk: int):
        self._selected_pk = pk

    def _open_edit_dialog(self, pk=None):
        from views._exhibitor_dialog import ExhibitorDialog
        dlg = ExhibitorDialog(self, pk)
        self.wait_window(dlg)
        self._load()

    def _delete_selected(self):
        if not self._selected_pk:
            return
        delete(self._selected_pk)
        self._selected_pk = None
        self._load()
