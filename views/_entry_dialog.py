# views/_entry_dialog.py
import customtkinter as ctk
from services.entry_service import add_entry, EntryValidationError


class EntryDialog(ctk.CTkToplevel):
    """Add a single show entry."""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Add Show Entry")
        self.geometry("320x200")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.grid(row=0, column=0, padx=20, pady=(20, 8), sticky="ew")
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Exhibitor #:", anchor="e").grid(
            row=0, column=0, sticky="e", padx=(0, 8), pady=6
        )
        self._exh_entry = ctk.CTkEntry(form, placeholder_text="e.g. 42")
        self._exh_entry.grid(row=0, column=1, sticky="ew", pady=6)

        ctk.CTkLabel(form, text="Class Code:", anchor="e").grid(
            row=1, column=0, sticky="e", padx=(0, 8), pady=6
        )
        self._class_entry = ctk.CTkEntry(form, placeholder_text="e.g. SC01")
        self._class_entry.grid(row=1, column=1, sticky="ew", pady=6)

        self._msg = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=11),
                                  text_color=("red4", "tomato"))
        self._msg.grid(row=1, column=0, pady=4)

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.grid(row=2, column=0, pady=(4, 16))
        ctk.CTkButton(btns, text="Add", width=110, command=self._save).pack(side="left", padx=8)
        ctk.CTkButton(btns, text="Cancel", width=110,
                      fg_color="transparent", border_width=1,
                      command=self.destroy).pack(side="left", padx=8)

    def _save(self):
        raw_exh = self._exh_entry.get().strip()
        raw_class = self._class_entry.get().strip().upper()
        if not raw_exh.isdigit():
            self._msg.configure(text="Exhibitor # must be a number.")
            return
        if not raw_class:
            self._msg.configure(text="Class code required.")
            return
        try:
            add_entry(exh_no=int(raw_exh), class_code=raw_class)
            self.destroy()
        except EntryValidationError as e:
            self._msg.configure(text=str(e))
