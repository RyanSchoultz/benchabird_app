# views/notes_view.py
import customtkinter as ctk

from services.class_glossary_service import list_class_glossary, list_species_filters

MAX_GLOSSARY_RENDER_ROWS = 250
FILTER_DEBOUNCE_MS = 250


def visible_glossary_rows(rows):
    return rows[:MAX_GLOSSARY_RENDER_ROWS]


class NotesView(ctk.CTkFrame):
    """Read-only class description glossary."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._rows = []
        self._reload_job = None
        self._build()
        self._reload()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        ctk.CTkLabel(
            toolbar,
            text="Class Glossary",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left")
        self._status = ctk.CTkLabel(
            toolbar,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
        )
        self._status.pack(side="left", padx=12)

        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 4))
        self._species_var = ctk.StringVar(value="All species")
        species_options = ["All species", *list_species_filters()]
        ctk.CTkOptionMenu(
            filter_bar,
            variable=self._species_var,
            values=species_options or ["All species"],
            width=220,
            command=lambda _: self._reload(),
        ).pack(side="left", padx=(0, 8))
        self._filter_var = ctk.StringVar()
        self._filter_var.trace_add("write", lambda *_: self._schedule_reload())
        ctk.CTkEntry(
            filter_bar,
            textvariable=self._filter_var,
            placeholder_text="Filter by class, type, main class, or description...",
            width=360,
        ).pack(side="left")
        ctk.CTkButton(
            filter_bar,
            text="x",
            width=28,
            height=28,
            fg_color="transparent",
            text_color=("gray40", "gray60"),
            command=lambda: self._filter_var.set(""),
        ).pack(side="left", padx=4)

        self._table = ctk.CTkScrollableFrame(self, fg_color=("gray88", "gray18"))
        self._table.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))
        for col, weight in enumerate([0, 1, 1, 2, 1]):
            self._table.grid_columnconfigure(col, weight=weight)

    def _schedule_reload(self):
        if self._reload_job is not None:
            self.after_cancel(self._reload_job)
        self._reload_job = self.after(FILTER_DEBOUNCE_MS, self._reload)

    def _reload(self):
        self._reload_job = None
        for child in self._table.winfo_children():
            child.destroy()
        query = self._filter_var.get().strip()
        species = self._species_var.get()
        species_heading = "" if species == "All species" else species
        self._rows = list_class_glossary(query, species_heading=species_heading)
        visible_rows = visible_glossary_rows(self._rows)

        headers = ["Class", "Type", "Main Class", "Description", "Extra"]
        widths = [80, 180, 180, 300, 160]
        for col, (header, width) in enumerate(zip(headers, widths)):
            ctk.CTkLabel(
                self._table,
                text=header,
                width=width,
                font=ctk.CTkFont(size=11, weight="bold"),
                anchor="w",
            ).grid(row=0, column=col, sticky="w", padx=6, pady=(6, 4))

        if not self._rows:
            message = "No matching classes." if query else "No class definitions found. Import legacy data or add classes first."
            ctk.CTkLabel(
                self._table,
                text=message,
                text_color=("gray45", "gray60"),
            ).grid(row=1, column=0, columnspan=5, sticky="w", padx=8, pady=12)
            self._status.configure(text="0 classes")
            return

        grid_row = 1
        last_species = None
        for row in visible_rows:
            if row.species_heading != last_species:
                ctk.CTkLabel(
                    self._table,
                    text=row.species_heading or "Unspecified",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    anchor="w",
                    text_color=("gray20", "gray80"),
                ).grid(row=grid_row, column=0, columnspan=5, sticky="ew", padx=6, pady=(10, 2))
                grid_row += 1
                last_species = row.species_heading
            values = [
                row.class_code,
                row.bird_type,
                row.main_class,
                row.description,
                row.extra,
            ]
            for col, value in enumerate(values):
                ctk.CTkLabel(
                    self._table,
                    text=value,
                    anchor="w",
                    justify="left",
                    wraplength=[80, 180, 180, 300, 160][col],
                ).grid(row=grid_row, column=col, sticky="nw", padx=6, pady=3)
            grid_row += 1

        suffix = "matching classes" if query else "classes"
        status = f"{len(self._rows)} {suffix}"
        if len(visible_rows) < len(self._rows):
            status += f" - showing first {len(visible_rows)}; filter to narrow"
        self._status.configure(text=status)
