"""
远程模型推理服务器
在服务器上运行，提供 HTTP API 供本地调用
"""
import os
import sys
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 请求/响应模型 ====================

class ChatMessage(BaseModel):
    """聊天消息"""
    role: str
    content: str


class ChatRequest(BaseModel):
    """聊天请求"""
    messages: List[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 2000


class ChatResponse(BaseModel):
    """聊天响应"""
    content: str
    model: str
    inference_time: float


class ModelInfo(BaseModel):
    """模型信息"""
    model_name: str
    model_path: str
    device: str
    is_loaded: bool
    inference_mode: str
    parameters: Optional[str] = None
    memory_usage: Optional[str] = None


# ==================== FastAPI 应用 ====================

app = FastAPI(
    title="远程模型推理服务",
    description="提供量化模型推理 API",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局模型服务
model_service = None


# ==================== API 端点 ====================

@app.on_event("startup")
async def startup_event():
    """启动时加载模型"""
    global model_service
    
    logger.info("=" * 60)
    logger.info("远程模型推理服务启动中...")
    logger.info("=" * 60)
    
    try:
        from backend.llm.local_quantized_model import LocalQuantizedModelService
        
        # 从环境变量或命令行参数获取模型路径
        model_path = os.environ.get("LOCAL_QUANTIZED_MODEL_PATH")
        
        if not model_path:
            logger.warning("未设置 LOCAL_QUANTIZED_MODEL_PATH 环境变量")
            logger.info("使用默认路径查找模型...")
        
        model_service = LocalQuantizedModelService(model_path=model_path)
        
        # 加载模型
        logger.info("正在加载量化模型...")
        if model_service.load_model():
            logger.info("✅ 模型加载成功！")
            
            # 打印模型信息
            info = model_service.get_model_info()
            logger.info("\n模型信息:")
            for key, value in info.items():
                logger.info(f"  {key}: {value}")
        else:
            logger.error("❌ 模型加载失败")
            model_service = None
    
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        model_service = None
    
    logger.info("=" * 60)


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "远程模型推理服务",
        "version": "1.0.0",
        "status": "running" if model_service and model_service.is_loaded else "model_not_loaded"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    if model_service is None:
        raise HTTPException(status_code=503, detail="模型服务未初始化")
    
    if not model_service.is_loaded:
        raise HTTPException(status_code=503, detail="模型未加载")
    
    return {
        "status": "healthy",
        "model_loaded": True
    }


@app.get("/model/info", response_model=ModelInfo)
async def get_model_info():
    """获取模型信息"""
    if model_service is None:
        raise HTTPException(status_code=503, detail="模型服务未初始化")
    
    info = model_service.get_model_info()
    
    return ModelInfo(
        model_name="Qwen3-8B-4bit",
        model_path=info.get("model_path", ""),
        device=info.get("device", "cpu"),
        is_loaded=info.get("is_loaded", False),
        inference_mode=info.get("inference_mode", "未知"),
        parameters=info.get("parameters"),
        memory_usage=info.get("estimated_memory_gb") or info.get("gpu_memory_gb")
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """聊天接口"""
    if model_service is None:
        raise HTTPException(status_code=503, detail="模型服务未初始化")
    
    if not model_service.is_loaded:
        raise HTTPException(status_code=503, detail="模型未加载")
    
    try:
        import time
        start_time = time.time()
        
        # 转换消息格式
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        # 调用模型
        logger.info(f"收到推理请求，消息数: {len(messages)}")
        response_content = model_service.chat(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        inference_time = time.time() - start_time
        logger.info(f"推理完成，耗时: {inference_time:.3f}秒")
        
        return ChatResponse(
            content=response_content,
            model="Qwen3-8B-4bit",
            inference_time=inference_time
        )
    
    except Exception as e:
        logger.error(f"推理失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"推理失败: {str(e)}")


# ==================== 主函数 ====================

def main():
    """启动服务器"""
    import argparse
    
    parser = argparse.ArgumentParser(description="远程模型推理服务器")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    parser.add_argument("--port", type=int, default=8001, help="监听端口")
    parser.add_argument("--model-path", help="模型文件路径")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数")
    
    args = parser.parse_args()
    
    # 设置环境变量
    if args.model_path:
        os.environ["LOCAL_QUANTIZED_MODEL_PATH"] = args.model_path
    
    logger.info(f"启动服务器: {args.host}:{args.port}")
    logger.info(f"工作进程数: {args.workers}")
    
    if args.model_path:
        logger.info(f"模型路径: {args.model_path}")
    
    # 启动服务器
    uvicorn.run(
        "backend.llm.remote_model_server:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        log_level="info"
    )


if __name__ == "__main__":
    main()
