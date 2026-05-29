from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QLineEdit, QVBoxLayout, QWidget

from texsheet.graph import AxisConfig, NumberFormatConfig, to_optional_float


def create_axis_tab(dialog, graph_config):
    tab = QWidget()
    layout = QVBoxLayout()
    form_layout = QFormLayout()

    dialog.axis_select_box = QComboBox()
    dialog.axis_select_box.addItem("下側X軸", "x_bottom")
    dialog.axis_select_box.addItem("上側X軸", "x_top")
    dialog.axis_select_box.addItem("左側Y軸", "y_left")
    dialog.axis_select_box.addItem("右側Y軸", "y_right")
    dialog.axis_select_box.currentIndexChanged.connect(dialog.on_axis_selected)
    form_layout.addRow("対象軸", dialog.axis_select_box)

    dialog.axis_independent_check = QCheckBox("個別に設定")
    dialog.axis_independent_check.stateChanged.connect(lambda *_: update_axis_link_controls(dialog))
    form_layout.addRow("", dialog.axis_independent_check)
    dialog.axis_visible_check = QCheckBox("軸を表示する")
    form_layout.addRow("", dialog.axis_visible_check)
    dialog.axis_label_visible_check = QCheckBox("軸ラベルを表示する")
    form_layout.addRow("", dialog.axis_label_visible_check)
    dialog.axis_label_edit = QLineEdit()
    dialog.axis_min_edit = QLineEdit()
    dialog.axis_max_edit = QLineEdit()
    dialog.axis_scale_box = QComboBox()
    dialog.axis_scale_box.addItem("線形", "linear")
    dialog.axis_scale_box.addItem("対数", "log")
    dialog.axis_tick_direction_box = QComboBox()
    dialog.axis_tick_direction_box.addItem("内側", "in")
    dialog.axis_tick_direction_box.addItem("外側", "out")
    dialog.axis_tick_direction_box.addItem("両方", "inout")
    dialog.axis_major_tick_check = QCheckBox("主目盛を表示する")
    dialog.axis_major_label_check = QCheckBox("主目盛値を表示する")
    dialog.axis_min_max_label_check = QCheckBox("最小値・最大値を表示")
    dialog.axis_major_tick_edit = QLineEdit()
    dialog.axis_minor_tick_check = QCheckBox("補助目盛を表示する")
    dialog.axis_minor_label_check = QCheckBox("補助目盛値を表示する")
    dialog.axis_minor_tick_edit = QLineEdit()
    dialog.axis_number_mode_box = QComboBox()
    dialog.axis_number_mode_box.addItem("小数点以下", "decimal_places")
    dialog.axis_number_mode_box.addItem("有効数字", "significant_figures")
    dialog.axis_number_digits_edit = QLineEdit("4")
    dialog.tick_label_position_box = QComboBox()
    dialog.tick_label_position_box.addItem("軸に沿わせる", "axis")
    dialog.tick_label_position_box.addItem("プロットエリアに沿わせる", "frame")
    dialog.axis_position_mode_box = QComboBox()
    dialog.axis_position_mode_box.addItem("通常位置", "default")
    dialog.axis_position_mode_box.addItem("0に配置", "zero")
    dialog.axis_position_mode_box.addItem("指定値に配置", "value")
    dialog.axis_position_value_edit = QLineEdit()
    dialog.axis_position_mode_box.currentIndexChanged.connect(lambda *_: update_axis_position_controls(dialog))

    for editor in [
        dialog.axis_label_edit,
        dialog.axis_min_edit,
        dialog.axis_max_edit,
        dialog.axis_major_tick_edit,
        dialog.axis_minor_tick_edit,
        dialog.axis_position_value_edit,
    ]:
        editor.returnPressed.connect(dialog.update_preview)

    form_layout.addRow("軸ラベル", dialog.axis_label_edit)
    form_layout.addRow("最小値", dialog.axis_min_edit)
    form_layout.addRow("最大値", dialog.axis_max_edit)
    form_layout.addRow("スケール", dialog.axis_scale_box)
    form_layout.addRow("目盛の向き", dialog.axis_tick_direction_box)
    form_layout.addRow("", dialog.axis_major_tick_check)
    form_layout.addRow("主目盛間隔", dialog.axis_major_tick_edit)
    form_layout.addRow("", dialog.axis_major_label_check)
    form_layout.addRow("", dialog.axis_min_max_label_check)
    form_layout.addRow("", dialog.axis_minor_tick_check)
    form_layout.addRow("補助目盛間隔", dialog.axis_minor_tick_edit)
    form_layout.addRow("", dialog.axis_minor_label_check)
    form_layout.addRow("目盛値表示", dialog.axis_number_mode_box)
    form_layout.addRow("目盛値桁数", dialog.axis_number_digits_edit)
    form_layout.addRow("目盛り値位置", dialog.tick_label_position_box)
    form_layout.addRow("軸の位置", dialog.axis_position_mode_box)
    form_layout.addRow("交点値", dialog.axis_position_value_edit)
    layout.addLayout(form_layout)
    layout.addStretch()
    tab.setLayout(layout)
    dialog.tabs.addTab(tab, "軸")
    dialog.load_axis_detail("x_bottom")

def linked_primary_axis(axis_key):
    if axis_key == "x_top":
        return "x_bottom"
    if axis_key == "y_right":
        return "y_left"
    return None

def axis_detail_widgets(dialog):
    return [
        dialog.axis_label_edit,
        dialog.axis_min_edit,
        dialog.axis_max_edit,
        dialog.axis_scale_box,
        dialog.axis_tick_direction_box,
        dialog.axis_major_tick_check,
        dialog.axis_min_max_label_check,
        dialog.axis_major_tick_edit,
        dialog.axis_minor_tick_check,
        dialog.axis_minor_label_check,
        dialog.axis_minor_tick_edit,
        dialog.axis_position_value_edit,
        dialog.axis_number_mode_box,
        dialog.axis_number_digits_edit,
        dialog.tick_label_position_box,
    ]

def update_axis_position_controls(dialog):
    dialog.axis_position_value_edit.setEnabled(
        dialog.axis_position_mode_box.currentData() == "value"
    )

def is_current_axis_linked(dialog):
    axis_key = dialog.current_axis_key
    return linked_primary_axis(axis_key) is not None and not dialog.axis_independent_check.isChecked()

def update_axis_link_controls(dialog):
    linked = is_current_axis_linked(dialog)
    for widget in axis_detail_widgets(dialog):
        widget.setEnabled(not linked)
    update_axis_position_controls(dialog)

def on_axis_selected(dialog):
    dialog.save_current_axis_detail()
    axis_key = dialog.axis_select_box.currentData()
    dialog.current_axis_key = axis_key
    dialog.load_axis_detail(axis_key)

def load_axis_detail(dialog, axis_key):
    axis = dialog.axis_configs[axis_key]
    dialog.axis_independent_check.setEnabled(axis_key in {"x_top", "y_right"})
    dialog.axis_independent_check.setChecked(axis.linked_to in {None, ""})
    dialog.axis_visible_check.setChecked(axis.visible)
    dialog.axis_label_visible_check.setChecked(axis.show_label)
    dialog.axis_label_edit.setText(axis.label)
    dialog.axis_min_edit.setText(dialog.float_text(axis.min_value))
    dialog.axis_max_edit.setText(dialog.float_text(axis.max_value))
    dialog.set_combo_data(dialog.axis_scale_box, axis.scale_type)
    dialog.set_combo_data(dialog.axis_tick_direction_box, axis.tick_direction)
    dialog.axis_major_tick_check.setChecked(axis.show_major_ticks)
    dialog.axis_major_label_check.setChecked(axis.show_major_tick_labels)
    dialog.axis_min_max_label_check.setChecked(axis.show_min_max_tick_labels)
    dialog.axis_major_tick_edit.setText(dialog.float_text(axis.major_tick))
    dialog.axis_minor_tick_check.setChecked(axis.show_minor_ticks)
    dialog.axis_minor_label_check.setChecked(axis.show_minor_tick_labels)
    dialog.axis_minor_tick_edit.setText(dialog.float_text(axis.minor_tick))
    dialog.set_combo_data(dialog.axis_number_mode_box, axis.tick_label_format.mode)
    dialog.axis_number_digits_edit.setText(str(axis.tick_label_format.digits))
    dialog.set_combo_data(dialog.tick_label_position_box, axis.tick_label_position_mode)
    dialog.set_combo_data(dialog.axis_position_mode_box, axis.axis_position_mode)
    dialog.axis_position_value_edit.setText(dialog.float_text(axis.axis_position_value))
    update_axis_link_controls(dialog)

def save_current_axis_detail(dialog):
    if not hasattr(dialog, "axis_select_box"):
        return
    axis_key = dialog.current_axis_key
    if axis_key not in dialog.axis_configs:
        return
    position = dialog.axis_configs[axis_key].position
    linked_to = None
    if axis_key == "x_top" and not dialog.axis_independent_check.isChecked():
        linked_to = "x_bottom"
    if axis_key == "y_right" and not dialog.axis_independent_check.isChecked():
        linked_to = "y_left"
    label = dialog.axis_label_edit.text().strip()
    if axis_key == "x_bottom" and hasattr(dialog, "x_label_edit"):
        dialog.x_label_edit.setText(label)
    if axis_key == "y_left" and hasattr(dialog, "y_label_edit"):
        dialog.y_label_edit.setText(label)
    if linked_to:
        axis = AxisConfig.from_dict(dialog.axis_configs[linked_to].to_dict(), position)
        axis.position = position
        axis.linked_to = linked_to
        axis.visible = dialog.axis_visible_check.isChecked()
        axis.show_label = dialog.axis_label_visible_check.isChecked()
        axis.show_major_tick_labels = dialog.axis_major_label_check.isChecked()
        axis.tick_label_position_mode = dialog.tick_label_position_box.currentData()
        axis.axis_position_mode = dialog.axis_position_mode_box.currentData()
        axis.axis_position_value = to_optional_float(dialog.axis_position_value_edit.text())
        dialog.axis_configs[axis_key] = axis
        return
    dialog.axis_configs[axis_key] = AxisConfig(
        label=label,
        min_value=to_optional_float(dialog.axis_min_edit.text()),
        max_value=to_optional_float(dialog.axis_max_edit.text()),
        major_tick=to_optional_float(dialog.axis_major_tick_edit.text()),
        minor_tick=to_optional_float(dialog.axis_minor_tick_edit.text()),
        scale_type=dialog.axis_scale_box.currentData(),
        tick_direction=dialog.axis_tick_direction_box.currentData(),
        show_major_ticks=dialog.axis_major_tick_check.isChecked(),
        show_minor_ticks=dialog.axis_minor_tick_check.isChecked(),
        show_major_tick_labels=dialog.axis_major_label_check.isChecked(),
        show_min_max_tick_labels=dialog.axis_min_max_label_check.isChecked(),
        show_minor_tick_labels=dialog.axis_minor_label_check.isChecked(),
        show_label=dialog.axis_label_visible_check.isChecked(),
        tick_label_format=NumberFormatConfig(
            mode=dialog.axis_number_mode_box.currentData(),
            digits=int(to_optional_float(dialog.axis_number_digits_edit.text()) or 4),
        ),
        linked_to=linked_to,
        position=position,
        visible=dialog.axis_visible_check.isChecked(),
        axis_position_mode=dialog.axis_position_mode_box.currentData(),
        axis_position_value=to_optional_float(dialog.axis_position_value_edit.text()),
        tick_label_position_mode=dialog.tick_label_position_box.currentData(),
    )
