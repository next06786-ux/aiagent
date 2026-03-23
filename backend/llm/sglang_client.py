"""
SGLang 客户端
用于后端服务调用 GPU 服务器上的 SGLang
兼容 OpenAI API 格式
"""
import os
import httpx
import asyncio
from typing import Optional, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass


@dataclass
class SGLangConfig:
    """SGLang 服务配置"""
    server_url: str = os.environ.get("SGLANG_SERVER_URL", "http://localhost:8001")
    model_name: str = os.environ.get("SGLANG_MODEL_NAME", "Qwen/Qwen3.5-9B")
    timeout: float = 120.0
    max_retries: int = 3


class SGLangClient:
    """SGLang 异步客户端"""
    
    def __init__(self, config: SGLangConfig = None):
        self.config = config or SGLangConfig()
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.server_url,
                timeout=self.config.timeout
            )
        return self._client
    
    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def health_check(self) -> Dict:
        """健康检查"""
        try:
            resp = await self.client.get("/health")
            if resp.status_code == 200:
                return {"status": "healthy"}
            # SGLang 也支持 /health_generate
            resp = await self.client.get("/health_generate")
            if resp.status_code == 200:
                return {"status": "healthy"}
            return {"status": "unhealthy", "code": resp.status_code}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def get_model_info(self) -> Dict:
        """获取模型信息"""
        try:
            resp = await self.client.get("/model_info")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 0.9,
        stream: bool = False,
        lora_path: str = None
    ) -> str:
        """
        聊天补全
        
        Args:
            messages: [{"role": "user", "content": "..."}]
            temperature: 温度
            max_tokens: 最大生成长度
            top_p: Top-p 采样
            stream: 是否流式
            lora_path: LoRA adapter 路径，传入后 SGLang 会在基座上叠加该 LoRA
        
        Returns:
            助手回复
        """
        payload = {
            "model": lora_path if lora_path else self.config.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": stream
        }
        
        resp = await self.client.post("/v1/chat/completions", json=payload)
        resp.raise_for_status()
        
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 0.9,
        lora_path: str = None
    ) -> AsyncGenerator[str, None]:
        """流式聊天"""
        payload = {
            "model": lora_path if lora_path else self.config.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": True
        }
        
        async with self.client.stream("POST", "/v1/chat/completions", json=payload) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        import json
                        chunk = json.loads(data)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except:
                        pass
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 0.9,
        lora_path: str = None
    ) -> str:
        """文本补全"""
        payload = {
            "model": lora_path if lora_path else self.config.model_name,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p
        }
        
        resp = await self.client.post("/v1/completions", json=payload)
        resp.raise_for_status()
        
        data = resp.json()
        return data["choices"][0]["text"]


class SGLangClientSync:
    """SGLang 同步客户端"""
    
    def __init__(self, config: SGLangConfig = None):
        self.config = config or SGLangConfig()
        self._client: Optional[httpx.Client] = None
    
    @property
    def client(self) -> httpx.Client:
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(
                base_url=self.config.server_url,
                timeout=self.config.timeout
            )
        return self._client
    
    def close(self):
        if self._client and not self._client.is_closed:
            self._client.close()
    
    def health_check(self) -> Dict:
        try:
            resp = self.client.get("/health")
            if resp.status_code == 200:
                return {"status": "healthy"}
            return {"status": "unhealthy", "code": resp.status_code}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 0.9,
        lora_path: str = None
    ) -> str:
        payload = {
            "model": lora_path if lora_path else self.config.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p
        }
        
        resp = self.client.post("/v1/chat/completions", json=payload)
        resp.raise_for_status()
        
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        lora_path: str = None
    ) -> str:
        payload = {
            "model": lora_path if lora_path else self.config.model_name,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        resp = self.client.post("/v1/completions", json=payload)
        resp.raise_for_status()
        
        data = resp.json()
        return data["choices"][0]["text"]


# 全局客户端实例
_sglang_client: Optional[SGLangClient] = None
_sglang_client_sync: Optional[SGLangClientSync] = None


def get_sglang_client() -> SGLangClient:
    """获取异步客户端"""
    global _sglang_client
    if _sglang_client is None:
        _sglang_client = SGLangClient()
    return _sglang_client


def get_sglang_client_sync() -> SGLangClientSync:
    """获取同步客户端"""
    global _sglang_client_sync
    if _sglang_client_sync is None:
        _sglang_client_sync = SGLangClientSync()
    return _sglang_client_sync


# ============== 便捷函数 ==============

async def chat_with_sglang(
    message: str,
    system_prompt: str = None,
    history: List[Dict] = None,
    temperature: float = 0.7,
    max_tokens: int = 1024
) -> str:
    """
    使用 SGLang 进行对话
    
    Args:
        message: 用户消息
        system_prompt: 系统提示
        history: 历史对话
        temperature: 温度
        max_tokens: 最大长度
    
    Returns:
        AI 回复
    """
    client = get_sglang_client()
    
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    if history:
        messages.extend(history)
    
    messages.append({"role": "user", "content": message})
    
    return await client.chat(messages, temperature=temperature, max_tokens=max_tokens)


def chat_with_sglang_sync(
    message: str,
    system_prompt: str = None,
    history: List[Dict] = None,
    temperature: float = 0.7,
    max_tokens: int = 1024
) -> str:
    """同步版本"""
    client = get_sglang_client_sync()
    
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    if history:
        messages.extend(history)
    
    messages.append({"role": "user", "content": message})
    
    return client.chat(messages, temperature=temperature, max_tokens=max_tokens)


# ============== 测试 ==============

if __name__ == "__main__":
    async def test():
        client = SGLangClient()
        
        # 健康检查
        print("🔍 健康检查...")
        health = await client.health_check()
        print(f"   {health}")
        
        if health.get("status") != "healthy":
            print("❌ 服务不可用")
            return
        
        # 获取模型信息
        print("\n📋 模型信息...")
        info = await client.get_model_info()
        print(f"   {info}")
        
        # 测试聊天
        print("\n💬 测试聊天...")
        response = await client.chat(
            messages=[{"role": "user", "content": "你好，请简单介绍一下你自己"}],
            temperature=0.7,
            max_tokens=200
        )
        print(f"   回复: {response}")
        
        await client.close()
        print("\n✅ 测试完成")
    
    asyncio.run(test())
