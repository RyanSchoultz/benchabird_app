# views/sql_editor_view.py
import customtkinter as ctk
from tkinter import messagebox

WRITE_KEYWORDS = ("INSERT", "UPDATE", "DELETE", "DROP", "CREATE",
                  "ALTER", "TRUNCATE", "REPLACE")

STARTER_SQL = "SELECT * FROM show_details LIMIT 10;"


class SQLEditorView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)   # results row expands

        # ── Toolbar ───────────────────────────────────────────────────
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))

        ctk.CTkLabel(toolbar, text="SQL Editor",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        ctk.CTkButton(
            toolbar, text="Tables…", width=90,
            fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
            command=self._show_tables,
        ).pack(side="right", padx=(4, 0))

        ctk.CTkButton(
            toolbar, text="▶  Run  (Ctrl+Enter)", width=165,
            command=self._execute,
        ).pack(side="right", padx=4)

        ctk.CTkLabel(
            toolbar,
            text="Write queries (INSERT/UPDATE/DELETE) require confirmation",
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray55"),
        ).pack(side="right", padx=8)

        # ── SQL input ─────────────────────────────────────────────────
        self._editor = ctk.CTkTextbox(
            self, height=140,
            font=ctk.CTkFont(family="Courier New", size=12),
        )
        self._editor.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 4))
        self._editor.insert("end", STARTER_SQL)
        self._editor.bind("<Control-Return>",    lambda e: self._execute())
        self._editor.bind("<Control-KP_Enter>",  lambda e: self._execute())

        # ── Status bar ────────────────────────────────────────────────
        self._status = ctk.CTkLabel(
            self, text="Press Ctrl+Enter to run a query.",
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray55"),
            anchor="w",
        )
        self._status.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 2))

        # ── Results area ──────────────────────────────────────────────
        self._results = ctk.CTkScrollableFrame(
            self, fg_color=("gray92", "gray16"),
        )
        self._results.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 16))

    # ── Execution ─────────────────────────────────────────────────────

    def _execute(self):
        raw = self._editor.get("1.0", "end")
        # Strip leading comments to find the first real keyword
        first_word = next(
            (ln.strip().split()[0].upper()
             for ln in raw.splitlines()
             if ln.strip() and not ln.strip().startswith("--")),
            "",
        )
        sql = raw.strip()
        if not sql or sql == "--":
            return

        if first_word in WRITE_KEYWORDS:
            if not messagebox.askyesno(
                "Write Query",
                f"This {first_word} statement will modify data.\n\nContinue?",
                parent=self,
            ):
                return

        self._set_status("Running…", neutral=True)
        self._clear_results()

        # Run synchronously — SQLite is fast and threading adds SQLite
        # cross-thread complications with no real benefit here.
        try:
            from models.database import database
            database.connect(reuse_if_open=True)
            cursor = database.execute_sql(sql)
            if cursor.description:
                cols  = [d[0] for d in cursor.description]
                rows  = cursor.fetchmany(500)
                self._show_results(cols, list(rows))
            else:
                self._set_status(f"OK — {cursor.rowcount} row(s) affected")
        except Exception as exc:
            self._set_status(f"Error: {exc}", error=True)

    # ── Status helpers ────────────────────────────────────────────────

    def _set_status(self, msg: str, *, error: bool = False, neutral: bool = False):
        if error:
            colour = ("red4", "tomato")
        elif neutral:
            colour = ("gray45", "gray55")
        else:
            colour = ("gray30", "gray70")
        self._status.configure(text=msg, text_color=colour)

    # ── Results rendering ─────────────────────────────────────────────

    def _clear_results(self):
        for w in self._results.winfo_children():
            w.destroy()

    def _show_results(self, cols: list, rows: list):
        self._clear_results()
        n = len(cols)
        for c_i in range(n):
            self._results.grid_columnconfigure(c_i, weight=1, minsize=60)

        # Header row
        for c_i, col in enumerate(cols):
            ctk.CTkLabel(
                self._results, text=col,
                font=ctk.CTkFont(weight="bold"),
                fg_color=("gray82", "gray22"), corner_radius=4,
                anchor="w",
            ).grid(row=0, column=c_i, sticky="ew", padx=2, pady=(0, 2))

        if not rows:
            ctk.CTkLabel(
                self._results, text="No rows returned",
                text_color=("gray50", "gray55"),
                font=ctk.CTkFont(size=12),
            ).grid(row=1, column=0, columnspan=max(n, 1), pady=20)
            self._set_status("0 rows returned")
            return

        for r_i, row in enumerate(rows, start=1):
            bg = ("gray88", "gray18") if r_i % 2 == 0 else ("gray92", "gray16")
            for c_i in range(n):
                val = row[c_i]
                text = "NULL" if val is None else str(val)[:120]
                ctk.CTkLabel(
                    self._results, text=text,
                    fg_color=bg, anchor="w",
                    font=ctk.CTkFont(family="Courier New", size=11),
                ).grid(row=r_i, column=c_i, sticky="ew", padx=2, pady=1)

        suffix = "  (limit 500 — refine your query for more)" if len(rows) == 500 else ""
        self._set_status(f"{len(rows)} row(s) returned{suffix}")

    # ── Helpers ───────────────────────────────────────────────────────

    def _show_tables(self):
        self._editor.delete("1.0", "end")
        self._editor.insert("end",
            "SELECT name, type\n"
            "FROM sqlite_master\n"
            "WHERE type IN ('table', 'view')\n"
            "ORDER BY type, name;")
        self._execute()
