# views/welcome_view.py
import io
import customtkinter as ctk
from PIL import Image
from models.reference import ShowDetails
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry, CalculatedEntry
from models.results import Result, NotBenched


def _nav(widget, key: str):
    widget.winfo_toplevel().navigate(key)


class WelcomeView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._logo_ctk = None
        self._build()

    # ── Build ─────────────────────────────────────────────────────────

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        sd = ShowDetails.select().first()

        # ── Hero ──────────────────────────────────────────────────────
        hero = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray88", "gray17"))
        hero.grid(row=0, column=0, sticky="ew")
        hero.grid_columnconfigure(1, weight=1)

        self._draw_hero_logo(hero, sd)

        text_col = ctk.CTkFrame(hero, fg_color="transparent")
        text_col.grid(row=0, column=1, sticky="w", padx=(0, 20), pady=20)

        if sd and sd.show_eng:
            ctk.CTkLabel(
                text_col,
                text=sd.show_eng,
                font=ctk.CTkFont(size=22, weight="bold"),
                anchor="w",
            ).pack(anchor="w")
            parts = [p for p in [sd.date_eng, sd.club_eng_full] if p]
            if parts:
                ctk.CTkLabel(
                    text_col,
                    text="  |  ".join(parts),
                    font=ctk.CTkFont(size=12),
                    text_color=("gray40", "gray60"),
                    anchor="w",
                ).pack(anchor="w", pady=(2, 0))
        else:
            ctk.CTkLabel(
                text_col,
                text="Welcome to Benchabird Show Manager",
                font=ctk.CTkFont(size=22, weight="bold"),
                anchor="w",
            ).pack(anchor="w")
            ctk.CTkLabel(
                text_col,
                text="Start by configuring your show in Show Setup",
                font=ctk.CTkFont(size=12),
                text_color=("gray40", "gray60"),
                anchor="w",
            ).pack(anchor="w", pady=(2, 0))

        ctk.CTkButton(
            hero,
            text="Dashboard →",
            width=130, height=34,
            fg_color=("steelblue4", "steelblue"),
            hover_color=("steelblue3", "#4a9eca"),
            command=lambda: _nav(self, "dashboard"),
        ).grid(row=0, column=2, padx=20, pady=20)

        # ── Scrollable body ───────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        self._build_stats(scroll)
        self._build_workflow(scroll)
        self._build_tips(scroll)

    def _draw_hero_logo(self, hero, sd):
        logo_img = None
        if sd:
            raw = sd.logo_data
            if raw:
                try:
                    logo_img = Image.open(io.BytesIO(bytes(raw))).convert("RGBA")
                except Exception:
                    pass
            if logo_img is None and sd.logo_path:
                try:
                    logo_img = Image.open(sd.logo_path).convert("RGBA")
                except Exception:
                    pass

        if logo_img:
            w, h = logo_img.size
            target_h = 72
            target_w = int(w * target_h / h)
            target_w = min(target_w, 140)
            self._logo_ctk = ctk.CTkImage(logo_img, size=(target_w, target_h))
            ctk.CTkLabel(
                hero, image=self._logo_ctk, text="",
            ).grid(row=0, column=0, padx=(20, 12), pady=20)
        else:
            ctk.CTkLabel(
                hero, text="🐦",
                font=ctk.CTkFont(size=48),
            ).grid(row=0, column=0, padx=(20, 12), pady=20)

    # ── Stats row ─────────────────────────────────────────────────────

    def _build_stats(self, parent):
        n_exhibitors = Exhibitor.select().count()
        n_entries = ShowEntry.select().count()
        n_calc = CalculatedEntry.select().count()
        n_results = Result.select().where(Result.result.is_null(False)).count()
        n_nb = NotBenched.select().count()
        result_pct = int((n_results + n_nb) / n_calc * 100) if n_calc > 0 else 0

        stats = [
            (str(n_exhibitors), "Exhibitors",  "registered"),
            (str(n_entries),    "Entries",     "show entries"),
            (str(n_calc),       "Benched",     "checked in"),
            (f"{result_pct}%",  "Results",     f"{n_results + n_nb} of {n_calc}"),
        ]

        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", padx=20, pady=(20, 8))
        for i in range(4):
            row_frame.grid_columnconfigure(i, weight=1)

        for col, (value, title, sub) in enumerate(stats):
            card = ctk.CTkFrame(row_frame, corner_radius=10, fg_color=("gray85", "gray20"))
            card.grid(row=0, column=col, padx=6, sticky="ew")
            ctk.CTkLabel(
                card, text=value,
                font=ctk.CTkFont(size=32, weight="bold"),
            ).pack(pady=(14, 2))
            ctk.CTkLabel(
                card, text=title,
                font=ctk.CTkFont(size=12, weight="bold"),
            ).pack()
            ctk.CTkLabel(
                card, text=sub,
                font=ctk.CTkFont(size=10),
                text_color=("gray50", "gray55"),
            ).pack(pady=(0, 12))

    # ── Workflow cards ─────────────────────────────────────────────────

    def _build_workflow(self, parent):
        sd = ShowDetails.select().first()
        n_exhibitors = Exhibitor.select().count()
        n_entries = ShowEntry.select().count()
        n_calc = CalculatedEntry.select().count()
        n_results = Result.select().where(Result.result.is_null(False)).count()
        n_nb = NotBenched.select().count()
        results_done = (n_results + n_nb) >= n_calc and n_calc > 0

        steps = [
            (
                bool(sd and sd.show_eng),
                "1",
                "Show Setup",
                "Configure show name, date, club & logo",
                "setup",
            ),
            (
                n_exhibitors > 0,
                "2",
                "Exhibitors",
                f"{n_exhibitors} exhibitor{'s' if n_exhibitors != 1 else ''} registered",
                "exhibitors",
            ),
            (
                n_entries > 0,
                "3",
                "Entries",
                f"{n_entries} show entr{'ies' if n_entries != 1 else 'y'} entered",
                "entries",
            ),
            (
                n_calc > 0,
                "4",
                "Check-in / Benching",
                f"{n_calc} birds benched" if n_calc > 0 else "Bench arrivals and allocate exhibit numbers",
                "participants",
            ),
            (
                n_calc > 0,
                "5",
                "Print Tickets",
                "Generate cage tickets PDF",
                "tickets",
            ),
            (
                results_done,
                "6",
                "Show Day Capture",
                f"{n_results + n_nb} of {n_calc} results recorded" if n_calc > 0 else "Capture judging sheets",
                "capture",
            ),
            (
                results_done,
                "7",
                "Generate Reports",
                "Produce show report PDFs",
                "reports",
            ),
        ]

        ctk.CTkLabel(
            parent,
            text="Show Workflow",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).pack(anchor="w", padx=26, pady=(8, 6))

        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="x", padx=20, pady=(0, 8))
        for i in range(4):
            grid.grid_columnconfigure(i, weight=1)

        for idx, (done, num, title, subtitle, nav_key) in enumerate(steps):
            col = idx % 4
            row_i = idx // 4

            if done:
                bg = ("palegreen3", "#2d5a27")
                num_bg = ("green4", "#4caf50")
                num_fg = ("white", "white")
                title_color = ("gray10", "white")
                sub_color = ("gray35", "gray75")
            else:
                bg = ("gray85", "gray20")
                num_bg = ("gray70", "gray35")
                num_fg = ("gray30", "gray70")
                title_color = ("gray30", "gray75")
                sub_color = ("gray55", "gray50")

            card = ctk.CTkFrame(
                grid, corner_radius=10,
                fg_color=bg,
                cursor="hand2",
            )
            card.grid(row=row_i, column=col, padx=6, pady=6, sticky="ew")

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=14, pady=12)
            inner.grid_columnconfigure(1, weight=1)

            badge = ctk.CTkLabel(
                inner,
                text="✓" if done else num,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=28, height=28,
                corner_radius=14,
                fg_color=num_bg,
                text_color=num_fg,
            )
            badge.grid(row=0, column=0, rowspan=2, padx=(0, 10))

            ctk.CTkLabel(
                inner, text=title,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=title_color,
                anchor="w",
            ).grid(row=0, column=1, sticky="w")

            ctk.CTkLabel(
                inner, text=subtitle,
                font=ctk.CTkFont(size=10),
                text_color=sub_color,
                anchor="w",
                wraplength=160,
                justify="left",
            ).grid(row=1, column=1, sticky="w")

            card.bind("<Button-1>", lambda e, k=nav_key: _nav(self, k))
            for child in card.winfo_children() + inner.winfo_children():
                try:
                    child.bind("<Button-1>", lambda e, k=nav_key: _nav(self, k))
                except Exception:
                    pass

    # ── Tips ─────────────────────────────────────────────────────────

    def _build_tips(self, parent):
        ctk.CTkLabel(
            parent,
            text="Quick Tips",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).pack(anchor="w", padx=26, pady=(8, 6))

        tips_frame = ctk.CTkFrame(parent, corner_radius=10, fg_color=("gray85", "gray20"))
        tips_frame.pack(fill="x", padx=20, pady=(0, 24))

        tips = [
            ("Ctrl+F", "Global search — find exhibitors, classes, entries instantly"),
            ("Ctrl+B", "Jump straight to Check-in / Benching"),
            ("Ctrl+E", "Jump straight to Entries"),
            ("Ctrl+R", "Jump straight to Results"),
            ("Ctrl+T", "Jump straight to Tickets"),
            ("Bulk Edit", "Right-click or Shift+click rows in Entries/Results to bulk-edit"),
            ("Archives", "Use Admin → Archives to snapshot the DB before major changes"),
            ("SQL Editor", "Use Admin → SQL Editor to run raw queries against the database"),
        ]

        for i, (shortcut, desc) in enumerate(tips):
            row = ctk.CTkFrame(tips_frame, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(
                row,
                text=shortcut,
                font=ctk.CTkFont(family="Courier New", size=11, weight="bold"),
                fg_color=("gray75", "gray30"),
                corner_radius=4,
                width=90,
                anchor="center",
            ).pack(side="left", padx=(0, 12))
            ctk.CTkLabel(
                row,
                text=desc,
                font=ctk.CTkFont(size=11),
                text_color=("gray30", "gray70"),
                anchor="w",
            ).pack(side="left")

        ctk.CTkFrame(tips_frame, height=8, fg_color="transparent").pack()
