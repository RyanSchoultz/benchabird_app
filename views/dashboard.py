# views/dashboard.py
import customtkinter as ctk
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry, CalculatedEntry
from models.reference import ShowDetails
from models.special import SpecialWinner
from models.results import Result, NotBenched


def _nav(widget, key: str):
    widget.winfo_toplevel().navigate(key)


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

        # ── Header ───────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray88", "gray18"))
        hdr.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            hdr, text=show_name, font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left", padx=20, pady=14)
        ctk.CTkLabel(
            hdr, text=club, font=ctk.CTkFont(size=12), text_color=("gray40", "gray60")
        ).pack(side="left")
        ctk.CTkButton(
            hdr, text="Refresh", width=80, height=28,
            fg_color="transparent", border_width=1,
            text_color=("gray30", "gray70"),
            command=self._refresh,
        ).pack(side="right", padx=16)

        # ── Scrollable body ───────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=16)
        scroll.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self._scroll = scroll

        self._populate(scroll)

    def _refresh(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        self._populate(self._scroll)

    def _populate(self, scroll):
        # ── Stat cards ────────────────────────────────────────────────
        n_exhibitors = Exhibitor.select().count()
        n_entries = ShowEntry.select().count()
        n_calc = CalculatedEntry.select().count()
        n_results = Result.select().where(Result.result.is_null(False)).count()
        n_nb = NotBenched.select().count()
        n_special = SpecialWinner.select().count()

        stats = [
            ("Exhibitors", n_exhibitors, "registered"),
            ("Entries", n_entries, "show entries"),
            ("Benched", n_calc, "checked in"),
            ("Results", n_results, f"+ {n_nb} not benched"),
        ]
        for col, (title, value, sub) in enumerate(stats):
            card = ctk.CTkFrame(scroll, corner_radius=10)
            card.grid(row=0, column=col, padx=6, pady=8, sticky="ew")
            ctk.CTkLabel(
                card, text=str(value), font=ctk.CTkFont(size=34, weight="bold")
            ).pack(padx=16, pady=(14, 2))
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=13, weight="bold")).pack()
            ctk.CTkLabel(
                card, text=sub, font=ctk.CTkFont(size=11), text_color=("gray50", "gray55")
            ).pack(pady=(0, 12))

        # ── Second row: workflow checklist + top exhibitors ───────────
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_columnconfigure(1, weight=1)

        left = ctk.CTkFrame(scroll, corner_radius=10)
        left.grid(row=1, column=0, columnspan=2, padx=6, pady=(4, 8), sticky="ew")
        right = ctk.CTkFrame(scroll, corner_radius=10)
        right.grid(row=1, column=2, columnspan=2, padx=6, pady=(4, 8), sticky="ew")

        # Workflow checklist
        ctk.CTkLabel(
            left, text="Show Workflow", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=14, pady=(12, 6))

        results_pct = int(n_results / n_calc * 100) if n_calc > 0 else 0

        steps = [
            (n_entries > 0, f"Entries imported ({n_entries})"),
            (n_calc > 0, f"Birds checked in ({n_calc} benched)"),
            (n_entries > n_calc, f"Awaiting check-in ({n_entries - n_calc} not benched yet)"),
            (n_results + n_nb > 0, f"Results being entered ({results_pct}% of benched, {n_nb} not benched)"),
            (n_results + n_nb >= n_calc and n_calc > 0, "All results entered — tickets & reports ready"),
        ]

        for done, label in steps:
            if "Awaiting check-in" in label and n_entries == n_calc:
                continue
            icon = "✓" if done else "○"
            color = ("gray25", "gray80") if done else ("gray60", "gray50")
            row = ctk.CTkFrame(left, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=2)
            ctk.CTkLabel(
                row, text=icon, font=ctk.CTkFont(size=13), text_color=("green4", "lime green") if done else ("gray60", "gray50"), width=20
            ).pack(side="left")
            ctk.CTkLabel(
                row, text=label, font=ctk.CTkFont(size=12), text_color=color, anchor="w"
            ).pack(side="left", padx=6)

        ctk.CTkFrame(left, height=12, fg_color="transparent").pack()

        # Top exhibitors
        ctk.CTkLabel(
            right, text="Top Exhibitors by Entries", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=14, pady=(12, 6))

        db = ShowEntry._meta.database
        try:
            cur = db.execute_sql(
                "SELECT se.exh_no, e.name, COUNT(*) as cnt "
                "FROM show_entry se "
                "LEFT JOIN exhibitor e ON se.exh_no = e.exh_no "
                "GROUP BY se.exh_no ORDER BY cnt DESC LIMIT 6"
            )
            top = cur.fetchall()
        except Exception:
            top = []

        if top:
            max_cnt = top[0][2] if top else 1
            for exh_no, name, cnt in top:
                row = ctk.CTkFrame(right, fg_color="transparent")
                row.pack(fill="x", padx=14, pady=3)
                row.grid_columnconfigure(1, weight=1)
                ctk.CTkLabel(
                    row, text=f"#{exh_no}", font=ctk.CTkFont(size=11), width=36,
                    text_color=("gray40", "gray60"), anchor="e"
                ).grid(row=0, column=0, padx=(0, 6))
                bar_frame = ctk.CTkFrame(row, fg_color=("gray85", "gray22"), corner_radius=4, height=18)
                bar_frame.grid(row=0, column=1, sticky="ew")
                bar_frame.grid_propagate(False)
                fill_pct = cnt / max_cnt
                bar_inner = ctk.CTkFrame(bar_frame, fg_color=("steelblue", "steelblue"), corner_radius=4, height=18)
                bar_frame.update_idletasks()
                bar_inner.place(relx=0, rely=0, relwidth=fill_pct, relheight=1)
                label_text = f"{name or '?'} ({cnt})"
                ctk.CTkLabel(
                    row, text=label_text, font=ctk.CTkFont(size=11),
                    text_color=("gray25", "gray80"), anchor="w", width=140
                ).grid(row=0, column=2, padx=(6, 0))
        else:
            ctk.CTkLabel(right, text="No entry data yet.", text_color=("gray50", "gray55")).pack(padx=14, pady=8)

        ctk.CTkFrame(right, height=12, fg_color="transparent").pack()

        # ── Quick Actions ─────────────────────────────────────────────
        ctk.CTkLabel(
            scroll, text="Quick Actions", font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=2, column=0, columnspan=4, sticky="w", padx=8, pady=(8, 6))

        actions_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        actions_frame.grid(row=3, column=0, columnspan=4, sticky="ew")
        actions_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        quick = [
            ("Check In Birds",  "participants", "Bench arrivals and allocate exhibit #"),
            ("Show Day Capture", "capture",     "Capture results and awards"),
            ("Special Prizes",  "special_list", "Manage special award prizes"),
            ("Print Reports",   "reports",      "Generate and preview PDFs"),
        ]
        for col, (label, key, sub) in enumerate(quick):
            btn_frame = ctk.CTkFrame(actions_frame, corner_radius=8, fg_color=("gray85", "gray22"))
            btn_frame.grid(row=0, column=col, padx=6, pady=4, sticky="ew")
            ctk.CTkButton(
                btn_frame, text=label, height=40, corner_radius=6,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color=("gray78", "gray32"), text_color=("gray5", "white"),
                hover_color=("gray68", "gray38"),
                command=lambda k=key: _nav(self, k),
            ).pack(fill="x", padx=8, pady=(8, 2))
            ctk.CTkLabel(
                btn_frame, text=sub, font=ctk.CTkFont(size=10),
                text_color=("gray50", "gray55")
            ).pack(pady=(0, 8))
