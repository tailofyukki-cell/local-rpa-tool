"""
フローノードウィジェットモジュール
フロー内の各アクションを表示するノードウィジェット。
ドラッグ並び替え対応。
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QWidget,
)

# カテゴリ別カラー定義
CATEGORY_COLORS = {
    "画像マッチ": "#2196F3",
    "マウス操作": "#4CAF50",
    "キーボード操作": "#FF9800",
    "同期・待機": "#9C27B0",
    "変数・データ": "#00BCD4",
    "条件分岐": "#F44336",
    "スクリーン操作": "#607D8B",
    "その他": "#795548",
}

STATUS_COLORS = {
    "idle": "#455A64",
    "running": "#1565C0",
    "success": "#2E7D32",
    "failed": "#C62828",
    "skipped": "#616161",
    "timeout": "#E65100",
}


class NodeWidget(QFrame):
    """フロー内の1アクションを表すノードウィジェット。"""

    clicked = Signal(object)  # self
    delete_requested = Signal(object)  # self
    duplicate_requested = Signal(object)  # self
    toggle_requested = Signal(object)  # self

    def __init__(self, action_data: dict, index: int, parent=None):
        super().__init__(parent)
        self.action_data = action_data
        self.index = index
        self._status = "idle"
        self._selected = False
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedHeight(56)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # インデックス番号
        self.index_label = QLabel(f"{self.index + 1:02d}")
        self.index_label.setFixedWidth(28)
        self.index_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        self.index_label.setFont(font)
        layout.addWidget(self.index_label)

        # カテゴリカラーバー
        self.color_bar = QFrame()
        self.color_bar.setFixedWidth(4)
        self.color_bar.setFixedHeight(40)
        layout.addWidget(self.color_bar)

        # アイコン
        action_type = self.action_data.get("type", "")
        icon = self._get_icon(action_type)
        self.icon_label = QLabel(icon)
        self.icon_label.setFixedWidth(24)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)

        # 名前と説明
        text_layout = QHBoxLayout()
        text_layout.setSpacing(4)

        self.name_label = QLabel(self.action_data.get("name", action_type))
        font_name = QFont()
        font_name.setPointSize(9)
        font_name.setBold(True)
        self.name_label.setFont(font_name)
        self.name_label.setMinimumWidth(80)
        text_layout.addWidget(self.name_label)

        self.type_label = QLabel(f"[{action_type}]")
        font_type = QFont()
        font_type.setPointSize(8)
        self.type_label.setFont(font_type)
        self.type_label.setStyleSheet("color: #90A4AE;")
        text_layout.addWidget(self.type_label)
        text_layout.addStretch()
        layout.addLayout(text_layout)
        layout.addStretch()

        # 有効/無効トグルボタン
        self.toggle_btn = QPushButton("●" if self.action_data.get("enabled", True) else "○")
        self.toggle_btn.setFixedSize(24, 24)
        self.toggle_btn.setToolTip("有効/無効切替")
        self.toggle_btn.setStyleSheet(
            "QPushButton { border: none; font-size: 14px; color: #4CAF50; background: transparent; }"
            "QPushButton:hover { color: #81C784; }"
        )
        self.toggle_btn.clicked.connect(lambda: self.toggle_requested.emit(self))
        layout.addWidget(self.toggle_btn)

        # 複製ボタン
        self.dup_btn = QPushButton("⧉")
        self.dup_btn.setFixedSize(24, 24)
        self.dup_btn.setToolTip("複製")
        self.dup_btn.setStyleSheet(
            "QPushButton { border: none; font-size: 14px; color: #90A4AE; background: transparent; }"
            "QPushButton:hover { color: #CFD8DC; }"
        )
        self.dup_btn.clicked.connect(lambda: self.duplicate_requested.emit(self))
        layout.addWidget(self.dup_btn)

        # 削除ボタン
        self.del_btn = QPushButton("✕")
        self.del_btn.setFixedSize(24, 24)
        self.del_btn.setToolTip("削除")
        self.del_btn.setStyleSheet(
            "QPushButton { border: none; font-size: 14px; color: #EF9A9A; background: transparent; }"
            "QPushButton:hover { color: #EF5350; }"
        )
        self.del_btn.clicked.connect(lambda: self.delete_requested.emit(self))
        layout.addWidget(self.del_btn)

    def _get_icon(self, action_type: str) -> str:
        icon_map = {
            "image.find": "🔍",
            "image.click": "🖱️",
            "image.wait_appear": "⏳",
            "image.wait_disappear": "👁️",
            "mouse.click": "🖱️",
            "mouse.move": "↗️",
            "mouse.drag": "✋",
            "mouse.scroll": "🖱️",
            "key.type": "⌨️",
            "key.press": "⌨️",
            "key.hotkey": "⌨️",
            "wait.sleep": "⏱️",
            "wait.color": "🎨",
            "wait.window": "🪟",
            "variable.set": "📝",
            "variable.get_date": "📅",
            "variable.math": "🔢",
            "condition.if": "🔀",
            "condition.endif": "🔚",
            "screen.screenshot": "📷",
            "screen.get_pixel": "🎨",
        }
        return icon_map.get(action_type, "⚙️")

    def _get_category(self, action_type: str) -> str:
        category_map = {
            "image": "画像マッチ",
            "mouse": "マウス操作",
            "key": "キーボード操作",
            "wait": "同期・待機",
            "variable": "変数・データ",
            "condition": "条件分岐",
            "screen": "スクリーン操作",
        }
        prefix = action_type.split(".")[0] if "." in action_type else ""
        return category_map.get(prefix, "その他")

    def _apply_style(self):
        action_type = self.action_data.get("type", "")
        category = self._get_category(action_type)
        color = CATEGORY_COLORS.get(category, "#795548")
        status_color = STATUS_COLORS.get(self._status, "#455A64")

        enabled = self.action_data.get("enabled", True)
        opacity = "1.0" if enabled else "0.5"

        if self._selected:
            border_color = "#64B5F6"
            bg_color = "#1A237E"
        else:
            border_color = status_color
            bg_color = "#263238"

        self.setStyleSheet(f"""
            NodeWidget {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                opacity: {opacity};
            }}
        """)

        self.color_bar.setStyleSheet(
            f"background-color: {color}; border-radius: 2px;"
        )

        # 無効時はグレーアウト
        if not enabled:
            self.name_label.setStyleSheet("color: #607D8B;")
            self.toggle_btn.setText("○")
            self.toggle_btn.setStyleSheet(
                "QPushButton { border: none; font-size: 14px; color: #607D8B; background: transparent; }"
            )
        else:
            self.name_label.setStyleSheet("color: #ECEFF1;")
            self.toggle_btn.setText("●")
            self.toggle_btn.setStyleSheet(
                "QPushButton { border: none; font-size: 14px; color: #4CAF50; background: transparent; }"
                "QPushButton:hover { color: #81C784; }"
            )

    def set_status(self, status: str):
        """実行ステータスを設定する。"""
        self._status = status
        self._apply_style()

    def set_selected(self, selected: bool):
        """選択状態を設定する。"""
        self._selected = selected
        self._apply_style()

    def update_index(self, index: int):
        """インデックスを更新する。"""
        self.index = index
        self.index_label.setText(f"{index + 1:02d}")

    def update_data(self, action_data: dict):
        """アクションデータを更新する。"""
        self.action_data = action_data
        self.name_label.setText(action_data.get("name", action_data.get("type", "")))
        self.type_label.setText(f"[{action_data.get('type', '')}]")
        self._apply_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self)
        super().mousePressEvent(event)
