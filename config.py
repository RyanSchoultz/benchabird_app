# benchabird_app/config.py
from pathlib import Path
import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
    DATA_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR

DB_PATH = DATA_DIR / "benchabird.db"

MDB_PATH = Path(
    r"C:\Users\Ryan\Downloads\access_mdb_analysis_export"
    r"\a.001National 2023 NewBugi.mdb"
)
MDB_CONN_STR = (
    r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
    f"DBQ={MDB_PATH};"
)

APP_NAME = "Benchabird Show Manager"
APP_VERSION = "1.0.0"
