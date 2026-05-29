from copy import deepcopy

from texsheet.config import normalize_config, save_config


def create_snapshot(window):
    window.update_current_caption_in_config()
    tables = []
    for index, table_config in enumerate(window.config["tables"]):
        table_widget = window.tab_widget.widget(index)
        if table_widget is not None:
            table_config["columns"] = window.table_columns_metadata(table_widget)
        tables.append(
            {
                "config": deepcopy(table_config),
                "headers": window.column_headers(table_widget),
                "rows": window.dataframe_from_table(table_widget).values.tolist(),
            }
        )
    return {
        "tables": tables,
        "current_index": window.tab_widget.currentIndex(),
    }


def restore_snapshot(window, snapshot):
    window.is_restoring_snapshot = True
    try:
        window.config["tables"] = [
            deepcopy(entry["config"])
            for entry in snapshot["tables"]
        ]
        save_config(normalize_config(window.config))
        window.current_table_index = max(0, snapshot.get("current_index", 0))
        window.load_tables(snapshot["tables"])
        if window.tab_widget.count() > 0:
            window.tab_widget.setCurrentIndex(
                min(window.current_table_index, window.tab_widget.count() - 1)
            )
            window.sync_caption_from_current_tab()
    finally:
        window.is_restoring_snapshot = False
    window.last_snapshot = create_snapshot(window)


def push_undo_state(window):
    snapshot = create_snapshot(window)
    if window.undo_stack and window.undo_stack[-1] == snapshot:
        return
    window.undo_stack.append(snapshot)
    if len(window.undo_stack) > window.max_undo_stack:
        window.undo_stack.pop(0)
    window.redo_stack.clear()


def mark_snapshot_current(window):
    window.last_snapshot = create_snapshot(window)


def record_cell_edit(window, *_):
    if window.is_restoring_snapshot or window.last_snapshot is None:
        return

    current_snapshot = create_snapshot(window)
    if current_snapshot == window.last_snapshot:
        return

    window.undo_stack.append(window.last_snapshot)
    if len(window.undo_stack) > window.max_undo_stack:
        window.undo_stack.pop(0)
    window.redo_stack.clear()
    window.last_snapshot = current_snapshot


def undo(window):
    if not window.undo_stack:
        window.append_log("Undoできる操作がありません。")
        return

    current_snapshot = create_snapshot(window)
    window.redo_stack.append(current_snapshot)
    snapshot = window.undo_stack.pop()
    restore_snapshot(window, snapshot)
    window.append_log("Undoしました。")


def redo(window):
    if not window.redo_stack:
        window.append_log("Redoできる操作がありません。")
        return

    current_snapshot = create_snapshot(window)
    window.undo_stack.append(current_snapshot)
    if len(window.undo_stack) > window.max_undo_stack:
        window.undo_stack.pop(0)
    snapshot = window.redo_stack.pop()
    restore_snapshot(window, snapshot)
    window.append_log("Redoしました。")
