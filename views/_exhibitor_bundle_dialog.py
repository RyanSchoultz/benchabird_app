import threading

import customtkinter as ctk

from models.exhibitor import Exhibitor
from services.reports.exhibitor_bundle import (
    ExhibitorBundleError,
    generate_exhibitor_bundle,
)


class ExhibitorBundleDialog(ctk.CTkToplevel):
    def __init__(self, parent, sd, on_pdf):
        super().__init__(parent)
        self._sd = sd
        self._on_pdf = on_pdf
        self._selected_exh_no = None
        self.title("Exhibitor Bundle")
        self.geometry("640x520")
        self.minsize(520, 420)
        self._build()
        self._load()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(
            self,
            text="Print Exhibitor Bundle",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._load())
        ctk.CTkEntry(
            self,
            textvariable=self._search_var,
            placeholder_text="Search by exhibitor number, name, email, or club",
        ).grid(row=1, column=0, sticky="ew", padx=16, pady=8)

        self._list = ctk.CTkScrollableFrame(self)
        self._list.grid(row=2, column=0, sticky="nsew", padx=16, pady=8)
        self._list.grid_columnconfigure(0, weight=1)

        options = ctk.CTkFrame(self, fg_color="transparent")
        options.grid(row=3, column=0, sticky="ew", padx=16, pady=4)
        self._include_tickets = ctk.BooleanVar(value=True)
        self._include_late = ctk.BooleanVar(value=True)
        self._include_results = ctk.BooleanVar(value=True)
        self._include_address = ctk.BooleanVar(value=True)
        for text, var in [
            ("Tickets", self._include_tickets),
            ("Late entries", self._include_late),
            ("Results", self._include_results),
            ("Address label", self._include_address),
        ]:
            ctk.CTkCheckBox(options, text=text, variable=var).pack(side="left", padx=6)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=4, column=0, sticky="ew", padx=16, pady=(4, 16))
        self._status = ctk.CTkLabel(bottom, text="", font=ctk.CTkFont(size=11))
        self._status.pack(side="left")
        self._generate_btn = ctk.CTkButton(
            bottom,
            text="Generate Bundle",
            state="disabled",
            command=self._generate,
        )
        self._generate_btn.pack(side="right")

    def _load(self):
        for child in self._list.winfo_children():
            child.destroy()
        q = self._search_var.get().strip().lower()
        rows = list(Exhibitor.select().order_by(Exhibitor.exh_no))
        if q:
            rows = [
                e
                for e in rows
                if q in str(e.exh_no or "").lower()
                or q in (e.name or "").lower()
                or q in (e.email or "").lower()
                or q in (e.club or "").lower()
            ]
        if not rows:
            ctk.CTkLabel(self._list, text="No matching exhibitors.").grid(
                row=0, column=0, sticky="w", padx=8, pady=8
            )
            return
        for index, exhibitor in enumerate(rows[:100]):
            label = f"#{exhibitor.exh_no or ''}  {exhibitor.name or ''}  {exhibitor.club or ''}"
            ctk.CTkButton(
                self._list,
                text=label,
                anchor="w",
                fg_color=("gray85", "gray25"),
                text_color=("gray10", "gray90"),
                command=lambda exh_no=exhibitor.exh_no: self._select(exh_no),
            ).grid(row=index, column=0, sticky="ew", padx=4, pady=3)

    def _select(self, exh_no):
        self._selected_exh_no = exh_no
        self._status.configure(text=f"Selected exhibitor #{exh_no}")
        self._generate_btn.configure(state="normal")

    def _generate(self):
        if self._selected_exh_no is None:
            return
        self._generate_btn.configure(state="disabled", text="Generating...")

        def run():
            try:
                pdf = generate_exhibitor_bundle(
                    self._selected_exh_no,
                    sd=self._sd,
                    include_tickets=self._include_tickets.get(),
                    include_late=self._include_late.get(),
                    include_results=self._include_results.get(),
                    include_address_label=self._include_address.get(),
                )
                self.after(0, lambda: self._done(pdf))
            except ExhibitorBundleError as exc:
                self.after(0, lambda: self._error(str(exc)))

        threading.Thread(target=run, daemon=True).start()

    def _done(self, pdf):
        self._generate_btn.configure(state="normal", text="Generate Bundle")
        self._on_pdf(pdf, f"benchabird_exhibitor_{self._selected_exh_no}_bundle.pdf")
        self.destroy()

    def _error(self, message):
        self._generate_btn.configure(state="normal", text="Generate Bundle")
        self._status.configure(text=message[:90])
