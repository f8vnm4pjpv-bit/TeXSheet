from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QLineEdit, QListWidget, QListWidgetItem, QWidget


def on_x_column_changed(dialog, column):
    dialog.x_label_edit.setText(column)
    dialog.update_series_rows()


def on_y_columns_changed(dialog):
    y_columns = dialog.selected_y_columns()
    dialog.y_label_edit.setText(", ".join(y_columns))
    dialog.update_series_rows()


def create_basic_tab(dialog, graph_config):
    tab = QWidget()
    form_layout = QFormLayout()
    dialog.title_edit = QLineEdit(graph_config.title)
    dialog.title_edit.returnPressed.connect(dialog.update_preview)
    form_layout.addRow("タイトル", dialog.title_edit)

    dialog.title_visible_check = QCheckBox("タイトルを表示する")
    dialog.title_visible_check.setChecked(graph_config.title_visible)
    form_layout.addRow("", dialog.title_visible_check)

    dialog.x_column_box = QComboBox()
    dialog.x_column_box.addItems(dialog.columns)
    default_x = dialog.default_x_column(graph_config)
    if default_x in dialog.columns:
        dialog.x_column_box.setCurrentText(default_x)
    dialog.x_column_box.currentTextChanged.connect(
        lambda text: on_x_column_changed(dialog, text)
    )
    form_layout.addRow("X列", dialog.x_column_box)

    dialog.y_column_list = QListWidget()
    dialog.y_column_list.setSelectionMode(QListWidget.MultiSelection)
    selected_y_columns = dialog.default_y_columns(graph_config, default_x)
    for column in dialog.columns:
        item = QListWidgetItem(column)
        dialog.y_column_list.addItem(item)
        if column in selected_y_columns:
            item.setSelected(True)
    dialog.y_column_list.itemSelectionChanged.connect(
        lambda: on_y_columns_changed(dialog)
    )
    form_layout.addRow("Y列", dialog.y_column_list)

    dialog.plot_type_box = QComboBox()
    for label, value in dialog.PLOT_TYPE_OPTIONS:
        dialog.plot_type_box.addItem(label, value)
    default_plot_type = graph_config.default_plot_type
    if graph_config.series:
        default_plot_type = graph_config.series[0].plot_type
    index = dialog.plot_type_box.findData(default_plot_type)
    dialog.plot_type_box.setCurrentIndex(max(index, 0))
    dialog.plot_type_box.currentIndexChanged.connect(
        lambda _index: dialog.update_series_rows()
    )
    form_layout.addRow("グラフ種別", dialog.plot_type_box)

    dialog.x_label_edit = QLineEdit(graph_config.axes["x_bottom"].label)
    dialog.y_label_edit = QLineEdit(graph_config.axes["y_left"].label)
    dialog.x_label_edit.returnPressed.connect(dialog.update_preview)
    dialog.y_label_edit.returnPressed.connect(dialog.update_preview)
    form_layout.addRow("X軸ラベル", dialog.x_label_edit)
    form_layout.addRow("Y軸ラベル", dialog.y_label_edit)

    dialog.grid_check = QCheckBox("グリッドを表示")
    dialog.grid_check.setChecked(graph_config.grid.enabled)
    form_layout.addRow("", dialog.grid_check)
    dialog.plot_frame_check = QCheckBox("プロットエリア枠を表示")
    dialog.plot_frame_check.setChecked(graph_config.show_plot_frame)
    form_layout.addRow("", dialog.plot_frame_check)

    dialog.legend_location_box = QComboBox()
    for label, value in [
        ("自動", "best"),
        ("左上", "upper left"),
        ("右上", "upper right"),
        ("左下", "lower left"),
        ("右下", "lower right"),
        ("外側右", "outside right"),
    ]:
        dialog.legend_location_box.addItem(label, value)
    dialog.set_combo_data(dialog.legend_location_box, graph_config.legend_location)
    form_layout.addRow("凡例位置", dialog.legend_location_box)

    dialog.fit_label_location_box = QComboBox()
    for label, value in [
        ("自動", "auto"),
        ("左上", "upper left"),
        ("右上", "upper right"),
        ("左下", "lower left"),
        ("右下", "lower right"),
    ]:
        dialog.fit_label_location_box.addItem(label, value)
    dialog.set_combo_data(dialog.fit_label_location_box, graph_config.fit_label_location)
    form_layout.addRow("近似式位置", dialog.fit_label_location_box)

    dialog.fit_label_background_check = QCheckBox("近似式に背景を付ける")
    dialog.fit_label_background_check.setChecked(graph_config.fit_label_background)
    form_layout.addRow("", dialog.fit_label_background_check)

    dialog.japanese_font_edit = QLineEdit(graph_config.font.japanese_font)
    dialog.latin_font_edit = QLineEdit(graph_config.font.latin_font)
    dialog.font_size_edit = QLineEdit(str(graph_config.font.font_size))
    dialog.japanese_font_edit.returnPressed.connect(dialog.update_preview)
    dialog.latin_font_edit.returnPressed.connect(dialog.update_preview)
    dialog.font_size_edit.returnPressed.connect(dialog.update_preview)
    form_layout.addRow("日本語フォント", dialog.japanese_font_edit)
    form_layout.addRow("英数字フォント", dialog.latin_font_edit)
    form_layout.addRow("フォントサイズ", dialog.font_size_edit)
    tab.setLayout(form_layout)
    dialog.tabs.addTab(tab, "基本")
