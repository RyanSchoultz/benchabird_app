# views/_exhibitor_dialog.py
import customtkinter as ctk
from controllers.exhibitor_ctrl import save
from repository.exhibitor_repo import ExhibitorRepo

_repo = ExhibitorRepo()

FIELDS = [
    ("exh_no",   "Exhibitor #",  "int"),
    ("name",     "Full Name",    "str"),
    ("address",  "Address",      "str"),
    ("suburb",   "Suburb",       "str"),
    ("town",     "Town",         "str"),
    ("zip_code", "Zip Code",     "str"),
    ("tel_home", "Tel (Home)",   "str"),
    ("cell_no",  "Cell",         "str"),
    ("email",    "Email",        "str"),
    ("club",     "Club Code",    "str"),
]


class ExhibitorDialog(ctk.CTkToplevel):
    def __init__(self, parent, pk):
        super().__init__(parent)
        self._pk = pk
        self.title("Add Exhibitor" if pk is None else "Edit Exhibitor")
        self.geometry("420x520")
        self.resizable(False, False)
        self.grab_set()
        self._entries: dict = {}
        self._build()
        if pk:
            self._populate(_repo.get_by_id(pk))

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        scroll = ctk.CTkScrollableFrame(self)
        scroll.grid(row=0, column=0, sticky="nsew", padx=16, pady=12)
        scroll.grid_columnconfigure(1, weight=1)

        for row, (field, label, _) in enumerate(FIELDS):
            ctk.CTkLabel(scroll, text=label, anchor="e").grid(row=row, column=0, sticky="e", padx=(0, 8), pady=3)
            ent = ctk.CTkEntry(scroll)
            ent.grid(row=row, column=1, sticky="ew", pady=3)
            self._entries[field] = ent

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, pady=(4, 12))
        ctk.CTkButton(btn_frame, text="Save", width=110, command=self._save).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="Cancel", width=110,
                      fg_color="transparent", border_width=1,
                      command=self.destroy).pack(side="left", padx=8)

    def _populate(self, exhibitor):
        for field, _, typ in FIELDS:
            val = getattr(exhibitor, field, None)
            if val is not None:
                self._entries[field].insert(0, str(val))

    def _save(self):
        data = {}
        for field, _, typ in FIELDS:
            raw = self._entries[field].get().strip()
            data[field] = int(raw) if typ == "int" and raw else (raw or None)
        save(self._pk, data)
        self.destroy()
