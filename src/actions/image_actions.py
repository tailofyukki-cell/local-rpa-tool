"""
画像マッチアクションモジュール
OpenCVを使用した画面上の画像検索・クリック・待機アクションを提供する。
"""
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from src.core.action_base import ActionBase, ActionResult, ActionStatus

# 遅延インポート（Windows環境でのみ動作）
def _get_cv2():
    import cv2
    return cv2

def _get_numpy():
    import numpy as np
    return np

def _get_pyautogui():
    import pyautogui
    return pyautogui


def _capture_screen():
    """スクリーンショットを取得してnumpy配列で返す。"""
    pyautogui = _get_pyautogui()
    np = _get_numpy()
    screenshot = pyautogui.screenshot()
    return np.array(screenshot)


def _find_template(
    screen_img,
    template_path: str,
    confidence: float = 0.8,
    grayscale: bool = False,
    region: Optional[Tuple[int, int, int, int]] = None,
) -> Optional[Tuple[int, int, float]]:
    """
    テンプレートマッチングで画像を検索する。

    Returns:
        (center_x, center_y, max_val) または None
    """
    cv2 = _get_cv2()
    np = _get_numpy()

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"テンプレート画像が見つかりません: {template_path}")

    # テンプレート読み込み
    template = cv2.imread(template_path)
    if template is None:
        raise ValueError(f"テンプレート画像を読み込めません: {template_path}")

    # 領域指定がある場合は切り取り
    search_img = screen_img.copy()
    offset_x, offset_y = 0, 0
    if region:
        x, y, w, h = region
        search_img = screen_img[y:y+h, x:x+w]
        offset_x, offset_y = x, y

    # グレースケール変換
    if grayscale:
        if len(search_img.shape) == 3:
            search_img = cv2.cvtColor(search_img, cv2.COLOR_RGB2GRAY)
        if len(template.shape) == 3:
            template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    else:
        # スクリーンショットはRGB、テンプレートはBGR → 変換
        if len(search_img.shape) == 3:
            search_img = cv2.cvtColor(search_img, cv2.COLOR_RGB2BGR)

    # テンプレートマッチング
    result = cv2.matchTemplate(search_img, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    if max_val >= confidence:
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2 + offset_x
        center_y = max_loc[1] + h // 2 + offset_y
        return (center_x, center_y, max_val)

    return None


def _resolve_template_path(template_name: str, context) -> str:
    """テンプレートパスを解決する。"""
    if os.path.isabs(template_name) and os.path.exists(template_name):
        return template_name
    templates_dir = context.get_variable("_templates_dir", "templates")
    path = os.path.join(templates_dir, template_name)
    if os.path.exists(path):
        return path
    # 拡張子なしの場合はPNGを試す
    if not template_name.lower().endswith((".png", ".jpg", ".bmp")):
        path_png = path + ".png"
        if os.path.exists(path_png):
            return path_png
    return path


def _highlight_match(x: int, y: int, w: int, h: int, duration: float = 0.5):
    """検出位置に一瞬ハイライト枠を表示する（Windows専用）。"""
    try:
        import ctypes
        import ctypes.wintypes
        # 簡易実装：マウスを検出位置に移動するだけ
        # 本格的なハイライトはWin32 APIが必要
    except Exception:
        pass


class ImageFindAction(ActionBase):
    ACTION_TYPE = "image.find"
    DISPLAY_NAME = "画像を検索"
    DESCRIPTION = "画面上でテンプレート画像を検索し、座標を変数に保存します。"
    CATEGORY = "画像マッチ"
    ICON = "🔍"
    PARAMS_SCHEMA = [
        {"name": "template", "label": "テンプレート画像", "type": "template_file",
         "default": "", "required": True, "description": "検索するテンプレート画像ファイル名"},
        {"name": "confidence", "label": "類似度", "type": "float",
         "default": 0.8, "min": 0.1, "max": 1.0, "step": 0.05,
         "required": False, "description": "マッチング類似度 (0.1〜1.0)"},
        {"name": "grayscale", "label": "グレースケール検索", "type": "bool",
         "default": False, "required": False, "description": "グレースケールで検索（高速化）"},
        {"name": "region_x", "label": "検索領域 X", "type": "int",
         "default": 0, "required": False, "description": "検索領域の左上X座標（0=全画面）"},
        {"name": "region_y", "label": "検索領域 Y", "type": "int",
         "default": 0, "required": False, "description": "検索領域の左上Y座標（0=全画面）"},
        {"name": "region_w", "label": "検索領域 幅", "type": "int",
         "default": 0, "required": False, "description": "検索領域の幅（0=全画面）"},
        {"name": "region_h", "label": "検索領域 高さ", "type": "int",
         "default": 0, "required": False, "description": "検索領域の高さ（0=全画面）"},
        {"name": "var_x", "label": "X座標変数名", "type": "string",
         "default": "match_x", "required": False, "description": "見つかったX座標を保存する変数名"},
        {"name": "var_y", "label": "Y座標変数名", "type": "string",
         "default": "match_y", "required": False, "description": "見つかったY座標を保存する変数名"},
        {"name": "var_found", "label": "検出結果変数名", "type": "string",
         "default": "match_found", "required": False, "description": "検出成否(true/false)を保存する変数名"},
        {"name": "highlight", "label": "ハイライト表示", "type": "bool",
         "default": True, "required": False, "description": "検出位置をハイライト表示する"},
        {"name": "save_debug_screenshot", "label": "デバッグスクリーンショット保存", "type": "bool",
         "default": False, "required": False, "description": "失敗時にスクリーンショットを保存する"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        template_name = params.get("template", "")
        if not template_name:
            return ActionResult(
                status=ActionStatus.FAILED,
                error_message="テンプレート画像が指定されていません。",
            )

        confidence = float(params.get("confidence", 0.8))
        grayscale = str(params.get("grayscale", "false")).lower() in ("true", "1", "yes")
        var_x = params.get("var_x", "match_x")
        var_y = params.get("var_y", "match_y")
        var_found = params.get("var_found", "match_found")
        highlight = str(params.get("highlight", "true")).lower() in ("true", "1", "yes")
        save_debug = str(params.get("save_debug_screenshot", "false")).lower() in ("true", "1", "yes")

        # 領域設定
        rx = int(params.get("region_x", 0))
        ry = int(params.get("region_y", 0))
        rw = int(params.get("region_w", 0))
        rh = int(params.get("region_h", 0))
        region = (rx, ry, rw, rh) if (rw > 0 and rh > 0) else None

        try:
            template_path = _resolve_template_path(template_name, context)
            screen = _capture_screen()
            match = _find_template(screen, template_path, confidence, grayscale, region)

            if match:
                cx, cy, score = match
                context.set_variable(var_x, cx)
                context.set_variable(var_y, cy)
                context.set_variable(var_found, "true")
                context.set_variable("match.x", cx)
                context.set_variable("match.y", cy)
                context.set_variable("match.score", round(score, 4))

                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    output=f"画像を検出: ({cx}, {cy}) 類似度={score:.4f}",
                    data={"x": cx, "y": cy, "score": score, "found": True},
                )
            else:
                context.set_variable(var_found, "false")
                context.set_variable("match.x", -1)
                context.set_variable("match.y", -1)
                context.set_variable("match.score", 0.0)

                # デバッグスクリーンショット保存
                if save_debug:
                    self._save_debug_screenshot(screen, context, template_name)

                return ActionResult(
                    status=ActionStatus.FAILED,
                    error_message=f"画像が見つかりません: {template_name} (confidence={confidence})",
                    data={"found": False},
                )

        except FileNotFoundError as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=str(e))
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                error_message=f"画像検索エラー: {e}",
            )

    def _save_debug_screenshot(self, screen_img, context, template_name: str):
        """デバッグ用スクリーンショットを保存する。"""
        try:
            cv2 = _get_cv2()
            base_dir = context.get_variable("_base_dir", ".")
            logs_dir = Path(base_dir) / "logs"
            logs_dir.mkdir(exist_ok=True)
            ts = time.strftime("%Y%m%d_%H%M%S")
            fname = logs_dir / f"debug_{ts}_{Path(template_name).stem}.png"
            bgr = cv2.cvtColor(screen_img, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(fname), bgr)
        except Exception:
            pass


class ImageClickAction(ActionBase):
    ACTION_TYPE = "image.click"
    DISPLAY_NAME = "画像をクリック"
    DESCRIPTION = "テンプレート画像を検索してクリックします。"
    CATEGORY = "画像マッチ"
    ICON = "🖱️"
    PARAMS_SCHEMA = [
        {"name": "template", "label": "テンプレート画像", "type": "template_file",
         "default": "", "required": True, "description": "クリックするテンプレート画像"},
        {"name": "confidence", "label": "類似度", "type": "float",
         "default": 0.8, "min": 0.1, "max": 1.0, "step": 0.05, "required": False},
        {"name": "grayscale", "label": "グレースケール", "type": "bool",
         "default": False, "required": False},
        {"name": "button", "label": "ボタン", "type": "select",
         "options": ["left", "right", "double"],
         "default": "left", "required": False, "description": "クリックボタン"},
        {"name": "offset_x", "label": "Xオフセット", "type": "int",
         "default": 0, "required": False, "description": "クリック位置のXオフセット(px)"},
        {"name": "offset_y", "label": "Yオフセット", "type": "int",
         "default": 0, "required": False, "description": "クリック位置のYオフセット(px)"},
        {"name": "region_x", "label": "検索領域 X", "type": "int", "default": 0, "required": False},
        {"name": "region_y", "label": "検索領域 Y", "type": "int", "default": 0, "required": False},
        {"name": "region_w", "label": "検索領域 幅", "type": "int", "default": 0, "required": False},
        {"name": "region_h", "label": "検索領域 高さ", "type": "int", "default": 0, "required": False},
        {"name": "pre_delay_ms", "label": "クリック前待機(ms)", "type": "int",
         "default": 0, "required": False, "description": "クリック前の待機時間(ms)"},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        template_name = params.get("template", "")
        if not template_name:
            return ActionResult(status=ActionStatus.FAILED, error_message="テンプレート画像が指定されていません。")

        confidence = float(params.get("confidence", 0.8))
        grayscale = str(params.get("grayscale", "false")).lower() in ("true", "1", "yes")
        button = params.get("button", "left")
        offset_x = int(params.get("offset_x", 0))
        offset_y = int(params.get("offset_y", 0))
        pre_delay = int(params.get("pre_delay_ms", 0))

        rx = int(params.get("region_x", 0))
        ry = int(params.get("region_y", 0))
        rw = int(params.get("region_w", 0))
        rh = int(params.get("region_h", 0))
        region = (rx, ry, rw, rh) if (rw > 0 and rh > 0) else None

        try:
            template_path = _resolve_template_path(template_name, context)
            screen = _capture_screen()
            match = _find_template(screen, template_path, confidence, grayscale, region)

            if not match:
                return ActionResult(
                    status=ActionStatus.FAILED,
                    error_message=f"クリック対象の画像が見つかりません: {template_name}",
                )

            cx, cy, score = match
            click_x = cx + offset_x
            click_y = cy + offset_y

            pyautogui = _get_pyautogui()

            if pre_delay > 0:
                time.sleep(pre_delay / 1000.0)

            if button == "double":
                pyautogui.doubleClick(click_x, click_y)
            elif button == "right":
                pyautogui.rightClick(click_x, click_y)
            else:
                pyautogui.click(click_x, click_y)

            context.set_variable("match.x", cx)
            context.set_variable("match.y", cy)
            context.set_variable("match.score", round(score, 4))

            return ActionResult(
                status=ActionStatus.SUCCESS,
                output=f"{button}クリック: ({click_x}, {click_y}) 類似度={score:.4f}",
                data={"x": click_x, "y": click_y, "score": score},
            )

        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=f"画像クリックエラー: {e}")


class ImageWaitAppearAction(ActionBase):
    ACTION_TYPE = "image.wait_appear"
    DISPLAY_NAME = "画像が出現するまで待機"
    DESCRIPTION = "指定した画像が画面に出現するまで待機します。"
    CATEGORY = "画像マッチ"
    ICON = "⏳"
    PARAMS_SCHEMA = [
        {"name": "template", "label": "テンプレート画像", "type": "template_file",
         "default": "", "required": True},
        {"name": "confidence", "label": "類似度", "type": "float",
         "default": 0.8, "min": 0.1, "max": 1.0, "step": 0.05, "required": False},
        {"name": "timeout_sec", "label": "タイムアウト(秒)", "type": "int",
         "default": 30, "min": 1, "max": 300, "required": True,
         "description": "最大待機時間（秒）"},
        {"name": "interval_ms", "label": "チェック間隔(ms)", "type": "int",
         "default": 500, "min": 100, "max": 5000, "required": False,
         "description": "検索間隔（ミリ秒）"},
        {"name": "grayscale", "label": "グレースケール", "type": "bool",
         "default": False, "required": False},
        {"name": "region_x", "label": "検索領域 X", "type": "int", "default": 0, "required": False},
        {"name": "region_y", "label": "検索領域 Y", "type": "int", "default": 0, "required": False},
        {"name": "region_w", "label": "検索領域 幅", "type": "int", "default": 0, "required": False},
        {"name": "region_h", "label": "検索領域 高さ", "type": "int", "default": 0, "required": False},
        {"name": "var_found", "label": "検出結果変数名", "type": "string",
         "default": "wait_found", "required": False},
        {"name": "save_debug_screenshot", "label": "タイムアウト時スクリーンショット保存", "type": "bool",
         "default": True, "required": False},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        template_name = params.get("template", "")
        if not template_name:
            return ActionResult(status=ActionStatus.FAILED, error_message="テンプレート画像が指定されていません。")

        confidence = float(params.get("confidence", 0.8))
        timeout_sec = int(params.get("timeout_sec", 30))
        interval_ms = int(params.get("interval_ms", 500))
        grayscale = str(params.get("grayscale", "false")).lower() in ("true", "1", "yes")
        var_found = params.get("var_found", "wait_found")
        save_debug = str(params.get("save_debug_screenshot", "true")).lower() in ("true", "1", "yes")

        rx = int(params.get("region_x", 0))
        ry = int(params.get("region_y", 0))
        rw = int(params.get("region_w", 0))
        rh = int(params.get("region_h", 0))
        region = (rx, ry, rw, rh) if (rw > 0 and rh > 0) else None

        try:
            template_path = _resolve_template_path(template_name, context)
            start_time = time.time()
            interval_sec = interval_ms / 1000.0
            last_screen = None

            while True:
                elapsed = time.time() - start_time
                if elapsed >= timeout_sec:
                    context.set_variable(var_found, "false")
                    # タイムアウト時のデバッグスクリーンショット
                    if save_debug and last_screen is not None:
                        self._save_debug_screenshot(last_screen, context, template_name)
                    return ActionResult(
                        status=ActionStatus.TIMEOUT,
                        error_message=f"タイムアウト: {template_name} が {timeout_sec}秒以内に出現しませんでした。",
                        data={"found": False},
                    )

                last_screen = _capture_screen()
                match = _find_template(last_screen, template_path, confidence, grayscale, region)

                if match:
                    cx, cy, score = match
                    context.set_variable(var_found, "true")
                    context.set_variable("match.x", cx)
                    context.set_variable("match.y", cy)
                    context.set_variable("match.score", round(score, 4))
                    return ActionResult(
                        status=ActionStatus.SUCCESS,
                        output=f"画像が出現: ({cx}, {cy}) 類似度={score:.4f} 経過={elapsed:.1f}s",
                        data={"x": cx, "y": cy, "score": score, "found": True},
                    )

                time.sleep(interval_sec)

        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=f"待機エラー: {e}")

    def _save_debug_screenshot(self, screen_img, context, template_name: str):
        try:
            cv2 = _get_cv2()
            base_dir = context.get_variable("_base_dir", ".")
            logs_dir = Path(base_dir) / "logs"
            logs_dir.mkdir(exist_ok=True)
            ts = time.strftime("%Y%m%d_%H%M%S")
            fname = logs_dir / f"timeout_{ts}_{Path(template_name).stem}.png"
            bgr = cv2.cvtColor(screen_img, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(fname), bgr)
        except Exception:
            pass


class ImageWaitDisappearAction(ActionBase):
    ACTION_TYPE = "image.wait_disappear"
    DISPLAY_NAME = "画像が消えるまで待機"
    DESCRIPTION = "指定した画像が画面から消えるまで待機します。"
    CATEGORY = "画像マッチ"
    ICON = "👁️"
    PARAMS_SCHEMA = [
        {"name": "template", "label": "テンプレート画像", "type": "template_file",
         "default": "", "required": True},
        {"name": "confidence", "label": "類似度", "type": "float",
         "default": 0.8, "min": 0.1, "max": 1.0, "step": 0.05, "required": False},
        {"name": "timeout_sec", "label": "タイムアウト(秒)", "type": "int",
         "default": 30, "min": 1, "max": 300, "required": True},
        {"name": "interval_ms", "label": "チェック間隔(ms)", "type": "int",
         "default": 500, "min": 100, "max": 5000, "required": False},
        {"name": "grayscale", "label": "グレースケール", "type": "bool",
         "default": False, "required": False},
        {"name": "region_x", "label": "検索領域 X", "type": "int", "default": 0, "required": False},
        {"name": "region_y", "label": "検索領域 Y", "type": "int", "default": 0, "required": False},
        {"name": "region_w", "label": "検索領域 幅", "type": "int", "default": 0, "required": False},
        {"name": "region_h", "label": "検索領域 高さ", "type": "int", "default": 0, "required": False},
        {"name": "var_disappeared", "label": "消滅結果変数名", "type": "string",
         "default": "wait_disappeared", "required": False},
    ]

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        template_name = params.get("template", "")
        if not template_name:
            return ActionResult(status=ActionStatus.FAILED, error_message="テンプレート画像が指定されていません。")

        confidence = float(params.get("confidence", 0.8))
        timeout_sec = int(params.get("timeout_sec", 30))
        interval_ms = int(params.get("interval_ms", 500))
        grayscale = str(params.get("grayscale", "false")).lower() in ("true", "1", "yes")
        var_disappeared = params.get("var_disappeared", "wait_disappeared")

        rx = int(params.get("region_x", 0))
        ry = int(params.get("region_y", 0))
        rw = int(params.get("region_w", 0))
        rh = int(params.get("region_h", 0))
        region = (rx, ry, rw, rh) if (rw > 0 and rh > 0) else None

        try:
            template_path = _resolve_template_path(template_name, context)
            start_time = time.time()
            interval_sec = interval_ms / 1000.0

            while True:
                elapsed = time.time() - start_time
                if elapsed >= timeout_sec:
                    context.set_variable(var_disappeared, "false")
                    return ActionResult(
                        status=ActionStatus.TIMEOUT,
                        error_message=f"タイムアウト: {template_name} が {timeout_sec}秒以内に消えませんでした。",
                        data={"disappeared": False},
                    )

                screen = _capture_screen()
                match = _find_template(screen, template_path, confidence, grayscale, region)

                if not match:
                    context.set_variable(var_disappeared, "true")
                    return ActionResult(
                        status=ActionStatus.SUCCESS,
                        output=f"画像が消滅を確認: 経過={elapsed:.1f}s",
                        data={"disappeared": True},
                    )

                time.sleep(interval_sec)

        except Exception as e:
            return ActionResult(status=ActionStatus.FAILED, error_message=f"待機エラー: {e}")
