# views/main_window.py
import customtkinter as ctk
from config import APP_NAME, APP_VERSION

NAV = [
    ("Dashboard",       "dashboard"),
    ("Show Setup",      "setup"),
    ("Exhibitors",      "exhibitors"),
    ("Entries",         "entries"),
    ("Late Entries",    "late_entries"),
    ("Results",         "results"),
    ("Special Winners", "special"),
    ("Special Prizes",  "special_list"),
    ("Tickets",         "tickets"),
    ("Reports",         "reports"),
    ("Hall of Fame",    "hall_of_fame"),
    ("Notes",           "notes"),
]

ADMIN_NAV = [
    ("Import Data",     "import"),
    ("Reset Data",      "reset"),
]


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1280x780")
        self.minsize(960, 620)
        self._active_key = None
        self._nav_btns: dict = {}
        self._build()

    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._sidebar = ctk.CTkFrame(self, width=195, corner_radius=0)
        self._sidebar.grid(row=0, column=0, sticky="nsew")
        self._sidebar.grid_propagate(False)

        ctk.CTkLabel(
            self._sidebar,
            text="Benchabird\nShow Manager",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(padx=14, pady=(20, 12))

        ctk.CTkFrame(self._sidebar, height=1, fg_color=("gray70", "gray35")).pack(fill="x", padx=14, pady=(0, 10))

        for label, key in NAV:
            btn = ctk.CTkButton(
                self._sidebar,
                text=label,
                anchor="w",
                corner_radius=6,
                height=34,
                fg_color="transparent",
                text_color=("gray20", "gray80"),
                hover_color=("gray85", "gray28"),
                command=lambda k=key: self.navigate(k),
            )
            btn.pack(fill="x", padx=8, pady=2)
            self._nav_btns[key] = btn

        ctk.CTkFrame(self._sidebar, height=1, fg_color=("gray70", "gray35")).pack(fill="x", padx=14, pady=(8, 4))

        for label, key in ADMIN_NAV:
            btn = ctk.CTkButton(
                self._sidebar,
                text=label,
                anchor="w",
                corner_radius=6,
                height=30,
                fg_color="transparent",
                text_color=("gray40", "gray60"),
                hover_color=("gray85", "gray28"),
                font=ctk.CTkFont(size=11),
                command=lambda k=key: self.navigate(k),
            )
            btn.pack(fill="x", padx=8, pady=2)
            self._nav_btns[key] = btn

        self._content = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray95", "gray13"))
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(0, weight=1)

    def navigate(self, key: str):
        if self._active_key and self._active_key in self._nav_btns:
            self._nav_btns[self._active_key].configure(
                fg_color="transparent",
                text_color=("gray20", "gray80"),
            )

        for w in self._content.winfo_children():
            w.destroy()

        view = self._make_view(key)
        if view:
            view.grid(row=0, column=0, sticky="nsew")

        self._active_key = key
        if key in self._nav_btns:
            self._nav_btns[key].configure(
                fg_color=("gray78", "gray28"),
                text_color=("gray5", "white"),
            )

    def _make_view(self, key: str):
        from views.dashboard import DashboardView
        from views.setup_view import SetupView
        from views.exhibitors_view import ExhibitorsView
        from views.entries_view import EntriesView
        from views.late_entries_view import LateEntriesView
        from views.results_view import ResultsView
        from views.special_view import SpecialView
        from views.special_list_view import SpecialListView
        from views.tickets_view import TicketsView
        from views.reports_view import ReportsView
        from views.hall_of_fame_view import HallOfFameView
        from views.notes_view import NotesView
        from views.reimport_view import ReImportView
        from views.reset_view import ResetView

        view_map = {
            "dashboard":    DashboardView,
            "setup":        SetupView,
            "exhibitors":   ExhibitorsView,
            "entries":      EntriesView,
            "late_entries": LateEntriesView,
            "results":      ResultsView,
            "special":      SpecialView,
            "special_list": SpecialListView,
            "tickets":      TicketsView,
            "reports":      ReportsView,
            "hall_of_fame": HallOfFameView,
            "notes":        NotesView,
            "import":       ReImportView,
            "reset":        ResetView,
        }
        cls = view_map.get(key)
        return cls(self._content) if cls else None
