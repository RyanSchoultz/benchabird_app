# views/help_view.py
"""In-app how-to guide — tabbed reference for all major workflows."""
import customtkinter as ctk


SECTIONS = {
    "Getting Started": [
        ("First Launch", (
            "When you start Benchabird for the first time with an empty database, "
            "the Import Wizard will appear automatically.\n\n"
            "Click 'Import from MDB' to load all exhibitors, classes, special prizes, "
            "Hall of Fame records, and brochure notes from the Access MDB file. "
            "The log shows progress for each table.\n\n"
            "If you want to start fresh without importing, click 'Skip (start empty)'."
        )),
        ("Navigation", (
            "Use the left sidebar to navigate between sections:\n\n"
            "• Dashboard — Show Setup\n"
            "• Exhibitors — Browse all registered exhibitors\n"
            "• Entries — Raw show entries and calculated entries\n"
            "• Late Entries — Entries submitted after closing\n"
            "• Results — Record judging results\n"
            "• Special Winners — Assign special prize winners\n"
            "• Special Prizes — Manage the special prize list\n"
            "• Tickets — Print cage tickets after Calculate\n"
            "• Reports — Generate and preview PDF reports\n"
            "• Hall of Fame — Historical records (read-only)\n"
            "• Notes — Edit brochure notes per bird type\n\n"
            "Admin section (below the divider):\n"
            "• Import Data — Re-import from MDB\n"
            "• Reset Data — Clear all show-year data"
        )),
        ("Show Setup", (
            "Go to Show Setup to enter the show name, date, club name, and association "
            "in both English and Afrikaans. These details appear at the top of all "
            "generated PDF reports.\n\n"
            "Club Logo: click 'Browse…' to select a PNG or JPG logo file. "
            "The logo appears in place of the show name text at the top of each PDF page. "
            "Click 'Clear' to remove it."
        )),
    ],
    "Entries": [
        ("Adding Entries", (
            "Navigate to Entries and use the Add Entry form:\n\n"
            "1. Enter the exhibitor number (must exist in the Exhibitors table)\n"
            "2. Enter the class code (must exist in the Class Schedule)\n"
            "3. Click 'Add' — the entry is validated and saved\n\n"
            "Duplicate entries are prevented: if an exhibitor already has an entry "
            "for a class, you will see an error message."
        )),
        ("Calculate (Generate Tickets)", (
            "The 'Calculate' button in the Entries view processes all raw entries "
            "and assigns sequential ticket numbers. This populates the Calculated "
            "Entries table, which is the basis for:\n\n"
            "• Cage tickets (with QR codes)\n"
            "• The Show Catalogue PDF\n"
            "• Results recording\n"
            "• Special winner assignments\n\n"
            "Always run Calculate before printing tickets or recording results."
        )),
        ("Late Entries", (
            "Late entries are managed in the Late Entries view. They follow the "
            "same entry format but are stored separately. Late entries are included "
            "in exhibitor-count reports but are not part of the main calculated sequence."
        )),
        ("Viewing Entries", (
            "The Entries view has two tabs:\n\n"
            "• Raw Entries — the original entries before Calculate\n"
            "• Calculated — entries after Calculate with assigned ticket numbers\n\n"
            "Both tables are paginated (100 rows per page). Use '← Prev' and 'Next →' "
            "to navigate. The row count is shown in the status bar."
        )),
    ],
    "Results & Specials": [
        ("Recording Results", (
            "In the Results view, select a calculated entry from the table, "
            "then enter the result (e.g. 1st, 2nd, 3rd, BOB, CC) and click Save.\n\n"
            "To mark an entry as Not Benched, tick the 'Not Benched' checkbox. "
            "Not-benched entries appear in red on the Results Sheet PDF."
        )),
        ("Special Winners", (
            "In the Special Winners view:\n\n"
            "1. The table shows all special prizes and their current winner (if assigned)\n"
            "2. Click 'Assign' on a row to open the assignment dialog\n"
            "3. Enter the ticket/exhibit number of the winner\n"
            "4. Click Save\n\n"
            "Winners are linked to calculated entries by their auto number (ticket number)."
        )),
        ("Managing Special Prizes", (
            "The Special Prizes view lets you add, edit, and delete the prize list:\n\n"
            "• Click '+ Add' to create a new special prize\n"
            "• Select a row and click 'Edit' to modify it\n"
            "• Select a row and click 'Delete' to remove it (no confirmation — be careful)\n\n"
            "Fields: Special Nr (unique ID), Description, Prize (trophy/medal/etc.), "
            "Cash Amount (leave blank if none)."
        )),
    ],
    "Tickets & Reports": [
        ("Printing Cage Tickets", (
            "After running Calculate in the Entries view:\n\n"
            "1. Go to Tickets\n"
            "2. Click 'Print Tickets' to generate the ticket PDF\n"
            "3. A preview window opens — check the layout\n"
            "4. Click 'Save As…' to save the PDF and open it for printing\n\n"
            "Each ticket shows:\n"
            "• Large ticket number (#001)\n"
            "• Class code\n"
            "• Exhibitor number and name\n"
            "• Show name\n"
            "• QR code (top-right) encoding the exhibitor number and class"
        )),
        ("Generating PDF Reports", (
            "The Reports view offers 7 PDF reports:\n\n"
            "• Entries Received — all calculated entries in ticket order\n"
            "• Show Catalogue — entries grouped by class with class headers\n"
            "• Results Sheet — all results, not-benched shown in red\n"
            "• Special Winners — all special prizes and their winners\n"
            "• Prize Money — cash prizes only with running total\n"
            "• Address Tags — 3-column mailing labels for all exhibitors\n"
            "• Exhibitor List — all exhibitors with entry and late-entry counts\n\n"
            "Click any report button to generate it. A preview window opens so you "
            "can review the output before saving. Click 'Save As…' in the preview "
            "window to save and open the PDF."
        )),
        ("PDF Preview Navigation", (
            "The PDF Preview window shows one page at a time:\n\n"
            "• Use '← Prev' and 'Next →' to move between pages\n"
            "• The page counter shows 'Page N / M'\n"
            "• Click 'Save As…' to choose a location and save the PDF\n"
            "• On Windows, the PDF opens automatically after saving\n"
            "• Click 'Close' to dismiss without saving"
        )),
    ],
    "Data Management": [
        ("Resetting Show Data", (
            "The Reset Data function permanently deletes all show-year data:\n\n"
            "• All show entries and calculated entries\n"
            "• All late entries\n"
            "• All results and not-benched flags\n"
            "• All special winner assignments\n\n"
            "It does NOT delete exhibitors, class definitions, Hall of Fame records, "
            "or brochure notes.\n\n"
            "Use this at the start of a new show season. A confirmation dialog will "
            "appear before any data is deleted."
        )),
        ("Re-importing from MDB", (
            "Go to Import Data in the admin section to re-import data from the "
            "Access MDB file. This will overwrite all currently imported reference data "
            "(exhibitors, classes, Hall of Fame, etc.).\n\n"
            "The import log shows progress for each table. The source MDB path is "
            "set in config.py and cannot be changed from within the app."
        )),
        ("Brochure Notes", (
            "The Notes view lets you edit the brochure text for each bird type:\n\n"
            "1. Click a type abbreviation in the left panel to load its notes\n"
            "2. Edit the text in the right panel\n"
            "3. Click 'Save Notes' to persist the changes\n\n"
            "Notes are imported from the MDB but can be freely edited here."
        )),
        ("Hall of Fame", (
            "The Hall of Fame view displays historical champion records imported "
            "from the Access database. This view is read-only — records cannot be "
            "added or edited from within the app.\n\n"
            "Records are sorted by year (most recent first) then by type abbreviation."
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
        tabs.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

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
                ).grid(row=row_i * 2, column=0, sticky="w", padx=8, pady=(16, 2))

                ctk.CTkLabel(
                    scroll,
                    text=topic_body,
                    font=ctk.CTkFont(size=12),
                    anchor="w",
                    justify="left",
                    wraplength=680,
                ).grid(row=row_i * 2 + 1, column=0, sticky="w", padx=16, pady=(0, 4))
