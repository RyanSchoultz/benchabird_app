# views/tickets_view.py
import threading
import customtkinter as ctk
from tkinter import filedialog
import subprocess
import sys
from services.ticket_service import get_ticket_assignments
from services.ticket_pdf_service import generate_ticket_pdf
from models.reference import ShowDetails
from views._paginated_table import PaginatedTable


def _matches(cells: list, q: str) -> bool:
    return any(q in c.lower() for c in cells)


class TicketsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._all_data: list = []
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        ctk.CTkLabel(toolbar, text="Tickets",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        ctk.CTkButton(toolbar, text="Export", width=80,
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=self._export).pack(side="right", padx=4)
        self._print_btn = ctk.CTkButton(
            toolbar, text="Print All Tickets",
            command=self._start_print,
        )
        self._print_btn.pack(side="right")

        self._status = ctk.CTkLabel(toolbar, text="",
                                    font=ctk.CTkFont(size=11),
                                    text_color=("gray40", "gray60"))
        self._status.pack(side="left", padx=12)

        # Filter bar
        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 2))
        self._filter_var = ctk.StringVar()
        self._filter_var.trace_add("write", lambda *_: self._apply_filter())
        ctk.CTkEntry(
            filter_bar, textvariable=self._filter_var,
            placeholder_text="Filter by ExhNo, class desc, or class…", width=280,
        ).pack(side="left")
        ctk.CTkButton(
            filter_bar, text="✕", width=28, height=28,
            fg_color="transparent", text_color=("gray40", "gray60"),
            command=lambda: self._filter_var.set(""),
        ).pack(side="left", padx=4)

        self._table = PaginatedTable(
            self,
            headers=["Ticket #", "AutoNum", "ExhNo", "Class Desc", "Class"],
            selectable=False,
        )
        self._table.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self._load_data()

    def _load_data(self):
        tickets = get_ticket_assignments()
        if tickets:
            self._all_data = [
                (t['ticket_no'], [
                    str(t['ticket_no']), str(t['auto_num']),
                    str(t['exh_no'] or ""), t['class_desc'] or "", t['class_code'] or "",
                ])
                for t in tickets
            ]
            self._apply_filter()
        else:
            self._all_data = []
            self._table.load([])
            self._status.configure(text="Bench birds in Show Participants first to generate tickets.")

    def _apply_filter(self):
        q = self._filter_var.get().strip().lower()
        data = [row for row in self._all_data if not q or _matches(row[1], q)]
        self._table.load(data)
        total = len(self._all_data)
        shown = len(data)
        self._status.configure(
            text=f"{shown} of {total} tickets" if q else f"{total} tickets"
        )

    def _start_print(self):
        tickets = get_ticket_assignments()
        if not tickets:
            self._status.configure(text="No tickets — run Calculate first.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile="benchabird_tickets.pdf",
            title="Save Ticket PDF",
        )
        if not path:
            return

        self._print_btn.configure(state="disabled", text="Generating…")
        sd = ShowDetails.select().first()
        show_name = f"{sd.show_eng} {sd.date_eng}" if sd else "Bird Show"
        logo_data = bytes(sd.logo_data) if sd and getattr(sd, 'logo_data', None) else None
        barcode_type = getattr(sd, 'barcode_type', None) or "QR" if sd else "QR"
        threading.Thread(
            target=self._generate, args=(tickets, show_name, logo_data, barcode_type, path), daemon=True
        ).start()

    def _generate(self, tickets: list, show_name: str, logo_data: bytes, barcode_type: str, path: str):
        try:
            pdf_bytes = generate_ticket_pdf(tickets, show_name=show_name, logo_data=logo_data, barcode_type=barcode_type)
            with open(path, "wb") as f:
                f.write(pdf_bytes)
            self.after(0, lambda: self._on_done(path))
        except Exception as e:
            self.after(0, lambda: self._on_error(str(e)))

    def _on_done(self, path: str):
        self._print_btn.configure(state="normal", text="Print All Tickets")
        self._status.configure(text=f"Saved: {path}")
        if sys.platform == "win32":
            subprocess.Popen(["start", "", path], shell=True)

    def _on_error(self, msg: str):
        self._print_btn.configure(state="normal", text="Print All Tickets")
        self._status.configure(text=f"Error: {msg[:60]}")

    def _export(self):
        from services.export_service import export_data
        rows = [list(cells) for _, cells in self._all_data]
        export_data(rows, ["TicketNo", "AutoNum", "ExhNo", "ClassDesc", "Class"], "tickets.csv")
