# Business Card Scanner

名刺のPDFファイルからvCardファイルを生成するPythonスクリプトです。Google Gemini APIを使用して名刺から情報を抽出し、VCardファイルを作成します。

## 機能

- PDFから名刺画像の抽出
- Google Gemini APIを使用した名刺情報の抽出
  - 氏名（漢字表記）
  - メールアドレス
  - 会社名
  - 役職
  - 住所
  - 電話番号
  - SNSリンク
- 読み仮名の自動推測（メールアドレスまたは漢字から）
- vCardファイルの生成（画像付き）

## 必要要件

- Python 3.7以上
- poppler-utils（PDF処理用）
  - Windowsの場合: [poppler for Windows](http://blog.alivate.com.au/poppler-windows/)をダウンロードして環境変数PATHに追加
  - Ubuntuの場合: `sudo apt-get install poppler-utils`
  - macOSの場合: `brew install poppler`

## セットアップ

1. 必要なPythonパッケージのインストール:
```bash
pip install -r requirements.txt
```

2. Google Cloud Projectの設定:
   - [Google Cloud Console](https://console.cloud.google.com/)で新しいプロジェクトを作成
   - Gemini APIを有効化
   - APIキーを生成

3. `.env`ファイルの作成:
```
GOOGLE_API_KEY=your_api_key_here
```

## 使用方法

```bash
python business_card_scanner.py path/to/cards.pdf --output output_directory
```

### オプション

- `pdf_path`: 処理する名刺PDFファイルのパス（必須）
- `--output`, `-o`: vCardファイルの出力ディレクトリ（デフォルト: output）

## 出力

- 指定した出力ディレクトリに、PDFの各ページごとにvCardファイル（.vcf）が生成されます
- vCardファイルには、抽出された情報と名刺画像が含まれます

## 制限事項

- PDFファイルは、スキャンされた名刺画像を含む必要があります
- 画像品質が低い場合、情報抽出の精度が低下する可能性があります
- Gemini APIの利用制限と料金が発生する可能性があります
