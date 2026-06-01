# views/special_view.py
import customtkinter as ctk
from services.special_service import get_winners_with_details
from views._paginated_table import PaginatedTable


class SpecialView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._all_data: list = []
        self._winner_map: dict = {}
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        ctk.CTkLabel(toolbar, text="Special Winners",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 2))
        self._filter_var = ctk.StringVar()
        self._filter_var.trace_add("write", lambda *_: self._apply_filter())
        ctk.CTkEntry(filter_bar, textvariable=self._filter_var,
                     placeholder_text="Filter by description, exhibit #…", width=280).pack(side="left")
        ctk.CTkButton(filter_bar, text="✕", width=28, height=28,
                      fg_color="transparent", text_color=("gray40", "gray60"),
                      command=lambda: self._filter_var.set("")).pack(side="left", padx=4)

        self._table = PaginatedTable(
            self,
            headers=["Special #", "Exhibit No", "Description", "Prize", ""],
            col_weights=[1, 1, 2, 2, 0],
            selectable=False,
        )
        self._table.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self._reload_table()

    def _reload_table(self):
        winners = get_winners_with_details()
        self._winner_map = {w['special_nr']: w for w in winners}
        self._all_data = [
            (w['special_nr'], [
                w['special_nr'] or "",
                str(w['exhibit_no'] or ""),
                w['description'] or "",
                w['prize'] or "",
            ])
            for w in winners
        ]
        self._apply_filter()

    def _apply_filter(self):
        q = self._filter_var.get().strip().lower()
        data = [r for r in self._all_data if not q or any(q in c.lower() for c in r[1])]
        winner_map = self._winner_map

        def assign_render(special_nr, row_i, frame):
            w = winner_map.get(special_nr, {})
            ctk.CTkButton(
                frame, text="Assign", width=64, height=26,
                fg_color=("gray78", "gray32"), text_color=("gray10", "gray90"),
                font=ctk.CTkFont(size=11),
                command=lambda nr=special_nr, d=w.get('description', ''), en=w.get('exhibit_no'):
                    self._open_assign(nr, d, en),
            ).grid(row=row_i, column=4, padx=4, pady=1)

        self._table.load(data, row_render=assign_render)

    def _open_assign(self, special_nr: str, description: str, current_exhibit_no):
        from views._special_dialog import SpecialAssignDialog
        dlg = SpecialAssignDialog(self, special_nr, description, current_exhibit_no)
        self.wait_window(dlg)
        self._reload_table()
