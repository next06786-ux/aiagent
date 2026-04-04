"""
决策信息收集器
在决策模拟前使用 Qwen3.5-plus API 进行多轮对话，收集足够的决策信息
"""
import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.llm.llm_service import get_llm_service


class DecisionInfoCollector:
    """决策信息收集器 - 使用 Qwen3.5-plus 进行多轮对话"""
    
    def __init__(self):
        self.llm_service = get_llm_service()
        self.min_rounds = 1  # 最少对话轮数（降低要求）
        self.max_rounds = 6  # 最多对话轮数（减少）
        self.user_free_talk_phase = True  # 用户自由表达阶段
    
    def start_collection(
        self,
        user_id: str,
        initial_question: str
    ) -> Dict[str, Any]:
        """
        开始信息收集会话
        
        Args:
            user_id: 用户ID
            initial_question: 用户初始问题
        
        Returns:
            会话信息，等待用户主动描述
        """
        session_id = f"collect_{user_id}_{int(datetime.now().timestamp())}"
        
        # 初始化会话
        first_prompt = "请详细描述你的情况，包括背景、考虑因素等。"

        session = {
            "session_id": session_id,
            "user_id": user_id,
            "initial_question": initial_question,
            "conversation_history": [
                {
                    "role": "user",
                    "content": initial_question,
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "role": "assistant",
                    "content": first_prompt,
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "collected_info": {
                "decision_context": {},  # 决策背景
                "user_constraints": {},  # 用户约束条件
                "priorities": {},  # 优先级
                "concerns": [],  # 顾虑
                "options_mentioned": []  # 提到的选项
            },
            "current_round": 0,
            "is_complete": False,
            "phase": "user_free_talk",  # 阶段：user_free_talk（用户自由表达）或 ai_questioning（AI提问）
            "user_said_no_more": False,  # 用户是否说没有更多要补充的
            "created_at": datetime.now().isoformat()
        }
        
        # 保存会话（异步优化：先返回，后台保存）
        self._save_session(session)
        
        # 异步持久化消息（不阻塞返回）
        import threading
        threading.Thread(target=self._persist_message_async, args=(
            user_id, session_id, "user", initial_question, {"phase": "init"}
        )).start()
        threading.Thread(target=self._persist_message_async, args=(
            user_id, session_id, "assistant", first_prompt, {"phase": "user_free_talk"}
        )).start()
        
        return {
            "session_id": session_id,
            "message": first_prompt,
            "phase": "user_free_talk",
            "round": 0
        }
    
    def continue_collection(
        self,
        session_id: str,
        user_response: str
    ) -> Dict[str, Any]:
        """
        继续信息收集
        
        Args:
            session_id: 会话ID
            user_response: 用户回答
        
        Returns:
            下一个AI问题或完成信号
        """
        import time
        start_time = time.time()
        
        # 加载会话
        session = self._load_session(session_id)
        if not session:
            raise ValueError(f"会话不存在: {session_id}")
        
        print(f"[信息收集] 加载会话耗时: {time.time() - start_time:.2f}秒")
        
        # 记录用户回答
        session["conversation_history"].append({
            "role": "user",
            "content": user_response,
            "timestamp": datetime.now().isoformat()
        })
        self._persist_message(
            session["user_id"],
            session_id,
            "user",
            user_response,
            {"phase": session.get("phase", "unknown"), "round": session["current_round"] + 1}
        )
        
        session["current_round"] += 1
        
        # 提取信息
        extract_start = time.time()
        self._extract_info_from_response(session, user_response)
        print(f"[信息收集] 提取信息耗时: {time.time() - extract_start:.2f}秒")
        
        # 判断当前阶段
        if session["phase"] == "user_free_talk":
            # 用户自由表达阶段
            # 检查用户是否表示没有更多要说的
            if self._user_indicates_no_more(user_response):
                # 用户表示没有更多信息，进入AI提问阶段
                session["phase"] = "ai_questioning"
                session["user_said_no_more"] = True
                
                # 生成第一个针对性问题
                question_start = time.time()
                next_question = self._generate_targeted_question(session)
                print(f"[信息收集] 生成针对性问题耗时: {time.time() - question_start:.2f}秒")
                
                session["conversation_history"].append({
                    "role": "assistant",
                    "content": next_question,
                    "timestamp": datetime.now().isoformat()
                })
                self._persist_message(
                    session["user_id"],
                    session_id,
                    "assistant",
                    next_question,
                    {"phase": "ai_questioning", "round": session["current_round"] + 1}
                )
                
                self._save_session(session)
                
                return {
                    "session_id": session_id,
                    "ai_question": next_question,
                    "phase": "ai_questioning",
                    "round": session["current_round"] + 1,
                    "is_complete": False
                }
            else:
                # 继续让用户自由表达，使用更自然的跟进方式
                followup_start = time.time()
                follow_up = self._generate_free_talk_followup(session)
                print(f"[信息收集] 生成跟进问题耗时: {time.time() - followup_start:.2f}秒")
                
                session["conversation_history"].append({
                    "role": "assistant",
                    "content": follow_up,
                    "timestamp": datetime.now().isoformat()
                })
                self._persist_message(
                    session["user_id"],
                    session_id,
                    "assistant",
                    follow_up,
                    {"phase": "user_free_talk", "round": session["current_round"] + 1}
                )
                
                self._save_session(session)
                
                print(f"[信息收集] 总耗时: {time.time() - start_time:.2f}秒")
                
                return {
                    "session_id": session_id,
                    "ai_question": follow_up,
                    "phase": "user_free_talk",
                    "round": session["current_round"] + 1,
                    "is_complete": False
                }
        
        else:  # ai_questioning 阶段
            # AI提问阶段
            
            # 检查用户是否要求直接开始决策（即使在AI提问阶段）
            if self._user_wants_to_skip(user_response):
                session["is_complete"] = True
                self._save_session(session)
                
                return {
                    "session_id": session_id,
                    "is_complete": True,
                    "collected_info": session["collected_info"],
                    "summary": "用户选择直接开始决策模拟。"
                }
            
            # 判断是否收集足够信息
            if self._is_info_sufficient(session):
                session["is_complete"] = True
                self._save_session(session)
                
                return {
                    "session_id": session_id,
                    "is_complete": True,
                    "collected_info": session["collected_info"],
                    "summary": self._generate_summary(session)
                }
            
            # 生成下一个问题
            next_question = self._generate_next_question(session)
            
            session["conversation_history"].append({
                "role": "assistant",
                "content": next_question,
                "timestamp": datetime.now().isoformat()
            })
            self._persist_message(
                session["user_id"],
                session_id,
                "assistant",
                next_question,
                {"phase": "ai_questioning", "round": session["current_round"] + 1}
            )
            
            # 保存会话
            self._save_session(session)
            
            return {
                "session_id": session_id,
                "ai_question": next_question,
                "phase": "ai_questioning",
                "round": session["current_round"] + 1,
                "is_complete": False
            }
    
    def _user_indicates_no_more(self, user_response: str) -> bool:
        """
        判断用户是否表示没有更多要补充的，或者要求直接开始决策
        
        Args:
            user_response: 用户回答
        
        Returns:
            True 如果用户表示没有更多信息或要求直接开始
        """
        response_lower = user_response.lower().strip()
        
        # 用户要求直接开始决策的表达
        start_decision_indicators = [
            "直接开始", "开始决策", "开始模拟", "直接模拟",
            "不用问了", "别问了", "够了", "可以了",
            "开始吧", "直接来", "快点开始", "马上开始",
            "跳过", "不需要", "不用了", "算了",
            "start now", "let's start", "begin", "skip"
        ]
        
        # 检查是否要求直接开始
        for indicator in start_decision_indicators:
            if indicator in response_lower:
                return True
        
        # 常见的"没有了"表达
        no_more_indicators = [
            "没有了", "没了", "没有", "没啥了", "就这些",
            "暂时没有", "目前没有", "应该没有了", "差不多了",
            "这些就够了", "就这样", "没什么了", "没其他的了",
            "no more", "nothing more", "that's all", "that's it",
            "没有其他", "没有别的", "想不到了", "没想到其他的"
        ]
        
        # 检查是否包含这些表达
        for indicator in no_more_indicators:
            if indicator in response_lower:
                return True
        
        # 如果回答很短（少于10个字符），也可能表示没有更多
        if len(user_response.strip()) < 10 and any(word in response_lower for word in ["没", "无", "不", "no"]):
            return True
        
        return False
    
    def _user_wants_to_skip(self, user_response: str) -> bool:
        """
        判断用户是否想要跳过剩余问题，直接开始决策
        
        Args:
            user_response: 用户回答
        
        Returns:
            True 如果用户想要跳过
        """
        response_lower = user_response.lower().strip()
        
        # 强烈的跳过意图
        skip_indicators = [
            "直接开始", "开始决策", "开始模拟", "直接模拟",
            "不用问了", "别问了", "够了", "可以开始了",
            "开始吧", "直接来", "快点开始", "马上开始",
            "跳过", "不需要问", "不用再问", "别再问了",
            "信息够了", "足够了", "这些够了",
            "start", "skip", "enough", "let's go"
        ]
        
        for indicator in skip_indicators:
            if indicator in response_lower:
                return True
        
        return False
    
    def _generate_targeted_question(self, session: Dict) -> str:
        """
        生成针对性问题（在用户自由表达后）
        
        Args:
            session: 会话信息
        
        Returns:
            针对性问题
        """
        if not self.llm_service or not self.llm_service.enabled:
            return self._get_first_targeted_question(session)
        
        try:
            print(f"[信息收集] 开始调用LLM生成针对性问题...")
            user_statements = [
                msg["content"] for msg in session["conversation_history"] 
                if msg["role"] == "user"
            ]
            user_content = "\n".join(user_statements)
            
            messages = [
                {
                    "role": "system",
                    "content": """你是一个真正会聊天的决策顾问，不要像问卷调查，不要机械列点。用户已经主动说了一些背景，你现在只提一个最自然、最有帮助的追问。\n\n要求：\n1. 像真实顾问聊天，不要模板化。\n2. 优先问最影响决策方向的缺失信息。\n3. 问题要短、自然、具体。\n4. 不要一次问很多小问题。\n5. 只输出一句追问。"""
                },
                {
                    "role": "user",
                    "content": f"""用户的决策问题：{session['initial_question']}\n\n用户已经说的内容：\n{user_content}\n\n请生成一个自然的追问。"""
                }
            ]
            
            response = self.llm_service.chat(messages, temperature=0.8)
            print(f"[信息收集] LLM生成针对性问题完成")
            return response.strip()
            
        except Exception as e:
            print(f"⚠️ 生成针对性问题失败: {e}")
            return self._get_first_targeted_question(session)

    def _generate_free_talk_followup(self, session: Dict) -> str:
        if not self.llm_service or not self.llm_service.enabled:
            if session["current_round"] == 1:
                return "你刚才提到的情况里，哪一点最让你纠结？"
            return "如果继续往下想，你觉得真正卡住你的核心点是什么？"

        try:
            user_statements = [
                msg["content"] for msg in session["conversation_history"]
                if msg["role"] == "user"
            ]
            user_content = "\n".join(user_statements[-3:])
            messages = [
                {
                    "role": "system",
                    "content": "你是一个自然、灵活的决策顾问。用户还在自由表达阶段，你的任务不是按模板追问，而是顺着用户刚才的话接一句最自然的跟进。不要官话，不要 checklist。只输出一句话。"
                },
                {
                    "role": "user",
                    "content": f"决策问题：{session['initial_question']}\n\n用户最近表达：\n{user_content}\n\n请给一句自然跟进。"
                }
            ]
            response = self.llm_service.chat(messages, temperature=0.85)
            return response.strip()
        except Exception:
            if session["current_round"] == 1:
                return "你刚才提到的情况里，哪一点最让你纠结？"
            return "如果继续往下想，你觉得真正卡住你的核心点是什么？"
    
    def _get_first_targeted_question(self, session: Dict) -> str:
        """获取第一个备用针对性问题"""
        collected = session["collected_info"]
        
        # 根据已收集的信息决定问什么
        if not collected.get("user_constraints"):
            return "你在做这个决策时，有什么限制条件吗？比如时间、资金、能力等方面。"
        elif not collected.get("priorities"):
            return "在做决策时，你最看重哪些方面？比如收入、发展空间、稳定性、兴趣等。"
        elif not collected.get("concerns"):
            return "你对这个决策有什么主要的顾虑或担心吗？"
        else:
            return "你理想中的结果是什么样的？"
    
    def _generate_first_question(self, initial_question: str) -> str:
        """生成第一个AI问题"""
        if not self.llm_service or not self.llm_service.enabled:
            return "请详细描述一下你的情况，包括你的背景、目标和主要考虑因素。"
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": "你是一个专业的决策顾问。用户向你咨询决策问题，你需要通过提问来收集足够的信息，以便后续进行深入的决策分析。你的问题应该：1) 开放式，鼓励用户详细表达 2) 聚焦关键信息 3) 友好且专业。"
                },
                {
                    "role": "user",
                    "content": f"用户的初始问题是：「{initial_question}」\n\n请生成第一个问题，了解用户的基本情况和决策背景。只返回问题本身，不要有其他内容。"
                }
            ]
            
            response = self.llm_service.chat(messages, temperature=0.7)
            return response.strip()
            
        except Exception as e:
            print(f"⚠️ 生成第一个问题失败: {e}")
            return "请详细描述一下你的情况，包括你的背景、目标和主要考虑因素。"
    
    def _generate_next_question(self, session: Dict) -> str:
        """生成下一个AI问题"""
        if not self.llm_service or not self.llm_service.enabled:
            return self._get_fallback_question(session)
        
        try:
            conversation_summary = self._summarize_conversation(session)
            missing_info = self._identify_missing_info(session)
            
            messages = [
                {
                    "role": "system",
                    "content": "你是一个自然、有判断力的决策顾问。你已经听过用户前面的表达，现在只提一个最值得问的追问。不要像表单，不要复读用户说过的话，不要列很多点。语气要像真实聊天。只输出一句话。"
                },
                {
                    "role": "user",
                    "content": f"""初始问题：{session['initial_question']}

对话摘要：
{conversation_summary}

仍然缺的信息：
{missing_info}

请给出一个自然追问。"""
                }
            ]
            
            response = self.llm_service.chat(messages, temperature=0.8)
            return response.strip()
            
        except Exception as e:
            print(f"⚠️ 生成下一个问题失败: {e}")
            return self._get_fallback_question(session)
    
    def _extract_info_from_response(self, session: Dict, user_response: str):
        """从用户回答中提取信息"""
        if not self.llm_service or not self.llm_service.enabled:
            return
        
        try:
            print(f"[信息收集] 开始调用LLM提取信息...")
            messages = [
                {
                    "role": "system",
                    "content": """你是一个信息提取专家。从用户的回答中提取关键信息，以JSON格式返回。

返回格式：
{
  "decision_context": {"key": "value"},  // 决策背景信息
  "constraints": ["约束1", "约束2"],  // 限制条件
  "priorities": ["优先级1", "优先级2"],  // 重要性排序
  "concerns": ["顾虑1", "顾虑2"],  // 担心的问题
  "options": ["选项1", "选项2"]  // 提到的选项
}"""
                },
                {
                    "role": "user",
                    "content": f"用户回答：{user_response}\n\n请提取关键信息。"
                }
            ]
            
            response = self.llm_service.chat(messages, temperature=0.3, response_format="json_object")
            print(f"[信息收集] LLM提取信息完成")
            extracted = json.loads(response)
            
            # 合并到已收集的信息中
            if "decision_context" in extracted:
                session["collected_info"]["decision_context"].update(extracted["decision_context"])
            
            if "constraints" in extracted:
                for constraint in extracted["constraints"]:
                    if constraint not in session["collected_info"]["user_constraints"]:
                        session["collected_info"]["user_constraints"][f"constraint_{len(session['collected_info']['user_constraints'])}"] = constraint
            
            if "priorities" in extracted:
                for priority in extracted["priorities"]:
                    if priority not in session["collected_info"]["priorities"]:
                        session["collected_info"]["priorities"][f"priority_{len(session['collected_info']['priorities'])}"] = priority
            
            if "concerns" in extracted:
                session["collected_info"]["concerns"].extend(
                    [c for c in extracted["concerns"] if c not in session["collected_info"]["concerns"]]
                )
            
            if "options" in extracted:
                session["collected_info"]["options_mentioned"].extend(
                    [o for o in extracted["options"] if o not in session["collected_info"]["options_mentioned"]]
                )
            
        except Exception as e:
            print(f"⚠️ 信息提取失败: {e}")
    
    def _is_info_sufficient(self, session: Dict) -> bool:
        """判断信息是否足够"""
        # 至少进行最少轮数
        if session["current_round"] < self.min_rounds:
            return False
        
        # 达到最大轮数
        if session["current_round"] >= self.max_rounds:
            return True
        
        # 检查关键信息是否收集完整（降低要求）
        info = session["collected_info"]
        
        # 只要有基本的决策背景就可以开始
        has_basic_info = (
            len(info["decision_context"]) >= 1 or
            len(info["user_constraints"]) >= 1 or
            len(info["priorities"]) >= 1 or
            len(info["options_mentioned"]) >= 1
        )
        
        # 如果已经有一些信息，就认为足够了
        if session["current_round"] >= 2 and has_basic_info:
            return True
        
        # 更严格的完整性检查（可选）
        has_context = len(info["decision_context"]) >= 1
        has_constraints = len(info["user_constraints"]) >= 1
        has_priorities = len(info["priorities"]) >= 1
        
        return has_context and (has_constraints or has_priorities)
    
    def _summarize_conversation(self, session: Dict) -> str:
        """总结对话内容"""
        history = session["conversation_history"]
        if not history:
            return "暂无对话"
        
        summary_parts = []
        for i, msg in enumerate(history[-4:], 1):  # 只看最近4条
            role = "用户" if msg["role"] == "user" else "AI"
            content = msg["content"][:100]  # 截断
            summary_parts.append(f"{role}: {content}")
        
        return "\n".join(summary_parts)
    
    def _identify_missing_info(self, session: Dict) -> str:
        """识别缺失的信息"""
        info = session["collected_info"]
        missing = []
        
        if len(info["decision_context"]) < 2:
            missing.append("- 决策背景和个人情况")
        
        if len(info["user_constraints"]) < 1:
            missing.append("- 限制条件（时间、金钱、能力等）")
        
        if len(info["priorities"]) < 1:
            missing.append("- 优先考虑的因素")
        
        if len(info["concerns"]) < 1:
            missing.append("- 主要顾虑和担心")
        
        if len(info["options_mentioned"]) < 2:
            missing.append("- 具体的选项")
        
        return "\n".join(missing) if missing else "信息基本完整"
    
    def _get_fallback_question(self, session: Dict) -> str:
        """获取备用问题（当LLM不可用时）"""
        round_num = session["current_round"]
        fallback_questions = [
            "如果现在必须做决定，你最怕承担的后果是什么？",
            "你会优先保住什么，而不是追求什么？",
            "现实里最可能卡住你的限制是什么？",
            "如果半年后回头看，你希望自己最不后悔哪一点？",
            "现在你最想再想清楚的，其实是哪一块？"
        ]
        if round_num < len(fallback_questions):
            return fallback_questions[round_num]
        return "如果再往深一层想，你觉得这个决定最难的地方到底是什么？"
    
    def _generate_summary(self, session: Dict) -> str:
        """生成信息收集总结"""
        if not self.llm_service or not self.llm_service.enabled:
            return "信息收集完成"
        
        try:
            info = session["collected_info"]
            
            messages = [
                {
                    "role": "system",
                    "content": "你是一个决策顾问。根据收集到的信息，生成一个简洁的总结，概括用户的决策情况。"
                },
                {
                    "role": "user",
                    "content": f"""初始问题：{session['initial_question']}

收集到的信息：
- 决策背景：{json.dumps(info['decision_context'], ensure_ascii=False)}
- 约束条件：{json.dumps(info['user_constraints'], ensure_ascii=False)}
- 优先级：{json.dumps(info['priorities'], ensure_ascii=False)}
- 顾虑：{info['concerns']}
- 提到的选项：{info['options_mentioned']}

请生成一个2-3句话的总结。"""
                }
            ]
            
            response = self.llm_service.chat(messages, temperature=0.7)
            return response.strip()
            
        except Exception as e:
            print(f"⚠️ 生成总结失败: {e}")
            return "信息收集完成，准备进行决策模拟。"
    
    def _save_session(self, session: Dict):
        """保存会话"""
        save_dir = "./backend/data/decision_sessions"
        os.makedirs(save_dir, exist_ok=True)
        
        filepath = os.path.join(save_dir, f"{session['session_id']}.json")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(session, f, ensure_ascii=False, indent=2)

    def _persist_message_async(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """异步持久化消息（不阻塞主流程）"""
        try:
            self._persist_message(user_id, session_id, role, content, context)
        except Exception as e:
            print(f"⚠️ 异步持久化失败（不影响主流程）: {e}")
    
    def _persist_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """将收集对话持久化到数据库，供后续 RAG / PKF / 复盘检索使用。"""
        if not content:
            return
        try:
            from backend.database.connection import db_connection
            from backend.database.models import ConversationHistory

            db = db_connection.get_session()
            db.add(ConversationHistory(
                user_id=user_id,
                role=role,
                content=content,
                context=context or {},
                timestamp=datetime.utcnow(),
                session_id=session_id
            ))
            db.commit()
            db.close()
        except Exception as e:
            print(f"⚠️ 收集会话持久化失败: {e}")
    
    def _load_session(self, session_id: str) -> Optional[Dict]:
        """加载会话"""
        filepath = f"./backend/data/decision_sessions/{session_id}.json"
        
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取会话信息"""
        return self._load_session(session_id)


# 测试代码
if __name__ == "__main__":
    collector = DecisionInfoCollector()
    
    print("="*60)
    print("决策信息收集器测试")
    print("="*60)
    
    # 开始收集
    result = collector.start_collection(
        user_id="test_user",
        initial_question="我是大三学生，毕业后不知道该考研还是工作"
    )
    
    print(f"\n会话ID: {result['session_id']}")
    print(f"第 {result['round']} 轮")
    print(f"\nAI问题: {result['ai_question']}")
    
    # 模拟用户回答
    session_id = result['session_id']
    
    test_responses = [
        "我学的是计算机专业，成绩中等，家里经济条件一般。我比较想提升学历，但也担心考不上浪费时间。",
        "我最看重的是未来的发展空间和收入，希望能有稳定的工作。时间上希望能尽快独立，不想再让家里负担。",
        "我主要担心考研失败后既浪费时间又错过校招，但直接工作又觉得学历不够竞争力不强。"
    ]
    
    for i, response in enumerate(test_responses, 2):
        print(f"\n{'='*60}")
        print(f"用户回答: {response}")
        
        result = collector.continue_collection(session_id, response)
        
        if result.get("is_complete"):
            print(f"\n{'='*60}")
            print("信息收集完成！")
            print(f"\n总结: {result['summary']}")
            print(f"\n收集到的信息:")
            print(json.dumps(result['collected_info'], ensure_ascii=False, indent=2))
            break
        else:
            print(f"\n第 {result['round']} 轮")
            print(f"AI问题: {result['ai_question']}")


    def _identify_decision_type(self, question: str) -> str:
        """识别决策类型"""
        if not self.llm_service or not self.llm_service.enabled:
            return "general"
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": """你是决策类型分类专家。根据用户的问题，判断决策类型。

可选类型：
- career: 职业发展（工作、跳槽、创业等）
- education: 教育学习（升学、培训、考证等）
- relationship: 人际关系（恋爱、婚姻、友情等）
- finance: 财务投资（理财、买房、投资等）
- lifestyle: 生活方式（搬家、旅行、兴趣等）
- health: 健康医疗（就医、健身、养生等）
- general: 通用决策（无法明确分类）

只返回类型标识，不要其他内容。"""
                },
                {
                    "role": "user",
                    "content": f"用户问题：{question}"
                }
            ]
            
            response = self.llm_service.chat(messages, temperature=0.3)
            decision_type = response.strip().lower()
            
            # 验证返回的类型
            valid_types = ["career", "education", "relationship", "finance", "lifestyle", "health", "general"]
            return decision_type if decision_type in valid_types else "general"
            
        except Exception as e:
            print(f"⚠️ 决策类型识别失败: {e}")
            return "general"
    
    def _get_decision_type_name(self, decision_type: str) -> str:
        """获取决策类型的中文名称"""
        names = {
            "career": "职业发展",
            "education": "教育学习",
            "relationship": "人际关系",
            "finance": "财务投资",
            "lifestyle": "生活方式",
            "health": "健康医疗",
            "general": "通用决策"
        }
        return names.get(decision_type, "通用决策")
    
    def _analyze_emotional_state(self, user_response: str) -> Dict[str, Any]:
        """分析用户情感状态"""
        if not self.llm_service or not self.llm_service.enabled:
            return {"emotion": "neutral", "confidence": 0.5, "urgency": "medium"}
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": """分析用户回答中的情感状态和决策紧迫性。

返回 JSON 格式：
{
  "emotion": "anxious|confident|confused|calm|excited",
  "confidence": 0.0-1.0,
  "urgency": "low|medium|high"
}"""
                },
                {
                    "role": "user",
                    "content": f"用户回答：{user_response}"
                }
            ]
            
            response = self.llm_service.chat(messages, temperature=0.3, response_format="json_object")
            return json.loads(response)
            
        except Exception as e:
            print(f"⚠️ 情感分析失败: {e}")
            return {"emotion": "neutral", "confidence": 0.5, "urgency": "medium"}
