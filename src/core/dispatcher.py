"""
アクションディスパッチャーモジュール
アクションタイプ文字列に基づいて対応するアクションクラスを管理・実行する。
"""
from typing import Dict, List, Optional, Type

from src.core.action_base import ActionBase, ActionResult, ActionStatus
from src.core.context import ExecutionContext


class ActionDispatcher:
    """アクションの登録と実行を管理するクラス。"""

    def __init__(self):
        self._registry: Dict[str, Type[ActionBase]] = {}
        self._register_all_actions()

    def _register_all_actions(self):
        """全アクションモジュールをインポートして登録する。"""
        # 画像マッチアクション
        from src.actions.image_actions import (
            ImageFindAction,
            ImageClickAction,
            ImageWaitAppearAction,
            ImageWaitDisappearAction,
        )
        # マウスアクション
        from src.actions.mouse_actions import (
            MouseClickAction,
            MouseMoveAction,
            MouseDragAction,
            MouseScrollAction,
        )
        # キーボードアクション
        from src.actions.keyboard_actions import (
            KeyTypeAction,
            KeyPressAction,
            KeyHotkeyAction,
        )
        # 同期・待機アクション
        from src.actions.wait_actions import (
            WaitAction,
            WaitColorAction,
            WaitWindowAction,
        )
        # 変数・条件アクション
        from src.actions.variable_actions import (
            SetVariableAction,
            GetDateAction,
            MathCalcAction,
        )
        from src.actions.condition_actions import (
            IfConditionAction,
            EndIfAction,
        )
        # スクリーンショットアクション
        from src.actions.screen_actions import (
            ScreenshotAction,
            GetPixelColorAction,
        )

        all_actions = [
            ImageFindAction,
            ImageClickAction,
            ImageWaitAppearAction,
            ImageWaitDisappearAction,
            MouseClickAction,
            MouseMoveAction,
            MouseDragAction,
            MouseScrollAction,
            KeyTypeAction,
            KeyPressAction,
            KeyHotkeyAction,
            WaitAction,
            WaitColorAction,
            WaitWindowAction,
            SetVariableAction,
            GetDateAction,
            MathCalcAction,
            IfConditionAction,
            EndIfAction,
            ScreenshotAction,
            GetPixelColorAction,
        ]

        for action_class in all_actions:
            self.register(action_class)

    def register(self, action_class: Type[ActionBase]):
        """アクションクラスを登録する。"""
        if not action_class.ACTION_TYPE:
            raise ValueError(f"ACTION_TYPE が未設定: {action_class.__name__}")
        self._registry[action_class.ACTION_TYPE] = action_class

    def get_action_class(self, action_type: str) -> Optional[Type[ActionBase]]:
        """アクションタイプに対応するクラスを返す。"""
        return self._registry.get(action_type)

    def execute(self, action_type: str, params: Dict, context: ExecutionContext) -> ActionResult:
        """アクションを実行する。"""
        action_class = self.get_action_class(action_type)
        if action_class is None:
            return ActionResult(
                status=ActionStatus.FAILED,
                error_message=f"不明なアクションタイプ: '{action_type}'",
            )
        action_instance = action_class()
        expanded_params = context.expand_params(params)
        return action_instance.execute(expanded_params, context)

    def get_all_action_classes(self) -> List[Type[ActionBase]]:
        """登録されている全アクションクラスのリストを返す。"""
        return list(self._registry.values())

    def get_categories(self) -> Dict[str, List[Type[ActionBase]]]:
        """カテゴリ別にアクションを分類して返す。"""
        categories: Dict[str, List[Type[ActionBase]]] = {}
        for action_class in self._registry.values():
            cat = action_class.CATEGORY or "その他"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(action_class)
        return categories
