import numpy as np

from texsheet.graph.formatting import format_number


def fit_series(data, series):
    fit = series.fit_config
    if not fit.enabled or len(data) < 2:
        return None
    x_values = data[series.x_column].to_numpy(dtype=float)
    y_values = data[series.y_column].to_numpy(dtype=float)
    weights = fit_weights(data, series)
    fit_type = fit.fit_type
    r2_values = None

    if fit_type == "linear" and fit.force_intercept_zero:
        fit_weights_values = weights if weights is not None else np.ones_like(x_values)
        denominator = np.sum(fit_weights_values * x_values ** 2)
        if denominator == 0:
            return None
        slope = float(np.sum(fit_weights_values * x_values * y_values) / denominator)
        predict = lambda x: slope * x
        predicted = predict(x_values)
        result = {"fit_type": fit_type, "parameters": {"a": slope, "b": 0.0}, "predict": predict}
    elif fit_type == "linear":
        coefficients = weighted_polyfit(x_values, y_values, 1, weights)
        polynomial = np.poly1d(coefficients)
        predicted = polynomial(x_values)
        result = {
            "fit_type": fit_type,
            "coefficients": coefficients,
            "parameters": {"a": float(coefficients[0]), "b": float(coefficients[1])},
            "predict": polynomial,
        }
    elif fit_type == "polynomial":
        degree = max(1, int(fit.degree))
        if len(x_values) <= degree:
            return None
        coefficients = weighted_polyfit(x_values, y_values, degree, weights)
        polynomial = np.poly1d(coefficients)
        predicted = polynomial(x_values)
        result = {
            "fit_type": fit_type,
            "coefficients": coefficients,
            "predict": polynomial,
        }
    elif fit_type == "power":
        mask = (x_values > 0) & (y_values > 0)
        if int(mask.sum()) < 2:
            return None
        log_x = np.log(x_values[mask])
        log_y = np.log(y_values[mask])
        transformed_weights = weights[mask] if weights is not None else None
        slope, intercept = weighted_polyfit(log_x, log_y, 1, transformed_weights)
        a = float(np.exp(intercept))
        b = float(slope)
        predict = lambda x: a * np.power(x, b)
        x_values = x_values[mask]
        y_values = y_values[mask]
        predicted = predict(x_values)
        r2_values = (log_y, intercept + slope * log_x) if fit.r2_space == "linearized" else None
        result = {"fit_type": fit_type, "parameters": {"a": a, "b": b}, "predict": predict}
    elif fit_type == "exponential":
        mask = y_values > 0
        if int(mask.sum()) < 2:
            return None
        x_fit = x_values[mask]
        log_y = np.log(y_values[mask])
        transformed_weights = weights[mask] if weights is not None else None
        slope, intercept = weighted_polyfit(x_fit, log_y, 1, transformed_weights)
        a = float(np.exp(intercept))
        b = float(slope)
        predict = lambda x: a * np.exp(b * x)
        x_values = x_fit
        y_values = y_values[mask]
        predicted = predict(x_values)
        r2_values = (log_y, intercept + slope * x_fit) if fit.r2_space == "linearized" else None
        result = {"fit_type": fit_type, "parameters": {"a": a, "b": b}, "predict": predict}
    elif fit_type == "logarithmic":
        mask = x_values > 0
        if int(mask.sum()) < 2:
            return None
        log_x = np.log(x_values[mask])
        y_fit = y_values[mask]
        transformed_weights = weights[mask] if weights is not None else None
        a, b = weighted_polyfit(log_x, y_fit, 1, transformed_weights)
        a = float(a)
        b = float(b)
        predict = lambda x: a * np.log(x) + b
        x_values = x_values[mask]
        y_values = y_fit
        predicted = predict(x_values)
        result = {"fit_type": fit_type, "parameters": {"a": a, "b": b}, "predict": predict}
    else:
        return None

    r2_target, r2_predicted = r2_values if r2_values is not None else (y_values, predicted)
    result.update(
        {
            "r2": calculate_r2(r2_target, r2_predicted),
            "data_x_min": float(np.min(x_values)),
            "data_x_max": float(np.max(x_values)),
        }
    )
    return result


def fit_weights(data, series):
    fit = series.fit_config
    if fit.weight_mode == "none" or not fit.weight_column or fit.weight_column not in data.columns:
        return None
    values = data[fit.weight_column].to_numpy(dtype=float)
    valid = np.isfinite(values) & (values > 0)
    if not np.all(valid):
        values = np.where(valid, values, np.nan)
    if fit.weight_mode == "y_sigma":
        weights = 1.0 / (values ** 2)
    elif fit.weight_mode == "custom_weight":
        weights = values
    else:
        return None
    if not np.all(np.isfinite(weights)):
        return None
    return weights


def weighted_polyfit(x_values, y_values, degree, weights=None):
    if weights is None:
        return np.polyfit(x_values, y_values, degree)
    return np.polyfit(x_values, y_values, degree, w=np.sqrt(weights))


def calculate_r2(y_values, predicted):
    residual = np.sum((y_values - predicted) ** 2)
    total = np.sum((y_values - np.mean(y_values)) ** 2)
    return float(1.0 if total == 0 else 1 - residual / total)


def signed_term(sign, term, first=False):
    if first:
        return f"-{term}" if sign == "-" else term
    return f" {sign} {term}"


def format_polynomial_equation(coefficients, number_format):
    degree = len(coefficients) - 1
    terms = []
    for index, coefficient in enumerate(coefficients):
        power = degree - index
        if abs(coefficient) < 1e-12:
            continue
        sign = "-" if coefficient < 0 else "+"
        value = abs(coefficient)
        if power == 0:
            term = format_number(value, number_format)
        elif power == 1:
            term = f"{format_number(value, number_format)}x"
        else:
            term = f"{format_number(value, number_format)}x^{power}"
        terms.append((sign, term))
    if not terms:
        return "y = 0"
    expression = ""
    for index, (sign, term) in enumerate(terms):
        expression += signed_term(sign, term, first=index == 0)
    return f"y = {expression}"


def format_fit_equation(fit_result, number_format):
    fit_type = fit_result["fit_type"]
    parameters = fit_result.get("parameters", {})
    if fit_type == "polynomial":
        return format_polynomial_equation(fit_result["coefficients"], number_format)
    if fit_type == "linear":
        a = parameters["a"]
        b = parameters["b"]
        if abs(b) < 1e-12:
            return f"y = {format_number(a, number_format)}x"
        sign = "+" if b >= 0 else "-"
        return (
            f"y = {format_number(a, number_format)}x "
            f"{sign} {format_number(abs(b), number_format)}"
        )
    if fit_type == "power":
        return (
            f"y = {format_number(parameters['a'], number_format)}"
            f"x^{format_number(parameters['b'], number_format)}"
        )
    if fit_type == "exponential":
        return (
            f"y = {format_number(parameters['a'], number_format)}"
            f"e^({format_number(parameters['b'], number_format)}x)"
        )
    if fit_type == "logarithmic":
        a = parameters["a"]
        b = parameters["b"]
        sign = "+" if b >= 0 else "-"
        return (
            f"y = {format_number(a, number_format)}ln x "
            f"{sign} {format_number(abs(b), number_format)}"
        )
    return ""
