"""
LLM 提供者切换 API
支持在运行时动态切换 API 大模型和基座模型
"""
import os
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/llm", tags=["LLM管理"])


class LLMSwitchRequest(BaseModel):
    """LLM 切换请求"""
    provider: str  # qwen, remote_model, local_quantized, openai
    remote_url: Optional[str] = None  # 远程模型URL（可选）


class LLMStatusResponse(BaseModel):
    """LLM 状态响应"""
    current_provider: str
    available_providers: Dict[str, Dict[str, Any]]
    remote_model_url: Optional[str]


@router.get("/status", response_model=LLMStatusResponse)
async def get_llm_status():
    """
    获取当前 LLM 状态
    
    Returns:
        当前使用的提供者和所有可用提供者的状态
    """
    from backend.llm.llm_service import get_llm_service
    
    current_provider = os.getenv("LLM_PROVIDER", "qwen")
    remote_url = os.getenv("REMOTE_MODEL_URL", "http://localhost:8001")
    
    # 检查各个提供者的可用性
    available_providers = {}
    
    # 1. Qwen API
    qwen_key = os.getenv("DASHSCOPE_API_KEY")
    available_providers["qwen"] = {
        "name": "通义千问 API",
        "available": bool(qwen_key),
        "description": "云端 API，速度快，按量计费",
        "status": "已配置" if qwen_key else "未配置 API Key"
    }
    
    # 2. 本地量化模型（实际是远程GPU服务器）
    try:
        from backend.llm.remote_model_client import RemoteModelClient
        remote_client = RemoteModelClient(base_url=remote_url)
        available_providers["local_quantized"] = {
            "name": "本地量化模型",
            "available": remote_client.is_available,
            "description": "本地运行，离线可用，需要 GPU",
            "status": "已加载" if remote_client.is_available else "未加载",
            "url": remote_url
        }
        remote_client.close()
    except Exception as e:
        available_providers["local_quantized"] = {
            "name": "本地量化模型",
            "available": False,
            "description": "本地运行，离线可用，需要 GPU",
            "status": f"加载失败: {str(e)}",
            "url": remote_url
        }
    
    # 3. 远程基座模型（隐藏，不再使用）
    # 已合并到 local_quantized
    
    # 4. OpenAI API
    openai_key = os.getenv("OPENAI_API_KEY")
    available_providers["openai"] = {
        "name": "OpenAI API",
        "available": bool(openai_key) and openai_key != "your_openai_api_key_here",
        "description": "OpenAI 云端 API，需要国际网络",
        "status": "已配置" if (openai_key and openai_key != "your_openai_api_key_here") else "未配置 API Key"
    }
    
    return LLMStatusResponse(
        current_provider=current_provider,
        available_providers=available_providers,
        remote_model_url=remote_url
    )


@router.post("/switch")
async def switch_llm_provider(request: LLMSwitchRequest):
    """
    切换 LLM 提供者
    
    Args:
        request: 切换请求，包含目标提供者和可选的远程URL
    
    Returns:
        切换结果
    """
    valid_providers = ["qwen", "remote_model", "local_quantized", "openai"]
    
    if request.provider not in valid_providers:
        raise HTTPException(
            status_code=400,
            detail=f"无效的提供者: {request.provider}，有效值: {valid_providers}"
        )
    
    # 更新环境变量
    os.environ["LLM_PROVIDER"] = request.provider
    
    # 如果切换到远程模型且提供了新的URL，更新URL
    if request.provider == "remote_model" and request.remote_url:
        os.environ["REMOTE_MODEL_URL"] = request.remote_url
        logger.info(f"[LLM切换] 更新远程模型URL: {request.remote_url}")
    
    logger.info(f"[LLM切换] 切换到: {request.provider}")
    
    # 重新初始化 LLM 服务
    try:
        from backend.llm.llm_service import get_llm_service
        # 清除旧的单例
        import backend.llm.llm_service as llm_module
        llm_module._llm_service = None
        
        # 创建新的服务实例
        new_service = get_llm_service()
        
        if not new_service or not new_service.enabled:
            raise HTTPException(
                status_code=500,
                detail=f"切换失败: {request.provider} 不可用，请检查配置"
            )
        
        # 测试新服务
        test_messages = [{"role": "user", "content": "你好"}]
        response = new_service.chat(test_messages, temperature=0.7)
        
        return {
            "success": True,
            "provider": request.provider,
            "message": f"已切换到 {request.provider}",
            "test_response": response[:100] + "..." if len(response) > 100 else response
        }
    
    except Exception as e:
        logger.error(f"[LLM切换] 切换失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"切换失败: {str(e)}"
        )


@router.post("/test")
async def test_llm_provider(request: LLMSwitchRequest):
    """
    测试 LLM 提供者（不切换）
    
    Args:
        request: 测试请求
    
    Returns:
        测试结果
    """
    try:
        if request.provider == "qwen":
            from openai import OpenAI
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                raise ValueError("DASHSCOPE_API_KEY 未配置")
            
            client = OpenAI(
                api_key=api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            response = client.chat.completions.create(
                model="qwen-turbo",
                messages=[{"role": "user", "content": "你好"}],
                temperature=0.7
            )
            result = response.choices[0].message.content
        
        elif request.provider == "remote_model":
            from backend.llm.remote_model_client import RemoteModelClient
            url = request.remote_url or os.getenv("REMOTE_MODEL_URL", "http://localhost:8001")
            client = RemoteModelClient(base_url=url)
            
            if not client.is_available:
                raise ValueError(f"远程服务器不可用: {url}")
            
            result = client.chat([{"role": "user", "content": "你好"}])
            client.close()
        
        elif request.provider == "local_quantized":
            from backend.llm.local_quantized_model import get_local_model_service
            service = get_local_model_service()
            if not service:
                raise ValueError("本地量化模型未加载")
            
            result = service.chat([{"role": "user", "content": "你好"}])
        
        elif request.provider == "openai":
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key or api_key == "your_openai_api_key_here":
                raise ValueError("OPENAI_API_KEY 未配置")
            
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "你好"}],
                temperature=0.7
            )
            result = response.choices[0].message.content
        
        else:
            raise ValueError(f"未知的提供者: {request.provider}")
        
        return {
            "success": True,
            "provider": request.provider,
            "response": result[:200] + "..." if len(result) > 200 else result
        }
    
    except Exception as e:
        logger.error(f"[LLM测试] 测试失败: {e}")
        return {
            "success": False,
            "provider": request.provider,
            "error": str(e)
        }
