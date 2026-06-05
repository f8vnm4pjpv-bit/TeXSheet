import csv
import re
import shutil
from pathlib import PurePosixPath

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

DEFAULT_TABLE_ID = "table_001"
INVALID_FILENAME_CHARS = set('/\\:*?"<>|')
SAFE_TABLE_ID_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


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
        "input_csv": f"tables_data/{DEFAULT_TABLE_ID}.csv",
        "output": {
            "table_tex": f"tables/{DEFAULT_TABLE_ID}.tex",
            "figure_pdf": "figures/result_graph.pdf",
        },
        "tables": [
            {
                "id": DEFAULT_TABLE_ID,
                "name": "table1",
                "input_csv": f"tables_data/{DEFAULT_TABLE_ID}.csv",
                "output_tex": f"tables/{DEFAULT_TABLE_ID}.tex",
                "caption": "table1",
                "label": f"tab:{DEFAULT_TABLE_ID}",
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

    default_csv_path = project_path(default_config()["input_csv"])
    if config_created and not default_csv_path.exists():
        default_csv_path.write_text("column1\n", encoding="utf-8")


def make_table_id(name, existing_ids):
    index = 1
    candidate = f"table_{index:03d}"
    while candidate in existing_ids:
        index += 1
        candidate = f"table_{index:03d}"
    return candidate


def is_safe_table_id(table_id):
    return isinstance(table_id, str) and bool(SAFE_TABLE_ID_PATTERN.fullmatch(table_id))


def table_input_csv_path(table_id):
    return f"tables_data/{table_id}.csv"


def table_output_tex_path(table_id):
    return f"tables/{table_id}.tex"


def is_safe_filename(filename, suffix):
    if not isinstance(filename, str) or not filename.endswith(suffix):
        return False
    stem = filename[: -len(suffix)]
    if not stem or stem in {".", ".."}:
        return False
    if any(char in INVALID_FILENAME_CHARS for char in filename):
        return False
    if stem.upper() in WINDOWS_RESERVED_NAMES:
        return False
    return True


def is_safe_table_file_path(relative_path, directory, suffix):
    if not isinstance(relative_path, str) or "\\" in relative_path:
        return False
    path = PurePosixPath(relative_path)
    if path.is_absolute() or ".." in path.parts or len(path.parts) != 2:
        return False
    if path.parts[0] != directory:
        return False
    return is_safe_filename(path.parts[1], suffix)


def can_migrate_project_relative_path(relative_path):
    if not isinstance(relative_path, str):
        return False
    path = PurePosixPath(relative_path)
    return not path.is_absolute() and ".." not in path.parts


def replace_latex_input_path(old_relative_path, new_relative_path):
    main_tex_path = project_path("main.tex")
    if not main_tex_path.exists():
        return

    try:
        content = main_tex_path.read_text(encoding="utf-8")
    except UnicodeError:
        return

    old_without_suffix = (
        old_relative_path[:-4]
        if old_relative_path.endswith(".tex")
        else old_relative_path
    )
    candidates = {old_relative_path, old_without_suffix}

    def replace_match(match):
        command, path_text, close = match.groups()
        if path_text in candidates:
            return f"{command}{new_relative_path}{close}"
        return match.group(0)

    pattern = re.compile(r"(\\(?:input|include)\s*\{\s*)([^{}]+?)(\s*\})")
    updated = pattern.sub(replace_match, content)
    if updated != content:
        main_tex_path.write_text(updated, encoding="utf-8")


def migrate_table_file(old_relative_path, new_relative_path, update_main_tex=False):
    if old_relative_path == new_relative_path:
        return
    if not can_migrate_project_relative_path(old_relative_path):
        return

    old_path = project_path(old_relative_path)
    new_path = project_path(new_relative_path)
    if old_path.exists() and not new_path.exists():
        new_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(old_path, new_path)
    if update_main_tex:
        replace_latex_input_path(old_relative_path, new_relative_path)


def normalize_table_file_paths(
    table_id,
    config,
    table_config,
    existing_input_paths=None,
    existing_output_paths=None,
):
    existing_input_paths = existing_input_paths or set()
    existing_output_paths = existing_output_paths or set()
    raw_input_csv = table_config.get("input_csv", config.get("input_csv"))
    raw_output_tex = table_config.get(
        "output_tex",
        config.get("output", {}).get("table_tex"),
    )

    input_csv = raw_input_csv
    output_tex = raw_output_tex
    if (
        not is_safe_table_file_path(input_csv, "tables_data", ".csv")
        or input_csv in existing_input_paths
    ):
        input_csv = table_input_csv_path(table_id)
        if raw_input_csv:
            migrate_table_file(raw_input_csv, input_csv)
    if (
        not is_safe_table_file_path(output_tex, "tables", ".tex")
        or output_tex in existing_output_paths
    ):
        output_tex = table_output_tex_path(table_id)
        if raw_output_tex:
            migrate_table_file(raw_output_tex, output_tex, update_main_tex=True)
    return input_csv, output_tex


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


def normalize_table_config(
    config,
    table_config=None,
    existing_ids=None,
    existing_input_paths=None,
    existing_output_paths=None,
):
    table_config = table_config or {}
    existing_ids = existing_ids or set()
    caption = repair_mojibake(table_config.get("caption", "表"))
    label = table_config.get("label", "tab:result")
    table_id = table_config.get("id")
    if not is_safe_table_id(table_id) or table_id in existing_ids:
        table_id = make_table_id(table_config.get("name", ""), existing_ids)
    input_csv, output_tex = normalize_table_file_paths(
        table_id,
        config,
        table_config,
        existing_input_paths,
        existing_output_paths,
    )
    csv_headers = read_csv_headers(input_csv)
    configured_columns = table_config.get("columns", [])
    configured_headers = [
        str(column.get("display_name", ""))
        for column in configured_columns
        if isinstance(column, dict) and column.get("display_name")
    ]
    reference_headers = configured_headers or csv_headers
    normalized = {
        "id": table_id,
        "name": repair_mojibake(table_config.get("name", caption)),
        "input_csv": input_csv,
        "output_tex": output_tex,
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

    raw_tables = config.get("tables")
    if raw_tables is None:
        raw_tables = [config.get("table", {})]

    normalized_tables = []
    existing_ids = set()
    existing_input_paths = set()
    existing_output_paths = set()
    for table_config in raw_tables:
        normalized_table = normalize_table_config(
            config,
            table_config,
            existing_ids,
            existing_input_paths,
            existing_output_paths,
        )
        normalized_tables.append(normalized_table)
        existing_ids.add(normalized_table["id"])
        existing_input_paths.add(normalized_table["input_csv"])
        existing_output_paths.add(normalized_table["output_tex"])
    config["tables"] = normalized_tables

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
