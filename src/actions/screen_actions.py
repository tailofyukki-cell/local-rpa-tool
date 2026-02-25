"""
スクリーン操作アクションモジュール
スクリーンショット保存・ピクセル色取得を提供する。
"""
import time
from pathlib import Path
from typing import Any, Dict

from src.core.action_base import ActionBase, ActionResult, ActionStatus


def _get_pyautogui():
    import pyautogui
    pyautogui.FAILSAFE = True
    return pyautogui


class ScreenshotAction(ActionBase):
    ACTION_TYPE = "screen.screenshot"
    DISPLAY_NAME = "スクリーンショット保存"
    DESCRIPTION = "現在の画面をスクリーンショットとして保存します。"
    CATEGORY = "スクリーン操作"
    ICON = "📷"
    PARAMS_SCHEMA = [
        {"name": "filename", "label": "ファイル名", "type": "string",
         "default": "screenshot_{{current_datetime}}.png", "required": False,
         "description": "保存ファイル名（{{変数名}}使用可）"},
        {"name": "save_dir", "label": "保存先", "type": "string",
         "default": "", "required": False,
         "description": "保存先ディレクトリ（空=logsフォルダ）"},
        {"name": "region_x", "label": "領域 X", "type": "int", "default": 0, "required": False},
        {"name": "region_y", "label": "領域 Y", "type": "int", "default": 0, "required": False},
        {"name": "region_w", "label": "領域 幅", "type": "int", "default": 0, "required": False},
        {"name": "region_h", "label": "領域 高さ", "type": "int", "default": 0, "required": False},
        {"name": "var_path", "label": "パス変数名", "type": "string",
         "default": "screenshot_path", "required": False,
         "description": "保存先パスを格納する変数名"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        try:
            pyautogui = _get_pyautogui()

            # 保存先ディレクトリ
            save_dir = params.get("save_dir", "")
            if not save_dir:
                base_dir = context.get_variable("_base_dir", ".")
                save_dir = str(Path(base_dir) / "logs")
            Path(save_dir).mkdir(parents=True, exist_ok=True)

            # ファイル名
            filename = params.get("filename", "")
            if not filename:
                ts = time.strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{ts}.png"

            save_path = str(Path(save_dir) / filename)

            # 領域指定
            rx = int(params.get("region_x", 0))
            ry = int(params.get("region_y", 0))
            rw = int(params.get("region_w", 0))
            rh = int(params.get("region_h", 0))

            if rw > 0 and rh > 0:
                screenshot = pyautogui.screenshot(region=(rx, ry, rw, rh))
            else:
                screenshot = pyautogui.screenshot()

            screenshot.save(save_path)

            var_path = params.get("var_path", "screenshot_path")
            context.set_variable(var_path, save_path)

            return ActionResult(
                status=ActionStatus.SUCCESS,
                output=f"スクリーンショット保存: {save_path}",
                data={"path": save_path},
            )
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=f"スクリーンショットエラー: {e}")


class GetPixelColorAction(ActionBase):
    ACTION_TYPE = "screen.get_pixel"
    DISPLAY_NAME = "ピクセル色取得"
    DESCRIPTION = "指定した座標のピクセル色を取得します。"
    CATEGORY = "スクリーン操作"
    ICON = "🎨"
    PARAMS_SCHEMA = [
        {"name": "x", "label": "X座標", "type": "int", "default": 0, "required": True},
        {"name": "y", "label": "Y座標", "type": "int", "default": 0, "required": True},
        {"name": "var_r", "label": "R値変数名", "type": "string", "default": "pixel_r", "required": False},
        {"name": "var_g", "label": "G値変数名", "type": "string", "default": "pixel_g", "required": False},
        {"name": "var_b", "label": "B値変数名", "type": "string", "default": "pixel_b", "required": False},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        try:
            x = int(params.get("x", 0))
            y = int(params.get("y", 0))
            var_r = params.get("var_r", "pixel_r")
            var_g = params.get("var_g", "pixel_g")
            var_b = params.get("var_b", "pixel_b")

            pyautogui = _get_pyautogui()
            pixel = pyautogui.pixel(x, y)
            r, g, b = pixel[0], pixel[1], pixel[2]

            context.set_variable(var_r, r)
            context.set_variable(var_g, g)
            context.set_variable(var_b, b)

            return ActionResult(
                status=ActionStatus.SUCCESS,
                output=f"ピクセル色: ({x},{y}) RGB({r},{g},{b})",
                data={"r": r, "g": g, "b": b},
            )
        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=f"ピクセル取得エラー: {e}")
