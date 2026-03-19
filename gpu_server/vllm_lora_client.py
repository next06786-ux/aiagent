#!/usr/bin/env python3
"""
vLLM Multi-LoRA 客户端
用于与 vLLM 服务器交互，支持多用户 LoRA
"""
import httpx
import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class LoRAInfo:
    """LoRA 信息"""
    name: str
    user_id: str
    path: str
    version: int
    is_loaded: bool = False


class VLLMLoRAClient:
    """vLLM Multi-LoRA 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
    
    async def health_check(self) -> Dict:
        """健康检查"""
        resp = await self.client.get(f"{self.base_url}/health")
        resp.raise_for_status()
        return resp.json()
    
    async def list_models(self) -> List[Dict]:
        """列出所有模型"""
        resp = await self.client.get(f"{self.base_url}/v1/models")
        resp.raise_for_status()
        return resp.json()["data"]
    
    async def list_loras(self) -> List[LoRAInfo]:
        """列出所有 LoRA 适配器"""
        resp = await self.client.get(f"{self.base_url}/v1/loras")
        resp.raise_for_status()
        data = resp.json()
        return [LoRAInfo(**lora) for lora in data["loras"]]
    
    async def reload_loras(self) -> Dict:
        """重新加载 LoRA 适配器"""
        resp = await self.client.post(f"{self.base_url}/v1/loras/reload")
        resp.raise_for_status()
        return resp.json()
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        user_id: Optional[str] = None,
        lora_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """
        聊天补全
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            user_id: 用户 ID（自动选择对应的 LoRA）
            lora_name: 直接指定 LoRA 名称
            temperature: 温度
            max_tokens: 最大生成长度
        
        Returns:
            助手回复内容
        """
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if user_id:
            payload["user_id"] = user_id
        if lora_name:
            payload["lora_name"] = lora_name
        
        resp = await self.client.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload
        )
        resp.raise_for_status()
        
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    
    async def complete(
        self,
        prompt: str,
        user_id: Optional[str] = None,
        lora_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """
        文本补全
        
        Args:
            prompt: 提示文本
            user_id: 用户 ID
            lora_name: LoRA 名称
            temperature: 温度
            max_tokens: 最大生成长度
        
        Returns:
            生成的文本
        """
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if user_id:
            payload["user_id"] = user_id
        if lora_name:
            payload["lora_name"] = lora_name
        
        resp = await self.client.post(
            f"{self.base_url}/v1/completions",
            json=payload
        )
        resp.raise_for_status()
        
        data = resp.json()
        return data["choices"][0]["text"]
    
    async def generate(
        self,
        prompt: str,
        user_id: Optional[str] = None,
        lora_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> Dict:
        """简单生成接口"""
        params = {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if user_id:
            params["user_id"] = user_id
        if lora_name:
            params["lora_name"] = lora_name
        
        resp = await self.client.post(
            f"{self.base_url}/generate",
            params=params
        )
        resp.raise_for_status()
        return resp.json()


# 同步版本的客户端
class VLLMLoRAClientSync:
    """同步版本的 vLLM 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=120.0)
    
    def close(self):
        self.client.close()
    
    def health_check(self) -> Dict:
        resp = self.client.get(f"{self.base_url}/health")
        resp.raise_for_status()
        return resp.json()
    
    def list_loras(self) -> List[Dict]:
        resp = self.client.get(f"{self.base_url}/v1/loras")
        resp.raise_for_status()
        return resp.json()["loras"]
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        user_id: Optional[str] = None,
        lora_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if user_id:
            payload["user_id"] = user_id
        if lora_name:
            payload["lora_name"] = lora_name
        
        resp = self.client.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload
        )
        resp.raise_for_status()
        
        data = resp.json()
        return data["choices"][0]["message"]["content"]


# ============== 测试代码 ==============

async def test_client():
    """测试客户端"""
    client = VLLMLoRAClient("http://localhost:8000")
    
    try:
        # 1. 健康检查
        print("🔍 健康检查...")
        health = await client.health_check()
        print(f"   状态: {health}")
        
        # 2. 列出 LoRA
        print("\n📦 LoRA 列表...")
        loras = await client.list_loras()
        for lora in loras:
            print(f"   - {lora.name} (user: {lora.user_id}, v{lora.version})")
        
        if not loras:
            print("   (暂无 LoRA 适配器)")
        
        # 3. 测试聊天（无 LoRA）
        print("\n💬 测试聊天（基座模型）...")
        response = await client.chat(
            messages=[{"role": "user", "content": "你好，请简单介绍一下你自己"}],
            temperature=0.7,
            max_tokens=200
        )
        print(f"   回复: {response[:200]}...")
        
        # 4. 测试聊天（带 LoRA，如果有的话）
        if loras:
            print(f"\n💬 测试聊天（使用 {loras[0].name}）...")
            response = await client.chat(
                messages=[{"role": "user", "content": "你好，请简单介绍一下你自己"}],
                lora_name=loras[0].name,
                temperature=0.7,
                max_tokens=200
            )
            print(f"   回复: {response[:200]}...")
        
        print("\n✅ 测试完成!")
        
    except httpx.ConnectError:
        print("❌ 无法连接到服务器，请确保 vLLM 服务已启动")
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_client())
