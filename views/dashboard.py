# views/dashboard.py
import customtkinter as ctk
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry, CalculatedEntry
from models.reference import ShowDetails
from models.special import SpecialWinner


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        details = ShowDetails.select().first()
        show_name = f"{details.show_eng} — {details.date_eng}" if details else "Show Manager"
        club = details.club_eng_full if details else ""

        hdr = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray88", "gray18"))
        hdr.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(hdr, text=show_name, font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=20, pady=14)
        ctk.CTkLabel(hdr, text=club, font=ctk.CTkFont(size=12), text_color=("gray40", "gray60")).pack(side="left")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=16)
        scroll.grid_columnconfigure((0, 1, 2, 3), weight=1)

        stats = [
            ("Exhibitors",      Exhibitor.select().count(),       "registered"),
            ("Show Entries",    ShowEntry.select().count(),       "total entries"),
            ("Calculated",      CalculatedEntry.select().count(), "after calculate"),
            ("Special Winners", SpecialWinner.select().count(),   "awards assigned"),
        ]

        for col, (title, value, sub) in enumerate(stats):
            card = ctk.CTkFrame(scroll, corner_radius=10)
            card.grid(row=0, column=col, padx=8, pady=8, sticky="ew")
            ctk.CTkLabel(card, text=str(value), font=ctk.CTkFont(size=36, weight="bold")).pack(padx=16, pady=(16, 2))
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=13, weight="bold")).pack()
            ctk.CTkLabel(card, text=sub, font=ctk.CTkFont(size=11), text_color=("gray50", "gray55")).pack(pady=(0, 14))

        ctk.CTkLabel(scroll, text="Quick Actions", font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=1, column=0, columnspan=4, sticky="w", padx=8, pady=(16, 8)
        )

        actions = ctk.CTkFrame(scroll, fg_color="transparent")
        actions.grid(row=2, column=0, columnspan=4, sticky="ew")
        actions.grid_columnconfigure((0, 1, 2, 3), weight=1)

        for col, text in enumerate(["Run Calculate", "View Entries", "Enter Results", "Print Tickets"]):
            ctk.CTkButton(
                actions, text=text, height=44,
                corner_radius=8,
                fg_color=("gray80", "gray25"),
                text_color=("gray10", "gray90"),
                hover_color=("gray72", "gray32"),
                command=lambda: None,
            ).grid(row=0, column=col, padx=8, pady=4, sticky="ew")
