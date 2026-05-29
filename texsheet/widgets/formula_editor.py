from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit, QListWidget, QListWidgetItem

from texsheet.formula_completion import formula_completion_items, token_bounds


class FormulaLineEdit(QLineEdit):
    def __init__(
        self,
        table_config,
        display_names,
        scientific_constants,
        project_constants,
        function_names,
        other_tables=None,
        parent=None,
    ):
        super().__init__(parent)
        self.table_config = table_config
        self.display_names = display_names
        self.scientific_constants = scientific_constants
        self.project_constants = project_constants
        self.function_names = function_names
        self.other_tables = other_tables or []

        self.popup = QListWidget()
        self.popup.setWindowFlags(Qt.Popup)
        self.popup.itemClicked.connect(self.insert_completion)

    def keyPressEvent(self, event):
        key = event.key()
        if self.popup.isVisible():
            if key in {Qt.Key_Return, Qt.Key_Enter, Qt.Key_Tab}:
                self.insert_completion(self.popup.currentItem())
                return
            if key == Qt.Key_Escape:
                self.popup.hide()
                return
            if key == Qt.Key_Down:
                self.move_popup_selection(1)
                return
            if key == Qt.Key_Up:
                self.move_popup_selection(-1)
                return

        if key == Qt.Key_Tab:
            self.complete_at_cursor()
            return

        self.popup.hide()
        super().keyPressEvent(event)

    def move_popup_selection(self, offset):
        count = self.popup.count()
        if count == 0:
            return
        row = self.popup.currentRow()
        self.popup.setCurrentRow((row + offset) % count)

    def complete_at_cursor(self):
        items = formula_completion_items(
            self.text(),
            self.cursorPosition(),
            self.table_config,
            self.display_names,
            self.scientific_constants,
            self.project_constants,
            self.function_names,
            self.other_tables,
        )
        if not items:
            self.popup.hide()
            return
        if len(items) == 1:
            self.apply_completion(items[0].text)
            self.popup.hide()
            return

        self.popup.clear()
        for item in items:
            widget_item = QListWidgetItem(item.label)
            widget_item.setData(Qt.UserRole, item.text)
            self.popup.addItem(widget_item)
        self.popup.setCurrentRow(0)
        self.popup.setMinimumWidth(max(self.width(), 240))
        position = self.mapToGlobal(self.cursorRect().bottomLeft())
        self.popup.move(position)
        self.popup.show()

    def insert_completion(self, item):
        if item is None:
            self.popup.hide()
            return
        self.apply_completion(item.data(Qt.UserRole))
        self.popup.hide()

    def apply_completion(self, completion_text):
        text = self.text()
        cursor_position = self.cursorPosition()
        start, end = token_bounds(text, cursor_position)
        self.setText(text[:start] + completion_text + text[end:])
        self.setCursorPosition(start + len(completion_text))
