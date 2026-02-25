"""
メインウィンドウモジュール
Power Automate風レイアウト（左:アクション一覧、中央:フロー、右:設定）を提供する。
安全対策・緊急停止・テンプレート管理を含む。
"""
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Qt, Signal, QTimer
from PySide6.QtGui import QAction, QFont, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.core.dispatcher import ActionDispatcher
from src.core.engine import FlowEngine
from src.gui.action_panel import ActionPanel
from src.gui.flow_editor import FlowEditor
from src.gui.log_panel import LogPanel
from src.gui.settings_panel import SettingsPanel


def get_base_dir() -> str:
    """exeまたはスクリプトと同じディレクトリを返す。"""
    if getattr(sys, "frozen", False):
        return str(Path(sys.executable).parent)
    return str(Path(__file__).parent.parent.parent)


class FlowRunThread(QThread):
    """フローを別スレッドで実行するクラス。"""
    step_started = Signal(int, dict)
    step_completed = Signal(int, dict, object)
    flow_completed = Signal(bool, str)
    log_message = Signal(str)

    def __init__(self, engine: FlowEngine, flow_data: dict, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.flow_data = flow_data

    def run(self):
        self.engine.on_step_start = lambda i, a: self.step_started.emit(i, a)
        self.engine.on_step_complete = lambda i, a, r: self.step_completed.emit(i, a, r)
        self.engine.on_flow_complete = lambda s, p: self.flow_completed.emit(s, p)
        self.engine.on_log = lambda m: self.log_message.emit(m)
        self.engine.run_flow(self.flow_data)


class MainWindow(QMainWindow):
    """メインウィンドウ。"""

    def __init__(self):
        super().__init__()
        self.base_dir = get_base_dir()
        self.engine = FlowEngine(self.base_dir)
        self.dispatcher = ActionDispatcher()
        self._current_flow_path: Optional[str] = None
        self._flow_modified = False
        self._run_thread: Optional[FlowRunThread] = None
        self._failsafe_timer: Optional[QTimer] = None

        self._setup_ui()
        self._setup_menu()
        self._setup_shortcuts()
        self._setup_failsafe_monitor()
        self._update_title()

    def _setup_ui(self):
        self.setWindowTitle("LocalRPA - 画像マッチ自動化ツール")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        self.setStyleSheet("""
            QMainWindow { background-color: #0D1B2A; }
            QToolBar {
                background-color: #0D1B2A;
                border-bottom: 1px solid #1E3A5F;
                spacing: 4px;
                padding: 2px 8px;
            }
            QStatusBar {
                background-color: #0D1B2A;
                color: #90A4AE;
                font-size: 10px;
                border-top: 1px solid #1E3A5F;
            }
            QSplitter::handle { background-color: #1E3A5F; width: 2px; }
        """)

        # ツールバー
        toolbar = QToolBar("メインツールバー")
        toolbar.setMovable(False)
        toolbar.setIconSize(__import__("PySide6.QtCore", fromlist=["QSize"]).QSize(20, 20))
        self.addToolBar(toolbar)

        # フロー名ラベル
        self._flow_name_label = QLabel("新しいフロー")
        self._flow_name_label.setStyleSheet(
            "color: #90CAF9; font-size: 13px; font-weight: bold; padding: 0 12px;"
        )
        toolbar.addWidget(self._flow_name_label)
        toolbar.addSeparator()

        # ツールバーボタン
        btn_style = """
            QPushButton {
                background-color: #1E3A5F;
                color: #ECEFF1;
                border: 1px solid #2E5F8A;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
                min-width: 60px;
            }
            QPushButton:hover { background-color: #2E5F8A; }
            QPushButton:pressed { background-color: #0D47A1; }
            QPushButton:disabled { background-color: #263238; color: #546E7A; }
        """

        self._btn_new = QPushButton("📄 新規")
        self._btn_new.setStyleSheet(btn_style)
        self._btn_new.clicked.connect(self._new_flow)
        toolbar.addWidget(self._btn_new)

        self._btn_open = QPushButton("📂 開く")
        self._btn_open.setStyleSheet(btn_style)
        self._btn_open.clicked.connect(self._open_flow)
        toolbar.addWidget(self._btn_open)

        self._btn_save = QPushButton("💾 保存")
        self._btn_save.setStyleSheet(btn_style)
        self._btn_save.clicked.connect(self._save_flow)
        toolbar.addWidget(self._btn_save)

        toolbar.addSeparator()

        run_style = btn_style.replace("#1E3A5F", "#1B5E20").replace("#2E5F8A", "#2E7D32").replace("#0D47A1", "#1B5E20").replace("#2E5F8A", "#388E3C")
        self._btn_run = QPushButton("▶ 実行")
        self._btn_run.setStyleSheet(run_style)
        self._btn_run.clicked.connect(self._run_flow)
        toolbar.addWidget(self._btn_run)

        stop_style = btn_style.replace("#1E3A5F", "#7F0000").replace("#2E5F8A", "#B71C1C").replace("#0D47A1", "#7F0000")
        self._btn_stop = QPushButton("⏹ 停止")
        self._btn_stop.setStyleSheet(stop_style)
        self._btn_stop.setEnabled(False)
        self._btn_stop.clicked.connect(self._stop_flow)
        toolbar.addWidget(self._btn_stop)

        toolbar.addSeparator()

        self._btn_templates = QPushButton("🖼 テンプレート管理")
        self._btn_templates.setStyleSheet(btn_style)
        self._btn_templates.clicked.connect(self._open_template_manager)
        toolbar.addWidget(self._btn_templates)

        # ステータスバー
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_label = QLabel("準備完了")
        self._status_bar.addWidget(self._status_label)
        self._failsafe_label = QLabel("🛡 フェイルセーフ: 有効")
        self._failsafe_label.setStyleSheet("color: #4CAF50; font-size: 10px;")
        self._status_bar.addPermanentWidget(self._failsafe_label)

        # メインレイアウト
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # スプリッター（左:アクション一覧、中央:フロー、右:設定）
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # 左パネル：アクション一覧
        self._action_panel = ActionPanel(self.dispatcher)
        self._action_panel.action_add_requested.connect(self._on_add_action)
        splitter.addWidget(self._action_panel)

        # 中央パネル：フローエディタ
        center_widget = QWidget()
        center_widget.setStyleSheet("background-color: #1C2833;")
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        flow_header = QLabel("フロー")
        flow_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        flow_header.setFixedHeight(36)
        flow_header.setStyleSheet("""
            background-color: #0D1B2A;
            color: #90CAF9;
            font-size: 12px;
            font-weight: bold;
            border-bottom: 1px solid #263238;
        """)
        center_layout.addWidget(flow_header)

        self._flow_editor = FlowEditor()
        self._flow_editor.node_selected.connect(self._on_node_selected)
        self._flow_editor.flow_changed.connect(self._on_flow_changed)
        center_layout.addWidget(self._flow_editor)

        # ログパネル
        self._log_panel = LogPanel()
        center_layout.addWidget(self._log_panel)

        splitter.addWidget(center_widget)

        # 右パネル：設定パネル
        self._settings_panel = SettingsPanel(str(self.engine.templates_dir))
        self._settings_panel.params_changed.connect(self._on_params_changed)
        splitter.addWidget(self._settings_panel)

        splitter.setSizes([200, 700, 280])
        main_layout.addWidget(splitter)

    def _setup_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #0D1B2A;
                color: #ECEFF1;
                font-size: 11px;
            }
            QMenuBar::item:selected { background-color: #1E3A5F; }
            QMenu {
                background-color: #1C2833;
                color: #ECEFF1;
                border: 1px solid #263238;
            }
            QMenu::item:selected { background-color: #1E3A5F; }
        """)

        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル(&F)")
        file_menu.addAction("新規(&N)", self._new_flow, QKeySequence.StandardKey.New)
        file_menu.addAction("開く(&O)", self._open_flow, QKeySequence.StandardKey.Open)
        file_menu.addSeparator()
        file_menu.addAction("保存(&S)", self._save_flow, QKeySequence.StandardKey.Save)
        file_menu.addAction("名前を付けて保存(&A)", self._save_flow_as)
        file_menu.addSeparator()
        file_menu.addAction("終了(&X)", self.close)

        # フローメニュー
        flow_menu = menubar.addMenu("フロー(&L)")
        flow_menu.addAction("実行(&R)", self._run_flow, "F5")
        flow_menu.addAction("停止(&T)", self._stop_flow, "F6")
        flow_menu.addSeparator()
        flow_menu.addAction("フローをクリア", self._clear_flow)

        # ツールメニュー
        tools_menu = menubar.addMenu("ツール(&T)")
        tools_menu.addAction("テンプレート管理", self._open_template_manager)
        tools_menu.addAction("logsフォルダを開く", self._open_logs_dir)
        tools_menu.addAction("flowsフォルダを開く", self._open_flows_dir)

        # ヘルプメニュー
        help_menu = menubar.addMenu("ヘルプ(&H)")
        help_menu.addAction("使い方", self._show_help)
        help_menu.addAction("バージョン情報", self._show_about)

    def _setup_shortcuts(self):
        """キーボードショートカットを設定する。"""
        # 緊急停止: Ctrl+Alt+Pause
        emergency_stop = QShortcut(QKeySequence("Ctrl+Alt+Pause"), self)
        emergency_stop.activated.connect(self._emergency_stop)

        # F5: 実行
        run_shortcut = QShortcut(QKeySequence("F5"), self)
        run_shortcut.activated.connect(self._run_flow)

        # F6: 停止
        stop_shortcut = QShortcut(QKeySequence("F6"), self)
        stop_shortcut.activated.connect(self._stop_flow)

    def _setup_failsafe_monitor(self):
        """フェイルセーフ監視タイマーを設定する（マウス左上移動で停止）。"""
        self._failsafe_timer = QTimer(self)
        self._failsafe_timer.setInterval(200)
        self._failsafe_timer.timeout.connect(self._check_failsafe)
        self._failsafe_timer.start()

    def _check_failsafe(self):
        """マウスが画面左上(0,0)付近にある場合は実行を停止する。"""
        if not self.engine.is_running():
            return
        try:
            cursor_pos = QApplication.primaryScreen().geometry()
            from PySide6.QtGui import QCursor
            pos = QCursor.pos()
            if pos.x() <= 5 and pos.y() <= 5:
                self._emergency_stop()
                self._log_panel.append_log(
                    "🛡 フェイルセーフ発動: マウスが画面左上に移動しました。実行を停止します。"
                )
        except Exception:
            pass

    def _emergency_stop(self):
        """緊急停止を実行する。"""
        if self.engine.is_running():
            self.engine.stop()
            self._log_panel.append_log("⚠️ 緊急停止が実行されました (Ctrl+Alt+Pause)")
            self._set_running_state(False)

    def _update_title(self):
        """ウィンドウタイトルを更新する。"""
        flow_name = "新しいフロー"
        if self._current_flow_path:
            flow_name = Path(self._current_flow_path).stem
        modified = " *" if self._flow_modified else ""
        self.setWindowTitle(f"LocalRPA - {flow_name}{modified}")
        self._flow_name_label.setText(f"{flow_name}{modified}")

    def _on_add_action(self, action_data: dict):
        """アクションをフローに追加する。"""
        self._flow_editor.add_action(action_data)

    def _on_node_selected(self, action_data: dict):
        """ノードが選択された時の処理。"""
        if action_data:
            self._settings_panel.load_action(action_data)
        else:
            self._settings_panel.clear()

    def _on_flow_changed(self):
        """フローが変更された時の処理。"""
        self._flow_modified = True
        self._update_title()

    def _on_params_changed(self, changes: dict):
        """パラメータが変更された時の処理。"""
        selected = self._flow_editor.get_selected_node()
        if selected:
            self._flow_editor.update_selected_node_data(selected.action_data)

    def _new_flow(self):
        """新しいフローを作成する。"""
        if self._flow_modified:
            reply = QMessageBox.question(
                self, "確認",
                "現在のフローに未保存の変更があります。破棄しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        self._flow_editor.clear_flow()
        self._settings_panel.clear()
        self._current_flow_path = None
        self._flow_modified = False
        self._update_title()
        self._log_panel.append_log("新しいフローを作成しました。")

    def _open_flow(self):
        """フローファイルを開く。"""
        flows_dir = str(self.engine.flows_dir)
        file_path, _ = QFileDialog.getOpenFileName(
            self, "フローを開く", flows_dir, "フローファイル (*.json)"
        )
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                flow_data = json.load(f)
            self._flow_editor.load_flow(flow_data.get("actions", []))
            self._current_flow_path = file_path
            self._flow_modified = False
            self._update_title()
            self._log_panel.append_log(f"フローを読み込みました: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"フローの読み込みに失敗しました:\n{e}")

    def _save_flow(self):
        """フローを保存する。"""
        if not self._current_flow_path:
            self._save_flow_as()
            return
        self._do_save(self._current_flow_path)

    def _save_flow_as(self):
        """フローを名前を付けて保存する。"""
        flows_dir = str(self.engine.flows_dir)
        file_path, _ = QFileDialog.getSaveFileName(
            self, "フローを保存", flows_dir, "フローファイル (*.json)"
        )
        if not file_path:
            return
        if not file_path.endswith(".json"):
            file_path += ".json"
        self._current_flow_path = file_path
        self._do_save(file_path)

    def _do_save(self, file_path: str):
        """フローをファイルに保存する。"""
        try:
            flow_name = Path(file_path).stem
            flow_data = {
                "name": flow_name,
                "version": "1.0",
                "actions": self._flow_editor.get_flow_actions(),
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(flow_data, f, ensure_ascii=False, indent=2)
            self._flow_modified = False
            self._update_title()
            self._log_panel.append_log(f"フローを保存しました: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"フローの保存に失敗しました:\n{e}")

    def _run_flow(self):
        """フローを実行する。"""
        if self.engine.is_running():
            return

        actions = self._flow_editor.get_flow_actions()
        if not actions:
            QMessageBox.information(self, "情報", "フローにアクションがありません。")
            return

        # 初回実行時の警告
        if not hasattr(self, "_warned_about_execution"):
            reply = QMessageBox.warning(
                self, "実行確認",
                "フローを実行します。\n\n"
                "⚠️ 注意事項:\n"
                "・マウス/キーボードが自動操作されます\n"
                "・マウスを画面左上(0,0)に移動すると緊急停止します\n"
                "・Ctrl+Alt+Pause でも緊急停止できます\n\n"
                "実行しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            self._warned_about_execution = True

        flow_name = "フロー"
        if self._current_flow_path:
            flow_name = Path(self._current_flow_path).stem
        flow_data = {
            "name": flow_name,
            "actions": actions,
        }

        self._flow_editor.reset_all_statuses()
        self._log_panel.clear_log()
        self._set_running_state(True)

        self._run_thread = FlowRunThread(self.engine, flow_data)
        self._run_thread.step_started.connect(self._on_step_started)
        self._run_thread.step_completed.connect(self._on_step_completed)
        self._run_thread.flow_completed.connect(self._on_flow_completed)
        self._run_thread.log_message.connect(self._log_panel.append_log)
        self._run_thread.start()

    def _stop_flow(self):
        """フローの実行を停止する。"""
        if self.engine.is_running():
            self.engine.stop()
            self._log_panel.append_log("--- 停止要求を送信しました ---")

    def _on_step_started(self, index: int, action: dict):
        """ステップ開始時の処理。"""
        self._flow_editor.set_node_status(index, "running")
        self._status_label.setText(f"実行中: [{index+1}] {action.get('name', '')}")

    def _on_step_completed(self, index: int, action: dict, result):
        """ステップ完了時の処理。"""
        status = result.status.value if hasattr(result, "status") else "success"
        self._flow_editor.set_node_status(index, status)

    def _on_flow_completed(self, success: bool, log_path: str):
        """フロー完了時の処理。"""
        self._set_running_state(False)
        if success:
            self._status_label.setText("✅ フロー完了")
            self._log_panel.append_log(f"✅ フローが正常に完了しました。ログ: {log_path}")
        else:
            self._status_label.setText("❌ フロー失敗")
            self._log_panel.append_log(f"❌ フローがエラーで終了しました。ログ: {log_path}")

    def _set_running_state(self, running: bool):
        """実行中/停止中のUI状態を切り替える。"""
        self._btn_run.setEnabled(not running)
        self._btn_stop.setEnabled(running)
        self._btn_new.setEnabled(not running)
        self._btn_open.setEnabled(not running)
        self._btn_save.setEnabled(not running)

    def _clear_flow(self):
        """フローをクリアする。"""
        reply = QMessageBox.question(
            self, "確認", "フローをクリアしますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._flow_editor.clear_flow()
            self._settings_panel.clear()
            self._flow_modified = True
            self._update_title()

    def _open_template_manager(self):
        """テンプレート管理ダイアログを開く。"""
        dialog = TemplateManagerDialog(str(self.engine.templates_dir), self)
        dialog.exec()

    def _open_logs_dir(self):
        """logsフォルダをエクスプローラーで開く。"""
        self._open_dir_in_explorer(str(self.engine.logs_dir))

    def _open_flows_dir(self):
        """flowsフォルダをエクスプローラーで開く。"""
        self._open_dir_in_explorer(str(self.engine.flows_dir))

    def _open_dir_in_explorer(self, path: str):
        """ディレクトリをエクスプローラーで開く。"""
        import subprocess
        Path(path).mkdir(exist_ok=True)
        try:
            if sys.platform == "win32":
                subprocess.Popen(["explorer", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            QMessageBox.information(self, "情報", f"フォルダ: {path}")

    def _show_help(self):
        """使い方ダイアログを表示する。"""
        QMessageBox.information(
            self, "使い方",
            "LocalRPA - 画像マッチ自動化ツール\n\n"
            "【基本操作】\n"
            "1. 左パネルのアクションをクリックしてフローに追加\n"
            "2. 右パネルでパラメータを設定\n"
            "3. ▶ 実行ボタンでフローを実行\n\n"
            "【テンプレート画像の登録】\n"
            "「テンプレート管理」ボタンからPNG画像を登録\n"
            "設定パネルの📂ボタンから直接選択も可能\n\n"
            "【緊急停止】\n"
            "・マウスを画面左上(0,0)に移動\n"
            "・Ctrl+Alt+Pause キー\n"
            "・⏹ 停止ボタン\n\n"
            "【フロー保存先】\n"
            f"{self.engine.flows_dir}\n\n"
            "【ログ保存先】\n"
            f"{self.engine.logs_dir}",
        )

    def _show_about(self):
        """バージョン情報ダイアログを表示する。"""
        QMessageBox.about(
            self, "バージョン情報",
            "LocalRPA v1.0.0\n\n"
            "画像マッチ特化型ローカルRPAツール\n\n"
            "技術スタック:\n"
            "・Python 3.11\n"
            "・PySide6 (Qt6)\n"
            "・OpenCV (cv2.matchTemplate)\n"
            "・PyAutoGUI\n\n"
            "完全オフライン動作 / 外部通信ゼロ",
        )

    def closeEvent(self, event):
        """ウィンドウを閉じる時の処理。"""
        if self.engine.is_running():
            reply = QMessageBox.question(
                self, "確認",
                "フローが実行中です。終了しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.engine.stop()

        if self._flow_modified:
            reply = QMessageBox.question(
                self, "確認",
                "未保存の変更があります。保存しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            if reply == QMessageBox.StandardButton.Yes:
                self._save_flow()

        if self._failsafe_timer:
            self._failsafe_timer.stop()
        event.accept()


class TemplateManagerDialog(QDialog):
    """テンプレート画像管理ダイアログ。"""

    def __init__(self, templates_dir: str, parent=None):
        super().__init__(parent)
        self.templates_dir = templates_dir
        Path(templates_dir).mkdir(parents=True, exist_ok=True)
        self.setWindowTitle("テンプレート画像管理")
        self.setMinimumSize(600, 400)
        self.setStyleSheet("""
            QDialog { background-color: #1C2833; }
            QLabel { color: #ECEFF1; font-size: 11px; }
            QPushButton {
                background-color: #1E3A5F;
                color: #ECEFF1;
                border: 1px solid #2E5F8A;
                border-radius: 3px;
                padding: 4px 12px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #2E5F8A; }
        """)
        self._setup_ui()
        self._refresh_list()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # ヘッダー
        header = QLabel(f"テンプレート画像フォルダ: {self.templates_dir}")
        header.setStyleSheet("color: #90A4AE; font-size: 10px; padding: 4px;")
        layout.addWidget(header)

        # ファイルリスト
        from PySide6.QtWidgets import QListWidget
        self._list = QListWidget()
        self._list.setStyleSheet("""
            QListWidget {
                background-color: #263238;
                color: #ECEFF1;
                border: 1px solid #37474F;
                font-size: 11px;
            }
            QListWidget::item:selected { background-color: #1565C0; }
        """)
        self._list.currentRowChanged.connect(self._on_selection_changed)
        layout.addWidget(self._list)

        # プレビュー
        self._preview = QLabel("画像を選択してください")
        self._preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview.setFixedHeight(120)
        self._preview.setStyleSheet(
            "background-color: #263238; border: 1px solid #37474F; border-radius: 3px;"
        )
        layout.addWidget(self._preview)

        # ボタン
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("📂 画像を追加")
        btn_add.clicked.connect(self._add_template)
        btn_layout.addWidget(btn_add)

        btn_del = QPushButton("🗑 削除")
        btn_del.clicked.connect(self._delete_template)
        btn_layout.addWidget(btn_del)

        btn_open = QPushButton("📁 フォルダを開く")
        btn_open.clicked.connect(self._open_folder)
        btn_layout.addWidget(btn_open)

        btn_close = QPushButton("閉じる")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def _refresh_list(self):
        self._list.clear()
        templates_dir = Path(self.templates_dir)
        for f in sorted(templates_dir.glob("*.png")):
            self._list.addItem(f.name)
        for f in sorted(templates_dir.glob("*.jpg")):
            self._list.addItem(f.name)
        for f in sorted(templates_dir.glob("*.bmp")):
            self._list.addItem(f.name)

    def _on_selection_changed(self, row: int):
        if row < 0:
            return
        item = self._list.item(row)
        if not item:
            return
        path = Path(self.templates_dir) / item.text()
        if path.exists():
            from PySide6.QtGui import QPixmap
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    580, 116,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._preview.setPixmap(scaled)
                return
        self._preview.setText("プレビューなし")

    def _add_template(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "テンプレート画像を追加", "", "画像ファイル (*.png *.jpg *.bmp)"
        )
        for f in files:
            dest = Path(self.templates_dir) / Path(f).name
            shutil.copy2(f, dest)
        self._refresh_list()

    def _delete_template(self):
        item = self._list.currentItem()
        if not item:
            return
        reply = QMessageBox.question(
            self, "確認", f"'{item.text()}' を削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            path = Path(self.templates_dir) / item.text()
            if path.exists():
                path.unlink()
            self._refresh_list()

    def _open_folder(self):
        import subprocess
        try:
            if sys.platform == "win32":
                subprocess.Popen(["explorer", self.templates_dir])
            else:
                subprocess.Popen(["xdg-open", self.templates_dir])
        except Exception:
            QMessageBox.information(self, "情報", f"フォルダ: {self.templates_dir}")
