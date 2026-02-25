"""
キーボード操作アクションモジュール
文字入力・特殊キー送信・キーコンビネーションを提供する。
"""
import time
from typing import Any, Dict

from src.core.action_base import ActionBase, ActionResult, ActionStatus


def _get_pyautogui():
    import pyautogui
    pyautogui.FAILSAFE = True
    return pyautogui


# PyAutoGUIで使用できる特殊キー一覧
SPECIAL_KEYS = [
    "enter", "return", "tab", "space", "backspace", "delete", "escape", "esc",
    "up", "down", "left", "right",
    "home", "end", "pageup", "pagedown",
    "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
    "ctrl", "alt", "shift", "win", "command",
    "insert", "printscreen", "scrolllock", "pause",
    "numlock", "capslock",
]


class KeyTypeAction(ActionBase):
    ACTION_TYPE = "key.type"
    DISPLAY_NAME = "文字入力"
    DESCRIPTION = "テキストを入力します。"
    CATEGORY = "キーボード操作"
    ICON = "⌨️"
    PARAMS_SCHEMA = [
        {"name": "text", "label": "入力テキスト", "type": "string",
         "default": "", "required": True, "description": "入力するテキスト（{{変数名}}使用可）"},
        {"name": "interval_ms", "label": "入力間隔(ms)", "type": "int",
         "default": 0, "required": False, "description": "1文字ごとの入力間隔（ms）"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        try:
            text = str(params.get("text", ""))
            interval = int(params.get("interval_ms", 0)) / 1000.0

            pyautogui = _get_pyautogui()
            pyautogui.typewrite(text, interval=interval)

            return ActionResult(
                status=ActionStatus.SUCCESS,
                output=f"文字入力: '{text[:50]}{'...' if len(text) > 50 else ''}'",
            )
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=f"文字入力エラー: {e}")


class KeyPressAction(ActionBase):
    ACTION_TYPE = "key.press"
    DISPLAY_NAME = "キー送信"
    DESCRIPTION = "特殊キーを送信します。"
    CATEGORY = "キーボード操作"
    ICON = "⌨️"
    PARAMS_SCHEMA = [
        {"name": "key", "label": "キー", "type": "select",
         "options": SPECIAL_KEYS,
         "default": "enter", "required": True, "description": "送信するキー"},
        {"name": "presses", "label": "回数", "type": "int",
         "default": 1, "min": 1, "max": 100, "required": False},
        {"name": "interval_ms", "label": "押下間隔(ms)", "type": "int",
         "default": 0, "required": False},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        try:
            key = params.get("key", "enter")
            presses = int(params.get("presses", 1))
            interval = int(params.get("interval_ms", 0)) / 1000.0

            pyautogui = _get_pyautogui()
            pyautogui.press(key, presses=presses, interval=interval)

            return ActionResult(
                status=ActionStatus.SUCCESS,
                output=f"キー送信: {key} x{presses}",
            )
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=f"キー送信エラー: {e}")


class KeyHotkeyAction(ActionBase):
    ACTION_TYPE = "key.hotkey"
    DISPLAY_NAME = "キー組み合わせ"
    DESCRIPTION = "Ctrl+Cなどのキーコンビネーションを送信します。"
    CATEGORY = "キーボード操作"
    ICON = "⌨️"
    PARAMS_SCHEMA = [
        {"name": "keys", "label": "キー組み合わせ", "type": "string",
         "default": "ctrl+c", "required": True,
         "description": "キーをプラス記号で連結（例: ctrl+c, ctrl+alt+delete, ctrl+shift+s）"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        try:
            keys_str = params.get("keys", "ctrl+c")
            keys = [k.strip().lower() for k in keys_str.split("+")]

            pyautogui = _get_pyautogui()
            pyautogui.hotkey(*keys)

            return ActionResult(
                status=ActionStatus.SUCCESS,
                output=f"ホットキー送信: {keys_str}",
            )
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=f"ホットキーエラー: {e}")
