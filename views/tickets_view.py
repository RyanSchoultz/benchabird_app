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


class TicketsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        ctk.CTkLabel(toolbar, text="Tickets",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        self._print_btn = ctk.CTkButton(
            toolbar, text="Print All Tickets",
            command=self._start_print,
        )
        self._print_btn.pack(side="right")

        self._status = ctk.CTkLabel(toolbar, text="",
                                    font=ctk.CTkFont(size=11),
                                    text_color=("gray40", "gray60"))
        self._status.pack(side="left", padx=12)

        self._table = PaginatedTable(
            self,
            headers=["Ticket #", "AutoNum", "ExhNo", "Name", "Class"],
            selectable=False,
        )
        self._table.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

        tickets = get_ticket_assignments()
        if tickets:
            data = [
                (t['ticket_no'], [
                    str(t['ticket_no']), str(t['auto_num']),
                    str(t['exh_no'] or ""), t['name'] or "", t['class_code'] or "",
                ])
                for t in tickets
            ]
            self._table.load(data)
            self._status.configure(text=f"{len(data)} tickets")
        else:
            self._table.load([])
            self._status.configure(text="Run Calculate first to generate tickets.")

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
        threading.Thread(
            target=self._generate, args=(tickets, show_name, path), daemon=True
        ).start()

    def _generate(self, tickets: list, show_name: str, path: str):
        try:
            pdf_bytes = generate_ticket_pdf(tickets, show_name=show_name)
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
