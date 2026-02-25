"""
ログパネルウィジェットモジュール
フロー実行ログをリアルタイムで表示する。
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class LogPanel(QWidget):
    """実行ログ表示パネル。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedHeight(180)
        self.setStyleSheet("background-color: #0D1117;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ヘッダー
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(8, 4, 8, 4)
        header = QLabel("実行ログ")
        header.setStyleSheet("color: #90CAF9; font-size: 11px; font-weight: bold;")
        header_layout.addWidget(header)
        header_layout.addStretch()

        clear_btn = QPushButton("クリア")
        clear_btn.setFixedSize(50, 20)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #263238;
                color: #90A4AE;
                border: 1px solid #37474F;
                border-radius: 3px;
                font-size: 10px;
            }
            QPushButton:hover { background-color: #37474F; }
        """)
        clear_btn.clicked.connect(self.clear_log)
        header_layout.addWidget(clear_btn)

        header_widget = QWidget()
        header_widget.setFixedHeight(28)
        header_widget.setStyleSheet(
            "background-color: #161B22; border-bottom: 1px solid #21262D;"
        )
        header_widget.setLayout(header_layout)
        layout.addWidget(header_widget)

        # ログテキストエリア
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0D1117;
                color: #C9D1D9;
                border: none;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                padding: 4px;
            }
        """)
        layout.addWidget(self._log_text)

    def append_log(self, message: str):
        """ログメッセージを追加する。"""
        cursor = self._log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        fmt = QTextCharFormat()

        # メッセージの種類に応じて色を変える
        msg_lower = message.lower()
        if "エラー" in message or "failed" in msg_lower or "error" in msg_lower:
            fmt.setForeground(QColor("#FF7B72"))
        elif "タイムアウト" in message or "timeout" in msg_lower:
            fmt.setForeground(QColor("#FFA657"))
        elif "スキップ" in message or "skipped" in msg_lower:
            fmt.setForeground(QColor("#8B949E"))
        elif "完了" in message or "success" in msg_lower or "開始" in message:
            fmt.setForeground(QColor("#7EE787"))
        elif "=== フロー" in message:
            fmt.setForeground(QColor("#79C0FF"))
            font = QFont()
            font.setBold(True)
            fmt.setFont(font)
        elif "if条件" in msg_lower or "true" in msg_lower or "false" in msg_lower:
            fmt.setForeground(QColor("#D2A8FF"))
        else:
            fmt.setForeground(QColor("#C9D1D9"))

        cursor.insertText(message + "\n", fmt)
        self._log_text.setTextCursor(cursor)
        self._log_text.ensureCursorVisible()

    def clear_log(self):
        """ログをクリアする。"""
        self._log_text.clear()

    def get_log_text(self) -> str:
        """ログテキスト全体を返す。"""
        return self._log_text.toPlainText()
