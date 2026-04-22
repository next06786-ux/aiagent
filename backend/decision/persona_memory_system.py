"""
决策人格记忆系统 - 分层混合架构

核心设计理念：共享事实，私有解读

架构层次：
┌─────────────────────────────────────────────────────────┐
│  私有层 (Persona-Specific Layer)                         │
│  - 每个人格对事实的独特解读                               │
│  - 个人立场、推理、学到的教训                             │
│  - 情感反应和价值观判断                                   │
├─────────────────────────────────────────────────────────┤
│  决策层 (Decision-Specific Layer)                        │
│  - 本次决策的上下文和选项                                 │
│  - 所有人格的分析和交互记录                               │
│  - 决策结果和反馈                                         │
├─────────────────────────────────────────────────────────┤
│  共享层 (Shared Facts Layer)                             │
│  - RAG + Neo4j 混合检索的用户数据                         │
│  - 用户的历史行为、关系、技能、经历                       │
│  - 客观事实，所有人格共享                                 │
└─────────────────────────────────────────────────────────┘

作者: AI System
版本: 1.0
日期: 2026-04-18
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


# ==================== 共享层：事实数据 ====================

@dataclass
class SharedFactsLayer:
    """
    共享事实层 - 所有人格共享的客观数据
    
    唯一数据来源：决策信息收集阶段的 collected_info
    
    职责：
    - 直接加载 collected_info 的所有数据
    - 不做额外的数据库查询
    - 生命周期 = 单次决策会话
    
    特点：客观、中立、所有人格可见
    """
    user_id: str
    
    # 直接从 collected_info 加载的数据
    decision_scenario: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    priorities: Dict[str, Any] = field(default_factory=dict)
    concerns: List[str] = field(default_factory=list)
    
    # 混合检索结果（已包含在 collected_info 中）
    retrieval_results: Dict[str, Any] = field(default_factory=dict)
    
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "user_id": self.user_id,
            "decision_scenario": self.decision_scenario,
            "constraints": self.constraints,
            "priorities": self.priorities,
            "concerns_count": len(self.concerns),
            "retrieval_results_count": len(self.retrieval_results.get('results', [])),
            "last_updated": self.last_updated.isoformat()
        }
    
    def get_summary(self) -> str:
        """获取事实摘要（供人格使用）"""
        summary_parts = []
        
        # 显示数据来源
        if self.retrieval_results:
            total = len(self.retrieval_results.get('results', []))
            if total > 0:
                summary_parts.append(f"[数据来源: 信息收集阶段，共{total}条检索结果]")
        
        if self.decision_scenario:
            summary_parts.append(f"决策场景: 已加载")
        
        if self.constraints:
            summary_parts.append(f"约束条件: {len(self.constraints)}项")
        
        if self.priorities:
            summary_parts.append(f"优先级: {len(self.priorities)}项")
        
        if self.concerns:
            summary_parts.append(f"担忧: {len(self.concerns)}项")
        
        return "\n".join(summary_parts) if summary_parts else "暂无数据"


# ==================== 决策层：决策上下文 ====================

@dataclass
class DecisionContext:
    """
    决策上下文层 - 历史决策记录 + 决策元数据
    
    数据来源：
    1. 历史决策记录（文件系统）
    2. 当前决策的元信息
    
    职责：
    - 加载历史决策记录
    - 分析用户决策风格
    - 管理决策状态和结果
    """
    decision_id: str
    user_id: str
    question: str
    options: List[Dict[str, Any]]
    
    # 历史决策记录
    past_decisions: List[Dict[str, Any]] = field(default_factory=list)
    
    # 决策元数据
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "in_progress"  # in_progress | completed | abandoned
    
    # 决策结果
    chosen_option: Optional[str] = None
    decision_rationale: Optional[str] = None
    outcome: Optional[str] = None
    success: Optional[bool] = None
    
    # 🆕 用户决策风格分析（第2层增强）
    user_decision_style: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "user_id": self.user_id,
            "question": self.question,
            "options_count": len(self.options),
            "past_decisions_count": len(self.past_decisions),
            "status": self.status,
            "chosen_option": self.chosen_option,
            "outcome": self.outcome,
            "success": self.success,
            "user_decision_style": self.user_decision_style,
            "created_at": self.created_at.isoformat()
        }
        }


# ==================== 私有层：人格解读 ====================

@dataclass
class PersonaInterpretation:
    """
    人格解读 - 单个人格对事实的私有解读
    
    特点：
    - 基于共享事实，但加入人格的价值观过滤
    - 同样的事实，不同人格有不同解读
    - 这是"数字生命"的核心：独特视角
    """
    persona_id: str
    decision_id: str
    
    # 对共享事实的解读
    facts_interpretation: Dict[str, str] = field(default_factory=dict)
    # 例如：{"用户GPA 3.5": "理性分析师认为这是中等水平，需要提升"}
    
    # 对决策选项的立场
    option_stances: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # 例如：{"选项1": {"stance": "支持", "score": 85, "reasoning": "..."}}
    
    # 个人推理过程
    reasoning_chain: List[str] = field(default_factory=list)
    
    # 情感反应
    emotional_reactions: List[Dict[str, Any]] = field(default_factory=list)
    
    # 学到的教训（决策后更新）
    learned_lessons: List[str] = field(default_factory=list)
    
    # 与其他人格的交互记录
    interactions: List[Dict[str, Any]] = field(default_factory=list)
    
    timestamp: datetime = field(default_factory=datetime.now)
    
    def add_fact_interpretation(self, fact: str, interpretation: str):
        """添加对事实的解读"""
        self.facts_interpretation[fact] = interpretation
    
    def set_option_stance(self, option_id: str, stance: str, score: float, reasoning: str):
        """设置对选项的立场"""
        self.option_stances[option_id] = {
            "stance": stance,
            "score": score,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat()
        }
    
    def add_reasoning_step(self, step: str):
        """添加推理步骤"""
        self.reasoning_chain.append(step)
    
    def add_emotional_reaction(self, emotion: str, intensity: float, trigger: str):
        """添加情感反应"""
        self.emotional_reactions.append({
            "emotion": emotion,
            "intensity": intensity,
            "trigger": trigger,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_learned_lesson(self, lesson: str):
        """添加学到的教训"""
        self.learned_lessons.append(lesson)
    
    def calculate_similarity(self, other_context: Dict[str, Any]) -> float:
        """
        计算与另一个决策上下文的相似度（用于历史经验查询）
        
        相似度计算维度：
        1. 问题类型相似度（关键词匹配）
        2. 选项数量相似度
        3. 决策领域相似度
        
        Args:
            other_context: 另一个决策的上下文信息
        
        Returns:
            相似度分数 (0-1)
        """
        similarity_score = 0.0
        weight_sum = 0.0
        
        # 1. 问题类型相似度（权重：0.5）
        if 'question' in other_context:
            current_question = other_context.get('question', '').lower()
            # 简单的关键词匹配
            common_keywords = ['职业', '工作', '学习', '关系', '投资', '健康', '旅行']
            current_keywords = [kw for kw in common_keywords if kw in current_question]
            
            # 这里需要当前决策的问题，但在PersonaInterpretation中没有直接访问
            # 所以这个方法应该在LayeredMemorySystem中调用时传入当前问题
            # 暂时返回基础相似度
            similarity_score += 0.3
            weight_sum += 0.5
        
        # 2. 选项数量相似度（权重：0.2）
        if 'options' in other_context:
            other_option_count = len(other_context.get('options', []))
            # 这里也需要当前选项数量
            similarity_score += 0.2
            weight_sum += 0.2
        
        # 3. 决策领域相似度（权重：0.3）
        # 基于collected_info中的领域标签
        similarity_score += 0.2
        weight_sum += 0.3
        
        return similarity_score / weight_sum if weight_sum > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "persona_id": self.persona_id,
            "decision_id": self.decision_id,
            "facts_interpretation_count": len(self.facts_interpretation),
            "option_stances": self.option_stances,
            "reasoning_steps": len(self.reasoning_chain),
            "emotional_reactions_count": len(self.emotional_reactions),
            "learned_lessons": self.learned_lessons,
            "interactions_count": len(self.interactions),
            "timestamp": self.timestamp.isoformat()
        }



# ==================== 分层记忆管理器 ====================

class LayeredMemorySystem:
    """
    分层记忆系统管理器
    
    职责：
    1. 管理三层记忆架构
    2. 从 RAG + Neo4j 加载共享事实
    3. 为每个人格提供视角过滤器
    4. 持久化决策记忆
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        
        # 共享层：所有人格共享的事实
        self.shared_facts: Optional[SharedFactsLayer] = None
        
        # 决策层：当前决策的上下文
        self.current_decision: Optional[DecisionContext] = None
        
        # 私有层：每个人格的解读（decision_id -> persona_id -> interpretation）
        self.persona_interpretations: Dict[str, Dict[str, PersonaInterpretation]] = {}
        
        logger.info(f"🧠 分层记忆系统已初始化: user={user_id}")
    
    async def load_shared_facts(
        self,
        collected_info: Dict[str, Any]
    ) -> SharedFactsLayer:
        """
        加载共享事实层 - 直接从 collected_info 加载
        
        设计理念：
        - 共享事实层 = 决策信息收集阶段的数据
        - 不做任何额外的数据库查询
        - 生命周期 = 单次决策会话
        - 所有7个Agent看到完全相同的事实基础

        Args:
            collected_info: 信息收集阶段的完整数据

        Returns:
            共享事实层对象
        """
        logger.info(f"📚 开始加载共享事实层...")
        logger.info(f"  📌 数据来源：决策信息收集阶段")
        logger.info(f"  📌 生命周期：绑定到当前决策会话")

        shared_facts = SharedFactsLayer(user_id=self.user_id)

        # 直接加载 collected_info 的所有数据
        shared_facts.decision_scenario = collected_info.get('decision_scenario', {})
        shared_facts.constraints = collected_info.get('constraints', {})
        shared_facts.priorities = collected_info.get('priorities', {})
        shared_facts.concerns = collected_info.get('concerns', [])
        shared_facts.retrieval_results = collected_info.get('retrieval_cache', {})
        
        logger.info(f"  ✓ 数据加载完成:")
        logger.info(f"    - 决策场景: {'已加载' if shared_facts.decision_scenario else '未提供'}")
        logger.info(f"    - 约束条件: {len(shared_facts.constraints)} 项")
        logger.info(f"    - 优先级: {len(shared_facts.priorities)} 项")
        logger.info(f"    - 担忧: {len(shared_facts.concerns)} 项")
        
        # 显示混合检索统计
        retrieval_results = shared_facts.retrieval_results
        if retrieval_results:
            total = len(retrieval_results.get('results', []))
            logger.info(f"    - 混合检索结果: {total} 条")
        
        shared_facts.last_updated = datetime.now()
        self.shared_facts = shared_facts

        logger.info(f"✅ 共享事实层加载完成")
        logger.info(f"   📊 数据摘要:\n{shared_facts.get_summary()}")

        return shared_facts

    
    def _load_past_decisions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """加载历史决策记录"""
        import os
        
        decisions_dir = "./backend/data/decision_sessions"
        if not os.path.exists(decisions_dir):
            return []
        
        past_decisions = []
        
        try:
            for filename in os.listdir(decisions_dir):
                if not filename.endswith('.json'):
                    continue
                
                filepath = os.path.join(decisions_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                        
                        if session_data.get('user_id') == user_id:
                            past_decisions.append({
                                "session_id": session_data.get('session_id'),
                                "question": session_data.get('initial_question'),
                                "created_at": session_data.get('created_at'),
                                "is_complete": session_data.get('is_complete', False)
                            })
                except json.JSONDecodeError as je:
                    logger.warning(f"跳过损坏的决策文件 {filename}: {je}")
                    continue
                except Exception as fe:
                    logger.warning(f"读取决策文件 {filename} 失败: {fe}")
                    continue
            
            # 按时间排序，最近的在前
            past_decisions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return past_decisions[:limit]
            
        except Exception as e:
            logger.error(f"加载历史决策失败: {e}")
            return []
    
    def _analyze_user_decision_style(self, past_decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析用户决策风格（第2层增强功能）
        
        基于历史决策数据分析用户的决策模式：
        1. 决策速度：快速决策 vs 深思熟虑
        2. 风险偏好：保守 vs 激进
        3. 决策依据：理性分析 vs 直觉感受
        4. 常见决策领域：职业、学习、关系等
        5. 决策成功率：历史决策的结果统计
        
        Args:
            past_decisions: 历史决策记录列表
        
        Returns:
            用户决策风格分析结果
        """
        logger.info(f"🎯 开始分析用户决策风格...")
        
        style_analysis = {
            "decision_speed": "unknown",  # fast | moderate | slow
            "risk_preference": "unknown",  # conservative | moderate | aggressive
            "decision_basis": "unknown",  # rational | intuitive | balanced
            "common_domains": [],  # 常见决策领域
            "success_rate": 0.0,  # 历史决策成功率
            "total_decisions": 0,
            "completed_decisions": 0,
            "patterns": []  # 发现的决策模式
        }
        
        # 获取历史决策数据
        if not past_decisions:
            logger.info(f"  ⚠️ 无历史决策数据，返回默认风格")
            return style_analysis
        
        style_analysis["total_decisions"] = len(past_decisions)
        
        # 统计完成的决策
        completed = [d for d in past_decisions if d.get('is_complete', False)]
        style_analysis["completed_decisions"] = len(completed)
        
        # 1. 分析决策速度（基于决策会话的时间跨度）
        # 这里需要更详细的时间数据，暂时基于决策数量推断
        if len(past_decisions) > 5:
            style_analysis["decision_speed"] = "fast"
            style_analysis["patterns"].append("用户倾向于快速做出决策")
        elif len(past_decisions) > 2:
            style_analysis["decision_speed"] = "moderate"
            style_analysis["patterns"].append("用户决策速度适中")
        else:
            style_analysis["decision_speed"] = "slow"
            style_analysis["patterns"].append("用户倾向于深思熟虑")
        
        # 2. 分析决策领域（基于问题关键词）
        domain_keywords = {
            "职业": ["工作", "职业", "跳槽", "晋升", "公司"],
            "学习": ["学习", "课程", "专业", "考试", "培训"],
            "关系": ["朋友", "恋爱", "家人", "社交", "关系"],
            "投资": ["投资", "理财", "买房", "股票", "基金"],
            "健康": ["健康", "运动", "饮食", "医疗"],
            "旅行": ["旅行", "旅游", "出行", "度假"]
        }
        
        domain_counts = {domain: 0 for domain in domain_keywords.keys()}
        
        for decision in past_decisions:
            question = decision.get('question', '').lower()
            for domain, keywords in domain_keywords.items():
                if any(kw in question for kw in keywords):
                    domain_counts[domain] += 1
        
        # 找出最常见的决策领域
        common_domains = sorted(
            [(domain, count) for domain, count in domain_counts.items() if count > 0],
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        style_analysis["common_domains"] = [
            {"domain": domain, "count": count} 
            for domain, count in common_domains
        ]
        
        if common_domains:
            top_domain = common_domains[0][0]
            style_analysis["patterns"].append(f"用户经常在{top_domain}领域做决策")
        
        # 3. 风险偏好分析（基于选项数量和决策完成率）
        if style_analysis["completed_decisions"] > 0:
            completion_rate = style_analysis["completed_decisions"] / style_analysis["total_decisions"]
            
            if completion_rate > 0.7:
                style_analysis["risk_preference"] = "conservative"
                style_analysis["patterns"].append("用户倾向于完成决策，风格较为保守")
            elif completion_rate > 0.4:
                style_analysis["risk_preference"] = "moderate"
                style_analysis["patterns"].append("用户决策风格适中")
            else:
                style_analysis["risk_preference"] = "aggressive"
                style_analysis["patterns"].append("用户可能倾向于探索多种可能性")
        
        # 4. 决策依据分析（需要更详细的历史数据，暂时设为balanced）
        style_analysis["decision_basis"] = "balanced"
        style_analysis["patterns"].append("用户综合理性分析和直觉感受做决策")
        
        logger.info(f"  ✅ 决策风格分析完成:")
        logger.info(f"    - 决策速度: {style_analysis['decision_speed']}")
        logger.info(f"    - 风险偏好: {style_analysis['risk_preference']}")
        logger.info(f"    - 决策依据: {style_analysis['decision_basis']}")
        logger.info(f"    - 常见领域: {[d['domain'] for d in style_analysis['common_domains']]}")
        logger.info(f"    - 历史决策: {style_analysis['total_decisions']} 条")
        
        return style_analysis
    
    def create_decision_context(
        self,
        decision_id: str,
        question: str,
        options: List[Dict[str, Any]]
    ) -> DecisionContext:
        """
        创建决策上下文（第2层）
        
        职责：
        - 加载历史决策记录
        - 分析用户决策风格
        - 创建决策元数据
        """
        # 加载历史决策记录
        past_decisions = self._load_past_decisions(self.user_id)
        
        # 分析用户决策风格（第2层增强）
        user_decision_style = self._analyze_user_decision_style(past_decisions)
        
        decision_context = DecisionContext(
            decision_id=decision_id,
            user_id=self.user_id,
            question=question,
            options=options,
            past_decisions=past_decisions,
            user_decision_style=user_decision_style
        )
        
        self.current_decision = decision_context
        
        # 为这个决策创建人格解读存储
        self.persona_interpretations[decision_id] = {}
        
        logger.info(f"📝 决策上下文已创建: {decision_id}")
        logger.info(f"  📚 历史决策: {len(past_decisions)} 条")
        logger.info(f"  🎯 用户决策风格: {user_decision_style.get('decision_speed')} / {user_decision_style.get('risk_preference')}")
        
        return decision_context
    
    def get_persona_view(
        self,
        persona_id: str,
        decision_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取人格视角 - 视角过滤器
        
        返回该人格能看到的所有信息：
        1. 共享事实（客观数据）
        2. 决策上下文（本次决策）
        3. 该人格的私有解读（如果存在）
        
        Args:
            persona_id: 人格ID
            decision_id: 决策ID（可选，默认使用当前决策）
        
        Returns:
            人格视角数据
        """
        decision_id = decision_id or (self.current_decision.decision_id if self.current_decision else None)
        
        view = {
            "persona_id": persona_id,
            "shared_facts": self.shared_facts.to_dict() if self.shared_facts else {},
            "shared_facts_summary": self.shared_facts.get_summary() if self.shared_facts else "无共享数据",
            "decision_context": self.current_decision.to_dict() if self.current_decision else {},
            "my_interpretation": None
        }
        
        # 添加该人格的私有解读
        if decision_id and decision_id in self.persona_interpretations:
            if persona_id in self.persona_interpretations[decision_id]:
                view["my_interpretation"] = self.persona_interpretations[decision_id][persona_id].to_dict()
        
        return view
    
    def create_persona_interpretation(
        self,
        persona_id: str,
        decision_id: Optional[str] = None
    ) -> PersonaInterpretation:
        """为人格创建私有解读空间"""
        decision_id = decision_id or (self.current_decision.decision_id if self.current_decision else None)
        
        if not decision_id:
            raise ValueError("必须指定决策ID或存在当前决策")
        
        if decision_id not in self.persona_interpretations:
            self.persona_interpretations[decision_id] = {}
        
        interpretation = PersonaInterpretation(
            persona_id=persona_id,
            decision_id=decision_id
        )
        
        self.persona_interpretations[decision_id][persona_id] = interpretation
        
        return interpretation
    
    def get_persona_interpretation(
        self,
        persona_id: str,
        decision_id: Optional[str] = None
    ) -> Optional[PersonaInterpretation]:
        """获取人格的私有解读"""
        decision_id = decision_id or (self.current_decision.decision_id if self.current_decision else None)
        
        if not decision_id:
            return None
        
        return self.persona_interpretations.get(decision_id, {}).get(persona_id)
    
    def get_persona_past_interpretations(
        self,
        persona_id: str,
        current_question: str,
        current_options: List[Dict[str, Any]],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        获取Agent的历史经验（第3层增强功能）
        
        查询该人格在相似决策场景中的历史解读和经验：
        1. 基于问题相似度匹配历史决策
        2. 提取该人格在历史决策中的立场和推理
        3. 提取学到的教训
        4. 返回最相关的top_k条经验
        
        Args:
            persona_id: 人格ID
            current_question: 当前决策问题
            current_options: 当前决策选项
            top_k: 返回最相关的经验数量
        
        Returns:
            历史经验列表，按相似度排序
        """
        logger.info(f"🔍 查询 {persona_id} 的历史经验...")
        
        past_experiences = []
        
        # 遍历所有历史决策的人格解读
        for decision_id, persona_dict in self.persona_interpretations.items():
            if persona_id not in persona_dict:
                continue
            
            interpretation = persona_dict[persona_id]
            
            # 计算相似度
            similarity_score = self._calculate_decision_similarity(
                current_question=current_question,
                current_options=current_options,
                past_decision_id=decision_id
            )
            
            # 提取该人格的历史经验
            experience = {
                "decision_id": decision_id,
                "similarity_score": similarity_score,
                "option_stances": interpretation.option_stances,
                "reasoning_steps": len(interpretation.reasoning_chain),
                "learned_lessons": interpretation.learned_lessons,
                "emotional_reactions": interpretation.emotional_reactions,
                "timestamp": interpretation.timestamp.isoformat()
            }
            
            # 添加决策上下文信息（如果可用）
            if decision_id in [d.get('session_id') for d in (self.shared_facts.past_decisions if self.shared_facts else [])]:
                past_decision = next(
                    (d for d in self.shared_facts.past_decisions if d.get('session_id') == decision_id),
                    None
                )
                if past_decision:
                    experience["past_question"] = past_decision.get('question', '')
                    experience["past_created_at"] = past_decision.get('created_at', '')
            
            past_experiences.append(experience)
        
        # 按相似度排序
        past_experiences.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # 返回top_k条最相关的经验
        top_experiences = past_experiences[:top_k]
        
        logger.info(f"  ✅ 找到 {len(past_experiences)} 条历史经验，返回最相关的 {len(top_experiences)} 条")
        for i, exp in enumerate(top_experiences, 1):
            logger.info(f"    {i}. 相似度: {exp['similarity_score']:.2f}, 决策ID: {exp['decision_id'][:8]}...")
        
        return top_experiences
    
    def _calculate_decision_similarity(
        self,
        current_question: str,
        current_options: List[Dict[str, Any]],
        past_decision_id: str
    ) -> float:
        """
        计算当前决策与历史决策的相似度
        
        相似度计算维度：
        1. 问题文本相似度（关键词匹配）
        2. 选项数量相似度
        3. 决策领域相似度
        
        Args:
            current_question: 当前决策问题
            current_options: 当前决策选项
            past_decision_id: 历史决策ID
        
        Returns:
            相似度分数 (0-1)
        """
        similarity_score = 0.0
        
        # 查找历史决策信息
        past_decision = None
        if self.shared_facts and self.shared_facts.past_decisions:
            past_decision = next(
                (d for d in self.shared_facts.past_decisions if d.get('session_id') == past_decision_id),
                None
            )
        
        if not past_decision:
            return 0.0
        
        past_question = past_decision.get('question', '').lower()
        current_question_lower = current_question.lower()
        
        # 1. 问题关键词相似度（权重：0.6）
        # 提取关键词
        keywords = ['职业', '工作', '学习', '关系', '投资', '健康', '旅行', 
                   '选择', '决定', '考虑', '应该', '是否', '如何']
        
        current_keywords = set([kw for kw in keywords if kw in current_question_lower])
        past_keywords = set([kw for kw in keywords if kw in past_question])
        
        if current_keywords and past_keywords:
            keyword_similarity = len(current_keywords & past_keywords) / len(current_keywords | past_keywords)
            similarity_score += keyword_similarity * 0.6
        
        # 2. 选项数量相似度（权重：0.2）
        current_option_count = len(current_options)
        # 历史决策的选项数量需要从存储中获取，这里简化处理
        # 假设选项数量在2-5之间
        option_diff = abs(current_option_count - 3)  # 假设平均3个选项
        option_similarity = max(0, 1 - option_diff * 0.2)
        similarity_score += option_similarity * 0.2
        
        # 3. 决策领域相似度（权重：0.2）
        # 基于问题中的领域关键词
        domain_keywords = {
            "职业": ["工作", "职业", "跳槽", "晋升", "公司"],
            "学习": ["学习", "课程", "专业", "考试", "培训"],
            "关系": ["朋友", "恋爱", "家人", "社交", "关系"],
            "投资": ["投资", "理财", "买房", "股票", "基金"],
        }
        
        current_domain = None
        past_domain = None
        
        for domain, kws in domain_keywords.items():
            if any(kw in current_question_lower for kw in kws):
                current_domain = domain
            if any(kw in past_question for kw in kws):
                past_domain = domain
        
        if current_domain and past_domain and current_domain == past_domain:
            similarity_score += 0.2
        
        return min(similarity_score, 1.0)
    
    def update_decision_outcome(
        self,
        decision_id: str,
        chosen_option: str,
        rationale: str,
        outcome: Optional[str] = None,
        success: Optional[bool] = None
    ):
        """更新决策结果"""
        if self.current_decision and self.current_decision.decision_id == decision_id:
            self.current_decision.chosen_option = chosen_option
            self.current_decision.decision_rationale = rationale
            self.current_decision.outcome = outcome
            self.current_decision.success = success
            self.current_decision.status = "completed"
            
            logger.info(f"✅ 决策结果已更新: {decision_id}")
            logger.info(f"   选择: {chosen_option}")
            logger.info(f"   成功: {success}")
    
    def get_all_persona_interpretations(
        self,
        decision_id: Optional[str] = None
    ) -> Dict[str, PersonaInterpretation]:
        """获取所有人格的解读"""
        decision_id = decision_id or (self.current_decision.decision_id if self.current_decision else None)
        
        if not decision_id:
            return {}
        
        return self.persona_interpretations.get(decision_id, {})
    
    def persist_to_storage(self, decision_id: str):
        """持久化到存储（文件系统或数据库）"""
        import os
        
        storage_dir = "./backend/data/persona_memories"
        os.makedirs(storage_dir, exist_ok=True)
        
        # 保存决策上下文
        if self.current_decision and self.current_decision.decision_id == decision_id:
            decision_file = os.path.join(storage_dir, f"decision_{decision_id}.json")
            with open(decision_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_decision.to_dict(), f, ensure_ascii=False, indent=2)
        
        # 保存所有人格的解读
        if decision_id in self.persona_interpretations:
            for persona_id, interpretation in self.persona_interpretations[decision_id].items():
                persona_file = os.path.join(storage_dir, f"persona_{persona_id}_{decision_id}.json")
                with open(persona_file, 'w', encoding='utf-8') as f:
                    json.dump(interpretation.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 记忆已持久化: {decision_id}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆系统统计信息"""
        return {
            "user_id": self.user_id,
            "shared_facts_loaded": self.shared_facts is not None,
            "current_decision": self.current_decision.decision_id if self.current_decision else None,
            "total_decisions": len(self.persona_interpretations),
            "total_interpretations": sum(
                len(interpretations) 
                for interpretations in self.persona_interpretations.values()
            )
        }



# ==================== 示例：不同人格如何解读同一事实 ====================

def demonstrate_layered_memory():
    """
    演示分层记忆系统的工作原理
    
    展示：同样的事实，不同人格有不同解读
    """
    print("="*60)
    print("分层记忆系统演示")
    print("="*60)
    
    # 共享事实层（所有人格看到的客观数据）
    shared_fact = {
        "fact": "用户GPA 3.5/4.0，排名前30%",
        "source": "教育背景数据"
    }
    
    print(f"\n📊 共享事实（客观）:")
    print(f"   {shared_fact['fact']}")
    
    # 不同人格的解读（私有层）
    persona_interpretations = {
        "理性分析师": {
            "interpretation": "GPA 3.5属于中等偏上水平，在申请顶尖院校时竞争力不足，建议提升到3.7以上",
            "emotion": "谨慎",
            "recommendation": "需要提升学业成绩"
        },
        "冒险家": {
            "interpretation": "GPA 3.5已经不错了，不要被数字束缚，更重要的是展现独特性和潜力",
            "emotion": "乐观",
            "recommendation": "关注软实力和特色项目"
        },
        "保守派": {
            "interpretation": "GPA 3.5虽然不是最高，但已经超过70%的同学，是一个安全的水平",
            "emotion": "满意",
            "recommendation": "保持现状，不要冒险"
        },
        "理想主义者": {
            "interpretation": "GPA只是一个数字，重要的是你在学习过程中获得了什么成长和启发",
            "emotion": "超脱",
            "recommendation": "追求知识本身的价值"
        },
        "实用主义者": {
            "interpretation": "GPA 3.5足够申请大部分学校，性价比最高的策略是保持现状，投入精力到其他方面",
            "emotion": "务实",
            "recommendation": "优化资源分配"
        },
        "社交导向者": {
            "interpretation": "GPA 3.5在同学中属于中上水平，不会让你在社交场合感到尴尬",
            "emotion": "关注",
            "recommendation": "考虑他人的看法"
        },
        "创新者": {
            "interpretation": "GPA 3.5说明你有学习能力，但也许传统的评价体系不适合你，考虑展示其他维度的才能",
            "emotion": "启发",
            "recommendation": "寻找非传统路径"
        }
    }
    
    print(f"\n🎭 不同人格的解读（私有）:\n")
    for persona_name, interp in persona_interpretations.items():
        print(f"【{persona_name}】")
        print(f"  解读: {interp['interpretation']}")
        print(f"  情感: {interp['emotion']}")
        print(f"  建议: {interp['recommendation']}")
        print()
    
    print("="*60)
    print("这就是'共享事实，私有解读'的核心理念")
    print("="*60)


# ==================== 便捷函数 ====================

def create_layered_memory_system(user_id: str) -> LayeredMemorySystem:
    """创建分层记忆系统"""
    return LayeredMemorySystem(user_id)


async def initialize_memory_for_decision(
    user_id: str,
    decision_id: str,
    question: str,
    options: List[Dict[str, Any]],
    collected_info: Dict[str, Any]
) -> LayeredMemorySystem:
    """
    为决策初始化完整的记忆系统
    
    三层数据职责：
    - 第1层（共享事实层）：直接加载 collected_info
    - 第2层（决策上下文层）：加载历史决策 + 分析决策风格
    - 第3层（私有解读层）：推演时产生
    
    Args:
        user_id: 用户ID
        decision_id: 决策ID
        question: 决策问题
        options: 决策选项列表
        collected_info: 信息收集阶段的完整数据
    
    Returns:
        初始化完成的分层记忆系统
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"🧠 初始化决策记忆系统")
    logger.info(f"{'='*60}")
    logger.info(f"用户: {user_id}")
    logger.info(f"决策: {decision_id}")
    logger.info(f"问题: {question}")
    logger.info(f"选项数: {len(options)}")
    logger.info(f"{'='*60}\n")
    
    memory_system = LayeredMemorySystem(user_id)
    
    # 第1层：加载共享事实层（直接从 collected_info 加载）
    await memory_system.load_shared_facts(collected_info=collected_info)
    
    # 第2层：创建决策上下文（加载历史决策 + 分析决策风格）
    decision_context = memory_system.create_decision_context(
        decision_id=decision_id,
        question=question,
        options=options
    )
    
    logger.info(f"\n{'='*60}")
    logger.info(f"✅ 记忆系统初始化完成")
    logger.info(f"{'='*60}\n")
    
    return memory_system


# ==================== 测试代码 ====================

if __name__ == "__main__":
    import asyncio
    
    async def test_memory_system():
        print("\n" + "="*60)
        print("测试分层记忆系统")
        print("="*60 + "\n")
        
        # 1. 演示概念
        demonstrate_layered_memory()
        
        # 2. 测试实际系统
        print("\n" + "="*60)
        print("测试实际记忆系统")
        print("="*60 + "\n")
        
        memory_system = await initialize_memory_for_decision(
            user_id="test_user",
            decision_id="test_decision_001",
            question="我是大三学生，毕业后该考研还是工作？",
            options=[
                {"title": "考研深造", "description": "继续读研"},
                {"title": "直接工作", "description": "毕业就业"}
            ],
            collected_info={
                "decision_context": {"major": "计算机", "gpa": 3.5},
                "user_constraints": {"budget": "有限", "time": "1年"}
            }
        )
        
        # 3. 为不同人格创建解读
        personas = ["rational_analyst", "adventurer", "conservative"]
        
        for persona_id in personas:
            interpretation = memory_system.create_persona_interpretation(persona_id)
            
            # 添加对事实的解读
            interpretation.add_fact_interpretation(
                fact="GPA 3.5",
                interpretation=f"{persona_id}的解读：这是一个中等水平的成绩"
            )
            
            # 设置对选项的立场
            interpretation.set_option_stance(
                option_id="option_1",
                stance="支持" if persona_id == "rational_analyst" else "中立",
                score=75.0,
                reasoning=f"{persona_id}的推理"
            )
            
            print(f"✓ 已创建 {persona_id} 的解读")
        
        # 4. 获取人格视角
        print(f"\n{'='*60}")
        print("理性分析师的视角")
        print("="*60)
        
        analyst_view = memory_system.get_persona_view("rational_analyst")
        print(f"\n共享事实摘要:")
        print(analyst_view["shared_facts_summary"])
        
        print(f"\n我的解读:")
        if analyst_view["my_interpretation"]:
            print(json.dumps(analyst_view["my_interpretation"], ensure_ascii=False, indent=2))
        
        # 5. 更新决策结果
        memory_system.update_decision_outcome(
            decision_id="test_decision_001",
            chosen_option="考研深造",
            rationale="综合考虑后决定提升学历",
            outcome="成功考上研究生",
            success=True
        )
        
        # 6. 持久化
        memory_system.persist_to_storage("test_decision_001")
        
        # 7. 统计信息
        stats = memory_system.get_memory_stats()
        print(f"\n{'='*60}")
        print("记忆系统统计")
        print("="*60)
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        
        print("\n✅ 测试完成")
    
    asyncio.run(test_memory_system())
