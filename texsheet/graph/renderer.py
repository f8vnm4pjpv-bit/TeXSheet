import numpy as np
import pandas as pd
from matplotlib import rc_context
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter, MultipleLocator, NullFormatter

from texsheet.graph.config import AxisConfig, graph_config_from_dict
from texsheet.graph.fitting import fit_series, format_fit_equation
from texsheet.graph.formatting import format_number
from texsheet.paths import project_path


def graph_font_rc(graph_config):
    font_config = graph_config.font
    japanese_fonts = [
        font_config.japanese_font,
        "Yu Gothic",
        "MS Gothic",
        "Meiryo",
        "MS Mincho",
        "Noto Sans JP",
        font_config.latin_font,
        "DejaVu Sans",
    ]
    return {
        "font.family": "sans-serif",
        "font.sans-serif": japanese_fonts,
        "font.size": font_config.font_size,
        "mathtext.fontset": "custom",
        "mathtext.rm": font_config.latin_font,
        "mathtext.it": f"{font_config.latin_font}:italic",
        "mathtext.bf": f"{font_config.latin_font}:bold",
    }


def has_japanese_text(value):
    return any(
        "\u3040" <= character <= "\u30ff"
        or "\u3400" <= character <= "\u9fff"
        for character in str(value)
    )


def text_font_families(value, font_config):
    japanese_fonts = [
        font_config.japanese_font,
        "Yu Gothic",
        "MS Gothic",
        "Meiryo",
        "MS Mincho",
        "Noto Sans JP",
    ]
    latin_fonts = [font_config.latin_font, "Times New Roman", "DejaVu Sans"]
    if has_japanese_text(value):
        return japanese_fonts + latin_fonts
    return latin_fonts + japanese_fonts


def text_font_properties(value, font_config, font_size=None):
    return FontProperties(
        family=text_font_families(value, font_config),
        size=font_size if font_size is not None else font_config.font_size,
    )


def apply_text_font(text, font_config, font_size=None):
    text.set_fontproperties(
        text_font_properties(text.get_text(), font_config, font_size)
    )
    text.set_fontsize(font_size if font_size is not None else font_config.font_size)


def apply_axis_text_fonts(axis, axis_config, font_config):
    if axis_config.position in {"bottom", "top"}:
        apply_text_font(axis.xaxis.label, font_config)
        tick_labels = axis.get_xticklabels() + axis.get_xticklabels(minor=True)
    else:
        apply_text_font(axis.yaxis.label, font_config)
        tick_labels = axis.get_yticklabels() + axis.get_yticklabels(minor=True)
    for label in tick_labels:
        apply_text_font(label, font_config)


def validate_columns(dataframe, graph_config):
    required_columns = []
    for series in graph_config.series:
        required_columns.extend([series.x_column, series.y_column])
        fit = series.fit_config
        if fit.weight_mode in {"y_sigma", "custom_weight"} and fit.weight_column:
            required_columns.append(fit.weight_column)
    missing_columns = [column for column in required_columns if column not in dataframe.columns]
    if missing_columns:
        available_columns = ", ".join(dataframe.columns)
        missing_text = ", ".join(dict.fromkeys(missing_columns))
        raise ValueError(
            f"CSVに指定された列が存在しない: {missing_text} "
            f"(利用可能な列: {available_columns})"
        )


def value_summary(values):
    finite_values = values[np.isfinite(values)]
    if len(finite_values) == 0:
        return "min/max=なし"
    return f"min={finite_values.min():.6g}, max={finite_values.max():.6g}"


def series_data_diagnostics(raw_data, numeric_data, filtered_data, series):
    x_values = numeric_data[series.x_column].to_numpy(dtype=float)
    y_values = numeric_data[series.y_column].to_numpy(dtype=float)
    raw_x = raw_data[series.x_column]
    raw_y = raw_data[series.y_column]
    x_nan = int(numeric_data[series.x_column].isna().sum())
    y_nan = int(numeric_data[series.y_column].isna().sum())
    x_inf = int(np.isinf(x_values).sum())
    y_inf = int(np.isinf(y_values).sum())
    return (
        f"{series.name or series.y_column}: "
        f"x={series.x_column} "
        f"{value_summary(x_values)} nan={x_nan} inf={x_inf}; "
        f"y={series.y_column} "
        f"{value_summary(y_values)} nan={y_nan} inf={y_inf}; "
        f"valid={len(filtered_data)}/{len(raw_data)}"
    )


def numeric_pair(dataframe, series, graph_config=None, warnings=None):
    columns = [series.x_column, series.y_column]
    fit = series.fit_config
    if fit.weight_mode in {"y_sigma", "custom_weight"} and fit.weight_column:
        columns.append(fit.weight_column)
    data = dataframe[list(dict.fromkeys(columns))].copy()
    data[series.x_column] = pd.to_numeric(data[series.x_column], errors="coerce")
    data[series.y_column] = pd.to_numeric(data[series.y_column], errors="coerce")
    if fit.weight_column in data.columns:
        data[fit.weight_column] = pd.to_numeric(data[fit.weight_column], errors="coerce")
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.dropna()
    if graph_config is None:
        return data

    x_axis = graph_config.axes.get(series.x_axis, graph_config.axes["x_bottom"])
    y_axis = graph_config.axes.get(series.y_axis, graph_config.axes["y_left"])
    mask = pd.Series(True, index=data.index)
    removed = 0
    if x_axis.scale_type == "log":
        invalid = data[series.x_column] <= 0
        removed += int(invalid.sum())
        mask &= ~invalid
    if y_axis.scale_type == "log":
        invalid = data[series.y_column] <= 0
        removed += int(invalid.sum())
        mask &= ~invalid
    if removed and warnings is not None:
        warnings.append(f"{series.name or series.y_column}: 対数軸のため0以下の値を除外しました。")
    filtered_data = data[mask]
    if len(filtered_data) == 0 and warnings is not None:
        warnings.append(
            f"{series.name or series.y_column}: 描画可能な数値データがありません。"
        )
    return filtered_data


def tick_params_for_axis(axis_config):
    return {
        "in": "in",
        "out": "out",
        "inout": "inout",
    }.get(axis_config.tick_direction, "in")


def apply_axis_position(axis, axis_config):
    if axis_config.axis_position_mode == "default":
        return False
    coordinate = 0.0
    if axis_config.axis_position_mode == "value":
        if axis_config.axis_position_value is None:
            return False
        coordinate = axis_config.axis_position_value

    spine = axis.spines.get(axis_config.position)
    if spine is None:
        return False
    spine.set_position(("data", coordinate))
    return True


def keep_axis_tick_labels_visible(axis, axis_config):
    if axis_config.position in {"bottom", "top"}:
        ticks = axis.xaxis.get_major_ticks() + axis.xaxis.get_minor_ticks()
        labels = [tick.label1 if axis_config.position == "bottom" else tick.label2 for tick in ticks]
    else:
        ticks = axis.yaxis.get_major_ticks() + axis.yaxis.get_minor_ticks()
        labels = [tick.label1 if axis_config.position == "left" else tick.label2 for tick in ticks]
    for label in labels:
        label.set_clip_on(False)


def apply_tick_label_position(axis, axis_config):
    if axis_config.tick_label_position_mode != "frame":
        return
    if axis_config.position == "bottom":
        axis.xaxis.set_ticks_position("bottom")
        axis.tick_params(axis="x", labelbottom=axis_config.show_major_tick_labels, labeltop=False)
    elif axis_config.position == "top":
        axis.xaxis.set_ticks_position("top")
        axis.tick_params(axis="x", labelbottom=False, labeltop=axis_config.show_major_tick_labels)
    elif axis_config.position == "left":
        axis.yaxis.set_ticks_position("left")
        axis.tick_params(axis="y", labelleft=axis_config.show_major_tick_labels, labelright=False)
    elif axis_config.position == "right":
        axis.yaxis.set_ticks_position("right")
        axis.tick_params(axis="y", labelleft=False, labelright=axis_config.show_major_tick_labels)


def with_unique_tick(ticks, value, tolerance):
    if any(np.isclose(tick, value, rtol=0.0, atol=tolerance) for tick in ticks):
        return ticks
    return ticks + [value]


def add_min_max_major_ticks(axis, axis_config):
    if not axis_config.show_min_max_tick_labels:
        return
    if axis_config.position in {"bottom", "top"}:
        lower, upper = axis.get_xlim()
        ticks = list(axis.get_xticks())
    else:
        lower, upper = axis.get_ylim()
        ticks = list(axis.get_yticks())

    low = min(lower, upper)
    high = max(lower, upper)
    tolerance = max(abs(high - low), 1.0) * 1e-9
    ticks = [
        tick for tick in ticks
        if np.isfinite(tick) and low - tolerance <= tick <= high + tolerance
    ]
    ticks = with_unique_tick(ticks, lower, tolerance)
    ticks = with_unique_tick(ticks, upper, tolerance)
    ticks = sorted(ticks)

    if axis_config.position in {"bottom", "top"}:
        axis.set_xticks(ticks)
        axis.set_xlim(lower, upper)
    else:
        axis.set_yticks(ticks)
        axis.set_ylim(lower, upper)


def apply_axis_settings(axis, axis_config, font_config=None):
    if axis_config.show_label and axis_config.label:
        if axis_config.position in {"bottom", "top"}:
            axis.set_xlabel(axis_config.label)
        else:
            axis.set_ylabel(axis_config.label)
    else:
        if axis_config.position in {"bottom", "top"}:
            axis.set_xlabel("")
        else:
            axis.set_ylabel("")

    if axis_config.min_value is not None or axis_config.max_value is not None:
        if axis_config.position in {"bottom", "top"}:
            axis.set_xlim(left=axis_config.min_value, right=axis_config.max_value)
        else:
            axis.set_ylim(bottom=axis_config.min_value, top=axis_config.max_value)

    if axis_config.scale_type == "log":
        if axis_config.position in {"bottom", "top"}:
            axis.set_xscale("log")
        else:
            axis.set_yscale("log")

    axis_position_changed = apply_axis_position(axis, axis_config)

    formatter = FuncFormatter(
        lambda value, _: format_number(value, axis_config.tick_label_format)
    )
    if axis_config.position in {"bottom", "top"}:
        axis.xaxis.set_major_formatter(formatter)
    else:
        axis.yaxis.set_major_formatter(formatter)

    axis_name = "x" if axis_config.position in {"bottom", "top"} else "y"
    direction = tick_params_for_axis(axis_config)
    axis.tick_params(
        axis=axis_name,
        which="major",
        direction=direction,
        bottom=axis_config.position == "bottom" and axis_config.show_major_ticks,
        top=axis_config.position == "top" and axis_config.show_major_ticks,
        left=axis_config.position == "left" and axis_config.show_major_ticks,
        right=axis_config.position == "right" and axis_config.show_major_ticks,
        labelbottom=axis_config.position == "bottom" and axis_config.show_major_tick_labels,
        labeltop=axis_config.position == "top" and axis_config.show_major_tick_labels,
        labelleft=axis_config.position == "left" and axis_config.show_major_tick_labels,
        labelright=axis_config.position == "right" and axis_config.show_major_tick_labels,
    )

    if axis_config.major_tick and axis_config.scale_type == "linear":
        locator = MultipleLocator(axis_config.major_tick)
        if axis_config.position in {"bottom", "top"}:
            axis.xaxis.set_major_locator(locator)
        else:
            axis.yaxis.set_major_locator(locator)
    add_min_max_major_ticks(axis, axis_config)
    if axis_config.minor_tick and axis_config.scale_type == "linear":
        locator = MultipleLocator(axis_config.minor_tick)
        if axis_config.position in {"bottom", "top"}:
            axis.xaxis.set_minor_locator(locator)
        else:
            axis.yaxis.set_minor_locator(locator)

    axis.tick_params(
        axis=axis_name,
        which="minor",
        direction=direction,
        bottom=axis_config.position == "bottom" and axis_config.show_minor_ticks,
        top=axis_config.position == "top" and axis_config.show_minor_ticks,
        left=axis_config.position == "left" and axis_config.show_minor_ticks,
        right=axis_config.position == "right" and axis_config.show_minor_ticks,
        labelbottom=axis_config.position == "bottom" and axis_config.show_minor_tick_labels,
        labeltop=axis_config.position == "top" and axis_config.show_minor_tick_labels,
        labelleft=axis_config.position == "left" and axis_config.show_minor_tick_labels,
        labelright=axis_config.position == "right" and axis_config.show_minor_tick_labels,
    )
    if not axis_config.show_minor_tick_labels:
        if axis_config.position in {"bottom", "top"}:
            axis.xaxis.set_minor_formatter(NullFormatter())
        else:
            axis.yaxis.set_minor_formatter(NullFormatter())
    else:
        minor_formatter = FuncFormatter(
            lambda value, _: format_number(value, axis_config.tick_label_format)
        )
        if axis_config.position in {"bottom", "top"}:
            axis.xaxis.set_minor_formatter(minor_formatter)
        else:
            axis.yaxis.set_minor_formatter(minor_formatter)

    if axis_position_changed:
        keep_axis_tick_labels_visible(axis, axis_config)
    apply_tick_label_position(axis, axis_config)

    if not axis_config.visible:
        if axis_config.position in {"bottom", "top"}:
            axis.tick_params(
                axis="x",
                labelbottom=False,
                labeltop=False,
                bottom=False,
                top=False,
            )
            axis.set_xlabel("")
        else:
            axis.tick_params(
                axis="y",
                labelleft=False,
                labelright=False,
                left=False,
                right=False,
            )
            axis.set_ylabel("")

    if font_config is not None:
        apply_axis_text_fonts(axis, axis_config, font_config)


def render_plot_frame(axis):
    frame = Rectangle(
        (0, 0),
        1,
        1,
        transform=axis.transAxes,
        fill=False,
        edgecolor="black",
        linewidth=1.0,
        clip_on=False,
        zorder=10,
    )
    axis.add_patch(frame)


def fit_curve_x_values(start, end, count, log_scale=False, positive_only=False):
    if start >= end:
        return np.array([])
    if log_scale:
        start = max(start, np.nextafter(0.0, 1.0))
        end = max(end, np.nextafter(start, np.inf))
        values = np.geomspace(start, end, count)
    else:
        values = np.linspace(start, end, count)
    if positive_only:
        values = values[values > 0]
    return values


def plot_fit_curve_segment(axis, predict, x_values, color, linestyle, line_width):
    if len(x_values) == 0:
        return
    axis.plot(
        x_values,
        predict(x_values),
        color=color,
        linestyle=linestyle,
        linewidth=line_width,
    )


def fit_axis_range(axis, series, graph_config, fit):
    x_axis_config = graph_config.axes.get(series.x_axis, graph_config.axes["x_bottom"])
    axis_min, axis_max = axis.get_xlim()
    if x_axis_config.min_value is not None:
        axis_min = x_axis_config.min_value
    if x_axis_config.max_value is not None:
        axis_max = x_axis_config.max_value
    display_min = fit.x_min if fit.x_min is not None else axis_min
    display_max = fit.x_max if fit.x_max is not None else axis_max
    if display_min > display_max:
        display_min, display_max = display_max, display_min
    return display_min, display_max, x_axis_config


def plot_fit_curve(axis, series, fit_result, graph_config):
    fit = series.fit_config
    if fit_result is None or not fit.show_curve:
        return None
    data_x_min = fit_result["data_x_min"]
    data_x_max = fit_result["data_x_max"]
    display_min, display_max, x_axis_config = fit_axis_range(axis, series, graph_config, fit)
    if display_min >= display_max:
        return None

    color = series.marker_color or None
    predict = fit_result["predict"]
    positive_only = fit_result["fit_type"] in {"power", "logarithmic"}
    log_scale = x_axis_config.scale_type == "log"
    inner_min = max(display_min, data_x_min)
    inner_max = min(display_max, data_x_max)
    inner_values = fit_curve_x_values(inner_min, inner_max, 200, log_scale, positive_only)
    if len(inner_values) == 0:
        return None
    plot_fit_curve_segment(axis, predict, inner_values, color, "-", series.line_width)

    if fit.outside_range_mode != "hidden":
        outside_style = "--" if fit.outside_range_mode == "dashed" else "-"
        left_values = fit_curve_x_values(
            display_min,
            min(display_max, data_x_min),
            80,
            log_scale,
            positive_only,
        )
        right_values = fit_curve_x_values(
            max(display_min, data_x_max),
            display_max,
            80,
            log_scale,
            positive_only,
        )
        plot_fit_curve_segment(axis, predict, left_values, color, outside_style, series.line_width)
        plot_fit_curve_segment(axis, predict, right_values, color, outside_style, series.line_width)

    label_parts = []
    if fit.show_equation:
        label_parts.append(format_fit_equation(fit_result, fit.equation_number_format))
    if fit.show_r2:
        label_parts.append(f"R² = {format_number(fit_result['r2'], fit.equation_number_format)}")
    if not label_parts:
        return None
    return ", ".join(label_parts)


def plot_series(axis, dataframe, series, graph_config, warnings, fit_labels):
    data = numeric_pair(dataframe, series, graph_config, warnings)
    if data.empty:
        return

    x_values = data[series.x_column]
    y_values = data[series.y_column]
    label = series.name or series.y_column
    color = series.marker_color or None

    if series.plot_type == "bar":
        axis.bar(x_values, y_values, label=label, color=color)
    elif series.plot_type in {"line", "scatter_line"} or series.show_line:
        axis.plot(
            x_values,
            y_values,
            label=label,
            marker=series.marker,
            markersize=series.marker_size,
            linestyle=series.line_style if series.show_line else "None",
            linewidth=series.line_width,
            color=color,
        )
    else:
        axis.scatter(
            x_values,
            y_values,
            label=label,
            marker=series.marker,
            s=series.marker_size ** 2,
            color=color,
        )
    fit_result = fit_series(data, series)
    fit_label = plot_fit_curve(axis, series, fit_result, graph_config)
    if fit_label:
        fit_labels.append((fit_label, series.marker, color))


def fit_label_anchor(location):
    return {
        "upper left": (0.02, 0.98, "left", "top"),
        "upper right": (0.98, 0.98, "right", "top"),
        "lower left": (0.02, 0.02, "left", "bottom"),
        "lower right": (0.98, 0.02, "right", "bottom"),
    }.get(location, (0.98, 0.98, "right", "top"))


def resolve_fit_label_location(graph_config):
    if graph_config.fit_label_location != "auto":
        return graph_config.fit_label_location
    return {
        "upper left": "upper right",
        "upper right": "upper left",
        "lower left": "lower right",
        "lower right": "lower left",
    }.get(graph_config.legend_location, "upper right")


def render_fit_labels(axis, fit_labels, graph_config):
    if not fit_labels:
        return
    text = "\n".join(label for label, _marker, _color in fit_labels)
    x, y, horizontal_alignment, vertical_alignment = fit_label_anchor(
        resolve_fit_label_location(graph_config)
    )
    bbox = None
    if graph_config.fit_label_background:
        bbox = {
            "facecolor": "white",
            "alpha": 0.75,
            "edgecolor": "none",
            "boxstyle": "round,pad=0.25",
        }
    axis.text(
        x,
        y,
        text,
        ha=horizontal_alignment,
        va=vertical_alignment,
        transform=axis.transAxes,
        fontproperties=text_font_properties(text, graph_config.font, 9),
        bbox=bbox,
        zorder=20,
    )


def render_legend(axis, graph_config):
    if not (len(graph_config.series) > 1 or any(series.name for series in graph_config.series)):
        return None
    handles, labels = axis.get_legend_handles_labels()
    visible_items = [
        (handle, label)
        for handle, label in zip(handles, labels)
        if label and not str(label).startswith("_")
    ]
    if not visible_items:
        return None
    handles, labels = zip(*visible_items)
    if graph_config.legend_location == "outside right":
        legend = axis.legend(
            handles,
            labels,
            loc="upper left",
            bbox_to_anchor=(1.02, 1.0),
            borderaxespad=0.0,
            prop=text_font_properties("", graph_config.font),
        )
    else:
        legend = axis.legend(
            handles,
            labels,
            loc=graph_config.legend_location,
            prop=text_font_properties("", graph_config.font),
        )
    for text in legend.get_texts():
        apply_text_font(text, graph_config.font)
    return legend


def render_warnings(axis, warnings, font_config):
    if not warnings:
        return
    unique_warnings = list(dict.fromkeys(warnings))
    axis.text(
        0.02,
        0.02,
        "\n".join(unique_warnings),
        ha="left",
        va="bottom",
        transform=axis.transAxes,
        fontproperties=text_font_properties("\n".join(unique_warnings), font_config, 8),
        color="tab:red",
        bbox={"facecolor": "white", "alpha": 0.75, "edgecolor": "none"},
    )


def configure_secondary_axes(axis, graph_config):
    x_top = graph_config.axes.get("x_top")
    y_right = graph_config.axes.get("y_right")
    if x_top and x_top.visible:
        top_axis = axis.secondary_xaxis("top")
        linked = x_top.linked_to == "x_bottom"
        axis_config = x_top
        if linked:
            axis_config = AxisConfig.from_dict(graph_config.axes["x_bottom"].to_dict(), "top")
            axis_config.position = "top"
            axis_config.visible = x_top.visible
            axis_config.show_label = x_top.show_label
            axis_config.show_major_tick_labels = x_top.show_major_tick_labels
            axis_config.axis_position_mode = x_top.axis_position_mode
            axis_config.axis_position_value = x_top.axis_position_value
            axis_config.tick_label_position_mode = x_top.tick_label_position_mode
        apply_axis_settings(top_axis, axis_config, graph_config.font)
    if y_right and y_right.visible:
        right_axis = axis.secondary_yaxis("right")
        linked = y_right.linked_to == "y_left"
        axis_config = y_right
        if linked:
            axis_config = AxisConfig.from_dict(graph_config.axes["y_left"].to_dict(), "right")
            axis_config.position = "right"
            axis_config.visible = y_right.visible
            axis_config.show_label = y_right.show_label
            axis_config.show_major_tick_labels = y_right.show_major_tick_labels
            axis_config.axis_position_mode = y_right.axis_position_mode
            axis_config.axis_position_value = y_right.axis_position_value
            axis_config.tick_label_position_mode = y_right.tick_label_position_mode
        apply_axis_settings(right_axis, axis_config, graph_config.font)


def render_graph(dataframe, graph_config, figure=None):
    with rc_context(graph_font_rc(graph_config)):
        return render_graph_body(dataframe, graph_config, figure)


def render_graph_body(dataframe, graph_config, figure=None):
    validate_columns(dataframe, graph_config)
    if figure is None:
        figure = Figure(figsize=(6.4, 4.2), dpi=120)
    figure.clear()
    axis = figure.add_subplot(111)
    warnings = []
    fit_labels = []
    for series in graph_config.series:
        plot_series(axis, dataframe, series, graph_config, warnings, fit_labels)

    if graph_config.title_visible and graph_config.title:
        axis.text(
            0.5,
            -0.22,
            graph_config.title,
            ha="center",
            va="top",
            transform=axis.transAxes,
            fontproperties=text_font_properties(graph_config.title, graph_config.font),
        )

    apply_axis_settings(axis, graph_config.axes["x_bottom"], graph_config.font)
    apply_axis_settings(axis, graph_config.axes["y_left"], graph_config.font)
    configure_secondary_axes(axis, graph_config)
    render_legend(axis, graph_config)
    render_fit_labels(axis, fit_labels, graph_config)
    render_warnings(axis, warnings, graph_config.font)

    if graph_config.grid.enabled:
        axis.grid(True, which="major" if graph_config.grid.major else "both", alpha=0.35)

    if graph_config.show_plot_frame:
        render_plot_frame(axis)

    figure.tight_layout()
    if graph_config.title_visible and graph_config.title:
        figure.subplots_adjust(bottom=0.22)
    if graph_config.legend_location == "outside right":
        figure.subplots_adjust(right=0.78)
    return figure


def save_graph(dataframe, graph_config):
    output_path = project_path(graph_config.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure = render_graph(dataframe, graph_config)
    with rc_context(graph_font_rc(graph_config)):
        figure.savefig(output_path)
    return output_path


def save_line_graph(dataframe, config):
    graph_config = graph_config_from_dict(
        config.get("graph", {}),
        columns=dataframe.columns,
    )
    return save_graph(dataframe, graph_config)
