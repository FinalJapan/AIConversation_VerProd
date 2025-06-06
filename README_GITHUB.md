# 🤖 AI同士の会話観察システム

ChatGPT、Claude、Geminiが自動で会話する様子をリアルタイムで観察できるWebアプリです。

## ✨ 特徴

- **AI同士の自動会話**: 3つのAIがランダムに自動で会話
- **ChatGPTライクなUI**: 白い背景で見やすいインターface
- **AI別色分け表示**: 話者が一目で分かる色分けデザイン
- **リアルタイム費用監視**: トークン使用量とAPI費用をリアルタイム表示
- **安全な費用制限**: 設定可能なトークン上限で費用暴走を防止

## 🎨 スクリーンショット

- 🤖 **ChatGPT**: 青系の背景
- 🧠 **Claude**: オレンジ系の背景  
- ⭐ **Gemini**: 緑系の背景

## 🚀 クイックスタート

### 方法1: Streamlit Cloud（推奨）

1. **このリポジトリをフォーク**
2. **Streamlit Cloudにデプロイ**:
   - [Streamlit Cloud](https://streamlit.io/cloud) にアクセス
   - GitHubと連携してこのリポジトリを選択
   - `streamlit_app.py` を指定してデプロイ
3. **APIキーを設定**: アプリのサイドバーで各自のAPIキーを入力

### 方法2: ローカル実行

```bash
# 1. リポジトリをクローン
git clone https://github.com/yourusername/ai-conversation-system.git
cd ai-conversation-system

# 2. 仮想環境を作成・有効化
python -m venv ai_chat_env
source ai_chat_env/bin/activate  # Windows: ai_chat_env\Scripts\activate

# 3. 依存関係をインストール
pip install -r requirements.txt

# 4. Streamlitアプリを起動
streamlit run streamlit_app.py
```

## 🔑 APIキー設定

### 必要なAPIキー（最低2つ）

| AI | APIキー取得先 | 料金 | 備考 |
|---|---|---|---|
| **ChatGPT** | [OpenAI Platform](https://platform.openai.com/api-keys) | 20,000トークンで約$0.1-0.3 | 従量課金 |
| **Claude** | [Anthropic Console](https://console.anthropic.com/) | 20,000トークンで約$0.15-0.75 | 要事前クレジット購入（最低$5） |
| **Gemini** | [Google AI Studio](https://makersuite.google.com/app/apikey) | 無料枠内では$0 | 無料枠あり |

### 設定方法

#### Streamlit Cloud / オンライン使用
- アプリのサイドバーで直接APIキーを入力（推奨）
- セキュア：ブラウザのセッションのみに保存

#### ローカル使用
1. `env_example.txt` をコピーして `.env` ファイルを作成
2. APIキーを設定
```bash
cp env_example.txt .env
# .envファイルを編集してAPIキーを設定
```

## 💰 料金について

### 概算料金（20,000トークン使用時）
- **ChatGPT-4o**: $0.10 - $0.30
- **Claude 3.5 Sonnet**: $0.15 - $0.75
- **Gemini 2.0 Flash**: 無料枠内では$0

### 費用制御機能
- ✅ トークン使用量のリアルタイム表示
- ✅ 90%到達時の警告
- ✅ 100%到達時の自動停止
- ✅ 設定可能な上限（20,000 / 50,000 / カスタム）

## 🛡️ セキュリティ

### APIキー保護
- ✅ `.env`ファイルは`.gitignore`で除外
- ✅ StreamlitのセッションレベルでAPIキー管理
- ✅ ユーザーが各自のAPIキーを設定
- ✅ 開発者のAPIキーは一切含まれません

### 注意事項
⚠️ **APIキーは絶対に他人と共有しないでください**  
⚠️ **公開リポジトリにAPIキーをコミットしないでください**  
⚠️ **使用後は必ずAPIキーをリセットしてください**

## 📁 プロジェクト構造

```
ai-conversation-system/
├── streamlit_app.py      # メインのStreamlitアプリ
├── main.py               # コマンドライン版
├── config.py             # 設定管理
├── llm_manager.py        # LLM API管理
├── cost_monitor.py       # コスト監視
├── logger.py             # ログ管理
├── requirements.txt      # 依存関係
├── env_example.txt       # APIキー設定テンプレート
├── .gitignore           # Git除外設定
└── README.md            # このファイル
```

## 🔧 カスタマイズ

### テーマの追加
`streamlit_app.py`の`theme_presets`リストに新しいテーマを追加できます。

### AI の追加
`llm_manager.py`で新しいLLMクラスを作成し、`LLMManager`に追加できます。

### UI色の変更
`streamlit_app.py`のCSSセクションで各AIの色を変更できます。

## 🌐 デプロイ方法

### Streamlit Cloud
1. GitHubリポジトリを作成
2. [Streamlit Cloud](https://streamlit.io/cloud) でアプリを作成
3. リポジトリを選択し、`streamlit_app.py`を指定

### Heroku
```bash
# Procfileを作成
echo "web: streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0" > Procfile

# デプロイ
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

### Railway / Render
同様の手順でデプロイ可能です。

## 🐛 トラブルシューティング

### よくある問題

**Q: APIキーエラーが出る**  
A: 正しいAPIキーが設定されているか、残高があるかを確認してください。

**Q: Claudeで「クレジット不足」エラー**  
A: Anthropic Consoleで事前にクレジット（最低$5）を購入してください。

**Q: 最低2つのLLMが必要です**  
A: 最低2つのAPIキーを正しく設定してください。

**Q: 会話が途中で止まる**  
A: トークン上限に達した可能性があります。上限を増やすか、新しいセッションを開始してください。

## 📄 ライセンス

MIT License

## 🤝 コントリビューション

プルリクエストやイシューの報告を歓迎します！

## ⚠️ 免責事項

- API使用料金は各ユーザーの責任です
- 本ツールの使用による費用や損害について開発者は責任を負いません
- APIの利用規約を遵守してご利用ください

## 📞 サポート

問題がある場合は[Issues](https://github.com/yourusername/ai-conversation-system/issues)で報告してください。

---

🌟 **このプロジェクトが気に入ったらスターをお願いします！** 🌟 