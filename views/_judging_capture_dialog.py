import customtkinter as ctk
from dataclasses import dataclass

from services.judging_catalogue_service import (
    CLEAR_OPTION,
    JudgingCatalogueError,
    NB_OPTION,
    RESULT_OPTIONS,
    get_judging_entries,
    list_class_options,
    list_judging_categories,
    save_category_results,
)

EMPTY_CATEGORY_LABEL = "No judging categories"
EMPTY_CATEGORY_MESSAGE = "Bench birds in Show Participants before capturing judging sheets."


@dataclass(frozen=True)
class CategoryComboState:
    labels: list[str]
    selected: str
    message: str
    enabled: bool


class JudgingCaptureDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_saved=None):
        super().__init__(parent)
        self._on_saved = on_saved
        self._categories = []
        self._rows = []
        self._vars = {}
        self._initial = {}
        self._class_vars = {}
        self._initial_classes = {}
        self._class_options = []
        self._class_labels_by_code = {}
        self._class_code_by_label = {}
        self._class_categories = {}
        self._active_category = ""
        self.title("Judging Capture")
        self.geometry("980x650")
        self.minsize(820, 500)
        self._build()
        self.after(50, self.lift)

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        ctk.CTkLabel(
            top,
            text="Judging Capture",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left")

        picker = ctk.CTkFrame(self, fg_color=("gray88", "gray20"), corner_radius=8)
        picker.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        ctk.CTkLabel(picker, text="Category").pack(side="left", padx=(12, 4), pady=8)
        self._category_combo = ctk.CTkComboBox(
            picker,
            values=[],
            width=240,
            command=lambda _value: self._load_selected(),
        )
        self._category_combo.pack(side="left", padx=4, pady=8)
        self._status = ctk.CTkLabel(
            picker,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
        )
        self._status.pack(side="left", padx=12)

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 8))

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 16))
        self._save_button = ctk.CTkButton(
            bottom,
            text="Save Category Results",
            command=self._save,
        )
        self._save_button.pack(side="right", padx=4)
        ctk.CTkButton(
            bottom,
            text="Close",
            fg_color=("gray75", "gray35"),
            text_color=("gray10", "gray90"),
            command=self.destroy,
        ).pack(side="right", padx=4)

        self._load_categories()

    @staticmethod
    def category_combo_state(categories):
        labels = [category.label for category in categories]
        if not labels:
            return CategoryComboState(
                labels=[EMPTY_CATEGORY_LABEL],
                selected=EMPTY_CATEGORY_LABEL,
                message=EMPTY_CATEGORY_MESSAGE,
                enabled=False,
            )
        return CategoryComboState(
            labels=labels,
            selected=labels[0],
            message="",
            enabled=True,
        )

    def _load_categories(self):
        self._class_options = list_class_options()
        self._class_labels_by_code = {
            option.class_code: option.label
            for option in self._class_options
        }
        self._class_code_by_label = {
            option.label: option.class_code
            for option in self._class_options
        }
        self._class_categories = {
            option.class_code: option.category
            for option in self._class_options
        }
        self._categories = list_judging_categories()
        state = self.category_combo_state(self._categories)
        widget_state = "normal" if state.enabled else "disabled"
        self._category_combo.configure(values=state.labels, state=widget_state)
        self._category_combo.set(state.selected)
        self._save_button.configure(state=widget_state)
        self._status.configure(text=state.message)
        if not state.enabled:
            self._render_empty_state(state.message)
            return
        self._load_selected()

    def _render_empty_state(self, message: str):
        for child in self._scroll.winfo_children():
            child.destroy()
        self._vars = {}
        self._initial = {}
        self._class_vars = {}
        self._initial_classes = {}
        ctk.CTkLabel(
            self._scroll,
            text=message,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("gray35", "gray70"),
        ).grid(row=0, column=0, padx=20, pady=(28, 6), sticky="w")
        ctk.CTkLabel(
            self._scroll,
            text="The judging sheet is based on benched birds with exhibit numbers.",
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray60"),
        ).grid(row=1, column=0, padx=20, pady=(0, 8), sticky="w")

    def _load_selected(self):
        label = self._category_combo.get()
        category = next(
            (item for item in self._categories if item.label == label),
            None,
        )
        if category is None:
            return
        self._active_category = category.key
        self._rows = get_judging_entries(category.key)
        self._render_rows()

    def _render_rows(self):
        for child in self._scroll.winfo_children():
            child.destroy()
        self._vars = {}
        self._initial = {}
        self._class_vars = {}
        self._initial_classes = {}
        if not self._rows:
            ctk.CTkLabel(self._scroll, text="No entries in this category.").grid(
                row=0,
                column=0,
                pady=20,
            )
            return

        headers = ["Exhibit", "Class", "Description", *RESULT_OPTIONS, NB_OPTION, CLEAR_OPTION]
        for col, header in enumerate(headers):
            ctk.CTkLabel(
                self._scroll,
                text=header,
                font=ctk.CTkFont(size=11, weight="bold"),
            ).grid(row=0, column=col, padx=3, pady=3, sticky="w")

        options = [*RESULT_OPTIONS, NB_OPTION, CLEAR_OPTION]
        for row_i, entry in enumerate(self._rows, start=1):
            ctk.CTkLabel(self._scroll, text=str(entry.auto_num), width=54).grid(
                row=row_i,
                column=0,
                padx=3,
                pady=2,
            )
            class_label = self._class_labels_by_code.get(
                entry.class_code or "",
                entry.class_code or "",
            )
            class_var = ctk.StringVar(value=class_label)
            self._class_vars[entry.auto_num] = class_var
            self._initial_classes[entry.auto_num] = entry.class_code or ""
            ctk.CTkComboBox(
                self._scroll,
                values=list(self._class_code_by_label.keys()),
                variable=class_var,
                width=150,
            ).grid(
                row=row_i,
                column=1,
                padx=3,
                pady=2,
            )
            desc = entry.colour or entry.type_b or ""
            ctk.CTkLabel(
                self._scroll,
                text=desc[:30],
                width=160,
                anchor="w",
            ).grid(row=row_i, column=2, padx=3, pady=2)
            current = NB_OPTION if entry.not_benched else (entry.current_result or "")
            var = ctk.StringVar(value=current)
            self._vars[entry.auto_num] = var
            self._initial[entry.auto_num] = current
            for offset, option in enumerate(options, start=3):
                ctk.CTkRadioButton(
                    self._scroll,
                    text="",
                    value=option,
                    variable=var,
                    width=26,
                ).grid(row=row_i, column=offset, padx=2, pady=2)

    @staticmethod
    def changed_selections(current, initial):
        return {
            auto_num: value
            for auto_num, value in current.items()
            if value and value != initial.get(auto_num, "")
        }

    @staticmethod
    def changed_payload(current_results, initial_results, current_classes, initial_classes):
        payload = {}
        for auto_num, value in current_results.items():
            if value and value != initial_results.get(auto_num, ""):
                payload.setdefault(auto_num, {})["result"] = value
        for auto_num, class_code in current_classes.items():
            if class_code and class_code != initial_classes.get(auto_num, ""):
                payload.setdefault(auto_num, {})["class_code"] = class_code
        return payload

    @staticmethod
    def cross_category_moves(payload, active_category, class_categories):
        moves = []
        for auto_num, values in payload.items():
            class_code = values.get("class_code")
            new_category = class_categories.get(class_code)
            if new_category and new_category != active_category:
                moves.append((auto_num, new_category))
        return moves

    def _save(self):
        current_results = {
            auto_num: var.get()
            for auto_num, var in self._vars.items()
        }
        current_classes = {
            auto_num: self._class_code_by_label.get(var.get(), var.get())
            for auto_num, var in self._class_vars.items()
        }
        payload = self.changed_payload(
            current_results,
            self._initial,
            current_classes,
            self._initial_classes,
        )
        moves = self.cross_category_moves(
            payload,
            self._active_category,
            self._class_categories,
        )
        if moves:
            msg = "\n".join(
                f"Exhibit #{auto_num} will move to {category}."
                for auto_num, category in moves
            )
            from tkinter import messagebox

            ok = messagebox.askyesno(
                "Class moves to another category",
                f"{msg}\n\nThese rows will disappear from this page after saving. Continue?",
                parent=self,
            )
            if not ok:
                return
        try:
            saved = save_category_results(payload)
        except JudgingCatalogueError as exc:
            self._status.configure(text=str(exc))
            return
        self._status.configure(text=f"Saved {saved} updates.")
        self._load_categories()
        if self._on_saved:
            self._on_saved()
