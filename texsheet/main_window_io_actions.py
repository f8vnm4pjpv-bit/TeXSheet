from PySide6.QtWidgets import QDialog

from texsheet.config import normalize_config, save_config
from texsheet.dialogs import GraphSettingsDialog, TableSettingsDialog
from texsheet.formula import apply_formulas_to_dataframe
from texsheet.graph import graph_config_from_dict, save_graph
from texsheet.generation import run_generation
from texsheet.paths import project_path


def save_table_at_index(window, index):
    if not (0 <= index < len(window.config["tables"])):
        return False
    if index == window.tab_widget.currentIndex():
        window.update_current_caption_in_config()
    window.apply_formulas_to_table_at_index(index)

    table_config = window.config["tables"][index]
    table_config["columns"] = window.table_columns_metadata(window.tab_widget.widget(index))
    dataframe = window.dataframe_from_table(window.tab_widget.widget(index))
    csv_path = project_path(table_config["input_csv"])
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(csv_path, index=False)
    save_config(normalize_config(window.config))
    return True


def save_current_table(window):
    index = window.tab_widget.currentIndex()
    if window.save_table_at_index(index):
        window.append_log(f"表を保存しました: {window.config['tables'][index]['name']}")
        window.mark_snapshot_current()
        return True
    window.append_log("保存する表がありません。")
    return False


def save_all_tables(window):
    window.update_current_caption_in_config()
    for index in range(window.tab_widget.count()):
        window.save_table_at_index(index)
    save_config(normalize_config(window.config))
    window.append_log("すべての表を保存しました。")
    window.mark_snapshot_current()
    return True


def open_table_settings(window):
    table_config = window.current_table_config()
    dialog = TableSettingsDialog(window.column_headers(), table_config, window)
    if dialog.exec() != QDialog.Accepted:
        window.append_log("表設定をキャンセルしました。")
        return

    window.push_undo_state()
    settings = dialog.table_settings()
    table_config["border_style"] = settings["border_style"]
    table_config["column_alignments"] = settings["column_alignments"]
    save_config(normalize_config(window.config))
    window.mark_snapshot_current()
    window.append_log("表設定を保存しました。")


def open_graph_settings(window):
    table_config = window.current_table_config()
    if table_config is None:
        window.append_log("グラフを作成する表がありません。")
        return

    dataframe = window.dataframe_from_table()
    dataframe, messages = apply_formulas_to_dataframe(
        dataframe,
        table_config,
        window.config.get("constants", {}),
        external_tables_for_index(window, window.tab_widget.currentIndex()),
    )
    for message in messages:
        window.append_log(message)

    graph_config = graph_config_from_dict(
        table_config.get("graph_configs", [{}])[0] if table_config.get("graph_configs") else {},
        columns=dataframe.columns,
        table_id=table_config["id"],
    )
    dialog = GraphSettingsDialog(dataframe, graph_config, table_config["id"], window)
    if dialog.exec() != QDialog.Accepted:
        window.append_log("グラフ作成をキャンセルしました。")
        return

    accepted_config = dialog.accepted_config or dialog.graph_config()
    table_config["graph_configs"] = [accepted_config.to_dict()]
    window.config = normalize_config(window.config)
    save_config(window.config)
    output_path = save_graph(dataframe, accepted_config)
    window.append_log(f"グラフを生成しました: {output_path}")


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


def generate_outputs(window):
    try:
        if not window.save_all_tables():
            return
        run_generation(window.append_log)
    except Exception as error:
        window.append_log(f"生成に失敗しました: {error}")
        return

    window.append_log("生成が完了しました。")
