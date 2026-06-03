# views/_enrol_dialog.py
import customtkinter as ctk
from services.show_participants_service import get_unenrolled_exhibitors, enrol_exhibitors


class EnrolDialog(ctk.CTkToplevel):
    """Bulk-enrol exhibitors into the current show by assigning sequential ExhNos."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Enrol Exhibitors for This Show")
        self.geometry("480x520")
        self.resizable(False, True)
        self.grab_set()
        self.after(50, self.lift)
        self._all_exhibitors = []
        self._vars: dict[int, ctk.BooleanVar] = {}
        self._build()
        self._load()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Filter bar
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 4))
        filter_frame.grid_columnconfigure(0, weight=1)
        self._filter_var = ctk.StringVar()
        self._filter_var.trace_add("write", lambda *_: self._apply_filter())
        ctk.CTkEntry(
            filter_frame, textvariable=self._filter_var,
            placeholder_text="Filter by name…",
        ).grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(
            filter_frame, text="✕", width=28, height=28,
            fg_color="transparent", text_color=("gray40", "gray60"),
            command=lambda: self._filter_var.set(""),
        ).grid(row=0, column=1, padx=(4, 0))

        # Select All row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=1, column=0, sticky="ew", padx=16, pady=(4, 0))
        self._select_all_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            header, text="Select All",
            variable=self._select_all_var,
            command=self._toggle_all,
        ).pack(side="left")
        self._count_lbl = ctk.CTkLabel(
            header, text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
        )
        self._count_lbl.pack(side="right")

        # Scrollable exhibitor list
        self._list = ctk.CTkScrollableFrame(self)
        self._list.grid(row=2, column=0, sticky="nsew", padx=16, pady=8)
        self._list.grid_columnconfigure(1, weight=1)

        # Buttons
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.grid(row=3, column=0, pady=(4, 16))
        ctk.CTkButton(
            btns, text="Cancel", width=110,
            fg_color="transparent", border_width=1,
            command=self.destroy,
        ).pack(side="left", padx=8)
        self._enrol_btn = ctk.CTkButton(
            btns, text="Enrol Selected (0)", width=180,
            command=self._enrol,
            state="disabled",
        )
        self._enrol_btn.pack(side="left", padx=8)
        self.bind("<Escape>", lambda e: self.destroy())

    def _load(self):
        self._all_exhibitors = get_unenrolled_exhibitors()
        self._vars = {e.id: ctk.BooleanVar(value=False) for e in self._all_exhibitors}
        self._apply_filter()

    def _apply_filter(self):
        q = self._filter_var.get().strip().lower()
        visible = [
            e for e in self._all_exhibitors
            if not q or q in (e.name or "").lower()
        ]
        for child in self._list.winfo_children():
            child.destroy()
        for row_i, exhibitor in enumerate(visible):
            var = self._vars[exhibitor.id]
            row = ctk.CTkFrame(self._list, fg_color="transparent")
            row.grid(row=row_i, column=0, sticky="ew", pady=1)
            row.grid_columnconfigure(1, weight=1)
            ctk.CTkCheckBox(
                row, text="", variable=var, width=32,
                command=self._update_counts,
            ).grid(row=0, column=0, padx=(0, 8))
            ctk.CTkLabel(
                row, text=exhibitor.name or "", anchor="w",
            ).grid(row=0, column=1, sticky="w")
            ctk.CTkLabel(
                row,
                text=exhibitor.town or "",
                font=ctk.CTkFont(size=11),
                text_color=("gray40", "gray60"),
                anchor="e",
            ).grid(row=0, column=2, sticky="e", padx=(8, 0))
        total_left = len(self._all_exhibitors)
        self._count_lbl.configure(text=f"{total_left} unenrolled")
        self._update_counts()

    def _toggle_all(self):
        state = self._select_all_var.get()
        q = self._filter_var.get().strip().lower()
        for e in self._all_exhibitors:
            if not q or q in (e.name or "").lower():
                self._vars[e.id].set(state)
        self._update_counts()

    def _update_counts(self):
        selected = sum(1 for v in self._vars.values() if v.get())
        if selected:
            self._enrol_btn.configure(
                text=f"Enrol Selected ({selected})", state="normal",
            )
        else:
            self._enrol_btn.configure(text="Enrol Selected (0)", state="disabled")

    def _enrol(self):
        selected_ids = [eid for eid, v in self._vars.items() if v.get()]
        if not selected_ids:
            return
        enrol_exhibitors(selected_ids)
        self.destroy()
