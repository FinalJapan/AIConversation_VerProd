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
    animation: slideIn 0.4s ease-out;
    transition: all 0.2s ease;
}

/* ChatGPTスタイル（OpenAI - 控えめな緑系） */
.chatgpt-message {
    background: linear-gradient(135deg, #e8f5e8 0%, #f0f9f0 100%);
    border-left: 4px solid #10A37F;
    color: #2d4a3d !important;
    box-shadow: 0 2px 8px rgba(16, 163, 127, 0.1);
    border: 1px solid rgba(16, 163, 127, 0.2);
}

.chatgpt-message * {
    color: #2d4a3d !important;
}

/* Claudeスタイル（Anthropic - 控えめなオレンジ系） */
.claude-message {
    background: linear-gradient(135deg, #fef4e8 0%, #fff8f0 100%);
    border-left: 4px solid #F56500;
    color: #5a3e2a !important;
    box-shadow: 0 2px 8px rgba(245, 101, 0, 0.1);
    border: 1px solid rgba(245, 101, 0, 0.2);
}

.claude-message * {
    color: #5a3e2a !important;
}

/* Geminiスタイル（Google - 控えめな青紫系） */
.gemini-message {
    background: linear-gradient(135deg, #f0f4ff 0%, #f8faff 100%);
    border-left: 4px solid #4285F4;
    color: #2d3a4f !important;
    box-shadow: 0 2px 8px rgba(66, 133, 244, 0.1);
    border: 1px solid rgba(66, 133, 244, 0.2);
}

.gemini-message * {
    color: #2d3a4f !important;
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
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.chat-message {
    animation: slideIn 0.4s ease-out;
    transition: all 0.2s ease;
}

/* ホバー効果（控えめ） */
.chat-message:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.chatgpt-message:hover {
    box-shadow: 0 4px 12px rgba(16, 163, 127, 0.15);
}

.claude-message:hover {
    box-shadow: 0 4px 12px rgba(245, 101, 0, 0.15);
}

.gemini-message:hover {
    box-shadow: 0 4px 12px rgba(66, 133, 244, 0.15);
}

/* パルスアニメーション（思考中表示用） */
@keyframes pulse {
    0% { 
        opacity: 1;
        transform: scale(1);
    }
    50% { 
        opacity: 0.7;
        transform: scale(1.05);
    }
    100% { 
        opacity: 1;
        transform: scale(1);
    }
}

/* 思考中メッセージの点滅効果 */
@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0.3; }
}

.thinking-message {
    animation: blink 2s ease-in-out infinite;
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
        box-shadow: 0 2px 10px rgba(255,255,255,0.05);
    }
    
    .stButton > button {
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    /* ダークテーマでのChatGPTメッセージ */
    .chatgpt-message {
        background: linear-gradient(135deg, #1a2f1a 0%, #2a3f2a 100%);
        border-left: 4px solid #10A37F;
        color: #b8e6c1 !important;
        border: 1px solid rgba(16, 163, 127, 0.3);
    }
    
    .chatgpt-message * {
        color: #b8e6c1 !important;
    }
    
    /* ダークテーマでのClaudeメッセージ */
    .claude-message {
        background: linear-gradient(135deg, #2f1f0f 0%, #3f2f1f 100%);
        border-left: 4px solid #F56500;
        color: #f5c99b !important;
        border: 1px solid rgba(245, 101, 0, 0.3);
    }
    
    .claude-message * {
        color: #f5c99b !important;
    }
    
    /* ダークテーマでのGeminiメッセージ */
    .gemini-message {
        background: linear-gradient(135deg, #1a1f2f 0%, #2a2f3f 100%);
        border-left: 4px solid #4285F4;
        color: #b8c5f5 !important;
        border: 1px solid rgba(66, 133, 244, 0.3);
    }
    
    .gemini-message * {
        color: #b8c5f5 !important;
    }
}

/* Streamlitのダークテーマクラス対応 */
.stApp[data-theme="dark"] .chatgpt-message {
    background: linear-gradient(135deg, #1a2f1a 0%, #2a3f2a 100%) !important;
    color: #b8e6c1 !important;
    border: 1px solid rgba(16, 163, 127, 0.3);
}

.stApp[data-theme="dark"] .chatgpt-message * {
    color: #b8e6c1 !important;
}

.stApp[data-theme="dark"] .claude-message {
    background: linear-gradient(135deg, #2f1f0f 0%, #3f2f1f 100%) !important;
    color: #f5c99b !important;
    border: 1px solid rgba(245, 101, 0, 0.3);
}

.stApp[data-theme="dark"] .claude-message * {
    color: #f5c99b !important;
}

.stApp[data-theme="dark"] .gemini-message {
    background: linear-gradient(135deg, #1a1f2f 0%, #2a2f3f 100%) !important;
    color: #b8c5f5 !important;
    border: 1px solid rgba(66, 133, 244, 0.3);
}

.stApp[data-theme="dark"] .gemini-message * {
    color: #b8c5f5 !important;
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
    """メッセージを表示（シンプル版）"""
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
    if 'last_message_time' not in st.session_state:
        st.session_state.last_message_time = None
    if 'conversation_paused' not in st.session_state:
        st.session_state.conversation_paused = False
    if 'is_thinking' not in st.session_state:
        st.session_state.is_thinking = False
    if 'thinking_speaker' not in st.session_state:
        st.session_state.thinking_speaker = None

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
        selected_option = st.selectbox("制限を選択", list(token_options.keys()), key="token_limit_select")
        token_limit = token_options[selected_option]
        
        # カスタム設定
        if st.checkbox("カスタム設定", key="custom_token_setting"):
            token_limit = st.number_input("カスタムトークン数", min_value=1000, max_value=200000, value=20000, key="custom_token_input")
        
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
        selected_theme = st.selectbox("テーマを選択", theme_presets, key="theme_presets_select")
        
        # カスタムテーマ
        if st.checkbox("カスタムテーマ", key="custom_theme_checkbox"):
            selected_theme = st.text_input("カスタムテーマを入力", value=selected_theme, key="custom_theme_input")
        
        st.divider()
        
        # 開始/停止ボタン
        api_count = len(api_keys_set)
        
        if not st.session_state.conversation_active:
            if api_count >= 2:
                if st.button("🚀 会話開始", type="primary", use_container_width=True, key="sidebar_start"):
                    start_conversation(token_limit, selected_theme)
            else:
                st.button("🚀 会話開始", type="primary", use_container_width=True, disabled=True, key="sidebar_start_disabled")
                st.error("最低2つのAPIキーを設定してください")
        else:
            # 会話中の制御ボタン
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🛑 会話停止", type="secondary", use_container_width=True, key="sidebar_stop"):
                    stop_conversation()
            
            with col2:
                if st.session_state.conversation_paused:
                    if st.button("▶️ 再開", use_container_width=True, key="sidebar_resume"):
                        st.session_state.conversation_paused = False
                        st.rerun()
                else:
                    if st.button("⏸️ 一時停止", use_container_width=True, key="sidebar_pause"):
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
        
        st.divider()
        
        # テーマ設定
        st.subheader("🎨 表示設定")
        
        # テーマ選択
        theme_choice = st.selectbox(
            "テーマ選択",
            ["自動（システム設定）", "ライトテーマ", "ダークテーマ"],
            help="テキストが見えない場合は別のテーマを試してください",
            key="display_theme_select"
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
    
    # トークン制限チェック
    if st.session_state.cost_monitor and st.session_state.cost_monitor.is_limit_exceeded():
        st.error("🔴 トークン上限に達しました。会話を終了します。")
        return True
    
    return False

def conversation_step():
    """会話の1ステップを実行（リアルタイム版）"""
    if not st.session_state.conversation_active or st.session_state.conversation_paused:
        return
    
    # 停止条件チェック
    if should_stop_conversation():
        stop_conversation()
        return
    
    try:
        # 次の発言者を選択
        current_speaker = st.session_state.llm_manager.select_next_speaker()
        
        # 思考中状態をセッション状態に保存
        st.session_state.thinking_speaker = current_speaker
        st.session_state.is_thinking = True
        
        # 応答生成
        response = st.session_state.llm_manager.generate_response(
            current_speaker,
            st.session_state.session_config.initial_theme,
            st.session_state.session_config.max_response_length
        )
        
        # 思考中状態をクリア
        st.session_state.is_thinking = False
        st.session_state.thinking_speaker = None
        
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
        st.session_state.last_message_time = time.time()  # 最後のメッセージ時刻を記録
        
        # 警告チェック
        if st.session_state.cost_monitor.is_warning_threshold():
            st.warning("⚠️ トークン使用量が90%を超えました！")
        
    except Exception as e:
        # エラー時も思考中状態をクリア
        st.session_state.is_thinking = False
        st.session_state.thinking_speaker = None
        st.error(f"❌ 会話エラー: {e}")
        # エラーが発生してもすぐには停止しない

def main():
    """メイン関数"""
    # セッション状態を初期化
    initialize_session_state()
    
    # サイドバーのセットアップ
    setup_sidebar()
    
    # メインタイトル
    st.title("🤖 AI同士の会話を観察")
    st.markdown("異なるAIが自動で会話を続けます。リアルタイムで観察してみましょう！")
    
    # 一時停止中の表示
    if st.session_state.conversation_paused:
        st.warning("⏸️ 会話が一時停止中です。サイドバーの「▶️ 再開」ボタンで続行できます。")
    
    # チャット表示エリア（常に表示）
    st.divider()
    
    # メッセージ表示（リアルタイム対応）
    if st.session_state.messages:
        st.subheader("💬 AI同士の会話")
        
        # メッセージ表示用のコンテナ
        message_container = st.container()
        
        with message_container:
            # 全メッセージを表示
            for message in st.session_state.messages:
                display_message(
                    message['speaker'],
                    message['content'],
                    message['tokens'],
                    message['cost']
                )
        
        # 思考中の表示
        if st.session_state.is_thinking and st.session_state.thinking_speaker:
            with st.container():
                speaker_style, icon = get_speaker_style(st.session_state.thinking_speaker)
                thinking_html = f"""
                <div class="chat-message {speaker_style}" style="opacity: 0.7; border-style: dashed;">
                    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                        <span class="speaker-icon">{icon}</span>
                        <strong style="font-size: 1.1em;">{st.session_state.thinking_speaker}</strong>
                        <span style="margin-left: 1rem; font-style: italic;">考え中...</span>
                    </div>
                    <div style="display: flex; align-items: center;">
                        <div style="animation: pulse 1.5s ease-in-out infinite;">💭</div>
                        <span style="margin-left: 0.5rem; opacity: 0.8;">応答を生成中です...</span>
                    </div>
                </div>
                """
                st.markdown(thinking_html, unsafe_allow_html=True)
        
        # 会話中の状態表示
        if st.session_state.conversation_active and not st.session_state.conversation_paused:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    if st.session_state.is_thinking:
                        st.success(f"🎤 {st.session_state.thinking_speaker} が考え中...")
                    else:
                        st.info("🔄 AIたちが会話中...")
                with col2:
                    st.metric("メッセージ数", st.session_state.total_messages)
                with col3:
                    if st.session_state.cost_monitor:
                        total_cost = sum(msg['cost'] for msg in st.session_state.messages)
                        st.metric("総コスト", f"${total_cost:.4f}")
        
        # 自動スクロール用のJavaScript
        scroll_script = """
        <script>
        function scrollToBottom() {
            window.scrollTo(0, document.body.scrollHeight);
        }
        setTimeout(scrollToBottom, 100);
        </script>
        """
        st.markdown(scroll_script, unsafe_allow_html=True)
    
    else:
        # 初期画面
        st.info("👈 左側のサイドバーで設定を行い、「🚀 会話開始」をクリックしてください")
        
        # 使い方説明（簡略版）
        st.subheader("📖 使い方")
        st.markdown("""
        1. **APIキー設定**: サイドバーで各AIのAPIキーを設定
        2. **トークン制限**: 使用量の上限を設定（費用制御）
        3. **テーマ選択**: AIたちが話し合うトピックを選択
        4. **会話開始**: 設定完了後、「🚀 会話開始」をクリック
        5. **観察**: AI同士の3秒間隔での自動会話を観察
        6. **制御**: 必要に応じて一時停止・再開・停止
        """)
        
        # 注意事項
        st.warning("""
        ⚠️ **注意事項**
        - API使用料金が発生します
        - 最低2つのAPIキーが必要です
        - トークン制限を設定して費用をコントロールしてください
        """)
    
    # 自動停止チェック
    if st.session_state.conversation_active and should_stop_conversation():
        stop_conversation()
        st.rerun()
    
    # 3秒間隔の自動進行（会話中のみ）- 最後に配置
    if (st.session_state.conversation_active and 
        not st.session_state.conversation_paused):
        
        current_time = time.time()
        should_step = False
        
        if st.session_state.last_message_time is None:
            should_step = True
        elif current_time - st.session_state.last_message_time >= 3:  # 3秒間隔固定
            should_step = True
        
        if should_step and not should_stop_conversation():
            # 新しいメッセージ生成
            conversation_step()
            # 即座に画面を更新
            st.rerun()
        else:
            # 待機中も短い間隔で画面を更新（0.5秒ごと）
            remaining = 3 - (current_time - st.session_state.last_message_time)
            if remaining > 0:
                # 下部に次のメッセージまでの時間を表示
                with st.container():
                    progress_percentage = (3 - remaining) / 3 * 100
                    st.progress(progress_percentage / 100)
                    st.caption(f"⏳ 次のメッセージまで {remaining:.1f}秒...")
                
                # 0.5秒後に画面を更新（よりスムーズな表示）
                time.sleep(0.5)
                st.rerun()

if __name__ == "__main__":
    main()
