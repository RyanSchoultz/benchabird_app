# views/search_view.py
import customtkinter as ctk

_DIM = ("gray55", "gray50")
_LINK = ("steelblue", "cornflowerblue")


def _nav(widget, key: str):
    widget.winfo_toplevel().navigate(key)


class SearchView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._after_id = None
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        hdr = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray88", "gray18"))
        hdr.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            hdr, text="Search", font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left", padx=20, pady=14)

        search_bar = ctk.CTkFrame(self, fg_color="transparent")
        search_bar.grid(row=1, column=0, sticky="ew", padx=40, pady=(20, 8))
        search_bar.grid_columnconfigure(0, weight=1)

        self._var = ctk.StringVar()
        self._var.trace_add("write", self._on_change)
        self._entry = ctk.CTkEntry(
            search_bar, textvariable=self._var,
            placeholder_text="Search exhibitors, entries, class codes, results…",
            font=ctk.CTkFont(size=15), height=44,
        )
        self._entry.grid(row=0, column=0, sticky="ew")
        self._entry.focus()

        self._results_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._results_frame.grid(row=2, column=0, sticky="nsew", padx=40, pady=(0, 20))
        self._results_frame.grid_columnconfigure(0, weight=1)

        self._show_hint("Type to search across all show data…")

    def _on_change(self, *_):
        if self._after_id:
            self.after_cancel(self._after_id)
        q = self._var.get().strip()
        if not q:
            self._show_hint("Type to search across all show data…")
            return
        self._after_id = self.after(3000, lambda: self._run_search(q))

    def _run_search(self, q: str):
        from services.search_service import global_search
        self._render(q, global_search(q))

    def _clear_results(self):
        for w in self._results_frame.winfo_children():
            w.destroy()

    def _show_hint(self, text: str):
        self._clear_results()
        ctk.CTkLabel(
            self._results_frame, text=text,
            font=ctk.CTkFont(size=13), text_color=_DIM,
        ).grid(row=0, column=0, pady=40)

    def _render(self, q: str, data: dict):
        self._clear_results()
        total = sum([
            data["exhibitors_total"], data["entries_total"],
            data["calc_total"], data["results_total"], data["specials_total"],
        ])
        if total == 0:
            ctk.CTkLabel(
                self._results_frame, text=f'No results for "{q}"',
                font=ctk.CTkFont(size=13), text_color=_DIM,
            ).grid(row=0, column=0, pady=40)
            return

        row = 0

        if data["exhibitors"]:
            row = self._section(f"Exhibitors  ({data['exhibitors_total']})", row)
            for e in data["exhibitors"]:
                sub = e["town"]
                if e["email"]:
                    sub += f"  ·  {e['email']}"
                row = self._result_row(
                    f"#{e['exh_no']}  {e['name']}", sub,
                    lambda: _nav(self, "exhibitors"), row,
                )
            if data["exhibitors_total"] > len(data["exhibitors"]):
                row = self._link_row(
                    f"View all {data['exhibitors_total']} exhibitors →",
                    "exhibitors", row,
                )

        if data["entries"]:
            row = self._section(f"Show Entries  ({data['entries_total']})", row)
            for e in data["entries"]:
                row = self._result_row(
                    f"Entry #{e['auto_num']}  ·  ExhNo {e['exh_no']}  ·  {e['class_code']}",
                    "", lambda: _nav(self, "entries"), row,
                )
            if data["entries_total"] > len(data["entries"]):
                row = self._link_row(
                    f"View all {data['entries_total']} entries →", "entries", row,
                )

        if data["calc_entries"]:
            row = self._section(f"Calculated Entries  ({data['calc_total']})", row)
            for e in data["calc_entries"]:
                row = self._result_row(
                    f"Exhibit #{e['auto_num']}  ·  {e['name']}  ·  {e['class_code']}",
                    f"ExhNo {e['exh_no']}",
                    lambda: _nav(self, "entries"), row,
                )
            if data["calc_total"] > len(data["calc_entries"]):
                row = self._link_row(
                    f"View all {data['calc_total']} calculated entries →", "entries", row,
                )

        if data["results"]:
            row = self._section(f"Results  ({data['results_total']})", row)
            for r in data["results"]:
                row = self._result_row(
                    f"Exhibit #{r['exhibit_no']}  →  {r['result']}",
                    "", lambda: _nav(self, "results"), row,
                )
            if data["results_total"] > len(data["results"]):
                row = self._link_row(
                    f"View all {data['results_total']} results →", "results", row,
                )

        if data["specials"]:
            row = self._section(f"Special Prizes  ({data['specials_total']})", row)
            for s in data["specials"]:
                row = self._result_row(
                    f"{s['special_nr']}  {s['description']}",
                    s["prize"], lambda: _nav(self, "special_list"), row,
                )
            if data["specials_total"] > len(data["specials"]):
                row = self._link_row(
                    f"View all {data['specials_total']} special prizes →", "special_list", row,
                )

    def _section(self, text: str, row: int) -> int:
        ctk.CTkLabel(
            self._results_frame, text=text,
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
        ).grid(row=row, column=0, sticky="ew", pady=(14, 2))
        ctk.CTkFrame(
            self._results_frame, height=1, fg_color=("gray75", "gray35")
        ).grid(row=row + 1, column=0, sticky="ew")
        return row + 2

    def _result_row(self, main: str, sub: str, command, row: int) -> int:
        card = ctk.CTkFrame(
            self._results_frame, corner_radius=6, fg_color=("gray88", "gray20")
        )
        card.grid(row=row, column=0, sticky="ew", pady=2)
        card.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="ew", padx=12, pady=(6, 4))
        inner.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(inner, text=main, anchor="w", font=ctk.CTkFont(size=12)).grid(
            row=0, column=0, sticky="w"
        )
        if sub:
            ctk.CTkLabel(
                inner, text=sub, anchor="w",
                font=ctk.CTkFont(size=11), text_color=_DIM,
            ).grid(row=1, column=0, sticky="w")

        ctk.CTkButton(
            card, text="→", width=40, height=36,
            fg_color=("gray78", "gray30"), text_color=("gray20", "gray80"),
            command=command,
        ).grid(row=0, column=1, padx=8, pady=4)
        return row + 1

    def _link_row(self, text: str, key: str, row: int) -> int:
        ctk.CTkButton(
            self._results_frame, text=text, anchor="w",
            fg_color="transparent", text_color=_LINK,
            hover_color=("gray85", "gray22"),
            font=ctk.CTkFont(size=12),
            command=lambda k=key: _nav(self, k),
        ).grid(row=row, column=0, sticky="ew", pady=2)
        return row + 1
