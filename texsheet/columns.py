DISPLAY_ROLE = 0x0100
INTERNAL_ROLE = 0x0101


def normalize_internal_name(display_name, internal_name=None):
    internal_name = str(internal_name or "").strip()
    return internal_name or str(display_name)


def normalize_columns_metadata(table_config, display_names):
    configured = table_config.get("columns", [])
    if not isinstance(configured, list):
        configured = []

    by_display = {}
    for column in configured:
        if not isinstance(column, dict):
            continue
        display_name = str(column.get("display_name", "")).strip()
        if display_name and display_name not in by_display:
            by_display[display_name] = column

    normalized = []
    for index, display_name in enumerate(display_names):
        source = by_display.get(display_name)
        if source is None and index < len(configured) and isinstance(configured[index], dict):
            source = configured[index]
        internal_name = source.get("internal_name", "") if source else ""
        normalized.append(
            {
                "display_name": str(display_name),
                "internal_name": normalize_internal_name(display_name, internal_name),
            }
        )
    table_config["columns"] = normalized
    return normalized


def display_names_from_metadata(table_config):
    return [
        str(column.get("display_name", ""))
        for column in table_config.get("columns", [])
        if isinstance(column, dict)
    ]


def internal_name_for_display(table_config, display_name):
    for column in table_config.get("columns", []):
        if not isinstance(column, dict):
            continue
        if column.get("display_name") == display_name:
            return normalize_internal_name(display_name, column.get("internal_name"))
    return str(display_name)


def column_reference_names(table_config, display_names=None):
    display_names = display_names or display_names_from_metadata(table_config)
    names = []
    seen = set()
    for display_name in display_names:
        for name in (display_name, internal_name_for_display(table_config, display_name)):
            if name and name not in seen:
                names.append(name)
                seen.add(name)
    return names


def validate_column_names(columns, editing_index=None):
    seen = {}
    for index, column in enumerate(columns):
        display_name = str(column.get("display_name", "")).strip()
        internal_name = normalize_internal_name(display_name, column.get("internal_name"))
        if not display_name:
            return "表示名が空である。"
        for name, kind in ((display_name, "表示名"), (internal_name, "内部名")):
            owner = seen.get(name)
            if owner is not None and owner != index:
                return f"{kind}が他の列名と重複している: {name}"
            if owner is not None and owner == index and display_name != internal_name:
                return f"表示名と内部名が重複している: {name}"
            seen[name] = index
    return ""


def header_label(display_name, internal_name):
    internal_name = normalize_internal_name(display_name, internal_name)
    return f"{display_name}\n[{internal_name}]"
