import threading
from dataclasses import dataclass

import customtkinter as ctk

from models.reference import ShowDetails
from services.show_day_capture_service import (
    get_capture_summary,
    get_category_statuses,
    list_special_assignment_rows,
    validate_capture,
)


PUBLISH_REPORTS = [
    ("Marked Catalogue", "benchabird_marked_catalogue.pdf", "services.reports.marked_catalogue", "generate_marked_catalogue"),
    ("Results Sheet", "benchabird_results_sheet.pdf", "services.reports.results_sheet", "generate_results_sheet"),
    ("Special Winners", "benchabird_special_winners.pdf", "services.reports.special_winners", "generate_special_winners"),
    ("Prize Money", "benchabird_prize_money.pdf", "services.reports.prize_money", "generate_prize_money"),
    ("Results by Exhibitor", "benchabird_results_by_exhibitor.pdf", "services.reports.results_by_exhibitor", "generate_results_by_exhibitor"),
    ("4.4 Marked Catalogue", "benchabird_4_4_marked_catalogue.pdf", "services.reports.marked_catalogue", "generate_marked_catalogue"),
]

EMPTY_JUDGING_STAGE_MESSAGE = "Bench birds in Show Participants before capturing judging sheets."


@dataclass(frozen=True)
class JudgingStageState:
    has_categories: bool
    message: str
    primary_action: str


def judging_stage_empty_state(statuses) -> JudgingStageState:
    if statuses:
        return JudgingStageState(True, "", "Open Judging Capture")
    return JudgingStageState(
        False,
        EMPTY_JUDGING_STAGE_MESSAGE,
        "Go to Show Participants",
    )


class ShowDayCaptureView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._active_stage = "judging"
        self._stage_buttons: dict[str, ctk.CTkButton] = {}
        self._content = None
        self._status = None
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 6))
        ctk.CTkLabel(
            header,
            text="Show Day Capture",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left")
        ctk.CTkButton(
            header,
            text="Refresh",
            width=90,
            fg_color=("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            command=self._refresh,
        ).pack(side="right")

        self._status = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
            anchor="w",
        )
        self._status.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))

        strip = ctk.CTkFrame(self, fg_color="transparent")
        strip.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 8))
        strip.grid_columnconfigure((0, 1, 2, 3), weight=1)
        for col, (key, label) in enumerate([
            ("judging", "Judging Capture"),
            ("specials", "Special Winners"),
            ("validation", "Validation"),
            ("publish", "Publish"),
        ]):
            btn = ctk.CTkButton(
                strip,
                text=label,
                height=34,
                fg_color="transparent",
                text_color=("gray20", "gray80"),
                command=lambda k=key: self._show_stage(k),
            )
            btn.grid(row=0, column=col, sticky="ew", padx=4)
            self._stage_buttons[key] = btn

        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(0, weight=1)

        self._refresh()

    def _refresh(self):
        summary = get_capture_summary()
        self._status.configure(
            text=(
                f"{summary.categories_complete}/{summary.total_categories} categories complete | "
                f"{summary.results_entered} results | {summary.not_benched} NB | "
                f"{summary.specials_assigned} specials | {summary.issue_count} issues | "
                f"{summary.next_action}"
            )
        )
        self._show_stage(self._active_stage)

    def _show_stage(self, key: str):
        self._active_stage = key
        for stage_key, button in self._stage_buttons.items():
            button.configure(
                fg_color=("gray78", "gray28") if stage_key == key else "transparent",
                text_color=("gray5", "white") if stage_key == key else ("gray20", "gray80"),
            )
        for child in self._content.winfo_children():
            child.destroy()
        {
            "judging": self._build_judging_stage,
            "specials": self._build_specials_stage,
            "validation": self._build_validation_stage,
            "publish": self._build_publish_stage,
        }[key]()

    def _build_judging_stage(self):
        frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        statuses = get_category_statuses()
        state = judging_stage_empty_state(statuses)

        top = ctk.CTkFrame(frame, fg_color=("gray88", "gray20"), corner_radius=8)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ctk.CTkLabel(
            top,
            text=state.message or "Capture completed Judges Catalogue sheets by category.",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left", padx=12, pady=10)
        ctk.CTkButton(
            top,
            text=state.primary_action,
            width=160,
            command=self._open_judging_capture if state.has_categories else self._go_to_participants,
        ).pack(side="right", padx=12, pady=8)
        if not state.has_categories:
            ctk.CTkLabel(
                frame,
                text="Judging Capture needs benched birds with exhibit numbers.",
                font=ctk.CTkFont(size=11),
                text_color=("gray45", "gray60"),
            ).grid(row=1, column=0, sticky="w", padx=12, pady=(6, 0))
            return

        for row_i, status in enumerate(statuses, start=1):
            row = ctk.CTkFrame(frame, fg_color=("gray92", "gray17") if row_i % 2 else ("gray88", "gray20"), corner_radius=6)
            row.grid(row=row_i, column=0, sticky="ew", pady=2)
            row.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(row, text=status.category, anchor="w").grid(row=0, column=0, sticky="ew", padx=10, pady=6)
            ctk.CTkLabel(row, text=f"{status.completed_count}/{status.entry_count}", width=80).grid(row=0, column=1, padx=6)
            ctk.CTkLabel(row, text=status.status, width=110).grid(row=0, column=2, padx=10)

    def _open_judging_capture(self):
        from views._judging_capture_dialog import JudgingCaptureDialog

        JudgingCaptureDialog(self, on_saved=self._refresh)

    def _go_to_participants(self):
        self.winfo_toplevel().navigate("participants")

    def _build_specials_stage(self):
        frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        rows = list_special_assignment_rows()
        if not rows:
            ctk.CTkLabel(frame, text="No special prizes found. Add them in Special Prizes.").grid(row=0, column=0, sticky="w", pady=8)
            return

        for row_i, item in enumerate(rows):
            row = ctk.CTkFrame(frame, fg_color=("gray92", "gray17") if row_i % 2 else ("gray88", "gray20"), corner_radius=6)
            row.grid(row=row_i, column=0, sticky="ew", pady=2)
            row.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(row, text=item.special_nr, width=70, anchor="w").grid(row=0, column=0, padx=10, pady=7)
            detail = item.description or item.prize
            winner = f"#{item.exhibit_no} {item.winner_name} {item.result}".strip() if item.exhibit_no else "Missing winner"
            ctk.CTkLabel(row, text=detail, anchor="w").grid(row=0, column=1, sticky="ew", padx=6)
            ctk.CTkLabel(row, text=winner, width=190, anchor="w").grid(row=0, column=2, padx=6)
            ctk.CTkButton(
                row,
                text="Assign",
                width=76,
                height=26,
                command=lambda nr=item.special_nr, desc=item.description, exh=item.exhibit_no: self._open_special_assign(nr, desc, exh),
            ).grid(row=0, column=3, padx=8)

    def _open_special_assign(self, special_nr: str, description: str, current_exhibit_no):
        from views._special_dialog import SpecialAssignDialog

        dialog = SpecialAssignDialog(self, special_nr, description, current_exhibit_no)
        self.wait_window(dialog)
        self._refresh()

    def _build_validation_stage(self):
        frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(1, weight=1)
        issues = validate_capture()
        if not issues:
            ctk.CTkLabel(frame, text="No validation issues found.").grid(row=0, column=0, sticky="w", pady=8)
            return
        for row_i, issue in enumerate(issues):
            row = ctk.CTkFrame(frame, fg_color=("gray92", "gray17") if row_i % 2 else ("gray88", "gray20"), corner_radius=6)
            row.grid(row=row_i, column=0, sticky="ew", pady=2)
            row.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(row, text=issue.severity.upper(), width=70).grid(row=0, column=0, padx=8, pady=7)
            ctk.CTkLabel(row, text=issue.message, anchor="w").grid(row=0, column=1, sticky="ew", padx=6)
            ctk.CTkButton(
                row,
                text=issue.action,
                width=140,
                height=26,
                command=lambda target=issue.action: self._jump_for_issue(target),
            ).grid(row=0, column=2, padx=8)

    def _jump_for_issue(self, action: str):
        if "special" in action.lower():
            self._show_stage("specials")
        else:
            self._show_stage("judging")

    def _build_publish_stage(self):
        frame = ctk.CTkFrame(self._content, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nw")
        for i, (label, default_name, module_name, function_name) in enumerate(PUBLISH_REPORTS):
            row, col = divmod(i, 3)
            ctk.CTkButton(
                frame,
                text=label,
                width=190,
                height=52,
                command=lambda m=module_name, f=function_name, n=default_name: self._generate_report(m, f, n),
            ).grid(row=row, column=col, padx=8, pady=8)

    def _get_sd(self):
        return ShowDetails.select().first()

    def _generate_report(self, module_name: str, function_name: str, default_name: str):
        self._status.configure(text=f"Generating {default_name}...")
        sd = self._get_sd()

        def run():
            try:
                module = __import__(module_name, fromlist=[function_name])
                gen_fn = getattr(module, function_name)
                pdf_bytes = gen_fn(sd=sd)
                self.after(0, lambda: self._show_preview(pdf_bytes, default_name))
            except Exception as exc:
                self.after(0, lambda: self._status.configure(text=f"Error: {str(exc)[:80]}"))

        threading.Thread(target=run, daemon=True).start()

    def _show_preview(self, pdf_bytes: bytes, default_name: str):
        self._refresh()
        from views.pdf_preview_window import PDFPreviewWindow

        title = default_name.replace("benchabird_", "").replace(".pdf", "").replace("_", " ").title()
        PDFPreviewWindow(self, pdf_bytes, title, default_name)
