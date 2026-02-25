"""
同期・待機アクションモジュール
固定待機・色一致待機・ウィンドウ前面化待機を提供する。
"""
import time
from typing import Any, Dict, Tuple

from src.core.action_base import ActionBase, ActionResult, ActionStatus


def _get_pyautogui():
    import pyautogui
    pyautogui.FAILSAFE = True
    return pyautogui


class WaitAction(ActionBase):
    ACTION_TYPE = "wait.sleep"
    DISPLAY_NAME = "固定待機"
    DESCRIPTION = "指定した時間だけ待機します。"
    CATEGORY = "同期・待機"
    ICON = "⏱️"
    PARAMS_SCHEMA = [
        {"name": "duration_ms", "label": "待機時間(ms)", "type": "int",
         "default": 1000, "min": 0, "max": 60000, "required": True,
         "description": "待機時間（ミリ秒）"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        try:
            duration_ms = int(params.get("duration_ms", 1000))
            time.sleep(duration_ms / 1000.0)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                output=f"待機完了: {duration_ms}ms",
            )
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=f"待機エラー: {e}")


class WaitColorAction(ActionBase):
    ACTION_TYPE = "wait.color"
    DISPLAY_NAME = "色一致待機"
    DESCRIPTION = "指定した座標のピクセル色が一致するまで待機します。"
    CATEGORY = "同期・待機"
    ICON = "🎨"
    PARAMS_SCHEMA = [
        {"name": "x", "label": "X座標", "type": "int", "default": 0, "required": True},
        {"name": "y", "label": "Y座標", "type": "int", "default": 0, "required": True},
        {"name": "r", "label": "R値", "type": "int", "default": 255, "min": 0, "max": 255, "required": True},
        {"name": "g", "label": "G値", "type": "int", "default": 0, "min": 0, "max": 255, "required": True},
        {"name": "b", "label": "B値", "type": "int", "default": 0, "min": 0, "max": 255, "required": True},
        {"name": "tolerance", "label": "許容誤差", "type": "int",
         "default": 10, "min": 0, "max": 100, "required": False,
         "description": "RGB各チャンネルの許容誤差"},
        {"name": "timeout_sec", "label": "タイムアウト(秒)", "type": "int",
         "default": 30, "min": 1, "max": 300, "required": True},
        {"name": "interval_ms", "label": "チェック間隔(ms)", "type": "int",
         "default": 200, "required": False},
        {"name": "var_matched", "label": "結果変数名", "type": "string",
         "default": "color_matched", "required": False},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        try:
            x = int(params.get("x", 0))
            y = int(params.get("y", 0))
            target_r = int(params.get("r", 255))
            target_g = int(params.get("g", 0))
            target_b = int(params.get("b", 0))
            tolerance = int(params.get("tolerance", 10))
            timeout_sec = int(params.get("timeout_sec", 30))
            interval_ms = int(params.get("interval_ms", 200))
            var_matched = params.get("var_matched", "color_matched")

            pyautogui = _get_pyautogui()
            start_time = time.time()
            interval_sec = interval_ms / 1000.0

            while True:
                elapsed = time.time() - start_time
                if elapsed >= timeout_sec:
                    context.set_variable(var_matched, "false")
                    return ActionResult(
                        status=ActionStatus.TIMEOUT,
                        error_message=f"色一致タイムアウト: ({x},{y}) RGB({target_r},{target_g},{target_b})",
                    )

                pixel = pyautogui.pixel(x, y)
                r, g, b = pixel[0], pixel[1], pixel[2]

                if (abs(r - target_r) <= tolerance and
                        abs(g - target_g) <= tolerance and
                        abs(b - target_b) <= tolerance):
                    context.set_variable(var_matched, "true")
                    return ActionResult(
                        status=ActionStatus.SUCCESS,
                        output=f"色一致: ({x},{y}) RGB({r},{g},{b}) 経過={elapsed:.1f}s",
                    )

                time.sleep(interval_sec)

        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=f"色待機エラー: {e}")


class WaitWindowAction(ActionBase):
    ACTION_TYPE = "wait.window"
    DISPLAY_NAME = "ウィンドウ前面化待機"
    DESCRIPTION = "指定したタイトルのウィンドウが前面に来るまで待機します。"
    CATEGORY = "同期・待機"
    ICON = "🪟"
    PARAMS_SCHEMA = [
        {"name": "title", "label": "ウィンドウタイトル", "type": "string",
         "default": "", "required": True,
         "description": "前面化を待つウィンドウのタイトル（部分一致）"},
        {"name": "timeout_sec", "label": "タイムアウト(秒)", "type": "int",
         "default": 30, "min": 1, "max": 300, "required": True},
        {"name": "interval_ms", "label": "チェック間隔(ms)", "type": "int",
         "default": 500, "required": False},
        {"name": "bring_to_front", "label": "前面化する", "type": "bool",
         "default": True, "required": False,
         "description": "ウィンドウを前面に移動する"},
        {"name": "var_found", "label": "結果変数名", "type": "string",
         "default": "window_found", "required": False},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        try:
            title = params.get("title", "")
            timeout_sec = int(params.get("timeout_sec", 30))
            interval_ms = int(params.get("interval_ms", 500))
            bring_to_front = str(params.get("bring_to_front", "true")).lower() in ("true", "1", "yes")
            var_found = params.get("var_found", "window_found")

            if not title:
                return ActionResult(status=ActionStatus.FAILED, error_message="ウィンドウタイトルが指定されていません。")

            # pygetwindowを使用（Windows専用）
            try:
                import pygetwindow as gw
            except ImportError:
                context.set_variable(var_found, "false")
                return ActionResult(
                    status=ActionStatus.FAILED,
                    error_message="pygetwindow がインストールされていません。",
                )

            start_time = time.time()
            interval_sec = interval_ms / 1000.0

            while True:
                elapsed = time.time() - start_time
                if elapsed >= timeout_sec:
                    context.set_variable(var_found, "false")
                    return ActionResult(
                        status=ActionStatus.TIMEOUT,
                        error_message=f"ウィンドウ待機タイムアウト: '{title}'",
                    )

                windows = gw.getWindowsWithTitle(title)
                if windows:
                    win = windows[0]
                    if bring_to_front:
                        try:
                            win.activate()
                        except Exception:
                            pass
                    context.set_variable(var_found, "true")
                    return ActionResult(
                        status=ActionStatus.SUCCESS,
                        output=f"ウィンドウ発見: '{win.title}' 経過={elapsed:.1f}s",
                    )

                time.sleep(interval_sec)

        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=f"ウィンドウ待機エラー: {e}")
