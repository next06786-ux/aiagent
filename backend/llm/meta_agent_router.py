"""
元智能体路由器
根据用户问题的类型，路由到不同的领域分析器
"""

from typing import Dict, List, Any, Tuple
from enum import Enum
import json


class DomainType(Enum):
    """领域类型"""
    HEALTH = "health"
    TIME = "time"
    EMOTION = "emotion"
    SOCIAL = "social"
    FINANCE = "finance"
    LEARNING = "learning"
    MULTI_DOMAIN = "multi_domain"
    GENERAL = "general"


class MetaAgentRouter:
    """元智能体路由器"""
    
    def __init__(self):
        """初始化路由器"""
        # 定义领域关键词
        self.domain_keywords = {
            DomainType.HEALTH: [
                "睡眠", "运动", "健康", "压力", "免疫", "心率", "步数",
                "锻炼", "身体", "疾病", "症状", "医生", "药物", "饮食",
                "体重", "血压", "血糖", "疲劳", "精力"
            ],
            DomainType.TIME: [
                "时间", "效率", "专注", "任务", "工作", "完成", "截止",
                "计划", "日程", "安排", "拖延", "时间管理", "生产力",
                "认知负荷", "中断", "压力", "忙碌"
            ],
            DomainType.EMOTION: [
                "心情", "情绪", "感受", "开心", "难过", "焦虑", "抑郁",
                "压力", "紧张", "放松", "冥想", "调节", "稳定", "波动",
                "快乐", "悲伤", "愤怒", "恐惧"
            ],
            DomainType.SOCIAL: [
                "社交", "朋友", "家人", "关系", "孤独", "满意", "互动",
                "沟通", "陪伴", "聚会", "约会", "团队", "同事", "人际",
                "连接", "归属", "支持"
            ],
            DomainType.FINANCE: [
                "金钱", "财务", "储蓄", "消费", "收入", "支出", "投资",
                "债务", "预算", "理财", "经济", "成本", "价格", "购买",
                "赚钱", "花钱", "财富"
            ],
            DomainType.LEARNING: [
                "学习", "教育", "知识", "技能", "进度", "考试", "成绩",
                "课程", "培训", "阅读", "研究", "理解", "记忆", "掌握",
                "学生", "学科", "目标"
            ]
        }
        
        # 定义领域权重
        self.domain_weights = {
            DomainType.HEALTH: 1.0,
            DomainType.TIME: 1.0,
            DomainType.EMOTION: 1.0,
            DomainType.SOCIAL: 1.0,
            DomainType.FINANCE: 1.0,
            DomainType.LEARNING: 1.0
        }
    
    def route(self, user_message: str, user_context: Dict[str, Any] = None) -> Tuple[List[DomainType], Dict[str, float]]:
        """
        路由用户消息到相应的领域
        
        Args:
            user_message: 用户消息
            user_context: 用户上下文（可选）
        
        Returns:
            (主要领域列表, 领域权重字典)
        """
        # 🔥 优先使用LLM进行智能路由
        try:
            from llm.llm_service import get_llm_service
            llm_service = get_llm_service()
            
            if llm_service and llm_service.enabled:
                print(f"🤖 使用LLM进行智能路由分析...")
                domain_scores = self._llm_route(user_message, user_context, llm_service)
                primary_domains = self._select_primary_domains(domain_scores)
                print(f"✅ LLM路由完成，主要领域: {[d.value for d in primary_domains]}")
                return primary_domains, domain_scores
        except Exception as e:
            print(f"⚠️ LLM路由失败: {e}，回退到关键词匹配")
            import traceback
            traceback.print_exc()
        
        # 回退到关键词匹配
        print(f"📝 使用关键词匹配进行路由...")
        domain_scores = self._calculate_domain_scores(user_message, user_context)
        primary_domains = self._select_primary_domains(domain_scores)
        
        return primary_domains, domain_scores
    
    def _llm_route(self, user_message: str, user_context: Dict[str, Any], llm_service) -> Dict[DomainType, float]:
        """
        使用LLM进行智能路由
        
        Args:
            user_message: 用户消息
            user_context: 用户上下文
            llm_service: LLM服务
        
        Returns:
            领域匹配度字典
        """
        # 构建提示词
        prompt = f"""你是一个专业的问题分类专家。请分析用户的问题，判断它属于以下哪些生活领域，并给出每个领域的相关度评分（0-1之间的小数）。

生活领域定义：
1. health（健康）：睡眠、运动、身体健康、压力、免疫力、心率、饮食、体重等
2. time（时间）：时间管理、效率、专注、任务、工作、计划、日程、拖延等
3. emotion（情绪）：心情、情绪、感受、焦虑、抑郁、压力、放松、冥想等
4. social（社交）：社交、朋友、家人、关系、孤独、互动、沟通、陪伴等
5. finance（财务）：金钱、财务、储蓄、消费、收入、支出、投资、理财等
6. learning（学习）：学习、教育、知识、技能、进度、考试、课程、培训等

用户问题：{user_message}

请以JSON格式返回分析结果，格式如下：
{{
    "health": 0.8,
    "time": 0.3,
    "emotion": 0.5,
    "social": 0.1,
    "finance": 0.0,
    "learning": 0.2
}}

注意：
- 评分范围是0-1之间的小数
- 一个问题可以涉及多个领域
- 如果某个领域完全不相关，评分为0
- 主要相关的领域评分应该在0.5以上
- 只返回JSON，不要其他解释
"""
        
        # 调用LLM
        messages = [
            {"role": "system", "content": "你是一个专业的问题分类专家，擅长分析用户问题并准确分类到不同的生活领域。"},
            {"role": "user", "content": prompt}
        ]
        
        response = llm_service.chat(messages, temperature=0.3)
        
        # 解析响应
        try:
            # 提取JSON部分
            response_text = response.strip()
            
            # 尝试找到JSON块
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            
            # 解析JSON
            scores_dict = json.loads(response_text)
            
            # 转换为DomainType字典
            domain_scores = {}
            for domain_str, score in scores_dict.items():
                try:
                    domain = DomainType(domain_str)
                    domain_scores[domain] = float(score)
                except (ValueError, KeyError):
                    print(f"⚠️ 未知领域: {domain_str}")
            
            # 确保所有领域都有分数
            for domain in DomainType:
                if domain not in domain_scores and domain not in [DomainType.MULTI_DOMAIN, DomainType.GENERAL]:
                    domain_scores[domain] = 0.0
            
            print(f"📊 LLM路由结果: {[(d.value, f'{s:.2f}') for d, s in domain_scores.items() if s > 0]}")
            
            return domain_scores
            
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON解析失败: {e}")
            print(f"原始响应: {response}")
            raise
        except Exception as e:
            print(f"⚠️ 解析LLM响应失败: {e}")
            raise
    
    def _calculate_domain_scores(self, user_message: str, user_context: Dict[str, Any] = None) -> Dict[DomainType, float]:
        """
        计算每个领域的匹配度
        
        Args:
            user_message: 用户消息
            user_context: 用户上下文
        
        Returns:
            领域匹配度字典
        """
        domain_scores = {}
        message_lower = user_message.lower()
        
        # 计算关键词匹配度
        for domain, keywords in self.domain_keywords.items():
            score = 0.0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword in message_lower:
                    score += 1.0
                    matched_keywords.append(keyword)
            
            # 归一化
            if keywords:
                score = score / len(keywords)
            
            # 应用领域权重
            score *= self.domain_weights[domain]
            
            domain_scores[domain] = score
        
        # 如果有用户上下文，调整分数
        if user_context:
            domain_scores = self._adjust_scores_by_context(domain_scores, user_context)
        
        return domain_scores
    
    def _adjust_scores_by_context(self, domain_scores: Dict[DomainType, float], 
                                   user_context: Dict[str, Any]) -> Dict[DomainType, float]:
        """
        根据用户上下文调整领域分数
        
        Args:
            domain_scores: 原始领域分数
            user_context: 用户上下文
        
        Returns:
            调整后的领域分数
        """
        # 如果用户最近关注某个领域，提升该领域的分数
        if "recent_focus" in user_context:
            focus_domain = user_context["recent_focus"]
            if focus_domain in domain_scores:
                domain_scores[focus_domain] *= 1.2
        
        # 如果用户有特定的问题，提升相关领域的分数
        if "problem_domain" in user_context:
            problem_domain = user_context["problem_domain"]
            if problem_domain in domain_scores:
                domain_scores[problem_domain] *= 1.5
        
        # 如果用户的某个指标异常，提升相关领域的分数
        if "anomaly_domain" in user_context:
            anomaly_domain = user_context["anomaly_domain"]
            if anomaly_domain in domain_scores:
                domain_scores[anomaly_domain] *= 1.3
        
        return domain_scores
    
    def _select_primary_domains(self, domain_scores: Dict[DomainType, float], 
                                threshold: float = 0.1) -> List[DomainType]:
        """
        选择主要领域
        
        Args:
            domain_scores: 领域分数
            threshold: 阈值
        
        Returns:
            主要领域列表
        """
        # 按分数排序
        sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 选择分数高于阈值的领域
        primary_domains = []
        for domain, score in sorted_domains:
            if score >= threshold:
                primary_domains.append(domain)
        
        # 如果没有选中任何领域，选择分数最高的领域
        if not primary_domains and sorted_domains:
            primary_domains.append(sorted_domains[0][0])
        
        # 如果还是没有，返回通用领域
        if not primary_domains:
            primary_domains.append(DomainType.GENERAL)
        
        return primary_domains
    
    def get_domain_info(self, domain: DomainType) -> Dict[str, Any]:
        """
        获取领域信息
        
        Args:
            domain: 领域类型
        
        Returns:
            领域信息
        """
        domain_info = {
            DomainType.HEALTH: {
                "name": "健康领域",
                "description": "分析用户的健康状况，包括睡眠、运动、压力、免疫力等",
                "key_metrics": ["sleep_hours", "exercise_minutes", "stress_level", "heart_rate"],
                "analysis_focus": ["睡眠债务", "免疫力", "健康分数"]
            },
            DomainType.TIME: {
                "name": "时间领域",
                "description": "分析用户的时间管理和效率，包括工作时间、专注度、任务完成率等",
                "key_metrics": ["work_hours", "focus_time", "task_completion_rate", "interruptions"],
                "analysis_focus": ["效率分数", "认知负荷", "时间压力"]
            },
            DomainType.EMOTION: {
                "name": "情绪领域",
                "description": "分析用户的情绪状态，包括心情、稳定性、调节能力等",
                "key_metrics": ["mood", "stress_level", "anxiety_level", "happiness"],
                "analysis_focus": ["情绪稳定性", "调节能力", "风险预警"]
            },
            DomainType.SOCIAL: {
                "name": "社交领域",
                "description": "分析用户的社交状况，包括孤独感、满意度、关系质量等",
                "key_metrics": ["social_hours", "social_interactions", "loneliness", "social_satisfaction"],
                "analysis_focus": ["孤独感", "满意度", "关系质量"]
            },
            DomainType.FINANCE: {
                "name": "财务领域",
                "description": "分析用户的财务状况，包括储蓄率、消费模式、风险评估等",
                "key_metrics": ["income", "spending", "savings", "debt"],
                "analysis_focus": ["储蓄率", "财务健康", "风险评估"]
            },
            DomainType.LEARNING: {
                "name": "学习领域",
                "description": "分析用户的学习进度，包括学习效率、知识保持、进度评估等",
                "key_metrics": ["learning_hours", "learning_quality", "test_score", "goal_progress"],
                "analysis_focus": ["学习效率", "知识保持", "进度评估"]
            },
            DomainType.MULTI_DOMAIN: {
                "name": "多领域",
                "description": "涉及多个领域的综合分析",
                "key_metrics": [],
                "analysis_focus": ["跨领域关系", "协同效应", "整体平衡"]
            },
            DomainType.GENERAL: {
                "name": "通用",
                "description": "通用问题，不属于特定领域",
                "key_metrics": [],
                "analysis_focus": ["通用知识", "建议"]
            }
        }
        
        return domain_info.get(domain, {})
    
    def get_routing_explanation(self, user_message: str, primary_domains: List[DomainType], 
                               domain_scores: Dict[DomainType, float]) -> str:
        """
        获取路由解释
        
        Args:
            user_message: 用户消息
            primary_domains: 主要领域
            domain_scores: 领域分数
        
        Returns:
            路由解释
        """
        explanation = f"用户问题分析：\n"
        explanation += f"问题：{user_message}\n\n"
        explanation += f"路由结果：\n"
        
        for domain in primary_domains:
            score = domain_scores.get(domain, 0)
            domain_info = self.get_domain_info(domain)
            explanation += f"- {domain_info['name']} (匹配度: {score:.2%})\n"
        
        return explanation


def get_meta_agent_router() -> MetaAgentRouter:
    """获取元智能体路由器实例"""
    return MetaAgentRouter()

