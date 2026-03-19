"""
vLLM Multi-LoRA 客户端
用于后端服务调用 GPU 服务器上的 vLLM
"""
import os
import httpx
import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class VLLMConfig:
    """vLLM 服务配置"""
    # GPU 服务器地址
    server_url: str = os.environ.get("VLLM_SERVER_URL", "http://localhost:8000")
    # 超时时间
    timeout: float = 120.0
    # 重试次数
    max_retries: int = 3


class VLLMClient:
    """vLLM 异步客户端"""
    
    def __init__(self, config: VLLMConfig = None):
        self.config = config or VLLMConfig()
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
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        user_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        """
        聊天补全
        
        Args:
            messages: [{"role": "user", "content": "..."}]
            user_id: 用户 ID（使用该用户的 LoRA）
            temperature: 温度
            max_tokens: 最大生成长度
        
        Returns:
            助手回复
        """
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if user_id:
            payload["user_id"] = user_id
        
        resp = await self.client.post("/v1/chat/completions", json=payload)
        resp.raise_for_status()
        
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    
    async def generate(
        self,
        prompt: str,
        user_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        """文本补全"""
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if user_id:
            payload["user_id"] = user_id
        
        resp = await self.client.post("/v1/completions", json=payload)
        resp.raise_for_status()
        
        data = resp.json()
        return data["choices"][0]["text"]
    
    async def get_user_lora(self, user_id: str) -> Dict:
        """获取用户 LoRA 信息"""
        resp = await self.client.get(f"/v1/users/{user_id}/lora")
        resp.raise_for_status()
        return resp.json()
    
    async def has_user_lora(self, user_id: str) -> bool:
        """检查用户是否有 LoRA"""
        info = await self.get_user_lora(user_id)
        return info.get("has_lora", False)
    
    async def train_lora(
        self,
        user_id: str,
        conversations: List[Dict[str, str]],
        num_epochs: int = 3
    ) -> Dict:
        """
        提交 LoRA 训练任务
        
        Args:
            user_id: 用户 ID
            conversations: [{"user": "...", "assistant": "..."}]
            num_epochs: 训练轮数
        
        Returns:
            任务信息
        """
        payload = {
            "user_id": user_id,
            "conversations": conversations,
            "num_epochs": num_epochs
        }
        
        resp = await self.client.post("/v1/train", json=payload)
        resp.raise_for_status()
        return resp.json()
    
    async def get_training_status(self, user_id: str) -> Dict:
        """获取训练状态"""
        resp = await self.client.get(f"/v1/train/{user_id}/status")
        if resp.status_code == 404:
            return {"status": "not_found"}
        resp.raise_for_status()
        return resp.json()
    
    async def list_loras(self) -> List[Dict]:
        """列出所有 LoRA"""
        resp = await self.client.get("/v1/loras")
        resp.raise_for_status()
        return resp.json()["loras"]


class VLLMClientSync:
    """vLLM 同步客户端"""
    
    def __init__(self, config: VLLMConfig = None):
        self.config = config or VLLMConfig()
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
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        user_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if user_id:
            payload["user_id"] = user_id
        
        resp = self.client.post("/v1/chat/completions", json=payload)
        resp.raise_for_status()
        
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    
    def generate(
        self,
        prompt: str,
        user_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if user_id:
            payload["user_id"] = user_id
        
        resp = self.client.post("/v1/completions", json=payload)
        resp.raise_for_status()
        
        data = resp.json()
        return data["choices"][0]["text"]
    
    def has_user_lora(self, user_id: str) -> bool:
        resp = self.client.get(f"/v1/users/{user_id}/lora")
        if resp.status_code == 200:
            return resp.json().get("has_lora", False)
        return False


# 全局客户端实例
_vllm_client: Optional[VLLMClient] = None
_vllm_client_sync: Optional[VLLMClientSync] = None


def get_vllm_client() -> VLLMClient:
    """获取异步客户端"""
    global _vllm_client
    if _vllm_client is None:
        _vllm_client = VLLMClient()
    return _vllm_client


def get_vllm_client_sync() -> VLLMClientSync:
    """获取同步客户端"""
    global _vllm_client_sync
    if _vllm_client_sync is None:
        _vllm_client_sync = VLLMClientSync()
    return _vllm_client_sync


# ============== 便捷函数 ==============

async def chat_with_lora(
    user_id: str,
    message: str,
    system_prompt: str = None,
    history: List[Dict] = None
) -> str:
    """
    使用用户专属 LoRA 进行对话
    
    Args:
        user_id: 用户 ID
        message: 用户消息
        system_prompt: 系统提示
        history: 历史对话
    
    Returns:
        AI 回复
    """
    client = get_vllm_client()
    
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    if history:
        messages.extend(history)
    
    messages.append({"role": "user", "content": message})
    
    return await client.chat(messages, user_id=user_id)


def chat_with_lora_sync(
    user_id: str,
    message: str,
    system_prompt: str = None,
    history: List[Dict] = None
) -> str:
    """同步版本"""
    client = get_vllm_client_sync()
    
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    if history:
        messages.extend(history)
    
    messages.append({"role": "user", "content": message})
    
    return client.chat(messages, user_id=user_id)


# ============== 测试 ==============

if __name__ == "__main__":
    async def test():
        client = VLLMClient()
        
        # 健康检查
        print("🔍 健康检查...")
        health = await client.health_check()
        print(f"   {health}")
        
        if health.get("status") != "healthy":
            print("❌ 服务不可用")
            return
        
        # 测试聊天
        print("\n💬 测试聊天...")
        response = await client.chat(
            messages=[{"role": "user", "content": "你好"}],
            temperature=0.7
        )
        print(f"   回复: {response[:100]}...")
        
        # 列出 LoRA
        print("\n📦 LoRA 列表...")
        loras = await client.list_loras()
        for lora in loras:
            print(f"   - {lora['user_id']} (v{lora['version']})")
        
        await client.close()
        print("\n✅ 测试完成")
    
    asyncio.run(test())
