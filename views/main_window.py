# views/main_window.py
import customtkinter as ctk
from PIL import Image
from tkinter import messagebox
from config import APP_NAME, APP_VERSION, BASE_DIR

NAV = [
    ("Dashboard",         "dashboard"),
    ("Search",            "search"),
    ("Show Setup",        "setup"),
    ("Exhibitors",        "exhibitors"),
    ("Show Participants", "participants"),
    ("Show Day Capture",  "capture"),
    ("Results",           "results"),
    ("Special Winners",   "special"),
    ("Special Prizes",    "special_list"),
    ("Tickets",           "tickets"),
    ("Reports",           "reports"),
    ("Hall of Fame",      "hall_of_fame"),
    ("Class Glossary",    "notes"),
    ("Help",              "help"),
]

ADMIN_NAV = [
    ("Import Data",     "import"),
    ("Reset Data",      "reset"),
    ("Archives",        "archives"),
    ("SQL Editor",      "sql_editor"),
]


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1280x780")
        self.minsize(960, 620)
        self._active_key = None
        self._nav_btns: dict = {}
        self._set_icon()
        self._build()
        self._bind_shortcuts()
        self.after(600, self._show_pending_changelog)

    def _bind_shortcuts(self):
        for seq, key in [
            ("<Control-f>", "search"),       ("<Control-F>", "search"),
            ("<Control-h>", "help"),         ("<Control-H>", "help"),
            ("<Control-e>", "participants"), ("<Control-E>", "participants"),
            ("<Control-b>", "participants"), ("<Control-B>", "participants"),
            ("<Control-r>", "results"),      ("<Control-R>", "results"),
            ("<Control-t>", "tickets"),      ("<Control-T>", "tickets"),
            ("<Control-x>", "exhibitors"),   ("<Control-X>", "exhibitors"),
        ]:
            self.bind(seq, lambda e, k=key: self.navigate(k))

    def _set_icon(self):
        ico = BASE_DIR / "icon.ico"
        if ico.exists():
            try:
                self.iconbitmap(str(ico))
            except Exception:
                pass

    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._sidebar = ctk.CTkFrame(self, width=195, corner_radius=0)
        self._sidebar.grid(row=0, column=0, sticky="nsew")
        self._sidebar.grid_propagate(False)

        # Logo in sidebar header
        logo_img = self._load_logo()
        if logo_img:
            ctk.CTkLabel(self._sidebar, image=logo_img, text="").pack(padx=14, pady=(16, 4))
            ctk.CTkLabel(
                self._sidebar,
                text="Show Manager",
                font=ctk.CTkFont(size=12, weight="bold"),
            ).pack(padx=14, pady=(0, 10))
        else:
            ctk.CTkLabel(
                self._sidebar,
                text="Benchabird\nShow Manager",
                font=ctk.CTkFont(size=14, weight="bold"),
            ).pack(padx=14, pady=(20, 12))

        ctk.CTkFrame(self._sidebar, height=1, fg_color=("gray70", "gray35")).pack(fill="x", padx=14, pady=(0, 6))

        nav_scroll = ctk.CTkScrollableFrame(self._sidebar, fg_color="transparent")
        nav_scroll.pack(fill="both", expand=True, padx=0, pady=(0, 8))

        for label, key in NAV:
            btn = ctk.CTkButton(
                nav_scroll,
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

        ctk.CTkFrame(nav_scroll, height=1, fg_color=("gray70", "gray35")).pack(fill="x", padx=14, pady=(8, 4))

        for label, key in ADMIN_NAV:
            btn = ctk.CTkButton(
                nav_scroll,
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

    def _load_logo(self):
        logo_path = BASE_DIR / "logo.png"
        if not logo_path.exists():
            return None
        try:
            img = Image.open(str(logo_path))
            # Fit into sidebar width (167px) preserving aspect ratio, max height 60px
            max_w, max_h = 167, 60
            w, h = img.size
            scale = min(max_w / w, max_h / h)
            new_w, new_h = int(w * scale), int(h * scale)
            return ctk.CTkImage(img, size=(new_w, new_h))
        except Exception:
            return None

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
        from views.show_participants_view import ShowParticipantsView
        from views.show_day_capture_view import ShowDayCaptureView
        from views.results_view import ResultsView
        from views.special_view import SpecialView
        from views.special_list_view import SpecialListView
        from views.tickets_view import TicketsView
        from views.reports_view import ReportsView
        from views.hall_of_fame_view import HallOfFameView
        from views.notes_view import NotesView
        from views.reimport_view import ReImportView
        from views.reset_view import ResetView
        from views.help_view import HelpView
        from views.search_view import SearchView
        from views.archive_view import ArchiveView
        from views.sql_editor_view import SQLEditorView
        from views.welcome_view import WelcomeView

        view_map = {
            "welcome":       WelcomeView,
            "dashboard":     DashboardView,
            "search":        SearchView,
            "setup":         SetupView,
            "exhibitors":    ExhibitorsView,
            "participants":  ShowParticipantsView,
            "capture":       ShowDayCaptureView,
            "results":       ResultsView,
            "special":       SpecialView,
            "special_list":  SpecialListView,
            "tickets":       TicketsView,
            "reports":       ReportsView,
            "hall_of_fame":  HallOfFameView,
            "notes":         NotesView,
            "help":          HelpView,
            "import":        ReImportView,
            "reset":         ResetView,
            "sql_editor":    SQLEditorView,
        }
        cls = view_map.get(key)
        return cls(self._content) if cls else None

    def _show_pending_changelog(self):
        try:
            from services.update_service import pop_pending_changelog

            changelog = pop_pending_changelog()
        except Exception:
            return
        if changelog:
            messagebox.showinfo("Benchabird Updated", changelog)
