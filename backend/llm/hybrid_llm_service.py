"""
混合LLM服务 - 支持云端API和本地模型自动切换
"""
import time
import logging
from typing import List, Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class LLMBackend(Enum):
    """LLM后端类型"""
    CLOUD_API = "cloud_api"  # 云端API（通义千问等）
    LOCAL_QUANTIZED = "local_quantized"  # 本地量化模型


class HybridLLMService:
    """混合LLM服务 - 云端+本地双保险"""
    
    def __init__(self):
        self.cloud_service = None
        self.local_service = None
        self.current_backend = LLMBackend.CLOUD_API
        self.fallback_enabled = True
        
        # 统计信息
        self.stats = {
            "cloud_requests": 0,
            "local_requests": 0,
            "fallback_count": 0,
            "total_requests": 0,
        }
        
        logger.info("[混合LLM] 初始化混合LLM服务")
    
    def initialize(self):
        """初始化云端和本地服务"""
        # 初始化云端服务
        try:
            from backend.llm.llm_service import get_llm_service
            self.cloud_service = get_llm_service()
            if self.cloud_service and self.cloud_service.enabled:
                logger.info("[混合LLM] ✓ 云端API服务已就绪")
            else:
                logger.warning("[混合LLM] ✗ 云端API服务不可用")
        except Exception as e:
            logger.error(f"[混合LLM] 云端服务初始化失败: {e}")
        
        # 初始化本地服务
        try:
            from backend.llm.local_quantized_model import get_local_model_service
            self.local_service = get_local_model_service()
            logger.info("[混合LLM] ✓ 本地量化模型服务已就绪")
        except Exception as e:
            logger.error(f"[混合LLM] 本地服务初始化失败: {e}")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        force_backend: Optional[LLMBackend] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        对话接口 - 自动选择最佳后端
        
        Args:
            messages: 对话消息列表
            temperature: 温度参数
            max_tokens: 最大生成token数
            force_backend: 强制使用指定后端
        
        Returns:
            {
                "response": 生成的回复,
                "backend": 使用的后端,
                "inference_time": 推理时间,
                "fallback": 是否发生了降级
            }
        """
        self.stats["total_requests"] += 1
        start_time = time.time()
        fallback_occurred = False
        
        # 确定使用的后端
        if force_backend:
            backend = force_backend
        else:
            backend = self.current_backend
        
        # 尝试使用指定后端
        try:
            if backend == LLMBackend.CLOUD_API:
                response = self._call_cloud_api(messages, temperature, max_tokens, **kwargs)
                self.stats["cloud_requests"] += 1
                used_backend = LLMBackend.CLOUD_API
                
            elif backend == LLMBackend.LOCAL_QUANTIZED:
                response = self._call_local_model(messages, temperature, max_tokens, **kwargs)
                self.stats["local_requests"] += 1
                used_backend = LLMBackend.LOCAL_QUANTIZED
            
            else:
                raise ValueError(f"未知的后端类型: {backend}")
        
        except Exception as e:
            logger.error(f"[混合LLM] {backend.value}调用失败: {e}")
            
            # 如果启用了降级，尝试切换到备用后端
            if self.fallback_enabled:
                logger.warning(f"[混合LLM] 触发降级机制，切换后端...")
                fallback_occurred = True
                self.stats["fallback_count"] += 1
                
                try:
                    if backend == LLMBackend.CLOUD_API:
                        # 云端失败，切换到本地
                        logger.info("[混合LLM] 云端API失败，切换到本地量化模型")
                        response = self._call_local_model(messages, temperature, max_tokens, **kwargs)
                        used_backend = LLMBackend.LOCAL_QUANTIZED
                        self.stats["local_requests"] += 1
                        
                    else:
                        # 本地失败，切换到云端
                        logger.info("[混合LLM] 本地模型失败，切换到云端API")
                        response = self._call_cloud_api(messages, temperature, max_tokens, **kwargs)
                        used_backend = LLMBackend.CLOUD_API
                        self.stats["cloud_requests"] += 1
                
                except Exception as fallback_error:
                    logger.error(f"[混合LLM] 降级也失败: {fallback_error}")
                    raise RuntimeError("所有LLM后端均不可用")
            else:
                raise
        
        inference_time = time.time() - start_time
        
        return {
            "response": response,
            "backend": used_backend.value,
            "inference_time": inference_time,
            "fallback": fallback_occurred,
        }
    
    def _call_cloud_api(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> str:
        """调用云端API"""
        if not self.cloud_service or not self.cloud_service.enabled:
            raise RuntimeError("云端API服务不可用")
        
        logger.info("[混合LLM] 使用云端API")
        response = self.cloud_service.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return response
    
    def _call_local_model(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> str:
        """调用本地量化模型"""
        if not self.local_service:
            raise RuntimeError("本地模型服务不可用")
        
        logger.info("[混合LLM] 使用本地量化模型")
        
        # 如果模型未加载，先加载
        if not self.local_service.is_loaded:
            logger.info("[混合LLM] 本地模型未加载，开始加载...")
            if not self.local_service.load_model():
                raise RuntimeError("本地模型加载失败")
        
        response = self.local_service.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return response
    
    def switch_backend(self, backend: LLMBackend):
        """手动切换后端"""
        logger.info(f"[混合LLM] 切换后端: {self.current_backend.value} -> {backend.value}")
        self.current_backend = backend
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "current_backend": self.current_backend.value,
            "fallback_enabled": self.fallback_enabled,
            "cloud_available": self.cloud_service is not None and self.cloud_service.enabled,
            "local_available": self.local_service is not None,
            "local_loaded": self.local_service.is_loaded if self.local_service else False,
        }
    
    def demo_fallback(self):
        """演示降级切换（用于演示视频）"""
        logger.info("[混合LLM] ========== 开始演示降级切换 ==========")
        
        # 1. 正常使用云端API
        print("\n1️⃣ 正常情况：使用云端API")
        messages = [{"role": "user", "content": "你好"}]
        
        try:
            result = self.chat(messages, force_backend=LLMBackend.CLOUD_API)
            print(f"   ✓ 云端API响应成功")
            print(f"   后端: {result['backend']}")
            print(f"   耗时: {result['inference_time']:.3f}秒")
        except Exception as e:
            print(f"   ✗ 云端API失败: {e}")
        
        # 2. 模拟云端API崩溃
        print("\n2️⃣ 异常情况：云端API崩溃")
        print("   [模拟] 断开网络连接...")
        
        # 临时禁用云端服务
        original_cloud = self.cloud_service
        self.cloud_service = None
        
        # 3. 自动切换到本地模型
        print("\n3️⃣ 自动降级：切换到本地量化模型")
        try:
            result = self.chat(messages, force_backend=LLMBackend.CLOUD_API)
            print(f"   ✓ 本地模型响应成功（无感切换）")
            print(f"   后端: {result['backend']}")
            print(f"   耗时: {result['inference_time']:.3f}秒")
            print(f"   降级: {result['fallback']}")
        except Exception as e:
            print(f"   ✗ 降级失败: {e}")
        
        # 恢复云端服务
        self.cloud_service = original_cloud
        
        # 4. 打印统计信息
        print("\n4️⃣ 统计信息:")
        stats = self.get_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        logger.info("[混合LLM] ========== 演示结束 ==========")


# 全局单例
_hybrid_llm_service: Optional[HybridLLMService] = None


def get_hybrid_llm_service() -> HybridLLMService:
    """获取混合LLM服务单例"""
    global _hybrid_llm_service
    
    if _hybrid_llm_service is None:
        _hybrid_llm_service = HybridLLMService()
        _hybrid_llm_service.initialize()
    
    return _hybrid_llm_service


if __name__ == "__main__":
    # 测试混合LLM服务
    service = get_hybrid_llm_service()
    service.demo_fallback()
