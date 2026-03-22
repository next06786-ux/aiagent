"""
ReAct Agent - 核心智能体框架
实现 Reasoning + Acting 循环，支持工具调用
"""
import json
import re
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio


class AgentState(Enum):
    """智能体状态"""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    OBSERVING = "observing"
    RESPONDING = "responding"


@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]
    func: Callable
    is_async: bool = False
    
    def to_prompt(self) -> str:
        """转换为提示词格式"""
        params_str = json.dumps(self.parameters, ensure_ascii=False, indent=2)
        return f"""- {self.name}: {self.description}
  参数: {params_str}"""


@dataclass
class AgentStep:
    """智能体执行步骤"""
    step_num: int
    thought: str
    action: Optional[str] = None
    action_input: Optional[Dict] = None
    observation: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentResult:
    """智能体执行结果"""
    success: bool
    final_answer: str
    steps: List[AgentStep]
    total_tokens: int = 0
    execution_time: float = 0.0
    tools_used: List[str] = field(default_factory=list)


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool):
        """注册工具"""
        self.tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[Tool]:
        """获取工具"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[Tool]:
        """列出所有工具"""
        return list(self.tools.values())
    
    def get_tools_prompt(self) -> str:
        """生成工具提示词"""
        if not self.tools:
            return "当前没有可用工具。"
        
        tools_desc = "\n".join([tool.to_prompt() for tool in self.tools.values()])
        return f"""可用工具：
{tools_desc}"""


class ReActAgent:
    """
    ReAct 智能体
    实现 Reasoning + Acting 循环
    """
    
    SYSTEM_PROMPT = """你是 LifeSwarm 智能助手，一个能够自主思考和行动的 AI 智能体。

你的工作方式是 ReAct 循环：
1. **思考(Thought)**: 分析用户需求，决定下一步行动
2. **行动(Action)**: 调用工具获取信息或执行操作
3. **观察(Observation)**: 分析工具返回的结果
4. 重复以上步骤直到能够给出最终答案

{tools_prompt}

## 输出格式

每一步必须严格按照以下格式输出：

```
Thought: [你的思考过程]
Action: [工具名称]
Action Input: [JSON格式的参数]
```

当你有足够信息回答用户时，输出：

```
Thought: [最终思考]
Final Answer: [给用户的最终回答]
```

## 重要规则

1. 每次只能调用一个工具
2. Action Input 必须是有效的 JSON
3. 如果工具调用失败，分析原因并尝试其他方法
4. 最多执行 {max_steps} 步，之后必须给出最终答案
5. 回答要自然、有帮助，像一个贴心的助手

## 用户上下文

用户ID: {user_id}
当前时间: {current_time}
"""

    def __init__(
        self,
        llm_service,
        tool_registry: ToolRegistry,
        max_steps: int = 5,
        verbose: bool = True
    ):
        self.llm = llm_service
        self.tools = tool_registry
        self.max_steps = max_steps
        self.verbose = verbose
        self.state = AgentState.IDLE
        
    def _build_system_prompt(self, user_id: str) -> str:
        """构建系统提示词"""
        return self.SYSTEM_PROMPT.format(
            tools_prompt=self.tools.get_tools_prompt(),
            max_steps=self.max_steps,
            user_id=user_id,
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M")
        )
    
    def _parse_llm_output(self, output: str) -> Dict[str, Any]:
        """解析 LLM 输出"""
        result = {
            "thought": None,
            "action": None,
            "action_input": None,
            "final_answer": None
        }
        
        # 提取 Thought
        thought_match = re.search(r'Thought:\s*(.+?)(?=Action:|Final Answer:|$)', output, re.DOTALL)
        if thought_match:
            result["thought"] = thought_match.group(1).strip()
        
        # 提取 Final Answer
        final_match = re.search(r'Final Answer:\s*(.+?)$', output, re.DOTALL)
        if final_match:
            result["final_answer"] = final_match.group(1).strip()
            return result
        
        # 提取 Action
        action_match = re.search(r'Action:\s*(\w+)', output)
        if action_match:
            result["action"] = action_match.group(1).strip()
        
        # 提取 Action Input
        input_match = re.search(r'Action Input:\s*(\{.+?\}|\[.+?\])', output, re.DOTALL)
        if input_match:
            try:
                result["action_input"] = json.loads(input_match.group(1))
            except json.JSONDecodeError:
                # 尝试修复常见的 JSON 错误
                try:
                    fixed = input_match.group(1).replace("'", '"')
                    result["action_input"] = json.loads(fixed)
                except:
                    result["action_input"] = {"raw": input_match.group(1)}
        
        return result
    
    async def _execute_tool(self, tool_name: str, tool_input: Dict) -> str:
        """执行工具"""
        tool = self.tools.get(tool_name)
        if not tool:
            return f"错误: 工具 '{tool_name}' 不存在。可用工具: {list(self.tools.tools.keys())}"
        
        try:
            if tool.is_async:
                result = await tool.func(**tool_input)
            else:
                result = tool.func(**tool_input)
            
            # 确保结果是字符串
            if isinstance(result, dict):
                return json.dumps(result, ensure_ascii=False, indent=2)
            return str(result)
        except Exception as e:
            return f"工具执行错误: {str(e)}"
    
    async def run(
        self,
        user_id: str,
        user_message: str,
        context: Optional[Dict] = None
    ) -> AgentResult:
        """
        运行智能体
        
        Args:
            user_id: 用户ID
            user_message: 用户消息
            context: 额外上下文
        
        Returns:
            AgentResult: 执行结果
        """
        start_time = datetime.now()
        steps: List[AgentStep] = []
        tools_used: List[str] = []
        
        # 构建初始消息
        system_prompt = self._build_system_prompt(user_id)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # 添加上下文
        if context:
            context_str = f"\n\n用户上下文信息:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
            messages[1]["content"] += context_str
        
        # ReAct 循环
        for step_num in range(1, self.max_steps + 1):
            self.state = AgentState.THINKING
            
            if self.verbose:
                print(f"\n{'='*50}")
                print(f"Step {step_num}")
                print('='*50)
            
            # 调用 LLM
            try:
                llm_output = self.llm.chat(messages, temperature=0.7)
            except Exception as e:
                return AgentResult(
                    success=False,
                    final_answer=f"LLM 调用失败: {str(e)}",
                    steps=steps,
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
            
            if self.verbose:
                print(f"LLM Output:\n{llm_output}")
            
            # 解析输出
            parsed = self._parse_llm_output(llm_output)
            
            step = AgentStep(
                step_num=step_num,
                thought=parsed["thought"] or "无明确思考"
            )
            
            # 检查是否有最终答案
            if parsed["final_answer"]:
                step.observation = "生成最终答案"
                steps.append(step)
                
                return AgentResult(
                    success=True,
                    final_answer=parsed["final_answer"],
                    steps=steps,
                    tools_used=tools_used,
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
            
            # 执行工具
            if parsed["action"]:
                self.state = AgentState.ACTING
                step.action = parsed["action"]
                step.action_input = parsed["action_input"] or {}
                
                if self.verbose:
                    print(f"\nAction: {step.action}")
                    print(f"Input: {step.action_input}")
                
                # 执行工具
                self.state = AgentState.OBSERVING
                observation = await self._execute_tool(
                    step.action,
                    step.action_input
                )
                step.observation = observation
                tools_used.append(step.action)
                
                if self.verbose:
                    print(f"\nObservation: {observation[:500]}...")
                
                # 将观察结果添加到消息历史
                messages.append({"role": "assistant", "content": llm_output})
                messages.append({"role": "user", "content": f"Observation: {observation}"})
            else:
                # 没有动作，可能是格式问题，提示重试
                messages.append({"role": "assistant", "content": llm_output})
                messages.append({
                    "role": "user", 
                    "content": "请按照格式输出 Action 和 Action Input，或者输出 Final Answer。"
                })
            
            steps.append(step)
        
        # 达到最大步数，强制生成答案
        self.state = AgentState.RESPONDING
        messages.append({
            "role": "user",
            "content": "你已经执行了足够多的步骤，请现在给出 Final Answer。"
        })
        
        try:
            final_output = self.llm.chat(messages, temperature=0.7)
            parsed = self._parse_llm_output(final_output)
            final_answer = parsed["final_answer"] or final_output
        except:
            final_answer = "抱歉，我无法完成这个请求。"
        
        return AgentResult(
            success=True,
            final_answer=final_answer,
            steps=steps,
            tools_used=tools_used,
            execution_time=(datetime.now() - start_time).total_seconds()
        )
    
    async def run_stream(
        self,
        user_id: str,
        user_message: str,
        context: Optional[Dict] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式运行智能体
        
        Yields:
            包含 type 和 content 的字典
            - type: 'thinking', 'action', 'observation', 'answer', 'error'
        """
        start_time = datetime.now()
        tools_used = []
        
        system_prompt = self._build_system_prompt(user_id)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        if context:
            context_str = f"\n\n用户上下文:\n{json.dumps(context, ensure_ascii=False)}"
            messages[1]["content"] += context_str
        
        for step_num in range(1, self.max_steps + 1):
            yield {"type": "step", "content": f"步骤 {step_num}"}
            
            try:
                # 流式获取 LLM 输出
                full_output = ""
                async for chunk in self._stream_llm(messages):
                    full_output += chunk
                    yield {"type": "thinking", "content": chunk}
                
                parsed = self._parse_llm_output(full_output)
                
                if parsed["final_answer"]:
                    yield {"type": "answer", "content": parsed["final_answer"]}
                    return
                
                if parsed["action"]:
                    yield {
                        "type": "action",
                        "content": f"调用工具: {parsed['action']}"
                    }
                    
                    observation = await self._execute_tool(
                        parsed["action"],
                        parsed["action_input"] or {}
                    )
                    tools_used.append(parsed["action"])
                    
                    yield {"type": "observation", "content": observation[:500]}
                    
                    messages.append({"role": "assistant", "content": full_output})
                    messages.append({"role": "user", "content": f"Observation: {observation}"})
                else:
                    messages.append({"role": "assistant", "content": full_output})
                    messages.append({
                        "role": "user",
                        "content": "请输出 Action 或 Final Answer。"
                    })
                    
            except Exception as e:
                yield {"type": "error", "content": str(e)}
                return
        
        # 强制结束
        yield {"type": "answer", "content": "已完成分析，请查看上述步骤。"}
    
    async def _stream_llm(self, messages: List[Dict]) -> AsyncGenerator[str, None]:
        """流式调用 LLM"""
        # 如果 LLM 支持流式，使用流式
        if hasattr(self.llm, 'chat_stream'):
            for chunk in self.llm.chat_stream(messages, temperature=0.7):
                if chunk.get("type") == "answer":
                    yield chunk.get("content", "")
        else:
            # 否则一次性返回
            result = self.llm.chat(messages, temperature=0.7)
            yield result
