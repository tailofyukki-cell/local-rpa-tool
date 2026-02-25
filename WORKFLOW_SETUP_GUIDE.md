# GitHub Actions ワークフロー追加手順

## ⚠️ なぜこのガイドが必要か

GitHub Actionsのワークフローファイル（`.github/workflows/`以下）は、セキュリティ上の理由から特別な権限（`workflow`スコープ）が必要です。このガイドでは、PCブラウザからGitHub Web UIを使って直接ワークフローファイルを追加する手順を説明します。

---

## 📋 手順（約2分）

### 1. リポジトリを開く

以下のURLにアクセスします：
```
https://github.com/tailofyukki-cell/local-rpa-tool
```

### 2. ワークフローファイルを作成する

1. 「**Add file**」ボタン → 「**Create new file**」をクリック
2. ファイル名の入力欄に以下を入力します（スラッシュを入力するとフォルダが自動作成されます）：
   ```
   .github/workflows/build.yml
   ```
3. エディタ部分に以下のYAML内容を**全てコピー&ペースト**します：

```yaml
name: Build Windows Executable

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build:
    runs-on: windows-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Build with PyInstaller
      run: |
        pyinstaller build.spec

    - name: Upload artifact
      uses: actions/upload-artifact@v3
      with:
        name: LocalRPA-exe
        path: dist/LocalRPA.exe
```

4. ページ下部の「**Commit new file**」ボタンをクリックします

---

## ✅ ビルド完了後のダウンロード手順

1. リポジトリの「**Actions**」タブをクリック
2. 最新の「Build Windows Executable」実行をクリック
3. ページ下部の「**Artifacts**」セクションから「**LocalRPA-exe**」をダウンロード
4. ダウンロードしたzipを展開すると `LocalRPA.exe` が入っています

ビルド時間の目安：**約5〜10分**

---

## 🔄 手動でビルドを再実行する方法

1. 「Actions」タブ → 「Build Windows Executable」を選択
2. 「**Run workflow**」ボタン → 「Run workflow」をクリック
