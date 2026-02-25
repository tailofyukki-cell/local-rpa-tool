"""
アクション基底クラスモジュール
全アクションが継承する基底クラスと結果クラスを定義する。
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ActionStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RUNNING = "running"
    TIMEOUT = "timeout"


@dataclass
class ActionResult:
    status: ActionStatus = ActionStatus.SUCCESS
    output: str = ""
    error_message: str = ""
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict:
        return {
            "status": self.status.value,
            "output": self.output,
            "error_message": self.error_message,
            "data": self.data or {},
        }


class ActionBase:
    """全アクションの基底クラス。"""
    ACTION_TYPE: str = ""
    DISPLAY_NAME: str = ""
    DESCRIPTION: str = ""
    CATEGORY: str = ""
    ICON: str = ""
    PARAMS_SCHEMA: List[Dict] = []

    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        raise NotImplementedError

    def get_default_params(self) -> Dict[str, Any]:
        """デフォルトパラメータを返す。"""
        defaults = {}
        for schema in self.PARAMS_SCHEMA:
            if "default" in schema:
                defaults[schema["name"]] = schema["default"]
        return defaults
