# LLMマルチ会話システム

AI同士の自動会話を観察するためのツール

## 概要

3つのAI（ChatGPT, Claude, Gemini）が自動でランダムな順序で会話を行い、ユーザーはその会話を観察して楽しむことができるシステムです。従量課金APIの費用暴走を防ぐため、トークン数で制限を設けています。

## 主な機能

✨ **AI同士の自動会話**
- ChatGPT、Claude、Geminiがランダムな順序で自動会話
- 直前の発言者は次の発言から除外（連続発言防止）
- ユーザーは観察のみで介入なし

💰 **リアルタイムコスト監視**
- トークン使用量とAPI費用をリアルタイム表示
- 90%到達時に警告、100%で自動停止
- 各発言ごとのトークン数・費用表示

📊 **自動停止機能**
- 50,000 または 100,000 tokens で上限設定可能
- 緊急停止機能（Ctrl+C）

📝 **会話ログ記録**
- テキスト形式とJSON形式で自動保存
- 発言者別の色分け表示
- セッション統計の自動計算

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. APIキーの設定

`env_example.txt`を参考に`.env`ファイルを作成し、以下のAPIキーを設定してください：

```bash
# .env ファイル
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here  
GOOGLE_API_KEY=your_google_api_key_here
```

### 3. APIキーの取得方法

- **OpenAI (ChatGPT)**: https://platform.openai.com/api-keys
- **Anthropic (Claude)**: https://console.anthropic.com/
- **Google (Gemini)**: https://makersuite.google.com/app/apikey

## 使用方法

### 基本実行

```bash
python main.py
```

実行すると対話的なセットアップが開始されます：

1. **トークン上限の選択**
   - 50,000 tokens (推奨)
   - 100,000 tokens  
   - カスタム

2. **会話テーマの設定**
   - 例：「哲学について議論」「SFについて語り合う」「料理のレシピ開発」

### 操作方法

- **観察**: AI同士の会話を自動で観察
- **緊急停止**: `Ctrl+C` で即座に停止
- **ログ確認**: `logs/` フォルダに自動保存

## ファイル構成

```
AIchat/
├── main.py              # メイン実行ファイル
├── config.py            # 設定管理
├── llm_manager.py       # LLM API管理
├── cost_monitor.py      # コスト監視
├── logger.py            # ログ管理
├── requirements.txt     # 依存関係
├── env_example.txt      # 環境変数テンプレート
├── README.md           # このファイル
└── logs/               # ログフォルダ（自動作成）
    ├── conversation_YYYYMMDD_HHMMSS.txt
    └── conversation_YYYYMMDD_HHMMSS.json
```

## 料金について

### API使用料金（2024年12月時点）

- **ChatGPT-4o**: Input $2.50/1M, Output $10.00/1M tokens
- **Claude 3.5 Sonnet**: Input $3.00/1M, Output $15.00/1M tokens  
- **Gemini 2.0 Flash**: 無料枠内は監視対象外

### 費用目安

- **50,000 tokens**: 約 $0.25-0.75
- **100,000 tokens**: 約 $0.50-1.50

*実際の費用は会話内容や各AIの応答長により変動します*

## 安全機能

🛡️ **費用の暴走防止**
- トークン数による厳格な上限設定
- 90%到達時の警告表示
- 100%到達時の自動停止

🚨 **緊急停止機能**
- Ctrl+C による即座の停止
- 部分的なログも保護・保存

📊 **リアルタイム監視**
- 累計トークン数とコストの表示
- 各発言ごとの詳細統計
- モデル別使用量の分析

## トラブルシューティング

### APIキーエラー
```
❌ 以下のAPIキーが設定されていません: OPENAI_API_KEY
```
→ `.env`ファイルにAPIキーを正しく設定してください

### 初期化失敗
```
❌ ChatGPT 初期化失敗: Invalid API key
```
→ APIキーが正しいか、残高があるか確認してください

### 最低LLM数不足
```
⚠️ 会話には最低2つのLLMが必要です
```
→ 少なくとも2つのAPIキーを設定してください

## カスタマイズ

### 設定変更

`config.py` でシステム設定をカスタマイズできます：

- `max_response_length`: 最大応答文字数
- `response_wait_time`: API応答待機時間
- `warning_threshold`: 警告閾値（デフォルト90%）

### 新しいLLMの追加

`llm_manager.py` の `BaseLLM` クラスを継承して新しいLLMを追加できます。

## ライセンス

MIT License

## 注意事項

- このツールは観察・学習目的での使用を想定しています
- 商用利用時は各APIの利用規約を確認してください
- 長時間の放置実行は推奨しません
- API使用料は自己責任でお願いします

## サポート

問題が発生した場合は、以下を確認してください：

1. APIキーが正しく設定されているか
2. 必要な依存関係がインストールされているか
3. API残高が十分にあるか
4. インターネット接続が安定しているか

---

🤖 **楽しいAI観察体験をお楽しみください！** 