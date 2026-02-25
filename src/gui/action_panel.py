"""
アクション一覧パネルモジュール
カテゴリ別にアクションを表示し、フローへの追加を提供する。
"""
from typing import Callable, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class ActionItemButton(QPushButton):
    """アクション一覧の各アイテムボタン。"""

    def __init__(self, action_class, parent=None):
        super().__init__(parent)
        self.action_class = action_class
        icon = getattr(action_class, "ICON", "⚙️")
        name = getattr(action_class, "DISPLAY_NAME", action_class.ACTION_TYPE)
        self.setText(f"{icon}  {name}")
        self.setToolTip(getattr(action_class, "DESCRIPTION", ""))
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 6px 10px;
                background-color: #263238;
                color: #ECEFF1;
                border: 1px solid #37474F;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #37474F;
                border-color: #546E7A;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(30)


class ActionPanel(QWidget):
    """アクション一覧パネル。カテゴリ別にアクションを表示する。"""

    action_add_requested = Signal(dict)  # 追加するアクションデータ

    def __init__(self, dispatcher, parent=None):
        super().__init__(parent)
        self.dispatcher = dispatcher
        self._setup_ui()
        self._populate_actions()

    def _setup_ui(self):
        self.setFixedWidth(200)
        self.setStyleSheet("background-color: #1A2332;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ヘッダー
        header = QLabel("アクション一覧")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFixedHeight(36)
        header.setStyleSheet("""
            background-color: #0D1B2A;
            color: #90CAF9;
            font-size: 12px;
            font-weight: bold;
            border-bottom: 1px solid #263238;
            padding: 4px;
        """)
        main_layout.addWidget(header)

        # スクロールエリア
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background-color: #1A2332; }
            QScrollBar:vertical { background: #1A2332; width: 6px; }
            QScrollBar::handle:vertical { background: #455A64; border-radius: 3px; }
        """)

        self._content = QWidget()
        self._content.setStyleSheet("background-color: #1A2332;")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(6, 6, 6, 6)
        self._content_layout.setSpacing(4)
        self._content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self._content)
        main_layout.addWidget(scroll)

    def _populate_actions(self):
        """アクションをカテゴリ別に表示する。"""
        categories = self.dispatcher.get_categories()
        # カテゴリ順序
        order = ["画像マッチ", "マウス操作", "キーボード操作", "同期・待機",
                 "変数・データ", "条件分岐", "スクリーン操作", "その他"]

        for cat in order:
            if cat not in categories:
                continue
            actions = categories[cat]

            # カテゴリヘッダー
            cat_label = QLabel(f"▶ {cat}")
            cat_label.setStyleSheet("""
                color: #64B5F6;
                font-size: 10px;
                font-weight: bold;
                padding: 4px 2px 2px 2px;
                border-bottom: 1px solid #263238;
            """)
            self._content_layout.addWidget(cat_label)

            # アクションボタン
            for action_class in sorted(actions, key=lambda a: a.DISPLAY_NAME):
                btn = ActionItemButton(action_class)
                btn.clicked.connect(
                    lambda checked=False, ac=action_class: self._on_action_clicked(ac)
                )
                self._content_layout.addWidget(btn)

        self._content_layout.addStretch()

    def _on_action_clicked(self, action_class):
        """アクションボタンがクリックされた時の処理。"""
        import uuid
        default_params = action_class().get_default_params()
        action_data = {
            "id": str(uuid.uuid4())[:8],
            "type": action_class.ACTION_TYPE,
            "name": action_class.DISPLAY_NAME,
            "params": default_params,
            "enabled": True,
        }
        self.action_add_requested.emit(action_data)
