# views/archive_view.py
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox
from services.archive_service import save_snapshot, list_snapshots, restore_snapshot, delete_snapshot

_GREY = ("gray40", "gray60")


class ArchiveView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()
        self._load_list()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        hdr = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray88", "gray18"))
        hdr.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(hdr, text="Show Archives",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=20, pady=14)

        # Save new snapshot
        save_panel = ctk.CTkFrame(self, fg_color=("gray88", "gray20"), corner_radius=8)
        save_panel.grid(row=1, column=0, sticky="ew", padx=20, pady=(16, 8))
        ctk.CTkLabel(save_panel, text="Save current show as:",
                     font=ctk.CTkFont(size=13)).pack(side="left", padx=(16, 8), pady=12)
        self._name_entry = ctk.CTkEntry(save_panel, placeholder_text="e.g. 2024 National Show", width=260)
        self._name_entry.pack(side="left", padx=4, pady=12)
        ctk.CTkButton(save_panel, text="Save Snapshot", width=130,
                      command=self._save).pack(side="left", padx=8, pady=12)
        self._save_msg = ctk.CTkLabel(save_panel, text="", font=ctk.CTkFont(size=11), text_color=_GREY)
        self._save_msg.pack(side="left", padx=8)

        # Archive list
        ctk.CTkLabel(self, text="Saved Archives",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=2, column=0, sticky="w", padx=20, pady=(8, 4)
        )
        self._list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._list_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 16))
        self._list_frame.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

    def _save(self):
        name = self._name_entry.get().strip()
        if not name:
            self._save_msg.configure(text="Enter a name first.", text_color=("red4", "tomato"))
            return
        dest = save_snapshot(name)
        self._save_msg.configure(text=f"Saved: {dest.name}", text_color=_GREY)
        self._name_entry.delete(0, "end")
        self._load_list()

    def _load_list(self):
        for w in self._list_frame.winfo_children():
            w.destroy()
        snapshots = list_snapshots()
        if not snapshots:
            ctk.CTkLabel(self._list_frame, text="No archives yet.",
                         text_color=_GREY).grid(row=0, column=0, pady=20)
            return
        for i, path in enumerate(snapshots):
            mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            size_kb = path.stat().st_size // 1024
            row = ctk.CTkFrame(self._list_frame, corner_radius=6, fg_color=("gray88", "gray20"))
            row.grid(row=i, column=0, sticky="ew", pady=3)
            row.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(row, text=path.stem, anchor="w",
                         font=ctk.CTkFont(size=12, weight="bold")).grid(
                row=0, column=0, sticky="w", padx=14, pady=(8, 2)
            )
            ctk.CTkLabel(row, text=f"{mtime}  ·  {size_kb} KB",
                         anchor="w", font=ctk.CTkFont(size=11), text_color=_GREY).grid(
                row=1, column=0, sticky="w", padx=14, pady=(0, 8)
            )
            btns = ctk.CTkFrame(row, fg_color="transparent")
            btns.grid(row=0, column=1, rowspan=2, padx=12, pady=8)
            ctk.CTkButton(btns, text="Restore", width=90,
                          command=lambda p=path: self._restore(p)).pack(side="left", padx=4)
            ctk.CTkButton(btns, text="Delete", width=70,
                          fg_color=("gray75", "gray30"), text_color=("gray10", "gray90"),
                          command=lambda p=path: self._delete(p)).pack(side="left", padx=4)

    def _restore(self, path):
        if not messagebox.askyesno(
            "Restore Archive",
            f"Replace all current show data with:\n{path.name}\n\nThis cannot be undone.",
        ):
            return
        restore_snapshot(path)
        self.winfo_toplevel().navigate("dashboard")

    def _delete(self, path):
        if not messagebox.askyesno("Delete Archive", f"Permanently delete {path.name}?"):
            return
        delete_snapshot(path)
        self._load_list()
