import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# 環境変数を読み込み（存在する場合のみ）
try:
    load_dotenv()
except:
    pass  # .envファイルがない場合は無視

@dataclass
class CostConfig:
    """API使用料金設定"""
    # 料金単価 (USD per 1M tokens)
    CHATGPT_INPUT_COST = 2.50 / 1_000_000  # $2.50/1M tokens
    CHATGPT_OUTPUT_COST = 10.00 / 1_000_000  # $10.00/1M tokens
    
    CLAUDE_INPUT_COST = 3.00 / 1_000_000   # $3.00/1M tokens  
    CLAUDE_OUTPUT_COST = 15.00 / 1_000_000  # $15.00/1M tokens
    
    # Gemini 2.0 Flash は無料枠内のため監視対象外
    GEMINI_INPUT_COST = 0.0
    GEMINI_OUTPUT_COST = 0.0

@dataclass  
class SystemConfig:
    """システム設定"""
    # APIキー
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None  
    google_api_key: Optional[str] = None
    
    # トークン制限設定
    token_limit: int = 50000  # デフォルト50,000トークン
    warning_threshold: float = 0.9  # 90%で警告
    
    # 会話設定
    initial_theme: str = "一般的な話題について自由に議論"
    max_response_length: int = 1000  # 最大応答文字数
    response_wait_time: int = 2  # API応答待機時間（秒）
    
    # ログ設定
    log_dir: str = "logs"
    save_logs: bool = True
    
    def __post_init__(self):
        """初期化後の処理"""
        self.load_api_keys()
        
        # デフォルト値の上書き
        if os.getenv('DEFAULT_TOKEN_LIMIT'):
            self.token_limit = int(os.getenv('DEFAULT_TOKEN_LIMIT'))
        if os.getenv('DEFAULT_THEME'):
            self.initial_theme = os.getenv('DEFAULT_THEME')
    
    def load_api_keys(self):
        """APIキーを環境変数またはStreamlitセッションから読み込み"""
        # まず環境変数から読み込み
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        
        # Streamlitセッション状態から読み込み（存在する場合）
        try:
            import streamlit as st
            if hasattr(st, 'session_state'):
                if hasattr(st.session_state, 'openai_api_key') and st.session_state.openai_api_key:
                    self.openai_api_key = st.session_state.openai_api_key
                if hasattr(st.session_state, 'anthropic_api_key') and st.session_state.anthropic_api_key:
                    self.anthropic_api_key = st.session_state.anthropic_api_key
                if hasattr(st.session_state, 'google_api_key') and st.session_state.google_api_key:
                    self.google_api_key = st.session_state.google_api_key
        except ImportError:
            # Streamlitがインストールされていない場合は無視
            pass
    
    def validate_api_keys(self) -> list[str]:
        """APIキーの検証"""
        # 最新のAPIキーを再読み込み
        self.load_api_keys()
        
        missing_keys = []
        
        if not self.openai_api_key:
            missing_keys.append("OPENAI_API_KEY")
        if not self.anthropic_api_key:
            missing_keys.append("ANTHROPIC_API_KEY")
        if not self.google_api_key:
            missing_keys.append("GOOGLE_API_KEY")
            
        return missing_keys
    
    def get_available_models(self) -> list[str]:
        """利用可能なモデルのリストを取得"""
        # 最新のAPIキーを再読み込み
        self.load_api_keys()
        
        models = []
        if self.openai_api_key:
            models.append("ChatGPT")
        if self.anthropic_api_key:
            models.append("Claude")
        if self.google_api_key:
            models.append("Gemini")
        return models

# グローバル設定インスタンス
config = SystemConfig()
cost_config = CostConfig()

def setup_config(token_limit: Optional[int] = None, theme: Optional[str] = None):
    """設定のセットアップ"""
    global config
    
    if token_limit:
        config.token_limit = token_limit
    if theme:
        config.initial_theme = theme
    
    # ログディレクトリの作成
    if config.save_logs and not os.path.exists(config.log_dir):
        os.makedirs(config.log_dir)
    
    return config 