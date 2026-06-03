# views/_special_dialog.py
import customtkinter as ctk
from services.special_service import assign_special_winner, clear_special_winner


class SpecialAssignDialog(ctk.CTkToplevel):
    """Set the winning exhibit number for a single special prize."""
    def __init__(self, parent, special_nr: str, description: str, current_exhibit_no):
        super().__init__(parent)
        self._special_nr = special_nr
        self.title(f"Assign Winner — {special_nr}")
        self.geometry("380x200")
        self.resizable(False, False)
        self.grab_set()
        self.after(50, self.lift)
        self._build(description, current_exhibit_no)

    def _build(self, description: str, current_exhibit_no):
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text=description or self._special_nr,
                     font=ctk.CTkFont(size=12, weight="bold"),
                     wraplength=340).grid(row=0, column=0, padx=20, pady=(20, 8))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.grid(row=1, column=0, padx=20, pady=4)
        ctk.CTkLabel(form, text="Exhibit #:").pack(side="left", padx=(0, 8))
        self._entry = ctk.CTkEntry(form, width=100, placeholder_text="e.g. 42")
        if current_exhibit_no:
            self._entry.insert(0, str(current_exhibit_no))
        self._entry.pack(side="left")

        self._msg = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=11),
                                  text_color=("red4", "tomato"))
        self._msg.grid(row=2, column=0, pady=4)

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.grid(row=3, column=0, pady=(4, 16))
        ctk.CTkButton(btns, text="Save", width=110, command=self._save).pack(side="left", padx=8)
        ctk.CTkButton(btns, text="Cancel", width=110,
                      fg_color="transparent", border_width=1,
                      command=self.destroy).pack(side="left", padx=8)

    def _save(self):
        raw = self._entry.get().strip()
        if not raw:
            clear_special_winner(self._special_nr)
            self.destroy()
            return
        if not raw.isdigit():
            self._msg.configure(text="Enter a numeric exhibit number, or clear the field to remove.")
            return
        try:
            assign_special_winner(self._special_nr, int(raw))
            self.destroy()
        except ValueError as e:
            self._msg.configure(text=str(e))
