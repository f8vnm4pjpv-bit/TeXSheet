import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QInputDialog, QMenu, QTableWidgetItem

from texsheet.columns import (
    DISPLAY_ROLE,
    INTERNAL_ROLE,
    header_label,
    normalize_internal_name,
    validate_column_names,
)
from texsheet.config import make_table_id, normalize_config, save_config
from texsheet.dialogs import ColumnNameDialog
from texsheet.paths import TABLES_DATA_DIR, project_path


def selected_rows(window):
    return sorted({index.row() for index in window.table.selectedIndexes()}, reverse=True)


def selected_columns(window):
    return sorted(
        {index.column() for index in window.table.selectedIndexes()},
        reverse=True,
    )


def get_selected_whole_row(window):
    ranges = window.table.selectedRanges()
    if len(ranges) != 1:
        return None

    selected_range = ranges[0]
    is_single_row = selected_range.rowCount() == 1
    is_whole_row = (
        selected_range.leftColumn() == 0
        and selected_range.rightColumn() == window.table.columnCount() - 1
    )
    if is_single_row and is_whole_row:
        return selected_range.topRow()
    return None


def get_selected_whole_column(window):
    ranges = window.table.selectedRanges()
    if len(ranges) != 1:
        return None

    selected_range = ranges[0]
    is_single_column = selected_range.columnCount() == 1
    is_whole_column = (
        selected_range.topRow() == 0
        and selected_range.bottomRow() == window.table.rowCount() - 1
    )
    if is_single_column and is_whole_column:
        return selected_range.leftColumn()
    return None


def column_headers(window, table_widget=None):
    table_widget = table_widget or window.table
    headers = []
    for column in range(table_widget.columnCount()):
        item = table_widget.horizontalHeaderItem(column)
        if item is None:
            headers.append("")
            continue
        display_name = item.data(DISPLAY_ROLE)
        headers.append(str(display_name) if display_name is not None else item.text())
    return headers


def column_internal_names(window, table_widget=None):
    table_widget = table_widget or window.table
    names = []
    for column in range(table_widget.columnCount()):
        item = table_widget.horizontalHeaderItem(column)
        if item is None:
            names.append("")
            continue
        display_name = item.data(DISPLAY_ROLE)
        display_name = str(display_name) if display_name is not None else item.text()
        names.append(normalize_internal_name(display_name, item.data(INTERNAL_ROLE)))
    return names


def make_header_item(display_name, internal_name=None):
    internal_name = normalize_internal_name(display_name, internal_name)
    item = QTableWidgetItem(header_label(display_name, internal_name))
    item.setData(DISPLAY_ROLE, display_name)
    item.setData(INTERNAL_ROLE, internal_name)
    return item


def set_header_item(table_widget, column, display_name, internal_name=None):
    table_widget.setHorizontalHeaderItem(
        column,
        make_header_item(display_name, internal_name),
    )


def table_columns_metadata(window, table_widget=None):
    return [
        {"display_name": display_name, "internal_name": internal_name}
        for display_name, internal_name in zip(
            column_headers(window, table_widget),
            column_internal_names(window, table_widget),
        )
    ]


def validate_new_column_names(window, display_name, internal_name=None, replace_index=None):
    columns = table_columns_metadata(window)
    candidate = {
        "display_name": display_name,
        "internal_name": normalize_internal_name(display_name, internal_name),
    }
    if replace_index is None:
        columns.append(candidate)
    else:
        columns[replace_index] = candidate
    return validate_column_names(columns)


def setup_table_context_menus(window, table_widget):
    horizontal_header = table_widget.horizontalHeader()
    horizontal_header.setContextMenuPolicy(Qt.CustomContextMenu)
    horizontal_header.customContextMenuRequested.connect(
        lambda position, table_widget=table_widget: show_column_header_menu(
            window,
            table_widget,
            position,
        )
    )

    vertical_header = table_widget.verticalHeader()
    vertical_header.setContextMenuPolicy(Qt.CustomContextMenu)
    vertical_header.customContextMenuRequested.connect(
        lambda position, table_widget=table_widget: show_row_header_menu(
            window,
            table_widget,
            position,
        )
    )


def select_column_for_context_menu(table_widget, column):
    if column < 0:
        return False
    selected_columns = {index.column() for index in table_widget.selectedIndexes()}
    if column not in selected_columns:
        table_widget.clearSelection()
        table_widget.selectColumn(column)
    return True


def select_row_for_context_menu(table_widget, row):
    if row < 0:
        return False
    selected_rows = {index.row() for index in table_widget.selectedIndexes()}
    if row not in selected_rows:
        table_widget.clearSelection()
        table_widget.selectRow(row)
    return True


def show_column_header_menu(window, table_widget, position):
    column = table_widget.horizontalHeader().logicalIndexAt(position)
    if not select_column_for_context_menu(table_widget, column):
        return

    menu = QMenu(window)
    add_column_action = menu.addAction("列追加")
    delete_column_action = menu.addAction("列削除")
    rename_column_action = menu.addAction("列名変更")
    rename_internal_action = menu.addAction("内部名変更")
    menu.addSeparator()
    set_formula_action = menu.addAction("数式列設定")
    clear_formula_action = menu.addAction("数式列解除")

    move_left_action = menu.addAction("列を左へ移動")
    move_right_action = menu.addAction("列を右へ移動")

    add_column_action.triggered.connect(window.add_column)
    delete_column_action.triggered.connect(window.delete_selected_columns)
    rename_column_action.triggered.connect(window.rename_selected_column)
    rename_internal_action.triggered.connect(window.rename_selected_column_internal_name)
    move_left_action.triggered.connect(window.move_selected_column_left)
    move_right_action.triggered.connect(window.move_selected_column_right)
    set_formula_action.triggered.connect(window.set_formula_for_selected_column)
    clear_formula_action.triggered.connect(window.clear_formula_for_selected_column)
    menu.exec(table_widget.horizontalHeader().mapToGlobal(position))


def show_row_header_menu(window, table_widget, position):
    row = table_widget.verticalHeader().logicalIndexAt(position)
    if not select_row_for_context_menu(table_widget, row):
        return

    menu = QMenu(window)
    add_row_action = menu.addAction("行追加")
    delete_row_action = menu.addAction("行削除")
    menu.addSeparator()
    move_up_action = menu.addAction("上へ移動")
    move_down_action = menu.addAction("下へ移動")

    add_row_action.triggered.connect(window.add_row)
    delete_row_action.triggered.connect(window.delete_selected_rows)
    move_up_action.triggered.connect(window.move_selected_row_up)
    move_down_action.triggered.connect(window.move_selected_row_down)
    menu.exec(table_widget.verticalHeader().mapToGlobal(position))


def add_table(window):
    name, accepted = QInputDialog.getText(window, "表追加", "表名:")
    name = name.strip()
    if not accepted:
        window.append_log("表追加をキャンセルしました。")
        return
    if not name:
        window.append_log("警告: 表名が空です。")
        return
    if name in [table_config["name"] for table_config in window.config["tables"]]:
        window.append_log(f"警告: 同じ表名が既に存在します: {name}")
        return
    if "_" in name:
        window.append_log("警告: 別表参照では表名に _ を含めないことを推奨する。")

    window.push_undo_state()
    TABLES_DATA_DIR.mkdir(parents=True, exist_ok=True)
    table_id = make_table_id(name, {table_config["id"] for table_config in window.config["tables"]})
    table_config = {
        "id": table_id,
        "name": name,
        "input_csv": f"tables_data/{table_id}.csv",
        "output_tex": f"tables/{table_id}.tex",
        "caption": name,
        "label": f"tab:{table_id}",
        "column_alignments": {"column1": "l"},
        "columns": [
            {"display_name": "column1", "internal_name": "column1"},
        ],
        "border_style": "booktabs",
        "formulas": {},
    }
    pd.DataFrame([[""]], columns=["column1"]).to_csv(
        project_path(table_config["input_csv"]),
        index=False,
    )
    window.config["tables"].append(table_config)
    save_config(normalize_config(window.config))

    window.current_table_index = len(window.config["tables"]) - 1
    window.load_tables()
    window.tab_widget.setCurrentIndex(window.current_table_index)
    window.mark_snapshot_current()
    window.append_log(f"表を追加しました: {name}")


def delete_current_table(window):
    index = window.tab_widget.currentIndex()
    if index < 0:
        window.append_log("削除する表がありません。")
        return
    if len(window.config["tables"]) <= 1:
        window.append_log("警告: 最後の表は削除できません。")
        return

    table_name = window.config["tables"][index]["name"]
    window.push_undo_state()
    window.config["tables"].pop(index)
    save_config(normalize_config(window.config))
    window.current_table_index = max(0, index - 1)
    window.load_tables()
    window.mark_snapshot_current()
    window.append_log(f"表を削除しました: {table_name}")


def rename_current_table(window):
    table_config = window.current_table_config()
    if table_config is None:
        window.append_log("名前を変更する表がありません。")
        return

    old_name = table_config["name"]
    new_name, accepted = QInputDialog.getText(
        window,
        "表名変更",
        "新しい表名:",
        text=old_name,
    )
    new_name = new_name.strip()
    if not accepted:
        window.append_log("表名変更をキャンセルしました。")
        return
    if not new_name:
        window.append_log("警告: 表名が空です。")
        return
    if new_name != old_name and new_name in [
        table["name"] for table in window.config["tables"]
    ]:
        window.append_log(f"警告: 同じ表名が既に存在します: {new_name}")
        return
    if "_" in new_name:
        window.append_log("警告: 別表参照では表名に _ を含めないことを推奨する。")

    window.push_undo_state()
    table_config["name"] = new_name
    table_config["caption"] = new_name
    window.caption_edit.setText(new_name)
    window.tab_widget.setTabText(window.tab_widget.currentIndex(), new_name)
    save_config(normalize_config(window.config))
    window.mark_snapshot_current()
    window.append_log(f"表名を変更しました: {old_name} -> {new_name}")


def swap_rows(window, first_row, second_row):
    for column in range(window.table.columnCount()):
        first_item = window.table.takeItem(first_row, column)
        second_item = window.table.takeItem(second_row, column)
        window.table.setItem(first_row, column, second_item or QTableWidgetItem(""))
        window.table.setItem(second_row, column, first_item or QTableWidgetItem(""))


def swap_columns(window, first_column, second_column):
    first_header = window.table.takeHorizontalHeaderItem(first_column)
    second_header = window.table.takeHorizontalHeaderItem(second_column)

    for row in range(window.table.rowCount()):
        first_item = window.table.takeItem(row, first_column)
        second_item = window.table.takeItem(row, second_column)
        window.table.setItem(row, first_column, second_item or QTableWidgetItem(""))
        window.table.setItem(row, second_column, first_item or QTableWidgetItem(""))

    window.table.setHorizontalHeaderItem(first_column, second_header or QTableWidgetItem(""))
    window.table.setHorizontalHeaderItem(second_column, first_header or QTableWidgetItem(""))


def move_selected_row_up(window):
    row = window.get_selected_whole_row()
    if row is None:
        window.append_log("行を選択してください。")
        return
    if row == 0:
        window.append_log("一番上の行は上に移動できません。")
        return

    window.push_undo_state()
    window.is_restoring_snapshot = True
    try:
        window.swap_rows(row, row - 1)
        window.table.selectRow(row - 1)
    finally:
        window.is_restoring_snapshot = False
    window.ensure_trailing_empty_row()
    window.mark_snapshot_current()
    window.append_log("行を上に移動しました。")


def move_selected_row_down(window):
    row = window.get_selected_whole_row()
    if row is None:
        window.append_log("行を選択してください。")
        return
    if row >= window.table.rowCount() - 1:
        window.append_log("一番下の行は下に移動できません。")
        return

    window.push_undo_state()
    window.is_restoring_snapshot = True
    try:
        window.swap_rows(row, row + 1)
        window.table.selectRow(row + 1)
    finally:
        window.is_restoring_snapshot = False
    window.ensure_trailing_empty_row()
    window.mark_snapshot_current()
    window.append_log("行を下に移動しました。")


def move_selected_column_left(window):
    column = window.get_selected_whole_column()
    if column is None:
        window.append_log("列を選択してください。")
        return
    if column == 0:
        window.append_log("一番左の列は左に移動できません。")
        return

    window.push_undo_state()
    window.is_restoring_snapshot = True
    try:
        window.swap_columns(column, column - 1)
        window.table.selectColumn(column - 1)
    finally:
        window.is_restoring_snapshot = False
    table_config = window.current_table_config()
    table_config["columns"] = table_columns_metadata(window)
    save_config(normalize_config(window.config))
    window.mark_snapshot_current()
    window.append_log("列を左に移動しました。")


def move_selected_column_right(window):
    column = window.get_selected_whole_column()
    if column is None:
        window.append_log("列を選択してください。")
        return
    if column >= window.table.columnCount() - 1:
        window.append_log("一番右の列は右に移動できません。")
        return

    window.push_undo_state()
    window.is_restoring_snapshot = True
    try:
        window.swap_columns(column, column + 1)
        window.table.selectColumn(column + 1)
    finally:
        window.is_restoring_snapshot = False
    table_config = window.current_table_config()
    table_config["columns"] = table_columns_metadata(window)
    save_config(normalize_config(window.config))
    window.mark_snapshot_current()
    window.append_log("列を右に移動しました。")


def add_row(window):
    window.push_undo_state()
    row = window.table.rowCount()
    window.is_restoring_snapshot = True
    try:
        window.table.insertRow(row)
        for column in range(window.table.columnCount()):
            window.table.setItem(row, column, QTableWidgetItem(""))
    finally:
        window.is_restoring_snapshot = False
    window.mark_snapshot_current()
    window.append_log("末尾に行を追加しました。")
    window.apply_formulas_to_table_at_index(window.tab_widget.currentIndex())


def delete_selected_rows(window):
    rows = window.selected_rows()
    if not rows:
        window.append_log("警告: 削除する行が選択されていません。")
        return

    window.push_undo_state()
    window.is_restoring_snapshot = True
    try:
        for row in rows:
            window.table.removeRow(row)
    finally:
        window.is_restoring_snapshot = False
    window.ensure_trailing_empty_row()
    window.mark_snapshot_current()
    window.append_log(f"{len(rows)}行を削除しました。")


def add_column(window):
    dialog = ColumnNameDialog(parent=window)
    if dialog.exec() != ColumnNameDialog.Accepted:
        window.append_log("列追加をキャンセルしました。")
        return
    column_name, internal_name = dialog.names()
    if not column_name:
        window.append_log("警告: 列名が空です。")
        return
    validation_error = validate_new_column_names(window, column_name, internal_name)
    if validation_error:
        window.append_log(f"警告: {validation_error}")
        return
    if "_" in internal_name:
        window.append_log("警告: 別表参照では内部名に _ を含めないことを推奨する。")

    window.push_undo_state()
    column = window.table.columnCount()
    window.is_restoring_snapshot = True
    try:
        window.table.insertColumn(column)
        set_header_item(window.table, column, column_name, internal_name)
        for row in range(window.table.rowCount()):
            window.table.setItem(row, column, QTableWidgetItem(""))
    finally:
        window.is_restoring_snapshot = False
    table_config = window.current_table_config()
    table_config["columns"] = table_columns_metadata(window)
    save_config(normalize_config(window.config))
    window.update_formula_cell_styles()
    window.mark_snapshot_current()
    window.append_log(f"列を追加しました: {column_name}")


def delete_selected_columns(window):
    columns = window.selected_columns()
    if not columns:
        window.append_log("警告: 削除する列が選択されていません。")
        return

    window.push_undo_state()
    deleted_column_names = [window.column_headers()[column] for column in columns]
    window.is_restoring_snapshot = True
    try:
        for column in columns:
            window.table.removeColumn(column)
    finally:
        window.is_restoring_snapshot = False
    table_config = window.current_table_config()
    for column_name in deleted_column_names:
        table_config.setdefault("column_alignments", {}).pop(column_name, None)
        table_config.setdefault("formulas", {}).pop(column_name, None)
    table_config["columns"] = table_columns_metadata(window)
    save_config(normalize_config(window.config))
    window.mark_snapshot_current()
    window.append_log(f"{len(columns)}列を削除しました。")


def rename_selected_column(window):
    columns = window.selected_columns()
    if not columns:
        window.append_log("警告: 名前を変更する列が選択されていません。")
        return

    column = min(columns)
    old_name = window.column_headers()[column]
    old_internal_name = column_internal_names(window)[column]
    new_name, accepted = QInputDialog.getText(
        window,
        "列名変更",
        "新しい列名:",
        text=old_name,
    )
    new_name = new_name.strip()
    if not accepted:
        window.append_log("列名変更をキャンセルしました。")
        return
    if not new_name:
        window.append_log("警告: 列名が空です。")
        return

    new_internal_name = old_internal_name if old_internal_name != old_name else new_name
    validation_error = validate_new_column_names(
        window,
        new_name,
        new_internal_name,
        replace_index=column,
    )
    if validation_error:
        window.append_log(f"警告: {validation_error}")
        return
    if "_" in new_internal_name:
        window.append_log("警告: 別表参照では内部名に _ を含めないことを推奨する。")

    window.push_undo_state()
    set_header_item(window.table, column, new_name, new_internal_name)
    window.rename_alignment_key(old_name, new_name)
    table_config = window.current_table_config()
    table_config["columns"] = table_columns_metadata(window)
    save_config(normalize_config(window.config))
    window.mark_snapshot_current()
    window.append_log(f"列名を変更しました: {old_name} -> {new_name}")


def rename_selected_column_internal_name(window):
    columns = window.selected_columns()
    if not columns:
        window.append_log("警告: 内部名を変更する列が選択されていません。")
        return

    column = min(columns)
    display_name = window.column_headers()[column]
    old_internal_name = column_internal_names(window)[column]
    new_internal_name, accepted = QInputDialog.getText(
        window,
        "内部名変更",
        "新しい内部名:",
        text=old_internal_name,
    )
    if not accepted:
        window.append_log("内部名変更をキャンセルしました。")
        return
    new_internal_name = normalize_internal_name(display_name, new_internal_name)
    validation_error = validate_new_column_names(
        window,
        display_name,
        new_internal_name,
        replace_index=column,
    )
    if validation_error:
        window.append_log(f"警告: {validation_error}")
        return

    if "_" in new_internal_name:
        window.append_log("警告: 別表参照では内部名に _ を含めないことを推奨する。")

    window.push_undo_state()
    set_header_item(window.table, column, display_name, new_internal_name)
    table_config = window.current_table_config()
    table_config["columns"] = table_columns_metadata(window)
    save_config(normalize_config(window.config))
    window.mark_snapshot_current()
    window.append_log(
        f"内部名を変更しました: {display_name} [{old_internal_name}] -> [{new_internal_name}]"
    )


def rename_alignment_key(window, old_name, new_name):
    table_config = window.current_table_config()
    column_alignments = table_config.setdefault("column_alignments", {})
    if old_name in column_alignments and new_name not in column_alignments:
        column_alignments[new_name] = column_alignments.pop(old_name)
        save_config(normalize_config(window.config))
        window.append_log("列配置設定の列名を更新しました。")
    formulas = table_config.setdefault("formulas", {})
    if old_name in formulas and new_name not in formulas:
        formulas[new_name] = formulas.pop(old_name)
        save_config(normalize_config(window.config))
        window.append_log("数式列設定の列名を更新しました。")
