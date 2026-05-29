from dataclasses import dataclass, field
from typing import Any

from texsheet.graph.formatting import NumberFormatConfig, to_optional_float
from texsheet.graph.styles import PLOT_TYPES


@dataclass
class GraphFontConfig:
    japanese_font: str = "MS Mincho"
    latin_font: str = "Times New Roman"
    font_size: float = 10.0

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None):
        data = data or {}
        return cls(
            japanese_font=str(data.get("japanese_font", "MS Mincho")),
            latin_font=str(data.get("latin_font", "Times New Roman")),
            font_size=float(data.get("font_size", 10.0)),
        )

    def to_dict(self):
        return {
            "japanese_font": self.japanese_font,
            "latin_font": self.latin_font,
            "font_size": self.font_size,
        }


@dataclass
class FitConfig:
    enabled: bool = False
    fit_type: str = "linear"
    degree: int = 1
    force_intercept_zero: bool = False
    r2_space: str = "original"
    weight_mode: str = "none"
    weight_column: str = ""
    show_curve: bool = True
    show_equation: bool = True
    show_r2: bool = True
    x_min: float | None = None
    x_max: float | None = None
    outside_range_mode: str = "hidden"
    equation_number_format: NumberFormatConfig = field(default_factory=NumberFormatConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None):
        data = data or {}
        return cls(
            enabled=bool(data.get("enabled", False)),
            fit_type=str(data.get("fit_type", "linear")),
            degree=int(data.get("degree", data.get("polynomial_degree", 1))),
            force_intercept_zero=bool(data.get("force_intercept_zero", False)),
            r2_space=str(data.get("r2_space", "original")),
            weight_mode=str(data.get("weight_mode", "none")),
            weight_column=str(data.get("weight_column", "")),
            show_curve=bool(data.get("show_curve", True)),
            show_equation=bool(data.get("show_equation", True)),
            show_r2=bool(data.get("show_r2", True)),
            x_min=to_optional_float(data.get("x_min")),
            x_max=to_optional_float(data.get("x_max")),
            outside_range_mode=str(
                data.get("outside_range_mode", data.get("outside_range_style", "hidden"))
            ),
            equation_number_format=NumberFormatConfig.from_dict(
                data.get("equation_number_format")
            ),
        )

    def to_dict(self):
        return {
            "enabled": self.enabled,
            "fit_type": self.fit_type,
            "degree": self.degree,
            "force_intercept_zero": self.force_intercept_zero,
            "r2_space": self.r2_space,
            "weight_mode": self.weight_mode,
            "weight_column": self.weight_column,
            "show_curve": self.show_curve,
            "show_equation": self.show_equation,
            "show_r2": self.show_r2,
            "x_min": self.x_min,
            "x_max": self.x_max,
            "outside_range_mode": self.outside_range_mode,
            "equation_number_format": self.equation_number_format.to_dict(),
        }


@dataclass
class MarkerConfig:
    color: str = ""
    shape: str = "o"
    size: float = 6.0

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None, legacy=None):
        data = data or {}
        legacy = legacy or {}
        return cls(
            color=str(data.get("color", legacy.get("marker_color", ""))),
            shape=str(data.get("shape", legacy.get("marker", "o"))),
            size=float(data.get("size", legacy.get("marker_size", 6.0))),
        )

    def to_dict(self):
        return {
            "color": self.color,
            "shape": self.shape,
            "size": self.size,
        }


@dataclass
class LineConfig:
    visible: bool = False
    style: str = "-"
    width: float = 1.5

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None, legacy=None, plot_type="scatter"):
        data = data or {}
        legacy = legacy or {}
        default_visible = plot_type in {"line", "scatter_line"}
        return cls(
            visible=bool(data.get("visible", legacy.get("show_line", default_visible))),
            style=str(data.get("style", legacy.get("line_style", "-"))),
            width=float(data.get("width", legacy.get("line_width", 1.5))),
        )

    def to_dict(self):
        return {
            "visible": self.visible,
            "style": self.style,
            "width": self.width,
        }


@dataclass
class SeriesConfig:
    name: str = ""
    x_column: str = ""
    y_column: str = ""
    plot_type: str = "scatter"
    marker_config: MarkerConfig = field(default_factory=MarkerConfig)
    line_config: LineConfig = field(default_factory=LineConfig)
    fit_config: FitConfig = field(default_factory=FitConfig)
    x_axis: str = "x_bottom"
    y_axis: str = "y_left"

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None):
        data = data or {}
        plot_type = str(data.get("plot_type", "scatter"))
        if plot_type not in PLOT_TYPES:
            plot_type = "scatter"
        return cls(
            name=str(data.get("name", data.get("y_column", ""))),
            x_column=str(data.get("x_column", "")),
            y_column=str(data.get("y_column", "")),
            plot_type=plot_type,
            marker_config=MarkerConfig.from_dict(data.get("marker_config"), data),
            line_config=LineConfig.from_dict(data.get("line_config"), data, plot_type),
            fit_config=FitConfig.from_dict(data.get("fit_config", data.get("fit"))),
            x_axis=str(data.get("x_axis", "x_bottom")),
            y_axis=str(data.get("y_axis", "y_left")),
        )

    @property
    def marker(self):
        return self.marker_config.shape

    @property
    def marker_color(self):
        return self.marker_config.color

    @property
    def marker_size(self):
        return self.marker_config.size

    @property
    def show_line(self):
        return self.line_config.visible

    @property
    def line_style(self):
        return self.line_config.style

    @property
    def line_width(self):
        return self.line_config.width

    @property
    def fit(self):
        return self.fit_config

    def to_dict(self):
        return {
            "name": self.name or self.y_column,
            "x_column": self.x_column,
            "y_column": self.y_column,
            "plot_type": self.plot_type,
            "marker_config": self.marker_config.to_dict(),
            "line_config": self.line_config.to_dict(),
            "fit_config": self.fit_config.to_dict(),
            "x_axis": self.x_axis,
            "y_axis": self.y_axis,
        }


@dataclass
class AxisConfig:
    label: str = ""
    min_value: float | None = None
    max_value: float | None = None
    major_tick: float | None = None
    minor_tick: float | None = None
    scale_type: str = "linear"
    tick_direction: str = "in"
    show_major_ticks: bool = True
    show_minor_ticks: bool = False
    show_major_tick_labels: bool = True
    show_min_max_tick_labels: bool = False
    show_minor_tick_labels: bool = False
    show_label: bool = True
    tick_label_format: NumberFormatConfig = field(
        default_factory=lambda: NumberFormatConfig("significant_figures", 4, False)
    )
    linked_to: str | None = None
    position: str = "bottom"
    visible: bool = True
    axis_position_mode: str = "default"
    axis_position_value: float | None = None
    tick_label_position_mode: str = "axis"

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None, position: str, default_label: str = ""):
        data = data or {}
        scale_type = str(data.get("scale_type", "log" if data.get("log_scale", False) else "linear"))
        if scale_type not in {"linear", "log"}:
            scale_type = "linear"
        axis_position_mode = str(data.get("axis_position_mode", "default"))
        if axis_position_mode not in {"default", "zero", "value"}:
            axis_position_mode = "default"
        tick_label_position_mode = str(data.get("tick_label_position_mode", "axis"))
        if tick_label_position_mode not in {"axis", "frame"}:
            tick_label_position_mode = "axis"
        default_major_labels = position in {"bottom", "left"}
        default_show_label = position in {"bottom", "left"}
        return cls(
            label=str(data.get("label", default_label)),
            min_value=to_optional_float(data.get("min_value")),
            max_value=to_optional_float(data.get("max_value")),
            major_tick=to_optional_float(data.get("major_tick")),
            minor_tick=to_optional_float(data.get("minor_tick")),
            scale_type=scale_type,
            tick_direction=str(data.get("tick_direction", "in")),
            show_major_ticks=bool(data.get("show_major_ticks", True)),
            show_minor_ticks=bool(data.get("show_minor_ticks", False)),
            show_major_tick_labels=bool(data.get("show_major_tick_labels", default_major_labels)),
            show_min_max_tick_labels=bool(data.get("show_min_max_tick_labels", False)),
            show_minor_tick_labels=bool(data.get("show_minor_tick_labels", False)),
            show_label=bool(data.get("show_label", default_show_label)),
            tick_label_format=NumberFormatConfig.from_dict(data.get("tick_label_format")),
            linked_to=data.get("linked_to"),
            position=str(data.get("position", position)),
            visible=bool(data.get("visible", True)),
            axis_position_mode=axis_position_mode,
            axis_position_value=to_optional_float(data.get("axis_position_value")),
            tick_label_position_mode=tick_label_position_mode,
        )

    @property
    def log_scale(self):
        return self.scale_type == "log"

    def to_dict(self):
        return {
            "label": self.label,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "major_tick": self.major_tick,
            "minor_tick": self.minor_tick,
            "scale_type": self.scale_type,
            "tick_direction": self.tick_direction,
            "show_major_ticks": self.show_major_ticks,
            "show_minor_ticks": self.show_minor_ticks,
            "show_major_tick_labels": self.show_major_tick_labels,
            "show_min_max_tick_labels": self.show_min_max_tick_labels,
            "show_minor_tick_labels": self.show_minor_tick_labels,
            "show_label": self.show_label,
            "tick_label_format": self.tick_label_format.to_dict(),
            "linked_to": self.linked_to,
            "position": self.position,
            "visible": self.visible,
            "axis_position_mode": self.axis_position_mode,
            "axis_position_value": self.axis_position_value,
            "tick_label_position_mode": self.tick_label_position_mode,
        }


@dataclass
class GridConfig:
    enabled: bool = True
    major: bool = True
    minor: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None):
        data = data or {}
        return cls(
            enabled=bool(data.get("enabled", True)),
            major=bool(data.get("major", True)),
            minor=bool(data.get("minor", False)),
        )

    def to_dict(self):
        return {
            "enabled": self.enabled,
            "major": self.major,
            "minor": self.minor,
        }


@dataclass
class GraphConfig:
    enabled: bool = False
    table_id: str = ""
    title: str = ""
    title_visible: bool = False
    default_plot_type: str = "scatter"
    output_path: str = "figures/result_graph.pdf"
    series: list[SeriesConfig] = field(default_factory=list)
    axes: dict[str, AxisConfig] = field(default_factory=dict)
    grid: GridConfig = field(default_factory=GridConfig)
    font: GraphFontConfig = field(default_factory=GraphFontConfig)
    show_plot_frame: bool = False
    legend_location: str = "best"
    fit_label_location: str = "auto"
    fit_label_background: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None, columns=None, table_id: str = ""):
        data = data or {}
        columns = list(columns) if columns is not None else []

        if "series" in data:
            series = [SeriesConfig.from_dict(item) for item in data.get("series", [])]
        else:
            series = legacy_series(data)

        if columns:
            series = [
                item
                for item in series
                if item.x_column in columns and item.y_column in columns
            ]

        if not series and len(columns) >= 2:
            series = [
                SeriesConfig(
                    name=columns[1],
                    x_column=columns[0],
                    y_column=columns[1],
                    plot_type="scatter",
                    line_config=LineConfig(visible=False),
                    x_axis="x_bottom",
                    y_axis="y_left",
                )
            ]

        axes_data = data.get("axes", {})
        x_top_data = axes_data.get("x_top", {})
        y_right_data = axes_data.get("y_right", {})
        x_label = data.get("xlabel", series[0].x_column if series else "")
        y_label = data.get("ylabel", series[0].y_column if series else "")
        axes = {
            "x_bottom": AxisConfig.from_dict(axes_data.get("x_bottom"), "bottom", x_label),
            "x_top": AxisConfig.from_dict(x_top_data, "top", x_label),
            "y_left": AxisConfig.from_dict(axes_data.get("y_left"), "left", y_label),
            "y_right": AxisConfig.from_dict(y_right_data, "right", y_label),
        }
        axes["x_top"].visible = bool(x_top_data.get("visible", False))
        axes["y_right"].visible = bool(y_right_data.get("visible", False))
        if "linked_to" not in x_top_data:
            axes["x_top"].linked_to = "x_bottom"
        if "linked_to" not in y_right_data:
            axes["y_right"].linked_to = "y_left"
        if "x_top" not in axes_data:
            axes["x_top"].show_major_tick_labels = False
        if "y_right" not in axes_data:
            axes["y_right"].show_major_tick_labels = False

        legend_location = str(data.get("legend_location", "best"))
        if legend_location not in {
            "best",
            "upper left",
            "upper right",
            "lower left",
            "lower right",
            "outside right",
        }:
            legend_location = "best"
        fit_label_location = str(data.get("fit_label_location", "auto"))
        if fit_label_location not in {
            "auto",
            "upper left",
            "upper right",
            "lower left",
            "lower right",
        }:
            fit_label_location = "auto"

        return cls(
            enabled=bool(data.get("enabled", False)),
            table_id=str(data.get("table_id", table_id)),
            title=str(data.get("title", "")),
            title_visible=bool(data.get("title_visible", False)),
            default_plot_type=str(data.get("default_plot_type", data.get("plot_type", "scatter"))),
            output_path=str(
                data.get(
                    "output_path",
                    data.get("figure_pdf", default_graph_output_path(table_id)),
                )
            ),
            series=series,
            axes=axes,
            grid=GridConfig.from_dict(data.get("grid")),
            font=GraphFontConfig.from_dict(data.get("font")),
            show_plot_frame=bool(data.get("show_plot_frame", False)),
            legend_location=legend_location,
            fit_label_location=fit_label_location,
            fit_label_background=bool(data.get("fit_label_background", True)),
        )

    def to_dict(self):
        return {
            "enabled": self.enabled,
            "table_id": self.table_id,
            "title": self.title,
            "title_visible": self.title_visible,
            "default_plot_type": self.default_plot_type,
            "output_path": self.output_path,
            "series": [series.to_dict() for series in self.series],
            "axes": {name: axis.to_dict() for name, axis in self.axes.items()},
            "grid": self.grid.to_dict(),
            "font": self.font.to_dict(),
            "show_plot_frame": self.show_plot_frame,
            "legend_location": self.legend_location,
            "fit_label_location": self.fit_label_location,
            "fit_label_background": self.fit_label_background,
        }


def default_graph_output_path(table_id=""):
    if table_id:
        return f"figures/{table_id}_graph.pdf"
    return "figures/result_graph.pdf"


def legacy_series(data):
    x_column = data.get("x_column", "")
    y_column = data.get("y_column", "")
    if not x_column or not y_column:
        return []
    return [
        SeriesConfig(
            name=str(y_column),
            x_column=str(x_column),
            y_column=str(y_column),
            plot_type=str(data.get("plot_type", "line")),
            line_config=LineConfig(visible=str(data.get("plot_type", "line")) == "line"),
            x_axis="x_bottom",
            y_axis="y_left",
        )
    ]


def graph_config_from_dict(data, columns=None, table_id=""):
    return GraphConfig.from_dict(data, columns, table_id)
