"""
流式AI对话API - 支持Server-Sent Events (SSE)
实现类似千问、豆包的实时思考过程和内容流式输出
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import asyncio
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    stream: bool = True
    session_id: str = None


class StreamChunk(BaseModel):
    """流式数据块"""
    type: str  # 'thinking' | 'content' | 'done'
    content: str = ""
    metadata: dict = {}


async def stream_chat_response(message: str) -> AsyncGenerator[str, None]:
    """
    流式生成聊天响应
    支持思考过程和内容分离输出
    """
    try:
        # 第一阶段：思考过程
        thinking_process = await generate_thinking_process(message)
        
        # 流式输出思考过程
        for thought in thinking_process:
            chunk = StreamChunk(
                type="thinking",
                content=thought
            )
            yield f"data: {json.dumps(chunk.model_dump())}\n\n"
            await asyncio.sleep(0.05)  # 模拟流式延迟

        # 第二阶段：生成实际内容
        content_stream = generate_response_content(message, thinking_process)
        
        async for content_chunk in content_stream:
            chunk = StreamChunk(
                type="content",
                content=content_chunk
            )
            yield f"data: {json.dumps(chunk.model_dump())}\n\n"
            await asyncio.sleep(0.02)  # 模拟流式延迟

        # 标记完成
        done_chunk = StreamChunk(type="done")
        yield f"data: {json.dumps(done_chunk.model_dump())}\n\n"

    except Exception as e:
        logger.error(f"Stream error: {e}")
        error_chunk = StreamChunk(
            type="error",
            content=str(e)
        )
        yield f"data: {json.dumps(error_chunk.model_dump())}\n\n"


async def generate_thinking_process(message: str) -> list:
    """
    生成AI的思考过程
    模拟思考步骤：理解问题 -> 分析 -> 规划 -> 准备回答
    """
    thinking_steps = [
        f"📖 理解问题: 用户问的是关于 '{message[:20]}...' 的内容\n",
        f"🔍 分析上下文: 检查相关知识库和历史对话\n",
        f"💡 生成思路: 准备多个可能的回答角度\n",
        f"✅ 验证逻辑: 确保回答的准确性和完整性\n",
    ]
    
    return thinking_steps


async def generate_response_content(message: str, thinking: list) -> AsyncGenerator[str, None]:
    """
    生成实际的回答内容
    这里可以集成真实的LLM调用
    """
    # 示例：模拟流式生成内容
    response_text = f"""根据您的问题 "{message}"，我的分析如下：

1. **问题理解**
   - 您询问的核心是关于流式输出的实现
   - 这涉及到前后端的协调

2. **解决方案**
   - 后端使用 Server-Sent Events (SSE) 协议
   - 前端使用 HarmonyOS Stream API 处理数据流
   - 支持思考过程和内容的分离显示

3. **技术要点**
   - 使用异步生成器实现流式响应
   - 前端通过 Readable/Writable 流处理数据
   - 实时更新UI显示进度

4. **最佳实践**
   - 合理控制流式延迟，提升用户体验
   - 实现错误处理和超时机制
   - 支持流式中断和恢复

希望这个解决方案对您有帮助！"""

    # 按字符流式输出
    words = response_text.split()
    for word in words:
        yield word + " "
        await asyncio.sleep(0.01)  # 控制输出速度


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    流式聊天端点
    返回 Server-Sent Events 格式的数据流
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    return StreamingResponse(
        stream_chat_response(request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    非流式聊天端点（备选）
    一次性返回完整响应
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # 收集所有流式数据
    full_thinking = ""
    full_content = ""

    async for chunk_str in stream_chat_response(request.message):
        if chunk_str.startswith("data: "):
            try:
                chunk_data = json.loads(chunk_str[6:])
                if chunk_data["type"] == "thinking":
                    full_thinking += chunk_data["content"]
                elif chunk_data["type"] == "content":
                    full_content += chunk_data["content"]
            except json.JSONDecodeError:
                pass

    return {
        "message": request.message,
        "thinking": full_thinking,
        "content": full_content,
        "timestamp": asyncio.get_event_loop().time()
    }


@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "ok",
        "service": "streaming-chat-api",
        "version": "1.0.0"
    }

