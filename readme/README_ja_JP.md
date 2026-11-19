# Dify 用 Box プラグイン

**作者:** kota-maeda0708
**バージョン:** 0.0.3
**タイプ:** ツール
**ソースリポジトリ:** https://github.com/kota-maeda0708/dify-plugin-box-tools

## 概要

Box プラグインを使うと、Dify アプリケーションから [Box](https://www.box.com/) のファイルとフォルダを操作できます。
Box 上のアイテムの一覧表示、検索、アップロード、ダウンロード、フォルダ作成、削除、移動・リネームを行う AI アプリケーションを作成できます。

## 機能

- **ファイル・フォルダ一覧（List Files）**: Box アカウント内の任意のフォルダの中身を表示
- **ファイル検索（Search Files）**: キーワードに一致するファイルとフォルダを検索
- **ファイルアップロード（Upload File）**: ファイル入力、プレーンテキスト、または base64 エンコードされた内容から Box に新しいファイルを作成
- **ファイルダウンロード（Download File）**: Box のファイルを、後続ノードで使える Dify ファイルとして取得
- **フォルダ作成（Create Folder）**: 新しいフォルダを作成して Box アカウントを整理
- **ファイル・フォルダ削除（Delete Item）**: Box からファイルやフォルダを削除
- **移動・リネーム（Move / Rename Item）**: アイテムを別のフォルダに移動、または名前を変更

## Box の ID について

Box はアイテムをパスではなく **数値の ID** で指定します。

- **ルートフォルダ** の ID は常に `0` です。
- すべてのファイルとフォルダに固有の ID があります。

**List Files**（ルートフォルダ `0` から始めます）または **Search Files** で操作したいアイテムの ID を調べ、その ID を他のツールに渡してください。

## 認証

このプラグインは **2 種類** の認証方法に対応しており、プラグインの設定時に選択できます。

### 1. OAuth 2.0（ユーザー認証）

1. [Box Developer Console](https://app.box.com/developers/console) で、アプリの種類に **OAuth 2.0（ユーザー認証）** を選んで Box アプリを作成します。
2. Dify に表示されるリダイレクト URI を、アプリの OAuth 2.0 リダイレクト URI 設定に追加します。
3. アプリの **Client ID** と **Client Secret** を控えます。
4. Dify で OAuth の認証方法を選び、Client ID と Client Secret を入力してから、ブラウザで認可を完了します。Dify は取得したアクセストークンとリフレッシュトークンを保存し、アクセストークンの期限が切れると自動で更新します。

### 2. シークレットキー（Client Credentials Grant / サーバー認証）

1. [Box Developer Console](https://app.box.com/developers/console) で、アプリの種類に **サーバー認証（Client Credentials Grant）** を選んで Box アプリを作成し、Box 管理コンソールでアプリを承認します。
2. アプリの **Client ID** と **Client Secret** を控えます。
3. Box の **Enterprise ID**（特定のユーザーとして操作する場合はその **User ID**）を控えます。
4. Dify でシークレットキーの認証方法を選び、Client ID、Client Secret、サブジェクトタイプ（`enterprise` または `user`）と、それに対応する Enterprise ID / User ID を入力します。この方法はブラウザでのリダイレクトが不要で、サーバー間の連携に適しています。

## ファイルの扱い

- **Download File** は、base64 のテキストではなく実際の Dify ファイルとして返すため、ドキュメント抽出、LLM の画像認識、別のアップロード処理などの後続ノードやツールに直接つなげられます。
- **Upload File** は `File` 入力（チャットでアップロードされたファイルや、Download File など別のツールの出力）を受け付けます。ファイルを指定しない場合は、プレーンテキストを入力するか、base64 エンコードされた内容を直接貼り付けることもできます。
- Upload File が使う Box のシンプルアップロードは、**50MB** までのファイルに対応しています。それより大きいファイルは、このバージョンのプラグインではアップロードできません。Download File は、メモリの使いすぎを防ぐため **100MB** を超えるファイルのダウンロードを行いません。

## 出力変数

ワークフローでは、**List Files** と **Search Files** は通常の `text` と `json` に加えて、結果を出力変数として返します。そのため、コードノードで結果を分解する必要はありません。

| 変数 | 型 | 説明 |
| --- | --- | --- |
| `items` | `array[object]` | 各アイテムの `id`、`name`、`type`、`size`、`created_at`、`modified_at` |
| `file_ids` | `array[string]` | ファイルだけの ID 一覧（フォルダは除く）。イテレーションで Download File に渡せます |
| `folder_ids` | `array[string]` | フォルダだけの ID 一覧（ファイルは除く）。イテレーションで List Files に渡せます |
| `count` | `integer` | 返されたアイテムの件数（ファイル、フォルダ、ウェブリンクを含む） |
| `file_count` | `integer` | 返されたファイルの件数 |
| `folder_count` | `integer` | 返されたフォルダの件数 |
| `has_more` | `boolean` | 返されたより多くのアイテムがあると Box が示したとき true（結果が途中まで） |
| `success` | `boolean` | エラーで止まったとき false |
| `error` | `string` | 止まった理由。成功時は空文字 |

`json` の出力は変わらないため、`json` を参照している既存のワークフローはそのまま動きます。

注意点:

- **`has_more` が true のときは、結果が途中までです。** 返されるのは最初の `limit` 件だけで、`file_ids`、`folder_ids` と各件数もその分だけです。List Files はフォルダ、ファイル、ウェブリンクの順に返すため、`limit` が小さいと、フォルダにファイルがあっても `file_ids` が空になることがあります。すべてを処理したい場合は、`limit` をアイテム数より大きくするか、`has_more` を確認して true のときに処理を止めるか警告を出してください。
- **`limit` の範囲。** List Files は 1〜1000（デフォルト 100）、Search Files は 1〜200（デフォルト 20）で、Box API の上限に合わせています。上限を超えた値は上限として扱います。整数でない値を指定すると、ツールは `success` を false にして止まります。
- **エラーでもノードは失敗になりません。** Box がエラーを返しても、ツールノードは成功として終わるため、ノードの「失敗ブランチ」によるエラー処理は動きません。代わりに IF/ELSE ノードで `success` を判定してください。理由は `error` に入ります。エラー時もすべての変数が空の値（`[]`、`0`、`false`、`""`）で出力されるため、後続ノードで変数が見つからないことはありません。
- 検索結果は名前の順ではなく、Box が判断した関連度の高い順に並びます。

### 例: フォルダ内のファイルをすべてダウンロードする

1. フォルダの ID を指定して **List Files** を実行します。
2. **イテレーション** の入力に、List Files の `file_ids` を指定します。
3. イテレーションの中で **Download File** を実行し、`file_id` にイテレーションの現在の要素を指定します。
4. イテレーションの出力に Download File の `files` を指定すると、ダウンロードしたファイルをまとめて受け取れます。

サブフォルダの中まで処理するには、`folder_ids` を別のイテレーションに渡し、その中で List Files を実行します。

## 使用例

### Box のルートフォルダのファイルを一覧表示する
```
List all files in my Box (folder 0)
```

### 特定のファイルを検索する
```
Find all PDF files in my Box
```

### 新しいファイルをアップロードする
```
Upload a file named "meeting-notes.txt" to my Box with the content "Meeting scheduled for next Tuesday"
```

### ファイルの内容をダウンロードする
```
Download the Box file with ID 123456789
```

### フォルダを作成する
```
Create a folder named "Reports" in my Box root folder
```

### アイテムを削除する
```
Delete the Box file with ID 123456789
```

### ファイルを移動またはリネームする
```
Rename the Box file with ID 123456789 to "final-report.pdf"
```
```
Move the Box file with ID 123456789 into folder 987654321
```

## 必要なもの

- Box アカウント
- Box アプリ（OAuth 2.0 アプリ、または Client Credentials Grant アプリ）
- Dify プラットフォーム

## テストの実行

```bash
uv sync
uv run --with pytest python -m pytest -q tests
```
