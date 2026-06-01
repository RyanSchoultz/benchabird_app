# views/special_view.py
import customtkinter as ctk
from services.special_service import get_winners_with_details
from views._paginated_table import PaginatedTable


class SpecialView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Special Winners",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=12
        )

        self._table = PaginatedTable(
            self,
            headers=["Special #", "Exhibit No", "Description", "Prize", ""],
            col_weights=[1, 1, 2, 2, 0],
            selectable=False,
        )
        self._table.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self._reload_table()

    def _reload_table(self):
        winners = get_winners_with_details()
        data = [
            (w['special_nr'], [
                w['special_nr'] or "",
                str(w['exhibit_no'] or ""),
                w['description'] or "",
                w['prize'] or "",
            ])
            for w in winners
        ]
        winner_map = {w['special_nr']: w for w in winners}

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
