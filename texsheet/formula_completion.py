from dataclasses import dataclass

from texsheet.columns import internal_name_for_display


TOKEN_DELIMITERS = set(" \t\r\n+-*/%^=(),[]{}<>")
CONSTANT_PREFIXES = ("cons.", "const.")
PROJECT_PREFIX = "proj."


@dataclass(frozen=True)
class CompletionItem:
    text: str
    label: str


def token_bounds(text, cursor_position):
    start = cursor_position
    while start > 0 and text[start - 1] not in TOKEN_DELIMITERS:
        start -= 1
    return start, cursor_position


def token_before_cursor(text, cursor_position):
    start, end = token_bounds(text, cursor_position)
    return text[start:end]


def column_completion_items(table_config, display_names):
    items = []
    seen = set()
    for display_name in display_names:
        internal_name = internal_name_for_display(table_config, display_name)
        if not internal_name or internal_name in seen:
            continue
        label = internal_name
        if internal_name != display_name:
            label = f"{internal_name}  —  {display_name}"
        items.append(CompletionItem(internal_name, label))
        seen.add(internal_name)
    return items


def table_completion_items(other_tables):
    items = []
    seen = set()
    for table in other_tables or []:
        table_name = str(table.get("name", "")).strip()
        if not table_name or table_name in seen:
            continue
        items.append(CompletionItem(f"{table_name}_", table_name))
        seen.add(table_name)
    return items


def external_column_completion_items(table, token):
    table_name = str(table.get("name", "")).strip()
    if not table_name:
        return []
    prefix = f"{table_name}_"
    items = []
    for item in column_completion_items(table, table.get("display_names", [])):
        label = f"{prefix}{item.text}"
        if item.label != item.text:
            label = f"{prefix}{item.label}"
        items.append(CompletionItem(f"{prefix}{item.text}", label))
    return matching_items(items, token)


def prefixed_completion_items(prefix, names):
    return [
        CompletionItem(f"{prefix}{name}", f"{prefix}{name}")
        for name in sorted(names)
    ]


def formula_completion_items(
    text,
    cursor_position,
    table_config,
    display_names,
    scientific_constants,
    project_constants,
    function_names,
    other_tables=None,
):
    token = token_before_cursor(text, cursor_position)
    lowered_token = token.lower()

    for table in other_tables or []:
        table_name = str(table.get("name", "")).strip()
        if table_name and lowered_token.startswith(f"{table_name.lower()}_"):
            return external_column_completion_items(table, token)

    for prefix in CONSTANT_PREFIXES:
        if token and (lowered_token.startswith(prefix) or prefix.startswith(lowered_token)):
            return matching_items(
                prefixed_completion_items(prefix, scientific_constants),
                token,
            )

    if token and (
        lowered_token.startswith(PROJECT_PREFIX)
        or PROJECT_PREFIX.startswith(lowered_token)
    ):
        return matching_items(
            prefixed_completion_items(PROJECT_PREFIX, project_constants),
            token,
        )

    items = column_completion_items(table_config, display_names)
    items.extend(
        CompletionItem(f"proj.{name}", f"proj.{name}")
        for name in sorted(project_constants)
    )
    items.extend(
        CompletionItem(f"cons.{name}", f"cons.{name}")
        for name in sorted(scientific_constants)
    )
    items.extend(
        CompletionItem(f"const.{name}", f"const.{name}")
        for name in sorted(scientific_constants)
    )
    items.extend(table_completion_items(other_tables))
    items.extend(CompletionItem(name, name) for name in sorted(function_names))
    return matching_items(items, token)


def matching_items(items, token):
    if not token:
        return items
    lowered_token = token.lower()
    return [
        item
        for item in items
        if item.text.lower().startswith(lowered_token)
        or item.label.lower().startswith(lowered_token)
    ]
