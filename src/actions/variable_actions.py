"""
変数処理アクションモジュール
変数の設定・日時取得・数値計算を提供する。
"""
import math
from datetime import datetime
from typing import Any, Dict

from src.core.action_base import ActionBase, ActionResult, ActionStatus


class SetVariableAction(ActionBase):
    ACTION_TYPE = "variable.set"
    DISPLAY_NAME = "変数を設定"
    DESCRIPTION = "変数に値を設定します。"
    CATEGORY = "変数・データ"
    ICON = "📝"
    PARAMS_SCHEMA = [
        {"name": "name", "label": "変数名", "type": "string",
         "default": "myVar", "required": True},
        {"name": "value", "label": "値", "type": "string",
         "default": "", "required": True, "description": "設定する値（{{変数名}}使用可）"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        try:
            name = params.get("name", "")
            value = params.get("value", "")
            if not name:
                return ActionResult(status=ActionStatus.FAILED, error_message="変数名が指定されていません。")
            context.set_variable(name, value)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                output=f"変数設定: {name} = '{value}'",
            )
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=f"変数設定エラー: {e}")


class GetDateAction(ActionBase):
    ACTION_TYPE = "variable.get_date"
    DISPLAY_NAME = "日時取得"
    DESCRIPTION = "現在の日時を変数に保存します。"
    CATEGORY = "変数・データ"
    ICON = "📅"
    PARAMS_SCHEMA = [
        {"name": "format", "label": "日時フォーマット", "type": "string",
         "default": "%Y%m%d_%H%M%S", "required": True,
         "description": "例: %Y%m%d_%H%M%S → 20250101_120000"},
        {"name": "var_name", "label": "変数名", "type": "string",
         "default": "current_datetime", "required": True},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        try:
            fmt = params.get("format", "%Y%m%d_%H%M%S")
            var_name = params.get("var_name", "current_datetime")
            now = datetime.now().strftime(fmt)
            context.set_variable(var_name, now)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                output=f"日時取得: {var_name} = '{now}'",
            )
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=f"日時取得エラー: {e}")


class MathCalcAction(ActionBase):
    ACTION_TYPE = "variable.math"
    DISPLAY_NAME = "数値計算"
    DESCRIPTION = "数値計算を行い結果を変数に保存します。"
    CATEGORY = "変数・データ"
    ICON = "🔢"
    PARAMS_SCHEMA = [
        {"name": "expression", "label": "計算式", "type": "string",
         "default": "{{a}} + {{b}}", "required": True,
         "description": "計算式（変数使用可、+,-,*,/,//,%,**）"},
        {"name": "var_name", "label": "結果変数名", "type": "string",
         "default": "result", "required": True},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        try:
            expression = params.get("expression", "0")
            var_name = params.get("var_name", "result")

            # 安全な評価（許可する関数のみ）
            safe_globals = {
                "__builtins__": {},
                "abs": abs, "round": round, "int": int, "float": float,
                "min": min, "max": max,
                "sqrt": math.sqrt, "floor": math.floor, "ceil": math.ceil,
                "pow": math.pow, "log": math.log,
            }
            result = eval(expression, safe_globals, {})
            context.set_variable(var_name, result)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                output=f"計算: {expression} = {result}",
            )
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=f"計算エラー: {e}")
