import csv
import re

import yaml

from texsheet.columns import normalize_columns_metadata
from texsheet.paths import (
    CONFIG_PATH,
    FIGURES_DIR,
    PROJECT_DIR,
    TABLES_DATA_DIR,
    TABLES_DIR,
    project_path,
)


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def load_config():
    ensure_project_structure()
    with CONFIG_PATH.open(encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def save_config(config):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        yaml.dump(
            config,
            Dumper=NoAliasDumper,
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def default_config():
    return {
        "compile": False,
        "constants": {},
        "input_csv": "tables_data/table1.csv",
        "output": {
            "table_tex": "tables/table1.tex",
            "figure_pdf": "figures/result_graph.pdf",
        },
        "tables": [
            {
                "id": "table1",
                "name": "table1",
                "input_csv": "tables_data/table1.csv",
                "output_tex": "tables/table1.tex",
                "caption": "table1",
                "label": "tab:table1",
                "column_alignments": {"column1": "l"},
                "columns": [
                    {"display_name": "column1", "internal_name": "column1"},
                ],
                "border_style": "booktabs",
                "formulas": {},
                "graph_configs": [],
            }
        ],
        "graph": {"enabled": False},
    }


def ensure_project_structure():
    for directory in (PROJECT_DIR, TABLES_DIR, FIGURES_DIR, TABLES_DATA_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    config_created = False
    if not CONFIG_PATH.exists():
        save_config(default_config())
        config_created = True

    default_csv_path = project_path("tables_data/table1.csv")
    if config_created and not default_csv_path.exists():
        default_csv_path.write_text("column1\n", encoding="utf-8")


def make_table_id(name, existing_ids):
    base = re.sub(r"[^0-9A-Za-z_]+", "_", name).strip("_").lower()
    if not base:
        base = "table"
    if base[0].isdigit():
        base = f"table_{base}"

    candidate = base
    index = 2
    while candidate in existing_ids:
        candidate = f"{base}_{index}"
        index += 1
    return candidate


def repair_mojibake(value):
    if not isinstance(value, str):
        return value
    try:
        repaired = value.encode("cp932").decode("utf-8")
    except UnicodeError:
        return value
    return repaired


def read_csv_headers(relative_path):
    try:
        with project_path(relative_path).open(newline="", encoding="utf-8-sig") as file:
            return next(csv.reader(file), [])
    except (FileNotFoundError, StopIteration, UnicodeError):
        return []


def normalize_keyed_settings(settings, reference_keys=None):
    if not isinstance(settings, dict):
        return {}

    reference_keys = reference_keys or []
    normalized = {}
    items = list(settings.items())
    use_position_fallback = len(items) == len(reference_keys)

    for index, (key, value) in enumerate(items):
        repaired_key = repair_mojibake(key)
        if key in reference_keys:
            normalized_key = key
        elif repaired_key in reference_keys:
            normalized_key = repaired_key
        elif (
            use_position_fallback
            and index < len(reference_keys)
            and reference_keys[index] not in normalized
        ):
            normalized_key = reference_keys[index]
        else:
            normalized_key = repaired_key
        normalized[normalized_key] = repair_mojibake(value)
    return normalized


def normalize_table_config(config, table_config=None):
    table_config = table_config or {}
    output = config.get("output", {})
    caption = repair_mojibake(table_config.get("caption", "表"))
    label = table_config.get("label", "tab:result")
    input_csv = table_config.get("input_csv", config.get("input_csv", "data.csv"))
    csv_headers = read_csv_headers(input_csv)
    configured_columns = table_config.get("columns", [])
    configured_headers = [
        str(column.get("display_name", ""))
        for column in configured_columns
        if isinstance(column, dict) and column.get("display_name")
    ]
    reference_headers = configured_headers or csv_headers
    normalized = {
        "id": table_config.get("id", "table1"),
        "name": repair_mojibake(table_config.get("name", caption)),
        "input_csv": input_csv,
        "output_tex": table_config.get(
            "output_tex",
            output.get("table_tex", "tables/result_table.tex"),
        ),
        "caption": caption,
        "label": label,
        "column_alignments": normalize_keyed_settings(
            table_config.get("column_alignments", {}),
            reference_headers,
        ),
        "border_style": table_config.get("border_style", "booktabs"),
        "formulas": normalize_keyed_settings(
            table_config.get("formulas", {}),
            reference_headers,
        ),
        "graph_configs": list(table_config.get("graph_configs", [])),
    }
    normalized["columns"] = normalize_columns_metadata(
        {"columns": configured_columns},
        reference_headers,
    )
    return normalized


def normalize_graph_config(config):
    from texsheet.graph import graph_config_from_dict

    graph_data = config.get("graph", {})
    graph_config = graph_config_from_dict(
        graph_data,
        columns=[],
        table_id=graph_data.get("table_id", ""),
    ).to_dict()
    figure_pdf = config.get("output", {}).get("figure_pdf")
    if figure_pdf and not config.get("graph", {}).get("output_path"):
        graph_config["output_path"] = figure_pdf
    return graph_config


def normalize_table_graph_configs(table_config, fallback_graph=None):
    from texsheet.graph import graph_config_from_dict

    csv_headers = read_csv_headers(table_config["input_csv"])
    graph_configs = list(table_config.get("graph_configs", []))
    if not graph_configs and fallback_graph:
        fallback_table_id = fallback_graph.get("table_id", "")
        if not fallback_table_id or fallback_table_id == table_config["id"]:
            graph_configs = [fallback_graph]

    table_config["graph_configs"] = [
        graph_config_from_dict(
            graph_config,
            columns=csv_headers,
            table_id=table_config["id"],
        ).to_dict()
        for graph_config in graph_configs
    ]
    return table_config


def normalize_config(config):
    config.setdefault("compile", False)
    config.setdefault("constants", {})
    config.setdefault("output", {})
    config["output"].setdefault("figure_pdf", "figures/result_graph.pdf")

    if "tables" not in config:
        config["tables"] = [normalize_table_config(config, config.get("table", {}))]
    else:
        config["tables"] = [
            normalize_table_config(config, table_config)
            for table_config in config["tables"]
        ]

    if config["tables"]:
        first_table = config["tables"][0]
        config["input_csv"] = first_table["input_csv"]
        config["table"] = {
            "caption": first_table["caption"],
            "label": first_table["label"],
            "column_alignments": first_table.get("column_alignments", {}),
            "border_style": first_table.get("border_style", "booktabs"),
            "formulas": first_table.get("formulas", {}),
        }
        config["output"]["table_tex"] = first_table["output_tex"]

    config.setdefault("graph", {"enabled": False})
    config["graph"] = normalize_graph_config(config)
    for index, table_config in enumerate(config["tables"]):
        fallback_graph = config["graph"] if index == 0 or config["graph"].get("table_id") == table_config["id"] else None
        normalize_table_graph_configs(table_config, fallback_graph)
    config["output"]["figure_pdf"] = config["graph"].get(
        "output_path",
        config["output"]["figure_pdf"],
    )

    return config
