from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class NumberFormatConfig:
    mode: str = "significant_figures"
    digits: int = 4
    use_scientific: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None):
        data = data or {}
        mode = str(data.get("mode", "significant_figures"))
        if mode not in {"decimal_places", "significant_figures"}:
            mode = "significant_figures"
        return cls(
            mode=mode,
            digits=max(0, int(data.get("digits", 4))),
            use_scientific=bool(data.get("use_scientific", False)),
        )

    def to_dict(self):
        return {
            "mode": self.mode,
            "digits": self.digits,
            "use_scientific": self.use_scientific,
        }


def to_optional_float(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def format_number(value, format_config=None):
    format_config = format_config or NumberFormatConfig()
    if value is None:
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not np.isfinite(number):
        return str(number)
    if format_config.use_scientific:
        return f"{number:.{format_config.digits}e}"
    if format_config.mode == "decimal_places":
        return f"{number:.{format_config.digits}f}"
    if number == 0:
        return f"{0:.{max(0, format_config.digits - 1)}f}"
    digits = max(1, format_config.digits)
    exponent = int(np.floor(np.log10(abs(number))))
    decimal_places = digits - exponent - 1
    if decimal_places >= 0:
        return f"{number:.{decimal_places}f}"
    rounded = round(number, decimal_places)
    return f"{rounded:.0f}"
