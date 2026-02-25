"""
マウス操作アクションモジュール
座標クリック・移動・ドラッグ・スクロールを提供する。
"""
import time
from typing import Any, Dict

from src.core.action_base import ActionBase, ActionResult, ActionStatus


def _get_pyautogui():
    import pyautogui
    pyautogui.FAILSAFE = True  # 左上コーナーで緊急停止
    return pyautogui


class MouseClickAction(ActionBase):
    ACTION_TYPE = "mouse.click"
    DISPLAY_NAME = "マウスクリック"
    DESCRIPTION = "指定した座標をクリックします。"
    CATEGORY = "マウス操作"
    ICON = "🖱️"
    PARAMS_SCHEMA = [
        {"name": "x", "label": "X座標", "type": "int_or_var",
         "default": "{{match.x}}", "required": True, "description": "クリックするX座標（変数使用可）"},
        {"name": "y", "label": "Y座標", "type": "int_or_var",
         "default": "{{match.y}}", "required": True, "description": "クリックするY座標（変数使用可）"},
        {"name": "button", "label": "ボタン", "type": "select",
         "options": ["left", "right", "double", "middle"],
         "default": "left", "required": False},
        {"name": "pre_delay_ms", "label": "クリック前待機(ms)", "type": "int",
         "default": 0, "required": False},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        try:
            x = int(float(str(params.get("x", 0))))
            y = int(float(str(params.get("y", 0))))
            button = params.get("button", "left")
            pre_delay = int(params.get("pre_delay_ms", 0))

            pyautogui = _get_pyautogui()

            if pre_delay > 0:
                time.sleep(pre_delay / 1000.0)

            if button == "double":
                pyautogui.doubleClick(x, y)
            elif button == "right":
                pyautogui.rightClick(x, y)
            elif button == "middle":
                pyautogui.middleClick(x, y)
            else:
                pyautogui.click(x, y)

            return ActionResult(
                status=ActionStatus.SUCCESS,
                output=f"{button}クリック: ({x}, {y})",
            )
        except pyautogui.FailSafeException:
            return ActionResult(
                status=ActionStatus.FAILED,
                error_message="フェイルセーフ: マウスが画面左上に移動しました。実行を停止します。",
            )
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=f"クリックエラー: {e}")


class MouseMoveAction(ActionBase):
    ACTION_TYPE = "mouse.move"
    DISPLAY_NAME = "マウス移動"
    DESCRIPTION = "マウスを指定した座標に移動します。"
    CATEGORY = "マウス操作"
    ICON = "↗️"
    PARAMS_SCHEMA = [
        {"name": "x", "label": "X座標", "type": "int_or_var", "default": 0, "required": True},
        {"name": "y", "label": "Y座標", "type": "int_or_var", "default": 0, "required": True},
        {"name": "duration_ms", "label": "移動時間(ms)", "type": "int",
         "default": 200, "required": False, "description": "移動にかける時間（0=即時）"},
        {"name": "relative", "label": "相対移動", "type": "bool",
         "default": False, "required": False, "description": "現在位置からの相対移動"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        try:
            x = int(float(str(params.get("x", 0))))
            y = int(float(str(params.get("y", 0))))
            duration = int(params.get("duration_ms", 200)) / 1000.0
            relative = str(params.get("relative", "false")).lower() in ("true", "1", "yes")

            pyautogui = _get_pyautogui()

            if relative:
                pyautogui.moveRel(x, y, duration=duration)
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    output=f"マウス相対移動: ({x:+d}, {y:+d})",
                )
            else:
                pyautogui.moveTo(x, y, duration=duration)
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    output=f"マウス移動: ({x}, {y})",
                )
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=f"マウス移動エラー: {e}")


class MouseDragAction(ActionBase):
    ACTION_TYPE = "mouse.drag"
    DISPLAY_NAME = "マウスドラッグ"
    DESCRIPTION = "マウスをドラッグします。"
    CATEGORY = "マウス操作"
    ICON = "✋"
    PARAMS_SCHEMA = [
        {"name": "from_x", "label": "開始X", "type": "int_or_var", "default": 0, "required": True},
        {"name": "from_y", "label": "開始Y", "type": "int_or_var", "default": 0, "required": True},
        {"name": "to_x", "label": "終了X", "type": "int_or_var", "default": 100, "required": True},
        {"name": "to_y", "label": "終了Y", "type": "int_or_var", "default": 100, "required": True},
        {"name": "duration_ms", "label": "ドラッグ時間(ms)", "type": "int",
         "default": 500, "required": False},
        {"name": "button", "label": "ボタン", "type": "select",
         "options": ["left", "right"], "default": "left", "required": False},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        try:
            from_x = int(float(str(params.get("from_x", 0))))
            from_y = int(float(str(params.get("from_y", 0))))
            to_x = int(float(str(params.get("to_x", 100))))
            to_y = int(float(str(params.get("to_y", 100))))
            duration = int(params.get("duration_ms", 500)) / 1000.0
            button = params.get("button", "left")

            pyautogui = _get_pyautogui()
            pyautogui.moveTo(from_x, from_y)
            pyautogui.dragTo(to_x, to_y, duration=duration, button=button)

            return ActionResult(
                status=ActionStatus.SUCCESS,
                output=f"ドラッグ: ({from_x}, {from_y}) → ({to_x}, {to_y})",
            )
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=f"ドラッグエラー: {e}")


class MouseScrollAction(ActionBase):
    ACTION_TYPE = "mouse.scroll"
    DISPLAY_NAME = "マウススクロール"
    DESCRIPTION = "マウスホイールをスクロールします。"
    CATEGORY = "マウス操作"
    ICON = "🖱️"
    PARAMS_SCHEMA = [
        {"name": "x", "label": "X座標", "type": "int_or_var", "default": 0, "required": False,
         "description": "スクロール位置X（0=現在位置）"},
        {"name": "y", "label": "Y座標", "type": "int_or_var", "default": 0, "required": False},
        {"name": "clicks", "label": "スクロール量", "type": "int",
         "default": 3, "required": True, "description": "正=上スクロール、負=下スクロール"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        try:
            x = int(float(str(params.get("x", 0))))
            y = int(float(str(params.get("y", 0))))
            clicks = int(params.get("clicks", 3))

            pyautogui = _get_pyautogui()
            if x > 0 or y > 0:
                pyautogui.scroll(clicks, x=x, y=y)
            else:
                pyautogui.scroll(clicks)

            direction = "上" if clicks > 0 else "下"
            return ActionResult(
                status=ActionStatus.SUCCESS,
                output=f"スクロール{direction}: {abs(clicks)}クリック",
            )
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=f"スクロールエラー: {e}")
