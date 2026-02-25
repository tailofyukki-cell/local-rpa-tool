"""
実行コンテキストモジュール
フロー実行中の変数管理とテンプレート展開を担当する。
"""
import re
from typing import Any, Dict, Optional


class ExecutionContext:
    """フロー実行中の変数を管理するクラス。"""

    def __init__(self):
        self._variables: Dict[str, Any] = {}
        self._step_results: Dict[str, Dict] = {}

    def set_variable(self, name: str, value: Any):
        """変数を設定する。"""
        self._variables[name] = value

    def get_variable(self, name: str, default: Any = None) -> Any:
        """変数を取得する。"""
        return self._variables.get(name, default)

    def set_step_result(self, step_id: str, result: Dict):
        """ステップの実行結果を保存する。"""
        self._step_results[step_id] = result

    def get_step_result(self, step_id: str) -> Optional[Dict]:
        """ステップの実行結果を取得する。"""
        return self._step_results.get(step_id)

    def expand_template(self, text: str) -> str:
        """
        テンプレート文字列を展開する。
        {{varName}} → 変数値
        {{stepId.field}} → ステップ結果のフィールド値
        """
        if not isinstance(text, str):
            return text

        def replace_match(m):
            key = m.group(1).strip()
            # ドット記法のステップ参照
            if "." in key:
                parts = key.split(".", 1)
                step_id = parts[0]
                field = parts[1]
                result = self._step_results.get(step_id, {})
                val = result.get(field, m.group(0))
                return str(val)
            # 通常変数
            val = self._variables.get(key, m.group(0))
            return str(val)

        return re.sub(r"\{\{([^}]+)\}\}", replace_match, text)

    def expand_params(self, params: Dict) -> Dict:
        """パラメータ辞書内の全テンプレートを展開する。"""
        expanded = {}
        for k, v in params.items():
            if isinstance(v, str):
                expanded[k] = self.expand_template(v)
            elif isinstance(v, dict):
                expanded[k] = self.expand_params(v)
            elif isinstance(v, list):
                expanded[k] = [
                    self.expand_template(item) if isinstance(item, str) else item
                    for item in v
                ]
            else:
                expanded[k] = v
        return expanded

    def get_all_variables(self) -> Dict[str, Any]:
        """全変数を返す。"""
        return dict(self._variables)
