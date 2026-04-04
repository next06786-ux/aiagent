"""
增强版决策信息收集器
优化对话策略：决策类型识别、领域适配、情感分析
"""
import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.llm.llm_service import get_llm_service


class DecisionType:
    """决策类型枚举"""
    CAREER = "career"  # 职业发展
    EDUCATION = "education"  # 教育学习
    RELATIONSHIP = "relationship"  # 人际关系
    FINANCE = "finance"  # 财务投资
    LIFESTYLE = "lifestyle"  # 生活方式
    HEALTH = "health"  # 健康医疗
    GENERAL = "general"  # 通用决策


class EnhancedInfoCollector:
    """增强版信息收集器 - 智能对话策略"""
    
    def __init__(self):
        self.llm_service = get_llm_service()
        self.min_rounds = 1
        self.max_rounds = 6
        
        # 决策类型对应的关键问题模板
        self.question_templates = {
            DecisionType.CAREER: [
                "你目前的职业状态是什么？工作多久了？",
                "这个决策对你的职业发展有什么影响？",
                "你在职业上最看重什么？薪资、成长空间还是工作环境？",
                "如果做出这个决定，你最担心失去什么？"
            ],
            DecisionType.EDUCATION: [
                "你的学习背景和当前状态是什么？",
                "这个决策会如何影响你的学习计划？",
                "你的学习目标是什么？短期还是长期？",
                "你有什么资源或限制条件？"
            ],
            DecisionType.RELATIONSHIP: [
                "这个决策涉及哪些重要的人？",
                "你和相关人员的关系如何？",
                "你最在意的是什么？关系的稳定性还是个人感受？",
                "如果做出这个决定，可能会对关系产生什么影响？"
            ],
            DecisionType.FINANCE: [
                "你目前的财务状况如何？",
                "这个决策需要多少资金投入？",
                "你的风险承受能力如何？",
                "你的财务目标是什么？短期收益还是长期增值？"
            ],
            DecisionType.LIFESTYLE: [
                "你目前的生活状态是什么样的？",
                "这个决策会如何改变你的日常生活？",
                "你理想的生活方式是什么？",
                "你愿意为这个改变付出什么代价？"
            ],
            DecisionType.HEALTH: [
                "你目前的健康状况如何？",
                "这个决策对你的健康有什么影响？",
                "你有什么健康方面的顾虑？",
                "你的医疗资源和支持系统如何？"
            ],
            DecisionType.GENERAL: [
                "请详细描述你的当前情况。",
                "这个决策对你最重要的影响是什么？",
                "你最看重哪些方面？",
                "你有什么主要的顾虑？"
            ]
        }
    
    def identify_decision_type(self, question: str) -> str:
        """识别决策类型"""
        if not self.llm_service or not self.llm_service.enabled:
            return DecisionType.GENERAL
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": f"""你是决策类型分类专家。根据用户的问题，判断决策类型。

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
            valid_types = [
                DecisionType.CAREER, DecisionType.EDUCATION, DecisionType.RELATIONSHIP,
                DecisionType.FINANCE, DecisionType.LIFESTYLE, DecisionType.HEALTH,
                DecisionType.GENERAL
            ]
            
            return decision_type if decision_type in valid_types else DecisionType.GENERAL
            
        except Exception as e:
            print(f"⚠️ 决策类型识别失败: {e}")
            return DecisionType.GENERAL
    
    def analyze_emotional_state(self, user_response: str) -> Dict[str, Any]:
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
  "urgency": "low|medium|high",
  "key_concerns": ["顾虑1", "顾虑2"]
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
    
    def generate_adaptive_question(
        self,
        session: Dict,
        decision_type: str,
        emotional_state: Dict[str, Any]
    ) -> str:
        """根据决策类型和情感状态生成自适应问题"""
        if not self.llm_service or not self.llm_service.enabled:
            # 使用模板问题
            templates = self.question_templates.get(decision_type, self.question_templates[DecisionType.GENERAL])
            round_num = session["current_round"]
            if round_num < len(templates):
                return templates[round_num]
            return "还有什么重要信息需要补充吗？"
        
        try:
            # 构建上下文
            conversation_summary = self._summarize_recent_conversation(session)
            collected_info_summary = self._summarize_collected_info(session["collected_info"])
            
            # 根据情感状态调整提问风格
            emotion = emotional_state.get("emotion", "neutral")
            urgency = emotional_state.get("urgency", "medium")
            
            style_guide = ""
            if emotion == "anxious":
                style_guide = "用户比较焦虑，用温和、支持性的语气提问，不要增加压力。"
            elif emotion == "confused":
                style_guide = "用户有些困惑，问题要具体、清晰，帮助理清思路。"
            elif emotion == "confident":
                style_guide = "用户比较自信，可以问更深入的问题，挑战其假设。"
            
            if urgency == "high":
                style_guide += " 决策紧迫，优先问最关键的信息。"
            
            messages = [
                {
                    "role": "system",
                    "content": f"""你是专业的{self._get_decision_type_name(decision_type)}决策顾问。

决策类型：{decision_type}
用户情感：{emotion}
紧迫程度：{urgency}

{style_guide}

要求：
1. 问题要自然、有针对性
2. 一次只问一个核心问题
3. 避免模板化、机械化
4. 根据用户状态调整语气"""
                },
                {
                    "role": "user",
                    "content": f"""初始问题：{session['initial_question']}

最近对话：
{conversation_summary}

已收集信息：
{collected_info_summary}

请生成下一个问题。"""
                }
            ]
            
            response = self.llm_service.chat(messages, temperature=0.8)
            return response.strip()
            
        except Exception as e:
            print(f"⚠️ 生成自适应问题失败: {e}")
            templates = self.question_templates.get(decision_type, self.question_templates[DecisionType.GENERAL])
            round_num = session["current_round"]
            if round_num < len(templates):
                return templates[round_num]
            return "还有什么重要信息需要补充吗？"
    
    def extract_structured_info(self, user_response: str, decision_type: str) -> Dict[str, Any]:
        """根据决策类型提取结构化信息"""
        if not self.llm_service or not self.llm_service.enabled:
            return {}
        
        try:
            # 根据决策类型定制提取模板
            extraction_schema = self._get_extraction_schema(decision_type)
            
            messages = [
                {
                    "role": "system",
                    "content": f"""从用户回答中提取关键信息。

决策类型：{decision_type}

提取模式：
{extraction_schema}

返回 JSON 格式。"""
                },
                {
                    "role": "user",
                    "content": f"用户回答：{user_response}"
                }
            ]
            
            response = self.llm_service.chat(messages, temperature=0.3, response_format="json_object")
            return json.loads(response)
            
        except Exception as e:
            print(f"⚠️ 结构化信息提取失败: {e}")
            return {}
    
    def _get_decision_type_name(self, decision_type: str) -> str:
        """获取决策类型的中文名称"""
        names = {
            DecisionType.CAREER: "职业发展",
            DecisionType.EDUCATION: "教育学习",
            DecisionType.RELATIONSHIP: "人际关系",
            DecisionType.FINANCE: "财务投资",
            DecisionType.LIFESTYLE: "生活方式",
            DecisionType.HEALTH: "健康医疗",
            DecisionType.GENERAL: "通用"
        }
        return names.get(decision_type, "通用")
    
    def _get_extraction_schema(self, decision_type: str) -> str:
        """获取决策类型对应的信息提取模式"""
        schemas = {
            DecisionType.CAREER: """
{
  "current_position": "当前职位",
  "years_experience": "工作年限",
  "salary_range": "薪资范围",
  "career_goals": ["目标1", "目标2"],
  "constraints": ["限制1", "限制2"],
  "priorities": ["优先级1", "优先级2"]
}""",
            DecisionType.FINANCE: """
{
  "financial_status": "财务状况",
  "investment_amount": "投资金额",
  "risk_tolerance": "风险承受能力",
  "time_horizon": "投资期限",
  "financial_goals": ["目标1", "目标2"]
}""",
            DecisionType.GENERAL: """
{
  "decision_context": {"key": "value"},
  "constraints": ["约束1", "约束2"],
  "priorities": ["优先级1", "优先级2"],
  "concerns": ["顾虑1", "顾虑2"],
  "options": ["选项1", "选项2"]
}"""
        }
        return schemas.get(decision_type, schemas[DecisionType.GENERAL])
    
    def _summarize_recent_conversation(self, session: Dict) -> str:
        """总结最近的对话"""
        history = session["conversation_history"]
        if not history:
            return "暂无对话"
        
        recent = history[-4:]  # 最近4条
        summary_parts = []
        for msg in recent:
            role = "用户" if msg["role"] == "user" else "AI"
            content = msg["content"][:80]
            summary_parts.append(f"{role}: {content}")
        
        return "\n".join(summary_parts)
    
    def _summarize_collected_info(self, collected_info: Dict) -> str:
        """总结已收集的信息"""
        parts = []
        
        if collected_info.get("decision_context"):
            parts.append(f"背景：{len(collected_info['decision_context'])} 项")
        
        if collected_info.get("user_constraints"):
            parts.append(f"约束：{len(collected_info['user_constraints'])} 项")
        
        if collected_info.get("priorities"):
            parts.append(f"优先级：{len(collected_info['priorities'])} 项")
        
        if collected_info.get("concerns"):
            parts.append(f"顾虑：{', '.join(collected_info['concerns'][:3])}")
        
        if collected_info.get("options_mentioned"):
            parts.append(f"选项：{', '.join(collected_info['options_mentioned'])}")
        
        return " | ".join(parts) if parts else "暂无"
