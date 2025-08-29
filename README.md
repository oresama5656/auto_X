# auto_X - X (Twitter) 自動投稿システム

GitHub Actionsを使用してX (Twitter)への自動投稿を行うシステムです。PCを常時稼働させることなく、スケジュールに基づいた投稿を実現します。

## 🏗️ システム概要

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   sns/*.txt     │───▶│ GitHub Actions   │───▶│   X (Twitter)   │
│  (投稿待ち)      │    │ (スケジュール実行)  │    │   API投稿       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        │                        ▼
┌─────────────────┐              │              ┌─────────────────┐
│ sns/posted/     │              │              │    投稿完了     │
│ (投稿済み)       │◀─────────────┘              │   (201応答)     │
└─────────────────┘                             └─────────────────┘
```

## 📁 ディレクトリ構成

```
auto_X/
├── core/                   # コアロジック
│   ├── oauth.js           # OAuth 1.0a 署名
│   ├── twitter-api.js     # X API クライアント
│   ├── scheduler.js       # スケジュール計算
│   ├── file-manager.js    # ファイル操作
│   ├── config.js          # 設定管理
│   ├── logger.js          # ログ機能
│   └── index.js           # コア API
├── cli/                   # CLI インターフェース
│   └── index.js           # コマンドライン実行
├── scripts/               # 互換スクリプト
│   └── post-to-sns.js     # レガシーランチャー
├── configs/               # 設定ファイル
│   └── sns.json           # 投稿スケジュール設定
├── sns/                   # 投稿ファイル
│   ├── *.txt             # 投稿待ちファイル
│   └── posted/           # 投稿済みファイル
├── logs/                  # ログファイル
├── .github/workflows/     # GitHub Actions
│   └── sns.yml           # 自動投稿ワークフロー
└── __tests__/            # テストファイル
```

## 🚀 セットアップ手順

### 1. リポジトリの準備

```bash
# 依存関係のインストール
npm install

# 設定ファイルの確認
cat configs/sns.json
```

### 2. X (Twitter) API 設定

X Developer Portal でアプリケーションを作成し、以下の認証情報を取得してください：

- API Key
- API Key Secret
- Access Token
- Access Token Secret

### 3. GitHub Secrets の設定

リポジトリの Settings > Secrets and variables > Actions で以下のシークレットを設定：

```
TW_API_KEY=your_api_key_here
TW_API_KEY_SECRET=your_api_key_secret_here
TW_ACCESS_TOKEN=your_access_token_here
TW_ACCESS_TOKEN_SECRET=your_access_token_secret_here
```

### 4. 投稿ファイルの準備

`sns/` ディレクトリに `.txt` ファイルを配置：

```bash
echo "初回投稿テストです 🚀" > sns/001-sns.txt
echo "自動投稿システムが動作中です ⚡" > sns/002-sns.txt
```

### 5. 動作確認

```bash
# ファイル検証
npm run lint

# スケジュール確認
npm run plan

# シミュレーション実行
npm run run

# 実投稿（期日到来分のみ）
node cli/index.js run --due-only
```

## ⚙️ 設定ファイル (configs/sns.json)

```json
{
  "posting": {
    "use": true,                    # スケジューリング有効/無効
    "startDate": "auto",            # 開始日 ("auto" または "YYYY-MM-DD")
    "interval": 0.5,                # 投稿間隔 (日数)
    "postTime": "auto",             # 投稿時刻 ("auto" または "HH:MM")
    "autoTimeOffset": 30,           # auto時のオフセット (分)
    "skipWeekends": false           # 週末スキップ
  },
  "twitterApi": {
    "apiKey": "",                   # 環境変数優先
    "apiKeySecret": "",
    "accessToken": "",
    "accessTokenSecret": ""
  }
}
```

### 設定例

```json
// 毎日午前9時に投稿
{
  "posting": {
    "use": true,
    "startDate": "2024-01-01",
    "interval": 1.0,
    "postTime": "09:00",
    "skipWeekends": true
  }
}

// 12時間間隔で投稿（現在時刻から30分後開始）
{
  "posting": {
    "use": true,
    "startDate": "auto",
    "interval": 0.5,
    "postTime": "auto",
    "autoTimeOffset": 30
  }
}
```

## 🤖 GitHub Actions

毎日 09:00 JST に自動実行されます。手動実行も可能です。

### 自動実行
- **スケジュール**: 毎日 09:00 JST (cron: '0 0 * * *')
- **実行内容**: 期日到来分のみ投稿
- **結果**: 投稿済みファイルを `sns/posted/` に移動してコミット

### 手動実行
1. GitHub リポジトリの Actions タブを開く
2. "X (Twitter) Auto Posting" ワークフローを選択
3. "Run workflow" ボタンをクリック
4. シミュレーションモードの選択（true/false）

## 📝 運用フロー

### 1. 投稿ファイルの準備
```bash
# ファイルを sns/ ディレクトリに配置
echo "新しい投稿内容です" > sns/003-sns.txt

# 文字数チェック
npm run lint
```

### 2. スケジュール確認
```bash
# 投稿予定を確認
npm run plan
```

### 3. 自動投稿
- GitHub Actions が毎日自動実行
- 期日到来分のみ投稿
- 投稿成功後、ファイルを `sns/posted/` に移動

### 4. 結果確認
- Actions タブでログ確認
- `sns/posted/` ディレクトリで投稿済みファイル確認

## 🛠️ CLI コマンド

```bash
# スケジュール計画表示
node cli/index.js plan

# シミュレーション実行
node cli/index.js run

# 実投稿（期日到来分のみ）
node cli/index.js run --due-only

# ファイル検証
node cli/index.js lint

# 設定移行（旧→新形式）
node cli/index.js migrate-config
```

### オプション

```bash
# 設定ファイル指定
node cli/index.js run -c custom/config.json

# SNSディレクトリ指定
node cli/index.js run -s custom/sns/

# ログ保存
node cli/index.js run --due-only --save-log
```

## 🔒 セキュリティ注意事項

### API キー管理
- **推奨**: GitHub Secrets に設定
- **非推奨**: 設定ファイルに直接記入
- ログにAPIキーが出力されないよう実装済み

### GitHub Actions 設定
- **権限最小化**: `permissions: contents: read`
- **Pull Request トリガー禁止**: フォークからの悪意あるPRを防止
- **Secrets アクセス制限**: mainブランチからのみアクセス可能

### コードレビュー
```bash
# セキュリティチェック用コマンド
grep -r "API\|SECRET\|TOKEN" . --exclude-dir=node_modules --exclude-dir=.git
```

## 🐛 トラブルシューティング

### 文字数超過
```bash
# 問題: 280文字を超過
npm run lint
# → エラー詳細が表示される

# 対策: ファイル内容を編集
nano sns/long-post.txt
```

### API 権限エラー
```
エラー: HTTP 403: Forbidden
```
**原因**: API キーの権限不足
**対策**: X Developer Portal で Read and Write 権限を確認

### 時刻ズレ問題
```bash
# JSTで現在時刻確認
TZ=Asia/Tokyo date

# 設定の postTime を調整
# "postTime": "09:00" → 毎日9時
# "postTime": "auto" → 現在時刻+オフセット
```

### API エンドポイントエラー
システムは自動的にフォールバック:
1. `api.x.com` (第一候補)
2. `api.twitter.com` (フォールバック)

### レート制限対策
- 429エラー時: 指数バックオフ (1.5s → 3s → 6s → ... 最大45s)
- 5xxエラー時: 同様にリトライ

## 🧪 テスト

```bash
# 全テスト実行
npm test

# 個別テスト
npm test oauth
npm test scheduler
npm test config

# ウォッチモード
npm run test:watch
```

## 📊 機能仕様

### 文字数制限
- **上限**: 280文字 (Unicodeコードポイントベース)
- **超過時**: `...` で自動切り詰め
- **検証**: `npm run lint` でチェック

### スケジューリング
- **タイムゾーン**: Asia/Tokyo 固定
- **間隔**: 日数指定（小数点対応）
- **週末スキップ**: 設定で有効/無効
- **開始時刻**: 固定時刻 or 実行時刻からのオフセット

### エラーハンドリング
- **OAuth 1.0a**: RFC3986準拠
- **レート制限**: 指数バックオフリトライ
- **ファイル操作**: 失敗時はバックアップ保持
- **ログ出力**: JST時刻、詳細レベル対応

## 📄 ライセンス

MIT License

## 🤝 コントリビューション

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 サポート

- **Issues**: バグ報告・機能要望
- **Discussions**: 使用方法・質問
- **Wiki**: 詳細ドキュメント (準備中)
