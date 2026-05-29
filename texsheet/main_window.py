import pandas as pd
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHeaderView,
    QMainWindow,
    QTableWidget,
    QTableWidgetItem,
)

from texsheet.config import load_config, normalize_config, save_config
from texsheet.columns import normalize_columns_metadata
from texsheet import main_window_history
from texsheet import main_window_formula_actions
from texsheet import main_window_io_actions
from texsheet import main_window_table_actions
from texsheet.main_window_ui import setup_main_window_ui
from texsheet.paths import project_path


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TeXSheet")
        self.resize(1100, 650)
        self.undo_stack = []
        self.redo_stack = []
        self.max_undo_stack = 50
        self.is_restoring_snapshot = False
        self.last_snapshot = None
        self.current_table_index = 0

        self.config = normalize_config(load_config())
        save_config(self.config)

        setup_main_window_ui(self)
        self.load_tables()
        self.setup_shortcuts()
        self.last_snapshot = self.create_snapshot()

    @property
    def table(self):
        return self.tab_widget.currentWidget()

    def append_log(self, message):
        self.log_view.appendPlainText(message)

    def setup_shortcuts(self):
        self.shortcuts = [
            QShortcut(QKeySequence("Ctrl+Z"), self),
            QShortcut(QKeySequence("Ctrl+Y"), self),
            QShortcut(QKeySequence("Ctrl+Shift+Z"), self),
        ]
        self.shortcuts[0].activated.connect(self.undo)
        self.shortcuts[1].activated.connect(self.redo)
        self.shortcuts[2].activated.connect(self.redo)

    def current_table_config(self):
        index = self.tab_widget.currentIndex()
        if index < 0:
            return None
        return self.config["tables"][index]

    def load_tables(self, snapshot_tables=None):
        self.is_restoring_snapshot = True
        try:
            self.tab_widget.clear()
            tables = snapshot_tables or [
                {"config": table_config}
                for table_config in self.config["tables"]
            ]
            for entry in tables:
                table_config = entry["config"]
                if "headers" in entry and "rows" in entry:
                    headers = entry["headers"]
                    rows = entry["rows"]
                else:
                    dataframe = pd.read_csv(
                        project_path(table_config["input_csv"]),
                        keep_default_na=False,
                    )
                    headers = [str(column) for column in dataframe.columns]
                    rows = [
                        [str(value) for value in row]
                        for row in dataframe.itertuples(index=False, name=None)
                    ]

                columns_metadata = normalize_columns_metadata(table_config, headers)
                rows = self.trim_trailing_empty_rows(rows)
                rows.append(["" for _ in headers])

                table_widget = QTableWidget()
                horizontal_header = table_widget.horizontalHeader()
                horizontal_header.setSectionResizeMode(QHeaderView.Stretch)
                horizontal_header.setMinimumHeight(44)
                table_widget.setRowCount(len(rows))
                table_widget.setColumnCount(len(headers))
                for column, column_data in enumerate(columns_metadata):
                    main_window_table_actions.set_header_item(
                        table_widget,
                        column,
                        column_data["display_name"],
                        column_data["internal_name"],
                    )
                for row_index, row in enumerate(rows):
                    for column_index, value in enumerate(row):
                        table_widget.setItem(
                            row_index,
                            column_index,
                            QTableWidgetItem(value),
                        )
                self.setup_table_context_menus(table_widget)
                table_widget.itemChanged.connect(self.record_cell_edit)
                self.tab_widget.addTab(table_widget, table_config["name"])
                self.update_formula_cell_styles(table_widget, table_config)
        except Exception as error:
            self.append_log(f"表の読み込みに失敗しました: {error}")
        finally:
            self.is_restoring_snapshot = False

        if self.tab_widget.count() > 0:
            self.tab_widget.setCurrentIndex(min(self.current_table_index, self.tab_widget.count() - 1))
            self.sync_caption_from_current_tab()
        self.append_log("表を読み込みました。")

    def on_tab_changed(self, index):
        if self.is_restoring_snapshot:
            return
        previous_index = self.current_table_index
        if 0 <= previous_index < len(self.config["tables"]):
            self.config["tables"][previous_index]["caption"] = self.caption_edit.text()
        self.current_table_index = index
        self.sync_caption_from_current_tab()
        self.mark_snapshot_current()

    def sync_caption_from_current_tab(self):
        table_config = self.current_table_config()
        self.caption_edit.setText(table_config.get("caption", "") if table_config else "")

    def is_row_empty(self, table_widget, row):
        if table_widget is None or row < 0 or row >= table_widget.rowCount():
            return True
        for column in range(table_widget.columnCount()):
            item = table_widget.item(row, column)
            if item is not None and item.text().strip():
                return False
        return True

    def trim_trailing_empty_rows(self, rows):
        trimmed_rows = list(rows)
        while trimmed_rows:
            if any(str(value).strip() for value in trimmed_rows[-1]):
                break
            trimmed_rows.pop()
        return trimmed_rows

    def ensure_trailing_empty_row(self, table_widget=None):
        table_widget = table_widget or self.table
        if table_widget is None:
            return

        previous_restoring = self.is_restoring_snapshot
        self.is_restoring_snapshot = True
        try:
            while (
                table_widget.rowCount() > 1
                and self.is_row_empty(table_widget, table_widget.rowCount() - 1)
                and self.is_row_empty(table_widget, table_widget.rowCount() - 2)
            ):
                table_widget.removeRow(table_widget.rowCount() - 1)

            if table_widget.rowCount() == 0 or not self.is_row_empty(
                table_widget, table_widget.rowCount() - 1
            ):
                row = table_widget.rowCount()
                table_widget.insertRow(row)
                for column in range(table_widget.columnCount()):
                    table_widget.setItem(row, column, QTableWidgetItem(""))
        finally:
            self.is_restoring_snapshot = previous_restoring

    def dataframe_from_table(self, table_widget=None, trim_trailing_empty=True):
        table_widget = table_widget or self.table
        headers = self.column_headers(table_widget)
        rows = []
        for row in range(table_widget.rowCount()):
            values = []
            for column in range(table_widget.columnCount()):
                item = table_widget.item(row, column)
                values.append(item.text() if item is not None else "")
            rows.append(values)
        if trim_trailing_empty:
            rows = self.trim_trailing_empty_rows(rows)
        return pd.DataFrame(rows, columns=headers)

    def selected_rows(self):
        return main_window_table_actions.selected_rows(self)

    def selected_columns(self):
        return main_window_table_actions.selected_columns(self)

    def get_selected_whole_row(self):
        return main_window_table_actions.get_selected_whole_row(self)

    def get_selected_whole_column(self):
        return main_window_table_actions.get_selected_whole_column(self)

    def column_headers(self, table_widget=None):
        return main_window_table_actions.column_headers(self, table_widget)

    def column_internal_names(self, table_widget=None):
        return main_window_table_actions.column_internal_names(self, table_widget)

    def table_columns_metadata(self, table_widget=None):
        return main_window_table_actions.table_columns_metadata(self, table_widget)

    def setup_table_context_menus(self, table_widget):
        return main_window_table_actions.setup_table_context_menus(self, table_widget)

    def update_formula_cell_styles(self, table_widget=None, table_config=None):
        return main_window_formula_actions.update_formula_cell_styles(
            self,
            table_widget,
            table_config,
        )

    def create_snapshot(self):
        return main_window_history.create_snapshot(self)

    def restore_snapshot(self, snapshot):
        return main_window_history.restore_snapshot(self, snapshot)

    def push_undo_state(self):
        return main_window_history.push_undo_state(self)

    def mark_snapshot_current(self):
        return main_window_history.mark_snapshot_current(self)

    def record_cell_edit(self, *_):
        if self.is_restoring_snapshot:
            return main_window_history.record_cell_edit(self, *_)
        result = main_window_history.record_cell_edit(self, *_)
        self.ensure_trailing_empty_row()
        return result

    def undo(self):
        return main_window_history.undo(self)

    def redo(self):
        return main_window_history.redo(self)

    def update_current_caption_in_config(self):
        index = self.tab_widget.currentIndex()
        if 0 <= index < len(self.config["tables"]):
            self.config["tables"][index]["caption"] = self.caption_edit.text()

    def apply_formulas_to_table_at_index(self, index):
        return main_window_formula_actions.apply_formulas_to_table_at_index(self, index)

    def save_table_at_index(self, index):
        return main_window_io_actions.save_table_at_index(self, index)

    def save_current_table(self):
        return main_window_io_actions.save_current_table(self)

    def save_all_tables(self):
        return main_window_io_actions.save_all_tables(self)

    def add_table(self):
        return main_window_table_actions.add_table(self)

    def delete_current_table(self):
        return main_window_table_actions.delete_current_table(self)

    def rename_current_table(self):
        return main_window_table_actions.rename_current_table(self)

    def swap_rows(self, first_row, second_row):
        return main_window_table_actions.swap_rows(self, first_row, second_row)

    def swap_columns(self, first_column, second_column):
        return main_window_table_actions.swap_columns(self, first_column, second_column)

    def move_selected_row_up(self):
        return main_window_table_actions.move_selected_row_up(self)

    def move_selected_row_down(self):
        return main_window_table_actions.move_selected_row_down(self)

    def move_selected_column_left(self):
        return main_window_table_actions.move_selected_column_left(self)

    def move_selected_column_right(self):
        return main_window_table_actions.move_selected_column_right(self)

    def add_row(self):
        return main_window_table_actions.add_row(self)

    def delete_selected_rows(self):
        return main_window_table_actions.delete_selected_rows(self)

    def add_column(self):
        return main_window_table_actions.add_column(self)

    def delete_selected_columns(self):
        return main_window_table_actions.delete_selected_columns(self)

    def rename_selected_column(self):
        return main_window_table_actions.rename_selected_column(self)

    def rename_selected_column_internal_name(self):
        return main_window_table_actions.rename_selected_column_internal_name(self)

    def rename_alignment_key(self, old_name, new_name):
        return main_window_table_actions.rename_alignment_key(self, old_name, new_name)

    def formula_candidates(self):
        return main_window_formula_actions.formula_candidates(self)

    def selected_formula_column(self):
        return main_window_formula_actions.selected_formula_column(self)

    def set_formula_for_selected_column(self):
        return main_window_formula_actions.set_formula_for_selected_column(self)

    def clear_formula_for_selected_column(self):
        return main_window_formula_actions.clear_formula_for_selected_column(self)

    def open_constants_settings(self):
        return main_window_formula_actions.open_constants_settings(self)

    def open_table_settings(self):
        return main_window_io_actions.open_table_settings(self)

    def open_graph_settings(self):
        return main_window_io_actions.open_graph_settings(self)

    def generate_outputs(self):
        return main_window_io_actions.generate_outputs(self)




