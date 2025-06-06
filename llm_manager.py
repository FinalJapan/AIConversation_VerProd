import time
import random
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod

import openai
import anthropic
import google.generativeai as genai

from config import config

class BaseLLM(ABC):
    """LLM基底クラス"""
    
    def __init__(self, name: str):
        self.name = name
        self.is_available = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """初期化"""
        pass
    
    @abstractmethod
    def generate_response(self, messages: List[Dict], max_tokens: int = 500) -> str:
        """応答生成"""
        pass
    
    def create_conversation_context(self, previous_messages: List[str], current_topic: str) -> List[Dict]:
        """会話コンテキストを作成"""
        context = []
        
        # システムプロンプト
        system_prompt = f"""あなたは他のAIと会話をしています。
現在のトピック: {current_topic}

会話のルール:
1. 自然で興味深い会話を心がけてください
2. 他のAIの発言に対して適切に反応してください  
3. 新しい観点や質問を提供してください
4. 簡潔に（500文字以内で）回答してください
5. あなたの個性を活かした発言をしてください
6. 発言に他のAIの名前は含めず、直接応答してください"""

        context.append({"role": "system", "content": system_prompt})
        
        # 過去の会話履歴を追加（最新10件まで）
        recent_messages = previous_messages[-10:] if len(previous_messages) > 10 else previous_messages
        
        for i, msg in enumerate(recent_messages):
            # 発言者名を除去（「ChatGPT:」「Claude:」「Gemini:」を削除）
            clean_msg = msg
            if ": " in msg:
                parts = msg.split(": ", 1)
                if parts[0] in ["ChatGPT", "Claude", "Gemini", "会話トピック"]:
                    clean_msg = parts[1] if len(parts) > 1 else msg
            
            role = "assistant" if i % 2 == 0 else "user"
            context.append({"role": role, "content": clean_msg})
        
        return context

class ChatGPTLLM(BaseLLM):
    """ChatGPT API管理"""
    
    def __init__(self):
        super().__init__("ChatGPT")
        self.client = None
        self.model = "gpt-4o"
    
    def initialize(self) -> bool:
        """初期化"""
        try:
            if not config.openai_api_key:
                print("⚠️ OpenAI APIキーが設定されていません")
                return False
            
            self.client = openai.OpenAI(api_key=config.openai_api_key)
            
            # 接続テスト
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            
            self.is_available = True
            print(f"✅ {self.name} 初期化完了")
            return True
            
        except Exception as e:
            print(f"❌ {self.name} 初期化失敗: {e}")
            return False
    
    def generate_response(self, messages: List[Dict], max_tokens: int = 500) -> str:
        """応答生成"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"{self.name} API呼び出しエラー: {e}")

class ClaudeLLM(BaseLLM):
    """Claude API管理"""
    
    def __init__(self):
        super().__init__("Claude")
        self.client = None
        self.model = "claude-3-5-sonnet-20241022"
    
    def initialize(self) -> bool:
        """初期化"""
        try:
            if not config.anthropic_api_key:
                print("⚠️ Anthropic APIキーが設定されていません")
                return False
            
            self.client = anthropic.Anthropic(api_key=config.anthropic_api_key)
            
            # 接続テスト
            response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}]
            )
            
            self.is_available = True
            print(f"✅ {self.name} 初期化完了")
            return True
            
        except Exception as e:
            print(f"❌ {self.name} 初期化失敗: {e}")
            return False
    
    def generate_response(self, messages: List[Dict], max_tokens: int = 500) -> str:
        """応答生成"""
        try:
            # Claudeの場合、system messageを分離
            system_message = ""
            user_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    user_messages.append(msg)
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_message,
                messages=user_messages,
                temperature=0.7
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            raise Exception(f"{self.name} API呼び出しエラー: {e}")

class GeminiLLM(BaseLLM):
    """Gemini API管理"""
    
    def __init__(self):
        super().__init__("Gemini")
        self.model = None
        self.model_name = "gemini-2.0-flash-exp"
    
    def initialize(self) -> bool:
        """初期化"""
        try:
            if not config.google_api_key:
                print("⚠️ Google APIキーが設定されていません")
                return False
            
            genai.configure(api_key=config.google_api_key)
            self.model = genai.GenerativeModel(self.model_name)
            
            # 接続テスト
            response = self.model.generate_content("Hello")
            
            self.is_available = True
            print(f"✅ {self.name} 初期化完了")
            return True
            
        except Exception as e:
            print(f"❌ {self.name} 初期化失敗: {e}")
            return False
    
    def generate_response(self, messages: List[Dict], max_tokens: int = 500) -> str:
        """応答生成"""
        try:
            # Geminiの場合、会話履歴を単一のプロンプトに結合
            prompt = ""
            
            for msg in messages:
                if msg["role"] == "system":
                    prompt += f"System: {msg['content']}\n\n"
                elif msg["role"] == "user":
                    prompt += f"User: {msg['content']}\n\n"
                elif msg["role"] == "assistant":
                    prompt += f"Assistant: {msg['content']}\n\n"
            
            prompt += "あなたの応答:"
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7
                )
            )
            
            return response.text.strip()
            
        except Exception as e:
            raise Exception(f"{self.name} API呼び出しエラー: {e}")

class LLMManager:
    """LLM管理クラス"""
    
    def __init__(self):
        self.llms = {
            "ChatGPT": ChatGPTLLM(),
            "Claude": ClaudeLLM(),
            "Gemini": GeminiLLM()
        }
        self.available_llms = []
        self.conversation_history = []
        self.previous_speaker = None
    
    def initialize_all(self) -> List[str]:
        """全LLMを初期化"""
        print("🔧 LLM初期化中...")
        
        for name, llm in self.llms.items():
            if llm.initialize():
                self.available_llms.append(name)
        
        if not self.available_llms:
            raise Exception("利用可能なLLMがありません。APIキーを確認してください。")
        
        print(f"✅ 利用可能なLLM: {', '.join(self.available_llms)}")
        return self.available_llms
    
    def select_next_speaker(self) -> str:
        """次の発言者をランダム選択（直前の発言者は除外）"""
        candidates = [name for name in self.available_llms if name != self.previous_speaker]
        
        if not candidates:
            candidates = self.available_llms
        
        next_speaker = random.choice(candidates)
        self.previous_speaker = next_speaker
        return next_speaker
    
    def generate_response(self, speaker: str, topic: str, max_tokens: int = 500) -> str:
        """指定されたLLMで応答を生成"""
        if speaker not in self.available_llms:
            raise Exception(f"{speaker} は利用できません")
        
        llm = self.llms[speaker]
        context = llm.create_conversation_context(self.conversation_history, topic)
        
        try:
            response = llm.generate_response(context, max_tokens)
            
            # 会話履歴に追加
            self.conversation_history.append(f"{speaker}: {response}")
            
            return response
            
        except Exception as e:
            print(f"❌ {speaker} の応答生成に失敗: {e}")
            raise
    
    def add_initial_message(self, topic: str):
        """初期メッセージを会話履歴に追加"""
        self.conversation_history.append(f"会話トピック: {topic}")
    
    def get_conversation_length(self) -> int:
        """会話の長さを取得"""
        return len(self.conversation_history)
    
    def wait_for_rate_limit(self, wait_time: int = 2):
        """レート制限対応の待機"""
        if wait_time > 0:
            print(f"⏳ {wait_time}秒待機中...")
            time.sleep(wait_time)

def create_llm_manager() -> LLMManager:
    """LLMマネージャーインスタンスを作成"""
    return LLMManager() 