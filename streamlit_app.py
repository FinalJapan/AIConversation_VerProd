#!/usr/bin/env python3
"""
LLMマルチ会話システム - Streamlit Web UI
AI同士の自動会話を観察するためのWebアプリ
"""

import streamlit as st
import time
import threading
from datetime import datetime
from typing import Optional

from config import setup_config, config
from cost_monitor import create_cost_monitor
from logger import create_logger
from llm_manager import create_llm_manager

# ページ設定（背景を白に）
st.set_page_config(
    page_title="AI同士の会話を観察",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS（ダークテーマ対応）
st.markdown("""
<style>
/* Streamlit テーマ変数を使用したスタイリング */
:root {
    --text-color: var(--text-color, #262730);
    --background-color: var(--background-color, #FFFFFF);
    --secondary-background-color: var(--secondary-background-color, #F0F2F6);
    --primary-color: var(--primary-color, #FF4B4B);
}

/* ダークテーマ対応 */
@media (prefers-color-scheme: dark) {
    :root {
        --text-color: #FAFAFA;
        --background-color: #0E1117;
        --secondary-background-color: #262730;
    }
}

/* Streamlitのダークテーマクラス対応 */
.stApp[data-theme="dark"] {
    --text-color: #FAFAFA !important;
    --background-color: #0E1117 !important;
    --secondary-background-color: #262730 !important;
}

.stApp[data-theme="light"] {
    --text-color: #262730 !important;
    --background-color: #FFFFFF !important;
    --secondary-background-color: #F0F2F6 !important;
}

/* メイン背景 */
.main {
    background-color: var(--background-color);
    color: var(--text-color);
}

/* チャットメッセージのベーススタイル */
.chat-message {
    padding: 1rem;
    border-radius: 10px;
    margin: 0.5rem 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    color: var(--text-color) !important;
    background-color: var(--secondary-background-color);
    border: 1px solid rgba(255,255,255,0.1);
}

/* ChatGPTスタイル（青系） */
.chatgpt-message {
    background: linear-gradient(135deg, #4285f4 0%, #34a853 100%);
    background-size: 200% 200%;
    border-left: 4px solid #4285f4;
    color: #ffffff !important;
    box-shadow: 0 2px 8px rgba(66, 133, 244, 0.3);
}

.chatgpt-message * {
    color: #ffffff !important;
}

/* Claudeスタイル（オレンジ系） */
.claude-message {
    background: linear-gradient(135deg, #ff8c00 0%, #ff6b35 100%);
    background-size: 200% 200%;
    border-left: 4px solid #ff8c00;
    color: #ffffff !important;
    box-shadow: 0 2px 8px rgba(255, 140, 0, 0.3);
}

.claude-message * {
    color: #ffffff !important;
}

/* Geminiスタイル（緑〜紫のグラデーション） */
.gemini-message {
    background: linear-gradient(135deg, #00c851 0%, #9c27b0 100%);
    background-size: 200% 200%;
    border-left: 4px solid #00c851;
    color: #ffffff !important;
    box-shadow: 0 2px 8px rgba(0, 200, 81, 0.3);
}

.gemini-message * {
    color: #ffffff !important;
}

/* システムメッセージ */
.system-message {
    background-color: var(--secondary-background-color);
    border-left: 4px solid #6c757d;
    color: var(--text-color) !important;
    font-style: italic;
    opacity: 0.8;
}

.system-message * {
    color: var(--text-color) !important;
}

/* アイコン */
.speaker-icon {
    font-size: 1.2em;
    margin-right: 0.5rem;
    filter: drop-shadow(0 0 2px rgba(0,0,0,0.3));
}

/* ステータスバー */
.status-bar {
    background-color: var(--secondary-background-color);
    color: var(--text-color);
    padding: 1rem;
    border-radius: 5px;
    border: 1px solid rgba(255,255,255,0.1);
}

/* プログレスバー */
.progress-bar {
    margin: 1rem 0;
}

/* Streamlit 要素のテーマ対応 */
.stMarkdown, .stText, .stCaption {
    color: var(--text-color) !important;
}

/* メトリクス */
.metric-container {
    background-color: var(--secondary-background-color);
    padding: 0.5rem;
    border-radius: 0.5rem;
    border: 1px solid rgba(255,255,255,0.1);
}

/* インフォメーションボックスの改善 */
.stInfo, .stSuccess, .stWarning, .stError {
    color: var(--text-color) !important;
}

/* ボタンのホバー効果 */
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    transition: all 0.2s ease;
}

/* セレクトボックス */
.stSelectbox > div > div {
    background-color: var(--secondary-background-color);
    color: var(--text-color);
}

/* テキスト入力 */
.stTextInput > div > div > input {
    background-color: var(--secondary-background-color);
    color: var(--text-color);
    border: 1px solid rgba(255,255,255,0.2);
}

/* スライダー */
.stSlider > div > div > div {
    color: var(--text-color);
}

/* エキスパンダー */
.streamlit-expanderHeader {
    background-color: var(--secondary-background-color);
    color: var(--text-color);
}

/* チャットメッセージのアニメーション */
@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateX(-20px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

.chat-message {
    animation: slideIn 0.3s ease-out;
}

/* 高度なグラデーション効果 */
.chatgpt-message {
    animation: gradientShift 3s ease infinite;
}

.claude-message {
    animation: gradientShift 3s ease infinite;
}

.gemini-message {
    animation: gradientShift 3s ease infinite;
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* レスポンシブ対応 */
@media (max-width: 768px) {
    .chat-message {
        padding: 0.8rem;
        margin: 0.3rem 0;
    }
    
    .speaker-icon {
        font-size: 1rem;
    }
}

/* ダークテーマでのコントラスト強化 */
@media (prefers-color-scheme: dark) {
    .chat-message {
        box-shadow: 0 2px 10px rgba(255,255,255,0.1);
    }
    
    .stButton > button {
        border: 1px solid rgba(255,255,255,0.2);
    }
}

/* 印刷対応 */
@media print {
    .chat-message {
        background: white !important;
        color: black !important;
        box-shadow: none;
        border: 1px solid #ccc;
    }
}
</style>
""", unsafe_allow_html=True)

def get_speaker_style(speaker: str) -> tuple[str, str]:
    """話者に応じたスタイルとアイコンを取得"""
    styles = {
        "ChatGPT": ("chatgpt-message", "🤖"),
        "Claude": ("claude-message", "🧠"),
        "Gemini": ("gemini-message", "⭐"),
    }
    return styles.get(speaker, ("system-message", "❓"))

def display_message(speaker: str, content: str, tokens: int, cost: float):
    """メッセージを表示（ダークテーマ対応版）"""
    style_class, icon = get_speaker_style(speaker)
    
    # タイムスタンプ
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # カスタムHTMLでメッセージを表示
    message_html = f"""
    <div class="chat-message {style_class}">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <div style="display: flex; align-items: center;">
                <span class="speaker-icon">{icon}</span>
                <strong style="font-size: 1.1em;">{speaker}</strong>
            </div>
            <div style="font-size: 0.8em; opacity: 0.8;">
                {tokens} tokens | ${cost:.4f} | {timestamp}
            </div>
        </div>
        <div style="line-height: 1.6; white-space: pre-wrap; word-wrap: break-word;">
            {content.replace('<', '&lt;').replace('>', '&gt;')}
        </div>
    </div>
    """
    
    # HTMLを表示
    st.markdown(message_html, unsafe_allow_html=True)
    
    # 追加のStreamlitコンポーネント表示（テーマ対応）
    with st.container():
        # 詳細情報をエキスパンダーで表示
        with st.expander(f"📊 {speaker}の詳細情報", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("トークン数", tokens)
            
            with col2:
                st.metric("コスト", f"${cost:.4f}")
            
            with col3:
                st.metric("文字数", len(content))
            
            with col4:
                st.metric("送信時刻", timestamp)
            
            # メッセージの感情分析（簡易版）
            if any(word in content.lower() for word in ['!', '？', 'すごい', 'great', 'excellent']):
                sentiment = "😊 ポジティブ"
            elif any(word in content.lower() for word in ['問題', 'error', '困', '難しい']):
                sentiment = "😟 ネガティブ"
            else:
                sentiment = "😐 中性"
            
            st.info(f"感情分析: {sentiment}")
    
    # 区切り線
    st.markdown("---")

def display_status(cost_monitor):
    """ステータス表示"""
    status = cost_monitor.get_status_summary()
    percentage = status['usage_percentage']
    
    # プログレスバー
    progress_color = "red" if percentage >= 100 else "orange" if percentage >= 90 else "green"
    st.progress(min(percentage / 100, 1.0))
    
    # ステータス情報
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("トークン使用量", f"{status['total_tokens']:,}", 
                 f"/ {cost_monitor.token_limit:,}")
    
    with col2:
        st.metric("使用率", f"{percentage:.1f}%")
    
    with col3:
        st.metric("総コスト", f"${status['total_cost_usd']:.4f}")
    
    with col4:
        st.metric("残りトークン", f"{status['remaining_tokens']:,}")

def initialize_session_state():
    """セッション状態を初期化"""
    if 'conversation_active' not in st.session_state:
        st.session_state.conversation_active = False
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'total_messages' not in st.session_state:
        st.session_state.total_messages = 0
    if 'session_config' not in st.session_state:
        st.session_state.session_config = None
    if 'cost_monitor' not in st.session_state:
        st.session_state.cost_monitor = None
    if 'llm_manager' not in st.session_state:
        st.session_state.llm_manager = None
    if 'auto_step' not in st.session_state:
        st.session_state.auto_step = False
    if 'last_message_time' not in st.session_state:
        st.session_state.last_message_time = None
    if 'conversation_paused' not in st.session_state:
        st.session_state.conversation_paused = False
    if 'auto_mode' not in st.session_state:
        st.session_state.auto_mode = "半自動（3秒間隔）"
    if 'message_counter' not in st.session_state:
        st.session_state.message_counter = 0
    if 'max_messages' not in st.session_state:
        st.session_state.max_messages = 50  # デフォルト最大メッセージ数

def setup_sidebar():
    """サイドバーのセットアップ"""
    with st.sidebar:
        st.title("🤖 AI会話設定")
        
        # APIキー設定セクション
        st.subheader("🔑 APIキー設定")
        st.info("⚠️ 各ユーザーが自分のAPIキーを設定してください")
        
        # OpenAI API Key
        openai_key = st.text_input(
            "OpenAI API Key (ChatGPT用)",
            type="password",
            help="https://platform.openai.com/api-keys から取得"
        )
        
        # Anthropic API Key
        anthropic_key = st.text_input(
            "Anthropic API Key (Claude用)",
            type="password", 
            help="https://console.anthropic.com/ から取得（要クレジット購入）"
        )
        
        # Google API Key
        google_key = st.text_input(
            "Google API Key (Gemini用)",
            type="password",
            help="https://makersuite.google.com/app/apikey から取得"
        )
        
        # APIキーをセッション状態に保存
        if openai_key:
            st.session_state.openai_api_key = openai_key
        if anthropic_key:
            st.session_state.anthropic_api_key = anthropic_key
        if google_key:
            st.session_state.google_api_key = google_key
        
        # APIキー設定状況の表示
        api_keys_set = []
        if openai_key:
            api_keys_set.append("✅ OpenAI (ChatGPT)")
        if anthropic_key:
            api_keys_set.append("✅ Anthropic (Claude)")
        if google_key:
            api_keys_set.append("✅ Google (Gemini)")
        
        if api_keys_set:
            st.success(f"設定済み: {', '.join(api_keys_set)}")
        else:
            st.warning("最低2つのAPIキーが必要です")
        
        st.divider()
        
        # トークン制限設定
        st.subheader("📊 トークン制限")
        token_options = {"20,000 tokens (推奨)": 20000, "50,000 tokens": 50000}
        selected_option = st.selectbox("制限を選択", list(token_options.keys()))
        token_limit = token_options[selected_option]
        
        # カスタム設定
        if st.checkbox("カスタム設定"):
            token_limit = st.number_input("カスタムトークン数", min_value=1000, max_value=200000, value=20000)
        
        # テーマ設定
        st.subheader("🎯 会話テーマ")
        theme_presets = [
            "一般的な話題について自由に議論",
            "哲学について議論",
            "SFについて語り合う",
            "料理のレシピ開発",
            "技術の未来について",
            "創作アイデアを考える"
        ]
        selected_theme = st.selectbox("テーマを選択", theme_presets)
        
        # カスタムテーマ
        if st.checkbox("カスタムテーマ"):
            selected_theme = st.text_input("カスタムテーマを入力", value=selected_theme)
        
        st.divider()
        
        # 自動化設定セクション
        st.subheader("⚙️ 自動化設定")
        
        # メッセージ制限
        max_messages = st.slider(
            "最大メッセージ数", 
            min_value=10, 
            max_value=200, 
            value=st.session_state.max_messages,
            help="この数に達すると自動で会話を停止します"
        )
        st.session_state.max_messages = max_messages
        
        # 自動停止設定
        auto_stop_options = st.multiselect(
            "自動停止条件",
            ["トークン上限達成", "最大メッセージ数達成", "エラー発生時", "指定時間経過"],
            default=["トークン上限達成", "最大メッセージ数達成", "エラー発生時"]
        )
        
        # 時間制限設定
        if "指定時間経過" in auto_stop_options:
            time_limit = st.number_input(
                "制限時間（分）", 
                min_value=1, 
                max_value=120, 
                value=30
            )
        
        st.divider()
        
        # 開始/停止ボタン
        api_count = len(api_keys_set)
        button_col1, button_col2 = st.columns(2)
        
        with button_col1:
            if not st.session_state.conversation_active:
                if api_count >= 2:
                    if st.button("🚀 会話開始", type="primary", use_container_width=True):
                        start_conversation(token_limit, selected_theme)
                else:
                    st.button("🚀 会話開始", type="primary", use_container_width=True, disabled=True)
                    st.error("最低2つのAPIキーを設定してください")
            else:
                if st.button("🛑 会話停止", type="secondary", use_container_width=True):
                    stop_conversation()
        
        with button_col2:
            if st.session_state.conversation_active:
                if st.session_state.conversation_paused:
                    if st.button("▶️ 再開", use_container_width=True):
                        st.session_state.conversation_paused = False
                        st.rerun()
                else:
                    if st.button("⏸️ 一時停止", use_container_width=True):
                        st.session_state.conversation_paused = True
                        st.rerun()
        
        st.divider()
        
        # システム情報
        st.subheader("ℹ️ システム情報")
        if st.session_state.llm_manager:
            available_llms = st.session_state.llm_manager.available_llms
            for llm in available_llms:
                st.success(f"✅ {llm}")
        
        # 料金情報
        st.subheader("💰 料金目安")
        st.markdown("""
        **20,000トークンでの概算:**
        - ChatGPT: $0.1-0.3
        - Claude: $0.15-0.75
        - Gemini: 無料枠内
        """)
        
        # ヘルプリンク
        st.subheader("📚 ヘルプ")
        st.markdown("""
        - [OpenAI API](https://platform.openai.com/api-keys)
        - [Anthropic API](https://console.anthropic.com/)
        - [Google AI Studio](https://makersuite.google.com/app/apikey)
        """)
        
        st.divider()
        
        # テーマ設定
        st.subheader("🎨 表示設定")
        
        # テーマ選択
        theme_choice = st.selectbox(
            "テーマ選択",
            ["自動（システム設定）", "ライトテーマ", "ダークテーマ"],
            help="テキストが見えない場合は別のテーマを試してください"
        )
        
        # テーマ切り替えの説明
        if theme_choice == "ライトテーマ":
            st.success("☀️ ライトテーマが選択されています")
        elif theme_choice == "ダークテーマ":
            st.info("🌙 ダークテーマが選択されています")
        else:
            st.info("🔄 システムの設定に従います")
        
        # テーマ切り替えのJavaScriptコード
        if theme_choice != "自動（システム設定）":
            theme_script = f"""
            <script>
            function setTheme(theme) {{
                const app = document.querySelector('.stApp');
                if (app) {{
                    app.setAttribute('data-theme', theme);
                }}
            }}
            
            // テーマを適用
            setTimeout(() => {{
                setTheme('{theme_choice.replace("テーマ", "").replace("ライト", "light").replace("ダーク", "dark")}');
            }}, 100);
            </script>
            """
            st.markdown(theme_script, unsafe_allow_html=True)
        
        # 表示設定のヒント
        st.caption("""
        💡 **表示のヒント**
        - テキストが見えない場合はテーマを変更してください
        - ダークテーマではメッセージが美しいグラデーションで表示されます
        - ライトテーマでは読みやすい表示になります
        """)
        
        st.divider()
        
        # トラブルシューティング
        st.subheader("🔧 表示の問題")
        
        with st.expander("テキストが見えない場合"):
            st.markdown("""
            **解決方法:**
            1. 上記の「テーマ選択」で別のテーマを選択
            2. ブラウザを更新（F5キー）
            3. Streamlitの設定 → Settings → Theme で変更
            4. ブラウザのダークモード設定を確認
            """)
        
        with st.expander("色が正しく表示されない場合"):
            st.markdown("""
            **確認事項:**
            - ブラウザが最新版か確認
            - CSSが正しく読み込まれているか確認
            - 他のブラウザで試してみる
            """)
        
        with st.expander("アニメーションが重い場合"):
            st.markdown("""
            **対処法:**
            - ブラウザの設定でアニメーションを無効化
            - 「手動」モードで動作を軽くする
            - 不要なタブを閉じる
            """)

def start_conversation(token_limit: int, theme: str):
    """会話を開始"""
    # 変数を事前に初期化（スコープ対策）
    openai_key = None
    anthropic_key = None
    google_key = None
    
    try:
        # セッション状態からAPIキーを明示的に取得
        openai_key = getattr(st.session_state, 'openai_api_key', None)
        anthropic_key = getattr(st.session_state, 'anthropic_api_key', None)
        google_key = getattr(st.session_state, 'google_api_key', None)
        
        # APIキーがない場合のエラーチェック
        api_keys_available = 0
        if openai_key:
            api_keys_available += 1
        if anthropic_key:
            api_keys_available += 1
        if google_key:
            api_keys_available += 1
        
        if api_keys_available < 2:
            st.error("⚠️ 最低2つのAPIキーを設定してください")
            return
        
        # configにAPIキーを明示的に設定
        if openai_key:
            config.openai_api_key = openai_key
        if anthropic_key:
            config.anthropic_api_key = anthropic_key
        if google_key:
            config.google_api_key = google_key
        
        # 設定を確実に反映
        config.load_api_keys()
        
        # 設定初期化
        st.session_state.session_config = setup_config(token_limit, theme)
        st.session_state.cost_monitor = create_cost_monitor(token_limit)
        st.session_state.llm_manager = create_llm_manager()
        
        # LLM初期化
        available_models = st.session_state.llm_manager.initialize_all()
        if len(available_models) < 2:
            st.error("⚠️ 会話には最低2つのLLMが必要です")
            st.error("エラー詳細: APIキーが正しく設定されていない可能性があります")
            return
        
        # 初期メッセージ
        st.session_state.llm_manager.add_initial_message(theme)
        st.session_state.messages = []
        st.session_state.total_messages = 0
        st.session_state.conversation_active = True
        st.session_state.last_message_time = None  # 初期化
        
        st.success(f"🚀 会話を開始しました！テーマ: {theme}")
        st.success(f"利用可能なAI: {', '.join(available_models)}")

    except Exception as e:
        st.error(f"❌ 初期化エラー: {e}")
        import traceback
        st.error(f"詳細: {traceback.format_exc()}")
        
        # デバッグ情報表示
        st.error("🔍 デバッグ情報:")
        st.error(f"OpenAI キー設定: {'✅' if openai_key else '❌'}")
        st.error(f"Anthropic キー設定: {'✅' if anthropic_key else '❌'}")
        st.error(f"Google キー設定: {'✅' if google_key else '❌'}")
        st.error(f"Config OpenAI: {'✅' if config.openai_api_key else '❌'}")
        st.error(f"Config Anthropic: {'✅' if config.anthropic_api_key else '❌'}")
        st.error(f"Config Google: {'✅' if config.google_api_key else '❌'}")

def stop_conversation():
    """会話を停止"""
    st.session_state.conversation_active = False
    st.session_state.last_message_time = None
    st.success("🛑 会話を停止しました")

def should_stop_conversation() -> bool:
    """会話を自動停止すべきかどうかを判定"""
    if not st.session_state.conversation_active:
        return False
    
    # メッセージ数制限チェック
    if st.session_state.total_messages >= st.session_state.max_messages:
        st.error(f"🔴 最大メッセージ数({st.session_state.max_messages})に達しました。会話を終了します。")
        return True
    
    # トークン制限チェック
    if st.session_state.cost_monitor and st.session_state.cost_monitor.is_limit_exceeded():
        st.error("🔴 トークン上限に達しました。会話を終了します。")
        return True
    
    # 時間制限チェック（実装予定）
    # TODO: 時間制限の実装
    
    return False

def conversation_step():
    """会話の1ステップを実行（改良版）"""
    if not st.session_state.conversation_active or st.session_state.conversation_paused:
        return
    
    # 停止条件チェック
    if should_stop_conversation():
        stop_conversation()
        return
    
    try:
        # 次の発言者を選択
        current_speaker = st.session_state.llm_manager.select_next_speaker()
        
        # スピナーで思考中を表示
        with st.spinner(f"🎤 {current_speaker} が考え中..."):
            # 応答生成
            response = st.session_state.llm_manager.generate_response(
                current_speaker,
                st.session_state.session_config.initial_theme,
                st.session_state.session_config.max_response_length
            )
        
        # トークン数とコストを計算
        session_tokens, session_cost = st.session_state.cost_monitor.add_usage(
            current_speaker,
            st.session_state.session_config.initial_theme,
            response
        )
        
        # メッセージをセッション状態に保存
        st.session_state.messages.append({
            'speaker': current_speaker,
            'content': response,
            'tokens': session_tokens,
            'cost': session_cost,
            'timestamp': datetime.now()
        })
        st.session_state.total_messages += 1
        st.session_state.message_counter += 1
        st.session_state.last_message_time = time.time()  # 最後のメッセージ時刻を記録
        
        # 警告チェック
        if st.session_state.cost_monitor.is_warning_threshold():
            st.warning("⚠️ トークン使用量が90%を超えました！")
        
        # 成功メッセージ
        st.success(f"✅ {current_speaker}がメッセージを送信しました ({st.session_state.total_messages}/{st.session_state.max_messages})")
        
    except Exception as e:
        st.error(f"❌ 会話エラー: {e}")
        st.error("💡 エラーが発生しましたが、会話は継続されます。問題が続く場合は会話を停止してください。")
        # エラーが発生してもすぐには停止しない（ユーザーの選択に任せる）

def main():
    """メイン関数"""
    # セッション状態を初期化
    initialize_session_state()
    
    # サイドバーのセットアップ
    setup_sidebar()
    
    # メインタイトル
    st.title("🤖 AI同士の会話を観察")
    st.markdown("異なるAIが自動で会話を続けます。リアルタイムで観察してみましょう！")
    
    # ステータス表示（会話開始後）
    if st.session_state.conversation_active and st.session_state.cost_monitor:
        with st.expander("📊 詳細ステータス", expanded=True):
            # 基本ステータス
            display_status(st.session_state.cost_monitor)
            
            st.divider()
            
            # 自動化ステータス
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                mode_status = "🔴 停止中" if st.session_state.conversation_paused else "🟢 進行中"
                st.metric("会話状態", mode_status)
            
            with col2:
                st.metric("進行モード", st.session_state.auto_mode.split("（")[0])
            
            with col3:
                progress_percentage = (st.session_state.total_messages / st.session_state.max_messages) * 100
                st.metric("進行率", f"{progress_percentage:.1f}%")
            
            with col4:
                if st.session_state.messages:
                    start_time = st.session_state.messages[0]['timestamp']
                    duration = (datetime.now() - start_time).total_seconds() / 60
                    st.metric("経過時間", f"{duration:.1f}分")
                else:
                    st.metric("経過時間", "0分")
            
            # プログレスバー（メッセージ数）
            st.write("**メッセージ進行状況**")
            progress = min(st.session_state.total_messages / st.session_state.max_messages, 1.0)
            st.progress(progress)
            st.caption(f"{st.session_state.total_messages} / {st.session_state.max_messages} メッセージ")
            
            # 次回実行予定時刻（自動モードの場合）
            if (st.session_state.auto_mode != "手動" and 
                not st.session_state.conversation_paused and 
                st.session_state.last_message_time):
                
                auto_intervals = {
                    "半自動（3秒間隔）": 3,
                    "自動（1秒間隔）": 1,
                    "高速（0.5秒間隔）": 0.5,
                    "超高速（即座）": 0
                }
                interval = auto_intervals.get(st.session_state.auto_mode, 3)
                
                if interval > 0:
                    next_time = st.session_state.last_message_time + interval
                    remaining = max(0, next_time - time.time())
                    
                    if remaining > 0:
                        st.info(f"⏰ 次のメッセージまで: {remaining:.1f}秒")
                    else:
                        st.success("🚀 次のメッセージを準備中...")
                else:
                    st.success("⚡ 超高速モードで実行中...")
    
    # 自動進行制御
    if st.session_state.conversation_active:
        st.subheader("🎮 会話制御")
        
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            auto_mode = st.selectbox(
                "進行モード",
                ["手動", "半自動（3秒間隔）", "自動（1秒間隔）", "高速（0.5秒間隔）", "超高速（即座）"],
                index=["手動", "半自動（3秒間隔）", "自動（1秒間隔）", "高速（0.5秒間隔）", "超高速（即座）"].index(st.session_state.auto_mode),
                key="auto_mode_select"
            )
            st.session_state.auto_mode = auto_mode
        
        with col2:
            if st.button("🎯 次のメッセージ", use_container_width=True, disabled=st.session_state.conversation_paused):
                if not st.session_state.conversation_paused:
                    conversation_step()
                    st.rerun()
        
        with col3:
            if st.session_state.conversation_paused:
                if st.button("▶️ 再開", use_container_width=True):
                    st.session_state.conversation_paused = False
                    st.rerun()
            else:
                if st.button("⏸️ 一時停止", use_container_width=True):
                    st.session_state.conversation_paused = True
                    st.success("⏸️ 会話を一時停止しました")
        
        with col4:
            if st.button("🔄 リセット", use_container_width=True):
                if st.session_state.conversation_active:
                    stop_conversation()
                    st.session_state.messages = []
                    st.session_state.total_messages = 0
                    st.session_state.message_counter = 0
                    st.success("🔄 会話をリセットしました")
                    st.rerun()
        
        # 自動進行の実行ロジック
        if (auto_mode != "手動" and 
            not st.session_state.conversation_paused and 
            not should_stop_conversation()):
            
            auto_intervals = {
                "半自動（3秒間隔）": 3,
                "自動（1秒間隔）": 1,
                "高速（0.5秒間隔）": 0.5,
                "超高速（即座）": 0
            }
            interval = auto_intervals.get(auto_mode, 3)
            
            # 自動進行のロジック
            current_time = time.time()
            should_step = False
            
            if st.session_state.last_message_time is None:
                should_step = True
            elif current_time - st.session_state.last_message_time >= interval:
                should_step = True
            
            if should_step:
                # ステータス表示
                status_placeholder = st.empty()
                with status_placeholder:
                    st.info(f"🔄 {auto_mode}で自動進行中...")
                
                conversation_step()
                
                # 短い待機（UIの応答性向上）
                if interval > 0:
                    time.sleep(min(interval * 0.1, 0.2))
                
                st.rerun()
            else:
                # 次のステップまでの待機時間表示
                remaining = interval - (current_time - st.session_state.last_message_time)
                if remaining > 0 and interval > 0:
                    st.info(f"⏳ 次のメッセージまで {remaining:.1f}秒...")
                    time.sleep(1)
                    st.rerun()
        
        # 一時停止中の表示
        if st.session_state.conversation_paused:
            st.warning("⏸️ 会話が一時停止中です。「▶️ 再開」ボタンで続行できます。")
    
    # 自動停止チェック関数の呼び出し
    if st.session_state.conversation_active and should_stop_conversation():
        stop_conversation()
        st.rerun()
    
    # チャット表示エリア
    st.divider()
    chat_container = st.container()
    
    # メッセージ表示
    if st.session_state.messages:
        with chat_container:
            st.subheader("💬 AI同士の会話")
            
            # 最新のメッセージから表示（チャット風）
            for message in st.session_state.messages[-10:]:  # 最新10件のみ表示
                display_message(
                    message['speaker'],
                    message['content'],
                    message['tokens'],
                    message['cost']
                )
            
            # さらに多くのメッセージがある場合
            if len(st.session_state.messages) > 10:
                with st.expander(f"📝 過去のメッセージ ({len(st.session_state.messages) - 10}件)"):
                    for message in st.session_state.messages[:-10]:
                        display_message(
                            message['speaker'],
                            message['content'],
                            message['tokens'],
                            message['cost']
                        )
        
        st.divider()
        
        # 統計情報表示
        if st.session_state.messages:
            # 会話統計
            st.subheader("📈 会話統計")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("総メッセージ数", st.session_state.total_messages)
            
            with col2:
                speaker_counts = {}
                for msg in st.session_state.messages:
                    speaker = msg['speaker']
                    speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1
                most_active = max(speaker_counts.items(), key=lambda x: x[1]) if speaker_counts else ("なし", 0)
                st.metric("最も活発なAI", f"{most_active[0]} ({most_active[1]}回)")
            
            with col3:
                start_time = st.session_state.messages[0]['timestamp']
                duration = (datetime.now() - start_time).total_seconds() / 60
                st.metric("会話時間", f"{duration:.1f}分")
    
    else:
        # 初期画面
        with chat_container:
            st.info("👈 左側のサイドバーで設定を行い、「🚀 会話開始」をクリックしてください")
            
            # 使い方説明
            st.subheader("📖 使い方")
            st.markdown("""
            1. **APIキー設定**: サイドバーで各AIのAPIキーを設定
            2. **トークン制限**: 使用量の上限を設定（費用制御）
            3. **自動化設定**: 最大メッセージ数、自動停止条件を設定
            4. **テーマ選択**: AIたちが話し合うトピックを選択
            5. **会話開始**: 設定完了後、「🚀 会話開始」をクリック
            6. **進行モード選択**: 手動から超高速自動まで5つのモードから選択
            7. **制御**: 一時停止・再開・リセットで柔軟に制御
            8. **観察**: AI同士の自動会話をリアルタイムで観察
            """)
            
            st.subheader("🎮 進行モード説明")
            st.markdown("""
            - **手動**: ボタンクリックで1つずつメッセージを進める
            - **半自動（3秒間隔）**: 3秒ごとに自動でメッセージを生成
            - **自動（1秒間隔）**: 1秒ごとに自動でメッセージを生成
            - **高速（0.5秒間隔）**: 0.5秒ごとに高速でメッセージを生成
            - **超高速（即座）**: 待機時間なしで連続してメッセージを生成
            """)
            
            # 注意事項
            st.warning("""
            ⚠️ **注意事項**
            - API使用料金が発生します
            - 最低2つのAPIキーが必要です
            - トークン制限を設定して費用をコントロールしてください
            - 高速・超高速モードは料金が急激に増加する可能性があります
            """)
            
            # 新機能の説明
            st.success("""
            ✨ **新機能**
            - **5つの進行モード**: 手動から超高速自動まで選択可能
            - **一時停止・再開**: いつでも会話を停止・再開可能
            - **リアルタイム制御**: 進行状況を見ながら設定を変更
            - **自動停止機能**: 制限達成時に自動で停止
            - **詳細ステータス**: 使用状況を詳細にモニタリング
            - **エラー耐性**: エラーが発生しても会話を継続
            """)
            
            st.subheader("💡 使用のコツ")
            st.markdown("""
            - **初回**: 「半自動（3秒間隔）」モードで様子を見る
            - **費用節約**: 手動モードで必要な時だけ実行
            - **観察重視**: 自動モードで流れを観察
            - **高速テスト**: 高速モードで短時間で多くの会話を生成
            - **安全第一**: 必ずトークン制限を設定して使用
            """)
            
            st.subheader("🔧 トラブルシューティング")
            st.markdown("""
            - **エラーが頻発**: APIキーが正しく設定されているか確認
            - **会話が止まる**: 一時停止状態になっていないか確認
            - **料金が心配**: 手動モードに切り替えて様子を見る
            - **応答が遅い**: APIの応答速度の問題の可能性
            """)
            
            # 推奨設定
            st.info("""
            🎯 **推奨初期設定**
            - トークン制限: 20,000 tokens
            - 最大メッセージ数: 30-50件
            - 進行モード: 半自動（3秒間隔）
            - 自動停止: トークン上限達成、最大メッセージ数達成、エラー発生時
            """)

if __name__ == "__main__":
    main()
