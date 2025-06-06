#!/usr/bin/env python3
"""
LLMマルチ会話システム - メイン実行ファイル
AI同士の自動会話を観察するためのツール
"""

import signal
import sys
import time
from typing import Optional

from config import setup_config, config
from cost_monitor import create_cost_monitor
from logger import create_logger
from llm_manager import create_llm_manager

class ConversationSession:
    """会話セッション管理クラス"""
    
    def __init__(self, token_limit: int = 50000, theme: str = "一般的な話題について自由に議論"):
        self.token_limit = token_limit
        self.theme = theme
        self.is_running = False
        self.session_interrupted = False
        
        # コンポーネント初期化
        self.config = setup_config(token_limit, theme)
        self.cost_monitor = create_cost_monitor(token_limit)
        self.logger = create_logger()
        self.llm_manager = create_llm_manager()
        
        # シグナルハンドラー設定（Ctrl+C対応）
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """緊急停止シグナルハンドラー"""
        print("\n\n🛑 緊急停止が要求されました...")
        self.session_interrupted = True
        self.is_running = False
    
    def initialize(self) -> bool:
        """システム初期化"""
        try:
            print("=" * 80)
            print("🤖 LLMマルチ会話システム 初期化中...")
            print("=" * 80)
            
            # APIキー検証
            missing_keys = self.config.validate_api_keys()
            if missing_keys:
                print(f"❌ 以下のAPIキーが設定されていません: {', '.join(missing_keys)}")
                print("env_example.txtを参考に.envファイルを作成してください。")
                return False
            
            # LLM初期化
            available_models = self.llm_manager.initialize_all()
            if len(available_models) < 2:
                print("⚠️ 会話には最低2つのLLMが必要です")
                return False
            
            # セッション設定表示
            self._display_session_config()
            
            return True
            
        except Exception as e:
            print(f"❌ 初期化エラー: {e}")
            return False
    
    def _display_session_config(self):
        """セッション設定を表示"""
        print(f"""
🎯 セッション設定:
  📝 テーマ: {self.theme}
  📊 トークン上限: {self.token_limit:,}
  🤖 利用可能なLLM: {', '.join(self.llm_manager.available_llms)}
  ⏰ 応答待機時間: {self.config.response_wait_time}秒

💡 観察モード: AI同士が自動で会話します
🛑 緊急停止: Ctrl+C
""")
    
    def start_conversation(self):
        """会話開始"""
        if not self.initialize():
            return False
        
        try:
            print("🚀 会話を開始します...")
            print("=" * 80)
            
            # 初期設定をログに記録
            self.logger.add_system_message(f"会話テーマ: {self.theme}")
            self.logger.add_system_message(f"トークン上限: {self.token_limit:,}")
            self.logger.add_system_message(f"参加LLM: {', '.join(self.llm_manager.available_llms)}")
            
            # 初期メッセージを会話履歴に追加
            self.llm_manager.add_initial_message(self.theme)
            
            self.is_running = True
            message_count = 0
            
            while self.is_running and not self.session_interrupted:
                try:
                    # 次の発言者を選択
                    current_speaker = self.llm_manager.select_next_speaker()
                    
                    print(f"\n🎤 {current_speaker} が発言中...")
                    
                    # 応答生成
                    response = self.llm_manager.generate_response(
                        current_speaker, 
                        self.theme, 
                        self.config.max_response_length
                    )
                    
                    # トークン数とコストを計算
                    session_tokens, session_cost = self.cost_monitor.add_usage(
                        current_speaker, 
                        self.theme,  # 入力プロンプト相当
                        response     # 出力
                    )
                    
                    # ログに記録
                    self.logger.add_message(current_speaker, response, session_tokens, session_cost)
                    
                    # コンソールに表示
                    self._display_message(current_speaker, response, session_tokens, session_cost)
                    
                    message_count += 1
                    
                    # 制限チェック
                    if self.cost_monitor.is_limit_exceeded():
                        print("\n🔴 トークン上限に達しました。会話を終了します。")
                        break
                    
                    # 警告チェック
                    if self.cost_monitor.is_warning_threshold() and message_count % 5 == 0:
                        print(f"\n⚠️ トークン使用量が90%を超えました！")
                        print(self.cost_monitor.format_status_display())
                    
                    # レート制限対応の待機
                    self.llm_manager.wait_for_rate_limit(self.config.response_wait_time)
                    
                except KeyboardInterrupt:
                    print("\n🛑 Ctrl+Cが押されました。会話を終了します。")
                    break
                    
                except Exception as e:
                    print(f"\n❌ エラーが発生しました: {e}")
                    print("会話を継続します...")
                    time.sleep(2)
                    continue
            
            # セッション終了処理
            self._finalize_session()
            return True
            
        except Exception as e:
            print(f"❌ 会話セッションでエラーが発生しました: {e}")
            return False
    
    def _display_message(self, speaker: str, content: str, tokens: int, cost: float):
        """メッセージをコンソールに表示"""
        # モデル別の色分け（文字記号使用）
        speaker_icons = {
            "ChatGPT": "🤖",
            "Claude": "🧠",
            "Gemini": "⭐"
        }
        
        icon = speaker_icons.get(speaker, "❓")
        
        print(f"""
{icon} {speaker}:
{'-' * 60}
{content}

📊 この発言: {tokens} tokens, ${cost:.4f}
{self.cost_monitor.format_status_display().strip()}
""")
    
    def _finalize_session(self):
        """セッション終了処理"""
        print("\n" + "=" * 80)
        print("📊 会話セッション終了")
        print("=" * 80)
        
        # 最終統計
        final_stats = self.cost_monitor.get_status_summary()
        conversation_stats = self.logger.get_conversation_summary()
        
        # 統計表示
        print(f"""
📈 セッション統計:
  💬 総メッセージ数: {conversation_stats.get('message_count', 0)}
  📊 総トークン数: {final_stats['total_tokens']:,} / {self.token_limit:,}
  💰 総コスト: ${final_stats['total_cost_usd']:.4f}
  ⏰ セッション時間: {conversation_stats.get('duration_minutes', 0):.1f}分
  
📊 モデル別統計:""")
        
        for model, stats in final_stats['usage_by_model'].items():
            if stats['total_tokens'] > 0:
                print(f"  {model}: {stats['total_tokens']:,} tokens (${stats['cost_usd']:.4f})")
        
        # ログファイル保存
        self.logger.finalize_session(conversation_stats)
        
        print("\n✨ 観察をお楽しみいただき、ありがとうございました！")

def interactive_setup() -> tuple[int, str]:
    """対話的セットアップ"""
    print("🔧 LLMマルチ会話システム セットアップ")
    print("=" * 50)
    
    # トークン上限設定
    while True:
        try:
            print("\n📊 トークン上限を選択してください:")
            print("1. 20,000 tokens (推奨)")
            print("2. 50,000 tokens")
            print("3. カスタム")
            
            choice = input("選択 (1-3): ").strip()
            
            if choice == "1":
                token_limit = 20000
                break
            elif choice == "2":
                token_limit = 50000
                break
            elif choice == "3":
                token_limit = int(input("トークン数を入力: "))
                if token_limit <= 0:
                    print("正の数を入力してください")
                    continue
                break
            else:
                print("1-3の数字を入力してください")
                
        except ValueError:
            print("有効な数字を入力してください")
    
    # テーマ設定
    print("\n🎯 会話テーマを設定してください:")
    print("例: 哲学について議論, SFについて語り合う, 料理のレシピ開発")
    
    theme = input("テーマ (空白でデフォルト): ").strip()
    if not theme:
        theme = "一般的な話題について自由に議論"
    
    return token_limit, theme

def main():
    """メイン関数"""
    try:
        print("🤖 LLMマルチ会話システム")
        print("AI同士の自動会話を観察するツール")
        print("=" * 60)
        
        # 対話的セットアップ
        token_limit, theme = interactive_setup()
        
        # セッション開始
        session = ConversationSession(token_limit, theme)
        success = session.start_conversation()
        
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n👋 セットアップがキャンセルされました")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 