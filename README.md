# Kindle to PDF Converter

Kindle本を自動的にスクリーンショットしてPDFファイルに変換するPythonアプリケーションです。

## ⚠️ 重要な注意事項

- **このツールは個人的なバックアップ目的のみに使用してください**
- Amazonの利用規約を必ず確認してください
- DRM保護されたコンテンツの扱いには十分注意してください
- 著作権法を遵守してください
- 商用利用や再配布は禁止されています

## 🎯 機能

- ✅ Kindle Cloud Readerの自動操作
- ✅ ページごとの自動スクリーンショット
- ✅ 複数の画像を1つのPDFファイルに統合
- ✅ **GUIで簡単に領域選択**（新機能！）
- ✅ カスタマイズ可能な設定（ページ数、遅延時間など）
- ✅ 自動的なChromeDriverのセットアップ
- ✅ ワンクリック実行用バッチファイル付き

## 📋 必要な環境

- Windows 10/11
- Python 3.8以上
- Google Chrome（最新版推奨）
- インターネット接続

## 🚀 クイックスタート（初めての方向け）

### 1. 必要なパッケージのインストール

プロジェクトフォルダで以下のコマンドを実行：

```bash
pip install -r requirements.txt
```

### 2. スクリーンショット領域の設定（オプション）

**全画面キャプチャでOKな場合はスキップ**してください。

特定の領域だけをキャプチャしたい場合：

```
set_region.bat をダブルクリック
```

1. Kindle Cloud Readerで本のページを開く
2. 領域設定ツールでEnterキーを押す
3. マウスでドラッグして領域を選択
4. 自動的に`config.json`が更新されます

### 3. PDF変換の実行

```
run_kindle_to_pdf.bat をダブルクリック
```

1. ブラウザが起動してKindle Cloud Readerが開きます
2. ログインして本を開きます
3. 本の**最初のページ（ページ1）**に移動
4. （オプション）F11キーで全画面モード
5. **ページめくり方向を確認**（左矢印または右矢印キーで次ページに進むかテスト）
6. `config.json`の`page_turn_direction`を設定（"left"または"right"）
7. ターミナルでEnterキーを押すと自動キャプチャ開始！

## 📁 ファイル構成

```
0104/
├── kindle_to_pdf.py          # メインアプリケーション
├── set_screenshot_region.py  # 領域選択ツール
├── config.json               # 設定ファイル
├── config.example.json       # 設定ファイルの例
├── config.template.json      # 設定ファイルのテンプレート
├── requirements.txt          # 必要なパッケージ
├── run_kindle_to_pdf.bat     # メインアプリ実行用バッチ
├── set_region.bat            # 領域設定用バッチ
├── README.md                 # このファイル
└── data/                     # スクリーンショット保存先
```

## ⚙️ 詳細な使い方

### 設定ファイル（config.json）の編集

必要に応じて`config.json`を編集してください：

```json
{
  "total_pages": 100,
  "output_dir": "data",
  "pdf_filename": null,
  "page_delay": 2.0,
  "screenshot_region": null,
  "fullscreen": true,
  "delete_screenshots": false,
  "page_turn_direction": "left"
}
```

#### 設定項目の説明

| 項目 | 説明 | デフォルト | 推奨値 |
|------|------|------------|--------|
| `total_pages` | キャプチャするページの総数 | 100 | 本のページ数 |
| `output_dir` | スクリーンショット保存先 | "data" | "data" |
| `pdf_filename` | 出力PDFファイル名 | null | null（自動生成） |
| `page_delay` | ページ送り後の待機時間（秒） | 2.0 | 1.5～3.0 |
| `screenshot_region` | スクリーンショット領域 `[x, y, width, height]` | null | null（全画面） |
| `fullscreen` | ブラウザを最大化するか | true | true |
| `delete_screenshots` | PDF作成後に画像を削除 | false | false |
| `page_turn_direction` | ページめくり方向（"left"または"right"） | "left" | "left"または"right" |

### スクリーンショット領域の設定方法

#### 方法1: GUIツールで設定（推奨）

1. **`set_region.bat`をダブルクリック**
2. モード1を選択
3. Kindle Cloud Readerで本のページを開く
4. Enterキーを押す
5. 画面が半透明になるので、マウスでドラッグして領域を選択
6. 自動的に`config.json`が更新されます

#### 方法2: 手動で座標を設定

1. **`set_region.bat`をダブルクリック**
2. モード2を選択（マウス位置確認モード）
3. マウスを動かして座標を確認
4. 左上と右下の座標をメモ
5. `config.json`を編集：
   ```json
   "screenshot_region": [x, y, width, height]
   ```

**例**: 位置(200, 100)から幅1520px、高さ880pxの領域
```json
"screenshot_region": [200, 100, 1520, 880]
```

### コマンドラインでの実行

#### バッチファイルを使う場合（簡単）

```bash
# 領域設定
set_region.bat

# PDF変換実行
run_kindle_to_pdf.bat
```

#### Pythonコマンドで実行する場合

```bash
# 仮想環境がある場合
.venv\Scripts\python.exe kindle_to_pdf.py

# 仮想環境がない場合
python kindle_to_pdf.py
```

## 🎨 使用例

### 例1: 100ページの本を全画面キャプチャ

**config.json**:
```json
{
  "total_pages": 100,
  "output_dir": "data",
  "screenshot_region": null,
  "fullscreen": true
}
```

実行: `run_kindle_to_pdf.bat`

### 例2: 50ページの本を部分領域キャプチャ

1. `set_region.bat`で領域を選択
2. `config.json`を確認：
   ```json
   {
     "total_pages": 50,
     "screenshot_region": [300, 150, 1320, 800]
   }
   ```
3. `run_kindle_to_pdf.bat`を実行

### 例3: ページ読み込みが遅い場合

**config.json**:
```json
{
  "page_delay": 3.0
}
```

ネットワークが遅い場合は`page_delay`を増やしてください。

### 例4: ページめくり方向が逆の本の場合

一部の本は右矢印キーで次のページに進みます：

**config.json**:
```json
{
  "page_turn_direction": "right"
}
```

本を開いたら、左右の矢印キーを試して正しい方向を確認してください。

## 📤 出力ファイル

### スクリーンショット画像

- 保存先: `data/`フォルダ
- ファイル名: `page_0001.png`, `page_0002.png`, ...
- 形式: PNG

### PDF ファイル

- 保存先: プロジェクトルート
- ファイル名: `kindle_book_20251129_143055.pdf`（タイムスタンプ付き）
- または: `config.json`で指定した名前

## 🔧 トラブルシューティング

### ブラウザが起動しない

**原因と対処法**:
- Google Chromeが最新版であることを確認
- `webdriver-manager`が正常にインストールされているか確認
- セキュリティソフトがブラウザ起動をブロックしていないか確認

```bash
# ChromeDriverを再インストール
pip install --upgrade webdriver-manager
```

### スクリーンショットが正しくキャプチャされない

**原因と対処法**:
- **領域設定が間違っている**: `set_region.bat`で再設定
- **ページ読み込みが遅い**: `page_delay`を2.0→3.0に増やす
- **ブラウザのズーム倍率**: ブラウザのズームを100%に設定
- **モニター解像度**: 高DPI環境では座標がずれる可能性あり

### ページ送りがうまくいかない

**原因と対処法**:
- **ページめくり方向が逆**: `page_turn_direction`を"left"→"right"（または逆）に変更
- Kindle Cloud Readerが正しくフォーカスされているか確認
- `page_delay`を2秒以上に設定してみる
- ブラウザの他のタブやウィンドウを閉じる
- キーボードショートカットが競合していないか確認
- 本を開いた状態で手動で左右矢印キーを試して、どちらで次ページに進むか確認

### PDFの作成に失敗する

**原因と対処法**:
- `img2pdf`が正常にインストールされているか確認
- ディスク容量が十分にあるか確認（100ページで約100-500MB必要）
- ファイル名に使用できない文字が含まれていないか確認
- アンチウイルスソフトがブロックしていないか確認

```bash
# img2pdfを再インストール
pip install --upgrade img2pdf
```

### プログラムが途中で止まる

**原因と対処法**:
- ネットワーク接続を確認
- Kindle Cloud Readerがログアウトされていないか確認
- `page_delay`を増やして安定性を向上
- スリープモードに入らないよう電源設定を確認

## 💡 Tips & ベストプラクティス

### ✅ おすすめの設定

```json
{
  "total_pages": 100,
  "output_dir": "data",
  "pdf_filename": null,
  "page_delay": 2.0,
  "screenshot_region": null,
  "fullscreen": true,
  "delete_screenshots": false,
  "page_turn_direction": "left"
}
```

**注意**: `page_turn_direction`は本によって異なります。本を開いたら左右矢印キーを試して、正しい方向を確認してください。

### ✅ 実行前のチェックリスト

- [ ] Chromeブラウザが最新版
- [ ] ネットワーク接続が安定している
- [ ] 十分なディスク容量がある（ページ数 × 5MB程度）
- [ ] `config.json`のページ数が正しい
- [ ] `config.json`のページめくり方向（"left"/"right"）を確認済み
- [ ] 他の作業を中断して専念できる時間がある

### ✅ 品質を向上させるコツ

1. **全画面モード**: F11キーでブラウザUI を完全に非表示
2. **ズーム100%**: ブラウザのズームを100%に設定
3. **安定したネット**: 有線LAN推奨
4. **遅延時間を長めに**: 初回は`page_delay: 3.0`で試す
5. **夜間実行**: ネットワークが空いている時間帯

### ✅ 大量ページの本を処理する場合

100ページ以上の本の場合：

1. **分割実行**: 50ページずつ分けて実行
2. **休憩を入れる**: プログラムに休憩時間を追加（カスタマイズ）
3. **ディスク容量**: 事前に十分な空き容量を確保

## ❓ よくある質問（FAQ）

### Q1: すべてのKindle本で動作しますか？

**A**: Kindle Cloud Readerで開ける本であれば基本的に動作します。ただし、以下の制限があります：
- 固定レイアウトの本は調整が必要な場合あり
- 雑誌やマンガは特別な設定が必要な場合あり
- DRM保護が厳しい本は開けない可能性あり

### Q2: モバイル版のKindleアプリでも使えますか？

**A**: いいえ、現在はPC版のKindle Cloud Reader専用です。モバイル版には対応していません。

### Q3: ページ数が事前にわからない場合は？

**A**: 以下の方法で確認できます：
1. Kindle Cloud Readerで本を開く
2. 最後のページまで移動
3. ページ番号を確認
4. `config.json`の`total_pages`に設定

### Q4: 自動的にページ数を検出できませんか？

**A**: 現在のバージョンでは手動設定が必要です。将来のバージョンでOCR機能を追加する予定です。

### Q5: 画像の品質を上げられますか？

**A**: はい、以下の方法があります：
1. 高解像度モニターを使用
2. ブラウザのズームを調整（推奨：100%）
3. Kindle Cloud Readerの表示設定を調整
4. `screenshot_region`で本文のみをキャプチャ

### Q6: PDFのファイルサイズが大きすぎます

**A**: 以下の方法で削減できます：
1. `delete_screenshots: true`に設定（画像を削除）
2. 画像を圧縮するツールを別途使用
3. `screenshot_region`で必要な部分のみキャプチャ

### Q7: 商用利用は可能ですか？

**A**: いいえ、このツールは**個人的なバックアップ目的のみ**に使用してください。商用利用や再配布は禁止されています。Amazonの利用規約も確認してください。

### Q8: Macでも使えますか？

**A**: 現在はWindows専用ですが、Pythonコードは基本的にクロスプラットフォームです。`.bat`ファイルを`.sh`に変更し、パスを調整すれば動作する可能性があります。

## 📚 関連リソース

- [Kindle Cloud Reader](https://read.amazon.com)
- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [PyAutoGUI Documentation](https://pyautogui.readthedocs.io/)

## 📝 ライセンス

このプロジェクトは個人利用目的で作成されています。商用利用は禁止されています。

## ⚖️ 免責事項

このツールの使用により生じたいかなる損害についても、開発者は責任を負いません。利用者の自己責任でご使用ください。

- このツールはスクリーンショットを利用した個人的なバックアップツールです
- Amazonの利用規約および著作権法を遵守してください
- DRM保護されたコンテンツの不正な配布や共有は違法です
- 本ツールを使用したことによるアカウント停止等の責任は負いかねます

---

**作成日**: 2025年11月29日  
**バージョン**: 1.0.0

質問や問題がある場合は、GitHubのIssueで報告してください。