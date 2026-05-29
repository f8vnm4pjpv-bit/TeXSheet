from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QTableWidgetItem

from texsheet.config import normalize_config, save_config
from texsheet.dialogs import ConstantsDialog, FormulaDialog
from texsheet.formula_completion import column_completion_items
from texsheet.formula import ALLOWED_FUNCTIONS, SCIENTIFIC_CONSTANTS
from texsheet.formula import apply_formulas_to_dataframe


def update_formula_cell_styles(window, table_widget=None, table_config=None):
    table_widget = table_widget or window.table
    table_config = table_config or window.current_table_config()
    if table_widget is None or table_config is None:
        return

    formula_columns = set(table_config.get("formulas", {}))
    headers = window.column_headers(table_widget)
    formula_color = QColor(245, 248, 255)
    normal_color = QColor(255, 255, 255)
    for column, column_name in enumerate(headers):
        is_formula_column = column_name in formula_columns
        for row in range(table_widget.rowCount()):
            item = table_widget.item(row, column)
            if item is None:
                item = QTableWidgetItem("")
                table_widget.setItem(row, column, item)
            flags = item.flags()
            if is_formula_column:
                item.setFlags(flags & ~Qt.ItemIsEditable)
                item.setBackground(formula_color)
            else:
                item.setFlags(flags | Qt.ItemIsEditable)
                item.setBackground(normal_color)


def apply_formulas_to_table_at_index(window, index):
    if not (0 <= index < len(window.config["tables"])):
        return False

    table_config = window.config["tables"][index]
    table_widget = window.tab_widget.widget(index)
    dataframe = window.dataframe_from_table(table_widget)
    calculated, messages = apply_formulas_to_dataframe(
        dataframe,
        table_config,
        window.config.get("constants", {}),
        external_tables_for_index(window, index),
    )
    for message in messages:
        window.append_log(message)
    if not table_config.get("formulas"):
        return True

    window.is_restoring_snapshot = True
    try:
        for row in range(len(calculated)):
            for column, column_name in enumerate(calculated.columns):
                item = table_widget.item(row, column)
                value = str(calculated.iloc[row, column])
                if item is None:
                    table_widget.setItem(row, column, QTableWidgetItem(value))
                else:
                    item.setText(value)
    finally:
        window.is_restoring_snapshot = False
    window.update_formula_cell_styles(table_widget, table_config)
    window.mark_snapshot_current()
    return True


def formula_completion_context(window):
    constants = window.config.get("constants", {})
    current_index = window.tab_widget.currentIndex()
    return {
        "table_config": window.current_table_config(),
        "display_names": window.column_headers(),
        "scientific_constants": SCIENTIFIC_CONSTANTS,
        "project_constants": constants,
        "function_names": ALLOWED_FUNCTIONS,
        "other_tables": completion_tables_for_index(window, current_index),
    }


def external_tables_for_index(window, current_index):
    tables = []
    for index, table_config in enumerate(window.config["tables"]):
        if index == current_index:
            continue
        table_widget = window.tab_widget.widget(index)
        if table_widget is None:
            continue
        tables.append(
            {
                "config": table_config,
                "dataframe": window.dataframe_from_table(table_widget),
            }
        )
    return tables


def completion_tables_for_index(window, current_index):
    tables = []
    for index, table_config in enumerate(window.config["tables"]):
        if index == current_index:
            continue
        table_widget = window.tab_widget.widget(index)
        if table_widget is None:
            continue
        tables.append(
            {
                "name": table_config.get("name", ""),
                "columns": table_config.get("columns", []),
                "display_names": window.column_headers(table_widget),
            }
        )
    return tables


def formula_candidates(window):
    context = formula_completion_context(window)
    candidates = []
    candidates.extend(
        item.text
        for item in column_completion_items(
            context["table_config"],
            context["display_names"],
        )
    )
    candidates.extend(f"cons.{name}" for name in SCIENTIFIC_CONSTANTS)
    candidates.extend(f"const.{name}" for name in SCIENTIFIC_CONSTANTS)
    candidates.extend(f"proj.{name}" for name in context["project_constants"])
    candidates.extend(sorted(ALLOWED_FUNCTIONS))
    return candidates


def selected_formula_column(window):
    columns = window.selected_columns()
    if not columns:
        window.append_log("警告: 数式列にする列が選択されていません。")
        return None
    return min(columns)


def set_formula_for_selected_column(window):
    column = window.selected_formula_column()
    if column is None:
        return

    column_name = window.column_headers()[column]
    table_config = window.current_table_config()
    formulas = table_config.setdefault("formulas", {})
    current_formula = formulas.get(column_name, "")
    dialog = FormulaDialog(
        column_name,
        current_formula,
        formula_completion_context(window),
        window,
    )
    if dialog.exec() != FormulaDialog.Accepted:
        window.append_log("数式列設定をキャンセルしました。")
        return
    formula = dialog.formula()
    if not formula:
        window.append_log("警告: 数式が空です。")
        return

    window.push_undo_state()
    formulas[column_name] = formula
    save_config(normalize_config(window.config))
    window.apply_formulas_to_table_at_index(window.tab_widget.currentIndex())
    window.update_formula_cell_styles()
    window.mark_snapshot_current()
    window.append_log(f"数式列を設定しました: {column_name} = {formula}")


def clear_formula_for_selected_column(window):
    column = window.selected_formula_column()
    if column is None:
        return

    column_name = window.column_headers()[column]
    table_config = window.current_table_config()
    formulas = table_config.setdefault("formulas", {})
    if column_name not in formulas:
        window.append_log(f"数式列ではありません: {column_name}")
        return

    window.push_undo_state()
    formulas.pop(column_name)
    save_config(normalize_config(window.config))
    window.update_formula_cell_styles()
    window.mark_snapshot_current()
    window.append_log(f"数式列を解除しました: {column_name}")


def open_constants_settings(window):
    dialog = ConstantsDialog(window.config.get("constants", {}), window)
    if dialog.exec() != ConstantsDialog.Accepted:
        window.append_log("定数設定をキャンセルしました。")
        return

    window.push_undo_state()
    window.config["constants"] = dialog.constants()
    save_config(normalize_config(window.config))
    for index in range(window.tab_widget.count()):
        window.apply_formulas_to_table_at_index(index)
    window.mark_snapshot_current()
    window.append_log("定数設定を保存しました。")
