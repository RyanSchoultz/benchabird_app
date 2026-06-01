# views/tickets_view.py
import customtkinter as ctk
from services.ticket_service import get_ticket_assignments


class TicketsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        ctk.CTkLabel(toolbar, text="Tickets", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(toolbar, text="Print All Tickets", command=self._print).pack(side="right")

        table = ctk.CTkScrollableFrame(self, fg_color=("gray92", "gray16"))
        table.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        for col_i, hdr in enumerate(["Ticket #", "AutoNum", "ExhNo", "Name", "Class"]):
            table.grid_columnconfigure(col_i, weight=1)
            ctk.CTkLabel(table, text=hdr, font=ctk.CTkFont(weight="bold"),
                         fg_color=("gray82", "gray22")).grid(row=0, column=col_i, sticky="ew", padx=2, pady=(0, 2))

        for row_i, t in enumerate(get_ticket_assignments(), start=1):
            bg = ("gray88", "gray18") if row_i % 2 == 0 else ("gray92", "gray16")
            vals = [str(t['ticket_no']), str(t['auto_num']), str(t['exh_no'] or ""),
                    t['name'] or "", t['class_code'] or ""]
            for col_i, val in enumerate(vals):
                ctk.CTkLabel(table, text=val, fg_color=bg, anchor="w",
                             font=ctk.CTkFont(size=12)).grid(row=row_i, column=col_i, sticky="ew", padx=2, pady=1)

    def _print(self):
        ctk.CTkLabel(self, text="PDF printing — planned for Phase 2",
                     text_color=("gray50", "gray60")).grid(row=2, column=0, pady=8)
