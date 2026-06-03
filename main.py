# benchabird_app/main.py
import shutil
import customtkinter as ctk
from config import BASE_DIR, DB_PATH
from models.database import database
from models import ALL_MODELS
from views.main_window import MainWindow
from views.import_wizard import ImportWizard

def _seed_db():
    """Copy pre-bundled database on first launch (frozen exe only)."""
    if DB_PATH.exists():
        return
    seed = BASE_DIR / "benchabird.db"
    if seed.exists() and seed.resolve() != DB_PATH.resolve():
        shutil.copy(seed, DB_PATH)

def _migrate_db():
    for sql in [
        "ALTER TABLE show_details ADD COLUMN logo_path VARCHAR(500)",
        "ALTER TABLE show_details ADD COLUMN logo_data BLOB",
        "ALTER TABLE class_def ADD COLUMN entry_limit INTEGER",
        "ALTER TABLE class_def ADD COLUMN judge VARCHAR(100)",
        "ALTER TABLE calculated_entry ADD COLUMN source_entry_auto_num INTEGER",
        "ALTER TABLE calculated_entry ADD COLUMN source_late_entry_auto_num INTEGER",
        "ALTER TABLE show_details ADD COLUMN barcode_type VARCHAR(10)",
    ]:
        try:
            database.execute_sql(sql)
        except Exception:
            pass  # column already exists

def init_db():
    database.connect(reuse_if_open=True)
    database.create_tables(ALL_MODELS, safe=True)
    _migrate_db()
    from services.class_glossary_service import seed_class_glossary

    seed_class_glossary()

def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    _seed_db()
    init_db()
    app = MainWindow()
    # First-launch: show import wizard only if no data (seed DB not available)
    from models.exhibitor import Exhibitor
    if Exhibitor.select().count() == 0:
        wizard = ImportWizard(app)
        app.wait_window(wizard)
    app.navigate("welcome")
    app.mainloop()

if __name__ == "__main__":
    main()
