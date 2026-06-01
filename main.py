# benchabird_app/main.py
import customtkinter as ctk
from models.database import database
from models import ALL_MODELS
from views.main_window import MainWindow
from views.import_wizard import ImportWizard

def _migrate_db():
    try:
        database.execute_sql(
            "ALTER TABLE show_details ADD COLUMN logo_path VARCHAR(500)"
        )
    except Exception:
        pass  # column already exists

def init_db():
    database.connect(reuse_if_open=True)
    database.create_tables(ALL_MODELS, safe=True)
    _migrate_db()

def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    init_db()
    app = MainWindow()
    # First-launch: show import wizard if no data
    from models.exhibitor import Exhibitor
    if Exhibitor.select().count() == 0:
        wizard = ImportWizard(app)
        app.wait_window(wizard)
    app.mainloop()

if __name__ == "__main__":
    main()
