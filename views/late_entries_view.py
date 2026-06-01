# views/late_entries_view.py
import customtkinter as ctk
from repository.entry_repo import EntryRepo
from services.late_entry_service import remove_late_entry

_repo = EntryRepo()


class LateEntriesView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._selected_auto_num = None
        self._table_frame = None
        self._build()
        self._reload_table()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        ctk.CTkLabel(toolbar, text="Late Entries",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        ctk.CTkButton(toolbar, text="Delete Selected", width=110,
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=self._delete_selected).pack(side="right", padx=4)
        ctk.CTkButton(toolbar, text="+ Add Late Entry", width=130,
                      command=self._open_add).pack(side="right", padx=4)

        self._status = ctk.CTkLabel(toolbar, text="",
                                    font=ctk.CTkFont(size=11),
                                    text_color=("gray40", "gray60"))
        self._status.pack(side="left", padx=12)

    def _reload_table(self):
        self._selected_auto_num = None
        if self._table_frame:
            self._table_frame.destroy()

        self._table_frame = ctk.CTkScrollableFrame(self, fg_color=("gray92", "gray16"))
        self._table_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 16))

        for col_i, hdr in enumerate(["AutoNum", "ExhNo", "Name", "Class"]):
            self._table_frame.grid_columnconfigure(col_i, weight=1)
            ctk.CTkLabel(self._table_frame, text=hdr, font=ctk.CTkFont(weight="bold"),
                         fg_color=("gray82", "gray22")).grid(
                row=0, column=col_i, sticky="ew", padx=2, pady=(0, 2)
            )

        entries = _repo.get_late()
        for row_i, e in enumerate(entries, start=1):
            bg = ("gray88", "gray18") if row_i % 2 == 0 else ("gray92", "gray16")
            for col_i, val in enumerate([str(e.auto_num), str(e.exh_no or ""),
                                          e.name or "", e.class_code or ""]):
                ctk.CTkButton(
                    self._table_frame, text=val, anchor="w",
                    fg_color=bg, text_color=("gray10", "gray90"),
                    hover_color=("gray80", "gray25"),
                    corner_radius=0, height=28,
                    font=ctk.CTkFont(size=12),
                    command=lambda an=e.auto_num: self._select(an),
                ).grid(row=row_i, column=col_i, sticky="ew", padx=2, pady=1)

        self._status.configure(text=f"{len(entries)} rows")

    def _select(self, auto_num: int):
        self._selected_auto_num = auto_num

    def _open_add(self):
        from views._late_entry_dialog import LateEntryDialog
        dlg = LateEntryDialog(self)
        self.wait_window(dlg)
        self._reload_table()

    def _delete_selected(self):
        if self._selected_auto_num is None:
            return
        remove_late_entry(self._selected_auto_num)
        self._reload_table()
