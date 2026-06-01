# services/export_service.py
"""Export table data to CSV or Excel via a save-as dialog."""
import pandas as pd
from tkinter import filedialog


def export_data(rows: list, headers: list, default_name: str = "export.csv") -> str | None:
    """
    Open save-as dialog, then write rows/headers to CSV or Excel.
    Returns the saved path, or None if cancelled.
    rows: list of lists (one per row, same length as headers).
    """
    path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV file", "*.csv"), ("Excel file", "*.xlsx")],
        initialfile=default_name,
        title="Export Data",
    )
    if not path:
        return None
    df = pd.DataFrame(rows, columns=headers)
    if path.lower().endswith(".xlsx"):
        df.to_excel(path, index=False)
    else:
        df.to_csv(path, index=False)
    return path
