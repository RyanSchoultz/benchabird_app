# views/help_view.py
"""In-app how-to guide — tabbed reference for all major workflows."""
import sys
import threading
import webbrowser
from tkinter import messagebox

import customtkinter as ctk

_KOFI_URL = "https://ko-fi.com/schoultzie"


SECTIONS = {
    "Getting Started": [
        ("First Launch", (
            "When you start Benchabird for the first time the app creates a fresh "
            "database automatically — you can begin entering data right away.\n\n"
            "If you are migrating from a legacy Access MDB file, go to Import Data "
            "in the admin section of the sidebar. The import wizard loads exhibitors, "
            "class definitions, special prizes, Hall of Fame records, and brochure "
            "notes from the MDB file. The log shows progress for each table.\n\n"
            "If you want to start from scratch, skip the import wizard and add your "
            "data directly through the Exhibitors and Entries views."
        )),
        ("Sidebar Navigation", (
            "Use the left sidebar to move between sections.\n\n"
            "Main section:\n"
            "  Dashboard          — live show progress overview\n"
            "  Search             — global search across all data (Ctrl+F)\n"
            "  Show Setup         — show name, date, club, logo, ticket barcode type\n"
            "  Exhibitors         — browse and manage the master exhibitor registry (Ctrl+X)\n"
            "  Show Participants  — entries, benching, and late entries in one view (Ctrl+B / Ctrl+E)\n"
            "  Results            — enter and review judging results (Ctrl+R)\n"
            "  Special Winners    — assign special prize winners\n"
            "  Special Prizes     — manage the prize list\n"
            "  Tickets            — print cage tickets (Ctrl+T)\n"
            "  Reports            — generate PDF reports\n"
            "  Hall of Fame       — historical records (read-only)\n"
            "  Class Glossary     — searchable class definitions and descriptions\n"
            "  Help               — this guide (Ctrl+H)\n\n"
            "Admin section (below the divider):\n"
            "  Import Data  — re-import from Access MDB\n"
            "  Reset Data   — clear all show-year data\n"
            "  Archives     — save and restore database snapshots\n"
            "  SQL Editor   — direct SQL access for advanced users"
        )),
        ("Recommended Show Workflow", (
            "Follow these steps in order for a typical show:\n\n"
            "1. Show Setup — enter show name, date, club details, upload logo\n"
            "2. Exhibitors — add all registered exhibitors (or import from CSV/Excel)\n"
            "3. Show Participants — add each exhibitor's class entries before the show\n"
            "4. Show Participants — on show day, bench arrived birds to allocate exhibit numbers\n"
            "   Late entries and corrections are handled in the same view\n"
            "5. Tickets — print cage tickets for exhibitors to attach to cages\n"
            "6. Reports — print the Judges Catalogue for judges to complete by hand\n"
            "7. Results — use Judging Capture to enter completed sheets by category\n"
            "8. Special Winners — assign special prize winners by exhibit number\n"
            "9. Reports — generate Results Sheet, Show Catalogue, Prize Money, etc.\n"
            "10. Archive (optional) — save a snapshot before resetting for next season\n\n"
            "Entries and exhibitors can be added at any time. Show Participants handles "
            "pre-show entries, show-day benching, and late entries all in one place."
        )),
        ("Keyboard Shortcuts", (
            "Global navigation shortcuts:\n\n"
            "  Ctrl+F   — Search\n"
            "  Ctrl+B   — Show Participants\n"
            "  Ctrl+E   — Show Participants\n"
            "  Ctrl+R   — Results\n"
            "  Ctrl+T   — Tickets\n"
            "  Ctrl+X   — Exhibitors\n"
            "  Ctrl+H   — Help (this view)\n\n"
            "Context shortcuts:\n\n"
            "  Results view\n"
            "    Enter on Exhibit # field  — moves focus to Result dropdown\n"
            "    Enter on Result dropdown  — saves the result\n\n"
            "  Results scanner buttons\n"
            "    Scan QR      — opens the desktop webcam scanner\n"
            "    Mobile Scan  — starts the temporary phone companion receiver\n\n"
            "  SQL Editor\n"
            "    Ctrl+Enter  — run the current query\n\n"
            "  Most dialogs\n"
            "    Escape  — close without saving"
        )),
        ("Updates", (
            "Click Check for Updates at the bottom of this Help view to check the "
            "latest GitHub release.\n\n"
            "In the packaged exe, Benchabird prompts before downloading, closes, "
            "replaces the exe through a helper script, restarts, and then shows the "
            "release changelog. When running from source, update checks can report "
            "availability but will not replace python.exe."
        )),
    ],

    "Setup & Logo": [
        ("Show Details", (
            "Go to Show Setup and fill in:\n\n"
            "  • Show Name (English and Afrikaans)\n"
            "  • Date (English and Afrikaans)\n"
            "  • Club Code and Club Full Name (English and Afrikaans)\n"
            "  • Association\n\n"
            "Click Save. These details appear at the top of every generated PDF report."
        )),
        ("Club Logo", (
            "1. In Show Setup, click Browse… next to Club Logo\n"
            "2. Select a PNG or JPG image file\n"
            "3. The logo appears immediately in the preview box below the buttons\n"
            "4. The image is stored as bytes inside the database — the original file "
            "is not needed again and the logo travels with the database file\n\n"
            "The logo is applied as a faded watermark centered on every PDF report page "
            "and on every cage ticket page. It does not overlap any text.\n\n"
            "Click Clear to remove the logo from the database."
        )),
    ],

    "Exhibitors": [
        ("Adding an Exhibitor", (
            "1. Click + Add in the toolbar\n"
            "2. Fill in the exhibitor number, name, address, suburb, town, zip code, "
            "phone, cell, email, and club\n"
            "3. Tick Include in address label print run if this exhibitor should appear "
            "on the Address Tags PDF report\n"
            "4. Click Save\n\n"
            "The exhibitor number must be unique. An error message appears if the number "
            "is already in use."
        )),
        ("Editing and Deleting", (
            "Select a row in the table by clicking it, then:\n\n"
            "  • Click Edit to open the edit dialog — make changes and click Save\n"
            "  • Click Delete to permanently remove the exhibitor\n\n"
            "Deleting an exhibitor does not automatically remove their entries. "
            "Use Bulk Edit in the Entries view to delete entries by exhibitor number."
        )),
        ("Address Labels", (
            "The Address Tags report prints mailing labels only for exhibitors whose "
            "Include in label print run flag is ticked.\n\n"
            "The Labels column in the table shows a ✓ for flagged exhibitors.\n\n"
            "To toggle the flag quickly without opening the edit dialog:\n"
            "1. Select an exhibitor row in the table\n"
            "2. Click Toggle Labels in the toolbar\n\n"
            "You can also tick the checkbox when adding or editing an exhibitor."
        )),
        ("Searching and Exporting", (
            "Search: type in the search box at the right of the toolbar. The table "
            "filters live as you type, matching on name and email.\n\n"
            "Export: click Export to save the current filtered list to a file. "
            "A save dialog lets you choose CSV (.csv) or Excel (.xlsx). "
            "The exported file includes all columns: exhibitor number, name, address, "
            "suburb, town, zip, phone, cell, email, club, and label flag."
        )),
    ],

    "Show Participants": [
        ("Left Panel — Participant List", (
            "The left panel lists all exhibitors who have at least one entry in the current show.\n\n"
            "Filter chips:\n"
            "  All        — all participants\n"
            "  Unbenched  — participants with at least one bird not yet benched\n"
            "  Late       — participants with at least one late entry\n\n"
            "Search box searches name, exhibitor number, email, and class code.\n"
            "Typing a name that is in the Exhibitors registry but not yet in the show "
            "surfaces them under 'Registry (not in this show)' — click to add them. "
            "If they have no exhibitor number, an inline prompt assigns the next available one.\n\n"
            "A warning banner appears at the top of the panel if any entry has an "
            "exhibitor number with no matching Exhibitor record."
        )),
        ("Adding and Managing Entries", (
            "Select an exhibitor from the left panel to open their entry list on the right.\n\n"
            "Add Entry:\n"
            "1. Click + Add Entry\n"
            "2. The exhibitor number is pre-filled and locked\n"
            "3. Select or type the class code\n"
            "4. An orange warning appears for duplicates\n"
            "5. Press Enter or click Save\n\n"
            "Add Late Entry:\n"
            "1. Click + Add Late Entry\n"
            "2. Exhibitor number and name are pre-filled\n"
            "3. Enter the class code and click Save\n\n"
            "Late entries appear in the same list as regular entries with a LATE badge. "
            "They are tracked separately in the database for reporting purposes.\n\n"
            "Per-class limits apply to both regular and late entries."
        )),
        ("Benching Arrivals", (
            "Use Show Participants on show day when exhibitors arrive with their birds.\n\n"
            "1. Search by name, email, or exhibitor number in the left panel\n"
            "2. Select the exhibitor\n"
            "3. Click Select Unbenched to tick all birds not yet benched, or tick individually\n"
            "4. Click Bench Selected\n\n"
            "Birds are allocated exhibit numbers in class-sequence order. "
            "Already-benched birds show their exhibit number, for example Benched #42. "
            "Late entries are benched the same way — they show LATE · Benched #N when done."
        )),
        ("Unbenching", (
            "Tick the birds you want to remove and click Unbench Selected.\n\n"
            "Unbenching is blocked once an exhibit has a result, an NB mark, or a special winner reference. "
            "The status badge shows the reason and the checkbox is disabled for those birds."
        )),
        ("Auto-Calculate", (
            "Exhibit numbers are kept current automatically.\n\n"
            "Before show day (no birds individually benched yet), numbers recalculate "
            "silently whenever you add or remove an entry — no manual step needed.\n\n"
            "Once show-day benching starts, recalculating would renumber birds that "
            "already have printed tickets. Instead, a notice appears:\n"
            "  'Entries changed — bench numbers may be stale'\n\n"
            "Click Recalculate in that notice and confirm to reassign numbers for "
            "unbenched entries. Benched birds keep their existing numbers.\n\n"
            "Once results are recorded, recalculate is blocked entirely."
        )),
    ],

    "Results": [
        ("Rapid Entry Mode", (
            "The Results view is designed for fast entry during judging:\n\n"
            "1. Type the exhibit number in the Exhibit # field\n"
            "2. Press Enter — focus moves to the Result dropdown\n"
            "3. Select the result (1st, 2nd, 3rd, 4th, 5th, BOB, R/U BOB, Champion, Reserve)\n"
            "4. Press Enter — the result is saved and focus returns to Exhibit #\n"
            "5. Repeat for the next exhibit\n\n"
            "Scanned QR payloads follow the same flow: a successful scan fills the "
            "Exhibit # field and moves focus to the Result dropdown. The result is "
            "not saved until you choose the placing and press Enter.\n\n"
            "This flow lets you enter results without touching the mouse. "
            "If an exhibit already has a result, it is updated with the new value."
        )),
        ("Judging Capture", (
            "Judging Capture is for entering completed paper Judges Catalogue sheets after judging.\n\n"
            "1. Go to Reports and print the Judges Catalogue\n"
            "2. Give the sheets to the judges to complete by hand\n"
            "3. Open Results and click Judging Capture\n"
            "4. Select the category from the dropdown\n"
            "5. If needed, change the exhibit's class before saving\n"
            "6. For each exhibit, choose a placing, NB, or Clear using the radio buttons\n"
            "7. Click Save Category Results at the end of the category/page\n\n"
            "Only changed rows are saved. Rapid Entry remains available for corrections, "
            "scanner entry, and one-off result changes."
        )),
        ("Not Benched", (
            "If a bird was not brought to the show:\n"
            "1. Type the exhibit number in the Exhibit # field\n"
            "2. Click Not Benched\n\n"
            "The exhibit appears in the table with NB shown in red in the NB column. "
            "Clicking Not Benched again on the same exhibit number removes the flag.\n\n"
            "Not-benched entries are highlighted in the Results Sheet PDF report."
        )),
        ("QR Scanner Entry", (
            "Cage-ticket QR codes include AutoNum, exhibitor number, and class code.\n\n"
            "USB scanner:\n"
            "1. Click the Exhibit # field\n"
            "2. Scan the ticket QR code\n"
            "3. Choose the result and press Enter to save\n"
            "Most USB barcode/QR scanners act like keyboards.\n\n"
            "Webcam scanner:\n"
            "1. Click Scan QR\n"
            "2. Hold the cage-ticket QR code in front of the desktop webcam\n"
            "3. When the scan is accepted, choose the result and press Enter to save\n\n"
            "Mobile companion scanner:\n"
            "1. Click Mobile Scan\n"
            "2. Scan the pairing QR with a phone on the same Wi-Fi/network\n"
            "3. Use the phone page to scan or submit a ticket QR payload\n"
            "4. When the desktop accepts the scan, choose the result and press Enter to save\n"
            "The phone only sends scan payloads. Results are still selected and saved "
            "on the desktop.\n\n"
            "Phone browser camera support depends on browser security rules. "
            "If camera scanning is blocked, use the text field on the phone page "
            "with a phone QR scanner app or pasted payload. If the phone cannot "
            "connect, check that both devices are on the same Wi-Fi/network and "
            "that Windows Firewall allows Benchabird on the local/private network.\n\n"
            "Pasted or scanned legacy QR text with ExhNo and Class is still accepted "
            "when it uniquely matches a calculated entry.\n\n"
            "If the webcam, OpenCV scanner dependency, phone camera, or local network "
            "is unavailable, manual entry and USB scanner entry still work."
        )),
        ("Filter and Export", (
            "The filter bar below the toolbar filters the results table live by exhibit "
            "number or result value.\n\n"
            "Click Export to save all results (including NB flags) to CSV or Excel. "
            "The exported file includes: exhibit number, result, and not-benched status."
        )),
        ("Clear All Results", (
            "Click Clear All Results in the top-right of the toolbar to remove every "
            "recorded result. A confirmation dialog appears before any data is deleted.\n\n"
            "This is useful when you need to re-judge a category or start over. "
            "Not-benched flags are not cleared by this action — use the SQL Editor "
            "to clear not_benched records if needed."
        )),
    ],

    "Tickets & Reports": [
        ("Printing Cage Tickets", (
            "Before printing, use Check-in to bench arrived birds and allocate exhibit numbers.\n\n"
            "1. Navigate to Tickets\n"
            "2. The table shows all assigned tickets with exhibitor details\n"
            "3. Use the filter bar to check specific exhibitors\n"
            "4. Click Print All Tickets\n"
            "5. Choose a save location — the PDF opens automatically after saving\n\n"
            "Each ticket contains:\n"
            "  • Large ticket number (#042)\n"
            "  • Class code\n"
            "  • Exhibitor number and name\n"
            "  • Show name\n"
            "  • QR code (top-right) encoding AutoNum, ExhNo, and Class\n"
            "  • Club logo watermark (if set in Show Setup)\n\n"
            "Tickets are printed 21 per A4 page (3 columns × 7 rows)."
        )),
        ("Generating PDF Reports", (
            "Click any report button in the Reports view to generate it:\n\n"
            "  Entries Received  — all benched entries in exhibit-number order\n"
            "  Show Catalogue    — entries grouped by class with section headers\n"
            "  4.1 Judges Catalogue  - printable judging sheet with placing and NB boxes\n"
            "  4.2 Special Lists     - special prize list for catalogue printing\n"
            "  4.3 Catalogue         - Access-style show catalogue\n"
            "  4.4 Marked Catalogue  - catalogue with result/NB/special markings\n"
            "  Results Sheet     — all results; not-benched rows shown in red\n"
            "  Special Winners   — all special prizes and their assigned winners\n"
            "  Prize Money       — cash prizes with per-exhibitor subtotals\n"
            "  Address Tags      — 3-column mailing labels (label-flagged exhibitors only)\n"
            "  Exhibitor List    — all exhibitors with entry and late-entry counts\n"
            "  Entry Confirmation — exhibitor entry confirmation sheets\n"
            "  Exhibitor Bundle  — one selected exhibitor's paperwork\n"
            "  Results by Exhibitor — results grouped by exhibitor\n\n"
            "All reports include the show name, date, club, and the club logo watermark "
            "(if configured). Generation runs in the background — the preview opens "
            "automatically when complete."
        )),
        ("Exhibitor Bundle", (
            "Use Exhibitor Bundle when you need one exhibitor's paperwork in a single PDF.\n\n"
            "1. Go to Reports\n"
            "2. Click Exhibitor Bundle\n"
            "3. Search by exhibitor name, exhibitor number, exhibit number, email, or club\n"
            "4. Select the exhibitor and choose the bundle sections\n"
            "5. Preview, print, or save the generated PDF\n\n"
            "Bundles can include exhibitor details, entries, cage tickets after Check-in, late entries, "
            "results when recorded, and an address label when the exhibitor is flagged for labels. "
            "If an exhibitor number is not assigned, the bundle still uses the selected exhibitor row and "
            "matches calculated or late entries by exhibitor name."
        )),
        ("PDF Preview Window", (
            "The preview window opens after any report or ticket PDF is generated.\n\n"
            "Navigation:\n"
            "  ← Prev / Next →  — move between pages\n"
            "  Page N / M label — shows current page and total\n\n"
            "Actions:\n"
            "  Print…    — opens the OS print dialog with the PDF pre-loaded\n"
            "  Save As…  — save to a location of your choice; on Windows the PDF "
            "opens automatically in your default viewer after saving\n"
            "  Close     — dismiss the preview without saving"
        )),
    ],

    "Search & Filter": [
        ("Global Search", (
            "Press Ctrl+F or click Search in the sidebar to open the global search view.\n\n"
            "Type your query in the search box. Results appear automatically after a "
            "short pause and are grouped into five categories:\n\n"
            "  Exhibitors       — matched by name or exhibitor number\n"
            "  Entries          — raw entries matched by exhibitor number or class code\n"
            "  Calculated       — calculated entries matched by name, number, or class\n"
            "  Results          — matched by exhibit number or result value\n"
            "  Special Winners  — matched by prize description or winner name\n\n"
            "Up to 8 results per category are shown. If there are more, a "
            "View all N → link appears to navigate to the full view.\n\n"
            "Each result has a → button to jump directly to that record."
        )),
        ("Per-View Filters", (
            "Every table view has a filter bar below the toolbar.\n\n"
            "Type in the filter box — the visible rows update live without re-querying "
            "the database. All data is loaded once and filtered in memory, so filtering "
            "is instant regardless of table size.\n\n"
            "Click the ✕ button to clear the filter and show all rows again.\n\n"
            "The status label (next to the toolbar title) shows how many rows are "
            "visible vs. the total, e.g. 12 of 559 tickets."
        )),
    ],

    "Archives": [
        ("Saving a Snapshot", (
            "Archives save a complete copy of the entire database at a point in time. "
            "Use them before resetting at the end of a show season, or before making "
            "bulk changes you might want to undo.\n\n"
            "1. Go to Archives (admin section in the sidebar)\n"
            "2. Type a descriptive name in the Save current show as field\n"
            "   (e.g. 2025 Western Cape Regional Show)\n"
            "3. Click Save Snapshot\n\n"
            "The snapshot appears in the archive list with its name, date, time, "
            "and file size. Snapshots are stored in an archives/ folder alongside "
            "the main database file."
        )),
        ("Restoring a Snapshot", (
            "Restoring replaces all current data with the saved snapshot.\n\n"
            "1. Find the snapshot in the archive list\n"
            "2. Click Restore\n"
            "3. Read the confirmation dialog — it explains exactly what will be replaced\n"
            "4. Click Yes to proceed\n\n"
            "After restoring, the app navigates to the Dashboard with the restored data "
            "loaded. The previous database state is permanently overwritten.\n\n"
            "Tip: if you want to keep the current state, save a new snapshot before "
            "restoring an older one."
        )),
        ("Deleting a Snapshot", (
            "Select a snapshot in the archive list and click Delete. "
            "A confirmation dialog appears before the file is removed. "
            "Deleted snapshots cannot be recovered."
        )),
    ],

    "Data Management": [
        ("Reset Data", (
            "Reset Data permanently deletes all show-year data:\n\n"
            "  ✓ Removed: all show entries, calculated entries, late entries, "
            "results, not-benched flags, and special winner assignments\n\n"
            "  ✗ Kept: exhibitors, class definitions, special prize list, "
            "Hall of Fame records, brochure notes, and show details\n\n"
            "Use Reset Data at the start of a new show season. A confirmation "
            "dialog explains what will be deleted before any action is taken.\n\n"
            "Best practice: save an Archive snapshot before resetting."
        )),
        ("Import Data (from MDB)", (
            "Go to Import Data in the admin section to load data from a legacy "
            "Microsoft Access MDB file.\n\n"
            "The import wizard loads:\n"
            "  • Exhibitors\n"
            "  • Class definitions\n"
            "  • Special prize list\n"
            "  • Hall of Fame records\n"
            "  • Brochure notes\n\n"
            "Existing records in those tables are overwritten. Show entries and "
            "results are not affected.\n\n"
            "The MDB file path is configured in config.py and cannot be changed "
            "from within the app."
        )),
        ("Class Glossary", (
            "The Class Glossary is a read-only lookup of class definitions imported "
            "from the legacy Access Classes_T data. It is seeded into a fast lookup "
            "table on launch and after legacy import.\n\n"
            "Use the species dropdown as a group filter, then use the filter box "
            "to search class codes, bird type, main class, "
            "description text, Afrikaans description text, or extra TYPEB text.\n\n"

            "For large imported class lists, the view shows the first 250 matches "
            "to keep the app responsive. Type part of a class, type, or description "
            "to narrow the list.\n\n"

            "The displayed description follows the Judges Catalogue/report pattern: "
            "colour plus AFRBESK when both are available. Edit class definitions "
            "through import data or the SQL Editor."
        )),
        ("Hall of Fame", (
            "The Hall of Fame view shows historical champion records imported "
            "from the Access database. Records are sorted by year (most recent first) "
            "and then by bird type abbreviation.\n\n"
            "This view is read-only. Records cannot be added or edited from within "
            "the app. To modify Hall of Fame records, use the SQL Editor."
        )),
    ],

    "SQL Editor": [
        ("What It Is", (
            "The SQL Editor gives direct read/write access to the SQLite database "
            "that powers Benchabird. It is intended for advanced users who are "
            "comfortable writing SQL queries.\n\n"
            "Common uses:\n"
            "  • Bulk corrections that the normal UI does not support\n"
            "  • Checking data counts and totals\n"
            "  • Exporting specific data combinations\n"
            "  • Investigating unexpected results\n\n"
            "The editor is in the SQL Editor item in the admin section of the sidebar."
        )),
        ("Running a Query", (
            "1. Type or paste your SQL into the editor (Courier New font)\n"
            "2. Press Ctrl+Enter or click ▶ Run to execute\n"
            "3. Results appear in the scrollable table below (up to 500 rows)\n"
            "4. The status bar shows the row count or an error message\n\n"
            "Click Tables… to auto-run a query listing all tables in the database. "
            "This is a quick way to explore the schema.\n\n"
            "Comments starting with -- are supported and ignored during execution."
        )),
        ("Write Queries", (
            "INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, and TRUNCATE queries "
            "require confirmation before running. A dialog explains what you are "
            "about to do and gives you the chance to cancel.\n\n"
            "There is no automatic undo for write operations. Save an Archive "
            "snapshot before making bulk changes with the SQL Editor."
        )),
        ("Key Tables", (
            "show_details       — show name, date, club, logo bytes\n"
            "exhibitor          — all exhibitors\n"
            "show_entry         — raw pre-show entries before Check-in\n"
            "calculated_entry   — benched birds with allocated exhibit numbers\n"
            "late_entry         — late entries\n"
            "result             — judging results\n"
            "not_benched        — exhibit numbers marked Not Benched\n"
            "special_list       — special prize definitions\n"
            "special_winner     — special prize winner assignments\n"
            "class_def          — class code definitions\n"
            "species            - imported species/category reference rows\n"
            "class_glossary     - seeded searchable glossary rows\n"
            "hall_of_fame       — historical champion records\n"
            "notes_brochure     — brochure text per bird type\n\n"
            "Run SELECT name FROM sqlite_master WHERE type='table' ORDER BY name; "
            "to get the full list of tables at any time."
        )),
    ],
}


class HelpView(ctk.CTkFrame):
    """In-app how-to guide with tabbed sections."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self, text="Help & How-To Guide",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))

        tabs = ctk.CTkTabview(self)
        tabs.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 8))

        # Ko-fi support strip
        support = ctk.CTkFrame(self, fg_color="transparent")
        support.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))
        support.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            support,
            text="Benchabird is free and open-source. If it helps your club, consider supporting development:",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=(0, 12))
        ctk.CTkButton(
            support,
            text="Support on Ko-fi",
            width=140,
            height=28,
            fg_color="#ff5e5b",
            hover_color="#e84d4a",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: webbrowser.open(_KOFI_URL),
        ).grid(row=0, column=1, sticky="e")
        self._update_status = ctk.CTkLabel(
            support,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
        )
        self._update_status.grid(row=1, column=0, sticky="w", pady=(6, 0))
        ctk.CTkButton(
            support,
            text="Check for Updates",
            width=140,
            height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._check_for_updates,
        ).grid(row=1, column=1, sticky="e", pady=(6, 0))

        for section_name, topics in SECTIONS.items():
            tab = tabs.add(section_name)
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)

            scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
            scroll.grid(row=0, column=0, sticky="nsew")
            scroll.grid_columnconfigure(0, weight=1)

            for row_i, (topic_title, topic_body) in enumerate(topics):
                ctk.CTkLabel(
                    scroll,
                    text=topic_title,
                    font=ctk.CTkFont(size=13, weight="bold"),
                    anchor="w",
                ).grid(row=row_i * 2, column=0, sticky="w", padx=8, pady=(18, 2))

                ctk.CTkLabel(
                    scroll,
                    text=topic_body,
                    font=ctk.CTkFont(size=12),
                    anchor="w",
                    justify="left",
                    wraplength=700,
                ).grid(row=row_i * 2 + 1, column=0, sticky="w", padx=20, pady=(0, 4))

    def _check_for_updates(self):
        self._update_status.configure(text="Checking for updates...")

        def run():
            try:
                from services.update_service import check_for_update

                info = check_for_update()
                self.after(0, lambda: self._update_check_done(info))
            except Exception as exc:
                self.after(0, lambda: self._update_check_error(str(exc)))

        threading.Thread(target=run, daemon=True).start()

    def _update_check_done(self, info):
        if info is None:
            self._update_status.configure(text="Benchabird is up to date.")
            messagebox.showinfo("Benchabird Updates", "You are already running the latest version.")
            return

        if not getattr(sys, "frozen", False):
            self._update_status.configure(text=f"Update {info.version} available; packaged exe required.")
            messagebox.showinfo(
                "Benchabird Update Available",
                f"Version {info.version} is available, but automatic replacement only works in the packaged exe.\n\n{info.changelog}",
            )
            return

        should_download = messagebox.askyesno(
            "Benchabird Update Available",
            f"Version {info.version} is available.\n\n{info.changelog}\n\nDownload and restart now?",
        )
        if not should_download:
            self._update_status.configure(text="Update cancelled.")
            return

        self._update_status.configure(text=f"Downloading {info.asset_name}...")

        def run_download():
            try:
                from services.update_service import download_update, install_downloaded_update

                downloaded = download_update(info)
                install_downloaded_update(downloaded, info.changelog)
                self.after(0, self.winfo_toplevel().destroy)
            except Exception as exc:
                self.after(0, lambda: self._update_check_error(str(exc)))

        threading.Thread(target=run_download, daemon=True).start()

    def _update_check_error(self, message: str):
        self._update_status.configure(text=f"Update check failed: {message[:80]}")
        messagebox.showerror("Benchabird Updates", message)
