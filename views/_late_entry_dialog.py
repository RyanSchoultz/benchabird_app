# views/_late_entry_dialog.py
import customtkinter as ctk
from services.late_entry_service import add_late_entry, LateEntryValidationError


class LateEntryDialog(ctk.CTkToplevel):
    """Add a single late entry. Pass exh_no and name to pre-fill and lock those fields."""
    def __init__(self, parent, exh_no: int | None = None, name: str | None = None):
        super().__init__(parent)
        self.title("Add Late Entry")
        self.geometry("340x240")
        self.resizable(False, False)
        self.grab_set()
        self.after(50, self.lift)
        self._preset_exh_no = exh_no
        self._preset_name = name
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.grid(row=0, column=0, padx=20, pady=(20, 8), sticky="ew")
        form.grid_columnconfigure(1, weight=1)

        fields = [
            ("Exhibitor #:", "_exh_entry",  "e.g. 42"),
            ("Name:",        "_name_entry",  "e.g. Smith, J."),
            ("Class Code:",  "_class_entry", "e.g. SC01"),
        ]
        presets = {
            "_exh_entry":  str(self._preset_exh_no) if self._preset_exh_no is not None else None,
            "_name_entry": self._preset_name,
        }
        for row_i, (label, attr, ph) in enumerate(fields):
            ctk.CTkLabel(form, text=label, anchor="e").grid(
                row=row_i, column=0, sticky="e", padx=(0, 8), pady=6
            )
            entry = ctk.CTkEntry(form, placeholder_text=ph)
            preset = presets.get(attr)
            if preset:
                entry.insert(0, preset)
                entry.configure(state="disabled")
            entry.grid(row=row_i, column=1, sticky="ew", pady=6)
            setattr(self, attr, entry)

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
        name = self._name_entry.get().strip()
        raw_class = self._class_entry.get().strip().upper()
        if not raw_exh.isdigit():
            self._msg.configure(text="Exhibitor # must be a number.")
            return
        if not name:
            self._msg.configure(text="Name required.")
            return
        if not raw_class:
            self._msg.configure(text="Class code required.")
            return
        try:
            add_late_entry(exh_no=int(raw_exh), name=name, class_code=raw_class)
            self.destroy()
        except LateEntryValidationError as e:
            self._msg.configure(text=str(e))
