import tiktoken
from typing import Dict, Tuple
from dataclasses import dataclass, field
from config import cost_config

@dataclass
class TokenUsage:
    """トークン使用量の記録"""
    input_tokens: int = 0
    output_tokens: int = 0
    
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

@dataclass  
class CostMonitor:
    """コスト監視クラス"""
    # 各モデルのトークン使用量
    usage: Dict[str, TokenUsage] = field(default_factory=dict)
    # 累計統計
    total_tokens: int = 0
    total_cost: float = 0.0
    token_limit: int = 50000
    
    def __post_init__(self):
        """初期化"""
        self.usage = {
            "ChatGPT": TokenUsage(),
            "Claude": TokenUsage(), 
            "Gemini": TokenUsage()
        }
        self.encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4用エンコーディング
    
    def count_tokens(self, text: str) -> int:
        """テキストのトークン数をカウント"""
        return len(self.encoding.encode(text))
    
    def add_usage(self, model: str, input_text: str, output_text: str) -> Tuple[int, float]:
        """使用量を追加し、トークン数とコストを返す"""
        input_tokens = self.count_tokens(input_text)
        output_tokens = self.count_tokens(output_text)
        
        # モデル別使用量を更新
        if model in self.usage:
            self.usage[model].input_tokens += input_tokens
            self.usage[model].output_tokens += output_tokens
        
        # コスト計算
        cost = self._calculate_cost(model, input_tokens, output_tokens)
        
        # 累計更新
        session_tokens = input_tokens + output_tokens
        self.total_tokens += session_tokens
        self.total_cost += cost
        
        return session_tokens, cost
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """モデル別コスト計算"""
        if model == "ChatGPT":
            return (input_tokens * cost_config.CHATGPT_INPUT_COST + 
                   output_tokens * cost_config.CHATGPT_OUTPUT_COST)
        elif model == "Claude":
            return (input_tokens * cost_config.CLAUDE_INPUT_COST + 
                   output_tokens * cost_config.CLAUDE_OUTPUT_COST)
        elif model == "Gemini":
            return (input_tokens * cost_config.GEMINI_INPUT_COST + 
                   output_tokens * cost_config.GEMINI_OUTPUT_COST)
        else:
            return 0.0
    
    def get_usage_percentage(self) -> float:
        """トークン使用率を取得（0-100%）"""
        return (self.total_tokens / self.token_limit) * 100 if self.token_limit > 0 else 0
    
    def is_limit_exceeded(self) -> bool:
        """制限を超過しているかチェック"""
        return self.total_tokens >= self.token_limit
    
    def is_warning_threshold(self) -> bool:
        """警告閾値を超えているかチェック（90%）"""
        return self.get_usage_percentage() >= 90.0
    
    def get_remaining_tokens(self) -> int:
        """残りトークン数を取得"""
        return max(0, self.token_limit - self.total_tokens)
    
    def get_status_summary(self) -> Dict:
        """現在の状況サマリーを取得"""
        return {
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost, 4),
            "usage_percentage": round(self.get_usage_percentage(), 1),
            "remaining_tokens": self.get_remaining_tokens(),
            "is_warning": self.is_warning_threshold(),
            "is_limit_exceeded": self.is_limit_exceeded(),
            "usage_by_model": {
                model: {
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "total_tokens": usage.total_tokens,
                    "cost_usd": round(self._calculate_cost(model, usage.input_tokens, usage.output_tokens), 4)
                }
                for model, usage in self.usage.items()
            }
        }
    
    def format_status_display(self) -> str:
        """ステータス表示用のフォーマット済み文字列"""
        percentage = self.get_usage_percentage()
        status_icon = "🔴" if self.is_limit_exceeded() else "⚠️" if self.is_warning_threshold() else "🟢"
        
        return f"""
{status_icon} トークン使用状況: {self.total_tokens:,}/{self.token_limit:,} ({percentage:.1f}%)
💰 累計コスト: ${self.total_cost:.4f}
📊 残りトークン: {self.get_remaining_tokens():,}

モデル別詳細:
  ChatGPT: {self.usage['ChatGPT'].total_tokens:,} tokens (${self._calculate_cost('ChatGPT', self.usage['ChatGPT'].input_tokens, self.usage['ChatGPT'].output_tokens):.4f})
  Claude:  {self.usage['Claude'].total_tokens:,} tokens (${self._calculate_cost('Claude', self.usage['Claude'].input_tokens, self.usage['Claude'].output_tokens):.4f})
  Gemini:  {self.usage['Gemini'].total_tokens:,} tokens (${self._calculate_cost('Gemini', self.usage['Gemini'].input_tokens, self.usage['Gemini'].output_tokens):.4f})
"""

def create_cost_monitor(token_limit: int = 50000) -> CostMonitor:
    """コスト監視インスタンスを作成"""
    monitor = CostMonitor()
    monitor.token_limit = token_limit
    return monitor 