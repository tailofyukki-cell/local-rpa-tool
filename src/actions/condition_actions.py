"""
条件分岐アクションモジュール
IF条件・ENDIFを提供する。
"""
from typing import Any, Dict

from src.core.action_base import ActionBase, ActionResult, ActionStatus


def _evaluate_condition(left: str, operator: str, right: str) -> bool:
    """条件式を評価する。"""
    op = operator.strip().lower()

    # 数値比較を試みる
    try:
        l_num = float(left)
        r_num = float(right)
        if op in ("=", "=="):
            return l_num == r_num
        elif op in ("!=", "<>"):
            return l_num != r_num
        elif op == ">":
            return l_num > r_num
        elif op == ">=":
            return l_num >= r_num
        elif op == "<":
            return l_num < r_num
        elif op == "<=":
            return l_num <= r_num
    except (ValueError, TypeError):
        pass

    # 文字列比較
    if op in ("=", "=="):
        return left == right
    elif op in ("!=", "<>"):
        return left != right
    elif op == "contains":
        return right in left
    elif op == "not_contains":
        return right not in left
    elif op == "startswith":
        return left.startswith(right)
    elif op == "endswith":
        return left.endswith(right)
    elif op == "isempty":
        return left.strip() == ""
    elif op == "notempty":
        return left.strip() != ""
    elif op == ">":
        return left > right
    elif op == ">=":
        return left >= right
    elif op == "<":
        return left < right
    elif op == "<=":
        return left <= right

    return False


class IfConditionAction(ActionBase):
    ACTION_TYPE = "condition.if"
    DISPLAY_NAME = "IF条件"
    DESCRIPTION = "条件が真の場合のみ後続のアクションを実行します。"
    CATEGORY = "条件分岐"
    ICON = "🔀"
    PARAMS_SCHEMA = [
        {"name": "left", "label": "左辺", "type": "string",
         "default": "{{match_found}}", "required": True,
         "description": "比較する左辺の値（変数使用可）"},
        {"name": "operator", "label": "演算子", "type": "select",
         "options": ["=", "!=", ">", ">=", "<", "<=", "contains", "not_contains",
                     "startswith", "endswith", "isempty", "notempty"],
         "default": "=", "required": True},
        {"name": "right", "label": "右辺", "type": "string",
         "default": "true", "required": False,
         "description": "比較する右辺の値（変数使用可）"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        try:
            left = str(params.get("left", ""))
            operator = params.get("operator", "=")
            right = str(params.get("right", ""))

            condition_met = _evaluate_condition(left, operator, right)

            return ActionResult(
                status=ActionStatus.SUCCESS,
                output=f"IF: '{left}' {operator} '{right}' → {'TRUE' if condition_met else 'FALSE'}",
                data={"condition_met": condition_met},
            )
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=f"条件評価エラー: {e}")


class EndIfAction(ActionBase):
    ACTION_TYPE = "condition.endif"
    DISPLAY_NAME = "ENDIF"
    DESCRIPTION = "IF条件ブロックの終端を示します。"
    CATEGORY = "条件分岐"
    ICON = "🔚"
    PARAMS_SCHEMA = []

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        return ActionResult(status=ActionStatus.SUCCESS, output="ENDIF")
