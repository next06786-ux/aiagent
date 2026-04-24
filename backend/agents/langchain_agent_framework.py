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
    from langchain_core.callbacks import CallbackManagerForLLMRun
    from langchain_core.tools import Tool
    from langchain_core.prompts import PromptTemplate
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    
    # 简化实现：不使用AgentExecutor，直接用LLM
    LANGCHAIN_VERSION = "new"
except ImportError:
    # 回退到旧版API
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain.tools import Tool, BaseTool
    from langchain.prompts import PromptTemplate
    from langchain_core.language_models import BaseLLM
    from langchain_core.callbacks import CallbackManagerForLLMRun
    from langchain.memory import ConversationBufferMemory
    LANGCHAIN_VERSION = "old"

# MCP导入
from backend.agents.mcp_integration import MCPHost, MCPTool, ParallelFunctionCaller


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

class DashScopeLLM(BaseLLM):
    """
    DashScope LLM包装器，适配LangChain接口
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
    
    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Any:
        """生成响应（新版API要求）"""
        from langchain_core.outputs import LLMResult, Generation
        
        generations = []
        for prompt in prompts:
            try:
                messages = [{"role": "user", "content": prompt}]
                response = self.llm_service.chat(
                    messages=messages,
                    temperature=self.temperature,
                    model=self.model
                )
                generations.append([Generation(text=response)])
            except Exception as e:
                print(f"❌ LLM调用失败: {e}")
                generations.append([Generation(text=f"Error: {str(e)}")])
        
        return LLMResult(generations=generations)
    
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
2. 单一事实查询（"什么是..."、"谁是..."、"哪里..."）
3. 简单确认或澄清（"是的"、"对"、"不是"）
4. 无需推理的直接回答
5. 不需要调用工具或检索记忆

**medium（中等）** - 满足以下任一条件：
1. 需要一定分析但不复杂（"如何..."、"为什么..."）
2. 需要检索用户历史信息
3. 需要简单的建议或推荐
4. 涉及1-2个维度的问题
5. 可能需要调用1个工具

**complex（复杂）** - 满足以下任一条件：
1. 需要深度分析和推理（"帮我规划..."、"如何解决..."）
2. 涉及多个维度或多步骤（"比较...并给出建议"）
3. 需要制定计划或策略
4. 需要调用多个工具或多次推理
5. 开放性问题需要创造性回答
6. 涉及复杂的人际关系/职业规划/教育路径

【示例】
- "你好" → simple
- "什么是职业规划" → simple
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
    
    def __init__(self, user_id: str, rag_system, retrieval_system):
        self.user_id = user_id
        self.rag_system = rag_system
        self.retrieval_system = retrieval_system
        
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
                
                return retrieved
            
            return ""
            
        except Exception as e:
            print(f"❌ 外部记忆检索失败: {e}")
            return ""
    
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
                memory_type=MemoryType.TASK_RESULT,
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
                memory_type=MemoryType.ERROR_LOG,
                content=content,
                metadata={
                    'error': error_message,
                    'context': error_context,
                    'timestamp': datetime.now().isoformat()
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
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # 如果事件循环已运行，创建新任务
                        import nest_asyncio
                        nest_asyncio.apply()
                    return loop.run_until_complete(executor(params_str))
                
                return sync_executor
            
            # 转换为LangChain Tool
            langchain_tool = Tool(
                name=mcp_tool.name,
                description=f"{mcp_tool.description} (MCP工具，来自{mcp_tool.server_id})",
                func=create_executor(mcp_tool.name)
            )
            
            self.tools.append(langchain_tool)
            
            approval_mark = "🔒" if mcp_tool.requires_approval else "🔓"
            print(f"   {approval_mark} {mcp_tool.name}")
        
        self.mcp_tools_discovered = True
        print(f"✅ [ToolModule] MCP工具发现完成，共 {len(mcp_tools)} 个\n")
    
    def _register_default_tools(self):
        """注册默认工具"""
        # 记忆检索工具（任务开始时）
        memory_tool = Tool(
            name="retrieve_memory",
            description="从外部记忆中检索相关信息。适用场景：任务开始时加载背景、遇到陌生问题、需要事实核查。输入：查询文本",
            func=self._retrieve_memory_tool
        )
        self.tools.append(memory_tool)
        
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
    
    def _retrieve_memory_tool(self, query: str) -> str:
        """记忆检索工具（智能判断检索原因）"""
        try:
            # 简单的原因判断（实际可以用LLM判断）
            reason = "general"
            if "背景" in query or "历史" in query or "之前" in query:
                reason = "task_start"
            elif "不知道" in query or "不了解" in query or "陌生" in query:
                reason = "unknown_problem"
            elif "确认" in query or "核实" in query or "是否" in query:
                reason = "fact_check"
            
            context = self.memory_module.retrieve_from_external_memory(
                query,
                self.agent_type,
                max_results=5,
                reason=reason
            )
            if context:
                return f"检索到相关信息：\n{context}"
            else:
                return "未找到相关信息"
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
        mcp_host: Optional[MCPHost] = None  # MCP Host（可选）
    ):
        self.agent_type = agent_type
        self.user_id = user_id
        self.use_workflow = use_workflow
        self.mcp_host = mcp_host
        
        # 初始化模块
        self.llm_module = LLMModule(llm_service)
        self.memory_module = MemoryModule(user_id, rag_system, retrieval_system)
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
        """创建LangChain ReAct Agent（简化实现）"""
        # 新版LangChain使用更简单的方式
        # 我们直接使用LLM + 工具，不依赖AgentExecutor
        return None  # 简化实现，直接在_handle_agent_decision中调用LLM
    
    def _create_workflow(self) -> Workflow:
        """
        创建工作流
        
        标准流程：
        START → MEMORY_LOAD → INTENT_CLASSIFY → 
        ├─ simple → SIMPLE_RESPONSE → MEMORY_SAVE → END
        └─ complex → AGENT_DECISION → MEMORY_SAVE → END
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
        
        # 3. 意图分类
        workflow.add_node(WorkflowNode(
            node_id="intent_classify",
            node_type=WorkflowNodeType.INTENT_CLASSIFY,
            description="分析用户意图和复杂度",
            handler=self._handle_intent_classify,
            next_nodes={
                "simple": "simple_response",
                "complex": "agent_decision"
            }
        ))
        
        # 4a. 简单回复（纯Workflow）
        workflow.add_node(WorkflowNode(
            node_id="simple_response",
            node_type=WorkflowNodeType.SIMPLE_RESPONSE,
            description="生成简单回复（无需Agent推理）",
            handler=self._handle_simple_response,
            next_nodes={"default": "memory_save"}
        ))
        
        # 4b. Agent决策（调用ReAct）
        workflow.add_node(WorkflowNode(
            node_id="agent_decision",
            node_type=WorkflowNodeType.AGENT_DECISION,
            description="调用Agent进行复杂推理",
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
        """意图分类"""
        context.intent = self.llm_module.understand_intent(
            context.user_message,
            self.memory_module.get_context_window()
        )
        
        print(f"   意图: {context.intent.get('intent')}")
        print(f"   复杂度: {context.intent.get('complexity')}")
        
        # 根据复杂度决定路径
        complexity = context.intent.get('complexity', 'medium')
        if complexity == 'simple':
            print(f"   → 路由到: 简单回复（纯Workflow）")
            return "simple"
        else:
            print(f"   → 路由到: Agent决策（ReAct推理）")
            return "complex"
    
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
        """Agent决策（简化ReAct实现）"""
        print(f"   调用ReAct Agent进行推理")
        
        try:
            # 构建系统提示词
            system_prompt = self.get_system_prompt()
            if context.retrieved_memory:
                system_prompt += f"\n\n【用户背景】\n{context.retrieved_memory}"
            
            # 构建工具列表描述
            tools_desc = "\n".join([
                f"- {tool.name}: {tool.description}"
                for tool in self.tool_module.get_tools()
            ])
            
            # 构建ReAct提示词
            react_prompt = f"""{system_prompt}

你可以使用以下工具：
{tools_desc}

请使用ReAct模式思考和回答：
1. Thought: 分析问题，思考需要做什么
2. Action: 如果需要工具，说明要使用哪个工具
3. Final Answer: 给出最终回答

用户问题：{context.user_message}"""
            
            # 调用LLM
            messages = [
                {"role": "system", "content": react_prompt}
            ]
            
            response = self.llm_module.llm_service.chat(
                messages=messages,
                temperature=0.7
            )
            
            context.agent_response = response
            context.metadata['mode'] = 'workflow_agent_hybrid'
            context.metadata['agent_used'] = True
            
        except Exception as e:
            print(f"   ❌ Agent执行失败: {e}")
            context.agent_response = "抱歉，处理过程中遇到了问题。"
            context.metadata['error'] = str(e)
            
            # 保存错误
            self.memory_module.save_error(
                error_context=f"Agent决策: {context.user_message}",
                error_message=str(e)
            )
        
        return "default"
    
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
        
        # 保存任务结果
        if not context.metadata.get('error'):
            self.memory_module.save_task_result(
                task_description=context.user_message,
                result=context.agent_response,
                success=True,
                key_findings=[
                    f"意图: {context.intent.get('intent')}",
                    f"模式: {context.metadata.get('mode')}"
                ]
            )
        
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
        
        # 执行工作流
        context = self.workflow.execute(context)
        
        # 收集MCP工具调用信息
        tool_calls = []
        if self.mcp_host and hasattr(self.mcp_host, 'client') and hasattr(self.mcp_host.client, 'call_logs'):
            for log in self.mcp_host.client.call_logs[-10:]:  # 最近10次调用
                tool_calls.append({
                    'tool_name': log.tool_name,
                    'server_name': self._get_server_name_by_id(log.server_id),
                    'status': 'completed' if log.success else 'failed',
                    'result': str(log.result)[:100] if log.result else None
                })
        
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
            
            # ReAct提示词
            react_prompt = f"""{system_prompt}

你可以使用以下工具：
{tools_desc}

请使用ReAct模式思考和回答：
1. Thought: 分析问题，思考需要做什么
2. Action: 如果需要工具，说明要使用哪个工具
3. Final Answer: 给出最终回答

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


