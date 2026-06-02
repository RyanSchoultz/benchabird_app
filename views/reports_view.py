# views/reports_view.py
import threading

import customtkinter as ctk

from models.reference import ShowDetails


class ReportsView(ctk.CTkFrame):
    """Generate and open PDF reports."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._include_late = ctk.BooleanVar(value=True)
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text="Reports",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))

        self._status = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
        )
        self._status.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 4))

        toggle_frame = ctk.CTkFrame(self, fg_color="transparent")
        toggle_frame.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 8))
        ctk.CTkSwitch(
            toggle_frame,
            text="Include late entries",
            variable=self._include_late,
            font=ctk.CTkFont(size=12),
        ).grid(row=0, column=0)

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.grid(row=3, column=0, padx=16)

        reports = [
            ("Entries Received", "benchabird_entries_received.pdf", self._gen_entries_received),
            ("Show Catalogue", "benchabird_show_catalogue.pdf", self._gen_show_catalogue),
            ("Results Sheet", "benchabird_results_sheet.pdf", self._gen_results_sheet),
            ("Special Winners", "benchabird_special_winners.pdf", self._gen_special_winners),
            ("Prize Money", "benchabird_prize_money.pdf", self._gen_prize_money),
            ("Address Tags", "benchabird_address_tags.pdf", self._gen_address_tags),
            ("Exhibitor List", "benchabird_exhibitor_list.pdf", self._gen_exhibitor_list),
            ("Entry Confirmation", "benchabird_entry_confirmation.pdf", self._gen_entry_confirmation),
            (
                "Results by Exhibitor",
                "benchabird_results_by_exhibitor.pdf",
                self._gen_results_by_exhibitor,
            ),
        ]

        for i, (label, _, cmd) in enumerate(reports):
            row, col = divmod(i, 3)
            ctk.CTkButton(
                grid,
                text=label,
                width=190,
                height=52,
                command=cmd,
            ).grid(row=row, column=col, padx=8, pady=8)

        self._reports = reports

    def _get_sd(self):
        return ShowDetails.select().first()

    def _save_and_open(self, gen_fn, default_name: str):
        self._status.configure(text=f"Generating {default_name}...")
        sd = self._get_sd()

        def run():
            try:
                pdf_bytes = gen_fn(sd=sd)
                self.after(0, lambda: self._show_preview(pdf_bytes, default_name))
            except Exception as e:
                self.after(0, lambda: self._on_error(str(e)))

        threading.Thread(target=run, daemon=True).start()

    def _show_preview(self, pdf_bytes: bytes, default_name: str):
        self._status.configure(text="")
        from views.pdf_preview_window import PDFPreviewWindow

        title = default_name.replace("benchabird_", "").replace(".pdf", "").replace("_", " ").title()
        PDFPreviewWindow(self, pdf_bytes, title, default_name)

    def _on_error(self, msg: str):
        self._status.configure(text=f"Error: {msg[:80]}")

    def _gen_entries_received(self):
        from services.reports.entries_received import generate_entries_received

        self._save_and_open(generate_entries_received, "benchabird_entries_received.pdf")

    def _gen_show_catalogue(self):
        from services.reports.show_catalogue import generate_show_catalogue

        self._save_and_open(generate_show_catalogue, "benchabird_show_catalogue.pdf")

    def _gen_results_sheet(self):
        from services.reports.results_sheet import generate_results_sheet

        self._save_and_open(generate_results_sheet, "benchabird_results_sheet.pdf")

    def _gen_special_winners(self):
        from services.reports.special_winners import generate_special_winners

        self._save_and_open(generate_special_winners, "benchabird_special_winners.pdf")

    def _gen_prize_money(self):
        from services.reports.prize_money import generate_prize_money

        self._save_and_open(generate_prize_money, "benchabird_prize_money.pdf")

    def _gen_address_tags(self):
        from services.reports.address_tags import generate_address_tags

        self._save_and_open(generate_address_tags, "benchabird_address_tags.pdf")

    def _gen_exhibitor_list(self):
        from services.reports.exhibitor_list import generate_exhibitor_list

        self._save_and_open(generate_exhibitor_list, "benchabird_exhibitor_list.pdf")

    def _gen_entry_confirmation(self):
        from services.reports.entry_confirmation import generate_entry_confirmation

        include_late = self._include_late.get()
        gen_fn = lambda sd: generate_entry_confirmation(sd=sd, include_late=include_late)
        self._save_and_open(gen_fn, "benchabird_entry_confirmation.pdf")

    def _gen_results_by_exhibitor(self):
        from services.reports.results_by_exhibitor import generate_results_by_exhibitor

        self._save_and_open(generate_results_by_exhibitor, "benchabird_results_by_exhibitor.pdf")
