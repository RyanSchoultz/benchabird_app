# views/reimport_view.py
import csv
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from config import MDB_PATH
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry
from models.class_def import ClassDef

# Exhibitor fields that can be mapped from a CSV
CSV_FIELDS = [
    ("exh_no",      "Exhibitor #"),
    ("name",        "Name *"),
    ("address",     "Address"),
    ("suburb",      "Suburb"),
    ("town",        "Town"),
    ("zip_code",    "Zip Code"),
    ("tel_home",    "Tel Home"),
    ("tel_work",    "Tel Work"),
    ("cell_no",     "Cell No"),
    ("email",       "Email"),
    ("club",        "Club"),
]

# Common CSV header name → model field auto-detect
_HEADER_ALIASES = {
    "exh_no": ["exh_no", "exhibitor_no", "exhibitor no", "exhibitor#", "no", "number"],
    "name":   ["name", "full_name", "fullname", "exhibitor_name", "exhibitor name"],
    "address":["address", "addr", "street", "physical_address"],
    "suburb": ["suburb", "area"],
    "town":   ["town", "city"],
    "zip_code":["zip_code", "zip", "postal_code", "postal code", "postcode"],
    "tel_home":["tel_home", "tel home", "home tel", "telephone", "phone"],
    "tel_work":["tel_work", "tel work", "work tel", "work phone"],
    "cell_no": ["cell_no", "cell", "mobile", "cellphone", "cell no"],
    "email":   ["email", "e-mail", "email address"],
    "club":    ["club", "club_name"],
}


def _auto_match(csv_headers: list[str]) -> dict:
    """Return {field: csv_column} guesses based on known aliases."""
    lower_headers = {h.lower().strip(): h for h in csv_headers}
    mapping = {}
    for field, aliases in _HEADER_ALIASES.items():
        for alias in aliases:
            if alias in lower_headers:
                mapping[field] = lower_headers[alias]
                break
    return mapping


class ReImportView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self, text="Import Data",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))

        tabs = ctk.CTkTabview(self)
        tabs.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

        mdb_tab = tabs.add("MDB File")
        csv_tab = tabs.add("CSV Import")
        db_tab  = tabs.add("Copy from DB")

        self._build_mdb_tab(mdb_tab)
        self._build_csv_tab(csv_tab)
        self._build_db_tab(db_tab)

    # ── MDB Tab (original) ─────────────────────────────────────────────

    def _build_mdb_tab(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(
            parent, text=f"Source: {MDB_PATH}",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
            wraplength=700, justify="left",
        ).grid(row=0, column=0, sticky="w", padx=4, pady=(4, 12))

        counts_frame = ctk.CTkFrame(parent, fg_color=("gray88", "gray20"), corner_radius=8)
        counts_frame.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 12))
        counts_frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(
            counts_frame, text="Current database counts:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=16, pady=(12, 4))

        for col_i, (label, count) in enumerate([
            ("Exhibitors", Exhibitor.select().count()),
            ("Show Entries", ShowEntry.select().count()),
            ("Classes", ClassDef.select().count()),
        ]):
            ctk.CTkLabel(counts_frame, text=str(count),
                         font=ctk.CTkFont(size=28, weight="bold")).grid(
                row=1, column=col_i, padx=16, pady=(4, 2))
            ctk.CTkLabel(counts_frame, text=label,
                         font=ctk.CTkFont(size=11),
                         text_color=("gray50", "gray55")).grid(
                row=2, column=col_i, padx=16, pady=(0, 12))

        ctk.CTkLabel(
            parent,
            text="Re-importing will overwrite all table data. Results and calculated entries are preserved only if the MDB contains them.",
            font=ctk.CTkFont(size=11),
            text_color=("orange3", "orange"),
            wraplength=700, justify="left",
        ).grid(row=2, column=0, sticky="w", padx=4, pady=(0, 8))

        if not MDB_PATH.exists():
            ctk.CTkLabel(parent, text=f"⚠ MDB file not found at: {MDB_PATH}",
                         text_color=("red4", "tomato")).grid(
                row=3, column=0, sticky="w", padx=4, pady=(0, 8))

        self._mdb_log = ctk.CTkTextbox(
            parent, state="disabled", height=160,
            font=ctk.CTkFont(family="Courier New", size=11),
            fg_color=("gray95", "gray10"),
        )
        self._mdb_log.grid(row=4, column=0, sticky="nsew", padx=4, pady=(0, 8))

        self._mdb_bar = ctk.CTkProgressBar(parent, mode="indeterminate")
        self._mdb_bar.grid(row=5, column=0, padx=60, sticky="ew", pady=(0, 8))
        self._mdb_bar.stop()
        self._mdb_bar.set(0)

        self._mdb_btn = ctk.CTkButton(
            parent, text="Import from MDB", width=200, height=38,
            state="normal" if MDB_PATH.exists() else "disabled",
            command=self._mdb_start,
        )
        self._mdb_btn.grid(row=6, column=0, pady=(0, 8))

    def _mdb_log_append(self, msg):
        self._mdb_log.configure(state="normal")
        self._mdb_log.insert("end", msg + "\n")
        self._mdb_log.configure(state="disabled")
        self._mdb_log.see("end")

    def _mdb_start(self):
        self._mdb_log.configure(state="normal")
        self._mdb_log.delete("1.0", "end")
        self._mdb_log.configure(state="disabled")
        self._mdb_btn.configure(state="disabled")
        self._mdb_bar.configure(mode="indeterminate")
        self._mdb_bar.start()
        self._mdb_log_append("Starting import...")
        threading.Thread(target=self._mdb_run, daemon=True).start()

    def _mdb_run(self):
        try:
            from services.import_service import import_from_mdb
            results = import_from_mdb(
                progress=lambda msg: self.after(0, lambda m=msg: self._mdb_log_append(m))
            )
            total = sum(results.values())
            self.after(0, lambda: self._mdb_done(results, total))
        except Exception as e:
            self.after(0, lambda: self._mdb_error(str(e)))

    def _mdb_done(self, results, total):
        self._mdb_bar.stop()
        self._mdb_bar.configure(mode="determinate")
        self._mdb_bar.set(1.0)
        self._mdb_log_append(
            f"\nDone — {total} records imported. "
            f"Exhibitors: {results.get('exhibitors', 0)}, "
            f"Entries: {results.get('show_entries', 0)}."
        )
        self._mdb_btn.configure(state="normal", text="Import Again")

    def _mdb_error(self, msg):
        self._mdb_bar.stop()
        self._mdb_bar.set(0)
        self._mdb_log_append(f"\nError: {msg}")
        self._mdb_btn.configure(state="normal")

    # ── CSV Tab ────────────────────────────────────────────────────────

    def _build_csv_tab(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)

        self._csv_path = None
        self._csv_headers = []
        self._csv_mapping_vars: dict = {}   # field → StringVar
        self._csv_mapping_menus: dict = {}  # field → CTkOptionMenu

        # ── File picker ──────────────────────────────────────────────
        file_row = ctk.CTkFrame(parent, fg_color="transparent")
        file_row.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 8))

        self._csv_path_lbl = ctk.CTkLabel(
            file_row, text="No file selected",
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray55"),
        )
        self._csv_path_lbl.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            file_row, text="Browse CSV…", width=120,
            command=self._csv_browse,
        ).pack(side="right")

        ctk.CTkLabel(
            parent,
            text="Map CSV columns to exhibitor fields. Rows with a blank Name are skipped.",
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray55"),
        ).grid(row=1, column=0, sticky="w", padx=4, pady=(0, 6))

        # ── Column mapper ─────────────────────────────────────────────
        mapper_scroll = ctk.CTkScrollableFrame(
            parent, fg_color=("gray90", "gray17"), corner_radius=8, height=200,
        )
        mapper_scroll.grid(row=2, column=0, sticky="nsew", padx=4, pady=(0, 8))
        mapper_scroll.grid_columnconfigure(1, weight=1)
        self._mapper_frame = mapper_scroll

        # ── Actions ───────────────────────────────────────────────────
        btns = ctk.CTkFrame(parent, fg_color="transparent")
        btns.grid(row=3, column=0, sticky="ew", padx=4, pady=(0, 8))

        self._csv_mode_var = ctk.StringVar(value="upsert")
        ctk.CTkSegmentedButton(
            btns,
            values=["Add new only", "Update existing", "Replace all"],
            variable=self._csv_mode_var,
            command=lambda v: None,
        ).pack(side="left", padx=(0, 12))

        self._csv_import_btn = ctk.CTkButton(
            btns, text="Import Exhibitors", width=160, height=38,
            state="disabled",
            command=self._csv_import,
        )
        self._csv_import_btn.pack(side="right")

        self._csv_status = ctk.CTkLabel(
            parent, text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray55"),
            anchor="w",
        )
        self._csv_status.grid(row=4, column=0, sticky="ew", padx=4)

    def _csv_browse(self):
        path = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                headers = next(reader, [])
                sample_rows = [row for _, row in zip(range(4), reader)]
        except Exception as exc:
            messagebox.showerror("CSV Error", f"Could not read file:\n{exc}", parent=self)
            return

        self._csv_path = path
        self._csv_headers = headers
        self._csv_path_lbl.configure(text=path, text_color=("gray20", "gray80"))
        self._csv_build_mapper(headers)
        self._csv_import_btn.configure(state="normal")
        self._csv_status.configure(text=f"{len(headers)} column(s) detected")

    def _csv_build_mapper(self, headers: list):
        for w in self._mapper_frame.winfo_children():
            w.destroy()
        self._csv_mapping_vars.clear()
        self._csv_mapping_menus.clear()

        auto = _auto_match(headers)
        options = ["(skip)"] + headers

        self._mapper_frame.grid_columnconfigure(0, minsize=140)
        self._mapper_frame.grid_columnconfigure(1, weight=1)

        # Header row
        ctk.CTkLabel(
            self._mapper_frame, text="Field",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=(8, 4), pady=(4, 2))
        ctk.CTkLabel(
            self._mapper_frame, text="CSV Column",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="w", padx=4, pady=(4, 2))

        for row_i, (field, label) in enumerate(CSV_FIELDS, start=1):
            ctk.CTkLabel(
                self._mapper_frame, text=label,
                font=ctk.CTkFont(size=11),
                anchor="w",
            ).grid(row=row_i, column=0, sticky="w", padx=(8, 4), pady=2)

            var = ctk.StringVar(value=auto.get(field, "(skip)"))
            self._csv_mapping_vars[field] = var

            menu = ctk.CTkOptionMenu(
                self._mapper_frame,
                variable=var,
                values=options,
                width=200,
                height=28,
            )
            menu.grid(row=row_i, column=1, sticky="w", padx=4, pady=2)
            self._csv_mapping_menus[field] = menu

    def _csv_import(self):
        if not self._csv_path:
            return

        name_col = self._csv_mapping_vars.get("name", ctk.StringVar()).get()
        if name_col == "(skip)":
            messagebox.showwarning(
                "Mapping Required",
                "You must map the 'Name' column before importing.",
                parent=self,
            )
            return

        mapping = {
            field: var.get()
            for field, var in self._csv_mapping_vars.items()
            if var.get() != "(skip)"
        }

        mode = self._csv_mode_var.get()
        self._csv_import_btn.configure(state="disabled", text="Importing…")
        self._csv_status.configure(text="Reading CSV…", text_color=("gray45", "gray55"))

        threading.Thread(
            target=self._csv_run,
            args=(mapping, mode),
            daemon=True,
        ).start()

    def _csv_run(self, mapping: dict, mode: str):
        try:
            from models.database import database
            database.connect(reuse_if_open=True)

            added = updated = skipped = 0
            with open(self._csv_path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            if mode == "Replace all":
                Exhibitor.delete().execute()

            for row in rows:
                kwargs = {}
                for field, col in mapping.items():
                    val = row.get(col, "").strip()
                    if val:
                        kwargs[field] = val

                name = kwargs.get("name", "").strip()
                if not name:
                    skipped += 1
                    continue

                existing = Exhibitor.get_or_none(Exhibitor.name == name)

                if existing:
                    if mode == "Add new only":
                        skipped += 1
                        continue
                    for field, val in kwargs.items():
                        setattr(existing, field, val)
                    existing.save()
                    updated += 1
                else:
                    Exhibitor.create(**kwargs)
                    added += 1

            self.after(0, lambda a=added, u=updated, s=skipped: self._csv_done(a, u, s))
        except Exception as exc:
            self.after(0, lambda e=str(exc): self._csv_error(e))

    def _csv_done(self, added, updated, skipped):
        self._csv_import_btn.configure(state="normal", text="Import Exhibitors")
        self._csv_status.configure(
            text=f"Done — {added} added, {updated} updated, {skipped} skipped",
            text_color=("gray25", "gray75"),
        )

    def _csv_error(self, msg):
        self._csv_import_btn.configure(state="normal", text="Import Exhibitors")
        self._csv_status.configure(text=f"Error: {msg}", text_color=("red4", "tomato"))

    # ── Copy from DB Tab ───────────────────────────────────────────────

    def _build_db_tab(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(3, weight=1)

        self._src_db_path = None

        ctk.CTkLabel(
            parent,
            text="Select another Benchabird database (.db) to copy data from.\n"
                 "This is useful for merging show data or copying exhibitor lists between seasons.",
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray55"),
            wraplength=680, justify="left",
        ).grid(row=0, column=0, sticky="w", padx=4, pady=(4, 10))

        # File picker
        file_row = ctk.CTkFrame(parent, fg_color="transparent")
        file_row.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 8))

        self._db_path_lbl = ctk.CTkLabel(
            file_row, text="No file selected",
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray55"),
        )
        self._db_path_lbl.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            file_row, text="Browse DB…", width=120,
            command=self._db_browse,
        ).pack(side="right")

        # Table checkboxes
        self._db_tables_frame = ctk.CTkFrame(
            parent, fg_color=("gray90", "gray17"), corner_radius=8,
        )
        self._db_tables_frame.grid(row=2, column=0, sticky="ew", padx=4, pady=(0, 8))
        self._db_check_vars: dict = {}

        ctk.CTkLabel(
            self._db_tables_frame,
            text="Select which data to copy:",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(10, 4))

        for table, label in [
            ("exhibitor",   "Exhibitors"),
            ("show_entry",  "Show Entries"),
            ("class_def",   "Class Definitions"),
            ("show_details","Show Details"),
        ]:
            var = ctk.BooleanVar(value=(table == "exhibitor"))
            self._db_check_vars[table] = var
            ctk.CTkCheckBox(
                self._db_tables_frame,
                text=label,
                variable=var,
            ).pack(anchor="w", padx=20, pady=2)

        ctk.CTkFrame(self._db_tables_frame, height=8, fg_color="transparent").pack()

        # Actions
        btns = ctk.CTkFrame(parent, fg_color="transparent")
        btns.grid(row=4, column=0, sticky="ew", padx=4, pady=(0, 4))

        self._db_import_btn = ctk.CTkButton(
            btns, text="Copy Selected Data", width=180, height=38,
            state="disabled",
            command=self._db_import,
        )
        self._db_import_btn.pack(side="right")

        self._db_status = ctk.CTkLabel(
            parent, text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray55"),
            anchor="w",
        )
        self._db_status.grid(row=5, column=0, sticky="ew", padx=4)

    def _db_browse(self):
        path = filedialog.askopenfilename(
            title="Select Benchabird database",
            filetypes=[("SQLite DB", "*.db"), ("All files", "*.*")],
        )
        if not path:
            return
        self._src_db_path = path
        self._db_path_lbl.configure(text=path, text_color=("gray20", "gray80"))
        self._db_import_btn.configure(state="normal")

        # Show source counts
        try:
            import sqlite3
            conn = sqlite3.connect(path)
            parts = []
            for tbl in ("exhibitor", "show_entry", "class_def"):
                try:
                    n = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
                    parts.append(f"{tbl}: {n}")
                except Exception:
                    pass
            conn.close()
            self._db_status.configure(
                text="Source — " + ", ".join(parts) if parts else "Source DB opened",
                text_color=("gray45", "gray55"),
            )
        except Exception as exc:
            self._db_status.configure(
                text=f"Could not read source: {exc}",
                text_color=("red4", "tomato"),
            )
            self._db_import_btn.configure(state="disabled")

    def _db_import(self):
        if not self._src_db_path:
            return
        tables = [t for t, v in self._db_check_vars.items() if v.get()]
        if not tables:
            messagebox.showwarning("Nothing Selected", "Select at least one table to copy.", parent=self)
            return

        if not messagebox.askyesno(
            "Confirm Copy",
            f"This will replace data in: {', '.join(tables)}.\n\nContinue?",
            parent=self,
        ):
            return

        self._db_import_btn.configure(state="disabled", text="Copying…")
        self._db_status.configure(text="Working…", text_color=("gray45", "gray55"))
        threading.Thread(target=self._db_run, args=(tables,), daemon=True).start()

    def _db_run(self, tables: list):
        try:
            import sqlite3
            from models.database import database
            database.connect(reuse_if_open=True)

            src = sqlite3.connect(self._src_db_path)
            counts = {}
            for tbl in tables:
                try:
                    cols = [r[1] for r in src.execute(f"PRAGMA table_info({tbl})").fetchall()]
                    rows = src.execute(f"SELECT * FROM {tbl}").fetchall()
                    database.execute_sql(f"DELETE FROM {tbl}")
                    if rows:
                        placeholders = ", ".join(["?"] * len(cols))
                        col_list = ", ".join(cols)
                        sql = f"INSERT INTO {tbl} ({col_list}) VALUES ({placeholders})"
                        for row in rows:
                            database.execute_sql(sql, row)
                    counts[tbl] = len(rows)
                except Exception as exc:
                    counts[tbl] = f"ERR: {exc}"
            src.close()
            self.after(0, lambda c=counts: self._db_done(c))
        except Exception as exc:
            self.after(0, lambda e=str(exc): self._db_error(e))

    def _db_done(self, counts: dict):
        self._db_import_btn.configure(state="normal", text="Copy Selected Data")
        parts = [f"{tbl}: {n}" for tbl, n in counts.items()]
        self._db_status.configure(
            text="Done — " + ", ".join(parts),
            text_color=("gray25", "gray75"),
        )

    def _db_error(self, msg: str):
        self._db_import_btn.configure(state="normal", text="Copy Selected Data")
        self._db_status.configure(text=f"Error: {msg}", text_color=("red4", "tomato"))
