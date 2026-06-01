import math
import customtkinter as ctk

PAGE_SIZE = 100


def paginate(data: list, page: int, page_size: int = PAGE_SIZE) -> list:
    start = page * page_size
    return data[start:start + page_size]


def total_pages(data_len: int, page_size: int = PAGE_SIZE) -> int:
    return max(1, math.ceil(data_len / page_size))


class PaginatedTable(ctk.CTkFrame):
    """
    Paginated data table widget.

    data format passed to load(): list of (key, [cell_str, ...])
      - key:       identifier passed to on_select callback and to row_render
      - cell_strs: one string per data column (does NOT include action columns)

    row_render: optional callable(key, row_i, scroll_frame)
      Called after regular cells are rendered for each row. Use it to grid
      action widgets (e.g. CTkButton) at a column index beyond len(vals).
    """

    def __init__(
        self,
        parent,
        *,
        headers: list,
        col_weights: list = None,
        on_select=None,
        selectable: bool = True,
        page_size: int = PAGE_SIZE,
        **kwargs,
    ):
        super().__init__(parent, fg_color=("gray92", "gray16"), **kwargs)
        self._headers = headers
        self._col_weights = col_weights or [1] * len(headers)
        self._on_select = on_select
        self._selectable = selectable
        self._page_size = page_size
        self._data: list = []
        self._row_render = None
        self._page = 0
        self._build()

    def _build(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._scroll = ctk.CTkScrollableFrame(self, fg_color=("gray92", "gray16"))
        self._scroll.grid(row=0, column=0, sticky="nsew")

        nav = ctk.CTkFrame(self, fg_color=("gray85", "gray22"), height=36)
        nav.grid(row=1, column=0, sticky="ew")
        nav.grid_propagate(False)
        nav.grid_columnconfigure(1, weight=1)

        self._prev_btn = ctk.CTkButton(
            nav, text="← Prev", width=80, height=28,
            fg_color=("gray75", "gray32"), text_color=("gray10", "gray90"),
            command=self._prev,
        )
        self._prev_btn.grid(row=0, column=0, padx=8, pady=4)

        self._page_label = ctk.CTkLabel(
            nav, text="", font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
        )
        self._page_label.grid(row=0, column=1)

        self._next_btn = ctk.CTkButton(
            nav, text="Next →", width=80, height=28,
            fg_color=("gray75", "gray32"), text_color=("gray10", "gray90"),
            command=self._next,
        )
        self._next_btn.grid(row=0, column=2, padx=8, pady=4)

    def load(self, data: list, *, row_render=None):
        """Replace displayed data. Resets to page 0."""
        self._data = data
        self._row_render = row_render
        self._page = 0
        self._render()

    def _render(self):
        for w in self._scroll.winfo_children():
            w.destroy()

        for col_i, (hdr, wt) in enumerate(zip(self._headers, self._col_weights)):
            self._scroll.grid_columnconfigure(col_i, weight=wt)
            ctk.CTkLabel(
                self._scroll, text=hdr, font=ctk.CTkFont(weight="bold"),
                fg_color=("gray82", "gray22"), corner_radius=4,
            ).grid(row=0, column=col_i, sticky="ew", padx=2, pady=(0, 2))

        page_data = paginate(self._data, self._page, self._page_size)

        # Issue 2: Empty-state message
        if not self._data:
            ctk.CTkLabel(
                self._scroll, text="No data",
                font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray55"),
            ).grid(row=1, column=0, columnspan=len(self._headers), pady=20)

        for row_i, (key, vals) in enumerate(page_data, start=1):
            bg = ("gray88", "gray18") if row_i % 2 == 0 else ("gray92", "gray16")
            for col_i, val in enumerate(vals):
                # Issue 3: Guard selectable=True with no on_select
                if self._selectable and self._on_select is not None:
                    ctk.CTkButton(
                        self._scroll, text=val, anchor="w",
                        fg_color=bg, text_color=("gray10", "gray90"),
                        hover_color=("gray80", "gray25"),
                        corner_radius=0, height=28,
                        font=ctk.CTkFont(size=12),
                        command=lambda k=key: self._on_select(k),
                    ).grid(row=row_i, column=col_i, sticky="ew", padx=2, pady=1)
                else:
                    ctk.CTkLabel(
                        self._scroll, text=val, fg_color=bg, anchor="w",
                        font=ctk.CTkFont(size=12),
                    ).grid(row=row_i, column=col_i, sticky="ew", padx=2, pady=1)
            if self._row_render:
                self._row_render(key, row_i, self._scroll)

        pages = total_pages(len(self._data), self._page_size)
        self._page_label.configure(
            text=f"Page {self._page + 1} / {pages}  ({len(self._data)} rows)",
        )
        self._prev_btn.configure(state="normal" if self._page > 0 else "disabled")
        self._next_btn.configure(state="normal" if self._page < pages - 1 else "disabled")

    def _prev(self):
        if self._page > 0:
            self._page -= 1
            self._render()

    def _next(self):
        if self._page < total_pages(len(self._data), self._page_size) - 1:
            self._page += 1
            self._render()
