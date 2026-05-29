from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QLineEdit, QListWidget, QVBoxLayout, QWidget

from texsheet.graph import LineConfig, MarkerConfig, SeriesConfig, to_optional_float


def create_series_tab(dialog, graph_config):
    tab = QWidget()
    layout = QHBoxLayout()

    dialog.series_list_widget = QListWidget()
    dialog.series_list_widget.currentRowChanged.connect(dialog.on_series_selected)
    layout.addWidget(dialog.series_list_widget, 1)

    detail_layout = QVBoxLayout()
    form_layout = QFormLayout()

    dialog.series_name_edit = QLineEdit()
    dialog.series_x_column_box = QComboBox()
    dialog.series_y_column_box = QComboBox()
    dialog.series_x_axis_box = QComboBox()
    dialog.series_y_axis_box = QComboBox()
    dialog.series_x_column_box.addItems(dialog.columns)
    dialog.series_y_column_box.addItems(dialog.columns)
    dialog.series_x_axis_box.addItem("下側X軸", "x_bottom")
    dialog.series_x_axis_box.addItem("上側X軸", "x_top")
    dialog.series_y_axis_box.addItem("左側Y軸", "y_left")
    dialog.series_y_axis_box.addItem("右側Y軸", "y_right")

    dialog.series_plot_type_box = dialog.combo(dialog.PLOT_TYPE_OPTIONS, "scatter")
    dialog.series_color_box = dialog.combo(dialog.COLOR_OPTIONS, "")
    dialog.series_marker_box = dialog.combo(dialog.MARKER_OPTIONS, "o")
    dialog.series_marker_size_edit = QLineEdit("6.0")
    dialog.series_line_visible_check = QCheckBox("線を表示する")
    dialog.series_line_style_box = dialog.combo(dialog.LINE_STYLE_OPTIONS, "-")
    dialog.series_line_width_edit = QLineEdit("1.5")

    form_layout.addRow("系列名", dialog.series_name_edit)
    form_layout.addRow("X列", dialog.series_x_column_box)
    form_layout.addRow("Y列", dialog.series_y_column_box)
    form_layout.addRow("使用X軸", dialog.series_x_axis_box)
    form_layout.addRow("使用Y軸", dialog.series_y_axis_box)
    form_layout.addRow("種別", dialog.series_plot_type_box)
    form_layout.addRow("マーカー色", dialog.series_color_box)
    form_layout.addRow("マーカー形状", dialog.series_marker_box)
    form_layout.addRow("マーカーサイズ", dialog.series_marker_size_edit)
    form_layout.addRow("", dialog.series_line_visible_check)
    form_layout.addRow("線種", dialog.series_line_style_box)
    form_layout.addRow("線幅", dialog.series_line_width_edit)

    detail_layout.addLayout(form_layout)
    detail_layout.addStretch()
    layout.addLayout(detail_layout, 3)
    tab.setLayout(layout)
    dialog.tabs.addTab(tab, "系列")

def make_default_series(dialog, index, y_column, default_x, default_plot_type):
    return SeriesConfig(
        name=y_column,
        x_column=default_x,
        y_column=y_column,
        plot_type=default_plot_type,
        marker_config=MarkerConfig(
            color=dialog.COLOR_OPTIONS[(index + 1) % len(dialog.COLOR_OPTIONS)][1],
            shape=["o", "s", "^", "D", "x"][index % 5],
            size=6.0,
        ),
        line_config=LineConfig(
            visible=default_plot_type in {"line", "scatter_line"},
            style="-",
            width=1.5,
        ),
    )


def sync_series_from_basic(dialog):
    if not hasattr(dialog, "series_list_widget"):
        return
    dialog.save_current_series_detail()
    y_columns = dialog.selected_y_columns()
    default_x = dialog.x_column_box.currentText()
    default_plot_type = dialog.plot_type_box.currentData()
    existing_by_y = {
        series.y_column: SeriesConfig.from_dict(series.to_dict())
        for series in dialog.series_configs
    }
    dialog.series_configs = []
    for index, y_column in enumerate(y_columns):
        existing = existing_by_y.get(y_column) or dialog.find_existing_series(y_column)
        if existing:
            series = SeriesConfig.from_dict(existing.to_dict())
            series.x_column = default_x
            series.y_column = y_column
            dialog.series_configs.append(series)
            continue
        dialog.series_configs.append(
            make_default_series(dialog, index, y_column, default_x, default_plot_type)
        )
    dialog.refresh_series_list()


def update_series_rows(dialog):
    sync_series_from_basic(dialog)

def refresh_series_list(dialog):
    current_row = dialog.series_list_widget.currentRow()
    dialog.series_list_widget.blockSignals(True)
    dialog.series_list_widget.clear()
    for series in dialog.series_configs:
        dialog.series_list_widget.addItem(series.name or series.y_column)
    if dialog.series_configs:
        row = min(max(current_row, 0), len(dialog.series_configs) - 1)
        dialog.series_list_widget.setCurrentRow(row)
        dialog.series_list_widget.blockSignals(False)
        dialog.current_series_index = row
        dialog.load_series_detail(dialog.series_configs[row])
    else:
        dialog.series_list_widget.blockSignals(False)
        dialog.current_series_index = -1
        dialog.clear_series_detail()
    dialog.refresh_fit_series_list()

def on_series_selected(dialog, row):
    dialog.save_current_series_detail()
    dialog.current_series_index = row
    if 0 <= row < len(dialog.series_configs):
        dialog.load_series_detail(dialog.series_configs[row])
    else:
        dialog.clear_series_detail()

def clear_series_detail(dialog):
    dialog.series_name_edit.setText("")
    dialog.series_marker_size_edit.setText("")
    dialog.series_line_width_edit.setText("")

def load_series_detail(dialog, series):
    dialog.series_name_edit.setText(series.name or series.y_column)
    if series.x_column in dialog.columns:
        dialog.series_x_column_box.setCurrentText(series.x_column)
    if series.y_column in dialog.columns:
        dialog.series_y_column_box.setCurrentText(series.y_column)
    dialog.set_combo_data(dialog.series_x_axis_box, series.x_axis)
    dialog.set_combo_data(dialog.series_y_axis_box, series.y_axis)
    dialog.set_combo_data(dialog.series_plot_type_box, series.plot_type)
    dialog.set_combo_data(dialog.series_color_box, series.marker_color)
    dialog.set_combo_data(dialog.series_marker_box, series.marker)
    dialog.series_marker_size_edit.setText(str(series.marker_size))
    dialog.series_line_visible_check.setChecked(series.show_line)
    dialog.set_combo_data(dialog.series_line_style_box, series.line_style)
    dialog.series_line_width_edit.setText(str(series.line_width))

def save_current_series_detail(dialog):
    index = dialog.current_series_index
    if not (0 <= index < len(dialog.series_configs)):
        return
    y_column = dialog.series_configs[index].y_column
    marker_size = to_optional_float(dialog.series_marker_size_edit.text()) or 6.0
    line_width = to_optional_float(dialog.series_line_width_edit.text()) or 1.5
    series = SeriesConfig(
        name=dialog.series_name_edit.text().strip() or y_column,
        x_column=dialog.x_column_box.currentText(),
        y_column=y_column,
        plot_type=dialog.series_plot_type_box.currentData(),
        marker_config=MarkerConfig(
            color=dialog.series_color_box.currentData(),
            shape=dialog.series_marker_box.currentData(),
            size=marker_size,
        ),
        line_config=LineConfig(
            visible=dialog.series_line_visible_check.isChecked(),
            style=dialog.series_line_style_box.currentData(),
            width=line_width,
        ),
        fit_config=dialog.series_configs[index].fit_config,
        x_axis=dialog.series_x_axis_box.currentData(),
        y_axis=dialog.series_y_axis_box.currentData(),
    )
    dialog.series_configs[index] = series
    item = dialog.series_list_widget.item(index)
    if item is not None:
        item.setText(series.name or series.y_column)

def series_from_detail(dialog):
    sync_series_from_basic(dialog)
    dialog.save_current_series_detail()
    dialog.save_current_fit_detail()
    return list(dialog.series_configs)
