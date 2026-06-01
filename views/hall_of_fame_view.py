# views/hall_of_fame_view.py
import customtkinter as ctk
from models.reference import HallOfFame
from views._paginated_table import PaginatedTable


class HallOfFameView(ctk.CTkFrame):
    """Read-only view of historical Hall of Fame records."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Hall of Fame",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(16, 4)
        )

        self._table = PaginatedTable(
            self,
            headers=["Type", "Year", "Name", "Class", "Colour", "Judge"],
            selectable=False,
        )
        self._table.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

        records = list(
            HallOfFame.select().order_by(HallOfFame.year.desc(), HallOfFame.type_abbr)
        )
        data = [
            (r.id, [
                r.type_abbr or "",
                r.year or "",
                r.name or "",
                r.class_name or "",
                r.colour or "",
                r.judge or "",
            ])
            for r in records
        ]
        self._table.load(data)
