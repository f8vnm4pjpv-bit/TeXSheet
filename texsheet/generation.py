import pandas as pd

from texsheet.config import load_config, normalize_config, save_config
from texsheet.formula import apply_formulas_to_dataframe
from texsheet.graph import graph_config_from_dict, save_graph
from texsheet.latex import compile_latex, save_table_tex
from texsheet.paths import project_path


def run_generation(log=None):
    def write_log(message):
        if log is not None:
            log(message)

    config = normalize_config(load_config())
    save_config(config)

    loaded_dataframes = {}
    for table_config in config["tables"]:
        loaded_dataframes[table_config["id"]] = pd.read_csv(
            project_path(table_config["input_csv"])
        )

    first_dataframe = None
    graph_jobs = []
    for table_config in config["tables"]:
        dataframe = loaded_dataframes[table_config["id"]]
        external_tables = [
            {
                "config": other_config,
                "dataframe": loaded_dataframes[other_config["id"]],
            }
            for other_config in config["tables"]
            if other_config["id"] != table_config["id"]
        ]
        dataframe, formula_messages = apply_formulas_to_dataframe(
            dataframe,
            table_config,
            config.get("constants", {}),
            external_tables,
        )
        loaded_dataframes[table_config["id"]] = dataframe
        for message in formula_messages:
            write_log(message)
        if first_dataframe is None:
            first_dataframe = dataframe
        for graph_data in table_config.get("graph_configs", []):
            graph_jobs.append((dataframe, graph_data))
        table_path = save_table_tex(dataframe, table_config)
        write_log(f"LaTeX表を生成しました: {table_config['name']} -> {table_path}")

    enabled_graph_jobs = [job for job in graph_jobs if job[1].get("enabled", False)]
    if enabled_graph_jobs:
        for graph_dataframe, graph_data in enabled_graph_jobs:
            graph_config = graph_config_from_dict(graph_data, graph_dataframe.columns)
            graph_path = save_graph(graph_dataframe, graph_config)
            write_log(f"グラフPDFを生成しました: {graph_path}")
    elif config["graph"].get("enabled", False) and first_dataframe is not None:
        graph_config = graph_config_from_dict(config["graph"], first_dataframe.columns)
        graph_path = save_graph(first_dataframe, graph_config)
        write_log(f"グラフPDFを生成しました: {graph_path}")
    else:
        write_log("グラフ生成をスキップしました。")

    if config.get("compile", False):
        write_log("LaTeXコンパイルを開始します。")
        pdf_path = compile_latex()
        write_log(f"LaTeXコンパイルに成功しました: {pdf_path}")
    else:
        write_log("LaTeXコンパイルをスキップしました。")
