# views/setup_view.py
import customtkinter as ctk
from tkinter import filedialog
from pathlib import Path
from models.reference import ShowDetails

FIELDS = [
    ("show_afr",      "Show Name (Afrikaans)"),
    ("show_eng",      "Show Name (English)"),
    ("date_afr",      "Date (Afrikaans)"),
    ("date_eng",      "Date (English)"),
    ("club_afr",      "Club Code (Afrikaans)"),
    ("club_afr_full", "Club Full Name (Afrikaans)"),
    ("club_eng",      "Club Code (English)"),
    ("club_eng_full", "Club Full Name (English)"),
    ("association",   "Association"),
]


class SetupView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._entries: dict = {}
        self._logo_ctk_img = None  # prevent GC
        self._build()
        self._load()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="Show & Club Details",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(12, 4))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.grid(row=1, column=0, sticky="nsew", padx=30, pady=8)
        form.grid_columnconfigure(1, weight=1)

        for row_i, (field, label) in enumerate(FIELDS):
            ctk.CTkLabel(form, text=label, anchor="e").grid(
                row=row_i, column=0, sticky="e", padx=(0, 10), pady=4)
            ent = ctk.CTkEntry(form, width=320)
            ent.grid(row=row_i, column=1, sticky="ew", pady=4)
            self._entries[field] = ent

        ctk.CTkButton(self, text="Save", width=120, command=self._save).grid(
            row=2, column=0, pady=16, padx=30, sticky="w"
        )

        # ── Logo row ─────────────────────────────────────────────────
        logo_row = ctk.CTkFrame(self, fg_color="transparent")
        logo_row.grid(row=3, column=0, sticky="w", padx=30, pady=(0, 8))

        ctk.CTkLabel(logo_row, text="Club Logo:",
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 8))

        self._logo_name_lbl = ctk.CTkLabel(
            logo_row, text="No logo set",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
        )
        self._logo_name_lbl.pack(side="left", padx=(0, 8))

        ctk.CTkButton(logo_row, text="Browse…", width=90,
                      command=self._browse_logo).pack(side="left", padx=(0, 4))
        ctk.CTkButton(logo_row, text="Clear", width=70,
                      fg_color="transparent", border_width=1,
                      text_color=("gray30", "gray70"),
                      command=self._clear_logo).pack(side="left")

        # ── Logo preview canvas ──────────────────────────────────────
        preview_outer = ctk.CTkFrame(self, fg_color=("gray88", "gray20"),
                                     corner_radius=8)
        preview_outer.grid(row=4, column=0, sticky="w", padx=30, pady=(0, 16))

        self._preview_lbl = ctk.CTkLabel(
            preview_outer, text="No logo set",
            text_color=("gray50", "gray55"),
            font=ctk.CTkFont(size=11),
            width=240, height=90,
        )
        self._preview_lbl.pack(padx=12, pady=8)

    def _load(self):
        sd = ShowDetails.select().first()
        if not sd:
            return
        for field, _ in FIELDS:
            val = getattr(sd, field, None)
            ent = self._entries[field]
            ent.delete(0, "end")
            if val:
                ent.insert(0, val)
        logo_data = getattr(sd, 'logo_data', None)
        logo_path = getattr(sd, 'logo_path', None)
        if logo_data:
            self._refresh_preview(bytes(logo_data))
            name = Path(logo_path).name if logo_path else "Logo (stored in DB)"
            self._logo_name_lbl.configure(text=name)
        elif logo_path:
            self._logo_name_lbl.configure(text=Path(logo_path).name)

    def _browse_logo(self):
        path = filedialog.askopenfilename(
            title="Select Club Logo",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError:
            return
        self._set_logo(path, data)

    def _clear_logo(self):
        self._set_logo(None, None)

    def _set_logo(self, path, data):
        sd = ShowDetails.select().first()
        if sd:
            sd.logo_path = path
            sd.logo_data = data
            sd.save()
        elif path:
            ShowDetails.create(logo_path=path, logo_data=data)

        name = Path(path).name if path else "No logo set"
        self._logo_name_lbl.configure(text=name)
        self._refresh_preview(data)

    def _refresh_preview(self, data):
        if not data:
            self._logo_ctk_img = None
            self._preview_lbl.configure(image=None, text="No logo set")
            return
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(data))
            max_w, max_h = 220, 80
            w, h = img.size
            scale = min(max_w / w, max_h / h)
            new_size = (int(w * scale), int(h * scale))
            self._logo_ctk_img = ctk.CTkImage(img, size=new_size)
            self._preview_lbl.configure(image=self._logo_ctk_img, text="")
        except Exception:
            self._preview_lbl.configure(image=None, text="Preview failed")

    def _save(self):
        data = {field: (self._entries[field].get().strip() or None) for field, _ in FIELDS}
        sd = ShowDetails.select().first()
        if sd:
            for k, v in data.items():
                setattr(sd, k, v)
            sd.save()
        else:
            ShowDetails.create(**data)
