"""
流式聊天集成模块 - 集成到 FastAPI 主应用
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import asyncio
from typing import AsyncGenerator, Optional
import logging

from .stream_processor import StreamProcessor, StreamEvent, StreamBuffer, StreamMetrics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["streaming-chat"])


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    stream: bool = True
    enable_thinking: bool = True
    system_prompt: Optional[str] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    thinking: str
    content: str
    metadata: dict


# 全局流式处理器
stream_processor = StreamProcessor(model="qwen")
stream_buffers: dict = {}  # session_id -> StreamBuffer


async def generate_stream(
    message: str,
    enable_thinking: bool = True,
    system_prompt: Optional[str] = None,
    session_id: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    生成流式响应
    """
    metrics = StreamMetrics()
    metrics.start()

    buffer = StreamBuffer()
    if session_id:
        stream_buffers[session_id] = buffer

    try:
        async for event in stream_processor.process_stream(
            message=message,
            system_prompt=system_prompt,
            enable_thinking=enable_thinking
        ):
            # 记录指标
            metrics.add_event(event)
            buffer.add_event(event)

            # 转换为 SSE 格式
            yield event.to_sse_format()

            # 小延迟以改善流式体验
            await asyncio.sleep(0.01)

    except Exception as e:
        logger.error(f"Stream generation error: {e}")
        error_event = StreamEvent(
            type="error",
            content=str(e)
        )
        yield error_event.to_sse_format()

    finally:
        metrics.end()
        logger.info(f"Stream metrics: {metrics.get_metrics()}")


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    流式聊天端点
    返回 Server-Sent Events 格式的数据流
    
    使用示例:
    ```
    curl -X POST http://localhost:8000/api/chat/stream \
      -H "Content-Type: application/json" \
      -d '{"message": "你好", "stream": true}'
    ```
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    return StreamingResponse(
        generate_stream(
            message=request.message,
            enable_thinking=request.enable_thinking,
            system_prompt=request.system_prompt,
            session_id=request.session_id
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream; charset=utf-8",
        }
    )


@router.post("/chat")
async def chat_complete(request: ChatRequest) -> ChatResponse:
    """
    非流式聊天端点
    一次性返回完整响应
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    buffer = StreamBuffer()

    try:
        async for event in stream_processor.process_stream(
            message=request.message,
            system_prompt=request.system_prompt,
            enable_thinking=request.enable_thinking
        ):
            buffer.add_event(event)

        data = buffer.get_all()
        return ChatResponse(
            thinking=data["thinking"],
            content=data["content"],
            metadata={"events": len(data["metadata"])}
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session_data(session_id: str):
    """
    获取会话的缓冲数据
    """
    if session_id not in stream_buffers:
        raise HTTPException(status_code=404, detail="Session not found")

    buffer = stream_buffers[session_id]
    return buffer.get_all()


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """
    清空会话数据
    """
    if session_id in stream_buffers:
        del stream_buffers[session_id]
        return {"status": "cleared"}
    return {"status": "not found"}


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "service": "streaming-chat-api",
        "version": "1.0.0",
        "active_sessions": len(stream_buffers)
    }


@router.post("/test-stream")
async def test_stream():
    """
    测试流式端点
    用于前端测试
    """
    async def test_generator():
        test_events = [
            {"type": "thinking", "content": "🔍 分析问题..."},
            {"type": "thinking", "content": "📚 检索知识库..."},
            {"type": "content", "content": "这是一个"},
            {"type": "content", "content": "测试"},
            {"type": "content", "content": "流式"},
            {"type": "content", "content": "响应"},
            {"type": "done", "content": ""},
        ]

        for event_data in test_events:
            event = StreamEvent(
                type=event_data["type"],
                content=event_data["content"]
            )
            yield event.to_sse_format()
            await asyncio.sleep(0.2)

    return StreamingResponse(
        test_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

