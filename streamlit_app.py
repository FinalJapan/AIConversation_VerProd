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

# カスタムCSS（ChatGPTライクなスタイル）
st.markdown("""
<style>
/* 背景色を白に */
.main {
    background-color: white;
}

/* チャットメッセージのスタイル */
.chat-message {
    padding: 1rem;
    border-radius: 10px;
    margin: 0.5rem 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    color: #000000 !important;  /* 黒文字を強制 */
}

/* ChatGPTスタイル（青系） */
.chatgpt-message {
    background-color: #f7f9fc;
    border-left: 4px solid #4285f4;
    color: #1a1a1a !important;  /* 濃い黒文字 */
}

/* Claudeスタイル（オレンジ系） */
.claude-message {
    background-color: #fff8f0;
    border-left: 4px solid #ff8c00;
    color: #1a1a1a !important;  /* 濃い黒文字 */
}

/* Geminiスタイル（緑系） */
.gemini-message {
    background-color: #f0fff4;
    border-left: 4px solid #00c851;
    color: #1a1a1a !important;  /* 濃い黒文字 */
}

/* システムメッセージ */
.system-message {
    background-color: #f8f9fa;
    border-left: 4px solid #6c757d;
    color: #1a1a1a !important;  /* 濃い黒文字 */
    font-style: italic;
}

/* メッセージ内のテキスト */
.chat-message div {
    color: #1a1a1a !important;  /* 濃い黒文字 */
}

/* アイコン */
.speaker-icon {
    font-size: 1.2em;
    margin-right: 0.5rem;
}

/* ステータスバー */
.status-bar {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 5px;
    border: 1px solid #dee2e6;
}

/* プログレスバー */
.progress-bar {
    margin: 1rem 0;
}

/* Streamlit要素の文字色を確実に黒にする */
.stMarkdown, .stText {
    color: #1a1a1a !important;
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
    """メッセージを表示"""
    style_class, icon = get_speaker_style(speaker)
    
    # Streamlitの標準コンポーネントで確実に表示
    with st.container():
        # ヘッダー部分
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### {icon} **{speaker}**")
        with col2:
            st.caption(f"{tokens} tokens | ${cost:.4f}")
        
        # メッセージ内容（背景色付き）
        if speaker == "ChatGPT":
            st.info(content)
        elif speaker == "Claude":
            st.warning(content)
        elif speaker == "Gemini":
            st.success(content)
        else:
            st.write(content)
        
        st.divider()

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
        
        # 開始/停止ボタン
        api_count = len(api_keys_set)
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

def conversation_step(chat_placeholder):
    """会話の1ステップを実行"""
    if not st.session_state.conversation_active:
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
        st.session_state.last_message_time = time.time()  # 最後のメッセージ時刻を記録
        
        # チャットエリア全体を更新（全メッセージを再表示）
        with chat_placeholder.container():
            for message in st.session_state.messages:
                display_message(
                    message['speaker'],
                    message['content'],
                    message['tokens'],
                    message['cost']
                )
        
        # 制限チェック
        if st.session_state.cost_monitor.is_limit_exceeded():
            st.session_state.conversation_active = False
            return
        
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {e}")
        return

def main():
    """メイン関数"""
    st.title("🤖 AI同士の会話を観察")
    st.markdown("**ChatGPT**、**Claude**、**Gemini**が自動で会話する様子を観察できます")
    
    # セッション状態初期化
    initialize_session_state()
    
    # サイドバー設定
    setup_sidebar()
    
    # メインコンテンツ
    if st.session_state.conversation_active:
        # ステータス表示
        if st.session_state.cost_monitor:
            st.subheader("📊 ステータス")
            display_status(st.session_state.cost_monitor)
        
        # リアルタイムチャット表示エリア
        st.subheader("💬 リアルタイム会話")
        st.info("💡 AI同士が自動で会話しています。傍観してお楽しみください。")
        
        # チャットメッセージエリア
        chat_placeholder = st.empty()
        
        # 既存のメッセージを表示
        if st.session_state.messages:
            with chat_placeholder.container():
                for message in st.session_state.messages:
                    display_message(
                        message['speaker'],
                        message['content'],
                        message['tokens'],
                        message['cost']
                    )
        else:
            with chat_placeholder.container():
                st.write("AI同士の会話が始まります...")
        
        # 自動会話進行 - 制限チェック後に次のステップを実行
        if (st.session_state.conversation_active and 
            not st.session_state.cost_monitor.is_limit_exceeded()):
            
            # タイムスタンプベースで自動進行（2秒間隔）
            current_time = time.time()
            should_step = False
            
            # デバッグ情報表示
            st.write(f"🔍 デバッグ: 現在時刻={current_time:.1f}, 最後のメッセージ時刻={st.session_state.last_message_time}")
            
            if st.session_state.last_message_time is None:
                # 初回メッセージ
                should_step = True
                st.write("🔍 デバッグ: 初回メッセージを生成します")
            elif current_time - st.session_state.last_message_time >= 2:
                # 前回のメッセージから2秒経過
                should_step = True
                st.write(f"🔍 デバッグ: 2秒経過({current_time - st.session_state.last_message_time:.1f}秒)、次のメッセージを生成します")
            else:
                remaining = 2 - (current_time - st.session_state.last_message_time)
                st.write(f"🔍 デバッグ: 待機中...あと{remaining:.1f}秒で次のメッセージ")
                time.sleep(remaining)
                st.rerun()
            
            if should_step:
                st.write("🔍 デバッグ: conversation_step()を実行します")
                conversation_step(chat_placeholder)
                st.rerun()  # ページを更新して次のステップへ
        else:
            if not st.session_state.conversation_active:
                st.write("🔍 デバッグ: 会話が停止中")
            if st.session_state.cost_monitor.is_limit_exceeded():
                st.write("🔍 デバッグ: トークン制限に達しました")
        
        # 制限・警告チェック
        if st.session_state.cost_monitor.is_limit_exceeded():
            st.error("🔴 トークン上限に達しました。会話を終了します。")
            st.session_state.conversation_active = False
        elif st.session_state.cost_monitor.is_warning_threshold():
            st.warning("⚠️ トークン使用量が90%を超えました！")
        
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
        st.info("👈 左側のサイドバーで設定を行い、「🚀 会話開始」をクリックしてください")
        
        # 使い方説明
        st.subheader("📖 使い方")
        st.markdown("""
        1. **APIキー設定**: サイドバーで各AIのAPIキーを設定
        2. **トークン制限**: 使用量の上限を設定（費用制御）
        3. **テーマ選択**: AIたちが話し合うトピックを選択
        4. **会話開始**: 設定完了後、「🚀 会話開始」をクリック
        5. **観察**: AI同士の自動会話をリアルタイムで観察
        """)
        
        # 注意事項
        st.warning("""
        ⚠️ **注意事項**
        - API使用料金が発生します
        - 最低2つのAPIキーが必要です
        - トークン制限を設定して費用をコントロールしてください
        """)

if __name__ == "__main__":
    main()
