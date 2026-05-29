from texsheet.columns import internal_name_for_display


def table_reference_prefix(table_config):
    return str(table_config.get("name", "")).strip()


def add_column_aliases(row_values, table_config, row_data):
    for display_name, value in row_data.items():
        display_name = str(display_name)
        row_values[display_name] = value
        internal_name = internal_name_for_display(table_config, display_name)
        if internal_name and internal_name not in row_values:
            row_values[internal_name] = value
    return row_values


def add_external_table_aliases(row_values, row_index, external_tables):
    for table in external_tables or []:
        table_config = table.get("config", {})
        dataframe = table.get("dataframe")
        prefix = table_reference_prefix(table_config)
        if not prefix or dataframe is None:
            continue
        if row_index >= len(dataframe):
            continue
        row_data = dataframe.iloc[row_index].to_dict()
        for display_name, value in row_data.items():
            display_name = str(display_name)
            names = [display_name]
            internal_name = internal_name_for_display(table_config, display_name)
            if internal_name and internal_name != display_name:
                names.append(internal_name)
            for column_name in names:
                row_values[f"{prefix}_{column_name}"] = value
    return row_values


def missing_external_references(expression, row_index, external_tables):
    missing = []
    for table in external_tables or []:
        table_config = table.get("config", {})
        dataframe = table.get("dataframe")
        prefix = table_reference_prefix(table_config)
        if not prefix or dataframe is None or f"{prefix}_" not in expression:
            continue
        if row_index >= len(dataframe):
            missing.append(prefix)
    return missing
