"""
フロー実行エンジンモジュール
フローJSONを読み込み、アクションを順番に実行する。
安全対策（フェイルセーフ・緊急停止）を含む。
"""
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src.core.action_base import ActionResult, ActionStatus
from src.core.context import ExecutionContext
from src.core.dispatcher import ActionDispatcher


class FlowEngine:
    """
    フロー実行エンジン。
    画像マッチRPAフローを実行し、安全対策を提供する。
    """

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.flows_dir = self.base_dir / "flows"
        self.logs_dir = self.base_dir / "logs"
        self.data_dir = self.base_dir / "data"
        self.templates_dir = self.base_dir / "templates"
        self._ensure_dirs()

        self.dispatcher = ActionDispatcher()
        self._is_running = False
        self._stop_requested = False

        # コールバック関数
        self.on_step_start: Optional[Callable[[int, Dict], None]] = None
        self.on_step_complete: Optional[Callable[[int, Dict, ActionResult], None]] = None
        self.on_flow_complete: Optional[Callable[[bool, str], None]] = None
        self.on_log: Optional[Callable[[str], None]] = None

    def _ensure_dirs(self):
        """必要なディレクトリを作成する。"""
        for d in [self.flows_dir, self.logs_dir, self.data_dir, self.templates_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def load_flow(self, flow_path: str) -> Dict:
        """フローJSONファイルを読み込む。"""
        with open(flow_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_flow(self, flow_data: Dict, flow_path: str):
        """フローJSONをファイルに保存する。"""
        with open(flow_path, "w", encoding="utf-8") as f:
            json.dump(flow_data, f, ensure_ascii=False, indent=2)

    def stop(self):
        """実行中のフローを停止する。"""
        self._stop_requested = True

    def is_running(self) -> bool:
        """フローが実行中かどうかを返す。"""
        return self._is_running

    def _log(self, message: str):
        """ログメッセージを発行する。"""
        if self.on_log:
            self.on_log(message)

    def run_flow(self, flow_data: Dict) -> List[Dict]:
        """
        フローを実行する。

        Args:
            flow_data: フローのデータ辞書。

        Returns:
            各ステップの実行結果リスト。
        """
        self._is_running = True
        self._stop_requested = False
        context = ExecutionContext()
        # テンプレートディレクトリをコンテキストに設定
        context.set_variable("_templates_dir", str(self.templates_dir))
        context.set_variable("_base_dir", str(self.base_dir))

        actions = flow_data.get("actions", [])
        flow_name = flow_data.get("name", "unnamed_flow")
        results: List[Dict] = []

        # ログファイルのセットアップ
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(
            c if c.isalnum() or c in "_- " else "_" for c in flow_name
        ).strip()
        log_filename = f"{timestamp}_{safe_name}.log"
        log_path = self.logs_dir / log_filename
        log_lines: List[str] = []

        def write_log(msg: str):
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            line = f"[{ts}] {msg}"
            log_lines.append(line)
            self._log(line)

        write_log(f"=== フロー開始: {flow_name} ===")
        write_log(f"アクション数: {len(actions)}")

        # IF条件のスキップ管理スタック
        skip_stack: List[bool] = []

        try:
            for i, action in enumerate(actions):
                # 停止要求チェック
                if self._stop_requested:
                    write_log("--- 実行が停止されました ---")
                    break

                action_id = action.get("id", f"step_{i}")
                action_type = action.get("type", "")
                action_name = action.get("name", action_type)
                params = action.get("params", {})
                enabled = action.get("enabled", True)

                # ENDIFはスキップ中でも処理する
                if action_type == "condition.endif":
                    if skip_stack:
                        skip_stack.pop()
                    result = ActionResult(status=ActionStatus.SUCCESS, output="ENDIF処理")
                    context.set_step_result(action_id, result.to_dict())
                    results.append({"index": i, "action": action, "result": result})
                    if self.on_step_complete:
                        self.on_step_complete(i, action, result)
                    write_log(f"[{i+1}/{len(actions)}] ENDIF: {action_name}")
                    continue

                # スキップ中の場合
                if skip_stack and skip_stack[-1]:
                    result = ActionResult(status=ActionStatus.SKIPPED, output="条件分岐によりスキップ")
                    context.set_step_result(action_id, result.to_dict())
                    results.append({"index": i, "action": action, "result": result})
                    if self.on_step_complete:
                        self.on_step_complete(i, action, result)
                    write_log(f"[{i+1}/{len(actions)}] スキップ: {action_name}")
                    continue

                # 無効なアクションはスキップ
                if not enabled:
                    result = ActionResult(status=ActionStatus.SKIPPED, output="無効化されています")
                    context.set_step_result(action_id, result.to_dict())
                    results.append({"index": i, "action": action, "result": result})
                    if self.on_step_complete:
                        self.on_step_complete(i, action, result)
                    write_log(f"[{i+1}/{len(actions)}] 無効: {action_name}")
                    continue

                # ステップ開始
                if self.on_step_start:
                    self.on_step_start(i, action)
                write_log(f"[{i+1}/{len(actions)}] 開始: {action_name} (type={action_type})")
                start_time = time.time()

                # アクション実行
                try:
                    result = self.dispatcher.execute(action_type, params, context)
                except Exception as e:
                    result = ActionResult(
                        status=ActionStatus.FAILED,
                        error_message=f"予期しないエラー: {e}",
                    )

                elapsed = time.time() - start_time
                context.set_step_result(action_id, result.to_dict())

                # IF条件の結果を処理
                if action_type == "condition.if":
                    condition_met = result.data.get("condition_met", False) if result.data else False
                    skip_stack.append(not condition_met)
                    if result.data is not None:
                        result = ActionResult(
                            status=ActionStatus.SUCCESS,
                            output=result.output,
                            data=result.data,
                        )
                    write_log(
                        f"[{i+1}/{len(actions)}] IF条件: {action_name} -> "
                        f"{'TRUE (実行)' if condition_met else 'FALSE (スキップ)'} ({elapsed:.3f}s)"
                    )
                else:
                    write_log(
                        f"[{i+1}/{len(actions)}] 完了: {action_name} -> "
                        f"{result.status.value} ({elapsed:.3f}s)"
                    )

                if result.error_message:
                    write_log(f"  エラー: {result.error_message}")
                if result.output:
                    write_log(f"  出力: {result.output}")

                results.append({"index": i, "action": action, "result": result})

                if self.on_step_complete:
                    self.on_step_complete(i, action, result)

                # タイムアウト・エラー時は停止
                if result.status in (ActionStatus.FAILED, ActionStatus.TIMEOUT):
                    write_log(f"--- エラー/タイムアウトにより実行を停止します ---")
                    break

        finally:
            write_log(f"=== フロー終了: {flow_name} ===")
            self._is_running = False

            # ログファイルに書き出す
            try:
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(log_lines))
            except Exception as e:
                self._log(f"ログファイルの保存に失敗しました: {e}")

            success = all(
                r["result"].status in (ActionStatus.SUCCESS, ActionStatus.SKIPPED)
                for r in results
            )
            if self.on_flow_complete:
                self.on_flow_complete(success, str(log_path))

        return results
