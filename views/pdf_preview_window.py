# views/pdf_preview_window.py
"""Modal PDF preview window — renders pages via pymupdf, allows Save As."""
import io
import threading
import subprocess
import sys
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image


class PDFPreviewWindow(ctk.CTkToplevel):
    """Show a rendered PDF with page navigation and a Save As button."""

    def __init__(self, parent, pdf_bytes: bytes, title: str,
                 default_filename: str = "report.pdf"):
        super().__init__(parent)
        self._pdf_bytes = pdf_bytes
        self._default_filename = default_filename
        self._page = 0
        self._doc = None
        self._page_count = 0
        self._ctk_img = None  # prevent GC

        self.title(f"Preview — {title}")
        self.geometry("760x960")
        self.minsize(500, 600)
        self.grab_set()
        self.after(50, self.lift)
        self._build()
        self._load_doc()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Navigation bar ──────────────────────────────────────────
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))

        self._prev_btn = ctk.CTkButton(
            nav, text="← Prev", width=80,
            command=self._prev_page,
            state="disabled",
        )
        self._prev_btn.pack(side="left")

        self._page_lbl = ctk.CTkLabel(nav, text="Loading…", width=160)
        self._page_lbl.pack(side="left", padx=12)

        self._next_btn = ctk.CTkButton(
            nav, text="Next →", width=80,
            command=self._next_page,
            state="disabled",
        )
        self._next_btn.pack(side="left")

        # ── Scrollable page area ─────────────────────────────────────
        self._scroll = ctk.CTkScrollableFrame(self, fg_color=("gray90", "gray15"))
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=12, pady=4)
        self._scroll.grid_columnconfigure(0, weight=1)

        self._img_lbl = ctk.CTkLabel(self._scroll, text="")
        self._img_lbl.grid(row=0, column=0)

        # ── Bottom action bar ────────────────────────────────────────
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=2, column=0, sticky="ew", padx=12, pady=(4, 12))

        self._status_lbl = ctk.CTkLabel(
            bottom, text="", font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
        )
        self._status_lbl.pack(side="left")

        ctk.CTkButton(
            bottom, text="Close", width=90,
            fg_color="transparent", border_width=1,
            text_color=("gray30", "gray70"),
            command=self.destroy,
        ).pack(side="right", padx=(4, 0))

        ctk.CTkButton(
            bottom, text="Save As…", width=110,
            command=self._save_as,
        ).pack(side="right")

        ctk.CTkButton(
            bottom, text="Print…", width=90,
            fg_color=("gray75", "gray32"), text_color=("gray10", "gray90"),
            command=self._print,
        ).pack(side="right", padx=(0, 4))

    def _load_doc(self):
        """Open the PDF bytes in a background thread, then render page 0."""
        def _load():
            import fitz
            doc = fitz.open(stream=self._pdf_bytes, filetype="pdf")
            self._doc = doc
            self._page_count = len(doc)
            self.after(0, self._render_current)
        threading.Thread(target=_load, daemon=True).start()

    def _render_current(self):
        if not self._doc:
            return
        import fitz
        page = self._doc[self._page]
        # Render at 1.2× for good quality on normal displays
        mat = fitz.Matrix(1.2, 1.2)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        pil_img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        self._ctk_img = ctk.CTkImage(
            light_image=pil_img, dark_image=pil_img,
            size=(pix.width, pix.height),
        )
        self._img_lbl.configure(image=self._ctk_img, text="")
        self._page_lbl.configure(
            text=f"Page {self._page + 1} / {self._page_count}"
        )
        self._prev_btn.configure(state="normal" if self._page > 0 else "disabled")
        self._next_btn.configure(
            state="normal" if self._page < self._page_count - 1 else "disabled"
        )

    def _prev_page(self):
        if self._page > 0:
            self._page -= 1
            self._render_current()

    def _next_page(self):
        if self._doc and self._page < self._page_count - 1:
            self._page += 1
            self._render_current()

    def _print(self):
        """Save to a temp file and invoke the OS print action."""
        import tempfile
        import os
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False,
                                              prefix="benchabird_print_")
            tmp.write(self._pdf_bytes)
            tmp.close()
            if sys.platform == "win32":
                os.startfile(tmp.name, "print")
            else:
                subprocess.Popen(["lpr", tmp.name])
            self._status_lbl.configure(text="Sent to printer.")
        except Exception as exc:
            self._status_lbl.configure(text=f"Print failed: {exc}")

    def _save_as(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=self._default_filename,
            title="Save PDF Report",
        )
        if not path:
            return
        try:
            with open(path, "wb") as f:
                f.write(self._pdf_bytes)
            self._status_lbl.configure(text=f"Saved: {path}")
            if sys.platform == "win32":
                subprocess.Popen(["start", "", path], shell=True)
        except Exception as exc:
            self._status_lbl.configure(text=f"Error: {exc}")
