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
    
    数据来源：RAG + Neo4j 混合检索系统
    特点：客观、中立、所有人格可见
    """
    user_id: str
    
    # 从 RAG + Neo4j 获取的用户数据
    user_profile: Dict[str, Any] = field(default_factory=dict)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    education_history: List[Dict[str, Any]] = field(default_factory=list)
    career_history: List[Dict[str, Any]] = field(default_factory=list)
    skills: List[Dict[str, Any]] = field(default_factory=list)
    past_decisions: List[Dict[str, Any]] = field(default_factory=list)
    
    # 混合检索结果缓存
    hybrid_retrieval_cache: Dict[str, Any] = field(default_factory=dict)
    
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "user_id": self.user_id,
            "user_profile": self.user_profile,
            "relationships_count": len(self.relationships),
            "education_count": len(self.education_history),
            "career_count": len(self.career_history),
            "skills_count": len(self.skills),
            "past_decisions_count": len(self.past_decisions),
            "last_updated": self.last_updated.isoformat()
        }
    
    def get_summary(self) -> str:
        """获取事实摘要（供人格使用）"""
        summary_parts = []
        
        if self.user_profile:
            summary_parts.append(f"用户基本信息: {self.user_profile.get('summary', '无')}")
        
        if self.relationships:
            summary_parts.append(f"人际关系: {len(self.relationships)}个重要联系人")
        
        if self.education_history:
            schools = [e.get('school_name', '未知') for e in self.education_history[:3]]
            summary_parts.append(f"教育背景: {', '.join(schools)}")
        
        if self.career_history:
            jobs = [c.get('job_title', '未知') for c in self.career_history[:3]]
            summary_parts.append(f"职业经历: {', '.join(jobs)}")
        
        if self.skills:
            skill_names = [s.get('name', '未知') for s in self.skills[:5]]
            summary_parts.append(f"技能: {', '.join(skill_names)}")
        
        if self.past_decisions:
            summary_parts.append(f"历史决策: {len(self.past_decisions)}次重要决策")
        
        return "\n".join(summary_parts) if summary_parts else "暂无用户数据"


# ==================== 决策层：决策上下文 ====================

@dataclass
class DecisionContext:
    """
    决策上下文层 - 本次决策的所有信息
    
    特点：决策范围内共享，但不同人格有不同解读
    """
    decision_id: str
    user_id: str
    question: str
    options: List[Dict[str, Any]]
    collected_info: Dict[str, Any]  # 从信息收集阶段获得
    
    # 决策元数据
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "in_progress"  # in_progress | completed | abandoned
    
    # 决策结果
    chosen_option: Optional[str] = None
    decision_rationale: Optional[str] = None
    outcome: Optional[str] = None
    success: Optional[bool] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "user_id": self.user_id,
            "question": self.question,
            "options_count": len(self.options),
            "status": self.status,
            "chosen_option": self.chosen_option,
            "outcome": self.outcome,
            "success": self.success,
            "created_at": self.created_at.isoformat()
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
        query: Optional[str] = None,
        retrieval_cache: Optional[Dict[str, Any]] = None
    ) -> SharedFactsLayer:
        """
        加载共享事实层 - 优先使用缓存,按需补充检索

        数据来源优先级:
        1. retrieval_cache: 信息收集阶段的检索缓存（优先使用）
        2. Neo4j + FAISS: 按需补充检索

        Args:
            query: 决策问题，用于检索相关数据
            retrieval_cache: 信息收集阶段的检索缓存（可选）

        Returns:
            共享事实层对象
        """
        logger.info(f"📚 开始加载共享事实层...")

        shared_facts = SharedFactsLayer(user_id=self.user_id)

        # ============================================================
        # 优先使用信息收集阶段的检索缓存
        # ============================================================
        if retrieval_cache:
            logger.info(f"  ✓ 使用信息收集阶段的检索缓存")
            
            # 直接使用缓存的数据
            shared_facts.relationships = retrieval_cache.get('relationships', [])
            shared_facts.education_history = retrieval_cache.get('education_history', [])
            shared_facts.career_history = retrieval_cache.get('career_history', [])
            shared_facts.skills = retrieval_cache.get('skills', [])
            shared_facts.hybrid_retrieval_cache = retrieval_cache.get('hybrid_retrieval_cache', {})
            
            logger.info(f"  ✓ 缓存数据加载完成:")
            logger.info(f"    - 人际关系: {len(shared_facts.relationships)}")
            logger.info(f"    - 教育背景: {len(shared_facts.education_history)}")
            logger.info(f"    - 职业经历: {len(shared_facts.career_history)}")
            logger.info(f"    - 技能: {len(shared_facts.skills)}")
            
        else:
            # ============================================================
            # 没有缓存时,使用统一混合检索系统（Neo4j + FAISS）
            # ============================================================
            logger.info(f"  ⚠️ 无缓存，使用统一混合检索系统（Neo4j + FAISS）...")
            
            try:
                from backend.learning.unified_hybrid_retrieval import (
                    UnifiedHybridRetrieval,
                    RetrievalConfig,
                    RetrievalStrategy,
                    FusionMethod
                )

                retrieval = UnifiedHybridRetrieval(user_id=self.user_id)

                # 配置检索参数 - 获取更多数据
                config = RetrievalConfig(
                    max_results=150,  # 进一步增加，确保获取足够的上下文
                    strategy=RetrievalStrategy.HYBRID_PARALLEL,
                    fusion_method=FusionMethod.RRF,
                    expand_relations=True,
                    query_expansion=True
                )

                # 执行混合检索
                retrieval_context = retrieval.retrieve(
                    query=query or f"用户{self.user_id}的所有信息", 
                    config=config
                )
                results = retrieval_context.results

                # 按来源分类
                kg_results = [r for r in results if r.source == 'neo4j']
                faiss_results = [r for r in results if r.source == 'faiss']

                logger.info(f"  ✓ 混合检索完成: {len(results)}个结果")
                logger.info(f"    - Neo4j知识图谱: {len(kg_results)}条")
                logger.info(f"    - FAISS向量库: {len(faiss_results)}条")

                # 从知识图谱结果中提取结构化数据
                for result in kg_results:
                    node_type = result.node_type
                    result_dict = result.to_dict()

                    if node_type == 'Person':
                        shared_facts.relationships.append(result_dict)
                    elif node_type == 'School':
                        shared_facts.education_history.append(result_dict)
                    elif node_type == 'Job' or node_type == 'Company':
                        shared_facts.career_history.append(result_dict)
                    elif node_type == 'Skill':
                        shared_facts.skills.append(result_dict)

                # 保存混合检索结果
                shared_facts.hybrid_retrieval_cache = {
                    "query": query,
                    "kg_results": [r.to_dict() for r in kg_results],
                    "faiss_results": [r.to_dict() for r in faiss_results],
                    "total": len(results)
                }

                logger.info(f"  ✓ 数据分类完成:")
                logger.info(f"    - 人际关系: {len(shared_facts.relationships)}")
                logger.info(f"    - 教育背景: {len(shared_facts.education_history)}")
                logger.info(f"    - 职业经历: {len(shared_facts.career_history)}")
                logger.info(f"    - 技能: {len(shared_facts.skills)}")

            except Exception as e:
                logger.error(f"  ✗ 统一混合检索失败: {e}")
                import traceback
                traceback.print_exc()
                # 不使用降级方案，直接抛出异常
                raise Exception(f"共享事实层加载失败，无法从数据库获取数据: {e}")

        try:
            # 获取历史决策记录（从文件系统）
            past_decisions = self._load_past_decisions(self.user_id)
            shared_facts.past_decisions = past_decisions

            logger.info(f"  ✓ 历史决策加载完成: {len(past_decisions)}条")

        except Exception as e:
            logger.warning(f"  ⚠️ 历史决策加载失败: {e}")

        shared_facts.last_updated = datetime.now()
        self.shared_facts = shared_facts

        logger.info(f"✅ 共享事实层加载完成")
        logger.info(f"   摘要:\n{shared_facts.get_summary()}")

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
    
    def create_decision_context(
        self,
        decision_id: str,
        question: str,
        options: List[Dict[str, Any]],
        collected_info: Dict[str, Any]
    ) -> DecisionContext:
        """创建决策上下文"""
        decision_context = DecisionContext(
            decision_id=decision_id,
            user_id=self.user_id,
            question=question,
            options=options,
            collected_info=collected_info
        )
        
        self.current_decision = decision_context
        
        # 为这个决策创建人格解读存储
        self.persona_interpretations[decision_id] = {}
        
        logger.info(f"📝 决策上下文已创建: {decision_id}")
        
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
    
    优先使用信息收集阶段的检索缓存,避免重复检索
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"初始化决策记忆系统")
    logger.info(f"用户: {user_id}")
    logger.info(f"决策: {decision_id}")
    logger.info(f"{'='*60}\n")
    
    memory_system = LayeredMemorySystem(user_id)
    
    # 尝试从collected_info中获取检索缓存
    retrieval_cache = collected_info.get('retrieval_cache') if collected_info else None
    
    if retrieval_cache:
        logger.info(f"✓ 发现信息收集阶段的检索缓存，直接使用")
    else:
        logger.info(f"⚠️ 未发现检索缓存，将从数据库重新检索")
    
    # 加载共享事实层（优先使用缓存）
    await memory_system.load_shared_facts(
        query=question,
        retrieval_cache=retrieval_cache
    )
    
    # 创建决策上下文
    memory_system.create_decision_context(
        decision_id=decision_id,
        question=question,
        options=options,
        collected_info=collected_info
    )
    
    logger.info(f"✅ 记忆系统初始化完成\n")
    
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
