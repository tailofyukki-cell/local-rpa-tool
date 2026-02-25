# LocalRPA - 画像マッチ特化型ローカルRPAツール

**完全オフラインで動作する、画像マッチベースのWindows専用GUI自動化ツールです。**

Microsoft Power Automate DesktopのようにGUIでフローを作成・実行できますが、クラウド依存や外部通信は一切ありません。インストール不要の単体.exeファイルとして配布され、USBメモリなどに入れて持ち運ぶことも可能です。

![screenshot](https://user-images.githubusercontent.com/12345/screenshot.png) <!-- ダミーURL -->

---

## 🎯 主な機能

- **GUIフロービルダー**: アクションをドラッグ＆ドロップで並べ替え、直感的にフローを構築できます。
- **画像マッチング**: OpenCVを利用した高精度な画像認識機能。
  - 画面上の指定画像を検索 (`image.find`)
  - 画像が出現するまで待機 (`image.wait_appear`)
  - 画像が消えるまで待機 (`image.wait_disappear`)
  - 見つけた画像をクリック (`image.click`)
- **マウス＆キーボード操作**: クリック、キー入力、ホットキーなど基本的なGUI操作を網羅。
- **変数と条件分岐**: 実行結果を変数に保存し、IF条件で処理を分岐させることが可能。
- **完全オフライン**: インターネット接続は一切不要。テレメトリや自動アップデートもありません。
- **ポータブル**: 単一の.exeファイルで動作し、設定やフローはすべてexeと同じフォルダ内に保存されます。

---

## 🛡 安全対策

- **フェイルセーフ**: フロー実行中にマウスカーソルを画面の左上隅に移動させると、実行が緊急停止します。
- **緊急停止キー**: `Ctrl + Alt + Pause` キーでいつでもフローを強制終了できます。
- **タイムアウト設定**: すべての待機系アクションにはタイムアウトが必須となっており、無限ループを防ぎます。

---

## 📂 フォルダ構成

`LocalRPA.exe` を実行すると、同じ階層に以下のフォルダが自動的に作成されます。

```
/LocalRPA/
├── LocalRPA.exe          # 実行ファイル
├── /flows/               # 作成したフロー（.json）が保存される場所
├── /logs/                # フローの実行ログが保存される場所
├── /templates/           # 画像マッチングで使用するテンプレート画像（.png）を置く場所
└── /data/                # アプリケーションの設定ファイルが保存される場所
```

---

## 🛠️ ビルド手順

このツールはGitHub Actions経由でビルドされ、Windows用の単体.exeファイルとして提供されます。

### 1. GitHub Actionsでのビルド

1. このリポジトリをフォークまたはクローンします。
2. リポジトリの「Actions」タブに移動します。
3. 「Build Windows Executable」ワークフローを選択し、「Run workflow」ボタンをクリックします。
4. ビルドが完了すると（約5〜10分）、「Artifacts」セクションに `LocalRPA-exe` という名前の成果物が表示されます。
5. それをダウンロードし、zipを展開すると `LocalRPA.exe` が入っています。

### 2. ローカル環境でのビルド（手動）

Windows環境でソースコードから直接ビルドすることも可能です。

```bash
# 1. リポジトリをクローン
git clone https://github.com/your-username/local-rpa-tool.git
cd local-rpa-tool

# 2. Python環境のセットアップ（Python 3.9以上を推奨）
python -m venv venv
venv\Scripts\activate

# 3. 依存パッケージのインストール
pip install -r requirements.txt

# 4. PyInstallerでビルド
pyinstaller build.spec
```

ビルドが成功すると、`dist` フォルダ内に `LocalRPA.exe` が生成されます。

---

## ✅ 受入基準

| 項目 | ステータス |
| :--- | :---: |
| 画像を登録できる | ✔️ Yes |
| 指定画像を画面上で検出できる | ✔️ Yes |
| 類似度指定が機能する | ✔️ Yes |
| 見つかった位置をクリックできる | ✔️ Yes |
| 出現/消滅待機が動作する | ✔️ Yes |
| 緊急停止が機能する | ✔️ Yes |
| 1ファイル.exeで配布可能 | ✔️ Yes |
| ネット依存ゼロ | ✔️ Yes |

---

## 📝 最終出力形式

- **採用技術**: Python 3.11, PySide6, OpenCV, PyAutoGUI, PyInstaller
- **画像マッチ方式**: OpenCV `cv2.matchTemplate` (TM_CCOEFF_NORMED)
- **テンプレート保存方式**: `/templates/` フォルダ内にPNG/JPG/BMP形式で直接保存
- **exe生成方法**: PyInstaller (`--onefile`相当のspec設定)
- **サンプルフロー**: 2種類（ボタンクリック、アプリフォーム入力）
