"""
远程模型客户端
在本地运行，通过 HTTP 调用服务器的模型推理服务
"""
import os
import logging
from typing import List, Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class RemoteModelClient:
    """远程模型客户端"""
    
    def __init__(self, base_url: str = None, timeout: float = 300.0):
        """
        初始化远程模型客户端
        
        Args:
            base_url: 远程服务器地址，如 http://your-server:8001
            timeout: 请求超时时间（秒）
        """
        # 从环境变量读取服务器地址
        self.base_url = base_url or os.environ.get(
            "REMOTE_MODEL_URL",
            "http://localhost:8001"
        )
        
        self.timeout = timeout
        self.is_available = False
        
        # 创建 HTTP 客户端（支持HTTPS和自签名证书）
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout, connect=10.0),
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20
            ),
            verify=False  # 禁用SSL证书验证（AutoDL使用自签名证书）
        )
        
        logger.info(f"[远程模型] 初始化客户端，服务器: {self.base_url}")
        
        # 检查服务器可用性
        self._check_availability()
    
    def _check_availability(self):
        """检查服务器是否可用"""
        try:
            response = self.client.get("/health", timeout=5.0)
            if response.status_code == 200:
                self.is_available = True
                logger.info(f"[远程模型] ✅ 服务器可用: {self.base_url}")
            else:
                self.is_available = False
                logger.warning(f"[远程模型] 服务器响应异常: {response.status_code}")
        except Exception as e:
            self.is_available = False
            logger.warning(f"[远程模型] 服务器不可用: {e}")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        聊天接口
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大生成token数
        
        Returns:
            生成的回复文本
        """
        if not self.is_available:
            # 重新检查一次
            self._check_availability()
            if not self.is_available:
                raise RuntimeError(f"远程模型服务器不可用: {self.base_url}")
        
        try:
            logger.info(f"[远程模型] 发送推理请求，消息数: {len(messages)}")
            
            # 发送请求
            response = self.client.post(
                "/chat",
                json={
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            
            # 检查响应
            if response.status_code != 200:
                error_detail = response.json().get("detail", "未知错误")
                raise RuntimeError(f"远程推理失败: {error_detail}")
            
            # 解析响应
            result = response.json()
            content = result.get("content", "")
            inference_time = result.get("inference_time", 0)
            
            logger.info(f"[远程模型] 推理完成，耗时: {inference_time:.3f}秒")
            
            return content
        
        except httpx.TimeoutException:
            logger.error(f"[远程模型] 请求超时（{self.timeout}秒）")
            self.is_available = False
            raise RuntimeError(f"远程模型请求超时")
        
        except httpx.ConnectError as e:
            logger.error(f"[远程模型] 连接失败: {e}")
            self.is_available = False
            raise RuntimeError(f"无法连接到远程模型服务器: {self.base_url}")
        
        except Exception as e:
            logger.error(f"[远程模型] 请求失败: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        try:
            response = self.client.get("/model/info", timeout=10.0)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"获取信息失败: {response.status_code}"}
        except Exception as e:
            logger.error(f"[远程模型] 获取模型信息失败: {e}")
            return {"error": str(e)}
    
    def close(self):
        """关闭客户端"""
        self.client.close()
        logger.info("[远程模型] 客户端已关闭")


# 全局单例
_remote_client: Optional[RemoteModelClient] = None


def get_remote_model_client() -> RemoteModelClient:
    """获取远程模型客户端单例"""
    global _remote_client
    
    if _remote_client is None:
        _remote_client = RemoteModelClient()
    
    return _remote_client


def test_remote_model():
    """测试远程模型"""
    print("测试远程模型客户端...")
    
    client = get_remote_model_client()
    
    if not client.is_available:
        print(f"❌ 远程服务器不可用: {client.base_url}")
        print("\n请确保:")
        print("1. 服务器已启动模型推理服务")
        print("2. 设置了正确的 REMOTE_MODEL_URL 环境变量")
        print("3. 网络连接正常")
        return
    
    print(f"✅ 远程服务器可用: {client.base_url}")
    
    # 获取模型信息
    print("\n获取模型信息...")
    info = client.get_model_info()
    print("模型信息:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # 测试推理
    print("\n测试推理...")
    messages = [
        {"role": "user", "content": "你好，请介绍一下自己"}
    ]
    
    try:
        # 使用较小的 max_tokens 避免量化模型崩溃
        response = client.chat(messages, max_tokens=50)
        print(f"\n模型响应:\n{response}")
        print("\n✅ 远程模型测试成功！")
        print("\n💡 提示: 量化模型建议使用 max_tokens=50-100，避免长文本生成崩溃")
    except Exception as e:
        print(f"\n❌ 推理失败: {e}")


if __name__ == "__main__":
    test_remote_model()
