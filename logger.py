import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class ChatMessage:
    """会話メッセージのデータクラス"""
    timestamp: str
    model: str
    content: str
    tokens: int
    cost: float
    
    @classmethod
    def create(cls, model: str, content: str, tokens: int = 0, cost: float = 0.0):
        """新しいメッセージを作成"""
        return cls(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            model=model,
            content=content,
            tokens=tokens,
            cost=cost
        )

class ConversationLogger:
    """会話ログ管理クラス"""
    
    def __init__(self, log_dir: str = "logs", session_name: Optional[str] = None):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # セッション名の生成
        if session_name is None:
            session_name = datetime.now().strftime("conversation_%Y%m%d_%H%M%S")
        
        self.session_name = session_name
        self.messages: List[ChatMessage] = []
        
        # ファイルパス設定
        self.text_log_path = self.log_dir / f"{session_name}.txt"
        self.json_log_path = self.log_dir / f"{session_name}.json"
        
        # セッション開始ログ
        self._log_session_start()
    
    def _log_session_start(self):
        """セッション開始ログ"""
        start_msg = f"=== 会話セッション開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n"
        
        # テキストログファイルに書き込み
        with open(self.text_log_path, 'w', encoding='utf-8') as f:
            f.write(start_msg)
    
    def add_message(self, model: str, content: str, tokens: int = 0, cost: float = 0.0):
        """メッセージを追加"""
        message = ChatMessage.create(model, content, tokens, cost)
        self.messages.append(message)
        
        # リアルタイムでファイルに保存
        self._save_text_log(message)
        self._save_json_log()
        
        return message
    
    def _save_text_log(self, message: ChatMessage):
        """テキストログファイルに追記"""
        # モデル別の色分け記号
        model_icons = {
            "ChatGPT": "🤖",
            "Claude": "🧠", 
            "Gemini": "⭐",
            "System": "🔧"
        }
        
        icon = model_icons.get(message.model, "❓")
        
        log_entry = f"""
[{message.timestamp}] {icon} {message.model}
{'-' * 50}
{message.content}

📊 トークン: {message.tokens}, 💰 コスト: ${message.cost:.4f}
{'=' * 80}

"""
        
        with open(self.text_log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def _save_json_log(self):
        """JSON形式でログを保存"""
        log_data = {
            "session_name": self.session_name,
            "start_time": self.messages[0].timestamp if self.messages else None,
            "message_count": len(self.messages),
            "messages": [asdict(msg) for msg in self.messages]
        }
        
        with open(self.json_log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    def add_system_message(self, content: str):
        """システムメッセージを追加"""
        return self.add_message("System", content, 0, 0.0)
    
    def get_conversation_summary(self) -> Dict:
        """会話のサマリーを取得"""
        if not self.messages:
            return {"message_count": 0, "total_tokens": 0, "total_cost": 0.0}
        
        total_tokens = sum(msg.tokens for msg in self.messages)
        total_cost = sum(msg.cost for msg in self.messages)
        
        # モデル別統計
        model_stats = {}
        for msg in self.messages:
            if msg.model not in model_stats:
                model_stats[msg.model] = {"count": 0, "tokens": 0, "cost": 0.0}
            
            model_stats[msg.model]["count"] += 1
            model_stats[msg.model]["tokens"] += msg.tokens
            model_stats[msg.model]["cost"] += msg.cost
        
        return {
            "session_name": self.session_name,
            "start_time": self.messages[0].timestamp,
            "end_time": self.messages[-1].timestamp,
            "duration_minutes": self._calculate_duration(),
            "message_count": len(self.messages),
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 4),
            "model_stats": {k: {**v, "cost": round(v["cost"], 4)} for k, v in model_stats.items()}
        }
    
    def _calculate_duration(self) -> float:
        """会話の継続時間を計算（分）"""
        if len(self.messages) < 2:
            return 0.0
        
        start_time = datetime.strptime(self.messages[0].timestamp, "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(self.messages[-1].timestamp, "%Y-%m-%d %H:%M:%S")
        
        duration = end_time - start_time
        return round(duration.total_seconds() / 60, 2)
    
    def finalize_session(self, summary_stats: Optional[Dict] = None):
        """セッション終了処理"""
        end_message = f"\n=== 会話セッション終了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n"
        
        # 統計情報を追加
        if summary_stats:
            end_message += f"""
会話統計:
- 総メッセージ数: {summary_stats.get('message_count', 0)}
- 総トークン数: {summary_stats.get('total_tokens', 0):,}
- 総コスト: ${summary_stats.get('total_cost', 0):.4f}
- セッション時間: {summary_stats.get('duration_minutes', 0):.1f}分
"""
        
        with open(self.text_log_path, 'a', encoding='utf-8') as f:
            f.write(end_message)
        
        # 最終JSON保存
        self._save_json_log()
        
        print(f"💾 ログファイルを保存しました:")
        print(f"  テキスト: {self.text_log_path}")
        print(f"  JSON: {self.json_log_path}")

def create_logger(log_dir: str = "logs", session_name: Optional[str] = None) -> ConversationLogger:
    """ロガーインスタンスを作成"""
    return ConversationLogger(log_dir, session_name) 