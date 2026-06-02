# views/_special_list_dialog.py
import customtkinter as ctk


class SpecialListDialog(ctk.CTkToplevel):
    """Add or edit a Special Prize List record."""

    def __init__(self, parent, special_nr: str = None):
        super().__init__(parent)
        self.title("Add Special Prize" if not special_nr else "Edit Special Prize")
        self.geometry("440x300")
        self.resizable(False, False)
        self.grab_set()
        self.after(50, self.lift)
        self._special_nr = special_nr
        self._build()
        if special_nr:
            self._prefill(special_nr)

    def _build(self):
        self.grid_columnconfigure(1, weight=1)

        fields = [
            ("Special Nr:", "_nr_entry"),
            ("Description:", "_desc_entry"),
            ("Prize:", "_prize_entry"),
            ("Cash Amount:", "_cash_entry"),
        ]
        for row_i, (label, attr) in enumerate(fields):
            ctk.CTkLabel(self, text=label).grid(
                row=row_i, column=0, padx=(16, 8), pady=6, sticky="e"
            )
            entry = ctk.CTkEntry(self, width=270)
            entry.grid(row=row_i, column=1, padx=(0, 16), pady=6, sticky="ew")
            setattr(self, attr, entry)

        if self._special_nr:
            self._nr_entry.configure(state="disabled")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=(8, 4))
        ctk.CTkButton(btn_frame, text="Save", width=130,
                      command=self._save).pack(side="left", padx=8)
        ctk.CTkButton(
            btn_frame, text="Cancel", width=130,
            fg_color="transparent", border_width=1,
            text_color=("gray30", "gray70"),
            command=self.destroy,
        ).pack(side="left", padx=8)

        self._msg = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=11), text_color=("red4", "tomato")
        )
        self._msg.grid(row=len(fields) + 1, column=0, columnspan=2, pady=(4, 8))

    def _prefill(self, special_nr: str):
        from models.special import SpecialList
        sp = SpecialList.get_or_none(SpecialList.special_nr == special_nr)
        if not sp:
            return
        self._nr_entry.configure(state="normal")
        self._nr_entry.insert(0, sp.special_nr or "")
        self._nr_entry.configure(state="disabled")
        self._desc_entry.insert(0, sp.description or "")
        self._prize_entry.insert(0, sp.prize1 or "")
        if sp.cash is not None:
            self._cash_entry.insert(0, str(sp.cash))

    def _save(self):
        from services.special_service import save_special_list
        nr = self._nr_entry.get().strip() if not self._special_nr else self._special_nr
        desc = self._desc_entry.get().strip()
        prize = self._prize_entry.get().strip()
        raw_cash = self._cash_entry.get().strip()
        if not nr:
            self._msg.configure(text="Special Nr is required.")
            return
        if raw_cash:
            try:
                cash = int(raw_cash)
                if cash < 0:
                    self._msg.configure(text="Cash amount must be 0 or greater.")
                    return
            except ValueError:
                self._msg.configure(text="Cash Amount must be a whole number.")
                return
        else:
            cash = None
        save_special_list(nr, desc, prize, cash)
        self.destroy()
