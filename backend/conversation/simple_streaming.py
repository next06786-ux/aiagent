"""
简化版流式聊天 - 直接可用
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import asyncio
from typing import AsyncGenerator, Optional
from datetime import datetime

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    user_id: str = "default_user"  # 用户ID
    message: str
    stream: bool = True
    enable_thinking: bool = True


async def stream_response(message: str, enable_thinking: bool = True) -> AsyncGenerator[str, None]:
    """生成流式响应"""
    
    # 思考过程
    if enable_thinking:
        thinking_steps = [
            "🔍 分析问题内容",
            "📚 检索相关知识",
            "💡 生成回答方案",
            "✅ 验证答案准确性"
        ]
        
        for step in thinking_steps:
            event = {
                "type": "thinking",
                "content": step + "\n"
            }
            yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(0.1)
    
    # 实际内容
    response_text = f"""根据您的问题："{message}"

我的分析如下：

**1. 问题理解**
您询问的是关于流式输出的实现方案。

**2. 核心技术**
- Server-Sent Events (SSE) 协议
- HarmonyOS Stream API
- FastAPI 异步生成器

**3. 实现步骤**
- 后端使用异步生成器流式输出
- 前端通过 HTTP 请求接收 SSE 数据
- 实时解析并更新 UI

**4. 性能优化**
- 合理控制流式延迟
- 实现缓冲区管理
- 支持流式中断

希望这个解决方案对您有帮助！"""
    
    words = response_text.split()
    for word in words:
        event = {
            "type": "content",
            "content": word + " "
        }
        yield f"data: {json.dumps(event)}\n\n"
        await asyncio.sleep(0.02)
    
    # 完成事件
    event = {"type": "done", "content": ""}
    yield f"data: {json.dumps(event)}\n\n"


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """流式聊天端点"""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # 【新增】提交消息到后台处理队列（异步提取信息并存储到Neo4j+RAG）
    try:
        from backend.conversation.message_processor import get_message_processor
        
        processor = get_message_processor()
        
        # 生成会话ID（如果没有）
        session_id = f"session_{request.user_id}_{datetime.now().strftime('%Y%m%d')}"
        
        # 异步提交到后台处理（不阻塞响应）
        asyncio.create_task(processor.submit_message(
            user_id=request.user_id,
            message=request.message,
            session_id=session_id,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "message_type": "user_query"
            }
        ))
        
        print(f"✅ [消息处理] 用户 {request.user_id} 的消息已提交到后台处理队列")
        
    except Exception as e:
        print(f"⚠️ [消息处理] 提交消息失败: {e}")
    
    # 生成响应（后续会存储AI回复）
    async def stream_with_memory():
        """流式响应"""
        async for chunk in stream_response(request.message, request.enable_thinking):
            yield chunk
    
    return StreamingResponse(
        stream_with_memory(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/chat")
async def chat_complete(request: ChatRequest):
    """完整聊天端点"""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # 【新增】提交消息到后台处理队列（异步提取信息并存储到Neo4j+RAG）
    try:
        from backend.conversation.message_processor import get_message_processor
        
        processor = get_message_processor()
        
        # 生成会话ID（如果没有）
        session_id = f"session_{request.user_id}_{datetime.now().strftime('%Y%m%d')}"
        
        # 异步提交到后台处理（不阻塞响应）
        asyncio.create_task(processor.submit_message(
            user_id=request.user_id,
            message=request.message,
            session_id=session_id,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "message_type": "user_query"
            }
        ))
        
        print(f"✅ [消息处理] 用户 {request.user_id} 的消息已提交到后台处理队列")
        
    except Exception as e:
        print(f"⚠️ [消息处理] 提交消息失败: {e}")
    
    thinking = ""
    content = ""
    
    async for chunk_str in stream_response(request.message, request.enable_thinking):
        if chunk_str.startswith("data: "):
            try:
                chunk_data = json.loads(chunk_str[6:])
                if chunk_data["type"] == "thinking":
                    thinking += chunk_data["content"]
                elif chunk_data["type"] == "content":
                    content += chunk_data["content"]
            except:
                pass
    
    return {
        "thinking": thinking,
        "content": content
    }


@router.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "service": "streaming-chat"}

