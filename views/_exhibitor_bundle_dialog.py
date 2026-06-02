import threading

import customtkinter as ctk
from services.reports.exhibitor_bundle import (
    BundleExhibitorMatch,
    ExhibitorBundleError,
    generate_exhibitor_bundle_for_exhibitor,
    search_exhibitors_for_bundle,
)


def _exhibitor_number_text(exh_no) -> str:
    return str(exh_no) if exh_no is not None else "not assigned"


def format_selected_summary(match: BundleExhibitorMatch) -> str:
    exhibitor = match.exhibitor
    parts = [
        f"Selected: {exhibitor.name or '(unnamed exhibitor)'}",
        f"Exhibitor #: {_exhibitor_number_text(exhibitor.exh_no)}",
        f"Entries: {match.entry_count}",
    ]
    if match.matching_exhibit_no is not None:
        parts.append(f"Matching exhibit #: {match.matching_exhibit_no}")
    return " | ".join(parts)


def _result_button_text(match: BundleExhibitorMatch) -> str:
    name = match.exhibitor.name or "(unnamed exhibitor)"
    return f"Generate Bundle for {name[:32]}"


class ExhibitorBundleDialog(ctk.CTkToplevel):
    def __init__(self, parent, sd, on_pdf):
        super().__init__(parent)
        self._sd = sd
        self._on_pdf = on_pdf
        self._selected_match = None
        self._matches = []
        self._row_buttons = {}
        self.title("Exhibitor Bundle")
        self.geometry("700x590")
        self.minsize(560, 460)
        self._build()
        self._load()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
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
            placeholder_text="Search by name, exhibitor #, exhibit #, email, or club",
        ).grid(row=1, column=0, sticky="ew", padx=16, pady=(8, 4))
        self.bind("<Return>", lambda _event: self._select_first())

        self._selected_panel = ctk.CTkFrame(self, fg_color=("gray88", "gray20"), corner_radius=8)
        self._selected_panel.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 8))
        self._selected_panel.grid_columnconfigure(0, weight=1)
        self._selected_label = ctk.CTkLabel(
            self._selected_panel,
            text="No exhibitor selected.",
            anchor="w",
            justify="left",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self._selected_label.grid(row=0, column=0, sticky="ew", padx=12, pady=10)

        self._list = ctk.CTkScrollableFrame(self)
        self._list.grid(row=3, column=0, sticky="nsew", padx=16, pady=8)
        self._list.grid_columnconfigure(0, weight=1)

        options = ctk.CTkFrame(self, fg_color="transparent")
        options.grid(row=4, column=0, sticky="ew", padx=16, pady=4)
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
        bottom.grid(row=5, column=0, sticky="ew", padx=16, pady=(4, 16))
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
        self._row_buttons = {}
        q = self._search_var.get().strip().lower()
        self._matches = search_exhibitors_for_bundle(q)
        if not self._matches:
            ctk.CTkLabel(self._list, text="No matching exhibitors.").grid(
                row=0, column=0, sticky="w", padx=8, pady=8
            )
            return
        for index, match in enumerate(self._matches):
            exhibitor = match.exhibitor
            detail = f"Exhibitor #: {_exhibitor_number_text(exhibitor.exh_no)}"
            if match.matching_exhibit_no is not None:
                detail += f"  |  Exhibit #: {match.matching_exhibit_no}"
            detail += f"  |  Entries: {match.entry_count}"
            if exhibitor.club:
                detail += f"  |  {exhibitor.club}"
            label = f"{exhibitor.name or '(unnamed exhibitor)'}\n{detail}"
            button = ctk.CTkButton(
                self._list,
                text=label,
                anchor="w",
                height=48,
                fg_color=("gray85", "gray25"),
                text_color=("gray10", "gray90"),
                command=lambda item=match: self._select(item),
            )
            button.grid(row=index, column=0, sticky="ew", padx=4, pady=3)
            self._row_buttons[exhibitor.id] = button
        self._refresh_row_highlight()

    def _select_first(self):
        if self._matches:
            self._select(self._matches[0])
        return "break"

    def _select(self, match):
        self._selected_match = match
        self._selected_label.configure(text=format_selected_summary(match))
        self._status.configure(text="")
        self._generate_btn.configure(state="normal")
        self._generate_btn.configure(text=_result_button_text(match))
        self._refresh_row_highlight()

    def _refresh_row_highlight(self):
        selected_id = (
            self._selected_match.exhibitor.id
            if self._selected_match is not None
            else None
        )
        for exhibitor_id, button in self._row_buttons.items():
            if exhibitor_id == selected_id:
                button.configure(fg_color=("gray65", "gray38"))
            else:
                button.configure(fg_color=("gray85", "gray25"))

    def _generate(self):
        if self._selected_match is None:
            return
        self._generate_btn.configure(state="disabled", text="Generating...")

        def run():
            try:
                pdf = generate_exhibitor_bundle_for_exhibitor(
                    self._selected_match.exhibitor.id,
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
        exhibitor = self._selected_match.exhibitor
        filename_part = exhibitor.exh_no if exhibitor.exh_no is not None else exhibitor.id
        self._on_pdf(pdf, f"benchabird_exhibitor_{filename_part}_bundle.pdf")
        self.destroy()

    def _error(self, message):
        self._generate_btn.configure(state="normal", text="Generate Bundle")
        self._status.configure(text=message[:90])
