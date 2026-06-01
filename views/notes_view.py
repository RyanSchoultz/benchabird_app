# views/notes_view.py
import customtkinter as ctk
from models.reference import NotesBrochure


class NotesView(ctk.CTkFrame):
    """Edit brochure notes per bird type."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._selected_id = None
        self._build()
        self._load_list()

    def _build(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Brochure Notes",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(16, 4)
        )

        self._list_frame = ctk.CTkScrollableFrame(
            self, width=180, fg_color=("gray88", "gray20")
        )
        self._list_frame.grid(row=1, column=0, sticky="nsew", padx=(16, 4), pady=(0, 16))
        self._list_frame.grid_columnconfigure(0, weight=1)

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=1, column=1, sticky="nsew", padx=(0, 16), pady=(0, 16))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(right, text="Notes:",
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self._text = ctk.CTkTextbox(right, font=ctk.CTkFont(family="Courier New", size=12))
        self._text.grid(row=1, column=0, sticky="nsew")
        ctk.CTkButton(right, text="Save Notes", width=120,
                      command=self._save).grid(row=2, column=0, pady=(8, 0), sticky="e")

    def _load_list(self):
        for w in self._list_frame.winfo_children():
            w.destroy()

        records = list(NotesBrochure.select().order_by(NotesBrochure.type_abbr))
        for row_i, r in enumerate(records):
            ctk.CTkButton(
                self._list_frame,
                text=r.type_abbr or "(no type)",
                anchor="w",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray80", "gray25"),
                font=ctk.CTkFont(size=12),
                command=lambda rid=r.id: self._select(rid),
            ).grid(row=row_i, column=0, sticky="ew", pady=1)

    def _select(self, rid: int):
        self._selected_id = rid
        r = NotesBrochure.get_by_id(rid)
        self._text.delete("1.0", "end")
        self._text.insert("1.0", r.notes or "")

    def _save(self):
        if not self._selected_id:
            return
        r = NotesBrochure.get_by_id(self._selected_id)
        r.notes = self._text.get("1.0", "end-1c")
        r.save()
