"""
主动提问调度器
Proactive Questioner - Schedules and triggers proactive questions
"""
import asyncio
from datetime import datetime, time
from typing import Dict, Any, Optional, Callable
import threading

from .conversation_manager import ConversationManager, QuestionTrigger, get_conversation_manager


class ProactiveQuestioner:
    """主动提问调度器"""
    
    def __init__(self, conversation_manager: Optional[ConversationManager] = None):
        self.conversation_manager = conversation_manager or get_conversation_manager()
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        
        # 回调函数：当生成问题时调用
        self.on_question_generated: Optional[Callable[[str, Dict], None]] = None
        
        # 数据获取函数：获取用户当前数据
        self.get_user_data: Optional[Callable[[], Dict[str, Any]]] = None
    
    def set_question_callback(self, callback: Callable[[str, Dict], None]):
        """设置问题生成回调"""
        self.on_question_generated = callback
    
    def set_data_provider(self, provider: Callable[[], Dict[str, Any]]):
        """设置数据提供者"""
        self.get_user_data = provider
    
    def start(self):
        """启动主动提问"""
        if self.is_running:
            print("主动提问已在运行")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print("✓ 主动提问调度器已启动")
    
    def stop(self):
        """停止主动提问"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("✓ 主动提问调度器已停止")
    
    def _run_loop(self):
        """运行循环"""
        import time as time_module
        
        while self.is_running:
            try:
                # 检查是否应该提问
                if self.conversation_manager.should_ask_question():
                    self._trigger_question()
                
                # 每30分钟检查一次
                time_module.sleep(1800)
            except Exception as e:
                print(f"主动提问循环错误: {e}")
                time_module.sleep(60)
    
    def _trigger_question(self):
        """触发提问"""
        # 获取用户数据
        user_data = {}
        if self.get_user_data:
            try:
                user_data = self.get_user_data()
            except Exception as e:
                print(f"获取用户数据失败: {e}")
        
        # 确定触发类型
        trigger = self._determine_trigger(user_data)
        
        # 生成问题
        question = self.conversation_manager.generate_proactive_question(trigger, user_data)
        
        if question and self.on_question_generated:
            try:
                self.on_question_generated(question, {
                    "trigger": trigger.value,
                    "timestamp": datetime.now().isoformat(),
                    "data": user_data
                })
            except Exception as e:
                print(f"问题回调执行失败: {e}")
    
    def _determine_trigger(self, user_data: Dict[str, Any]) -> QuestionTrigger:
        """确定触发类型"""
        # 检查是否有异常
        if user_data.get('has_anomaly'):
            return QuestionTrigger.ANOMALY_BASED
        
        # 检查是否有模式
        if user_data.get('has_pattern'):
            return QuestionTrigger.PATTERN_BASED
        
        # 检查是否有重要上下文
        if user_data.get('important_context'):
            return QuestionTrigger.CONTEXT_BASED
        
        # 默认基于时间
        return QuestionTrigger.TIME_BASED
    
    def trigger_manual_question(self, trigger: QuestionTrigger, data: Dict[str, Any]) -> Optional[str]:
        """手动触发问题"""
        return self.conversation_manager.generate_proactive_question(trigger, data)


# 全局实例
_proactive_questioner = None

def get_proactive_questioner() -> ProactiveQuestioner:
    """获取主动提问调度器实例"""
    global _proactive_questioner
    if _proactive_questioner is None:
        _proactive_questioner = ProactiveQuestioner()
    return _proactive_questioner
