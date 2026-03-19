"""
对话管理器 - 实现主动提问和上下文管理
Conversation Manager - Proactive questioning and context management
"""
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum

from .llm_service import get_llm_service


class QuestionTrigger(Enum):
    """提问触发器类型"""
    TIME_BASED = "time_based"  # 基于时间
    CONTEXT_BASED = "context_based"  # 基于上下文
    PATTERN_BASED = "pattern_based"  # 基于模式
    ANOMALY_BASED = "anomaly_based"  # 基于异常


class ConversationManager:
    """对话管理器"""
    
    def __init__(self):
        self.llm = get_llm_service()
        self.conversation_history: List[Dict[str, Any]] = []
        self.user_context: Dict[str, Any] = {}
        self.last_question_time: Optional[datetime] = None
        
        # 主动提问配置
        self.question_intervals = {
            "morning": timedelta(hours=2),  # 早上每2小时
            "afternoon": timedelta(hours=3),  # 下午每3小时
            "evening": timedelta(hours=4)  # 晚上每4小时
        }
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """添加消息到对话历史"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.conversation_history.append(message)
    
    def update_context(self, context: Dict[str, Any]):
        """更新用户上下文"""
        self.user_context.update(context)
    
    def should_ask_question(self) -> bool:
        """判断是否应该主动提问"""
        if not self.last_question_time:
            return True
        
        # 获取当前时间段
        current_hour = datetime.now().hour
        if 6 <= current_hour < 12:
            period = "morning"
        elif 12 <= current_hour < 18:
            period = "afternoon"
        else:
            period = "evening"
        
        # 检查是否到了提问时间
        interval = self.question_intervals[period]
        time_since_last = datetime.now() - self.last_question_time
        
        return time_since_last >= interval
    
    def generate_proactive_question(self, trigger: QuestionTrigger, data: Dict[str, Any]) -> Optional[str]:
        """
        生成主动提问
        
        Args:
            trigger: 触发器类型
            data: 相关数据
        
        Returns:
            生成的问题
        """
        if not self.llm:
            return None
        
        # 构建提示词
        if trigger == QuestionTrigger.TIME_BASED:
            prompt = self._build_time_based_prompt(data)
        elif trigger == QuestionTrigger.CONTEXT_BASED:
            prompt = self._build_context_based_prompt(data)
        elif trigger == QuestionTrigger.PATTERN_BASED:
            prompt = self._build_pattern_based_prompt(data)
        elif trigger == QuestionTrigger.ANOMALY_BASED:
            prompt = self._build_anomaly_based_prompt(data)
        else:
            return None
        
        messages = [
            {"role": "system", "content": "你是一个关心用户健康和生活质量的AI助手。请生成一个自然、友好的问题，帮助用户反思和改善。问题要简短（不超过30字），不要说教。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            question = self.llm.chat(messages, temperature=0.8)
            self.last_question_time = datetime.now()
            self.add_message("assistant", question, {"trigger": trigger.value})
            return question
        except Exception as e:
            print(f"生成问题失败: {e}")
            return None
    
    def _build_time_based_prompt(self, data: Dict[str, Any]) -> str:
        """构建基于时间的提问提示词"""
        current_hour = datetime.now().hour
        
        if 6 <= current_hour < 9:
            return f"""
现在是早上 {current_hour} 点。用户刚起床不久。
昨晚睡眠: {data.get('sleep_hours', '未知')} 小时
今天计划: {data.get('today_plan', '未知')}

请生成一个问题，了解用户的早晨状态和今天的计划。
"""
        elif 12 <= current_hour < 14:
            return f"""
现在是中午 {current_hour} 点。
上午工作时长: {data.get('morning_work_hours', '未知')} 小时
压力水平: {data.get('stress_level', '未知')}

请生成一个问题，关心用户的午休和下午计划。
"""
        elif 18 <= current_hour < 21:
            return f"""
现在是傍晚 {current_hour} 点。
今天工作时长: {data.get('work_hours', '未知')} 小时
运动情况: {data.get('exercise_done', '未知')}

请生成一个问题，了解用户的晚间安排和放松计划。
"""
        else:
            return f"""
现在是晚上 {current_hour} 点。
今天总结: {data.get('day_summary', '未知')}

请生成一个问题，帮助用户反思今天并准备休息。
"""
    
    def _build_context_based_prompt(self, data: Dict[str, Any]) -> str:
        """构建基于上下文的提问提示词"""
        return f"""
用户当前状态:
- 最近活动: {data.get('recent_activity', '未知')}
- 情绪状态: {data.get('mood', '未知')}
- 待办事项: {data.get('pending_tasks', 0)} 个

请根据用户当前状态，生成一个有针对性的问题。
"""
    
    def _build_pattern_based_prompt(self, data: Dict[str, Any]) -> str:
        """构建基于模式的提问提示词"""
        pattern = data.get('pattern', {})
        return f"""
发现用户行为模式:
- 模式类型: {pattern.get('type', '未知')}
- 持续时间: {pattern.get('duration', '未知')}
- 影响: {pattern.get('impact', '未知')}

请生成一个问题，帮助用户意识到这个模式并思考改进。
"""
    
    def _build_anomaly_based_prompt(self, data: Dict[str, Any]) -> str:
        """构建基于异常的提问提示词"""
        anomaly = data.get('anomaly', {})
        return f"""
检测到异常情况:
- 异常类型: {anomaly.get('type', '未知')}
- 偏离程度: {anomaly.get('deviation', '未知')}
- 可能原因: {anomaly.get('possible_cause', '未知')}

请生成一个关心的问题，了解用户是否遇到了什么问题。
"""
    
    def chat(self, user_message: str, context: Optional[Dict] = None) -> str:
        """
        对话接口
        
        Args:
            user_message: 用户消息
            context: 额外上下文
        
        Returns:
            AI回复
        """
        if not self.llm:
            return "AI服务未配置，请检查环境变量。"
        
        # 添加用户消息
        self.add_message("user", user_message, context)
        
        # 更新上下文
        if context:
            self.update_context(context)
        
        # 构建消息历史（保留最近10条）
        recent_history = self.conversation_history[-10:]
        messages = [
            {"role": "system", "content": self._build_system_prompt()}
        ]
        
        for msg in recent_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # 调用LLM
        try:
            response = self.llm.chat(messages, temperature=0.7)
            self.add_message("assistant", response)
            return response
        except Exception as e:
            error_msg = f"对话失败: {str(e)}"
            print(error_msg)
            return error_msg
    
    def chat_stream(self, user_message: str, context: Optional[Dict] = None):
        """
        流式对话接口
        
        Args:
            user_message: 用户消息
            context: 额外上下文
        
        Yields:
            流式响应
        """
        if not self.llm:
            yield {"type": "error", "content": "AI服务未配置"}
            return
        
        # 添加用户消息
        self.add_message("user", user_message, context)
        
        # 更新上下文
        if context:
            self.update_context(context)
        
        # 构建消息历史
        recent_history = self.conversation_history[-10:]
        messages = [
            {"role": "system", "content": self._build_system_prompt()}
        ]
        
        for msg in recent_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # 流式调用
        full_response = ""
        for chunk in self.llm.chat_stream(messages, temperature=0.7):
            if chunk["type"] == "answer":
                full_response += chunk["content"]
            yield chunk
        
        # 保存完整回复
        if full_response:
            self.add_message("assistant", full_response)
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        context_str = ""
        if self.user_context:
            context_str = f"\n\n用户上下文:\n{json.dumps(self.user_context, ensure_ascii=False, indent=2)}"
        
        return f"""你是 LifeSwarm 的AI助手，一个关心用户全面健康和生活质量的智能伙伴。

你的特点:
1. 专业但不说教 - 提供科学建议，但语气友好温和
2. 主动但不打扰 - 适时关心，但尊重用户空间
3. 个性化 - 基于用户数据提供针对性建议
4. 全面关注 - 关注健康、时间、情绪、社交、财务、学习等多个维度

你的能力:
- 分析用户的健康数据和生活模式
- 发现潜在问题和改进机会
- 提供可操作的具体建议
- 解释复杂的数据模式
- 鼓励和支持用户的积极改变

对话风格:
- 简洁明了，避免冗长
- 温暖友好，有同理心
- 实用为主，少讲大道理
- 适当使用emoji增加亲和力{context_str}
"""
    
    def get_conversation_summary(self) -> str:
        """获取对话摘要"""
        if not self.llm or len(self.conversation_history) < 3:
            return "对话历史不足"
        
        # 提取最近的对话
        recent = self.conversation_history[-10:]
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in recent
        ])
        
        messages = [
            {"role": "system", "content": "请用2-3句话总结以下对话的主要内容和结论。"},
            {"role": "user", "content": conversation_text}
        ]
        
        try:
            return self.llm.chat(messages, temperature=0.5)
        except Exception as e:
            return f"生成摘要失败: {e}"
    
    def save_conversation(self, filepath: str):
        """保存对话历史"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'history': self.conversation_history,
                'context': self.user_context,
                'last_question_time': self.last_question_time.isoformat() if self.last_question_time else None
            }, f, ensure_ascii=False, indent=2)
    
    def load_conversation(self, filepath: str):
        """加载对话历史"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.conversation_history = data.get('history', [])
                self.user_context = data.get('context', {})
                last_time = data.get('last_question_time')
                if last_time:
                    self.last_question_time = datetime.fromisoformat(last_time)
        except Exception as e:
            print(f"加载对话历史失败: {e}")


# 全局对话管理器实例
_conversation_manager = None

def get_conversation_manager() -> ConversationManager:
    """获取对话管理器实例"""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager
