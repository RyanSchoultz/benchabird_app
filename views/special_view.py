# views/special_view.py
import customtkinter as ctk
from services.special_service import get_winners_with_details


class SpecialView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._table_frame = None
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Special Winners",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=12
        )
        self._reload_table()

    def _reload_table(self):
        if self._table_frame:
            self._table_frame.destroy()

        self._table_frame = ctk.CTkScrollableFrame(self, fg_color=("gray92", "gray16"))
        self._table_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

        hdrs = ["Special #", "Exhibit No", "Description", "Prize", ""]
        col_weights = [1, 1, 2, 2, 0]
        for col_i, hdr in enumerate(hdrs):
            self._table_frame.grid_columnconfigure(col_i, weight=col_weights[col_i])
            ctk.CTkLabel(self._table_frame, text=hdr, font=ctk.CTkFont(weight="bold"),
                         fg_color=("gray82", "gray22")).grid(
                row=0, column=col_i, sticky="ew", padx=2, pady=(0, 2)
            )

        for row_i, w in enumerate(get_winners_with_details(), start=1):
            bg = ("gray88", "gray18") if row_i % 2 == 0 else ("gray92", "gray16")
            for col_i, val in enumerate([
                w['special_nr'] or "",
                str(w['exhibit_no'] or ""),
                w['description'] or "",
                w['prize'] or "",
            ]):
                ctk.CTkLabel(self._table_frame, text=val, fg_color=bg, anchor="w",
                             font=ctk.CTkFont(size=12)).grid(
                    row=row_i, column=col_i, sticky="ew", padx=2, pady=1
                )
            ctk.CTkButton(
                self._table_frame, text="Assign", width=64, height=26,
                fg_color=("gray78", "gray32"), text_color=("gray10", "gray90"),
                font=ctk.CTkFont(size=11),
                command=lambda nr=w['special_nr'], d=w['description'], en=w['exhibit_no']:
                    self._open_assign(nr, d, en),
            ).grid(row=row_i, column=4, padx=4, pady=1)

    def _open_assign(self, special_nr: str, description: str, current_exhibit_no):
        from views._special_dialog import SpecialAssignDialog
        dlg = SpecialAssignDialog(self, special_nr, description, current_exhibit_no)
        self.wait_window(dlg)
        self._reload_table()
