"""
Agent框架 - Workflow + Agent + MCP 混合架构
Hybrid Architecture: Workflow + Agent + MCP

整合：
1. 四模块架构（LLM + 记忆 + 工具 + ReAct）
2. Workflow引擎（确定性任务流程）
3. Agent决策点（不确定性推理）
4. MCP协议（动态工具发现）

设计理念：
- 简单任务 → 纯Workflow（快速响应）
- 复杂任务 → Workflow + Agent（结构化 + 灵活性）
- 开放问题 → 纯Agent（完全自主）
- 工具调用 → MCP动态发现和管理
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod
from enum import Enum
import json
import asyncio

# LangChain核心导入
try:
    # 尝试新版API
    from langchain_core.language_models import BaseLLM
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.callbacks import CallbackManagerForLLMRun
    from langchain_core.callbacks.base import BaseCallbackHandler
    from langchain_core.tools import Tool
    from langchain_core.prompts import PromptTemplate
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
    from langchain_core.outputs import LLMResult
    
    # 简化实现：不使用AgentExecutor，直接用LLM
    LANGCHAIN_VERSION = "new"
except ImportError:
    # 回退到旧版API
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain.tools import Tool, BaseTool
    from langchain.prompts import PromptTemplate
    from langchain_core.language_models import BaseLLM
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.callbacks import CallbackManagerForLLMRun
    from langchain_core.callbacks.base import BaseCallbackHandler
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
    from langchain_core.outputs import LLMResult
    from langchain.memory import ConversationBufferMemory
    LANGCHAIN_VERSION = "old"

# MCP导入
from backend.agents.mcp_integration import MCPHost, MCPTool, ParallelFunctionCaller


# ==================== 工具调用回调处理器 ====================

class ToolCallbackHandler(BaseCallbackHandler):
    """工具调用回调处理器 - 实时捕获工具调用状态"""
    
    def __init__(self, websocket_callback=None):
        """
        初始化回调处理器
        
        Args:
            websocket_callback: WebSocket发送函数，格式为 callback(event_type, data)
                              可以是同步或异步函数
        """
        super().__init__()
        self.websocket_callback = websocket_callback
        self.current_tool_call = None
    
    def _send_callback(self, event_type: str, data: dict):
        """发送回调（支持同步和异步）"""
        if not self.websocket_callback:
            return
        
        try:
            # 直接调用回调（现在是同步包装器）
            self.websocket_callback(event_type, data)
        except Exception as e:
            print(f"⚠️  回调发送失败: {e}")
    
    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any
    ) -> None:
        """工具开始执行时调用"""
        tool_name = serialized.get("name", "unknown_tool")
        print(f"   🔧 工具开始: {tool_name}")
        
        # 发送 running 状态
        self._send_callback("tool_call", {
            "tool_name": tool_name,
            "status": "running",
            "input": input_str,
            "timestamp": datetime.now().isoformat()
        })
        
        self.current_tool_call = {
            "tool_name": tool_name,
            "input": input_str,
            "start_time": datetime.now()
        }
    
    def on_tool_end(
        self,
        output: str,
        **kwargs: Any
    ) -> None:
        """工具执行完成时调用"""
        if self.current_tool_call:
            tool_name = self.current_tool_call["tool_name"]
            duration = (datetime.now() - self.current_tool_call["start_time"]).total_seconds()
            print(f"   ✅ 工具完成: {tool_name} (耗时: {duration:.2f}s)")
            
            # 转换输出为字符串并限制长度
            output_str = str(output) if output else ""
            output_preview = output_str[:500] if len(output_str) > 500 else output_str
            
            # 发送 completed 状态
            self._send_callback("tool_call", {
                "tool_name": tool_name,
                "status": "completed",
                "output": output_preview,
                "duration": duration,
                "timestamp": datetime.now().isoformat()
            })
            
            self.current_tool_call = None
    
    def on_tool_error(
        self,
        error: Exception,
        **kwargs: Any
    ) -> None:
        """工具执行出错时调用"""
        if self.current_tool_call:
            tool_name = self.current_tool_call["tool_name"]
            print(f"   ❌ 工具错误: {tool_name} - {str(error)}")
            
            # 发送 error 状态
            self._send_callback("tool_call", {
                "tool_name": tool_name,
                "status": "error",
                "error": str(error),
                "timestamp": datetime.now().isoformat()
            })
            
            self.current_tool_call = None


# ==================== 数据结构定义 ====================

@dataclass
class AgentMessage:
    """Agent消息"""
    role: str  # user, assistant, system, tool
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class ReActStep:
    """ReAct步骤记录"""
    step_type: str  # thought, action, observation
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = None


# ==================== Workflow定义 ====================

class WorkflowNodeType(Enum):
    """工作流节点类型"""
    START = "start"
    MEMORY_LOAD = "memory_load"
    INTENT_CLASSIFY = "intent_classify"
    SIMPLE_RESPONSE = "simple_response"
    AGENT_DECISION = "agent_decision"
    MEMORY_SAVE = "memory_save"
    END = "end"


@dataclass
class WorkflowNode:
    """工作流节点"""
    node_id: str
    node_type: WorkflowNodeType
    description: str
    handler: Optional[Callable] = None
    next_nodes: Dict[str, str] = None
    
    def __post_init__(self):
        if self.next_nodes is None:
            self.next_nodes = {}


@dataclass
class WorkflowContext:
    """工作流上下文"""
    user_message: str
    user_id: str
    agent_type: str
    intent: Dict[str, Any] = None
    retrieved_memory: str = ""
    agent_response: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Workflow:
    """
    工作流引擎
    
    负责：
    1. 定义确定性的任务流程
    2. 编排节点执行顺序
    3. 在关键点调用Agent
    """
    
    def __init__(self, name: str):
        self.name = name
        self.nodes: Dict[str, WorkflowNode] = {}
        self.start_node_id: Optional[str] = None
    
    def add_node(self, node: WorkflowNode):
        """添加节点"""
        self.nodes[node.node_id] = node
        if node.node_type == WorkflowNodeType.START:
            self.start_node_id = node.node_id
    
    def execute(self, context: WorkflowContext) -> WorkflowContext:
        """执行工作流"""
        if not self.start_node_id:
            raise ValueError("工作流没有开始节点")
        
        current_node_id = self.start_node_id
        execution_path = []
        
        print(f"\n{'='*60}")
        print(f"[Workflow] 开始执行: {self.name}")
        print(f"{'='*60}\n")
        
        while current_node_id:
            node = self.nodes.get(current_node_id)
            if not node:
                raise ValueError(f"节点不存在: {current_node_id}")
            
            execution_path.append(node.node_id)
            print(f"📍 节点: {node.node_id} ({node.node_type.value})")
            print(f"   {node.description}")
            
            # 执行节点处理器
            if node.handler:
                result = node.handler(context)
            else:
                result = "default"
            
            # 结束节点
            if node.node_type == WorkflowNodeType.END:
                break
            
            # 确定下一个节点
            if result in node.next_nodes:
                current_node_id = node.next_nodes[result]
            elif "default" in node.next_nodes:
                current_node_id = node.next_nodes["default"]
            else:
                break
            
            print()
        
        context.metadata['execution_path'] = execution_path
        context.metadata['workflow_name'] = self.name
        
        print(f"{'='*60}")
        print(f"[Workflow] 完成")
        print(f"路径: {' → '.join(execution_path)}")
        print(f"{'='*60}\n")
        
        return context


# ==================== 自定义LLM包装器 ====================

class DashScopeLLM(BaseChatModel):
    """
    DashScope LLM包装器，适配LangChain Chat Model接口
    """
    llm_service: Any = None
    model: str = "qwen-turbo"
    temperature: float = 0.7
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, llm_service, model: str = "qwen-turbo", temperature: float = 0.7, **kwargs):
        # 使用Pydantic v2的方式初始化
        super().__init__(
            llm_service=llm_service,
            model=model,
            temperature=temperature,
            **kwargs
        )
    
    @property
    def _llm_type(self) -> str:
        return "dashscope"
    
    def bind_tools(self, tools: List[Any], **kwargs: Any) -> "DashScopeLLM":
        """
        绑定工具（LangGraph需要）
        
        创建一个新实例，包含绑定的工具信息
        """
        # 创建新实例并复制工具信息
        bound = self.__class__(
            llm_service=self.llm_service,
            model=self.model,
            temperature=self.temperature
        )
        # 存储工具信息
        bound._bound_tools = tools
        return bound
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Any:
        """生成响应（Chat Model接口）- 支持工具调用"""
        from langchain_core.outputs import ChatResult, ChatGeneration
        from langchain_core.messages.tool import ToolCall
        import json
        
        try:
            # 转换消息格式
            api_messages = []
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    api_messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    # 处理包含工具调用的AI消息
                    msg_dict = {"role": "assistant", "content": msg.content or ""}
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        # 添加工具调用信息
                        msg_dict["tool_calls"] = [
                            {
                                "id": tc.get("id", ""),
                                "type": "function",
                                "function": {
                                    "name": tc.get("name", ""),
                                    "arguments": json.dumps(tc.get("args", {}))
                                }
                            }
                            for tc in msg.tool_calls
                        ]
                    api_messages.append(msg_dict)
                elif isinstance(msg, SystemMessage):
                    api_messages.append({"role": "system", "content": msg.content})
                elif hasattr(msg, 'type') and msg.type == 'tool':
                    # 工具执行结果消息 - 转换为用户消息（通义千问兼容）
                    tool_name = getattr(msg, 'name', 'unknown_tool')
                    api_messages.append({
                        "role": "user",
                        "content": f"[工具 {tool_name} 返回结果]\n{msg.content}"
                    })
                else:
                    # 其他类型消息转为用户消息
                    api_messages.append({"role": "user", "content": str(msg.content)})
            
            # 准备工具定义（优先使用绑定的工具，否则使用kwargs中的tools）
            tools = getattr(self, '_bound_tools', None) or kwargs.get('tools')
            tool_choice = kwargs.get('tool_choice', 'auto')
            
            # 转换LangChain工具格式为OpenAI格式
            api_tools = None
            if tools:
                api_tools = []
                for tool in tools:
                    if hasattr(tool, 'name') and hasattr(tool, 'description'):
                        # LangChain Tool对象
                        # 安全获取参数schema
                        parameters = {}
                        if hasattr(tool, 'args_schema') and tool.args_schema is not None:
                            try:
                                parameters = tool.args_schema.schema()
                            except Exception as e:
                                print(f"⚠️  工具 {tool.name} 的schema获取失败: {e}")
                                parameters = {"type": "object", "properties": {}}
                        else:
                            parameters = {"type": "object", "properties": {}}
                        
                        tool_def = {
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description,
                                "parameters": parameters
                            }
                        }
                        api_tools.append(tool_def)
                    elif isinstance(tool, dict):
                        # 已经是字典格式
                        api_tools.append(tool)
            
            # 调用LLM（传递工具定义）
            response_text = self.llm_service.chat(
                messages=api_messages,
                temperature=self.temperature,
                model=self.model,
                tools=api_tools,
                tool_choice=tool_choice
            )
            
            # 检查是否返回了工具调用JSON
            if response_text.startswith('{') and '"tool_calls"' in response_text:
                try:
                    response_data = json.loads(response_text)
                    tool_calls_data = response_data.get('tool_calls', [])
                    content = response_data.get('content', '')
                    
                    # 构建包含工具调用的AIMessage
                    tool_calls = []
                    for tc in tool_calls_data:
                        tool_calls.append(ToolCall(
                            name=tc['function']['name'],
                            args=json.loads(tc['function']['arguments']),
                            id=tc.get('id', f"call_{tc['function']['name']}")
                        ))
                    
                    message = AIMessage(
                        content=content or "",
                        tool_calls=tool_calls
                    )
                except json.JSONDecodeError:
                    # JSON解析失败，当作普通文本
                    message = AIMessage(content=response_text)
            else:
                # 普通文本响应
                message = AIMessage(content=response_text)
            
            generation = ChatGeneration(message=message)
            return ChatResult(generations=[generation])
            
        except Exception as e:
            print(f"❌ LLM调用失败: {e}")
            import traceback
            traceback.print_exc()
            error_message = AIMessage(content=f"Error: {str(e)}")
            return ChatResult(generations=[ChatGeneration(message=error_message)])
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """调用LLM（旧版API兼容）"""
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.llm_service.chat(
                messages=messages,
                temperature=self.temperature,
                model=self.model
            )
            return response
        except Exception as e:
            print(f"❌ LLM调用失败: {e}")
            return f"Error: {str(e)}"



# ==================== 1. LLM模块 ====================

class LLMModule:
    """
    LLM模块 - 负责意图理解和推理判断
    """
    
    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.langchain_llm = DashScopeLLM(llm_service)
    
    def understand_intent(self, user_message: str, context: List[AgentMessage]) -> Dict[str, Any]:
        """理解用户意图"""
        system_prompt = """你是一个意图理解和复杂度评估专家。分析用户消息，识别意图类型、关键实体和任务复杂度。

【复杂度判断标准】

**simple（简单）** - 满足以下任一条件：
1. 简单问候或闲聊（"你好"、"在吗"、"谢谢"）
2. 简单确认或澄清（"是的"、"对"、"不是"）
3. 无需推理的直接回答
4. 不需要调用工具或检索记忆

**medium（中等）** - 满足以下任一条件：
1. 需要联网搜索最新信息（"搜索..."、"查一下..."、"最新..."）
2. 需要调用专属工具（分析、评估、推荐、计算等）
3. 单一事实查询（"什么是..."、"谁是..."、"哪里..."）
4. 需要一定分析但不复杂（"如何..."、"为什么..."）
5. 需要检索用户历史信息
6. 需要简单的建议或推荐
7. 涉及1-2个维度的问题

**complex（复杂）** - 满足以下任一条件：
1. 需要深度分析和推理（"帮我规划..."、"如何解决..."）
2. 涉及多个维度或多步骤（"比较...并给出建议"）
3. 需要制定计划或策略
4. 需要调用多个工具或多次推理
5. 开放性问题需要创造性回答
6. 涉及复杂的人际关系/职业规划/教育路径

【示例】
- "你好" → simple
- "搜索职场沟通技巧" → medium（需要联网搜索）
- "帮我分析沟通模式" → medium（需要调用工具）
- "什么是职业规划" → medium
- "我应该考研还是工作" → medium
- "帮我分析我的职业发展路径，考虑我的背景和市场趋势" → complex
- "如何改善和同事的关系" → medium
- "我和朋友、家人、同事的关系都有问题，帮我全面分析并制定改善计划" → complex

返回JSON格式：
{
  "intent": "查询信息/寻求建议/制定计划/解决问题/闲聊/其他",
  "entities": {"主题": "...", "时间范围": "...", "具体对象": "..."},
  "complexity": "simple/medium/complex",
  "requires_tools": false,
  "reasoning": "复杂度判断理由"
}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"用户消息：{user_message}"}
        ]
        
        try:
            response = self.llm_service.chat(
                messages=messages,
                temperature=0.3,
                response_format="json_object",
                model="qwen-turbo"
            )
            result = json.loads(response)
            
            # 打印判断理由（调试用）
            if result.get('reasoning'):
                print(f"   复杂度判断: {result.get('reasoning')}")
            
            return result
        except Exception as e:
            print(f"❌ 意图理解失败: {e}")
            # 默认返回medium，避免简单任务被误判为complex
            return {
                'intent': '其他',
                'entities': {},
                'complexity': 'medium',
                'requires_tools': False,
                'reasoning': '意图理解失败，默认中等复杂度'
            }



# ==================== 2. 记忆模块 ====================

class MemoryModule:
    """
    记忆模块 - 上下文窗口 + 外部记忆
    
    两层架构：
    1. 上下文窗口（Context Window）：128K tokens，速度最快
       - 当前对话、任务状态、工具调用历史、检索结果
    2. 外部记忆（External Memory）：
       - FAISS：语义检索
       - MySQL：结构化数据
       - Neo4j：知识图谱
       - Redis：热点缓存
    """
    
    def __init__(self, user_id: str, rag_system, retrieval_system, websocket_callback=None):
        self.user_id = user_id
        self.rag_system = rag_system
        self.retrieval_system = retrieval_system
        self.websocket_callback = websocket_callback
        
        # 上下文窗口（短期记忆）
        self.context_window: List[AgentMessage] = []
        self.max_context_tokens = 128000  # 128K tokens
        self.compression_threshold = 0.8  # 80%触发压缩
        
        # 工作记忆（任务执行中的临时信息）
        self.working_memory: Dict[str, Any] = {
            'task_status': {},
            'tool_calls': [],
            'retrieved_facts': [],
            'user_preferences': {}
        }
    
    def add_to_context_window(self, message: AgentMessage):
        """添加到上下文窗口"""
        self.context_window.append(message)
        
        # 检查是否需要压缩
        if self._should_compress():
            print("⚠️  上下文窗口接近容量限制，触发摘要压缩")
            self._compress_context_window()
    
    def _should_compress(self) -> bool:
        """检查是否需要压缩上下文窗口"""
        # 简化实现：基于消息数量（实际应该计算tokens）
        current_messages = len(self.context_window)
        # 假设每条消息平均500 tokens
        estimated_tokens = current_messages * 500
        return estimated_tokens > (self.max_context_tokens * self.compression_threshold)
    
    def _compress_context_window(self):
        """
        压缩上下文窗口
        
        策略：
        1. 保留最近3轮完整对话
        2. 旧对话用LLM总结成摘要
        3. 原始对话保存到外部记忆
        """
        if len(self.context_window) <= 6:  # 3轮对话
            return
        
        # 保留最近3轮（6条消息）
        recent_messages = self.context_window[-6:]
        old_messages = self.context_window[:-6]
        
        # 将旧消息保存到外部记忆
        for msg in old_messages:
            self._save_to_external_memory(msg)
        
        # TODO: 用LLM生成摘要（简化实现，直接截断）
        summary = AgentMessage(
            role='system',
            content=f'[摘要] 之前的{len(old_messages)}条对话已压缩保存',
            timestamp=datetime.now(),
            metadata={'compressed': True, 'original_count': len(old_messages)}
        )
        
        # 更新上下文窗口
        self.context_window = [summary] + recent_messages
        print(f"✅ 上下文窗口已压缩：{len(old_messages)}条 → 1条摘要")
    
    def _save_to_external_memory(self, message: AgentMessage):
        """保存到外部记忆"""
        try:
            # 保存到RAG系统（向量数据库）
            from backend.learning.production_rag_system import MemoryType
            
            self.rag_system.add_memory(
                memory_type=MemoryType.CONVERSATION,
                content=message.content,
                metadata={
                    'role': message.role,
                    'timestamp': message.timestamp.isoformat(),
                    **message.metadata
                },
                importance=0.5
            )
        except Exception as e:
            print(f"⚠️  保存到外部记忆失败: {e}")
    
    def get_context_window(self, max_messages: int = 10) -> List[AgentMessage]:
        """获取上下文窗口内容"""
        return self.context_window[-max_messages:]
    
    def retrieve_from_external_memory(
        self,
        query: str,
        agent_type: str,
        max_results: int = 5,
        reason: str = "general"
    ) -> str:
        """
        从外部记忆检索（读取时机）
        
        Args:
            query: 查询文本
            agent_type: Agent类型
            max_results: 最大结果数
            reason: 检索原因（'task_start', 'unknown_problem', 'fact_check'）
        
        读取时机：
        1. task_start: 任务开始时加载用户偏好和历史背景
        2. unknown_problem: 遇到陌生问题时检索相关历史经验
        3. fact_check: 需要事实核查时检索已知信息
        """
        print(f"🔍 从外部记忆检索 (原因: {reason})")
        
        # 发送检索开始消息
        self._send_retrieval_callback("retrieval_start", {
            "query": query,
            "reason": reason,
            "agent_type": agent_type
        })
        
        try:
            from backend.learning.unified_hybrid_retrieval import RetrievalConfig, RetrievalStrategy
            
            config = RetrievalConfig(
                strategy=RetrievalStrategy.HYBRID_PARALLEL,
                max_results=max_results
            )
            
            # 根据Agent类型设置领域过滤
            domain_map = {
                'relationship': 'relationship',
                'education': 'education',
                'career': 'career'
            }
            config.domain_filter = domain_map.get(agent_type)
            
            # 执行检索
            retrieval_context = self.retrieval_system.retrieve(
                query=query,
                config=config
            )
            
            if retrieval_context and retrieval_context.results:
                context_parts = []
                for result in retrieval_context.results[:5]:
                    context_parts.append(f"- {result.content}")
                
                retrieved = "\n".join(context_parts)
                
                # 保存检索结果到工作记忆
                self.working_memory['retrieved_facts'].append({
                    'query': query,
                    'results': retrieved,
                    'reason': reason,
                    'timestamp': datetime.now().isoformat()
                })
                
                # 发送检索完成消息
                self._send_retrieval_callback("retrieval_complete", {
                    "query": query,
                    "reason": reason,
                    "results_count": len(retrieval_context.results),
                    "sources": [r.source for r in retrieval_context.results[:3]]  # 前3个来源
                })
                
                return retrieved
            
            # 没有结果
            self._send_retrieval_callback("retrieval_complete", {
                "query": query,
                "reason": reason,
                "results_count": 0,
                "sources": []
            })
            
            return ""
            
        except Exception as e:
            print(f"❌ 外部记忆检索失败: {e}")
            
            # 发送检索失败消息
            self._send_retrieval_callback("retrieval_error", {
                "query": query,
                "reason": reason,
                "error": str(e)
            })
            
            return ""
    
    def _send_retrieval_callback(self, event_type: str, data: dict):
        """发送检索回调消息"""
        if not self.websocket_callback:
            return
        
        try:
            # 直接调用回调（现在是同步包装器）
            self.websocket_callback("memory_retrieval", {
                "type": event_type,
                **data,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"⚠️  检索回调发送失败: {e}")
    
    def save_task_result(
        self,
        task_description: str,
        result: Any,
        success: bool,
        key_findings: List[str] = None
    ):
        """
        保存任务结果（写入时机1：任务完成后）
        
        Args:
            task_description: 任务描述
            result: 任务结果
            success: 是否成功
            key_findings: 关键发现
        """
        print(f"💾 保存任务结果 (成功: {success})")
        
        # 构建记忆内容
        content = f"任务: {task_description}\n"
        content += f"结果: {'成功' if success else '失败'}\n"
        
        if success and key_findings:
            content += f"关键发现:\n"
            for finding in key_findings:
                content += f"- {finding}\n"
        elif not success and result:
            content += f"失败原因: {result}\n"
        
        # 保存到外部记忆
        try:
            from backend.learning.production_rag_system import MemoryType
            
            self.rag_system.add_memory(
                memory_type=MemoryType.TASK_COMPLETION,
                content=content,
                metadata={
                    'task': task_description,
                    'success': success,
                    'timestamp': datetime.now().isoformat()
                },
                importance=0.8 if success else 0.9  # 失败经验更重要
            )
        except Exception as e:
            print(f"⚠️  保存任务结果失败: {e}")
    
    def save_user_preference(self, preference_type: str, value: Any):
        """
        保存用户偏好（写入时机2：用户提供个人信息时）
        
        Args:
            preference_type: 偏好类型（如'communication_style', 'goals'）
            value: 偏好值
        """
        print(f"💾 保存用户偏好: {preference_type}")
        
        # 更新工作记忆
        self.working_memory['user_preferences'][preference_type] = value
        
        # 保存到外部记忆
        content = f"用户偏好 - {preference_type}: {value}"
        try:
            from backend.learning.production_rag_system import MemoryType
            
            self.rag_system.add_memory(
                memory_type=MemoryType.USER_PREFERENCE,
                content=content,
                metadata={
                    'preference_type': preference_type,
                    'value': str(value),
                    'timestamp': datetime.now().isoformat()
                },
                importance=0.9  # 用户偏好很重要
            )
        except Exception as e:
            print(f"⚠️  保存用户偏好失败: {e}")
    
    def save_new_knowledge(self, knowledge: str, source: str):
        """
        保存新知识（写入时机3：发现新知识时）
        
        Args:
            knowledge: 新知识内容
            source: 知识来源
        """
        print(f"💾 保存新知识 (来源: {source})")
        
        try:
            from backend.learning.production_rag_system import MemoryType
            
            self.rag_system.add_memory(
                memory_type=MemoryType.KNOWLEDGE,
                content=knowledge,
                metadata={
                    'source': source,
                    'timestamp': datetime.now().isoformat()
                },
                importance=0.7
            )
        except Exception as e:
            print(f"⚠️  保存新知识失败: {e}")
    
    def save_error(self, error_context: str, error_message: str, solution: str = None):
        """
        保存错误信息（写入时机4：出错时）
        
        Args:
            error_context: 错误上下文
            error_message: 错误消息
            solution: 解决方案（如果有）
        """
        print(f"💾 保存错误记录: {error_message[:50]}...")
        
        content = f"错误上下文: {error_context}\n"
        content += f"错误信息: {error_message}\n"
        if solution:
            content += f"解决方案: {solution}\n"
        
        try:
            from backend.learning.production_rag_system import MemoryType
            
            self.rag_system.add_memory(
                memory_type=MemoryType.EXPERIENCE,
                content=content,
                metadata={
                    'error': error_message,
                    'context': error_context,
                    'timestamp': datetime.now().isoformat(),
                    'type': 'error'
                },
                importance=0.95  # 错误经验非常重要，避免重蹈覆辙
            )
        except Exception as e:
            print(f"⚠️  保存错误记录失败: {e}")
    
    def update_working_memory(self, key: str, value: Any):
        """更新工作记忆"""
        self.working_memory[key] = value
    
    def get_working_memory(self, key: str) -> Optional[Any]:
        """获取工作记忆"""
        return self.working_memory.get(key)
    
    def clear_working_memory(self):
        """清空工作记忆"""
        self.working_memory = {
            'task_status': {},
            'tool_calls': [],
            'retrieved_facts': [],
            'user_preferences': {}
        }



# ==================== 3. 工具模块（集成MCP） ====================

class ToolModule:
    """
    工具模块 - 集成MCP动态工具发现
    
    功能：
    1. 管理LangChain工具
    2. 集成MCP Host
    3. 动态发现MCP工具
    4. 工具调用统一接口
    """
    
    def __init__(
        self,
        memory_module: MemoryModule,
        agent_type: str,
        mcp_host: Optional[MCPHost] = None
    ):
        self.memory_module = memory_module
        self.agent_type = agent_type
        self.mcp_host = mcp_host
        self.tools: List[Tool] = []
        self.mcp_tools_discovered = False
        
        # 注册默认工具
        self._register_default_tools()
    
    async def discover_mcp_tools(self):
        """
        发现MCP工具（Agent启动时调用）
        
        将MCP工具转换为LangChain工具并注册
        """
        if not self.mcp_host or self.mcp_tools_discovered:
            return
        
        print(f"\n🔍 [ToolModule] 开始发现MCP工具")
        
        # 发现所有MCP工具
        await self.mcp_host.discover_tools()
        
        # 转换为LangChain工具
        mcp_tools = self.mcp_host.get_available_tools()
        for mcp_tool in mcp_tools:
            # 创建工具执行器
            def create_executor(tool_name: str):
                async def executor(params_str: str) -> str:
                    """MCP工具执行器"""
                    try:
                        # 解析参数（LangChain传入的是字符串）
                        if params_str:
                            try:
                                params = json.loads(params_str)
                            except:
                                # 如果不是JSON，当作单个参数
                                params = {"input": params_str}
                        else:
                            params = {}
                        
                        # 调用MCP工具
                        result = await self.mcp_host.call_tool(tool_name, params)
                        return json.dumps(result, ensure_ascii=False)
                    except Exception as e:
                        return f"工具调用失败: {str(e)}"
                
                # 包装为同步函数（LangChain需要）
                def sync_executor(params_str: str) -> str:
                    try:
                        # 尝试获取当前事件循环
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # 如果事件循环已运行，创建新任务
                            import nest_asyncio
                            nest_asyncio.apply()
                            return loop.run_until_complete(executor(params_str))
                    except RuntimeError:
                        # 没有事件循环，创建新的
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            return loop.run_until_complete(executor(params_str))
                        finally:
                            loop.close()
                    
                    return loop.run_until_complete(executor(params_str))
                
                return sync_executor
            
            # 转换为LangChain StructuredTool（支持多参数）
            from langchain_core.tools import StructuredTool
            from pydantic import BaseModel, Field, create_model
            from typing import Optional
            
            # 从MCP工具的parameters构建Pydantic模型
            fields = {}
            if mcp_tool.parameters and 'properties' in mcp_tool.parameters:
                for prop_name, prop_info in mcp_tool.parameters['properties'].items():
                    field_type = str  # 默认类型
                    if prop_info.get('type') == 'integer':
                        field_type = int
                    elif prop_info.get('type') == 'number':
                        field_type = float
                    elif prop_info.get('type') == 'boolean':
                        field_type = bool
                    
                    # 检查是否必需
                    is_required = prop_name in mcp_tool.parameters.get('required', [])
                    
                    # 获取默认值
                    default_value = prop_info.get('default')
                    
                    if is_required:
                        fields[prop_name] = (field_type, Field(description=prop_info.get('description', '')))
                    else:
                        # 对于可选字段，使用...作为默认值标记（Pydantic v2）
                        if default_value is not None:
                            fields[prop_name] = (field_type, Field(default=default_value, description=prop_info.get('description', '')))
                        else:
                            fields[prop_name] = (Optional[field_type], Field(default=None, description=prop_info.get('description', '')))
            
            # 创建动态Pydantic模型（确保至少有一个字段）
            if not fields:
                # 如果没有参数定义，创建一个空的schema
                fields = {'__dummy__': (Optional[str], Field(default=None, description='Placeholder'))}
            
            ArgsSchema = create_model(f"{mcp_tool.name}_args", **fields)
            
            # 创建同步包装函数（接受关键字参数）
            def create_sync_wrapper(tool_name: str):
                async def async_executor(**kwargs) -> str:
                    """MCP工具异步执行器"""
                    try:
                        # 调用MCP工具
                        result = await self.mcp_host.call_tool(tool_name, kwargs)
                        return json.dumps(result, ensure_ascii=False)
                    except Exception as e:
                        return f"工具调用失败: {str(e)}"
                
                def sync_wrapper(**kwargs) -> str:
                    """同步包装器"""
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            import nest_asyncio
                            nest_asyncio.apply()
                            return loop.run_until_complete(async_executor(**kwargs))
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            return loop.run_until_complete(async_executor(**kwargs))
                        finally:
                            loop.close()
                    
                    return loop.run_until_complete(async_executor(**kwargs))
                
                return sync_wrapper
            
            langchain_tool = StructuredTool(
                name=mcp_tool.name,
                description=f"{mcp_tool.description} (MCP工具，来自{mcp_tool.server_id})",
                func=create_sync_wrapper(mcp_tool.name),
                args_schema=ArgsSchema,
                coroutine=None  # 我们已经处理了异步
            )
            
            self.tools.append(langchain_tool)
            
            approval_mark = "🔒" if mcp_tool.requires_approval else "🔓"
            print(f"   {approval_mark} {mcp_tool.name}")
        
        self.mcp_tools_discovered = True
        print(f"✅ [ToolModule] MCP工具发现完成，共 {len(mcp_tools)} 个\n")
    
    def _register_default_tools(self):
        """注册默认工具"""
        # RAG混合检索工具（可多次调用）
        rag_tool = Tool(
            name="retrieve_user_data",
            description="""从用户的历史数据和知识库中检索相关信息（RAG混合检索）。
            
适用场景：
1. 需要了解用户的历史背景、偏好、经历时
2. 需要查找用户之前提到过的信息时
3. 需要基于用户的真实情况进行个性化分析时
4. 遇到需要用户具体数据支持的问题时

重要提示：
- 这个工具会从用户的对话历史、导入的数据、知识图谱中检索信息
- 检索到的信息应该融入到其他工具的参数中，实现个性化分析
- 可以多次调用，每次使用不同的查询关键词获取不同维度的信息

输入：查询文本（描述你想了解用户的什么信息）
输出：相关的用户背景信息""",
            func=self._retrieve_user_data_tool
        )
        self.tools.append(rag_tool)
        
        # 当前时间工具
        time_tool = Tool(
            name="get_current_time",
            description="获取当前时间和日期",
            func=self._get_current_time_tool
        )
        self.tools.append(time_tool)
        
        print(f"✅ 已注册 {len(self.tools)} 个默认工具")
    
    def register_custom_tool(
        self,
        name: str,
        description: str,
        func: Callable
    ):
        """注册自定义工具"""
        tool = Tool(
            name=name,
            description=description,
            func=func
        )
        self.tools.append(tool)
        print(f"✅ 工具已注册: {name}")
    
    def get_tools(self) -> List[Tool]:
        """获取所有工具（包括MCP工具）"""
        return self.tools
    
    # ===== 默认工具实现 =====
    
    def _retrieve_user_data_tool(self, query: str) -> str:
        """RAG混合检索工具（可多次调用）"""
        try:
            # 智能判断检索原因
            reason = "general"
            if "背景" in query or "历史" in query or "之前" in query or "以前" in query:
                reason = "task_start"
            elif "不知道" in query or "不了解" in query or "陌生" in query or "不清楚" in query:
                reason = "unknown_problem"
            elif "确认" in query or "核实" in query or "是否" in query or "验证" in query:
                reason = "fact_check"
            
            print(f"   🔍 RAG检索: {query} (原因: {reason})")
            
            context = self.memory_module.retrieve_from_external_memory(
                query,
                self.agent_type,
                max_results=5,
                reason=reason
            )
            if context:
                return f"检索到的用户相关信息：\n{context}\n\n提示：请将这些信息融入到后续工具调用的参数中，实现个性化分析。"
            else:
                return "未找到相关的用户信息。可能用户还没有提供相关背景，或者需要调整查询关键词。"
        except Exception as e:
            return f"检索失败: {str(e)}"
    
    def _get_current_time_tool(self, _: str = "") -> str:
        """获取当前时间工具"""
        now = datetime.now()
        return f"当前时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')}"


# ==================== 4. Workflow + Agent 混合架构 ====================

class LangChainReActAgent(ABC):
    """
    Workflow + Agent + MCP 混合架构
    
    工作模式：
    1. 简单任务：纯Workflow快速处理（无需Agent推理）
    2. 中等任务：Workflow + 少量Agent决策
    3. 复杂任务：Workflow编排 + 多次Agent介入
    4. 工具调用：MCP动态发现和管理
    
    优势：
    - 确定性任务用Workflow：快速、可预测、高效
    - 不确定性任务用Agent：灵活、自主决策
    - 工具动态发现：MCP协议，运行时扩展
    - 混合使用：结构化流程 + 智能决策
    """
    
    def __init__(
        self,
        agent_type: str,
        user_id: str,
        llm_service,
        rag_system,
        retrieval_system,
        use_workflow: bool = True,  # 是否启用Workflow混合模式
        mcp_host: Optional[MCPHost] = None,  # MCP Host（可选）
        websocket_callback: Optional[Callable] = None  # WebSocket回调函数
    ):
        self.agent_type = agent_type
        self.user_id = user_id
        self.use_workflow = use_workflow
        self.mcp_host = mcp_host
        self.websocket_callback = websocket_callback
        
        # 初始化工具回调处理器
        self.tool_callback_handler = ToolCallbackHandler(websocket_callback)
        
        # 初始化模块
        self.llm_module = LLMModule(llm_service)
        self.memory_module = MemoryModule(user_id, rag_system, retrieval_system, websocket_callback)
        self.tool_module = ToolModule(self.memory_module, agent_type, mcp_host)
        
        # 注册专属工具
        self._register_agent_tools()
        
        # 如果有MCP Host，发现MCP工具（异步）
        if self.mcp_host:
            print(f"🔌 [Agent] MCP Host已配置，将在初始化时发现工具")
        
        # 创建LangChain ReAct Agent
        self.agent_executor = None  # 延迟创建，等MCP工具发现完成
        
        # 创建工作流（如果启用）
        if self.use_workflow:
            self.workflow = self._create_workflow()
        
        # ReAct步骤记录
        self.react_steps: List[ReActStep] = []
    
    async def initialize(self):
        """
        异步初始化（发现MCP工具）
        
        必须在使用Agent前调用
        """
        if self.mcp_host:
            await self.tool_module.discover_mcp_tools()
        
        # 创建Agent Executor
        self.agent_executor = self._create_react_agent()
        
        print(f"✅ [Agent] 初始化完成")
        print(f"   工具总数: {len(self.tool_module.get_tools())}")
        print(f"   Workflow模式: {'启用' if self.use_workflow else '禁用'}\n")
    
    @abstractmethod
    def _register_agent_tools(self):
        """注册Agent专属工具（子类实现）"""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """获取系统提示词（子类实现）"""
        pass
    
    def _create_react_agent(self) -> Any:
        """创建LangChain ReAct Agent（使用LangGraph）"""
        try:
            # 新版LangChain使用LangGraph
            from langgraph.prebuilt import create_react_agent
            
            # 获取工具列表
            tools = self.tool_module.get_tools()
            
            if not tools:
                print("⚠️  没有可用工具，无法创建Agent")
                return None
            
            print(f"   创建ReAct Agent，工具数: {len(tools)}")
            
            # 创建系统提示（强调工具使用）
            system_prompt = self.get_system_prompt()
            
            # 添加工具使用指导
            system_prompt += """

## 工具使用指南

你有以下专业工具可用：
"""
            for tool in tools:
                system_prompt += f"\n- {tool.name}: {tool.description}"
            
            system_prompt += """

## 核心原则：优先使用工具

1. **工具优先原则**：当有相关工具可用时，应该优先调用工具获取专业分析，而不是仅凭通用知识回答
2. **工具的专业性**：这些工具经过专门设计和训练，能提供比通用知识更准确、更专业、更可靠的分析结果
3. **多工具协作**：复杂问题可以调用多个工具，从不同角度分析，综合结果后给出全面建议
4. **工具增强可信度**：使用工具的分析结果会让你的回答更有说服力和专业性
5. **智能工具使用**：根据实际需要决定调用哪些工具，避免不必要的重复调用
6. **结合用户背景（重要）**：如果系统提供了【用户背景】信息，你必须在调用工具时将这些背景信息融入到工具参数中，实现个性化分析

## 如何结合用户背景使用工具（关键）

当系统提供了【用户背景】信息时，你需要：

**步骤1：理解用户背景**
- 仔细阅读【用户背景】部分，提取关键信息（如：性格特点、历史经历、偏好、目标等）
- 识别哪些背景信息与当前问题相关

**步骤2：将背景融入工具参数**
- 在调用工具时，把相关的用户背景信息写入工具的参数描述中
- 让工具的LLM分析能够基于用户的真实情况进行个性化分析

**示例1：人际关系分析**
```
用户背景：性格内向，不善于表达情感，曾经因为沟通问题失去过一段友谊
用户问题：我和新同事关系不太好，怎么办？

❌ 错误做法（忽略背景）：
analyze_communication_pattern(
  relationship_type="同事",
  recent_interactions="关系不太好",
  issues="不知道"
)

✅ 正确做法（融入背景）：
analyze_communication_pattern(
  relationship_type="同事",
  recent_interactions="我是一个性格内向的人，不太善于主动表达情感。最近和新同事的互动比较少，感觉关系有些疏远。",
  issues="我曾经因为沟通问题失去过友谊，担心这次也会出现类似问题。我的内向性格让我不知道如何主动改善关系。"
)
```

**示例2：职业规划**
```
用户背景：计算机专业大三学生，GPA 3.6，有一次实习经历，对AI方向感兴趣但不确定
用户问题：我应该考研还是工作？

❌ 错误做法（忽略背景）：
analyze_career_path(
  current_situation="大三学生",
  options="考研或工作"
)

✅ 正确做法（融入背景）：
analyze_career_path(
  current_situation="我是计算机专业大三学生，目前GPA 3.6，有一次互联网公司的实习经历。我对AI方向很感兴趣，但还不确定是否要深入研究。",
  options="考研（可以深入学习AI理论）或直接工作（积累实践经验）",
  concerns="不确定自己是否适合做研究，也担心工作后就没机会深造了"
)
```

**示例3：教育规划**
```
用户背景：目标是申请美国TOP30大学的CS专业，托福105，GRE 325，有两篇论文
用户问题：我的GPA 3.5够吗？

❌ 错误做法（忽略背景）：
calculate_gpa_requirements(
  target_university="美国大学",
  current_gpa=3.5
)

✅ 正确做法（融入背景）：
calculate_gpa_requirements(
  target_university="美国TOP30大学",
  major="计算机科学",
  current_gpa=3.5,
  additional_scores="托福105分，GRE 325分，有两篇学术论文发表"
)
```

**核心要点**：
- 用户背景不是可选的，而是必须利用的关键信息
- 将背景信息转化为工具参数的具体描述，而不是简单复制
- 让工具的LLM能够基于用户的真实情况进行分析，而不是给出通用建议
- 这样工具返回的结果会更加个性化、更有针对性、更有价值

## 如何使用retrieve_user_data工具（RAG检索）

**重要**：系统在对话开始时会自动加载一次用户背景，但这可能不够全面。你可以在需要时主动调用`retrieve_user_data`工具获取更多用户信息。

**何时调用retrieve_user_data**：
1. 系统提供的【用户背景】信息不够详细或不够相关
2. 需要了解用户在特定领域的历史经历（如：职业经历、教育背景、人际关系史）
3. 需要查找用户之前提到过但当前对话中没有的信息
4. 需要验证或补充用户的某些信息

**调用示例**：
```
用户问题：我应该如何改善和领导的关系？
系统背景：（只有基本信息，没有职场相关内容）

步骤1：先调用retrieve_user_data获取职场背景
retrieve_user_data("用户的职场经历、与领导相处的历史、工作环境")

步骤2：基于检索结果，调用专业工具
analyze_communication_pattern(
  relationship_type="上下级",
  recent_interactions="[融入检索到的具体职场互动信息]",
  issues="[融入检索到的历史问题]"
)
```

**多次检索策略**：
- 第一次检索：获取宏观背景（如"用户的教育背景和职业目标"）
- 第二次检索：获取具体细节（如"用户在AI领域的学习经历"）
- 第三次检索：获取相关经验（如"用户之前的求职经历"）

**检索结果的使用**：
- 检索到的信息应该立即融入到后续工具调用的参数中
- 不要只是告诉用户"我检索到了你的信息"，而是要实际使用这些信息
- 让每个工具调用都基于用户的真实情况，而不是假设或通用场景

## 何时使用工具

**必须使用工具的情况**：
- 需要最新信息、实时数据（使用web_search）
- 需要专业分析、评估、计算（使用对应的专业工具）
- 用户明确要求使用工具或要求专业分析
- 涉及具体数据、分数、指标的计算

**可以直接回答的情况**：
- 简单问候和闲聊（"你好"、"谢谢"）
- 纯粹的常识性问题且不需要专业分析
- 用户只是想聊天而不是寻求专业建议

## 工具使用原则

✅ **高效使用工具**：
- 每次调用工具前，先思考：这个工具能提供什么信息？我真的需要它吗？
- 如果一个工具已经返回了足够的信息，就不需要再次调用它
- 如果需要更多信息，应该调用其他不同的工具，从不同角度分析
- 例如：web_search一次通常就够了，除非第一次搜索的关键词不对需要换个角度搜索

✅ **合理的工具组合**：
- 人际关系问题：可以组合使用 assess_relationship_health + analyze_communication_pattern + suggest_conversation_topics
- 需要最新信息：通常web_search一次就够，除非需要搜索不同的关键词
- 复杂问题：可以调用多个不同的工具，但每个工具根据需要调用，不是为了调用而调用

## 工作流程

1. **Thought（思考）**：分析用户问题，判断需要哪些信息和工具
2. **Action（可选）**：如果需要更多用户背景，先调用retrieve_user_data
3. **Observation（可选）**：查看检索到的用户信息
4. **Thought（再思考）**：基于用户背景，决定调用哪个专业工具
5. **Action（行动）**：调用专业工具（参数中融入用户背景）
6. **Observation（观察）**：仔细阅读工具返回的结果
7. **Thought（再思考）**：
   - 这个结果是否已经足够回答问题？
   - 如果不够，我需要什么额外信息？
   - 应该调用哪个其他工具来获取这些信息？
8. **Action（可选）**：如果确实需要，调用另一个不同的工具
9. **Observation（可选）**：查看新工具的结果
10. **Final Answer（最终回答）**：综合所有信息，给出专业建议

## 示例

**示例1：人际关系问题（先检索背景，再多工具协作）**
用户："我和朋友关系紧张，怎么办？"
系统背景：（只有基本信息）

Thought: 需要了解用户的人际关系历史和性格特点
Action: retrieve_user_data("用户的性格特点、人际关系历史、社交模式")
Observation: 用户性格内向，曾因沟通问题失去友谊，不善表达情感
Thought: 现在有了背景，需要评估当前关系健康度
Action: assess_relationship_health(
  relationship_type="朋友",
  interaction_frequency="每周",
  satisfaction_level=4,
  conflict_frequency="经常",
  additional_context="我是性格内向的人，不善于表达情感，曾经因为沟通问题失去过友谊"
)
Observation: 健康度55分，关系紧张，需要改善沟通
Thought: 知道了健康度，现在需要分析具体的沟通问题
Action: analyze_communication_pattern(
  relationship_type="朋友",
  recent_interactions="最近互动减少，对话时感觉有距离感。我因为内向不太主动联系。",
  issues="担心重蹈覆辙，不知道如何主动修复关系。我的内向性格让我很难开口。"
)
Observation: 识别出沟通障碍：主动性不足、情感表达欠缺、倾听不够
Thought: 已经有了健康度评估和沟通分析，足够给出建议了
Final Answer: 综合建议...

**示例2：职业规划（多次检索不同维度）**
用户："我应该考研还是工作？"
系统背景：（只有基本学历信息）

Thought: 需要了解用户的教育背景和职业目标
Action: retrieve_user_data("用户的专业、GPA、实习经历、职业兴趣")
Observation: 计算机专业大三，GPA 3.6，有一次实习，对AI感兴趣
Thought: 还需要了解用户的长期规划和顾虑
Action: retrieve_user_data("用户的职业规划、考研意向、对未来的期望")
Observation: 想进大厂，但也想深入学习AI，担心工作后没机会深造
Thought: 现在有足够背景，可以分析职业路径
Action: analyze_career_path(
  current_situation="计算机专业大三学生，GPA 3.6，有互联网公司实习经历，对AI方向感兴趣但不确定是否要深入研究",
  options="考研（深入学习AI理论，提升学历竞争力）vs 直接工作（进大厂积累实践经验，快速成长）",
  goals="长期目标是进入顶尖科技公司，从事AI相关工作",
  concerns="担心工作后就没机会深造，也担心读研后错过最佳就业时机"
)
Observation: 工具返回详细的路径分析和建议
Final Answer: 基于你的情况...

**示例3：搜索问题（单次调用）**
用户："今年的诺贝尔奖得主是谁？"
Thought: 需要最新信息，使用web_search
Action: 调用web_search("今年诺贝尔奖得主")
Observation: 获得搜索结果
Thought: 搜索结果已经包含了答案，不需要再搜索
Final Answer: 基于搜索结果回答

**示例4：教育规划（先检索再分析）**
用户："我的GPA能申请到好学校吗？"
系统背景：（没有详细的申请信息）

Thought: 需要了解用户的完整申请背景
Action: retrieve_user_data("用户的GPA、标准化考试成绩、目标院校、专业方向")
Observation: GPA 3.5，托福105，GRE 325，目标美国TOP30 CS专业，有两篇论文
Thought: 现在有完整信息，可以分析录取概率
Action: calculate_gpa_requirements(
  target_university="美国TOP30大学",
  major="计算机科学",
  current_gpa=3.5,
  additional_scores="托福105分，GRE 325分，有两篇学术论文发表，一次科研项目经历"
)
Observation: 工具返回GPA要求和录取概率分析
Final Answer: 基于分析结果给出建议...
"""
            
            # 使用LangGraph创建ReAct Agent
            # LangGraph的create_react_agent不支持自定义系统提示
            # 系统提示需要在调用时通过messages传递
            agent_executor = create_react_agent(
                model=self.llm_module.langchain_llm,
                tools=tools
            )
            
            # 保存系统提示词，在调用时使用
            self.system_prompt_for_agent = system_prompt
            
            print(f"   ✅ ReAct Agent创建成功")
            return agent_executor
            
        except ImportError as e:
            print(f"❌ 导入失败: {e}")
            print(f"   请安装: pip install langgraph")
            return None
            
        except Exception as e:
            print(f"❌ 创建Agent失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _create_workflow(self) -> Workflow:
        """
        创建工作流 - 简化版
        
        标准流程：
        START → MEMORY_LOAD → INTENT_CLASSIFY → AGENT_DECISION → MEMORY_SAVE → END
        
        所有查询统一走Agent路径，由Agent自己决定是否需要工具
        """
        workflow = Workflow(f"{self.agent_type}_workflow")
        
        # 1. 开始
        workflow.add_node(WorkflowNode(
            node_id="start",
            node_type=WorkflowNodeType.START,
            description="工作流开始",
            next_nodes={"default": "memory_load"}
        ))
        
        # 2. 加载记忆
        workflow.add_node(WorkflowNode(
            node_id="memory_load",
            node_type=WorkflowNodeType.MEMORY_LOAD,
            description="加载用户偏好和历史背景",
            handler=self._handle_memory_load,
            next_nodes={"default": "intent_classify"}
        ))
        
        # 3. 意图分类（保留用于记录，但不再分流）
        workflow.add_node(WorkflowNode(
            node_id="intent_classify",
            node_type=WorkflowNodeType.INTENT_CLASSIFY,
            description="分析用户意图（记录用）",
            handler=self._handle_intent_classify,
            next_nodes={"agent": "agent_decision"}  # 统一走Agent
        ))
        
        # 4. Agent决策（统一入口）
        workflow.add_node(WorkflowNode(
            node_id="agent_decision",
            node_type=WorkflowNodeType.AGENT_DECISION,
            description="Agent智能处理（自动决定是否使用工具）",
            handler=self._handle_agent_decision,
            next_nodes={"default": "memory_save"}
        ))
        
        # 5. 保存记忆
        workflow.add_node(WorkflowNode(
            node_id="memory_save",
            node_type=WorkflowNodeType.MEMORY_SAVE,
            description="保存对话到记忆系统",
            handler=self._handle_memory_save,
            next_nodes={"default": "end"}
        ))
        
        # 6. 结束
        workflow.add_node(WorkflowNode(
            node_id="end",
            node_type=WorkflowNodeType.END,
            description="工作流结束"
        ))
        
        return workflow
    
    # ===== Workflow节点处理器 =====
    
    def _handle_memory_load(self, context: WorkflowContext) -> str:
        """加载记忆"""
        context.retrieved_memory = self.memory_module.retrieve_from_external_memory(
            f"用户偏好和历史背景",
            self.agent_type,
            max_results=3,
            reason="task_start"
        )
        return "default"
    
    def _handle_intent_classify(self, context: WorkflowContext) -> str:
        """意图分类 - 简化版：统一走Agent路径"""
        context.intent = self.llm_module.understand_intent(
            context.user_message,
            self.memory_module.get_context_window()
        )
        
        print(f"   意图: {context.intent.get('intent')}")
        print(f"   复杂度: {context.intent.get('complexity')}")
        print(f"   → 路由到: Agent决策（统一由Agent处理）")
        
        # 统一走Agent路径，让Agent自己决定是否需要工具
        return "agent"
    
    def _handle_simple_response(self, context: WorkflowContext) -> str:
        """简单回复（纯Workflow，无需Agent）"""
        print(f"   使用LLM直接生成回复（无ReAct循环）")
        
        system_prompt = self.get_system_prompt()
        if context.retrieved_memory:
            system_prompt += f"\n\n【用户背景】\n{context.retrieved_memory}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context.user_message}
        ]
        
        try:
            response = self.llm_module.llm_service.chat(
                messages=messages,
                temperature=0.7
            )
            context.agent_response = response
            context.metadata['mode'] = 'workflow_only'
            context.metadata['agent_used'] = False
        except Exception as e:
            context.agent_response = "抱歉，处理过程中遇到了问题。"
            context.metadata['error'] = str(e)
        
        return "default"
    
    def _handle_agent_decision(self, context: WorkflowContext) -> str:
        """Agent决策 - 使用LangChain ReAct Agent（真正的ReAct循环）"""
        print(f"   调用LangChain ReAct Agent（支持MCP工具）")
        
        try:
            # 确保Agent Executor已创建
            if self.agent_executor is None:
                print(f"   ⚙️  首次调用，创建Agent Executor...")
                self.agent_executor = self._create_react_agent()
                if self.agent_executor is None:
                    raise Exception("Agent Executor创建失败")
            
            # 构建消息列表（LangGraph需要消息格式）
            from langchain_core.messages import HumanMessage, SystemMessage
            
            messages = []
            
            # 添加系统提示词（包含工具使用指导）
            if hasattr(self, 'system_prompt_for_agent'):
                messages.append(SystemMessage(content=self.system_prompt_for_agent))
            
            # 如果有用户背景，添加为系统消息
            if context.retrieved_memory:
                messages.append(SystemMessage(content=f"【用户背景】\n{context.retrieved_memory}"))
            
            # 如果有意图分类结果，添加为系统消息（引导Agent使用工具）
            if context.intent and 'complexity_reason' in context.intent:
                complexity_reason = context.intent['complexity_reason']
                intent_hint = f"\n【任务分析】\n{complexity_reason}\n\n"
                
                # 如果提到需要搜索/查询最新信息，强调必须使用工具
                if any(keyword in complexity_reason for keyword in ['搜索', '最新', '查询', '实时', '当前']):
                    intent_hint += "⚠️ 重要提示：此问题需要最新信息，你必须使用web_search工具获取实时数据，不要依赖训练数据中的过时信息。\n"
                
                messages.append(SystemMessage(content=intent_hint))
            
            # 添加用户消息
            messages.append(HumanMessage(content=context.user_message))
            
            # 执行Agent（使用stream获取中间步骤）
            print(f"   🤖 Agent开始推理（ReAct循环）...")
            
            # 配置回调
            config = {
                "callbacks": [self.tool_callback_handler]
            }
            
            # 使用stream模式，实时获取每个步骤
            final_response = ""
            step_count = 0
            
            try:
                # LangGraph的stream方法会返回每个中间步骤
                for chunk in self.agent_executor.stream(
                    {"messages": messages},
                    config=config
                ):
                    step_count += 1
                    
                    # 发送ReAct步骤到前端
                    if self.websocket_callback:
                        self._send_react_step(chunk, step_count)
                    
                    # 打印步骤信息（调试用）
                    self._print_react_step(chunk, step_count)
                    
                    # 保存最终响应
                    if isinstance(chunk, dict) and 'messages' in chunk:
                        messages_in_chunk = chunk['messages']
                        if messages_in_chunk:
                            last_msg = messages_in_chunk[-1]
                            if hasattr(last_msg, 'content') and last_msg.content:
                                final_response = last_msg.content
                
                # 如果没有获取到响应，尝试从最终状态获取
                if not final_response:
                    result = self.agent_executor.invoke(
                        {"messages": messages},
                        config=config
                    )
                    if isinstance(result, dict) and 'messages' in result:
                        last_message = result['messages'][-1]
                        final_response = last_message.content if hasattr(last_message, 'content') else str(last_message)
                
                context.agent_response = final_response
                context.metadata['mode'] = 'workflow_agent_hybrid'
                context.metadata['agent_used'] = True
                context.metadata['react_steps'] = step_count
                print(f"   ✅ Agent推理完成（共{step_count}步）")
                
            except Exception as stream_error:
                # 如果stream失败，回退到invoke
                print(f"   ⚠️  Stream模式失败，回退到invoke: {stream_error}")
                
                result = self.agent_executor.invoke(
                    {"messages": messages},
                    config=config
                )
                
                # 提取回复
                if isinstance(result, dict):
                    if 'messages' in result and result['messages']:
                        last_message = result['messages'][-1]
                        if hasattr(last_message, 'content'):
                            context.agent_response = last_message.content
                        else:
                            context.agent_response = str(last_message)
                    else:
                        context.agent_response = result.get('output', str(result))
                else:
                    context.agent_response = str(result)
                
                context.metadata['mode'] = 'workflow_agent_hybrid'
                context.metadata['agent_used'] = True
                print(f"   ✅ Agent推理完成（invoke模式）")
            
        except Exception as e:
            print(f"   ❌ Agent执行失败: {e}")
            import traceback
            traceback.print_exc()
            
            # 降级：使用简单LLM回复
            try:
                system_prompt = self.get_system_prompt()
                if context.retrieved_memory:
                    system_prompt += f"\n\n【用户背景】\n{context.retrieved_memory}"
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context.user_message}
                ]
                
                response = self.llm_module.llm_service.chat(
                    messages=messages,
                    temperature=0.7
                )
                context.agent_response = response
                context.metadata['mode'] = 'fallback_llm'
                context.metadata['agent_used'] = False
                print(f"   ⚠️  降级为简单LLM回复")
                
            except Exception as e2:
                print(f"   ❌ 降级也失败: {e2}")
                context.agent_response = "抱歉，处理过程中遇到了问题。"
                context.metadata['error'] = str(e2)
            
            # 保存错误
            self.memory_module.save_error(
                error_context=f"Agent决策: {context.user_message}",
                error_message=str(e)
            )
        
        return "default"
    
    def _send_react_step(self, chunk: dict, step_number: int):
        """发送ReAct步骤到前端（包含SVG图标标识）"""
        try:
            if not self.websocket_callback:
                return
            
            # 解析chunk，提取步骤信息
            step_data = {
                "step_number": step_number,
                "timestamp": datetime.now().isoformat()
            }
            
            # 检查是否包含消息
            if isinstance(chunk, dict) and 'messages' in chunk:
                messages = chunk['messages']
                if messages:
                    last_msg = messages[-1]
                    
                    # 判断步骤类型
                    if hasattr(last_msg, 'type'):
                        msg_type = last_msg.type
                        
                        if msg_type == 'ai':
                            # AI的思考或回答
                            content = last_msg.content if hasattr(last_msg, 'content') else ''
                            
                            # 检查是否有工具调用
                            if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                                # 这是Action步骤
                                tool_call = last_msg.tool_calls[0]
                                step_data['type'] = 'action'
                                step_data['icon'] = 'tool'  # 前端渲染工具图标
                                step_data['tool_name'] = tool_call.get('name', 'unknown')
                                step_data['tool_args'] = tool_call.get('args', {})
                                step_data['content'] = f"调用工具: {step_data['tool_name']}"
                                
                                # Action步骤总是发送，即使没有content
                                self.websocket_callback("react_step", step_data)
                                return
                            
                            # 这是Thought或Final Answer（只有有内容时才发送）
                            if content and len(content) > 0:
                                if any(keyword in content.lower() for keyword in ['final answer', '最终回答', '综合以上', '根据以上']):
                                    step_data['type'] = 'final_answer'
                                    step_data['icon'] = 'check'  # 前端渲染完成图标
                                else:
                                    step_data['type'] = 'thought'
                                    step_data['icon'] = 'brain'  # 前端渲染思考图标
                                step_data['content'] = content
                                self.websocket_callback("react_step", step_data)
                                return
                        
                        elif msg_type == 'tool':
                            # 工具返回结果（Observation）
                            step_data['type'] = 'observation'
                            step_data['icon'] = 'eye'  # 前端渲染观察图标
                            step_data['tool_name'] = getattr(last_msg, 'name', 'unknown')
                            content = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
                            
                            # 限制observation内容长度，避免过长
                            if len(content) > 500:
                                content = content[:500] + "..."
                            
                            step_data['content'] = content
                            self.websocket_callback("react_step", step_data)
                            return
                
        except Exception as e:
            print(f"⚠️  发送ReAct步骤失败: {e}")
    
    def _print_react_step(self, chunk: dict, step_number: int):
        """打印ReAct步骤（调试用）"""
        try:
            # 打印原始chunk结构（调试用）
            # print(f"   [DEBUG] Chunk keys: {chunk.keys() if isinstance(chunk, dict) else 'not dict'}")
            
            if isinstance(chunk, dict) and 'messages' in chunk:
                messages = chunk['messages']
                if messages:
                    last_msg = messages[-1]
                    
                    if hasattr(last_msg, 'type'):
                        msg_type = last_msg.type
                        
                        if msg_type == 'ai':
                            content = last_msg.content if hasattr(last_msg, 'content') else ''
                            
                            if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                                tool_call = last_msg.tool_calls[0]
                                print(f"   🎯 [步骤{step_number}] Action: 调用工具 {tool_call.get('name', 'unknown')}")
                            elif content:
                                if any(keyword in content.lower() for keyword in ['final answer', '最终回答']):
                                    print(f"   ✅ [步骤{step_number}] Final Answer: {content[:100]}...")
                                else:
                                    print(f"   💭 [步骤{step_number}] Thought: {content[:100]}...")
                            else:
                                # 空content的AI消息，可能是中间状态
                                print(f"   ⏸️  [步骤{step_number}] AI消息（无内容）")
                        
                        elif msg_type == 'tool':
                            tool_name = getattr(last_msg, 'name', 'unknown')
                            content = last_msg.content if hasattr(last_msg, 'content') else ''
                            content_preview = content[:100] if content else '(空结果)'
                            print(f"   👁️  [步骤{step_number}] Observation: 工具 {tool_name} 返回 - {content_preview}...")
                        
                        else:
                            # 其他类型的消息
                            print(f"   ❓ [步骤{step_number}] 未知消息类型: {msg_type}")
                    else:
                        print(f"   ⚠️  [步骤{step_number}] 消息无type属性")
            else:
                # 不是标准的messages格式
                if isinstance(chunk, dict):
                    print(f"   📦 [步骤{step_number}] 非标准chunk: {list(chunk.keys())}")
                            
        except Exception as e:
            print(f"   ⚠️  [步骤{step_number}] 打印失败: {e}")
    
    def _handle_memory_save(self, context: WorkflowContext) -> str:
        """保存记忆"""
        # 添加到上下文窗口
        self.memory_module.add_to_context_window(AgentMessage(
            role='user',
            content=context.user_message,
            timestamp=datetime.now(),
            metadata={'intent': context.intent}
        ))
        self.memory_module.add_to_context_window(AgentMessage(
            role='assistant',
            content=context.agent_response,
            timestamp=datetime.now(),
            metadata=context.metadata
        ))
        
        # 保存任务结果（只在没有错误时保存）
        if not context.metadata.get('error'):
            try:
                self.memory_module.save_task_result(
                    task_description=context.user_message,
                    result=context.agent_response,
                    success=True,
                    key_findings=[
                        f"意图: {context.intent.get('intent')}",
                        f"模式: {context.metadata.get('mode')}",
                        f"工具调用: {len(context.metadata.get('tool_calls', []))}"
                    ]
                )
            except Exception as e:
                print(f"⚠️  保存任务结果失败（非致命错误）: {e}")
        
        return "default"
    
    # ===== 主处理方法 =====
    
    def process(self, user_message: str) -> Dict[str, Any]:
        """
        处理用户消息
        
        模式：
        - use_workflow=True: Workflow + Agent混合架构
        - use_workflow=False: 纯Agent ReAct模式
        
        Returns:
            {
                'response': str,
                'mode': 'workflow_only' | 'workflow_agent_hybrid' | 'pure_agent',
                'execution_path': List[str],  # Workflow模式
                'react_steps': List[Dict],    # 纯Agent模式
                'retrieval_stats': Dict
            }
        """
        if self.use_workflow:
            return self._process_with_workflow(user_message)
        else:
            return self._process_pure_agent(user_message)
    
    def _process_with_workflow(self, user_message: str) -> Dict[str, Any]:
        """使用Workflow混合架构处理"""
        # 创建工作流上下文
        context = WorkflowContext(
            user_message=user_message,
            user_id=self.user_id,
            agent_type=self.agent_type
        )
        
        # 清空之前的工具调用记录（每次对话重新开始）
        if self.mcp_host and hasattr(self.mcp_host, 'client'):
            self.mcp_host.client.call_logs = []
        
        # 执行工作流
        context = self.workflow.execute(context)
        
        # 收集MCP工具调用信息（从本次对话的日志）
        tool_calls = []
        if self.mcp_host and hasattr(self.mcp_host, 'client') and hasattr(self.mcp_host.client, 'call_logs'):
            for log in self.mcp_host.client.call_logs:  # 使用所有日志，不限制数量
                tool_calls.append({
                    'tool_name': log.tool_name,
                    'server_name': self._get_server_name_by_id(log.server_id),
                    'status': 'completed' if log.success else 'failed',
                    'result': str(log.result)[:100] if log.result else None
                })
        
        print(f"\n[DEBUG] 本次对话工具调用数: {len(tool_calls)}")
        if tool_calls:
            for i, tool in enumerate(tool_calls, 1):
                print(f"  {i}. {tool['tool_name']} - {tool['status']}")
        
        return {
            'response': context.agent_response,
            'mode': context.metadata.get('mode', 'unknown'),
            'agent_used': context.metadata.get('agent_used', False),
            'execution_path': context.metadata.get('execution_path', []),
            'tasks_executed': [],  # 兼容旧API
            'tools_used': [],      # 兼容旧API
            'tool_calls': tool_calls,  # MCP工具调用信息
            'retrieval_stats': {
                'intent': context.intent.get('intent') if context.intent else None,
                'complexity': context.intent.get('complexity') if context.intent else None,
                'context_window_size': len(self.memory_module.context_window),
                'workflow_mode': context.metadata.get('mode')
            }
        }
    
    def _get_server_name_by_id(self, server_id: str) -> str:
        """根据Server ID获取Server名称"""
        if not self.mcp_host:
            return "Unknown"
        
        for server in self.mcp_host.servers.values():
            if server.server_id == server_id:
                return server.name
        
        return server_id
    
    def _process_pure_agent(self, user_message: str) -> Dict[str, Any]:
        """使用纯Agent ReAct模式处理（简化实现）"""
        print(f"\n{'='*60}")
        print(f"[{self.agent_type} Agent] 纯Agent ReAct模式")
        print(f"{'='*60}\n")
        
        self.react_steps = []
        
        # 1. 任务开始 - 加载用户记忆
        print("📖 任务开始：加载用户记忆")
        user_context = self.memory_module.retrieve_from_external_memory(
            f"用户偏好和历史背景",
            self.agent_type,
            max_results=3,
            reason="task_start"
        )
        
        # 2. 意图理解
        print("\n🤔 理解用户意图")
        intent = self.llm_module.understand_intent(
            user_message,
            self.memory_module.get_context_window()
        )
        print(f"   意图: {intent.get('intent')}")
        print(f"   复杂度: {intent.get('complexity')}\n")
        
        # 3. 执行ReAct（简化实现）
        print("🔄 执行ReAct推理")
        try:
            # 构建系统提示词
            system_prompt = self.get_system_prompt()
            if user_context:
                system_prompt += f"\n\n【用户背景】\n{user_context}"
            
            # 构建工具列表
            tools_desc = "\n".join([
                f"- {tool.name}: {tool.description}"
                for tool in self.tool_module.get_tools()
            ])
            
            # ReAct提示词（优化：强调工具使用）
            react_prompt = f"""{system_prompt}

你可以使用以下工具：
{tools_desc}

【重要原则】
1. 优先使用工具：当有相关工具可用时，应该优先调用工具获取专业分析，而不是仅凭通用知识回答
2. 工具提供专业能力：这些工具经过专门设计，能提供比通用知识更准确、更专业的分析
3. 多工具协作：复杂问题可以调用多个工具，综合分析后给出建议

请使用ReAct模式思考和回答：
1. Thought: 分析问题，判断是否需要使用工具（优先考虑使用工具）
2. Action: 如果有相关工具，应该调用工具获取专业分析
3. Observation: 观察工具返回的结果
4. Thought: 基于工具结果继续思考，判断是否需要更多工具
5. Final Answer: 综合工具分析结果，给出最终回答

用户问题：{user_message}"""
            
            messages = [
                {"role": "system", "content": react_prompt}
            ]
            
            response = self.llm_module.llm_service.chat(
                messages=messages,
                temperature=0.7
            )
            
            success = True
            
        except Exception as e:
            print(f"❌ ReAct执行失败: {e}")
            response = "抱歉，处理过程中遇到了问题。"
            success = False
            
            self.memory_module.save_error(
                error_context=f"处理消息: {user_message}",
                error_message=str(e)
            )
        
        # 4. 保存到记忆系统
        print("\n💾 保存到记忆系统")
        self.memory_module.add_to_context_window(AgentMessage(
            role='user',
            content=user_message,
            timestamp=datetime.now(),
            metadata={'intent': intent}
        ))
        self.memory_module.add_to_context_window(AgentMessage(
            role='assistant',
            content=response,
            timestamp=datetime.now(),
            metadata={'success': success}
        ))
        
        if success:
            self.memory_module.save_task_result(
                task_description=user_message,
                result=response,
                success=True,
                key_findings=[f"意图: {intent.get('intent')}"]
            )
        
        self.memory_module.clear_working_memory()
        
        print(f"{'='*60}")
        print(f"[{self.agent_type} Agent] 处理完成")
        print(f"{'='*60}\n")
        
        return {
            'response': response,
            'mode': 'pure_agent',
            'agent_used': True,
            'react_steps': [step.__dict__ for step in self.react_steps],
            'tasks_executed': [],  # 兼容旧API
            'tools_used': [],      # 兼容旧API
            'retrieval_stats': {
                'intent': intent.get('intent'),
                'complexity': intent.get('complexity'),
                'context_window_size': len(self.memory_module.context_window)
            }
        }


