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

### 基本設定項目

```json
{
  "posting": {
    "use": true,                    # スケジューリング有効/無効
    "scheduleType": "interval",     # "interval"(間隔指定) または "fixed"(固定時刻)
    "startDate": "auto",            # 開始日 ("auto" または "YYYY-MM-DD")
    
    // interval モード用設定
    "interval": 0.5,                # 投稿間隔 (日数)
    "postTime": "auto",             # 投稿時刻 ("auto" または "HH:MM")
    "autoTimeOffset": 30,           # auto時のオフセット (分)
    
    // fixed モード用設定
    "fixedTimes": ["09:00", "12:00", "15:00", "18:00", "21:00"],
    
    // 共通設定
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

### スケジュール設定例

#### 間隔指定モード (interval)
```json
// 3時間おきに投稿
{
  "posting": {
    "scheduleType": "interval",
    "interval": 0.125,              // 3時間 = 0.125日
    "startDate": "auto",
    "postTime": "auto"
  }
}

// 毎日午前9時に投稿
{
  "posting": {
    "scheduleType": "interval",
    "interval": 1.0,                // 1日間隔
    "postTime": "09:00",            // 固定時刻
    "skipWeekends": true
  }
}

// 1時間おきに投稿（現在時刻から30分後開始）
{
  "posting": {
    "scheduleType": "interval", 
    "interval": 0.0417,             // 1時間 = 0.0417日
    "postTime": "auto",
    "autoTimeOffset": 30
  }
}
```

#### 固定時刻モード (fixed)
```json
// 1日5回、決まった時間に投稿
{
  "posting": {
    "scheduleType": "fixed",
    "fixedTimes": ["09:00", "12:00", "15:00", "18:00", "21:00"],
    "startDate": "auto"
  }
}

// ビジネス時間内のみ投稿
{
  "posting": {
    "scheduleType": "fixed", 
    "fixedTimes": ["10:00", "14:00", "17:00"],
    "skipWeekends": true
  }
}

// 頻繁投稿（2時間おき）
{
  "posting": {
    "scheduleType": "fixed",
    "fixedTimes": ["08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00", "22:00"]
  }
}
```

### 間隔設定の参考値

| 間隔 | interval 値 | 説明 |
|------|------------|------|
| 30分 | 0.0208 | 30分 ÷ (24時間 × 60分) |
| 1時間 | 0.0417 | 1時間 ÷ 24時間 |
| 3時間 | 0.125 | 3時間 ÷ 24時間 |
| 6時間 | 0.25 | 6時間 ÷ 24時間 |
| 12時間 | 0.5 | 12時間 ÷ 24時間 |
| 1日 | 1.0 | 24時間 ÷ 24時間 |

## 🤖 GitHub Actions

設定された投稿時刻に基づいて自動実行され、効率的な投稿スケジュールを実現します。手動実行も可能です。

### 自動実行
- **スケジュール**: 投稿時刻に応じて最適化されたcron（例：16:00投稿なら '0 16 * * *'）
- **実行内容**: 期日到来分のみ投稿
- **結果**: 投稿済みファイルを `sns/posted/` に移動してコミット

### ⚠️ 時刻設定の制限事項
- **GitHub Actions の制限**: 時刻は**1時間単位**でのみ設定可能
  - ✅ 設定可能: `09:00`, `12:00`, `15:30` → `15:00`で実行
  - ❌ 設定不可: `09:15`, `12:30`, `15:45` などの分単位指定
- **実行タイミング**: 設定時刻の5～15分後に実行される場合があります（GitHub側の負荷による）
- **推奨設定**: 毎時00分（例：`09:00`, `12:00`, `18:00`）で設定

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

### 2. スケジュール設定
```bash
# 現在の設定確認
cat configs/sns.json

# 固定時刻に投稿する場合（推奨）
{
  "posting": {
    "use": true,
    "times": ["09:00", "12:00", "18:00", "21:00"],
    "startDate": "auto",
    "skipWeekends": false
  }
}

# 1日1回投稿の場合
{
  "posting": {
    "use": true,
    "times": ["16:00"],
    "startDate": "auto",
    "skipWeekends": false
  }
}
```

### 3. スケジュール確認
```bash
# 投稿予定を確認
npm run plan
```

### 4. 自動投稿
- GitHub Actions が設定時刻に自動実行（最適化されたスケジュール）
- 期日到来分のみ投稿
- 投稿成功後、ファイルを `sns/posted/` に移動

### 5. 結果確認
- Actions タブでログ確認
- `sns/posted/` ディレクトリで投稿済みファイル確認

### スケジュール変更の手順
1. GUIから `configs/sns.json` を編集（または直接編集）
2. `npm run plan` でスケジュール確認
3. GUI の「GitHub Actions最適化」で cron を更新
4. GitHub Actions の手動実行でテスト（シミュレーションモード）
5. 問題なければ自動実行に任せる

**注意**: 時刻設定は1時間単位でのみ有効（09:15 → 09:00 で実行）

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
