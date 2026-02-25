"""
LocalRPA - 画像マッチ特化型ローカルRPAツール
エントリポイント
"""
import sys
import os
from pathlib import Path


def main():
    """アプリケーションのエントリポイント。"""
    # PyInstaller onefile環境でのパス設定
    if getattr(sys, "frozen", False):
        # exeと同じディレクトリを作業ディレクトリに設定
        base_dir = Path(sys.executable).parent
        os.chdir(str(base_dir))
    else:
        base_dir = Path(__file__).parent.parent

    # srcディレクトリをパスに追加
    src_dir = str(Path(__file__).parent)
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    # PySide6アプリケーション起動
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont

    app = QApplication(sys.argv)
    app.setApplicationName("LocalRPA")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("LocalRPA")

    # ダークテーマのデフォルトフォント設定
    font = QFont("Meiryo UI", 9)
    app.setFont(font)

    # スタイルシート（ダークテーマ）
    app.setStyleSheet("""
        QToolTip {
            background-color: #263238;
            color: #ECEFF1;
            border: 1px solid #455A64;
            padding: 4px;
            font-size: 11px;
        }
        QMessageBox {
            background-color: #1C2833;
        }
        QMessageBox QLabel {
            color: #ECEFF1;
            font-size: 11px;
        }
        QMessageBox QPushButton {
            background-color: #1E3A5F;
            color: #ECEFF1;
            border: 1px solid #2E5F8A;
            border-radius: 4px;
            padding: 4px 16px;
            min-width: 60px;
        }
        QMessageBox QPushButton:hover {
            background-color: #2E5F8A;
        }
        QInputDialog {
            background-color: #1C2833;
        }
        QInputDialog QLabel {
            color: #ECEFF1;
        }
        QInputDialog QLineEdit {
            background-color: #263238;
            color: #ECEFF1;
            border: 1px solid #37474F;
            border-radius: 3px;
            padding: 4px;
        }
        QFileDialog {
            background-color: #1C2833;
            color: #ECEFF1;
        }
    """)

    from src.gui.main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
