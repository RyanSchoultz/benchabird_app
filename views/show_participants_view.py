# views/show_participants_view.py
import customtkinter as ctk

from services.show_participants_service import (
    ParticipantRow, ParticipantEntryRow,
    get_participants, search_registry, get_orphaned_exh_nos,
    next_available_exh_no, assign_exh_no, get_participant_entries,
)
from services.checkin_service import (
    bench_entries, bench_late_entries,
    unbench_entries, unbench_late_entries,
)
from services.calculate_service import auto_calculate_if_safe


class ShowParticipantsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._participants: list[ParticipantRow] = []
        self._selected: ParticipantRow | None = None
        self._entry_rows: list[ParticipantEntryRow] = []
        self._entry_vars: dict[tuple[int, bool], ctk.BooleanVar] = {}
        self._active_filter = "all"
        self._needs_recalc = False
        self._build()
        self._refresh_left()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_left()
        self._build_right()

    def _build_left(self):
        left = ctk.CTkFrame(self, corner_radius=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        left.grid_rowconfigure(4, weight=1)
        left.grid_columnconfigure(0, weight=1)
        self._left = left

        header_row = ctk.CTkFrame(left, fg_color="transparent")
        header_row.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))
        header_row.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header_row, text="Show Participants",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            header_row, text="Enrol…", width=70, height=28,
            command=self._open_enrol_dialog,
        ).grid(row=0, column=1)

        search_frame = ctk.CTkFrame(left, fg_color="transparent")
        search_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 4))
        search_frame.grid_columnconfigure(0, weight=1)
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search_change())
        ctk.CTkEntry(
            search_frame, textvariable=self._search_var,
            placeholder_text="Name, ExhNo, email, class…",
        ).grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(
            search_frame, text="✕", width=28, height=28,
            fg_color="transparent", text_color=("gray40", "gray60"),
            command=lambda: self._search_var.set(""),
        ).grid(row=0, column=1, padx=(4, 0))

        self._filter_seg = ctk.CTkSegmentedButton(
            left,
            values=["All", "Unbenched", "Late"],
            command=self._on_filter_change,
        )
        self._filter_seg.set("All")
        self._filter_seg.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 6))

        # Orphan warning — hidden until needed
        self._orphan_btn = ctk.CTkButton(
            left, text="",
            fg_color=("orange3", "darkorange"),
            text_color="white", anchor="w", height=32,
            command=self._show_orphaned,
        )

        self._list_frame = ctk.CTkScrollableFrame(left, width=290)
        self._list_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def _build_right(self):
        right = ctk.CTkFrame(self, corner_radius=8)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(4, weight=1)
        self._right = right

        self._right_header = ctk.CTkLabel(
            right, text="Select an exhibitor.",
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
        )
        self._right_header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))

        # Recalculate notice — hidden until needed
        self._recalc_frame = ctk.CTkFrame(
            right, fg_color=("orange3", "darkorange"), corner_radius=6,
        )
        ctk.CTkLabel(
            self._recalc_frame,
            text="  Entries changed — bench numbers may be stale.",
            font=ctk.CTkFont(size=11), text_color="white",
        ).pack(side="left", pady=6)
        ctk.CTkButton(
            self._recalc_frame, text="Recalculate", width=100,
            fg_color=("white", "gray20"), text_color=("gray10", "white"),
            command=self._on_recalculate,
        ).pack(side="right", padx=8, pady=6)

        # Action bar
        act = ctk.CTkFrame(right, fg_color="transparent")
        act.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 4))
        ctk.CTkButton(act, text="Select Unbenched",
                      command=self._select_all_unbenched).pack(side="left", padx=(0, 4))
        ctk.CTkButton(act, text="Clear",
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=self._clear_selection).pack(side="left", padx=4)
        ctk.CTkButton(act, text="Bench Selected",
                      command=self._bench_selected).pack(side="right")
        ctk.CTkButton(act, text="Unbench Selected",
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=self._unbench_selected).pack(side="right", padx=(0, 4))

        # Add entry bar
        add_bar = ctk.CTkFrame(right, fg_color="transparent")
        add_bar.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 6))
        ctk.CTkButton(add_bar, text="+ Add Entry", width=110,
                      command=self._open_add_entry).pack(side="left", padx=(0, 4))
        ctk.CTkButton(add_bar, text="+ Add Late Entry", width=130,
                      command=self._open_add_late_entry).pack(side="left")
        self._status = ctk.CTkLabel(
            add_bar, text="", font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
        )
        self._status.pack(side="right")

        self._entries_frame = ctk.CTkScrollableFrame(right)
        self._entries_frame.grid(row=4, column=0, sticky="nsew", padx=12, pady=(0, 12))

    # ── Left panel logic ──────────────────────────────────────────────────────

    def _refresh_left(self):
        self._participants = get_participants(filter=self._active_filter)
        self._render_participant_list(self._participants)
        self._check_orphans()

    def _on_search_change(self):
        q = self._search_var.get().strip()
        if not q:
            self._refresh_left()
            return
        lower_q = q.lower()
        filtered = [
            p for p in get_participants()
            if lower_q in (p.name or "").lower()
            or lower_q in str(p.exh_no or "")
            or lower_q in (p.email or "").lower()
        ]
        current_exh_nos = {p.exh_no for p in filtered}
        registry_extras = [
            e for e in search_registry(q)
            if e.exh_no not in current_exh_nos
        ]
        self._render_participant_list(filtered, registry_extras=registry_extras)

    def _on_filter_change(self, value: str):
        filter_map = {"All": "all", "Unbenched": "unbenched", "Late": "late"}
        self._active_filter = filter_map.get(value, "all")
        self._search_var.set("")
        self._refresh_left()

    def _check_orphans(self):
        orphans = get_orphaned_exh_nos()
        if orphans:
            self._orphan_btn.configure(
                text=f"  ⚠ {len(orphans)} entries have no matching exhibitor"
            )
            self._orphan_btn.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 4))
        else:
            self._orphan_btn.grid_remove()

    def _show_orphaned(self):
        self._search_var.set("")
        self._active_filter = "all"
        self._filter_seg.set("All")
        orphan_nos = set(get_orphaned_exh_nos())
        orphaned = [p for p in get_participants() if p.exh_no in orphan_nos]
        self._render_participant_list(orphaned)

    def _render_participant_list(self, rows: list[ParticipantRow], registry_extras=None):
        for child in self._list_frame.winfo_children():
            child.destroy()

        if not rows and not registry_extras:
            ctk.CTkLabel(
                self._list_frame, text="No participants found.",
                text_color=("gray45", "gray60"),
            ).pack(anchor="w", padx=4, pady=8)
            return

        for p in rows:
            sub = f"{p.entry_count} entries · {p.benched_count} benched"
            if p.late_count:
                sub += f" · {p.late_count} late"
            ctk.CTkButton(
                self._list_frame,
                text=f"#{p.exh_no}  {p.name}\n{sub}",
                anchor="w", height=52,
                fg_color=("gray82", "gray24"),
                text_color=("gray10", "gray90"),
                command=lambda _p=p: self._select_participant(_p),
            ).pack(fill="x", padx=2, pady=3)

        if registry_extras:
            ctk.CTkLabel(
                self._list_frame, text="Registry (not in this show):",
                font=ctk.CTkFont(size=10), text_color=("gray50", "gray55"),
            ).pack(anchor="w", padx=4, pady=(8, 2))
            for e in registry_extras:
                label = f"+ {e.name}"
                if e.exh_no:
                    label = f"#{e.exh_no}  {e.name}"
                ctk.CTkButton(
                    self._list_frame,
                    text=label,
                    anchor="w", height=36,
                    fg_color=("gray88", "gray20"),
                    text_color=("gray30", "gray60"),
                    command=lambda _e=e: self._add_registry_exhibitor(_e),
                ).pack(fill="x", padx=2, pady=2)

    def _add_registry_exhibitor(self, exhibitor):
        if exhibitor.exh_no is None:
            new_no = next_available_exh_no()
            assign_exh_no(exhibitor.id, new_no)
            self._refresh_left()
            updated = next(
                (p for p in self._participants if p.exh_no == new_no), None
            )
            if updated:
                self._select_participant(updated)
        else:
            self._select_participant(ParticipantRow(
                exhibitor_id=exhibitor.id,
                exh_no=exhibitor.exh_no,
                name=exhibitor.name,
                email=exhibitor.email,
                entry_count=0, benched_count=0, late_count=0,
            ))

    def _open_enrol_dialog(self):
        from views._enrol_dialog import EnrolDialog
        dlg = EnrolDialog(self)
        self.wait_window(dlg)
        self._refresh_left()

    # ── Right panel logic ─────────────────────────────────────────────────────

    def _select_participant(self, p: ParticipantRow):
        self._selected = p
        self._right_header.configure(
            text=f"#{p.exh_no}  {p.name}  ·  {p.entry_count} entries · {p.benched_count} benched"
        )
        self._load_entries()

    def _load_entries(self):
        for child in self._entries_frame.winfo_children():
            child.destroy()
        self._entry_vars = {}
        if self._selected is None:
            return

        self._entry_rows = get_participant_entries(self._selected.exh_no)

        if self._needs_recalc:
            self._recalc_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 4))
        else:
            self._recalc_frame.grid_remove()

        if not self._entry_rows:
            ctk.CTkLabel(
                self._entries_frame,
                text="No entries yet. Use '+ Add Entry' to begin.",
                text_color=("gray45", "gray60"),
            ).pack(anchor="w", padx=8, pady=8)
            return

        self._entries_frame.grid_columnconfigure(2, weight=1)
        headers = [("Bench", 56), ("Class", 80), ("Description", 0), ("Status", 180)]
        for col, (h, w) in enumerate(headers):
            ctk.CTkLabel(
                self._entries_frame, text=h,
                width=w if w else 1,
                font=ctk.CTkFont(size=11, weight="bold"),
                anchor="w",
            ).grid(row=0, column=col, sticky="ew" if w == 0 else "w", padx=4, pady=4)

        for row_i, row in enumerate(self._entry_rows, start=1):
            key = (row.source_auto_num, row.is_late)
            var = ctk.BooleanVar(value=False)
            self._entry_vars[key] = var
            disabled = row.blocked_reason is not None
            ctk.CTkCheckBox(
                self._entries_frame, text="", variable=var, width=48,
                state="disabled" if disabled else "normal",
            ).grid(row=row_i, column=0, sticky="w", padx=4, pady=2)
            ctk.CTkLabel(
                self._entries_frame,
                text=row.class_code or "", width=80, anchor="w",
            ).grid(row=row_i, column=1, sticky="w", padx=4, pady=2)
            ctk.CTkLabel(
                self._entries_frame,
                text=(row.class_desc or "")[:40], anchor="w",
            ).grid(row=row_i, column=2, sticky="ew", padx=4, pady=2)
            ctk.CTkLabel(
                self._entries_frame,
                text=row.status, width=180, anchor="w",
                text_color=self._status_color(row.status),
            ).grid(row=row_i, column=3, sticky="w", padx=4, pady=2)

    def _status_color(self, status: str) -> tuple:
        if "Benched" in status:
            return ("green4", "lightgreen")
        if "LATE" in status and "Benched" not in status:
            return ("orange3", "orange")
        if status in ("Has result", "NB", "Special winner"):
            return ("red4", "tomato")
        return ("gray40", "gray60")

    def _select_all_unbenched(self):
        for row in self._entry_rows:
            if row.auto_num is None and row.blocked_reason is None:
                self._entry_vars[(row.source_auto_num, row.is_late)].set(True)

    def _clear_selection(self):
        for var in self._entry_vars.values():
            var.set(False)

    def _bench_selected(self):
        show_keys = [k[0] for k, v in self._entry_vars.items() if v.get() and not k[1]]
        late_keys = [k[0] for k, v in self._entry_vars.items() if v.get() and k[1]]
        bits = []
        if show_keys:
            r = bench_entries(show_keys)
            if r.created:
                bits.append(f"Benched {len(r.created)}")
        if late_keys:
            r = bench_late_entries(late_keys)
            if r.created:
                bits.append(f"Benched {len(r.created)} late")
        self._status.configure(text=", ".join(bits) if bits else "Nothing new to bench.")
        self._after_entry_change()

    def _unbench_selected(self):
        show_keys = [k[0] for k, v in self._entry_vars.items() if v.get() and not k[1]]
        late_keys = [k[0] for k, v in self._entry_vars.items() if v.get() and k[1]]
        bits = []
        if show_keys:
            r = unbench_entries(show_keys)
            if r.removed:
                bits.append(f"Unbenched {len(r.removed)}")
        if late_keys:
            r = unbench_late_entries(late_keys)
            if r.removed:
                bits.append(f"Unbenched {len(r.removed)} late")
        self._status.configure(text=", ".join(bits) if bits else "Nothing to unbench.")
        self._after_entry_change()

    def _open_add_entry(self):
        if self._selected is None:
            return
        from views._entry_dialog import EntryDialog
        dlg = EntryDialog(self, exh_no=self._selected.exh_no)
        self.wait_window(dlg)
        self._after_entry_change()

    def _open_add_late_entry(self):
        if self._selected is None:
            return
        from views._late_entry_dialog import LateEntryDialog
        dlg = LateEntryDialog(self, exh_no=self._selected.exh_no, name=self._selected.name)
        self.wait_window(dlg)
        self._after_entry_change()

    def _after_entry_change(self):
        calc_result = auto_calculate_if_safe()
        self._needs_recalc = calc_result == "warning"
        self._refresh_left()
        if self._selected:
            updated = next(
                (p for p in self._participants if p.exh_no == self._selected.exh_no),
                self._selected,
            )
            self._select_participant(updated)

    def _on_recalculate(self):
        from tkinter import messagebox
        ok = messagebox.askyesno(
            "Recalculate",
            "This will reassign bench numbers for all unbenched entries.\nContinue?",
            parent=self,
        )
        if ok:
            from services.calculate_service import calculate_entries
            calculate_entries()
            self._needs_recalc = False
            self._after_entry_change()
