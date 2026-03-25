"""
高级流式处理工具 - 支持真实LLM集成
集成 Qwen、GPT 等大模型的流式输出
"""

import asyncio
import json
import os
from typing import AsyncGenerator, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(_env_path)
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class StreamEventType(Enum):
    """流式事件类型"""
    THINKING = "thinking"
    CONTENT = "content"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    DONE = "done"


@dataclass
class StreamEvent:
    """流式事件数据结构"""
    type: StreamEventType
    content: str = ""
    metadata: Dict[str, Any] = None
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().timestamp()
        if self.metadata is None:
            self.metadata = {}

    def to_sse_format(self) -> str:
        """转换为 Server-Sent Events 格式"""
        data = {
            "type": self.type.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
        return f"data: {json.dumps(data)}\n\n"


class StreamProcessor:
    """流式处理器 - 处理LLM的流式输出"""

    def __init__(self, model: str = "qwen", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.thinking_enabled = True
        self.max_thinking_length = 8000

    async def process_stream(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        enable_thinking: bool = True
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        处理流式响应
        
        Args:
            message: 用户消息
            system_prompt: 系统提示词
            enable_thinking: 是否启用思考过程
        """
        try:
            # 第一阶段：生成思考过程
            if enable_thinking:
                async for event in self._generate_thinking(message, system_prompt):
                    yield event

            # 第二阶段：生成实际内容
            async for event in self._generate_content(message, system_prompt):
                yield event

            # 完成事件
            yield StreamEvent(type=StreamEventType.DONE)

        except Exception as e:
            logger.error(f"Stream processing error: {e}")
            yield StreamEvent(
                type=StreamEventType.ERROR,
                content=str(e)
            )

    async def _generate_thinking(
        self,
        message: str,
        system_prompt: Optional[str]
    ) -> AsyncGenerator[StreamEvent, None]:
        """生成思考过程"""
        
        # 这里可以集成真实的LLM思考过程
        # 示例：使用 Qwen 的思考模式
        
        thinking_prompts = [
            f"🔍 分析用户问题: '{message[:50]}...'",
            "📚 检索相关知识库信息",
            "💭 生成多个可能的回答方向",
            "🧠 评估回答的准确性和完整性",
            "✅ 确定最优的回答策略"
        ]

        for prompt in thinking_prompts:
            yield StreamEvent(
                type=StreamEventType.THINKING,
                content=prompt + "\n"
            )
            await asyncio.sleep(0.1)  # 模拟思考延迟

    async def _generate_content(
        self,
        message: str,
        system_prompt: Optional[str]
    ) -> AsyncGenerator[StreamEvent, None]:
        """生成实际内容"""
        
        # 这里集成真实的LLM调用
        # 示例使用 Qwen API
        
        if self.model == "qwen":
            async for event in self._stream_qwen(message, system_prompt):
                yield event
        else:
            # 默认实现
            async for event in self._stream_default(message):
                yield event

    async def _stream_qwen(
        self,
        message: str,
        system_prompt: Optional[str]
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        使用 Qwen API 的流式处理
        需要安装: pip install dashscope
        """
        try:
            from dashscope import Generation
        except ImportError:
            logger.warning("dashscope not installed, using default stream")
            async for event in self._stream_default(message):
                yield event
            return

        try:
            # 构建消息
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": message})

            # 调用 Qwen API
            response = Generation.call(
                model="qwen-max",
                messages=messages,
                stream=True,
                api_key=self.api_key,
                top_p=0.8,
                temperature=0.7
            )

            # 处理流式响应
            for chunk in response:
                if chunk.status_code == 200:
                    content = chunk.output.choices[0].message.content
                    if content:
                        yield StreamEvent(
                            type=StreamEventType.CONTENT,
                            content=content
                        )
                else:
                    logger.error(f"API error: {chunk.message}")
                    yield StreamEvent(
                        type=StreamEventType.ERROR,
                        content=chunk.message
                    )

        except Exception as e:
            logger.error(f"Qwen API error: {e}")
            yield StreamEvent(
                type=StreamEventType.ERROR,
                content=str(e)
            )

    async def _stream_default(
        self,
        message: str
    ) -> AsyncGenerator[StreamEvent, None]:
        """默认流式处理实现"""
        
        response_template = f"""感谢您的问题: "{message}"

我的分析如下:

**1. 问题理解**
- 您询问的是关于流式输出的实现方案
- 这涉及前后端的协调和优化

**2. 核心技术**
- Server-Sent Events (SSE) 协议
- HarmonyOS Stream API
- 异步生成器模式

**3. 实现步骤**
- 后端使用 FastAPI 和异步生成器
- 前端使用 Readable/Writable 流处理
- 实时更新 UI 显示进度

**4. 性能优化**
- 合理控制流式延迟
- 实现缓冲区管理
- 支持流式中断和恢复

**5. 最佳实践**
- 错误处理和重试机制
- 超时控制
- 用户体验优化

希望这个方案对您有帮助！"""

        # 按单词流式输出
        words = response_template.split()
        buffer = ""
        
        for word in words:
            buffer += word + " "
            
            # 每5个单词输出一次
            if len(buffer.split()) >= 5:
                yield StreamEvent(
                    type=StreamEventType.CONTENT,
                    content=buffer
                )
                buffer = ""
                await asyncio.sleep(0.05)

        # 输出剩余内容
        if buffer:
            yield StreamEvent(
                type=StreamEventType.CONTENT,
                content=buffer
            )


class StreamBuffer:
    """流式缓冲区 - 用于处理和缓存流式数据"""

    def __init__(self, max_size: int = 1024 * 1024):
        self.max_size = max_size
        self.buffer: Dict[str, list] = {
            "thinking": [],
            "content": [],
            "metadata": []
        }
        self.total_size = 0

    def add_event(self, event: StreamEvent) -> bool:
        """添加事件到缓冲区"""
        event_size = len(event.content.encode('utf-8'))
        
        if self.total_size + event_size > self.max_size:
            logger.warning("Buffer overflow, dropping oldest events")
            self._drop_oldest()

        if event.type == StreamEventType.THINKING:
            self.buffer["thinking"].append(event.content)
        elif event.type == StreamEventType.CONTENT:
            self.buffer["content"].append(event.content)

        self.buffer["metadata"].append({
            "type": event.type.value,
            "timestamp": event.timestamp
        })

        self.total_size += event_size
        return True

    def get_thinking(self) -> str:
        """获取完整的思考过程"""
        return "".join(self.buffer["thinking"])

    def get_content(self) -> str:
        """获取完整的内容"""
        return "".join(self.buffer["content"])

    def get_all(self) -> Dict[str, Any]:
        """获取所有缓冲数据"""
        return {
            "thinking": self.get_thinking(),
            "content": self.get_content(),
            "metadata": self.buffer["metadata"],
            "total_size": self.total_size
        }

    def clear(self):
        """清空缓冲区"""
        self.buffer = {
            "thinking": [],
            "content": [],
            "metadata": []
        }
        self.total_size = 0

    def _drop_oldest(self):
        """删除最旧的事件"""
        if self.buffer["thinking"]:
            dropped = self.buffer["thinking"].pop(0)
            self.total_size -= len(dropped.encode('utf-8'))
        elif self.buffer["content"]:
            dropped = self.buffer["content"].pop(0)
            self.total_size -= len(dropped.encode('utf-8'))


class StreamMetrics:
    """流式指标收集"""

    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.events_count = 0
        self.total_bytes = 0
        self.thinking_time = 0
        self.content_time = 0

    def start(self):
        """开始计时"""
        self.start_time = datetime.now().timestamp()

    def end(self):
        """结束计时"""
        self.end_time = datetime.now().timestamp()

    def add_event(self, event: StreamEvent):
        """记录事件"""
        self.events_count += 1
        self.total_bytes += len(event.content.encode('utf-8'))

    def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        duration = 0
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time

        return {
            "duration": duration,
            "events_count": self.events_count,
            "total_bytes": self.total_bytes,
            "throughput": self.total_bytes / duration if duration > 0 else 0,
            "avg_event_size": self.total_bytes / self.events_count if self.events_count > 0 else 0
        }

