# views/exhibitors_view.py
import customtkinter as ctk
from controllers.exhibitor_ctrl import get_all, search, save, delete
from repository.exhibitor_repo import ExhibitorRepo
from views._paginated_table import PaginatedTable

_repo = ExhibitorRepo()


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

        ctk.CTkButton(toolbar, text="+ Add", width=80,
                      command=self._open_edit_dialog).pack(side="right", padx=(4, 0))
        ctk.CTkButton(toolbar, text="Edit", width=70,
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=lambda: self._open_edit_dialog(self._selected_pk)).pack(side="right", padx=4)
        ctk.CTkButton(toolbar, text="Delete", width=70,
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=self._delete_selected).pack(side="right", padx=4)
        ctk.CTkButton(toolbar, text="Toggle Labels", width=110,
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=self._toggle_labels).pack(side="right", padx=4)
        ctk.CTkButton(toolbar, text="Export", width=80,
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=self._export).pack(side="right", padx=4)

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._load())
        ctk.CTkEntry(toolbar, textvariable=self._search_var,
                     placeholder_text="Search name / email...", width=200).pack(side="right", padx=(0, 8))

        self._table = PaginatedTable(
            self,
            headers=["Exh #", "Name", "Town", "Phone", "Email", "Labels"],
            col_weights=[1, 2, 1, 1, 2, 1],
            on_select=self._select,
        )
        self._table.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 16))

    def _load(self):
        exhibitors = search(self._search_var.get())
        self._all_exhibitors = exhibitors
        data = [
            (e.id, [
                str(e.exh_no or ""), e.name or "", e.town or "",
                e.tel_home or e.cell_no or "", e.email or "",
                "✓" if e.print_address else "",
            ])
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

    def _toggle_labels(self):
        if not self._selected_pk:
            return
        exhibitor = _repo.get_by_id(self._selected_pk)
        if exhibitor:
            _repo.update(exhibitor, print_address=not exhibitor.print_address)
        self._load()

    def _export(self):
        from services.export_service import export_data
        exhibitors = search(self._search_var.get())
        rows = [
            [str(e.exh_no or ""), e.name or "", e.address or "", e.suburb or "",
             e.town or "", e.zip_code or "", e.tel_home or "", e.cell_no or "",
             e.email or "", e.club or "", "Yes" if e.print_address else "No"]
            for e in exhibitors
        ]
        headers = ["ExhNo", "Name", "Address", "Suburb", "Town", "ZipCode",
                   "TelHome", "Cell", "Email", "Club", "PrintAddress"]
        export_data(rows, headers, "exhibitors.csv")
