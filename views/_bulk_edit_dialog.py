# views/_bulk_edit_dialog.py
from tkinter import messagebox
import customtkinter as ctk
from models.show_entry import ShowEntry
from services.entry_service import (
    bulk_add_entries,
    rename_class_code,
    delete_entries_for_exhibitor,
    reassign_exhibitor,
    EntryValidationError,
)

_RED = ("red4", "tomato")
_GREY = ("gray40", "gray60")


class BulkEditDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Bulk Entry Tools")
        self.geometry("500x420")
        self.resizable(False, False)
        self.grab_set()
        self.after(50, self.lift)
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        tabs = ctk.CTkTabView(self)
        tabs.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self._build_add(tabs.add("Bulk Add"))
        self._build_rename(tabs.add("Rename Class"))
        self._build_delete(tabs.add("Delete Exhibitor"))
        self._build_reassign(tabs.add("Reassign Exhibitor"))

    # ── Tab 1: Bulk Add ───────────────────────────────────────────────
    def _build_add(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        row = ctk.CTkFrame(tab, fg_color="transparent")
        row.grid(row=0, column=0, sticky="ew", pady=(8, 2))
        row.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(row, text="Exhibitor #:", width=110, anchor="e").grid(row=0, column=0, padx=(0, 8), pady=6)
        self._ba_exh = ctk.CTkEntry(row, placeholder_text="e.g. 14")
        self._ba_exh.grid(row=0, column=1, sticky="ew", pady=6)

        ctk.CTkLabel(tab, text="Class codes — one per line:", anchor="w").grid(
            row=1, column=0, sticky="w", padx=4, pady=(4, 2)
        )
        self._ba_codes = ctk.CTkTextbox(tab, height=160)
        self._ba_codes.grid(row=2, column=0, sticky="nsew", padx=4)

        self._ba_msg = ctk.CTkLabel(tab, text="", font=ctk.CTkFont(size=11), text_color=_GREY)
        self._ba_msg.grid(row=3, column=0, pady=4)

        ctk.CTkButton(tab, text="Add All", command=self._do_add).grid(row=4, column=0, pady=(0, 6))

    def _do_add(self):
        raw = self._ba_exh.get().strip()
        if not raw.isdigit():
            self._ba_msg.configure(text="Exhibitor # must be a number.", text_color=_RED)
            return
        codes = [l.strip().upper() for l in self._ba_codes.get("1.0", "end").splitlines() if l.strip()]
        if not codes:
            self._ba_msg.configure(text="Enter at least one class code.", text_color=_RED)
            return
        ok, errors = bulk_add_entries(int(raw), codes)
        msg = f"{ok} added"
        if errors:
            msg += f", {len(errors)} skipped: " + "; ".join(errors[:3])
            if len(errors) > 3:
                msg += f" (+{len(errors) - 3} more)"
        self._ba_msg.configure(text=msg, text_color=_GREY)

    # ── Tab 2: Rename Class ───────────────────────────────────────────
    def _build_rename(self, tab):
        tab.grid_columnconfigure(0, weight=1)

        form = ctk.CTkFrame(tab, fg_color="transparent")
        form.grid(row=0, column=0, sticky="ew", pady=(24, 4))
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Old class code:", width=130, anchor="e").grid(row=0, column=0, padx=(0, 8), pady=8)
        self._rn_old = ctk.CTkEntry(form, placeholder_text="e.g. SC01")
        self._rn_old.grid(row=0, column=1, sticky="ew", pady=8)

        ctk.CTkLabel(form, text="New class code:", width=130, anchor="e").grid(row=1, column=0, padx=(0, 8), pady=8)
        self._rn_new = ctk.CTkEntry(form, placeholder_text="e.g. SC02")
        self._rn_new.grid(row=1, column=1, sticky="ew", pady=8)

        self._rn_msg = ctk.CTkLabel(tab, text="", font=ctk.CTkFont(size=11), text_color=_GREY)
        self._rn_msg.grid(row=1, column=0, pady=4)

        ctk.CTkButton(tab, text="Rename All Matching Entries", command=self._do_rename).grid(row=2, column=0, pady=8)

    def _do_rename(self):
        old = self._rn_old.get().strip().upper()
        new = self._rn_new.get().strip().upper()
        if not old or not new:
            self._rn_msg.configure(text="Both codes required.", text_color=_RED)
            return
        try:
            count = rename_class_code(old, new)
            self._rn_msg.configure(text=f"{count} entries updated: {old} → {new}", text_color=_GREY)
        except EntryValidationError as e:
            self._rn_msg.configure(text=str(e), text_color=_RED)

    # ── Tab 3: Delete Exhibitor ───────────────────────────────────────
    def _build_delete(self, tab):
        tab.grid_columnconfigure(0, weight=1)

        form = ctk.CTkFrame(tab, fg_color="transparent")
        form.grid(row=0, column=0, sticky="ew", pady=(24, 4))
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Exhibitor #:", width=130, anchor="e").grid(row=0, column=0, padx=(0, 8), pady=8)
        self._del_exh = ctk.CTkEntry(form, placeholder_text="e.g. 14")
        self._del_exh.grid(row=0, column=1, sticky="ew", pady=8)

        self._del_msg = ctk.CTkLabel(tab, text="", font=ctk.CTkFont(size=11), text_color=_GREY)
        self._del_msg.grid(row=1, column=0, pady=4)

        btns = ctk.CTkFrame(tab, fg_color="transparent")
        btns.grid(row=2, column=0, pady=8)
        ctk.CTkButton(
            btns, text="Preview Count", width=120,
            fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
            command=self._del_preview,
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            btns, text="Delete All", width=120,
            fg_color=("firebrick", "darkred"), text_color="white",
            command=self._do_delete,
        ).pack(side="left", padx=6)

    def _del_preview(self):
        raw = self._del_exh.get().strip()
        if not raw.isdigit():
            self._del_msg.configure(text="Enter a valid exhibitor number.", text_color=_RED)
            return
        count = ShowEntry.select().where(ShowEntry.exh_no == int(raw)).count()
        self._del_msg.configure(text=f"{count} entries found for exhibitor {raw}.", text_color=_GREY)

    def _do_delete(self):
        raw = self._del_exh.get().strip()
        if not raw.isdigit():
            self._del_msg.configure(text="Enter a valid exhibitor number.", text_color=_RED)
            return
        exh = int(raw)
        count = ShowEntry.select().where(ShowEntry.exh_no == exh).count()
        if not messagebox.askyesno("Confirm Delete", f"Delete all {count} entries for exhibitor {exh}?\nThis cannot be undone."):
            return
        deleted = delete_entries_for_exhibitor(exh)
        self._del_msg.configure(text=f"{deleted} entries deleted.", text_color=_GREY)

    # ── Tab 4: Reassign Exhibitor ─────────────────────────────────────
    def _build_reassign(self, tab):
        tab.grid_columnconfigure(0, weight=1)

        form = ctk.CTkFrame(tab, fg_color="transparent")
        form.grid(row=0, column=0, sticky="ew", pady=(24, 4))
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="From exhibitor #:", width=130, anchor="e").grid(row=0, column=0, padx=(0, 8), pady=8)
        self._ra_from = ctk.CTkEntry(form, placeholder_text="wrong number")
        self._ra_from.grid(row=0, column=1, sticky="ew", pady=8)

        ctk.CTkLabel(form, text="To exhibitor #:", width=130, anchor="e").grid(row=1, column=0, padx=(0, 8), pady=8)
        self._ra_to = ctk.CTkEntry(form, placeholder_text="correct number")
        self._ra_to.grid(row=1, column=1, sticky="ew", pady=8)

        self._ra_msg = ctk.CTkLabel(tab, text="", font=ctk.CTkFont(size=11), text_color=_GREY)
        self._ra_msg.grid(row=1, column=0, pady=4)

        ctk.CTkButton(tab, text="Reassign All Entries", command=self._do_reassign).grid(row=2, column=0, pady=8)

    def _do_reassign(self):
        raw_from = self._ra_from.get().strip()
        raw_to = self._ra_to.get().strip()
        if not raw_from.isdigit() or not raw_to.isdigit():
            self._ra_msg.configure(text="Both must be integer exhibitor numbers.", text_color=_RED)
            return
        from_no, to_no = int(raw_from), int(raw_to)
        if from_no == to_no:
            self._ra_msg.configure(text="From and To cannot be the same.", text_color=_RED)
            return
        count = ShowEntry.select().where(ShowEntry.exh_no == from_no).count()
        if not messagebox.askyesno(
            "Confirm Reassign",
            f"Move {count} entries from exhibitor {from_no} to exhibitor {to_no}?\nThis cannot be undone.",
        ):
            return
        updated = reassign_exhibitor(from_no, to_no)
        self._ra_msg.configure(text=f"{updated} entries moved to exhibitor {to_no}.", text_color=_GREY)
