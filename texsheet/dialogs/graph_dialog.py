from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from texsheet.graph import (
    AxisConfig,
    FitConfig,
    GraphConfig,
    GridConfig,
    GraphFontConfig,
    LineConfig,
    MarkerConfig,
    NumberFormatConfig,
    SeriesConfig,
    render_graph,
    to_optional_float,
)


def _load_graph_dialog_tab(module_name):
    import importlib.util
    import sys
    import types
    from pathlib import Path

    graph_dir = Path(__file__).with_name("graph")
    package_name = "texsheet.dialogs.graph"
    if package_name not in sys.modules:
        package = types.ModuleType(package_name)
        package.__path__ = [str(graph_dir)]
        sys.modules[package_name] = package
        parent = sys.modules.get("texsheet.dialogs")
        if parent is not None:
            setattr(parent, "graph", package)

    full_module_name = f"{package_name}.{module_name}"
    if full_module_name in sys.modules:
        return sys.modules[full_module_name]

    module_path = graph_dir / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(full_module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load graph dialog tab module: {module_name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_BASIC_TAB = _load_graph_dialog_tab("basic_tab")
_AXIS_TAB = _load_graph_dialog_tab("axis_tab")
_SERIES_TAB = _load_graph_dialog_tab("series_tab")
_FIT_TAB = _load_graph_dialog_tab("fit_tab")


class GraphSettingsDialog(QDialog):
    COLOR_OPTIONS = [
        ("自動", ""),
        ("青", "tab:blue"),
        ("赤", "tab:red"),
        ("緑", "tab:green"),
        ("黒", "black"),
        ("オレンジ", "tab:orange"),
        ("紫", "tab:purple"),
    ]
    MARKER_OPTIONS = [
        ("円", "o"),
        ("四角", "s"),
        ("三角", "^"),
        ("ひし形", "D"),
        ("×", "x"),
        ("*", "*"),
    ]
    LINE_STYLE_OPTIONS = [
        ("実線", "-"),
        ("破線", "--"),
        ("点線", ":"),
        ("一点鎖線", "-."),
    ]
    PLOT_TYPE_OPTIONS = [
        ("散布図", "scatter"),
        ("折れ線", "line"),
        ("散布図＋折れ線", "scatter_line"),
    ]

    def __init__(self, dataframe, graph_config, table_id="", parent=None):
        super().__init__(parent)
        self.dataframe = dataframe
        self.table_id = table_id
        self.output_path = graph_config.output_path
        self.columns = [str(column) for column in dataframe.columns]
        self.initial_series = graph_config.series
        self.series_configs = [SeriesConfig.from_dict(series.to_dict()) for series in graph_config.series]
        self.axis_configs = {
            key: AxisConfig.from_dict(axis.to_dict(), axis.position)
            for key, axis in graph_config.axes.items()
        }
        self.current_series_index = -1
        self.current_axis_key = "x_bottom"
        self.current_fit_series_index = -1
        self.accepted_config = None
        self.setWindowTitle("グラフ作成")
        self.resize(1100, 720)

        self.figure = Figure(figsize=(6.4, 4.2), dpi=100)
        self.canvas = FigureCanvas(self.figure)

        layout = QHBoxLayout()
        settings_layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.create_basic_tab(graph_config)
        self.create_axis_tab(graph_config)
        self.create_series_tab(graph_config)
        self.create_fit_tab(graph_config)
        settings_layout.addWidget(self.tabs)

        self.preview_button = QPushButton("プレビュー更新")
        self.preview_button.clicked.connect(self.update_preview)
        settings_layout.addWidget(self.preview_button)

        self.error_label = QLabel("")
        settings_layout.addWidget(self.error_label)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_button = self.buttons.button(QDialogButtonBox.Ok)
        if ok_button is not None:
            ok_button.setDefault(False)
            ok_button.setAutoDefault(False)
            ok_button.setFocusPolicy(Qt.NoFocus)
        cancel_button = self.buttons.button(QDialogButtonBox.Cancel)
        if cancel_button is not None:
            cancel_button.setDefault(False)
            cancel_button.setAutoDefault(False)
        self.buttons.accepted.connect(self.try_accept)
        self.buttons.rejected.connect(self.reject)
        settings_layout.addWidget(self.buttons)

        layout.addLayout(settings_layout, 0)
        layout.addWidget(self.canvas, 1)
        self.setLayout(layout)
        self.disable_default_buttons()
        QTimer.singleShot(0, self.disable_default_buttons)
        self.update_series_rows()
        self.update_preview()

    def disable_default_buttons(self):
        for role in (QDialogButtonBox.Ok, QDialogButtonBox.Cancel):
            button = self.buttons.button(role)
            if button is not None:
                button.setDefault(False)
                button.setAutoDefault(False)
        ok_button = self.buttons.button(QDialogButtonBox.Ok)
        if ok_button is not None:
            ok_button.setFocusPolicy(Qt.NoFocus)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self.disable_default_buttons)

    def create_basic_tab(self, graph_config):
        return _BASIC_TAB.create_basic_tab(self, graph_config)

    def create_axis_tab(self, graph_config):
        return _AXIS_TAB.create_axis_tab(self, graph_config)

    def create_series_tab(self, graph_config):
        return _SERIES_TAB.create_series_tab(self, graph_config)

    def create_fit_tab(self, graph_config):
        return _FIT_TAB.create_fit_tab(self, graph_config)

    def update_series_rows(self):
        return _SERIES_TAB.update_series_rows(self)

    def refresh_series_list(self):
        return _SERIES_TAB.refresh_series_list(self)

    def on_series_selected(self, row):
        return _SERIES_TAB.on_series_selected(self, row)

    def on_axis_selected(self):
        return _AXIS_TAB.on_axis_selected(self)

    def load_axis_detail(self, axis_key):
        return _AXIS_TAB.load_axis_detail(self, axis_key)

    def save_current_axis_detail(self):
        return _AXIS_TAB.save_current_axis_detail(self)

    def clear_series_detail(self):
        return _SERIES_TAB.clear_series_detail(self)

    def load_series_detail(self, series):
        return _SERIES_TAB.load_series_detail(self, series)

    def save_current_series_detail(self):
        return _SERIES_TAB.save_current_series_detail(self)

    def series_from_detail(self):
        return _SERIES_TAB.series_from_detail(self)

    def refresh_fit_series_list(self):
        return _FIT_TAB.refresh_fit_series_list(self)

    def on_fit_series_selected(self, row):
        return _FIT_TAB.on_fit_series_selected(self, row)

    def load_fit_detail(self, fit_config):
        return _FIT_TAB.load_fit_detail(self, fit_config)

    def save_current_fit_detail(self):
        return _FIT_TAB.save_current_fit_detail(self)

    def default_x_column(self, graph_config):
        if (
            graph_config.series
            and graph_config.series[0].x_column
            and graph_config.series[0].x_column in self.columns
        ):
            return graph_config.series[0].x_column
        for column in self.columns:
            if self.is_numeric_column(column):
                return column
        return self.columns[0] if self.columns else ""

    def default_y_columns(self, graph_config, x_column):
        columns = [
            series.y_column
            for series in graph_config.series
            if (
                series.y_column
                and series.y_column != x_column
                and series.y_column in self.columns
            )
        ]
        if columns:
            return columns
        for column in self.columns:
            if column != x_column and self.is_numeric_column(column):
                return [column]
        return [column for column in self.columns if column != x_column][:1]

    def is_numeric_column(self, column):
        if column not in self.dataframe.columns:
            return False
        values = self.dataframe[column]
        return values.notna().any() and values.map(lambda value: str(value).strip() != "").any() and values.astype(str).map(
            lambda value: to_optional_float(value) is not None
        ).any()

    def selected_y_columns(self):
        return [item.text() for item in self.y_column_list.selectedItems()]

    def float_text(self, value):
        return "" if value is None else str(value)

    def find_existing_series(self, y_column):
        for series in self.initial_series:
            if series.y_column == y_column:
                return series
        return None

    def combo(self, options, current_value):
        box = QComboBox()
        for label, value in options:
            box.addItem(label, value)
        index = box.findData(current_value)
        box.setCurrentIndex(max(index, 0))
        return box

    def column_combo(self, current_value):
        box = QComboBox()
        box.addItems(self.columns)
        if current_value in self.columns:
            box.setCurrentText(current_value)
        return box

    def line_check(self, checked):
        check = QCheckBox()
        check.setChecked(checked)
        return check

    def set_combo_data(self, combo, value):
        index = combo.findData(value)
        combo.setCurrentIndex(max(index, 0))

    def sync_linked_axis_details(self, axes):
        linked_axes = {
            "x_top": "x_bottom",
            "y_right": "y_left",
        }
        for axis_key, primary_key in linked_axes.items():
            axis = axes.get(axis_key)
            primary_axis = axes.get(primary_key)
            if axis is None or primary_axis is None or axis.linked_to != primary_key:
                continue
            visible = axis.visible
            show_label = axis.show_label
            show_major_tick_labels = axis.show_major_tick_labels
            axis_position_mode = axis.axis_position_mode
            axis_position_value = axis.axis_position_value
            tick_label_position_mode = axis.tick_label_position_mode
            axes[axis_key] = AxisConfig.from_dict(primary_axis.to_dict(), axis.position)
            axes[axis_key].position = axis.position
            axes[axis_key].linked_to = primary_key
            axes[axis_key].visible = visible
            axes[axis_key].show_label = show_label
            axes[axis_key].show_major_tick_labels = show_major_tick_labels
            axes[axis_key].axis_position_mode = axis_position_mode
            axes[axis_key].axis_position_value = axis_position_value
            axes[axis_key].tick_label_position_mode = tick_label_position_mode

    def graph_config(self):
        x_column = self.x_column_box.currentText()
        y_columns = self.selected_y_columns()
        if not x_column:
            raise ValueError("X列を選択してください。")
        if not y_columns:
            raise ValueError("Y列を1つ以上選択してください。")

        series_list = self.series_from_detail()
        if not series_list:
            raise ValueError("系列設定がありません。")

        self.save_current_axis_detail()
        axes = {
            key: AxisConfig.from_dict(axis.to_dict(), axis.position)
            for key, axis in self.axis_configs.items()
        }
        axes["x_bottom"].label = self.x_label_edit.text().strip() or x_column
        axes["y_left"].label = self.y_label_edit.text().strip() or ", ".join(y_columns)
        self.sync_linked_axis_details(axes)
        return GraphConfig(
            enabled=True,
            table_id=self.table_id,
            title=self.title_edit.text().strip(),
            title_visible=self.title_visible_check.isChecked(),
            default_plot_type=self.plot_type_box.currentData(),
            output_path=self.output_path,
            series=series_list,
            axes=axes,
            grid=GridConfig(enabled=self.grid_check.isChecked()),
            font=GraphFontConfig(
                japanese_font=self.japanese_font_edit.text().strip() or "MS Mincho",
                latin_font=self.latin_font_edit.text().strip() or "Times New Roman",
                font_size=to_optional_float(self.font_size_edit.text()) or 10.0,
            ),
            show_plot_frame=self.plot_frame_check.isChecked(),
            legend_location=self.legend_location_box.currentData(),
            fit_label_location=self.fit_label_location_box.currentData(),
            fit_label_background=self.fit_label_background_check.isChecked(),
        )

    def update_preview(self):
        try:
            config = self.graph_config()
            render_graph(self.dataframe, config, self.figure)
        except Exception as error:
            self.error_label.setText(str(error))
            self.figure.clear()
        else:
            self.error_label.setText("")
        self.canvas.draw_idle()

    def try_accept(self):
        try:
            self.accepted_config = self.graph_config()
        except ValueError as error:
            self.error_label.setText(str(error))
            return
        self.accept()

    def keyPressEvent(self, event):
        if event.key() in {Qt.Key_Return, Qt.Key_Enter}:
            self.update_preview()
            event.accept()
            return
        super().keyPressEvent(event)
