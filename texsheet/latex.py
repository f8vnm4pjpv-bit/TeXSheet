import re
import subprocess

from texsheet.paths import PROJECT_DIR, project_path


def escape_latex(value):
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def escape_latex_with_math(value):
    text = str(value)
    if text.count("$") % 2 == 1:
        return escape_latex(text)

    parts = re.split(r"(\$.*?\$)", text)
    escaped_parts = []
    for index, part in enumerate(parts):
        if index % 2 == 1:
            escaped_parts.append(part)
        else:
            escaped_parts.append(escape_latex(part))
    return "".join(escaped_parts)


def escape_latex_header_text(value):
    text = str(value)
    replacements = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def escape_latex_header(value):
    text = str(value)
    if text.count("$") % 2 == 1:
        return escape_latex_header_text(text)

    parts = re.split(r"(\$.*?\$)", text)
    escaped_parts = []
    for index, part in enumerate(parts):
        if index % 2 == 1:
            escaped_parts.append(part)
        else:
            escaped_parts.append(escape_latex_header_text(part))
    return "".join(escaped_parts)


def normalize_latex_label(value, default="tab:table"):
    text = str(value or default)
    text = text.replace(r"\_", "_")
    text = re.sub(r"[^0-9A-Za-z_:-]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or default


def get_column_alignment(column, table_config):
    alignment = table_config.get("column_alignments", {}).get(column, "l")
    if alignment not in {"l", "c", "r"}:
        return "l"
    return alignment


def build_column_format(columns, table_config):
    alignments = [get_column_alignment(column, table_config) for column in columns]
    border_style = table_config.get("border_style", "booktabs")
    if border_style in {"full", "vertical"}:
        return "|" + "|".join(alignments) + "|"
    return "".join(alignments)


def build_table_tex(dataframe, table_config):
    border_style = table_config.get("border_style", "booktabs")
    column_format = build_column_format(dataframe.columns, table_config)
    header = " & ".join(escape_latex_header(column) for column in dataframe.columns)
    rows = [
        " & ".join(escape_latex_with_math(value) for value in row)
        for row in dataframe.itertuples(index=False, name=None)
    ]

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        rf"\caption{{{escape_latex_with_math(table_config['caption'])}}}",
        rf"\label{{{normalize_latex_label(table_config['label'])}}}",
        rf"\begin{{tabular}}{{{column_format}}}",
    ]

    if border_style in {"booktabs", "vertical"}:
        lines.extend([r"\toprule", rf"{header} \\", r"\midrule"])
        lines.extend(rf"{row} \\" for row in rows)
        lines.append(r"\bottomrule")
    elif border_style == "full":
        lines.extend([r"\hline", rf"{header} \\ \hline"])
        lines.extend(rf"{row} \\ \hline" for row in rows)
    else:
        lines.append(rf"{header} \\")
        lines.extend(rf"{row} \\" for row in rows)

    lines.extend([r"\end{tabular}", r"\end{table}", ""])
    return "\n".join(lines)


def save_table_tex(dataframe, table_config):
    output_path = project_path(table_config["output_tex"])
    table_tex = build_table_tex(dataframe, table_config)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(table_tex, encoding="utf-8")
    return output_path


def compile_latex():
    if not (PROJECT_DIR / "main.tex").exists():
        raise RuntimeError(
            "main.tex が見つからない。コンパイルするには project/main.tex が必要である。"
        )

    command = ["latexmk", "-lualatex", "main.tex"]
    try:
        subprocess.run(
            command,
            cwd=PROJECT_DIR,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as error:
        raise RuntimeError(
            "latexmkが見つかりません。TeX環境にlatexmkをインストールし、PATHに追加してください。"
        ) from error
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or "").strip()
        if detail:
            raise RuntimeError(f"LaTeXコンパイルに失敗しました。\n{detail}") from error
        raise RuntimeError("LaTeXコンパイルに失敗しました。") from error

    return PROJECT_DIR / "main.pdf"
