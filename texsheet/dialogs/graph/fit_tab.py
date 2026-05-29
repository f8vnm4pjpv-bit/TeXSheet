from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QLineEdit, QListWidget, QVBoxLayout, QWidget

from texsheet.graph import FitConfig, NumberFormatConfig, to_optional_float


def create_fit_tab(dialog, graph_config):
    tab = QWidget()
    layout = QHBoxLayout()
    dialog.fit_series_list_widget = QListWidget()
    dialog.fit_series_list_widget.currentRowChanged.connect(dialog.on_fit_series_selected)
    layout.addWidget(dialog.fit_series_list_widget, 1)

    detail_layout = QVBoxLayout()
    form_layout = QFormLayout()
    dialog.fit_enabled_check = QCheckBox("近似曲線を表示する")
    dialog.fit_type_box = QComboBox()
    dialog.fit_type_box.addItem("線形近似", "linear")
    dialog.fit_type_box.addItem("n次多項式近似", "polynomial")
    dialog.fit_type_box.addItem("べき乗近似", "power")
    dialog.fit_type_box.addItem("指数近似", "exponential")
    dialog.fit_type_box.addItem("対数近似", "logarithmic")
    dialog.fit_degree_edit = QLineEdit("1")
    dialog.fit_force_intercept_zero_check = QCheckBox("切片を0に固定する")
    dialog.fit_r2_space_box = QComboBox()
    dialog.fit_r2_space_box.addItem("元スケール", "original")
    dialog.fit_r2_space_box.addItem("線形化スケール", "linearized")
    dialog.fit_equation_check = QCheckBox("近似式を表示する")
    dialog.fit_r2_check = QCheckBox("R²を表示する")
    dialog.fit_x_min_edit = QLineEdit()
    dialog.fit_x_max_edit = QLineEdit()
    dialog.fit_outside_box = QComboBox()
    dialog.fit_outside_box.addItem("表示しない", "hidden")
    dialog.fit_outside_box.addItem("点線で表示する", "dashed")
    dialog.fit_outside_box.addItem("実線で表示する", "solid")
    dialog.fit_number_mode_box = QComboBox()
    dialog.fit_number_mode_box.addItem("小数点以下", "decimal_places")
    dialog.fit_number_mode_box.addItem("有効数字", "significant_figures")
    dialog.fit_number_digits_edit = QLineEdit("4")
    dialog.fit_weight_mode_box = QComboBox()
    dialog.fit_weight_mode_box.addItem("重みなし", "none")
    dialog.fit_weight_mode_box.addItem("Y誤差列を使う", "y_sigma")
    dialog.fit_weight_mode_box.addItem("重み列を使う", "custom_weight")
    dialog.fit_weight_column_box = QComboBox()
    dialog.fit_weight_column_box.addItems(dialog.columns)
    for editor in [dialog.fit_degree_edit, dialog.fit_x_min_edit, dialog.fit_x_max_edit]:
        editor.returnPressed.connect(dialog.update_preview)

    form_layout.addRow("", dialog.fit_enabled_check)
    form_layout.addRow("近似タイプ", dialog.fit_type_box)
    form_layout.addRow("多項式次数", dialog.fit_degree_edit)
    form_layout.addRow("", dialog.fit_force_intercept_zero_check)
    form_layout.addRow("R²計算空間", dialog.fit_r2_space_box)
    form_layout.addRow("", dialog.fit_equation_check)
    form_layout.addRow("", dialog.fit_r2_check)
    form_layout.addRow("近似X最小値", dialog.fit_x_min_edit)
    form_layout.addRow("近似X最大値", dialog.fit_x_max_edit)
    form_layout.addRow("データ範囲外", dialog.fit_outside_box)
    form_layout.addRow("近似式の数値表示", dialog.fit_number_mode_box)
    form_layout.addRow("近似式の桁数", dialog.fit_number_digits_edit)
    form_layout.addRow("重み設定", dialog.fit_weight_mode_box)
    form_layout.addRow("重み/誤差列", dialog.fit_weight_column_box)
    detail_layout.addLayout(form_layout)
    detail_layout.addStretch()
    layout.addLayout(detail_layout, 3)
    tab.setLayout(layout)
    dialog.tabs.addTab(tab, "近似")

def refresh_fit_series_list(dialog):
    if not hasattr(dialog, "fit_series_list_widget"):
        return
    current_row = dialog.fit_series_list_widget.currentRow()
    dialog.fit_series_list_widget.blockSignals(True)
    dialog.fit_series_list_widget.clear()
    for series in dialog.series_configs:
        dialog.fit_series_list_widget.addItem(series.name or series.y_column)
    dialog.fit_series_list_widget.blockSignals(False)
    if dialog.series_configs:
        dialog.fit_series_list_widget.setCurrentRow(min(max(current_row, 0), len(dialog.series_configs) - 1))
    else:
        dialog.current_fit_series_index = -1

def on_fit_series_selected(dialog, row):
    dialog.save_current_fit_detail()
    dialog.current_fit_series_index = row
    if 0 <= row < len(dialog.series_configs):
        dialog.load_fit_detail(dialog.series_configs[row].fit_config)

def load_fit_detail(dialog, fit_config):
    dialog.fit_enabled_check.setChecked(fit_config.enabled)
    dialog.set_combo_data(dialog.fit_type_box, fit_config.fit_type)
    dialog.fit_degree_edit.setText(str(fit_config.degree))
    dialog.fit_force_intercept_zero_check.setChecked(fit_config.force_intercept_zero)
    dialog.set_combo_data(dialog.fit_r2_space_box, fit_config.r2_space)
    dialog.fit_equation_check.setChecked(fit_config.show_equation)
    dialog.fit_r2_check.setChecked(fit_config.show_r2)
    dialog.fit_x_min_edit.setText(dialog.float_text(fit_config.x_min))
    dialog.fit_x_max_edit.setText(dialog.float_text(fit_config.x_max))
    dialog.set_combo_data(dialog.fit_outside_box, fit_config.outside_range_mode)
    dialog.set_combo_data(dialog.fit_number_mode_box, fit_config.equation_number_format.mode)
    dialog.fit_number_digits_edit.setText(str(fit_config.equation_number_format.digits))
    dialog.set_combo_data(dialog.fit_weight_mode_box, fit_config.weight_mode)
    if fit_config.weight_column in dialog.columns:
        dialog.fit_weight_column_box.setCurrentText(fit_config.weight_column)

def save_current_fit_detail(dialog):
    index = dialog.current_fit_series_index
    if not (0 <= index < len(dialog.series_configs)):
        return
    dialog.series_configs[index].fit_config = FitConfig(
        enabled=dialog.fit_enabled_check.isChecked(),
        fit_type=dialog.fit_type_box.currentData(),
        degree=int(to_optional_float(dialog.fit_degree_edit.text()) or 1),
        force_intercept_zero=dialog.fit_force_intercept_zero_check.isChecked(),
        r2_space=dialog.fit_r2_space_box.currentData(),
        weight_mode=dialog.fit_weight_mode_box.currentData(),
        weight_column=dialog.fit_weight_column_box.currentText(),
        show_curve=dialog.fit_enabled_check.isChecked(),
        show_equation=dialog.fit_equation_check.isChecked(),
        show_r2=dialog.fit_r2_check.isChecked(),
        x_min=to_optional_float(dialog.fit_x_min_edit.text()),
        x_max=to_optional_float(dialog.fit_x_max_edit.text()),
        outside_range_mode=dialog.fit_outside_box.currentData(),
        equation_number_format=NumberFormatConfig(
            mode=dialog.fit_number_mode_box.currentData(),
            digits=int(to_optional_float(dialog.fit_number_digits_edit.text()) or 4),
        ),
    )
