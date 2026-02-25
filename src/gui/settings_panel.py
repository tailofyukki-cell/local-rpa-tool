"""
設定パネルウィジェットモジュール
選択されたノードのパラメータ設定UIを提供する。
テンプレート画像選択UIを含む。
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class SettingsPanel(QWidget):
    """選択ノードの設定パネル。"""

    params_changed = Signal(dict)  # 変更されたパラメータ辞書

    def __init__(self, templates_dir: str, parent=None):
        super().__init__(parent)
        self.templates_dir = templates_dir
        self._current_action_data: Optional[Dict] = None
        self._param_widgets: Dict[str, QWidget] = {}
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedWidth(280)
        self.setStyleSheet("background-color: #1A2332;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ヘッダー
        self._header = QLabel("設定パネル")
        self._header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._header.setFixedHeight(36)
        self._header.setStyleSheet("""
            background-color: #0D1B2A;
            color: #90CAF9;
            font-size: 12px;
            font-weight: bold;
            border-bottom: 1px solid #263238;
            padding: 4px;
        """)
        main_layout.addWidget(self._header)

        # ノード名編集
        name_frame = QFrame()
        name_frame.setStyleSheet("background-color: #1E2D3D; border-bottom: 1px solid #263238;")
        name_layout = QHBoxLayout(name_frame)
        name_layout.setContentsMargins(8, 6, 8, 6)
        name_layout.setSpacing(4)
        name_label = QLabel("名前:")
        name_label.setStyleSheet("color: #90A4AE; font-size: 10px;")
        name_label.setFixedWidth(40)
        name_layout.addWidget(name_label)
        self._name_edit = QLineEdit()
        self._name_edit.setStyleSheet("""
            QLineEdit {
                background-color: #263238;
                color: #ECEFF1;
                border: 1px solid #37474F;
                border-radius: 3px;
                padding: 3px 6px;
                font-size: 11px;
            }
            QLineEdit:focus { border-color: #64B5F6; }
        """)
        self._name_edit.textChanged.connect(self._on_name_changed)
        name_layout.addWidget(self._name_edit)
        main_layout.addWidget(name_frame)

        # スクロールエリア（パラメータ）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background-color: #1A2332; }
            QScrollBar:vertical { background: #1A2332; width: 6px; }
            QScrollBar::handle:vertical { background: #455A64; border-radius: 3px; }
        """)

        self._params_container = QWidget()
        self._params_container.setStyleSheet("background-color: #1A2332;")
        self._params_layout = QVBoxLayout(self._params_container)
        self._params_layout.setContentsMargins(8, 8, 8, 8)
        self._params_layout.setSpacing(8)
        self._params_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._empty_label = QLabel("ノードを選択してください")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #546E7A; font-size: 11px; padding: 20px;")
        self._params_layout.addWidget(self._empty_label)

        scroll.setWidget(self._params_container)
        main_layout.addWidget(scroll)

    def load_action(self, action_data: dict):
        """アクションデータを設定パネルに読み込む。"""
        self._current_action_data = action_data
        self._param_widgets.clear()

        # ヘッダー更新
        action_type = action_data.get("type", "")
        self._header.setText(f"設定: {action_type}")
        self._name_edit.blockSignals(True)
        self._name_edit.setText(action_data.get("name", ""))
        self._name_edit.blockSignals(False)

        # 既存ウィジェットをクリア
        while self._params_layout.count():
            item = self._params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not action_data:
            self._params_layout.addWidget(self._empty_label)
            return

        # パラメータスキーマを取得
        from src.core.dispatcher import ActionDispatcher
        dispatcher = ActionDispatcher()
        action_class = dispatcher.get_action_class(action_type)
        if not action_class:
            lbl = QLabel(f"不明なアクション: {action_type}")
            lbl.setStyleSheet("color: #EF9A9A; font-size: 11px;")
            self._params_layout.addWidget(lbl)
            return

        schema = action_class.PARAMS_SCHEMA
        params = action_data.get("params", {})

        for param_def in schema:
            self._add_param_widget(param_def, params)

        self._params_layout.addStretch()

    def _add_param_widget(self, param_def: dict, params: dict):
        """パラメータウィジェットを追加する。"""
        name = param_def["name"]
        label_text = param_def.get("label", name)
        param_type = param_def.get("type", "string")
        default = param_def.get("default", "")
        description = param_def.get("description", "")
        current_value = params.get(name, default)

        # ラベル
        label = QLabel(label_text)
        label.setStyleSheet("color: #90A4AE; font-size: 10px;")
        if description:
            label.setToolTip(description)
        self._params_layout.addWidget(label)

        widget = None

        if param_type == "template_file":
            widget = self._create_template_selector(name, current_value)
        elif param_type == "bool":
            widget = QCheckBox()
            val = str(current_value).lower() in ("true", "1", "yes")
            widget.setChecked(val)
            widget.setStyleSheet("color: #ECEFF1; font-size: 11px;")
            widget.stateChanged.connect(lambda state, n=name: self._on_param_changed(n, state == 2))
        elif param_type == "select":
            widget = QComboBox()
            widget.setStyleSheet("""
                QComboBox {
                    background-color: #263238;
                    color: #ECEFF1;
                    border: 1px solid #37474F;
                    border-radius: 3px;
                    padding: 3px 6px;
                    font-size: 11px;
                }
                QComboBox::drop-down { border: none; }
                QComboBox QAbstractItemView {
                    background-color: #263238;
                    color: #ECEFF1;
                    selection-background-color: #1565C0;
                }
            """)
            options = param_def.get("options", [])
            for opt in options:
                widget.addItem(opt)
            if str(current_value) in options:
                widget.setCurrentText(str(current_value))
            widget.currentTextChanged.connect(lambda val, n=name: self._on_param_changed(n, val))
        elif param_type == "float":
            widget = QDoubleSpinBox()
            widget.setMinimum(param_def.get("min", 0.0))
            widget.setMaximum(param_def.get("max", 1.0))
            widget.setSingleStep(param_def.get("step", 0.05))
            widget.setDecimals(2)
            try:
                widget.setValue(float(current_value))
            except (ValueError, TypeError):
                widget.setValue(float(default) if default else 0.0)
            widget.setStyleSheet(self._spinbox_style())
            widget.valueChanged.connect(lambda val, n=name: self._on_param_changed(n, val))
        elif param_type in ("int", "int_or_var"):
            widget = QSpinBox()
            widget.setMinimum(param_def.get("min", -99999))
            widget.setMaximum(param_def.get("max", 99999))
            try:
                widget.setValue(int(float(str(current_value))))
            except (ValueError, TypeError):
                widget.setValue(int(default) if default else 0)
            widget.setStyleSheet(self._spinbox_style())
            widget.valueChanged.connect(lambda val, n=name: self._on_param_changed(n, val))
        else:
            # string / その他
            widget = QLineEdit()
            widget.setText(str(current_value))
            widget.setStyleSheet("""
                QLineEdit {
                    background-color: #263238;
                    color: #ECEFF1;
                    border: 1px solid #37474F;
                    border-radius: 3px;
                    padding: 3px 6px;
                    font-size: 11px;
                }
                QLineEdit:focus { border-color: #64B5F6; }
            """)
            widget.textChanged.connect(lambda val, n=name: self._on_param_changed(n, val))

        if widget:
            widget.setToolTip(description)
            self._params_layout.addWidget(widget)
            self._param_widgets[name] = widget

    def _create_template_selector(self, param_name: str, current_value: str) -> QWidget:
        """テンプレート画像選択ウィジェットを作成する。"""
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # ドロップダウン + 参照ボタン
        row = QHBoxLayout()
        combo = QComboBox()
        combo.setEditable(True)
        combo.setStyleSheet("""
            QComboBox {
                background-color: #263238;
                color: #ECEFF1;
                border: 1px solid #37474F;
                border-radius: 3px;
                padding: 3px 6px;
                font-size: 11px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #263238;
                color: #ECEFF1;
                selection-background-color: #1565C0;
            }
        """)

        # テンプレートディレクトリのPNGファイルを列挙
        self._refresh_template_combo(combo)
        if current_value:
            combo.setCurrentText(str(current_value))

        combo.currentTextChanged.connect(
            lambda val, n=param_name: self._on_param_changed(n, val)
        )
        row.addWidget(combo)

        # 参照ボタン
        browse_btn = QPushButton("📂")
        browse_btn.setFixedSize(28, 28)
        browse_btn.setToolTip("テンプレート画像を選択")
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #37474F;
                color: #ECEFF1;
                border: 1px solid #455A64;
                border-radius: 3px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #455A64; }
        """)
        browse_btn.clicked.connect(
            lambda: self._browse_template(combo, param_name)
        )
        row.addWidget(browse_btn)

        # 更新ボタン
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(28, 28)
        refresh_btn.setToolTip("テンプレート一覧を更新")
        refresh_btn.setStyleSheet(browse_btn.styleSheet())
        refresh_btn.clicked.connect(lambda: self._refresh_template_combo(combo))
        row.addWidget(refresh_btn)

        layout.addLayout(row)

        # プレビュー
        self._preview_label = QLabel()
        self._preview_label.setFixedHeight(80)
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setStyleSheet(
            "background-color: #263238; border: 1px solid #37474F; border-radius: 3px;"
        )
        self._update_template_preview(current_value)
        combo.currentTextChanged.connect(
            lambda val: self._update_template_preview(val)
        )
        layout.addWidget(self._preview_label)

        self._param_widgets[param_name] = combo
        return container

    def _refresh_template_combo(self, combo: QComboBox):
        """テンプレートコンボボックスを更新する。"""
        current = combo.currentText()
        combo.clear()
        combo.addItem("")
        templates_dir = Path(self.templates_dir)
        if templates_dir.exists():
            for f in sorted(templates_dir.glob("*.png")):
                combo.addItem(f.name)
            for f in sorted(templates_dir.glob("*.jpg")):
                combo.addItem(f.name)
            for f in sorted(templates_dir.glob("*.bmp")):
                combo.addItem(f.name)
        if current:
            combo.setCurrentText(current)

    def _browse_template(self, combo: QComboBox, param_name: str):
        """テンプレート画像ファイルを選択する。"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "テンプレート画像を選択",
            self.templates_dir,
            "画像ファイル (*.png *.jpg *.bmp)",
        )
        if file_path:
            # templatesディレクトリにコピー
            import shutil
            dest = Path(self.templates_dir) / Path(file_path).name
            if not dest.exists():
                shutil.copy2(file_path, dest)
            combo.setCurrentText(Path(file_path).name)
            self._refresh_template_combo(combo)
            combo.setCurrentText(Path(file_path).name)

    def _update_template_preview(self, template_name: str):
        """テンプレート画像のプレビューを更新する。"""
        if not hasattr(self, "_preview_label"):
            return
        if not template_name:
            self._preview_label.setText("プレビューなし")
            self._preview_label.setStyleSheet(
                "background-color: #263238; border: 1px solid #37474F; "
                "border-radius: 3px; color: #546E7A; font-size: 10px;"
            )
            return

        template_path = Path(self.templates_dir) / template_name
        if template_path.exists():
            pixmap = QPixmap(str(template_path))
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    260, 76,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._preview_label.setPixmap(scaled)
                self._preview_label.setStyleSheet(
                    "background-color: #263238; border: 1px solid #37474F; border-radius: 3px;"
                )
                return

        self._preview_label.setText(f"画像なし: {template_name}")
        self._preview_label.setStyleSheet(
            "background-color: #263238; border: 1px solid #EF9A9A; "
            "border-radius: 3px; color: #EF9A9A; font-size: 10px;"
        )

    def _spinbox_style(self) -> str:
        return """
            QSpinBox, QDoubleSpinBox {
                background-color: #263238;
                color: #ECEFF1;
                border: 1px solid #37474F;
                border-radius: 3px;
                padding: 3px 6px;
                font-size: 11px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus { border-color: #64B5F6; }
            QSpinBox::up-button, QDoubleSpinBox::up-button,
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                background-color: #37474F;
                border: none;
                width: 16px;
            }
        """

    def _on_name_changed(self, text: str):
        """ノード名が変更された時の処理。"""
        if self._current_action_data:
            self._current_action_data["name"] = text
            self.params_changed.emit({"name": text})

    def _on_param_changed(self, param_name: str, value: Any):
        """パラメータが変更された時の処理。"""
        if self._current_action_data:
            if "params" not in self._current_action_data:
                self._current_action_data["params"] = {}
            self._current_action_data["params"][param_name] = value
            self.params_changed.emit({"params": {param_name: value}})

    def clear(self):
        """設定パネルをクリアする。"""
        self._current_action_data = None
        self._param_widgets.clear()
        self._header.setText("設定パネル")
        self._name_edit.clear()
        while self._params_layout.count():
            item = self._params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._params_layout.addWidget(self._empty_label)
