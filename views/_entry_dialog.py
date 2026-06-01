# views/_entry_dialog.py
import customtkinter as ctk
from services.entry_service import add_entry, EntryValidationError
from models.show_entry import ShowEntry


def _load_class_codes() -> list:
    from models.class_def import ClassDef
    return [c.class_code for c in ClassDef.select().order_by(ClassDef.class_code) if c.class_code]


class EntryDialog(ctk.CTkToplevel):
    """Add a single show entry."""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Add Show Entry")
        self.geometry("360x240")
        self.resizable(False, False)
        self.grab_set()
        self._class_codes = _load_class_codes()
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.grid(row=0, column=0, padx=20, pady=(20, 4), sticky="ew")
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Exhibitor #:", anchor="e").grid(
            row=0, column=0, sticky="e", padx=(0, 8), pady=6
        )
        self._exh_entry = ctk.CTkEntry(form, placeholder_text="e.g. 42")
        self._exh_entry.grid(row=0, column=1, sticky="ew", pady=6)
        self._exh_entry.bind("<Return>", lambda e: self._class_combo.focus())
        self._exh_entry.bind("<Tab>", lambda e: (self._class_combo.focus(), "break"))

        ctk.CTkLabel(form, text="Class Code:", anchor="e").grid(
            row=1, column=0, sticky="e", padx=(0, 8), pady=6
        )
        self._class_combo = ctk.CTkComboBox(
            form, values=self._class_codes,
            command=lambda v: self._check_duplicate(),
        )
        self._class_combo.set("")
        self._class_combo.grid(row=1, column=1, sticky="ew", pady=6)
        self._class_combo.bind("<KeyRelease>", lambda e: self._check_duplicate())
        self._class_combo.bind("<Return>", lambda e: self._save())

        self._msg = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=11),
                                  text_color=("red4", "tomato"), wraplength=300)
        self._msg.grid(row=1, column=0, pady=(0, 4))

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.grid(row=2, column=0, pady=(4, 16))
        self._save_btn = ctk.CTkButton(btns, text="Add", width=110, command=self._save)
        self._save_btn.pack(side="left", padx=8)
        ctk.CTkButton(btns, text="Cancel", width=110,
                      fg_color="transparent", border_width=1,
                      command=self.destroy).pack(side="left", padx=8)

        self.bind("<Escape>", lambda e: self.destroy())
        self._exh_entry.focus()

    def _check_duplicate(self):
        raw_exh = self._exh_entry.get().strip()
        raw_class = self._class_combo.get().strip().upper()
        if not raw_exh.isdigit() or not raw_class:
            self._msg.configure(text="")
            return
        exists = ShowEntry.get_or_none(
            (ShowEntry.exh_no == int(raw_exh)) & (ShowEntry.class_code == raw_class)
        )
        if exists:
            self._msg.configure(
                text=f"⚠ Exhibitor {raw_exh} already has an entry for {raw_class}.",
                text_color=("orange4", "orange"),
            )
        else:
            self._msg.configure(text="")

    def _save(self):
        raw_exh = self._exh_entry.get().strip()
        raw_class = self._class_combo.get().strip().upper()
        if not raw_exh.isdigit():
            self._msg.configure(text="Exhibitor # must be a number.", text_color=("red4", "tomato"))
            return
        if not raw_class:
            self._msg.configure(text="Class code required.", text_color=("red4", "tomato"))
            return
        try:
            add_entry(exh_no=int(raw_exh), class_code=raw_class)
            self.destroy()
        except EntryValidationError as e:
            self._msg.configure(text=str(e), text_color=("red4", "tomato"))
