# engine/utils/api_client.py
import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

# ═══════════════════════════════════════════
#   PyInstaller 打包兼容：根据运行模式定位 .env 文件
#   frozen=True  → .exe 同级目录
#   frozen=False → 项目根目录 (开发模式，engine/utils/ 向上两级)
# ═══════════════════════════════════════════
def _resolve_env_path() -> str:
    if getattr(sys, 'frozen', False):
        # PyInstaller 单文件打包：.env 与 .exe 同级
        return os.path.join(os.path.dirname(sys.executable), '.env')
    else:
        # 开发模式：engine/utils/api_client.py → 项目根目录
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            '.env'
        )

load_dotenv(_resolve_env_path())

class LLMClient:
    """
    独立解耦的大语言模型 API 客户端
    统一处理认证、请求与异常，方便随时切换 OpenAI、DeepSeek、Ollama 等兼容接口
    """
    def __init__(self):
        # 从 .env 读取配置，如果没有配置则给默认的 DeepSeek 官方接口
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
        self.default_model = os.getenv("OPENAI_MODEL", "deepseek-chat")
        # 【新增】：从 .env 读取高级参数，带默认值和类型转换
        try:
            self.default_temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.01"))
        except ValueError:
            self.default_temperature = 0.01  # 容错兜底
            
        try:
            self.default_max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "4000"))
        except ValueError:
            self.default_max_tokens = 4000   # 容错兜底


            
        # 【防线1修改】：去掉 raise，改为赋值 flag
        if not self.api_key:
            self._key_missing = True
        else:
            self._key_missing = False
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
        

    def generate_response(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        model: str = None, 
        stream: bool = False,
        temperature: float = None,  # 改为 None，以便动态接收 self 里的配置
        max_tokens: int = None      # 改为 None，以便动态接收 self 里的配置
    ):

        # 动态赋值：如果调用时没指定，就用 .env 里读到的全局配置
        actual_temp = temperature if temperature is not None else self.default_temperature
        actual_tokens = max_tokens if max_tokens is not None else self.default_max_tokens

        if getattr(self, '_key_missing', False):
            if stream:
                # 返回一个伪造的生成器
                def fake_stream():
                    class DummyDelta:
                        def __init__(self, c): self.content = c
                    class DummyChoice:
                        def __init__(self, c): self.delta = DummyDelta(c)
                    class DummyChunk:
                        def __init__(self, c): self.choices = [DummyChoice(c)]
                    
                    yield DummyChunk("🚨 [系统提示] 未检测到大模型 API Key！\n")
                    yield DummyChunk("请在项目根目录找到 `.env.example` 文件，将其重命名为 `.env`，并在其中填入你的密钥，然后重启引擎。")
                return fake_stream()
            else:
                return "🚨 [系统提示] 未检测到大模型 API Key！请配置 .env 文件。"


        """
        发起模型调用
        """
        target_model = model if model else self.default_model
        
        try:
            response = self.client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            if stream:
                return response # 如果是流式，直接返回生成器对象
            else:
                return response.choices[0].message.content
                
        except Exception as e:
            return f"[API 调用失败] 请检查网络或余额。错误信息: {str(e)}"