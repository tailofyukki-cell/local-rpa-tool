"""
フローエディタウィジェットモジュール
ノードの追加・削除・複製・ドラッグ並び替えを提供する。
"""
import uuid
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.gui.node_widget import NodeWidget


class FlowEditor(QScrollArea):
    """フローのノード一覧を表示・編集するウィジェット。"""

    node_selected = Signal(dict)  # 選択されたアクションデータ
    flow_changed = Signal()  # フロー変更通知

    def __init__(self, parent=None):
        super().__init__(parent)
        self._nodes: List[NodeWidget] = []
        self._selected_node: Optional[NodeWidget] = None
        self._drag_node: Optional[NodeWidget] = None
        self._drag_start_y: int = 0
        self._setup_ui()

    def _setup_ui(self):
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("""
            QScrollArea {
                background-color: #1C2833;
                border: none;
            }
            QScrollBar:vertical {
                background: #1C2833;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: #455A64;
                border-radius: 4px;
            }
        """)

        self._container = QWidget()
        self._container.setStyleSheet("background-color: #1C2833;")
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(4)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 空のプレースホルダー
        self._placeholder = QLabel(
            "← アクション一覧からドラッグ、または\n「追加」ボタンでアクションを追加してください"
        )
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("color: #546E7A; font-size: 12px; padding: 40px;")
        self._layout.addWidget(self._placeholder)
        self._layout.addStretch()

        self.setWidget(self._container)

    def _update_placeholder(self):
        """ノードが0件の場合はプレースホルダーを表示する。"""
        if len(self._nodes) == 0:
            self._placeholder.setVisible(True)
        else:
            self._placeholder.setVisible(False)

    def add_action(self, action_data: dict, index: int = -1):
        """アクションをフローに追加する。"""
        if "id" not in action_data:
            action_data["id"] = str(uuid.uuid4())[:8]
        if "enabled" not in action_data:
            action_data["enabled"] = True

        node = NodeWidget(action_data, len(self._nodes))
        node.clicked.connect(self._on_node_clicked)
        node.delete_requested.connect(self._on_delete_node)
        node.duplicate_requested.connect(self._on_duplicate_node)
        node.toggle_requested.connect(self._on_toggle_node)

        if index < 0 or index >= len(self._nodes):
            self._nodes.append(node)
            # stretchの前に挿入
            self._layout.insertWidget(self._layout.count() - 1, node)
        else:
            self._nodes.insert(index, node)
            self._layout.insertWidget(index, node)

        self._reindex_nodes()
        self._update_placeholder()
        self.flow_changed.emit()
        return node

    def _on_node_clicked(self, node: NodeWidget):
        """ノードがクリックされた時の処理。"""
        if self._selected_node:
            self._selected_node.set_selected(False)
        self._selected_node = node
        node.set_selected(True)
        self.node_selected.emit(node.action_data)

    def _on_delete_node(self, node: NodeWidget):
        """ノードを削除する。"""
        if node in self._nodes:
            self._nodes.remove(node)
            self._layout.removeWidget(node)
            node.deleteLater()
            if self._selected_node == node:
                self._selected_node = None
                self.node_selected.emit({})
            self._reindex_nodes()
            self._update_placeholder()
            self.flow_changed.emit()

    def _on_duplicate_node(self, node: NodeWidget):
        """ノードを複製する。"""
        import copy
        new_data = copy.deepcopy(node.action_data)
        new_data["id"] = str(uuid.uuid4())[:8]
        new_data["name"] = new_data.get("name", "") + " (コピー)"
        idx = self._nodes.index(node) + 1
        self.add_action(new_data, idx)

    def _on_toggle_node(self, node: NodeWidget):
        """ノードの有効/無効を切り替える。"""
        node.action_data["enabled"] = not node.action_data.get("enabled", True)
        node.update_data(node.action_data)
        self.flow_changed.emit()

    def _reindex_nodes(self):
        """全ノードのインデックスを再設定する。"""
        for i, node in enumerate(self._nodes):
            node.update_index(i)

    def get_flow_actions(self) -> List[dict]:
        """現在のフローのアクションリストを返す。"""
        return [node.action_data for node in self._nodes]

    def load_flow(self, actions: List[dict]):
        """フローをロードする。"""
        self.clear_flow()
        for action in actions:
            self.add_action(action)

    def clear_flow(self):
        """フローをクリアする。"""
        for node in self._nodes[:]:
            self._layout.removeWidget(node)
            node.deleteLater()
        self._nodes.clear()
        self._selected_node = None
        self._update_placeholder()

    def get_selected_node(self) -> Optional[NodeWidget]:
        """選択中のノードを返す。"""
        return self._selected_node

    def set_node_status(self, index: int, status: str):
        """指定インデックスのノードのステータスを設定する。"""
        if 0 <= index < len(self._nodes):
            self._nodes[index].set_status(status)
            # 実行中のノードが見えるようにスクロール
            if status == "running":
                self.ensureWidgetVisible(self._nodes[index])

    def reset_all_statuses(self):
        """全ノードのステータスをリセットする。"""
        for node in self._nodes:
            node.set_status("idle")

    def update_selected_node_data(self, action_data: dict):
        """選択中ノードのデータを更新する。"""
        if self._selected_node:
            self._selected_node.action_data.update(action_data)
            self._selected_node.update_data(self._selected_node.action_data)
            self.flow_changed.emit()

    # ドラッグ&ドロップによる並び替え
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            widget = self._container.childAt(
                self._container.mapFromGlobal(event.globalPosition().toPoint())
            )
            # NodeWidgetかその子ウィジェットを探す
            node = self._find_node_at(event.globalPosition().toPoint())
            if node:
                self._drag_node = node
                self._drag_start_y = event.globalPosition().toPoint().y()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_node and event.buttons() & Qt.MouseButton.LeftButton:
            current_y = event.globalPosition().toPoint().y()
            delta = current_y - self._drag_start_y
            if abs(delta) > 20:
                self._drag_start_y = current_y
                current_idx = self._nodes.index(self._drag_node)
                if delta < 0 and current_idx > 0:
                    self._swap_nodes(current_idx, current_idx - 1)
                elif delta > 0 and current_idx < len(self._nodes) - 1:
                    self._swap_nodes(current_idx, current_idx + 1)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._drag_node:
            self._drag_node = None
            self.flow_changed.emit()
        super().mouseReleaseEvent(event)

    def _find_node_at(self, global_pos) -> Optional[NodeWidget]:
        """グローバル座標にあるNodeWidgetを返す。"""
        for node in self._nodes:
            local_pos = node.mapFromGlobal(global_pos)
            if node.rect().contains(local_pos):
                return node
        return None

    def _swap_nodes(self, idx1: int, idx2: int):
        """2つのノードを入れ替える。"""
        self._nodes[idx1], self._nodes[idx2] = self._nodes[idx2], self._nodes[idx1]
        # レイアウトでも入れ替え
        w1 = self._nodes[idx1]
        w2 = self._nodes[idx2]
        self._layout.removeWidget(w1)
        self._layout.removeWidget(w2)
        if idx1 < idx2:
            self._layout.insertWidget(idx1, w1)
            self._layout.insertWidget(idx2, w2)
        else:
            self._layout.insertWidget(idx1, w2)
            self._layout.insertWidget(idx2, w1)
        self._reindex_nodes()
