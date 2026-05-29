import ast
import math

import pandas as pd

from texsheet.formula_resolver import (
    add_column_aliases,
    add_external_table_aliases,
    missing_external_references,
)


SCIENTIFIC_CONSTANTS = {

    # --- デフォルト ---
    "R": 8.31446261815324,             #[J/mol/K]
    "N_A": 6.02214076e23,
    "k_B": 1.380649e-23,
    "e": 1.602176634e-19,
    "F": 96485.33212331001,
    "h": 6.62607015e-34,
    "c": 299792458.0,
    

     # --- 基本化学定数 ---
    "R_L_atm": 0.082057366080960,       # 気体定数 [L·atm/mol/K]
    "R_cm3_MPa": 8.314462618,           # [cm^3·MPa/mol/K]
    "pKa_water": 14.0,                  # 水の自己解離 pKa（25℃）
    "K_w": 1.0e-14,                     # 水のイオン積
    "NA_volume": 22.414,                # 標準状態モル体積 [L/mol]

     # --- 基本物理定数 ---
    "mu_0": 1.25663706212e-6,          # 真空の透磁率 [N/A^2]
    "epsilon_0": 8.8541878128e-12,     # 真空の誘電率 [F/m]
    "sigma_SB": 5.670374419e-8,        # ステファン＝ボルツマン定数 [W/m^2/K^4]
    "G": 6.67430e-11,                  # 万有引力定数 [m^3/kg/s^2]
    "g_0": 9.80665,                    # 標準重力加速度 [m/s^2]

    # --- 電磁気・回路 ---
    "Z_0": 376.730313668,              # 真空インピーダンス [Ω]
    "phi_0": 2.067833848e-15,          # 磁束量子 [Wb]

    # --- 量子物理・原子物理 ---
    "hbar": 1.054571817e-34,           # ディラック定数 [J·s]
    "a_0": 5.29177210903e-11,          # ボーア半径 [m]
    "R_inf": 1.0973731568160e7,        # リュードベリ定数 [1/m]
    "alpha": 7.2973525693e-3,          # 微細構造定数 [-]
    "E_h": 4.3597447222071e-18,        # ハートリーエネルギー [J]

    # --- 分光・量子化学 ---
    "hc": 1.98644586e-25,              # h*c [J·m]
    "hc_eV_nm": 1239.841984,           # [eV·nm]
    "k_B_eV": 8.617333262e-5,          # ボルツマン定数 [eV/K]
    "amu_to_kg": 1.66053906660e-27,    # 1原子質量→kg
    "Eh_to_eV": 27.211386245988,       # ハートリー→eV

    # --- 粒子の質量 ---
    "m_e": 9.1093837015e-31,           # 電子質量 [kg]
    "m_p": 1.67262192369e-27,          # 陽子質量 [kg]
    "m_n": 1.67492749804e-27,          # 中性子質量 [kg]

    # --- 単位変換 ---
    "eV_to_J": 1.602176634e-19,        # 1 eV in J
    "angstrom_to_m": 1e-10,            # 1 Å in m
    "atm_to_Pa": 101325.0,             # 1 atm in Pa
    "cal_to_J": 4.184,                 # 1 cal in J

    # --- 熱力学 ---
    "sigma": 5.670374419e-8,           # ステファン＝ボルツマン定数（別名）
    "R_inf_energy": 2.1798723611035e-18, # リュードベリエネルギー [J]

    # --- 地球科学 ---
    "R_E": 6.371e6,                    # 地球半径 [m]
    "M_E": 5.9722e24,                  # 地球質量 [kg]
    "P_0": 101325.0,                   # 標準大気圧 [Pa]

    # --- 天文 ---
    "AU": 1.495978707e11,              # 天文単位 [m]
    "parsec": 3.085677581e16,          # パーセク [m]
    "year": 31557600,                  # ユリウス年 [s]

    "solar_mass": 1.98847e30,          # [kg]
    "planck_length": 1.616255e-35,     # [m]
    "planck_time": 5.391247e-44,       # [s]

    # --- その他 ---
    "mu_B": 9.2740100783e-24,          # ボーア磁子 [J/T]
    "mu_N": 5.0507837461e-27,          # 核磁子 [J/T]
    "golden_ratio": 1.6180339887498948,
    "euler_gamma": 0.5772156649015329,
}

ALLOWED_FUNCTIONS = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "ln": math.log,
    "exp": math.exp,
    "sqrt": math.sqrt,
    "abs": abs,
}


def root(value, degree):
    if degree == 0:
        raise FormulaError("0乗根は使用できない")
    if value < 0 and float(degree).is_integer() and int(degree) % 2 == 0:
        raise FormulaError("負の数の偶数乗根は実数で扱えない")
    if value < 0:
        return -((-value) ** (1 / degree))
    return value ** (1 / degree)


ALLOWED_FUNCTIONS["root"] = root

ALLOWED_BINOPS = {
    ast.Add: lambda left, right: left + right,
    ast.Sub: lambda left, right: left - right,
    ast.Mult: lambda left, right: left * right,
    ast.Div: lambda left, right: left / right,
    ast.Pow: lambda left, right: left ** right,
    ast.BitXor: lambda left, right: left ** right,
}

ALLOWED_UNARYOPS = {
    ast.UAdd: lambda value: value,
    ast.USub: lambda value: -value,
}


class FormulaError(Exception):
    pass


def parse_number(value):
    if value is None:
        raise FormulaError("値が空である")
    text = str(value).strip()
    if not text:
        raise FormulaError("値が空である")
    return float(text)


class SafeFormulaEvaluator:
    def __init__(self, row_values, project_constants):
        self.row_values = row_values
        self.project_constants = project_constants

    def evaluate(self, expression):
        tree = ast.parse(expression, mode="eval")
        return self.visit(tree)

    def visit(self, node):
        if isinstance(node, ast.Expression):
            return self.visit(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise FormulaError("数値以外のリテラルは使用できない")
        if isinstance(node, ast.Name):
            if node.id in ALLOWED_FUNCTIONS:
                return ALLOWED_FUNCTIONS[node.id]
            if node.id in {"cons", "const", "proj"}:
                return node.id
            if node.id not in self.row_values:
                raise FormulaError(f"未定義列: {node.id}")
            return parse_number(self.row_values[node.id])
        if isinstance(node, ast.Attribute):
            namespace = self.visit(node.value)
            if node.attr.startswith("_"):
                raise FormulaError("不正な属性参照である")
            if namespace in {"cons", "const"}:
                if node.attr not in SCIENTIFIC_CONSTANTS:
                    raise FormulaError(f"未定義定数: {namespace}.{node.attr}")
                return SCIENTIFIC_CONSTANTS[node.attr]
            if namespace == "proj":
                if node.attr not in self.project_constants:
                    raise FormulaError(f"未定義定数: proj.{node.attr}")
                return parse_number(self.project_constants[node.attr])
            raise FormulaError("不正な属性参照である")
        if isinstance(node, ast.BinOp):
            operator = type(node.op)
            if operator not in ALLOWED_BINOPS:
                raise FormulaError("使用できない演算子である")
            return ALLOWED_BINOPS[operator](self.visit(node.left), self.visit(node.right))
        if isinstance(node, ast.UnaryOp):
            operator = type(node.op)
            if operator not in ALLOWED_UNARYOPS:
                raise FormulaError("使用できない単項演算子である")
            return ALLOWED_UNARYOPS[operator](self.visit(node.operand))
        if isinstance(node, ast.Call):
            function = self.visit(node.func)
            if function not in ALLOWED_FUNCTIONS.values():
                raise FormulaError("使用できない関数である")
            if node.keywords:
                raise FormulaError("キーワード引数は使用できない")
            arguments = [self.visit(argument) for argument in node.args]
            return function(*arguments)
        raise FormulaError("使用できない構文である")


def format_result(value):
    if math.isfinite(value) and value.is_integer():
        return str(int(value))
    return f"{value:.12g}"


def apply_formulas_to_dataframe(
    dataframe,
    table_config,
    project_constants=None,
    external_tables=None,
):
    formulas = table_config.get("formulas", {})
    project_constants = project_constants or {}
    if not formulas:
        return dataframe.copy(), []

    result = dataframe.copy()
    messages = []
    for column, expression in formulas.items():
        if column not in result.columns:
            messages.append(f"{column}列: 数式列が存在しないため計算をスキップしました。")
            continue

        result[column] = result[column].astype("object")
        error_rows = []
        for row_index, row in result.iterrows():
            row_values = {}
            add_column_aliases(row_values, table_config, row.to_dict())
            add_external_table_aliases(row_values, row_index, external_tables)
            try:
                missing_tables = missing_external_references(
                    expression,
                    row_index,
                    external_tables,
                )
                if missing_tables:
                    raise FormulaError(
                        f"参照先表の行が不足している: {', '.join(missing_tables)}"
                    )
                value = SafeFormulaEvaluator(row_values, project_constants).evaluate(expression)
                result.at[row_index, column] = format_result(float(value))
            except Exception:
                result.at[row_index, column] = "-"
                error_rows.append(row_index + 1)

        if error_rows:
            rows_text = ", ".join(str(row) for row in error_rows)
            messages.append(
                f"{column}列: {len(error_rows)}行で計算エラーが発生しました。行: {rows_text}"
            )
        else:
            messages.append(f"{column}列: 数式を計算しました。")

    return result, messages
