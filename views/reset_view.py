# views/reset_view.py
import customtkinter as ctk
from tkinter import messagebox
from services.reset_service import reset_show_data


class ResetView(ctk.CTkFrame):
    """Delete all show-year data (entries, results, specials) while preserving reference data."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Reset Show Data",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(16, 4)
        )

        ctk.CTkLabel(
            self,
            text=(
                "This permanently deletes:\n"
                "  • All show entries and calculated entries\n"
                "  • All late entries\n"
                "  • All results and not-benched flags\n"
                "  • All special winner assignments\n\n"
                "Exhibitors, class definitions, Hall of Fame records,\n"
                "and brochure notes are NOT affected."
            ),
            justify="left",
            font=ctk.CTkFont(size=12),
            text_color=("gray30", "gray70"),
        ).grid(row=1, column=0, sticky="w", padx=32, pady=(8, 16))

        ctk.CTkLabel(
            self, text="⚠ This cannot be undone.",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("red4", "tomato"),
        ).grid(row=2, column=0, sticky="w", padx=32, pady=(0, 16))

        self._btn = ctk.CTkButton(
            self, text="Reset Show Data", width=200, height=40,
            fg_color=("red4", "red3"), hover_color=("red3", "red2"),
            command=self._confirm_reset,
        )
        self._btn.grid(row=3, column=0, pady=(0, 12))

        self._msg = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=11),
                                  text_color=("gray40", "gray60"))
        self._msg.grid(row=4, column=0)

    def _confirm_reset(self):
        if not messagebox.askyesno(
            "Reset Show Data",
            "This will permanently delete ALL entries, results, and special winners.\nContinue?",
            icon="warning",
        ):
            return
        try:
            counts = reset_show_data()
        except Exception as exc:
            messagebox.showerror("Reset Failed", str(exc))
            return
        total = sum(counts.values())
        self._msg.configure(
            text=f"Reset complete — {total} records removed. "
                 f"({counts['entries']} entries, {counts['results']} results, "
                 f"{counts['special_winners']} special winners)"
        )
