import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from texsheet.widgets.formula_editor import FormulaLineEdit


class ColumnNameDialog(QDialog):
    def __init__(self, display_name="", internal_name="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("列追加")

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.display_name_edit = QLineEdit(display_name)
        self.internal_name_edit = QLineEdit(internal_name)
        form_layout.addRow("表示名", self.display_name_edit)
        form_layout.addRow("内部名", self.internal_name_edit)
        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def names(self):
        return (
            self.display_name_edit.text().strip(),
            self.internal_name_edit.text().strip(),
        )


class TableSettingsDialog(QDialog):
    def __init__(self, columns, table_config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("表設定")
        self.alignment_boxes = {}

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.border_style_box = QComboBox()
        self.border_style_box.addItems(["booktabs", "full", "vertical", "none"])
        border_style = table_config.get("border_style", "booktabs")
        if border_style not in {"booktabs", "full", "vertical", "none"}:
            border_style = "booktabs"
        self.border_style_box.setCurrentText(border_style)
        form_layout.addRow("罫線スタイル", self.border_style_box)
        layout.addLayout(form_layout)

        grid_layout = QGridLayout()
        grid_layout.addWidget(QLabel("列名"), 0, 0)
        grid_layout.addWidget(QLabel("配置"), 0, 1)

        column_alignments = table_config.get("column_alignments", {})
        for row, column in enumerate(columns, start=1):
            alignment_box = QComboBox()
            alignment_box.addItems(["l", "c", "r"])
            alignment_box.setCurrentText(column_alignments.get(column, "l"))
            self.alignment_boxes[column] = alignment_box
            grid_layout.addWidget(QLabel(column), row, 0)
            grid_layout.addWidget(alignment_box, row, 1)

        layout.addLayout(grid_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def table_settings(self):
        return {
            "border_style": self.border_style_box.currentText(),
            "column_alignments": {
                column: box.currentText()
                for column, box in self.alignment_boxes.items()
            },
        }


class FormulaDialog(QDialog):
    def __init__(self, column_name, current_formula, completion_context, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数式列設定")

        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"{column_name}列の数式"))

        self.formula_edit = FormulaLineEdit(
            completion_context["table_config"],
            completion_context["display_names"],
            completion_context["scientific_constants"],
            completion_context["project_constants"],
            completion_context["function_names"],
            completion_context.get("other_tables", []),
            self,
        )
        self.formula_edit.setText(current_formula)
        layout.addWidget(self.formula_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def formula(self):
        return self.formula_edit.text().strip()


class ConstantsDialog(QDialog):
    def __init__(self, constants, parent=None):
        super().__init__(parent)
        self.setWindowTitle("定数設定")

        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["定数名", "値"])
        self.table.setRowCount(len(constants))
        for row, (name, value) in enumerate(constants.items()):
            self.table.setItem(row, 0, QTableWidgetItem(str(name)))
            self.table.setItem(row, 1, QTableWidgetItem(str(value)))
        layout.addWidget(self.table)

        edit_layout = QHBoxLayout()
        self.add_button = QPushButton("追加")
        self.delete_button = QPushButton("削除")
        self.add_button.clicked.connect(self.add_row)
        self.delete_button.clicked.connect(self.delete_selected_rows)
        edit_layout.addWidget(self.add_button)
        edit_layout.addWidget(self.delete_button)
        edit_layout.addStretch()
        layout.addLayout(edit_layout)

        self.error_label = QLabel("")
        layout.addWidget(self.error_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.try_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(""))
        self.table.setItem(row, 1, QTableWidgetItem(""))

    def delete_selected_rows(self):
        rows = sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.table.removeRow(row)

    def constants(self):
        constants = {}
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            value_item = self.table.item(row, 1)
            name = name_item.text().strip() if name_item else ""
            value_text = value_item.text().strip() if value_item else ""
            if not name and not value_text:
                continue
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                raise ValueError(f"定数名が不正です: {name}")
            if name in constants:
                raise ValueError(f"定数名が重複しています: {name}")
            try:
                constants[name] = float(value_text)
            except ValueError as error:
                raise ValueError(f"値がfloatに変換できません: {name}") from error
        return constants

    def try_accept(self):
        try:
            self.constants()
        except ValueError as error:
            self.error_label.setText(str(error))
            return
        self.accept()


def _load_graph_settings_dialog():
    import importlib.util
    import sys
    from pathlib import Path

    module_name = "texsheet.dialogs.graph_dialog"
    module_path = Path(__file__).with_name("dialogs") / "graph_dialog.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module.GraphSettingsDialog


GraphSettingsDialog = _load_graph_settings_dialog()
