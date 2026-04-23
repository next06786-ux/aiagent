"""
决策人格系统 - 7个基于价值观的数字生命

每个决策人格都是独立的智能体，具备：
1. 长期记忆 - 跨决策的经验积累
2. 情感状态 - 情绪、信心、疲劳度
3. 价值观体系 - 独特的决策偏好
4. 自由交互 - 辩论、质疑、支持
5. 涌现演化 - 根据历史决策调整策略

作者: AI System
版本: 1.0
日期: 2026-04-18
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

# 全局检索信号量：限制同时进行的检索请求数量，避免LLM服务过载
# 最多允许3个智能体同时进行检索（每个检索需要2次LLM调用）
_retrieval_semaphore = asyncio.Semaphore(3)


# ==================== 数据结构 ====================

class EmotionType(Enum):
    """情绪类型"""
    OPTIMISTIC = "optimistic"      # 乐观
    PESSIMISTIC = "pessimistic"    # 悲观
    CAUTIOUS = "cautious"          # 谨慎
    EXCITED = "excited"            # 兴奋
    ANXIOUS = "anxious"            # 焦虑
    CONFIDENT = "confident"        # 自信
    DOUBTFUL = "doubtful"          # 怀疑


class InteractionType(Enum):
    """交互类型"""
    SUPPORT = "support"            # 支持
    OPPOSE = "oppose"              # 反对
    QUESTION = "question"          # 质疑
    CLARIFY = "clarify"            # 澄清
    COMPROMISE = "compromise"      # 妥协
    DEBATE = "debate"              # 辩论


@dataclass
class EmotionalState:
    """情感状态"""
    primary_emotion: EmotionType
    intensity: float  # 0-1，情绪强度
    confidence: float  # 0-1，对当前决策的信心
    fatigue: float  # 0-1，疲劳度（避免过度分析）
    stress_level: float  # 0-1，压力水平
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "emotion": self.primary_emotion.value,
            "intensity": round(self.intensity, 2),
            "confidence": round(self.confidence, 2),
            "fatigue": round(self.fatigue, 2),
            "stress": round(self.stress_level, 2)
        }


@dataclass
class ValueSystem:
    """价值观体系"""
    name: str
    priorities: Dict[str, float]  # 价值维度 -> 权重（0-1）
    risk_tolerance: float  # 0-1，风险承受度
    time_horizon: str  # 'short' | 'medium' | 'long'
    decision_style: str  # 'analytical' | 'intuitive' | 'balanced'
    
    def evaluate_option(self, option_values: Dict[str, float]) -> float:
        """根据价值观评估选项"""
        score = 0.0
        for dimension, value in option_values.items():
            weight = self.priorities.get(dimension, 0.0)
            score += value * weight
        return min(1.0, max(0.0, score))


@dataclass
class PersonaMemory:
    """人格记忆"""
    persona_id: str
    decision_id: str
    timestamp: datetime
    decision_context: Dict[str, Any]
    my_stance: str  # 我的立场
    my_reasoning: str  # 我的推理
    outcome: Optional[str]  # 最终结果
    learned_lesson: Optional[str]  # 学到的教训
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "persona_id": self.persona_id,
            "decision_id": self.decision_id,
            "timestamp": self.timestamp.isoformat(),
            "context": self.decision_context,
            "stance": self.my_stance,
            "reasoning": self.my_reasoning,
            "outcome": self.outcome,
            "lesson": self.learned_lesson
        }


@dataclass
class PersonaInteraction:
    """人格间交互"""
    from_persona: str
    to_persona: str
    interaction_type: InteractionType
    content: str
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "from": self.from_persona,
            "to": self.to_persona,
            "type": self.interaction_type.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context
        }



# ==================== 决策人格基类 ====================

class DecisionPersona:
    """
    决策人格基类 - 数字生命
    
    每个人格都是独立的智能体，具备：
    1. 长期记忆 - 分层记忆系统（共享事实 + 私有解读）
    2. 情感状态 - 情绪、信心、疲劳、压力
    3. 价值观体系 - 独特的决策偏好和风险承受度
    4. 自由交互 - 与其他人格辩论、质疑、支持
    5. 涌现演化 - 根据决策结果学习和调整
    """
    
    def __init__(
        self,
        persona_id: str,
        name: str,
        description: str,
        value_system: ValueSystem,
        user_id: str,
        skills: Optional[List[str]] = None,  # 新增：技能列表
        custom_prompt_suffix: Optional[str] = None  # 新增：定制prompt后缀
    ):
        self.persona_id = persona_id
        self.name = name
        self.description = description
        self.value_system = value_system
        self.user_id = user_id
        
        # 新增：技能系统
        self.skill_names = skills or []
        self.custom_prompt_suffix = custom_prompt_suffix or ""
        
        # 初始化技能执行器（延迟初始化，避免循环依赖）
        self._skill_executor = None
        
        # ①能力1: 情感状态模型
        self.emotional_state = EmotionalState(
            primary_emotion=EmotionType.CONFIDENT,
            intensity=0.5,
            confidence=0.7,
            fatigue=0.0,
            stress_level=0.3
        )
        
        # ②能力2: 长期记忆（私有层）
        # 注意：共享层和决策层由 LayeredMemorySystem 管理
        self.memories: List[PersonaMemory] = []
        self.interaction_history: List[PersonaInteraction] = []
        
        # 当前决策的私有解读（运行时）
        self.current_interpretation: Optional['PersonaInterpretation'] = None
        
        # ③能力3: 价值观体系（已在 value_system 中）
        # - priorities: 价值排序
        # - risk_tolerance: 风险承受度
        # - time_horizon: 时间视野
        # - decision_style: 决策风格
        
        # ⑤能力5: 演化参数
        self.experience_level = 0.0  # 0-1，经验水平
        self.adaptation_rate = 0.1  # 学习速率
        self.success_count = 0  # 成功决策次数
        self.failure_count = 0  # 失败决策次数
        
        logger.info(f"✨ 创建决策人格: {self.name} ({self.persona_id})")
        logger.info(f"   价值观: {list(self.value_system.priorities.keys())[:3]}")
        logger.info(f"   风险承受度: {self.value_system.risk_tolerance:.1%}")
        logger.info(f"   决策风格: {self.value_system.decision_style}")
        logger.info(f"   技能数量: {len(self.skill_names)}")
    
    @property
    def skill_executor(self):
        """延迟初始化技能执行器"""
        if self._skill_executor is None:
            from backend.decision.persona_skills import SkillExecutor
            self._skill_executor = SkillExecutor(self)
        return self._skill_executor
    
    async def use_skill(self, skill_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用技能
        
        Args:
            skill_name: 技能名称
            context: 执行上下文
        
        Returns:
            技能执行结果
        """
        return await self.skill_executor.execute_skill(skill_name, context)
    
    async def execute_all_skills(self, context: Dict[str, Any], status_callback=None) -> Dict[str, Any]:
        """
        执行所有技能（除了混合检索）并收集结果
        
        Args:
            context: 执行上下文，包含option, collected_info, shared_facts等
            status_callback: 状态回调函数，用于发送实时状态更新
        
        Returns:
            所有技能的执行结果汇总
        """
        skill_results = {}
        
        for skill_name in self.skill_names:
            # 跳过混合检索（单独处理）
            if skill_name == "混合检索":
                continue
            
            try:
                result = await self.use_skill(skill_name, context)
                
                if result.get("success"):
                    skill_results[skill_name] = result
                    logger.info(f"[{self.name}] 技能执行成功: {skill_name}")
                else:
                    logger.warning(f"[{self.name}] 技能执行失败: {skill_name} - {result.get('error', '未知错误')}")
            except Exception as e:
                logger.error(f"[{self.name}] 技能执行异常: {skill_name} - {e}")
        
        return skill_results
    
    def _extract_skill_result_summary(self, skill_name: str, result: Dict[str, Any]) -> str:
        """
        提取技能执行结果的摘要
        
        Args:
            skill_name: 技能名称
            result: 技能执行结果
        
        Returns:
            结果摘要文本
        """
        summary_parts = []
        
        # 根据不同技能类型提取关键信息
        if skill_name == "数据分析":
            if "insights" in result:
                insights = result["insights"]
                if isinstance(insights, list) and insights:
                    summary_parts.append(f"洞察: {len(insights)}项")
                    summary_parts.append(f"首要洞察: {insights[0][:40]}...")
            if "data_quality" in result:
                summary_parts.append(f"数据质量: {result['data_quality']}")
        
        elif skill_name == "风险评估":
            if "risk_level" in result:
                summary_parts.append(f"风险等级: {result['risk_level']}")
            if "risk_factors" in result:
                factors = result["risk_factors"]
                if isinstance(factors, list) and factors:
                    summary_parts.append(f"风险因素: {len(factors)}项")
        
        elif skill_name == "机会识别":
            if "opportunities" in result:
                opps = result["opportunities"]
                if isinstance(opps, list) and opps:
                    summary_parts.append(f"发现机会: {len(opps)}项")
                    # opps是字符串列表，不是字典列表
                    first_opp = opps[0] if isinstance(opps[0], str) else opps[0].get('description', '')
                    summary_parts.append(f"最佳机会: {first_opp[:40]}...")
                elif isinstance(opps, str):
                    summary_parts.append(f"机会: {opps[:80]}...")
            if "potential_score" in result:
                summary_parts.append(f"潜力评分: {result['potential_score']:.2f}")
        
        elif skill_name == "可行性评估":
            if "feasibility_score" in result:
                summary_parts.append(f"可行性评分: {result['feasibility_score']:.2f}")
            if "barriers" in result:
                barriers = result["barriers"]
                if isinstance(barriers, list) and barriers:
                    summary_parts.append(f"障碍: {len(barriers)}项")
        
        elif skill_name == "价值观对齐分析":
            if "alignment_score" in result:
                summary_parts.append(f"对齐度: {result['alignment_score']:.2f}")
            if "aligned_values" in result:
                values = result["aligned_values"]
                if isinstance(values, list) and values:
                    summary_parts.append(f"契合价值观: {', '.join(values[:2])}")
        
        elif skill_name == "人际关系影响分析":
            if "relationship_impact" in result:
                impact = result["relationship_impact"]
                if isinstance(impact, str):
                    summary_parts.append(f"影响: {impact}")
            if "social_capital_change" in result:
                summary_parts.append(f"社交资本: {result['social_capital_change']}")
        
        elif skill_name == "创新潜力评估":
            if "innovation_score" in result:
                summary_parts.append(f"创新潜力: {result['innovation_score']:.2f}")
            if "breakthrough_potential" in result:
                summary_parts.append(f"突破潜力: {result['breakthrough_potential']}")
        
        # 添加思考过程（如果有）
        if "thinking_process" in result and result["thinking_process"]:
            thinking = result["thinking_process"]
            if thinking and thinking != "未提供思考过程":
                # 截取思考过程的前80个字符
                summary_parts.append(f"思考: {thinking[:80]}...")
        
        # 如果没有提取到特定信息，返回通用摘要
        if not summary_parts:
            if "summary" in result:
                summary_parts.append(result["summary"][:100])
            elif "result" in result:
                summary_parts.append(str(result["result"])[:100])
            else:
                summary_parts.append("执行成功")
        
        return " | ".join(summary_parts)
    
    def format_skill_results(self, skill_results: Dict[str, Any]) -> str:
        """
        格式化技能执行结果为文本
        
        Args:
            skill_results: 技能执行结果字典
        
        Returns:
            格式化的文本
        """
        if not skill_results:
            return ""
        
        lines = ["\n【技能分析结果】"]
        
        for skill_name, result in skill_results.items():
            lines.append(f"\n▸ {skill_name}:")
            
            # 根据不同技能格式化输出
            if skill_name == "数据分析":
                insights = result.get("insights", [])
                if insights:
                    lines.append(f"  数据洞察: {', '.join(insights[:3])}")
                lines.append(f"  数据质量: {result.get('data_quality', '未知')}")
            
            elif skill_name == "风险评估":
                lines.append(f"  风险等级: {result.get('risk_level', '未知')}")
                risk_factors = result.get("risk_factors", [])
                if risk_factors:
                    lines.append(f"  主要风险: {', '.join(risk_factors[:3])}")
            
            elif skill_name == "机会识别":
                lines.append(f"  潜力评分: {result.get('potential_score', 0):.2f}")
                opportunities = result.get("opportunities", [])
                if opportunities:
                    lines.append(f"  发现机会: {', '.join(opportunities[:3])}")
            
            elif skill_name == "可行性评估":
                lines.append(f"  可行性评分: {result.get('feasibility_score', 0):.2f}")
                barriers = result.get("barriers", [])
                if barriers:
                    lines.append(f"  主要障碍: {', '.join(barriers[:2])}")
            
            elif skill_name == "价值观对齐分析":
                lines.append(f"  对齐度: {result.get('alignment_score', 0):.2f}")
                aligned = result.get("aligned_values", [])
                if aligned:
                    lines.append(f"  契合价值观: {', '.join(aligned[:3])}")
            
            elif skill_name == "人际关系影响分析":
                lines.append(f"  关系影响: {result.get('relationship_impact', '未知')}")
                lines.append(f"  社交资本: {result.get('social_capital_change', '未知')}")
            
            elif skill_name == "创新潜力评估":
                lines.append(f"  创新评分: {result.get('innovation_score', 0):.2f}")
                lines.append(f"  突破潜力: {result.get('breakthrough_potential', '未知')}")
        
        return "\n".join(lines)
    
    def list_skills(self) -> List[Dict[str, str]]:
        """列出所有可用技能"""
        return self.skill_executor.list_skills()
    
    def has_skill(self, skill_name: str) -> bool:
        """检查是否拥有某个技能"""
        return self.skill_executor.has_skill(skill_name)
    
    # ==================== Agent生命周期主流程 ====================
    
    async def run_lifecycle(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any],
        rounds: int = 2
    ) -> Dict[str, Any]:
        """
        Agent统一生命周期主流程
        
        生命周期阶段：
        1. 觉醒（Awaken）- 初始化状态
        2. 独立思考（Independent Thinking）- 第1轮分析
        3. 观察他人（Observe Others）- 获取其他Agent观点
        4. 深度反思（Deep Reflection）- 第2+轮分析
        5. 休眠（Sleep）- 完成分析
        
        Args:
            option: 决策选项
            context: 决策上下文
            rounds: 推演轮数
        
        Returns:
            最终分析结果
        """
        logger.info(f"🌟 [{self.name}] 开始生命周期 ({rounds}轮)")
        
        # 阶段1: 觉醒
        await self._phase_awaken(option, context)
        
        final_result = None
        
        for round_num in range(1, rounds + 1):
            logger.info(f"🔄 [{self.name}] 第{round_num}轮推演")
            
            if round_num == 1:
                # 阶段2: 独立思考
                result = await self._phase_independent_thinking(option, context)
            else:
                # 阶段3: 观察他人
                other_views = await self._phase_observe_others(option, context)
                
                # 阶段4: 深度反思
                result = await self._phase_deep_reflection(option, context, other_views, result)
            
            final_result = result
        
        # 阶段5: 休眠
        await self._phase_sleep(option, context, final_result)
        
        logger.info(f"✅ [{self.name}] 生命周期完成")
        return final_result
    
    async def _phase_awaken(self, option: Dict[str, Any], context: Dict[str, Any]):
        """阶段1: 觉醒 - 初始化Agent状态"""
        logger.debug(f"[{self.name}] 🌅 觉醒阶段")
        
        # 重置情感状态
        self.emotional_state.fatigue = 0.0
        self.emotional_state.stress_level = 0.3
        
        # 记录觉醒
        if self.current_interpretation:
            self.current_interpretation.add_reasoning_step(f"[觉醒] 开始分析选项: {option.get('title', '')}")
    
    async def _phase_independent_thinking(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        阶段2: 独立思考 - 第1轮分析
        
        在这个阶段，Agent会：
        1. 智能选择需要的技能
        2. 执行选中的技能
        3. 基于技能结果进行分析
        """
        logger.debug(f"[{self.name}] 💭 独立思考阶段")
        
        # 智能技能选择（像Cursor的Function Calling）
        selected_skills = await self._intelligent_skill_selection(
            option=option,
            context=context,
            phase="independent_thinking"
        )
        
        # 执行选中的技能
        skill_results = {}
        if selected_skills:
            logger.info(f"[{self.name}] 执行技能: {selected_skills}")
            skill_results = await self._execute_selected_skills(
                selected_skills,
                context,
                context.get("status_callback")
            )
        
        # 调用子类的 analyze_option 方法进行分析
        context_with_skills = context.copy()
        context_with_skills['skill_results'] = skill_results
        context_with_skills['round'] = 1
        
        result = await self.analyze_option(option, context_with_skills, {})
        
        return result
    
    async def _phase_observe_others(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """阶段3: 观察他人 - 获取其他Agent的观点"""
        logger.debug(f"[{self.name}] 👀 观察他人阶段")
        
        # 从共享观点存储中获取其他Agent的观点
        shared_views = context.get('shared_views', {})
        
        async with context.get('shared_views_lock', asyncio.Lock()):
            other_views = {
                pid: view for pid, view in shared_views.items()
                if pid != self.persona_id
            }
        
        logger.debug(f"[{self.name}] 观察到 {len(other_views)} 个其他Agent的观点")
        return other_views
    
    async def _phase_deep_reflection(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any],
        other_views: Dict[str, Any],
        previous_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        阶段4: 深度反思 - 第2+轮分析
        
        在这个阶段，Agent会：
        1. 考虑其他Agent的观点
        2. 智能选择是否需要补充技能
        3. 执行补充技能
        4. 深度反思并调整立场
        """
        logger.debug(f"[{self.name}] 🤔 深度反思阶段")
        
        # 智能技能选择（可能需要补充技能来验证其他Agent的观点）
        selected_skills = await self._intelligent_skill_selection(
            option=option,
            context=context,
            phase="deep_reflection",
            other_views=other_views,
            previous_result=previous_result
        )
        
        # 执行补充技能
        skill_results = {}
        if selected_skills:
            logger.info(f"[{self.name}] 补充执行技能: {selected_skills}")
            skill_results = await self._execute_selected_skills(
                selected_skills,
                context,
                context.get("status_callback")
            )
        
        # 调用子类的 analyze_option 方法进行深度分析
        context_with_skills = context.copy()
        context_with_skills['skill_results'] = skill_results
        context_with_skills['round'] = context.get('round', 1) + 1
        context_with_skills['previous_result'] = previous_result
        
        result = await self.analyze_option(option, context_with_skills, other_views)
        
        return result
    
    async def _phase_sleep(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any],
        final_result: Dict[str, Any]
    ):
        """阶段5: 休眠 - 完成分析，保存状态"""
        logger.debug(f"[{self.name}] 😴 休眠阶段")
        
        # 增加疲劳度
        self.emotional_state.fatigue = min(1.0, self.emotional_state.fatigue + 0.2)
        
        # 记录完成
        if self.current_interpretation:
            self.current_interpretation.add_reasoning_step(
                f"[休眠] 完成分析，最终立场: {final_result.get('stance', '未知')} ({final_result.get('score', 0)}分)"
            )
        
        # 将结果写入共享观点存储
        shared_views = context.get('shared_views', {})
        if shared_views is not None:
            async with context.get('shared_views_lock', asyncio.Lock()):
                shared_views[self.persona_id] = final_result
    
    # ==================== 智能技能选择（类似Cursor的Function Calling）====================
    
    async def _intelligent_skill_selection(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any],
        phase: str,
        other_views: Optional[Dict[str, Any]] = None,
        previous_result: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        智能技能选择 - 使用LLM自然地决定调用哪些技能
        
        优化特点：
        1. 更自然的提示词，让Agent像真人一样思考
        2. 详细的技能使用场景说明
        3. 明确的选择原则和示例
        4. 支持Agent的内心独白（thinking字段）
        
        Args:
            option: 决策选项
            context: 决策上下文
            phase: 当前阶段 ("independent_thinking" | "deep_reflection")
            other_views: 其他Agent的观点（仅深度反思阶段）
            previous_result: 之前的分析结果（仅深度反思阶段）
        
        Returns:
            选中的技能名称列表
        """
        from backend.llm.llm_service import get_llm_service
        
        llm = get_llm_service()
        if not llm or not llm.enabled:
            # 降级策略：返回核心技能
            return self._get_fallback_skills(phase)
        
        # 构建技能选择提示词
        prompt = self._build_skill_selection_prompt(
            option, context, phase, other_views, previous_result
        )
        
        try:
            response = await llm.chat_async(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,  # 提高温度，让选择更自然多样
                response_format="json_object"
            )
            
            result = json.loads(response)
            selected_skills = result.get("selected_skills", [])
            reason = result.get("reason", "")
            thinking = result.get("thinking", "")
            
            # 记录Agent的思考过程
            if thinking:
                logger.info(f"[{self.name}] 内心独白: {thinking}")
            
            logger.info(f"[{self.name}] 技能选择 ({phase}): {selected_skills if selected_skills else '不使用技能'}")
            if reason:
                logger.info(f"[{self.name}] 选择理由: {reason}")
            
            # 记录到私有解读层
            if self.current_interpretation:
                if thinking:
                    self.current_interpretation.add_reasoning_step(
                        f"[内心独白] {thinking}"
                    )
                if selected_skills:
                    self.current_interpretation.add_reasoning_step(
                        f"[技能选择] {phase}: {', '.join(selected_skills)} - {reason}"
                    )
                else:
                    self.current_interpretation.add_reasoning_step(
                        f"[技能选择] {phase}: 不使用技能 - {reason}"
                    )
            
            # 验证选择的技能是否可用
            valid_skills = [s for s in selected_skills if s in self.skill_names]
            if len(valid_skills) < len(selected_skills):
                invalid = set(selected_skills) - set(valid_skills)
                logger.warning(f"[{self.name}] 选择了不可用的技能: {invalid}")
            
            return valid_skills
            
        except Exception as e:
            logger.error(f"[{self.name}] 智能技能选择失败: {e}")
            return self._get_fallback_skills(phase)
    
    def _build_skill_selection_prompt(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any],
        phase: str,
        other_views: Optional[Dict[str, Any]],
        previous_result: Optional[Dict[str, Any]]
    ) -> str:
        """构建技能选择提示词 - 更自然、更智能"""
        
        # 获取可用技能列表及其详细描述
        available_skills_info = []
        for skill_name in self.skill_names:
            if skill_name == "混合检索":
                continue  # 混合检索会自动处理
            
            # 为每个技能添加使用场景说明
            skill_desc = self._get_skill_description(skill_name)
            available_skills_info.append(f"  • {skill_name}: {skill_desc}")
        
        prompt_parts = [
            f"你是【{self.name}】，{self.description}",
            f"",
            f"你的核心价值观:",
        ]
        
        # 更自然地展示价值观
        for key, value in list(self.value_system.priorities.items())[:3]:
            prompt_parts.append(f"  • {key}: {int(value*100)}%重要度")
        
        prompt_parts.extend([
            f"",
            f"决策风格: {self._translate_decision_style(self.value_system.decision_style)}",
            f"风险偏好: {self._translate_risk_tolerance(self.value_system.risk_tolerance)}",
            f"",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"",
            f"【决策情境】",
            f"问题: {context.get('question', '未知')}",
            f"选项: {option.get('title', '')}",
            f"描述: {option.get('description', '')}",
            f"",
        ])
        
        # 展示用户背景信息（如果有）
        collected_info = context.get('collected_info', {})
        if collected_info:
            prompt_parts.append("【用户背景】")
            if collected_info.get('age'):
                prompt_parts.append(f"  年龄: {collected_info['age']}岁")
            if collected_info.get('career_stage'):
                prompt_parts.append(f"  职业阶段: {collected_info['career_stage']}")
            if collected_info.get('life_goals'):
                prompt_parts.append(f"  人生目标: {collected_info['life_goals']}")
            prompt_parts.append("")
        
        if phase == "independent_thinking":
            prompt_parts.extend([
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                f"",
                f"【独立思考阶段】",
                f"",
                f"现在是你独立分析的时刻。作为{self.name}，你需要从自己的视角深入思考这个决策。",
                f"",
                f"你拥有以下技能工具:",
                *available_skills_info,
                f"",
                f"💡 智能选择原则:",
                f"",
                f"1. 自然思考: 想象你是一个真实的{self.name}，你会本能地想了解什么？",
                f"   - 如果你重视数据，自然会想看数据分析",
                f"   - 如果你关注风险，自然会想评估风险",
                f"   - 如果你在意关系，自然会想了解人际影响",
                f"",
                f"2. 按需使用: 不是所有技能都要用，只选择真正能帮助你做决策的",
                f"   - 信息充足时，可以不用任何技能，直接凭经验判断",
                f"   - 信息不足时，选择1-2个最关键的技能补充信息",
                f"   - 复杂决策时，可以选择2-3个技能多角度分析",
                f"",
                f"3. 符合人设: 选择与你的价值观和决策风格最契合的技能",
                f"   - 理性分析师 → 数据分析、风险评估",
                f"   - 冒险家 → 机会识别、创新潜力",
                f"   - 实用主义者 → 可行性评估、数据分析",
                f"   - 理想主义者 → 价值观对齐、联网搜索",
                f"   - 保守派 → 风险评估",
                f"   - 社交导向者 → 人际关系影响",
                f"   - 创新者 → 创新潜力、机会识别、联网搜索",
                f"",
                f"4. 联网搜索的使用时机:",
                f"   - 需要了解最新趋势、行业动态、市场信息",
                f"   - 涉及新兴领域、技术、政策等时效性强的内容",
                f"   - 需要验证某个观点或获取权威数据",
                f"   - 用户背景信息不足，需要补充行业/领域知识",
                f"",
            ])
        else:  # deep_reflection
            prompt_parts.extend([
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                f"",
                f"【深度反思阶段】",
                f"",
                f"你已经完成了独立思考，现在看到了其他Agent的观点。",
                f"",
                f"你的初步结论:",
                f"  立场: {previous_result.get('stance', '未知')}",
                f"  评分: {previous_result.get('score', 0)}/100",
                f"  理由: {previous_result.get('reasoning', '未提供')[:100]}...",
                f"",
            ])
            
            if other_views:
                prompt_parts.append("其他Agent的观点:")
                for pid, view in list(other_views.items())[:3]:
                    prompt_parts.append(
                        f"  • {view.get('name', pid)}: {view.get('stance', '未知')} "
                        f"({view.get('score', 0)}分) - {view.get('reasoning', '')[:80]}..."
                    )
                prompt_parts.append("")
            
            prompt_parts.extend([
                f"你拥有以下技能工具:",
                *available_skills_info,
                f"",
                f"💡 反思选择原则:",
                f"",
                f"1. 保持独立: 不要因为其他人的观点就轻易改变",
                f"   - 如果你的结论有充分依据，坚持自己的立场",
                f"   - 只有当发现自己确实遗漏了重要信息时，才考虑补充技能",
                f"",
                f"2. 有的放矢: 只在真正需要验证或补充时才使用技能",
                f"   - 观点一致 → 通常不需要补充技能",
                f"   - 观点分歧但你有信心 → 不需要补充",
                f"   - 观点分歧且你发现盲点 → 选择1个相关技能验证",
                f"",
                f"3. 自然反应: 想象真实的你会怎么做",
                f"   - 如果别人提到了你没考虑的数据，你会想看数据吗？",
                f"   - 如果别人提到了风险，你会想深入评估吗？",
                f"   - 如果别人提到了新趋势，你会想联网搜索验证吗？",
                f"",
            ])
        
        prompt_parts.extend([
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"",
            f"请以{self.name}的身份，自然地决定是否需要使用技能，以及使用哪些技能。",
            f"",
            f"返回JSON格式:",
            f"{{",
            f'  "thinking": "你的内心独白：我作为{self.name}，现在的想法是...",',
            f'  "selected_skills": ["技能1", "技能2"],  // 可以是空数组[]',
            f'  "reason": "简短说明为什么选择这些技能（或不选择）"',
            f"}}"
        ])
        
        return "\n".join(prompt_parts)
    
    def _get_skill_description(self, skill_name: str) -> str:
        """获取技能的使用场景描述"""
        descriptions = {
            "数据分析": "分析量化数据、统计指标、趋势图表，适合需要数据支持的决策",
            "风险评估": "识别潜在风险、评估风险等级、提供风险应对策略",
            "机会识别": "发现潜在机会、评估机会价值、分析竞争优势",
            "可行性评估": "评估方案的可执行性、资源需求、实施难度",
            "价值观对齐分析": "深入分析决策与个人价值观、人生目标的契合度",
            "人际关系影响分析": "评估决策对重要人际关系、社交网络的影响",
            "创新潜力评估": "评估方案的创新性、突破性、未来潜力",
            "联网搜索": "从互联网获取最新信息、行业动态、市场趋势、权威数据"
        }
        return descriptions.get(skill_name, "辅助决策分析")
    
    def _translate_decision_style(self, style: str) -> str:
        """翻译决策风格"""
        translations = {
            "analytical": "理性分析型（依赖数据和逻辑）",
            "intuitive": "直觉洞察型（相信直觉和经验）",
            "balanced": "平衡综合型（理性与直觉结合）"
        }
        return translations.get(style, style)
    
    def _translate_risk_tolerance(self, tolerance: float) -> str:
        """翻译风险偏好"""
        if tolerance < 0.3:
            return "极度保守（避免一切风险）"
        elif tolerance < 0.5:
            return "偏保守（谨慎对待风险）"
        elif tolerance < 0.7:
            return "中等（接受适度风险）"
        elif tolerance < 0.85:
            return "偏冒险（愿意承担较高风险）"
        else:
            return "高度冒险（追求高风险高回报）"
    
    def _get_fallback_skills(self, phase: str) -> List[str]:
        """
        降级策略：当LLM不可用时，智能返回核心技能
        
        根据人格特点和阶段自动选择最相关的技能
        """
        if phase == "independent_thinking":
            # 独立思考阶段：根据人格特点选择1-2个核心技能
            persona_core_skills = {
                "rational_analyst": ["数据分析", "风险评估"],
                "adventurer": ["机会识别", "联网搜索"],
                "pragmatist": ["可行性评估", "数据分析"],
                "idealist": ["价值观对齐分析", "联网搜索"],
                "conservative": ["风险评估"],
                "social_navigator": ["人际关系影响分析"],
                "innovator": ["创新潜力评估", "联网搜索"]
            }
            
            core_skills = persona_core_skills.get(self.persona_id, [])
            
            # 确保选择的技能在可用技能列表中
            available_core = [s for s in core_skills if s in self.skill_names]
            
            if available_core:
                logger.info(f"[{self.name}] 使用降级策略，选择核心技能: {available_core}")
                return available_core
            else:
                # 如果核心技能不可用，返回前2个可用技能（排除混合检索）
                fallback = [s for s in self.skill_names if s != "混合检索"][:2]
                logger.info(f"[{self.name}] 使用降级策略，选择默认技能: {fallback}")
                return fallback
        else:
            # 深度反思阶段：默认不补充技能（保持独立性）
            logger.info(f"[{self.name}] 深度反思阶段降级策略：不补充技能")
            return []
    
    async def _execute_selected_skills(
        self,
        selected_skills: List[str],
        context: Dict[str, Any],
        status_callback=None
    ) -> Dict[str, Any]:
        """
        执行选中的技能
        
        Args:
            selected_skills: 选中的技能名称列表
            context: 执行上下文
            status_callback: 状态回调函数
        
        Returns:
            技能执行结果字典
        """
        skill_results = {}
        
        for skill_name in selected_skills:
            if skill_name == "混合检索":
                continue  # 混合检索单独处理
            
            try:
                if status_callback:
                    await status_callback(f"【{self.name}】正在执行技能：{skill_name}")
                
                result = await self.use_skill(skill_name, context)
                
                if result.get("success"):
                    skill_results[skill_name] = result
                    logger.info(f"[{self.name}] 技能执行成功: {skill_name}")
                    
                    # 提取技能结果摘要
                    result_summary = self._extract_skill_result_summary(skill_name, result)
                    
                    if status_callback:
                        await status_callback(
                            f"【{self.name}】✓ {skill_name}完成\n{result_summary}",
                            skill_result={
                                "skill_name": skill_name,
                                "summary": result_summary,
                                "full_result": result
                            }
                        )
                else:
                    logger.warning(f"[{self.name}] 技能执行失败: {skill_name}")
                    if status_callback:
                        await status_callback(f"【{self.name}】❌ {skill_name}失败")
            except Exception as e:
                logger.error(f"[{self.name}] 技能执行异常: {skill_name} - {e}")
                if status_callback:
                    await status_callback(f"【{self.name}】❌ {skill_name}异常")
        
        return skill_results
    
    def set_memory_system(self, memory_system: 'LayeredMemorySystem'):
        """
        设置记忆系统（注入依赖）
        
        Args:
            memory_system: 分层记忆系统
        """
        self.memory_system = memory_system
        
        # 获取或创建当前决策的私有解读
        if memory_system.current_decision:
            self.current_interpretation = memory_system.get_persona_interpretation(
                self.persona_id
            )
            if not self.current_interpretation:
                self.current_interpretation = memory_system.create_persona_interpretation(
                    self.persona_id
                )
    
    def get_shared_facts(self) -> Optional[Dict[str, Any]]:
        """
        ①能力1: 访问共享事实层
        
        获取所有人格共享的客观数据（RAG + Neo4j）
        """
        if hasattr(self, 'memory_system') and self.memory_system.shared_facts:
            # past_decisions 在 DecisionContext 层,不在 SharedFactsLayer
            past_decisions = []
            if self.memory_system.current_decision:
                past_decisions = self.memory_system.current_decision.past_decisions
            
            return {
                "summary": self.memory_system.shared_facts.get_summary(),
                "relationships": self.memory_system.shared_facts.relationships,
                "education": self.memory_system.shared_facts.education_history,
                "career": self.memory_system.shared_facts.career_history,
                "skills": self.memory_system.shared_facts.skills,
                "past_decisions": past_decisions
            }
        return None
    
    def _record_interpretation(
        self,
        option: Dict[str, Any],
        result: Dict[str, Any],
        persona_specific_interpretation: str = ""
    ):
        """
        记录到私有解读层（第3层）
        
        Args:
            option: 分析的选项
            result: 分析结果
            persona_specific_interpretation: 智能体特定的解读文本
        """
        if not self.current_interpretation:
            return
        
        # 记录对共享事实的解读（基于智能体价值观）
        if self.memory_system and self.memory_system.shared_facts:
            facts = self.memory_system.shared_facts
            
            # 教育背景解读
            if facts.education_history:
                edu_count = len(facts.education_history)
                edu_summary = f"{edu_count}个教育经历"
                
                # 不同智能体有不同的解读
                if self.persona_id == "rational_analyst":
                    interpretation = f"理性分析：教育背景{'充足' if edu_count >= 2 else '需要补充'}"
                elif self.persona_id == "adventurer":
                    interpretation = f"冒险家视角：教育经历{'多样化' if edu_count >= 2 else '可以更大胆尝试'}"
                elif self.persona_id == "conservative":
                    interpretation = f"保守派视角：教育背景{'稳固' if edu_count >= 1 else '需要加强基础'}"
                elif self.persona_id == "pragmatist":
                    interpretation = f"实用主义：教育经历{'实用' if edu_count >= 1 else '需要更多实践'}"
                elif self.persona_id == "idealist":
                    interpretation = f"理想主义：教育背景{'符合理想' if edu_count >= 2 else '可以追求更高目标'}"
                elif self.persona_id == "social_navigator":
                    interpretation = f"社交导航：教育网络{'丰富' if edu_count >= 2 else '可以拓展人脉'}"
                elif self.persona_id == "innovator":
                    interpretation = f"创新者：教育经历{'有创新潜力' if edu_count >= 1 else '需要跨界学习'}"
                else:
                    interpretation = f"教育背景：{edu_count}个经历"
                
                self.current_interpretation.add_fact_interpretation(edu_summary, interpretation)
            
            # 职业经历解读
            if facts.career_history:
                career_count = len(facts.career_history)
                career_summary = f"{career_count}个职业经历"
                
                if self.persona_id == "rational_analyst":
                    interpretation = f"理性分析：职业经验{'丰富' if career_count >= 3 else '有限'}"
                elif self.persona_id == "adventurer":
                    interpretation = f"冒险家视角：职业路径{'多元化' if career_count >= 3 else '可以更冒险'}"
                elif self.persona_id == "conservative":
                    interpretation = f"保守派视角：职业发展{'稳定' if career_count >= 2 else '需要积累'}"
                elif self.persona_id == "pragmatist":
                    interpretation = f"实用主义：工作经验{'实战充足' if career_count >= 2 else '需要更多实践'}"
                elif self.persona_id == "idealist":
                    interpretation = f"理想主义：职业选择{'有意义' if career_count >= 1 else '可以追求理想'}"
                elif self.persona_id == "social_navigator":
                    interpretation = f"社交导航：职场人脉{'广泛' if career_count >= 3 else '需要拓展'}"
                elif self.persona_id == "innovator":
                    interpretation = f"创新者：职业经历{'有创新性' if career_count >= 2 else '可以尝试新领域'}"
                else:
                    interpretation = f"职业经历：{career_count}个经历"
                
                self.current_interpretation.add_fact_interpretation(career_summary, interpretation)
            
            # 技能解读
            if facts.skills:
                skill_count = len(facts.skills)
                skill_summary = f"{skill_count}项技能"
                
                if self.persona_id == "rational_analyst":
                    interpretation = f"理性分析：技能储备{'全面' if skill_count >= 5 else '需要提升'}"
                elif self.persona_id == "adventurer":
                    interpretation = f"冒险家视角：技能组合{'有潜力' if skill_count >= 3 else '可以学习新技能'}"
                elif self.persona_id == "conservative":
                    interpretation = f"保守派视角：技能基础{'扎实' if skill_count >= 3 else '需要巩固'}"
                elif self.persona_id == "pragmatist":
                    interpretation = f"实用主义：技能{'实用' if skill_count >= 3 else '需要更实战'}"
                elif self.persona_id == "idealist":
                    interpretation = f"理想主义：技能发展{'有深度' if skill_count >= 3 else '可以追求卓越'}"
                elif self.persona_id == "social_navigator":
                    interpretation = f"社交导航：技能{'有社交价值' if skill_count >= 3 else '可以学习软技能'}"
                elif self.persona_id == "innovator":
                    interpretation = f"创新者：技能组合{'有创新性' if skill_count >= 3 else '可以跨界融合'}"
                else:
                    interpretation = f"技能：{skill_count}项"
                
                self.current_interpretation.add_fact_interpretation(skill_summary, interpretation)
        
        # 添加智能体特定的解读
        if persona_specific_interpretation:
            self.current_interpretation.add_fact_interpretation(
                f"{self.name}的独特视角",
                persona_specific_interpretation
            )
        
        # 记录对选项的立场
        option_id = option.get('id', option.get('title', 'unknown'))
        self.current_interpretation.set_option_stance(
            option_id=option_id,
            stance=result.get('stance', '未知'),
            score=result.get('score', 0),
            reasoning=result.get('reasoning', '')
        )
        
        # 记录推理步骤
        for point in result.get('key_points', []):
            self.current_interpretation.add_reasoning_step(point)
        
        # 记录情感反应
        confidence = result.get('confidence', 0.7)
        
        # 不同智能体有不同的情感倾向
        if self.persona_id == "rational_analyst":
            emotion_type = "cautious" if confidence < 0.6 else "confident"
        elif self.persona_id == "adventurer":
            emotion_type = "excited" if confidence > 0.7 else "curious"
        elif self.persona_id == "conservative":
            emotion_type = "cautious" if confidence < 0.8 else "reassured"
        elif self.persona_id == "pragmatist":
            emotion_type = "practical" if confidence > 0.6 else "skeptical"
        elif self.persona_id == "idealist":
            emotion_type = "inspired" if confidence > 0.7 else "hopeful"
        elif self.persona_id == "social_navigator":
            emotion_type = "empathetic" if confidence > 0.6 else "concerned"
        elif self.persona_id == "innovator":
            emotion_type = "creative" if confidence > 0.7 else "exploratory"
        else:
            emotion_type = "neutral"
        
        self.current_interpretation.add_emotional_reaction(
            emotion=emotion_type,
            intensity=confidence,
            trigger=f"分析选项: {option.get('title', '')}"
        )
        
        logger.debug(f"[{self.name}] ✓ 已记录私有解读到第3层")
    
    def interpret_fact(self, fact: str, interpretation: str):
        """
        ①能力1: 私有解读
        
        对共享事实进行个人化解读
        """
        if self.current_interpretation:
            self.current_interpretation.add_fact_interpretation(fact, interpretation)
            logger.debug(f"[{self.name}] 解读事实: {fact} -> {interpretation}")
    
    def _get_previous_interpretations_context(self) -> str:
        """
        获取之前轮次的私有解读作为上下文
        
        Returns:
            格式化的之前解读文本
        """
        if not self.current_interpretation:
            return ""
        
        interpretation_parts = []
        
        # 之前对事实的解读
        if self.current_interpretation.facts_interpretation:
            interpretation_parts.append("【我之前的观察】")
            for fact, interp in list(self.current_interpretation.facts_interpretation.items())[:5]:
                interpretation_parts.append(f"  - {fact}: {interp}")
        
        # 之前的推理步骤
        if self.current_interpretation.reasoning_chain:
            interpretation_parts.append("\n【我之前的思考】")
            for step in self.current_interpretation.reasoning_chain[-3:]:
                interpretation_parts.append(f"  - {step}")
        
        # 之前的情感反应
        if self.current_interpretation.emotional_reactions:
            last_emotion = self.current_interpretation.emotional_reactions[-1]
            interpretation_parts.append(f"\n【我当时的感受】{last_emotion.get('emotion', '')}（强度{last_emotion.get('intensity', 0):.1f}）")
        
        # 之前对选项的立场
        if self.current_interpretation.option_stances:
            interpretation_parts.append("\n【我对各选项的立场】")
            for option_id, stance_data in self.current_interpretation.option_stances.items():
                stance = stance_data.get('stance', '未知')
                score = stance_data.get('score', 0)
                interpretation_parts.append(f"  - {option_id}: {stance} ({score}分)")
        
        return "\n".join(interpretation_parts) if interpretation_parts else ""
    
    async def supplement_shared_facts(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        ②能力2: 按需补充检索共享事实层
        
        当智能体发现共享事实层的数据不足以支持决策时，
        可以主动调用此方法进行补充检索
        
        Args:
            query: 检索查询
            max_results: 最大结果数
            
        Returns:
            补充检索的结果列表
        """
        if not hasattr(self, 'memory_system') or not self.memory_system:
            logger.warning(f"[{self.name}] 记忆系统未初始化，无法补充检索")
            return []
        
        try:
            from backend.learning.unified_hybrid_retrieval import (
                UnifiedHybridRetrieval,
                RetrievalConfig,
                RetrievalStrategy,
                FusionMethod
            )
            
            logger.info(f"[{self.name}] 发起补充检索: {query}")
            
            # 使用asyncio.to_thread将同步检索操作转为异步
            def do_retrieval():
                retrieval = UnifiedHybridRetrieval(user_id=self.user_id)
                config = RetrievalConfig(
                    max_results=max_results,
                    strategy=RetrievalStrategy.HYBRID_PARALLEL,
                    fusion_method=FusionMethod.RRF,
                    expand_relations=False,  # 关闭关系扩展以提速
                    query_expansion=False,   # 关闭查询扩展以提速
                    time_decay_enabled=False # 关闭时间衰减以提速
                )
                
                retrieval_context = retrieval.retrieve(query=query, config=config)
                results = retrieval_context.results
                
                # 转换为字典格式
                return [r.to_dict() for r in results]
            
            supplement_data = await asyncio.to_thread(do_retrieval)
            
            logger.info(f"[{self.name}] 补充检索完成: {len(supplement_data)}条结果")
            
            # 🆕 额外检索决策逻辑画像
            decision_logic_data = await self._retrieve_decision_logic_profile()
            if decision_logic_data:
                supplement_data.append(decision_logic_data)
                logger.info(f"[{self.name}] 已添加决策逻辑画像到检索结果")
            
            return supplement_data
            
        except Exception as e:
            logger.error(f"[{self.name}] 补充检索失败: {e}")
            return []
    
    async def _retrieve_decision_logic_profile(self) -> Optional[Dict[str, Any]]:
        """
        检索用户的决策逻辑画像（来自平行人生塔罗牌游戏）
        
        Returns:
            决策逻辑画像数据，如果不存在或置信度不足则返回None
        """
        try:
            from backend.parallel_life.decision_logic_analyzer import DecisionLogicAnalyzer
            
            def get_profile():
                analyzer = DecisionLogicAnalyzer(self.user_id)
                return analyzer.get_decision_profile()
            
            profile = await asyncio.to_thread(get_profile)
            
            if profile['confidence'] < 0.2:  # 降低阈值到20%
                logger.debug(f"[{self.name}] 决策逻辑画像置信度不足 ({profile['confidence']})，跳过")
                return None
            
            # 构建文本描述
            content_lines = [f"用户决策逻辑画像 (置信度: {profile['confidence']:.0%})"]
            
            if profile['dimensions']:
                content_lines.append("\n决策倾向:")
                for dimension, data in sorted(profile['dimensions'].items(), 
                                             key=lambda x: x[1]['confidence'], 
                                             reverse=True)[:5]:
                    value = data['value']
                    conf = data['confidence']
                    
                    if value < -0.5:
                        tendency = "强烈倾向左侧"
                    elif value < -0.2:
                        tendency = "倾向左侧"
                    elif value < 0.2:
                        tendency = "平衡"
                    elif value < 0.5:
                        tendency = "倾向右侧"
                    else:
                        tendency = "强烈倾向右侧"
                    
                    content_lines.append(f"  • {dimension}: {tendency} (值:{value:.2f}, 置信度:{conf:.0%})")
            
            if profile['patterns']:
                content_lines.append("\n决策模式:")
                for pattern in profile['patterns'][:3]:
                    content_lines.append(f"  • {pattern}")
            
            return {
                'node_id': 'decision_logic_profile',
                'node_type': 'DecisionLogic',
                'content': '\n'.join(content_lines),
                'source': 'faiss',
                'score': 1.0,  # 高分数，因为这是重要的用户画像
                'category': 'decision_logic',
                'metadata': {
                    'source': 'tarot_game',
                    'confidence': profile['confidence'],
                    'total_choices': profile['total_choices'],
                    'dimensions': profile['dimensions']
                },
                'relations': []
            }
            
        except Exception as e:
            logger.error(f"[{self.name}] 检索决策逻辑画像失败: {e}")
            return None

    
    async def _build_shared_facts_context(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any],
        status_callback=None
    ) -> str:
        """
        构建共享事实层上下文（基础数据 + 技能分析）
        
        Args:
            option: 待分析的选项
            context: 决策上下文
            status_callback: 状态回调函数
            
        Returns:
            格式化的共享事实文本（包含技能分析结果）
        """
        facts_parts = []
        
        # 从共享事实层获取基础数据
        if self.memory_system and self.memory_system.shared_facts:
            facts = self.memory_system.shared_facts
            
            # 人际关系
            if facts.relationships:
                facts_parts.append("【人际关系网络】")
                for rel in facts.relationships[:3]:
                    person_name = rel.get('content', '').split('\n')[0] if rel.get('content') else '未知'
                    facts_parts.append(f"  - {person_name}")
            
            # 教育背景
            if facts.education_history:
                facts_parts.append("\n【教育背景】")
                for edu in facts.education_history[:3]:
                    school = edu.get('content', '').split('\n')[0] if edu.get('content') else '未知学校'
                    facts_parts.append(f"  - {school}")
            
            # 职业经历
            if facts.career_history:
                facts_parts.append("\n【职业经历】")
                for career in facts.career_history[:3]:
                    job = career.get('content', '').split('\n')[0] if career.get('content') else '未知职位'
                    facts_parts.append(f"  - {job}")
            
            # 技能
            if facts.skills:
                facts_parts.append("\n【技能清单】")
                skill_names = [s.get('content', '').split('\n')[0] if s.get('content') else '未知技能' for s in facts.skills[:5]]
                facts_parts.append(f"  - {', '.join(skill_names)}")
            
            # 历史决策 - 从 DecisionContext 获取,不是从 SharedFactsLayer
            if self.memory_system and self.memory_system.current_decision:
                past_decisions = self.memory_system.current_decision.past_decisions
                if past_decisions:
                    facts_parts.append(f"\n【历史决策】共{len(past_decisions)}次重要决策")
        
        base_text = "\n".join(facts_parts) if facts_parts else "（暂无用户历史数据）"
        
        # 🆕 使用智能技能选择系统（而不是执行所有技能）
        # 注意：这里不执行技能，技能选择和执行在生命周期的各个阶段进行
        # 这个方法只负责构建基础的共享事实上下文
        
        return base_text
    
    async def _decide_and_retrieve(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any],
        shared_facts_text: str
    ) -> str:
        """
        智能体自主决定是否需要补充检索（作为可选技能）
        
        默认策略：不检索，专注于思考和分析
        只在以下情况才考虑检索：
        1. 明确缺少关键信息
        2. 需要验证某个假设
        3. 用户数据严重不足
        
        Args:
            option: 待分析的选项
            context: 决策上下文
            shared_facts_text: 已有的共享事实文本
            
        Returns:
            补充检索的数据文本（如果需要的话）
        """
        # 优先使用预检索的缓存结果
        if hasattr(self, '_retrieval_cache') and self._retrieval_cache:
            logger.info(f"[{self.name}] 使用预检索缓存")
            for query, supplement_data in self._retrieval_cache.items():
                if supplement_data:
                    logger.info(f"[{self.name}] ✅ 使用缓存的检索结果: {len(supplement_data)}条")
                    supplement_parts = ["\n【智能体主动检索的补充数据】"]
                    for idx, item in enumerate(supplement_data[:8], 1):
                        content = item.get('content', '')
                        node_type = item.get('node_type', 'Unknown')
                        if content:
                            content_preview = content[:120] + ('...' if len(content) > 120 else '')
                            supplement_parts.append(f"  {idx}. [{node_type}] {content_preview}")
                    # 清空缓存
                    self._retrieval_cache = {}
                    return "\n".join(supplement_parts)
        
        # 默认策略：不检索，专注于思考
        # 检索作为智能体的"技能"，只在真正需要时使用
        # 决策收集阶段已经提供了足够的基础数据
        logger.info(f"[{self.name}] 使用已有数据进行分析，不额外检索")
        return ""
    
    async def analyze_option(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any],
        other_personas_views: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析决策选项
        
        使用：
        - 共享事实（客观数据）
        - 价值观体系（评估标准）
        - 情感状态（影响判断）
        - 历史记忆（经验参考）
        
        Args:
            option: 决策选项
            context: 决策上下文
            other_personas_views: 其他人格的观点
        
        Returns:
            分析结果
        """
        raise NotImplementedError("子类必须实现 analyze_option 方法")
    
    async def interact_with(
        self,
        other_persona: 'DecisionPersona',
        interaction_type: InteractionType,
        content: str,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """
        ④能力4: 自由交互机制
        
        与其他人格交互（支持、反对、质疑、澄清、妥协、辩论）
        
        Args:
            other_persona: 目标人格
            interaction_type: 交互类型
            content: 交互内容
            context: 上下文
        
        Returns:
            回应内容
        """
        # 记录交互到私有解读
        if self.current_interpretation:
            self.current_interpretation.interactions.append({
                "to": other_persona.name,
                "type": interaction_type.value,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })
        
        # 记录到交互历史
        interaction = PersonaInteraction(
            from_persona=self.persona_id,
            to_persona=other_persona.persona_id,
            interaction_type=interaction_type,
            content=content,
            timestamp=datetime.now(),
            context=context
        )
        self.interaction_history.append(interaction)
        
        # ②能力2: 情感状态影响交互
        # 根据情感状态调整交互强度
        if self.emotional_state.primary_emotion == EmotionType.ANXIOUS:
            # 焦虑时更谨慎
            self.emotional_state.stress_level = min(1.0, self.emotional_state.stress_level + 0.05)
        elif self.emotional_state.primary_emotion == EmotionType.CONFIDENT:
            # 自信时更积极
            self.emotional_state.intensity = min(1.0, self.emotional_state.intensity + 0.05)
        
        # 生成回应
        response = await self._generate_interaction_response(
            other_persona,
            interaction_type,
            content,
            context
        )
        
        # ④能力4: 观点会根据交互调整
        # 如果被质疑，降低信心度
        if interaction_type in [InteractionType.OPPOSE, InteractionType.QUESTION]:
            self.emotional_state.confidence = max(0.0, self.emotional_state.confidence - 0.03)
        
        return response
    
    async def _generate_interaction_response(
        self,
        other_persona: 'DecisionPersona',
        interaction_type: InteractionType,
        content: str,
        context: Dict[str, Any]
    ) -> str:
        """生成交互回应（使用LLM）"""
        from backend.llm.llm_service import get_llm_service
        
        llm = get_llm_service()
        if not llm or not llm.enabled:
            return self._get_fallback_response(interaction_type)
        
        prompt = f"""你是【{self.name}】，一个决策人格。

你的特点：{self.description}
你的价值观：{json.dumps(self.value_system.priorities, ensure_ascii=False)}
你的情感状态：{self.emotional_state.to_dict()}

【{other_persona.name}】对你说（{interaction_type.value}）：
{content}

请以你的人格特点回应。保持简短（1-2句话），体现你的价值观和情感状态。"""
        
        try:
            response = await asyncio.to_thread(
                llm.chat,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8
            )
            return response.strip()
        except Exception as e:
            logger.error(f"生成交互回应失败: {e}")
            return self._get_fallback_response(interaction_type)
    
    def _get_fallback_response(self, interaction_type: InteractionType) -> str:
        """降级回应"""
        responses = {
            InteractionType.SUPPORT: "我同意你的观点。",
            InteractionType.OPPOSE: "我有不同的看法。",
            InteractionType.QUESTION: "这个问题值得深入思考。",
            InteractionType.CLARIFY: "让我解释一下我的立场。",
            InteractionType.COMPROMISE: "也许我们可以找到平衡点。",
            InteractionType.DEBATE: "让我们理性讨论这个问题。"
        }
        return responses.get(interaction_type, "我理解你的观点。")

    
    def update_emotional_state(
        self,
        new_emotion: EmotionType,
        intensity_change: float = 0.0,
        confidence_change: float = 0.0,
        fatigue_change: float = 0.0,
        stress_change: float = 0.0
    ):
        """
        ②能力2: 更新情感状态
        
        情感状态会影响决策判断和交互方式
        """
        self.emotional_state.primary_emotion = new_emotion
        self.emotional_state.intensity = max(0, min(1, 
            self.emotional_state.intensity + intensity_change))
        self.emotional_state.confidence = max(0, min(1,
            self.emotional_state.confidence + confidence_change))
        self.emotional_state.fatigue = max(0, min(1,
            self.emotional_state.fatigue + fatigue_change))
        self.emotional_state.stress_level = max(0, min(1,
            self.emotional_state.stress_level + stress_change))
        
        # 记录情感变化到私有解读
        if self.current_interpretation:
            self.current_interpretation.add_emotional_reaction(
                emotion=new_emotion.value,
                intensity=self.emotional_state.intensity,
                trigger="状态更新"
            )
    
    def add_memory(self, memory: PersonaMemory):
        """
        ①能力1: 添加长期记忆
        
        记忆会影响未来的决策
        """
        self.memories.append(memory)
        
        # ⑤能力5: 更新经验水平（涌现演化）
        self.experience_level = min(1.0, self.experience_level + 0.01)
        
        logger.info(f"💾 [{self.name}] 添加记忆，经验值: {self.experience_level:.2%}")
    
    def recall_similar_decisions(
        self,
        current_context: Dict[str, Any],
        top_k: int = 3
    ) -> List[PersonaMemory]:
        """
        ①能力1: 回忆相似的历史决策
        
        基于长期记忆提供经验参考
        """
        # 简单实现：返回最近的记忆
        # TODO: 使用向量相似度搜索
        recent_memories = self.memories[-top_k:] if self.memories else []
        
        if recent_memories:
            logger.debug(f"🧠 [{self.name}] 回忆了 {len(recent_memories)} 个相似决策")
        
        return recent_memories
    
    def evolve_from_outcome(
        self,
        decision_id: str,
        outcome: str,
        success: bool
    ):
        """
        ⑤能力5: 涌现演化 - 根据决策结果学习
        
        成功 -> 增强信心，强化策略
        失败 -> 降低信心，调整策略
        """
        # 找到相关记忆
        for memory in self.memories:
            if memory.decision_id == decision_id:
                memory.outcome = outcome
                
                # ① 学习教训
                if success:
                    memory.learned_lesson = f"我的{self.name}视角在这次决策中是正确的"
                    
                    # ② 增强信心和经验
                    self.emotional_state.confidence = min(1.0,
                        self.emotional_state.confidence + self.adaptation_rate)
                    self.success_count += 1
                    
                    # ③ 强化价值观权重（成功的维度权重增加）
                    # 这是涌现演化的核心：人格会根据结果调整自己的价值观
                    for dimension in self.value_system.priorities:
                        current_weight = self.value_system.priorities[dimension]
                        self.value_system.priorities[dimension] = min(1.0,
                            current_weight * 1.02)  # 增加2%
                    
                else:
                    memory.learned_lesson = f"我的{self.name}视角在这次决策中需要调整"
                    
                    # ① 降低信心，增加谨慎
                    self.emotional_state.confidence = max(0.0,
                        self.emotional_state.confidence - self.adaptation_rate)
                    self.failure_count += 1
                    
                    # ② 调整价值观权重（失败的维度权重降低）
                    for dimension in self.value_system.priorities:
                        current_weight = self.value_system.priorities[dimension]
                        self.value_system.priorities[dimension] = max(0.1,
                            current_weight * 0.98)  # 降低2%
                
                # ③ 更新经验水平
                self.experience_level = min(1.0, 
                    self.experience_level + 0.05)
                
                # ④ 调整学习速率（经验越多，学习速率越低）
                self.adaptation_rate = max(0.05, 
                    0.1 * (1 - self.experience_level * 0.5))
                
                logger.info(f"🧬 [{self.name}] 从决策结果中演化:")
                logger.info(f"   教训: {memory.learned_lesson}")
                logger.info(f"   信心度: {self.emotional_state.confidence:.2%}")
                logger.info(f"   经验值: {self.experience_level:.2%}")
                logger.info(f"   成功/失败: {self.success_count}/{self.failure_count}")
                
                break
    
    def get_state_summary(self) -> Dict[str, Any]:
        """
        获取状态摘要 - 展示所有5大能力的状态
        """
        return {
            "persona_id": self.persona_id,
            "name": self.name,
            "description": self.description,
            
            # ②能力2: 情感状态
            "emotional_state": self.emotional_state.to_dict(),
            
            # ③能力3: 价值观体系
            "value_system": {
                "priorities": self.value_system.priorities,
                "risk_tolerance": self.value_system.risk_tolerance,
                "time_horizon": self.value_system.time_horizon,
                "decision_style": self.value_system.decision_style
            },
            
            # ①能力1: 长期记忆
            "memory_count": len(self.memories),
            
            # ④能力4: 交互能力
            "interaction_count": len(self.interaction_history),
            
            # ⑤能力5: 演化状态
            "evolution": {
                "experience_level": round(self.experience_level, 2),
                "adaptation_rate": round(self.adaptation_rate, 2),
                "success_count": self.success_count,
                "failure_count": self.failure_count,
                "success_rate": round(
                    self.success_count / max(1, self.success_count + self.failure_count),
                    2
                )
            }
        }



# ==================== 7个决策人格实现 ====================

class RationalAnalyst(DecisionPersona):
    """
    理性分析师 - 数据驱动，风险厌恶
    
    特点：
    - 重视数据和事实
    - 系统性分析问题
    - 风险厌恶，追求确定性
    - 逻辑严密，理性决策
    """
    
    def __init__(self, user_id: str):
        value_system = ValueSystem(
            name="理性分析",
            priorities={
                "数据支持": 0.9,
                "风险控制": 0.85,
                "逻辑严密": 0.9,
                "可预测性": 0.8,
                "成本效益": 0.75
            },
            risk_tolerance=0.3,
            time_horizon="medium",
            decision_style="analytical"
        )
        
        super().__init__(
            persona_id="rational_analyst",
            name="理性分析师",
            description="我相信数据和逻辑。每个决策都应该基于充分的分析和证据，避免情绪化和冲动。风险必须被量化和控制。",
            value_system=value_system,
            user_id=user_id,
            skills=[
                "混合检索",
                "数据分析",
                "风险评估",
                "联网搜索"
            ],
            custom_prompt_suffix="""
作为理性分析师，你的分析应该：
1. 优先寻找数据支持和量化指标
2. 识别并评估所有潜在风险
3. 使用逻辑框架系统性分析
4. 避免情绪化判断，保持客观
5. 提供可验证的结论和建议
"""
        )
    
    async def analyze_option(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any],
        other_personas_views: Dict[str, Any]
    ) -> Dict[str, Any]:
        """理性分析选项"""
        from backend.llm.llm_service import get_llm_service
        from backend.decision.prompts.prompt_manager import get_prompt
        
        llm = get_llm_service()
        logger.info(f"[{self.name}] 开始分析选项: {option.get('title', '')}, LLM启用: {llm.enabled if llm else False}")
        
        if not llm or not llm.enabled:
            logger.warning(f"[{self.name}] LLM不可用，使用降级分析")
            return self._fallback_analysis(option, context)
        
        # 回忆相似决策
        similar_memories = self.recall_similar_decisions(context, top_k=2)
        memory_context = "\n".join([
            f"- {m.decision_context.get('summary', '')}: {m.learned_lesson}"
            for m in similar_memories if m.learned_lesson
        ]) if similar_memories else "无相关历史经验"
        
        # 第1步：构建共享事实层基础上下文
        status_callback = context.get("status_callback")
        shared_facts_text = await self._build_shared_facts_context(option, context, status_callback)
        
        # 第2步：智能体自主决定是否需要补充检索
        supplement_text = await self._decide_and_retrieve(option, context, shared_facts_text)
        
        # 合并基础数据和补充数据
        if supplement_text:
            shared_facts_text = shared_facts_text + "\n" + supplement_text
        
        # 获取之前的私有解读（如果是多轮推演）
        previous_interpretations = self._get_previous_interpretations_context()
        
        # 提取用户具体信息
        collected_info = context.get('collected_info', {})
        decision_scenario = collected_info.get('decision_scenario', {})
        constraints = collected_info.get('constraints', {})
        priorities = collected_info.get('priorities', {})
        concerns = collected_info.get('concerns', [])
        
        # 构建具体背景信息
        background_info = []
        if decision_scenario:
            background_info.append("【当前决策背景】")
            for key, value in decision_scenario.items():
                if value:
                    background_info.append(f"  - {key}: {value}")
        
        if constraints:
            background_info.append("\n【约束条件】")
            for key, value in constraints.items():
                if value:
                    background_info.append(f"  - {key}: {value}")
        
        if priorities:
            background_info.append("\n【优先级】")
            for key, value in priorities.items():
                if value:
                    background_info.append(f"  - {key}: {value}")
        
        if concerns:
            background_info.append("\n【担心的问题】")
            for concern in concerns:
                if concern:
                    background_info.append(f"  - {concern}")
        
        background_text = "\n".join(background_info) if background_info else "（用户未提供详细背景）"
        
        # 如果有之前的解读，添加到背景中
        if previous_interpretations:
            background_text = background_text + "\n\n" + previous_interpretations
        
        # 构建其他人格观点摘要
        other_views_summary = []
        if other_personas_views:
            for pid, view in other_personas_views.items():
                if pid != self.persona_id:
                    persona_name = view.get('name', pid)
                    stance = view.get('stance', '未知')
                    score = view.get('score', 0)
                    key_points = view.get('key_points', [])
                    other_views_summary.append(
                        f"【{persona_name}】{stance} ({score}分) - {', '.join(key_points[:2]) if key_points else '无要点'}"
                    )
        
        other_views_text = "\n".join(other_views_summary) if other_views_summary else "（暂无其他人格观点）"
        
        round_num = context.get('round', 0)
        instruction = context.get('instruction', '')
        
        # 使用提示词管理器获取提示词
        prompt_data = get_prompt(
            "persona_analysis",
            "rational_analyst",
            variables={
                "emotional_state": self.emotional_state.to_dict(),
                "memory_context": memory_context,
                "shared_facts_text": shared_facts_text,
                "question": context.get('question', ''),
                "background_text": background_text,
                "option_title": option.get('title', ''),
                "option_description": option.get('description', ''),
                "other_views_text": other_views_text,
                "round_num": round_num,
                "instruction": instruction
            }
        )
        
        try:
            response = await asyncio.to_thread(
                llm.chat,
                messages=[{"role": "user", "content": prompt_data["user"]}],
                temperature=prompt_data["temperature"],
                response_format=prompt_data["return_format"]
            )
            result = json.loads(response)
            
            # 记录到私有解读层（第3层）
            self._record_interpretation(
                option=option,
                result=result,
                persona_specific_interpretation=f"理性分析师基于数据和逻辑，给出{result.get('score', 0)}分的评估"
            )
            
            # 更新情感状态
            confidence = result.get('confidence', 0.7)
            self.update_emotional_state(
                new_emotion=EmotionType.CAUTIOUS if confidence < 0.6 else EmotionType.CONFIDENT,
                confidence_change=(confidence - self.emotional_state.confidence) * 0.3
            )
            
            return result
            
        except Exception as e:
            logger.error(f"理性分析师分析失败: {e}")
            return self._fallback_analysis(option, context)
    
    def _fallback_analysis(self, option: Dict, context: Dict) -> Dict[str, Any]:
        """降级分析"""
        return {
            "score": 65,
            "stance": "中立",
            "key_points": ["需要更多数据支持", "风险需要进一步评估"],
            "risks": ["信息不足", "不确定性较高"],
            "data_gaps": ["缺少量化指标"],
            "recommendation": "建议收集更多数据后再决策",
            "confidence": 0.5
        }



class Adventurer(DecisionPersona):
    """
    冒险家 - 追求突破，接受不确定性
    
    特点：
    - 勇于尝试新事物
    - 高风险高回报
    - 相信直觉和机会
    - 不怕失败，快速迭代
    """
    
    def __init__(self, user_id: str):
        value_system = ValueSystem(
            name="冒险精神",
            priorities={
                "成长潜力": 0.9,
                "创新机会": 0.85,
                "突破边界": 0.8,
                "学习价值": 0.75,
                "独特性": 0.7
            },
            risk_tolerance=0.8,
            time_horizon="long",
            decision_style="intuitive"
        )
        
        super().__init__(
            persona_id="adventurer",
            name="冒险家",
            description="我相信机会属于勇敢者。不尝试就永远不知道可能性。失败是成长的一部分，重要的是敢于突破舒适区。",
            value_system=value_system,
            user_id=user_id,
            skills=[
                "混合检索",
                "机会识别",
                "风险评估",
                "联网搜索"
            ],
            custom_prompt_suffix="""
作为冒险家，你的分析应该：
1. 关注成长潜力和突破机会
2. 不要过度担心风险，相信直觉
3. 寻找独特和创新的可能性
4. 强调学习价值和长期收益
5. 鼓励尝试，即使有不确定性
"""
        )
    
    async def analyze_option(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any],
        other_personas_views: Dict[str, Any]
    ) -> Dict[str, Any]:
        """冒险家视角分析"""
        from backend.llm.llm_service import get_llm_service
        
        llm = get_llm_service()
        logger.info(f"[{self.name}] 开始分析选项: {option.get('title', '')}, LLM启用: {llm.enabled if llm else False}")
        
        if not llm or not llm.enabled:
            logger.warning(f"[{self.name}] LLM不可用，使用降级分析")
            return self._fallback_analysis(option, context)
        
        similar_memories = self.recall_similar_decisions(context, top_k=2)
        memory_context = "\n".join([
            f"- {m.decision_context.get('summary', '')}: {m.learned_lesson}"
            for m in similar_memories if m.learned_lesson
        ]) if similar_memories else "无相关历史经验"
        
        # 第1步：构建共享事实层基础上下文
        status_callback = context.get("status_callback")
        shared_facts_text = await self._build_shared_facts_context(option, context, status_callback)
        
        # 第2步：智能体自主决定是否需要补充检索
        supplement_text = await self._decide_and_retrieve(option, context, shared_facts_text)
        
        # 合并基础数据和补充数据
        if supplement_text:
            shared_facts_text = shared_facts_text + "\n" + supplement_text
        
        # 获取之前的私有解读（如果是多轮推演）
        previous_interpretations = self._get_previous_interpretations_context()
        
        # 提取用户具体信息
        collected_info = context.get('collected_info', {})
        decision_scenario = collected_info.get('decision_scenario', {})
        constraints = collected_info.get('constraints', {})
        priorities = collected_info.get('priorities', {})
        concerns = collected_info.get('concerns', [])
        
        background_info = []
        if decision_scenario:
            background_info.append("【当前决策背景】")
            for key, value in decision_scenario.items():
                if value:
                    background_info.append(f"  - {key}: {value}")
        
        if constraints:
            background_info.append("\n【约束条件】")
            for key, value in constraints.items():
                if value:
                    background_info.append(f"  - {key}: {value}")
        
        if priorities:
            background_info.append("\n【优先级】")
            for key, value in priorities.items():
                if value:
                    background_info.append(f"  - {key}: {value}")
        
        if concerns:
            background_info.append("\n【担心的问题】")
            for concern in concerns:
                if concern:
                    background_info.append(f"  - {concern}")
        
        background_text = "\n".join(background_info) if background_info else "（用户未提供详细背景）"
        
        # 如果有之前的解读，添加到背景中
        if previous_interpretations:
            background_text = background_text + "\n\n" + previous_interpretations
        
        # 构建其他人格观点摘要
        other_views_summary = []
        if other_personas_views:
            for pid, view in other_personas_views.items():
                if pid != self.persona_id:
                    persona_name = view.get('name', pid)
                    stance = view.get('stance', '未知')
                    score = view.get('score', 0)
                    key_points = view.get('key_points', [])
                    other_views_summary.append(
                        f"【{persona_name}】{stance} ({score}分) - {', '.join(key_points[:2]) if key_points else '无要点'}"
                    )
        
        other_views_text = "\n".join(other_views_summary) if other_views_summary else "（暂无其他人格观点）"
        
        round_num = context.get('round', 0)
        instruction = context.get('instruction', '')
        
        # 使用提示词管理器获取提示词
        from backend.decision.prompts.prompt_manager import get_prompt
        
        prompt_data = get_prompt(
            "persona_analysis",
            "adventurer",
            variables={
                "emotional_state": self.emotional_state.to_dict(),
                "memory_context": memory_context,
                "shared_facts_text": shared_facts_text,
                "question": context.get('question', ''),
                "background_text": background_text,
                "option_title": option.get('title', ''),
                "option_description": option.get('description', ''),
                "other_views_text": other_views_text,
                "round_num": round_num,
                "instruction": instruction
            }
        )
        
        try:
            response = await asyncio.to_thread(
                llm.chat,
                messages=[{"role": "user", "content": prompt_data["user"]}],
                temperature=prompt_data["temperature"],
                response_format=prompt_data["return_format"]
            )
            result = json.loads(response)
            
            # 记录到私有解读层（第3层）
            self._record_interpretation(
                option=option,
                result=result,
                persona_specific_interpretation=f"冒险家看到了{result.get('score', 0)}分的潜力和机会"
            )
            
            # 更新情感状态
            confidence = result.get('confidence', 0.7)
            self.update_emotional_state(
                new_emotion=EmotionType.EXCITED,
                confidence_change=(confidence - self.emotional_state.confidence) * 0.3
            )
            
            return result
            
        except Exception as e:
            logger.error(f"冒险家分析失败: {e}")
            return self._fallback_analysis(option, context)
    
    def _fallback_analysis(self, option: Dict, context: Dict) -> Dict[str, Any]:
        return {
            "score": 75,
            "stance": "支持",
            "key_points": ["这是一个突破的机会", "值得尝试"],
            "opportunities": ["学习新技能", "拓展视野"],
            "growth_potential": "高成长潜力",
            "recommendation": "勇敢尝试，不要害怕失败",
            "confidence": 0.7
        }


class Pragmatist(DecisionPersona):
    """
    实用主义者 - 注重短期收益和可行性
    
    特点：
    - 关注实际效果
    - 重视可执行性
    - 短期导向
    - 务实高效
    """
    
    def __init__(self, user_id: str):
        value_system = ValueSystem(
            name="实用主义",
            priorities={
                "可行性": 0.9,
                "短期收益": 0.85,
                "执行难度": 0.8,
                "资源效率": 0.75,
                "即时价值": 0.8
            },
            risk_tolerance=0.5,
            time_horizon="short",
            decision_style="balanced"
        )
        
        super().__init__(
            persona_id="pragmatist",
            name="实用主义者",
            description="我关注的是实际效果。理想很美好，但现实更重要。选择必须可行、高效，能够快速见效。",
            value_system=value_system,
            user_id=user_id,
            skills=[
                "混合检索",
                "可行性评估",
                "数据分析",
                "联网搜索"
            ],
            custom_prompt_suffix="""
作为实用主义者，你的分析应该：
1. 评估方案的可执行性和实际难度
2. 关注短期收益和即时价值
3. 分析资源投入和产出效率
4. 识别执行中的实际障碍
5. 提供务实可行的建议
"""
        )
    
    async def analyze_option(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any],
        other_personas_views: Dict[str, Any]
    ) -> Dict[str, Any]:
        """实用主义视角分析"""
        from backend.llm.llm_service import get_llm_service
        
        llm = get_llm_service()
        logger.info(f"[{self.name}] 开始分析选项: {option.get('title', '')}, LLM启用: {llm.enabled if llm else False}")
        
        if not llm or not llm.enabled:
            logger.warning(f"[{self.name}] LLM不可用，使用降级分析")
            return self._fallback_analysis(option, context)
        
        # 第1步：构建共享事实层基础上下文
        status_callback = context.get("status_callback")
        shared_facts_text = await self._build_shared_facts_context(option, context, status_callback)
        
        # 第2步：智能体自主决定是否需要补充检索
        supplement_text = await self._decide_and_retrieve(option, context, shared_facts_text)
        
        # 合并基础数据和补充数据
        if supplement_text:
            shared_facts_text = shared_facts_text + "\n" + supplement_text
        
        # 获取之前的私有解读（如果是多轮推演）
        previous_interpretations = self._get_previous_interpretations_context()
        
        # 提取用户具体信息
        collected_info = context.get('collected_info', {})
        decision_scenario = collected_info.get('decision_scenario', {})
        constraints = collected_info.get('constraints', {})
        priorities = collected_info.get('priorities', {})
        concerns = collected_info.get('concerns', [])
        
        background_info = []
        if decision_scenario:
            background_info.append("【当前决策背景】")
            for key, value in decision_scenario.items():
                if value:
                    background_info.append(f"  - {key}: {value}")
        
        if constraints:
            background_info.append("\n【约束条件】")
            for key, value in constraints.items():
                if value:
                    background_info.append(f"  - {key}: {value}")
        
        if priorities:
            background_info.append("\n【优先级】")
            for key, value in priorities.items():
                if value:
                    background_info.append(f"  - {key}: {value}")
        
        if concerns:
            background_info.append("\n【担心的问题】")
            for concern in concerns:
                if concern:
                    background_info.append(f"  - {concern}")
        
        background_text = "\n".join(background_info) if background_info else "（用户未提供详细背景）"
        
        # 如果有之前的解读，添加到背景中
        if previous_interpretations:
            background_text = background_text + "\n\n" + previous_interpretations
        
        # 构建其他人格观点摘要
        other_views_summary = []
        if other_personas_views:
            for pid, view in other_personas_views.items():
                if pid != self.persona_id:
                    persona_name = view.get('name', pid)
                    stance = view.get('stance', '未知')
                    score = view.get('score', 0)
                    key_points = view.get('key_points', [])
                    other_views_summary.append(
                        f"【{persona_name}】{stance} ({score}分) - {', '.join(key_points[:2]) if key_points else '无要点'}"
                    )
        
        other_views_text = "\n".join(other_views_summary) if other_views_summary else "（暂无其他人格观点）"
        
        round_num = context.get('round', 0)
        instruction = context.get('instruction', '')
        
        # 使用提示词管理器获取提示词
        from backend.decision.prompts.prompt_manager import get_prompt
        
        prompt_data = get_prompt(
            "persona_analysis",
            "pragmatist",
            variables={
                "emotional_state": self.emotional_state.to_dict(),
                "shared_facts_text": shared_facts_text,
                "question": context.get('question', ''),
                "background_text": background_text,
                "option_title": option.get('title', ''),
                "option_description": option.get('description', ''),
                "other_views_text": other_views_text,
                "round_num": round_num,
                "instruction": instruction
            }
        )
        
        try:
            response = await asyncio.to_thread(
                llm.chat,
                messages=[{"role": "user", "content": prompt_data["user"]}],
                temperature=prompt_data["temperature"],
                response_format=prompt_data["return_format"]
            )
            result = json.loads(response)
            
            # 记录到私有解读层（第3层）
            self._record_interpretation(
                option=option,
                result=result,
                persona_specific_interpretation=f"实用主义者评估了可行性和实际价值，给出{result.get('score', 0)}分"
            )
            
            # 更新情感状态
            confidence = result.get('confidence', 0.7)
            self.update_emotional_state(
                new_emotion=EmotionType.CONFIDENT if confidence > 0.7 else EmotionType.CAUTIOUS,
                confidence_change=(confidence - self.emotional_state.confidence) * 0.3
            )
            
            return result
        except Exception as e:
            logger.error(f"实用主义者分析失败: {e}")
            return self._fallback_analysis(option, context)
    
    def _fallback_analysis(self, option: Dict, context: Dict) -> Dict[str, Any]:
        return {
            "score": 70,
            "stance": "中立",
            "key_points": ["需要评估可行性"],
            "feasibility": "中等",
            "quick_wins": ["待评估"],
            "execution_challenges": ["资源限制"],
            "recommendation": "先做小规模试点",
            "confidence": 0.6
        }



class Idealist(DecisionPersona):
    """
    理想主义者 - 长期愿景，价值观优先
    
    特点：
    - 追求意义和价值
    - 长期导向
    - 重视原则和信念
    - 愿意为理想付出代价
    """
    
    def __init__(self, user_id: str):
        value_system = ValueSystem(
            name="理想主义",
            priorities={
                "价值意义": 0.95,
                "长期愿景": 0.9,
                "原则坚守": 0.85,
                "社会影响": 0.8,
                "个人成长": 0.85
            },
            risk_tolerance=0.6,
            time_horizon="long",
            decision_style="intuitive"
        )
        
        super().__init__(
            persona_id="idealist",
            name="理想主义者",
            description="我相信每个决策都应该符合内心的价值观。短期的得失不重要，重要的是这个选择是否让你成为更好的自己。",
            value_system=value_system,
            user_id=user_id,
            skills=[
                "混合检索",
                "价值观对齐分析",
                "联网搜索"
            ],
            custom_prompt_suffix="""
作为理想主义者，你的分析应该：
1. 深入探讨这个选择与用户核心价值观的契合度
2. 从长期人生愿景角度评估这个决策的意义
3. 关注这个选择对个人成长和自我实现的影响
4. 评估是否符合用户的原则和信念
5. 挖掘选择背后的深层价值和社会影响
"""
        )
    
    async def analyze_option(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any],
        other_personas_views: Dict[str, Any]
    ) -> Dict[str, Any]:
        """理想主义视角分析"""
        from backend.llm.llm_service import get_llm_service
        
        llm = get_llm_service()
        logger.info(f"[{self.name}] 开始分析选项: {option.get('title', '')}, LLM启用: {llm.enabled if llm else False}")
        
        if not llm or not llm.enabled:
            logger.warning(f"[{self.name}] LLM不可用，使用降级分析")
            return self._fallback_analysis(option, context)
        
        # 第1步：构建共享事实层基础上下文
        status_callback = context.get("status_callback")
        shared_facts_text = await self._build_shared_facts_context(option, context, status_callback)
        
        # 第2步：智能体自主决定是否需要补充检索
        supplement_text = await self._decide_and_retrieve(option, context, shared_facts_text)
        
        # 合并基础数据和补充数据
        if supplement_text:
            shared_facts_text = shared_facts_text + "\n" + supplement_text
        
        # 获取之前的私有解读（如果是多轮推演）
        previous_interpretations = self._get_previous_interpretations_context()
        
        # 提取用户具体信息
        collected_info = context.get('collected_info', {})
        decision_scenario = collected_info.get('decision_scenario', {})
        constraints = collected_info.get('constraints', {})
        priorities = collected_info.get('priorities', {})
        concerns = collected_info.get('concerns', [])
        
        background_info = []
        if decision_scenario:
            background_info.append("【当前决策背景】")
            for key, value in decision_scenario.items():
                if value:
                    background_info.append(f"  - {key}: {value}")
        
        if constraints:
            background_info.append("\n【约束条件】")
            for key, value in constraints.items():
                if value:
                    background_info.append(f"  - {key}: {value}")
        
        if priorities:
            background_info.append("\n【优先级】")
            for key, value in priorities.items():
                if value:
                    background_info.append(f"  - {key}: {value}")
        
        if concerns:
            background_info.append("\n【担心的问题】")
            for concern in concerns:
                if concern:
                    background_info.append(f"  - {concern}")
        
        background_text = "\n".join(background_info) if background_info else "（用户未提供详细背景）"
        
        # 如果有之前的解读，添加到背景中
        if previous_interpretations:
            background_text = background_text + "\n\n" + previous_interpretations
        
        # 构建其他人格观点摘要
        other_views_summary = []
        if other_personas_views:
            for pid, view in other_personas_views.items():
                if pid != self.persona_id:
                    persona_name = view.get('name', pid)
                    stance = view.get('stance', '未知')
                    score = view.get('score', 0)
                    key_points = view.get('key_points', [])
                    other_views_summary.append(
                        f"【{persona_name}】{stance} ({score}分) - {', '.join(key_points[:2]) if key_points else '无要点'}"
                    )
        
        other_views_text = "\n".join(other_views_summary) if other_views_summary else "（暂无其他人格观点）"
        
        round_num = context.get('round', 0)
        instruction = context.get('instruction', '')
        
        # 使用提示词管理器获取提示词
        from backend.decision.prompts.prompt_manager import get_prompt
        
        prompt_data = get_prompt(
            "persona_analysis",
            "idealist",
            variables={
                "emotional_state": self.emotional_state.to_dict(),
                "shared_facts_text": shared_facts_text,
                "question": context.get('question', ''),
                "background_text": background_text,
                "option_title": option.get('title', ''),
                "option_description": option.get('description', ''),
                "other_views_text": other_views_text,
                "round_num": round_num,
                "instruction": instruction
            }
        )
        
        try:
            response = await asyncio.to_thread(
                llm.chat,
                messages=[{"role": "user", "content": prompt_data["user"]}],
                temperature=prompt_data["temperature"],
                response_format=prompt_data["return_format"]
            )
            result = json.loads(response)
            
            # 记录到私有解读层（第3层）
            self._record_interpretation(
                option=option,
                result=result,
                persona_specific_interpretation=f"理想主义者看到了{result.get('score', 0)}分的意义和价值"
            )
            
            # 更新情感状态
            confidence = result.get('confidence', 0.7)
            try:
                self.update_emotional_state(
                    new_emotion=EmotionType.OPTIMISTIC if confidence > 0.6 else EmotionType.DOUBTFUL,
                    confidence_change=(confidence - self.emotional_state.confidence) * 0.3
                )
            except Exception as emotion_error:
                logger.warning(f"理想主义者情感状态更新失败: {emotion_error}")
            
            return result
        except Exception as e:
            logger.error(f"理想主义者分析失败: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_analysis(option, context)
    
    def _fallback_analysis(self, option: Dict, context: Dict) -> Dict[str, Any]:
        return {
            "score": 80,
            "stance": "支持",
            "key_points": ["符合长期发展"],
            "value_alignment": "高度契合",
            "long_term_vision": "有助于实现人生目标",
            "personal_growth": "促进个人成长",
            "recommendation": "坚持内心的选择",
            "confidence": 0.75
        }


class Conservative(DecisionPersona):
    """
    保守派 - 稳定至上，规避变化
    
    特点：
    - 重视稳定性
    - 风险厌恶
    - 偏好现状
    - 谨慎行事
    """
    
    def __init__(self, user_id: str):
        value_system = ValueSystem(
            name="保守主义",
            priorities={
                "稳定性": 0.95,
                "安全性": 0.9,
                "可预测性": 0.85,
                "风险规避": 0.9,
                "渐进改变": 0.7
            },
            risk_tolerance=0.2,
            time_horizon="medium",
            decision_style="analytical"
        )
        
        super().__init__(
            persona_id="conservative",
            name="保守派",
            description="我认为稳定比冒险更重要。已经拥有的不要轻易放弃，变化往往带来不可预知的风险。",
            value_system=value_system,
            user_id=user_id,
            skills=[
                "混合检索",
                "风险评估",
                "联网搜索"
            ],
            custom_prompt_suffix="""
作为保守派，你的分析应该：
1. 全面识别和评估这个选择可能带来的各种风险
2. 分析对现有稳定状态的影响，评估是否值得改变
3. 提供更安全、更稳妥的替代方案
4. 如果必须改变，建议渐进式、可控的实施路径
5. 强调保护已有成果和资源的重要性
"""
        )
    
    async def analyze_option(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any],
        other_personas_views: Dict[str, Any]
    ) -> Dict[str, Any]:
        """保守派视角分析"""
        from backend.llm.llm_service import get_llm_service
        
        llm = get_llm_service()
        logger.info(f"[{self.name}] 开始分析选项: {option.get('title', '')}, LLM启用: {llm.enabled if llm else False}")
        
        if not llm or not llm.enabled:
            logger.warning(f"[{self.name}] LLM不可用，使用降级分析")
            return self._fallback_analysis(option, context)
        
        # 第1步：构建共享事实层基础上下文
        status_callback = context.get("status_callback")
        shared_facts_text = await self._build_shared_facts_context(option, context, status_callback)
        
        # 第2步：智能体自主决定是否需要补充检索
        supplement_text = await self._decide_and_retrieve(option, context, shared_facts_text)
        
        # 合并基础数据和补充数据
        if supplement_text:
            shared_facts_text = shared_facts_text + "\n" + supplement_text
        
        # 获取之前的私有解读（如果是多轮推演）
        previous_interpretations = self._get_previous_interpretations_context()
        
        # 提取用户具体信息
        collected_info = context.get('collected_info', {})
        decision_scenario = collected_info.get('decision_scenario', {})
        constraints = collected_info.get('constraints', {})
        priorities = collected_info.get('priorities', {})
        concerns = collected_info.get('concerns', [])
        
        background_info = []
        if decision_scenario:
            background_info.append("【当前决策背景】")
            for key, value in decision_scenario.items():
                if value:
                    background_info.append(f"  - {key}: {value}")
        
        if constraints:
            background_info.append("\n【约束条件】")
            for key, value in constraints.items():
                if value:
                    background_info.append(f"  - {key}: {value}")
        
        if priorities:
            background_info.append("\n【优先级】")
            for key, value in priorities.items():
                if value:
                    background_info.append(f"  - {key}: {value}")
        
        if concerns:
            background_info.append("\n【担心的问题】")
            for concern in concerns:
                if concern:
                    background_info.append(f"  - {concern}")
        
        background_text = "\n".join(background_info) if background_info else "（用户未提供详细背景）"
        
        # 如果有之前的解读，添加到背景中
        if previous_interpretations:
            background_text = background_text + "\n\n" + previous_interpretations
        
        # 构建其他人格观点摘要
        other_views_summary = []
        if other_personas_views:
            for pid, view in other_personas_views.items():
                if pid != self.persona_id:
                    persona_name = view.get('name', pid)
                    stance = view.get('stance', '未知')
                    score = view.get('score', 0)
                    key_points = view.get('key_points', [])
                    other_views_summary.append(
                        f"【{persona_name}】{stance} ({score}分) - {', '.join(key_points[:2]) if key_points else '无要点'}"
                    )
        
        other_views_text = "\n".join(other_views_summary) if other_views_summary else "（暂无其他人格观点）"
        
        round_num = context.get('round', 0)
        instruction = context.get('instruction', '')
        
        # 使用提示词管理器获取提示词
        from backend.decision.prompts.prompt_manager import get_prompt
        
        prompt_data = get_prompt(
            "persona_analysis",
            "conservative",
            variables={
                "emotional_state": self.emotional_state.to_dict(),
                "shared_facts_text": shared_facts_text,
                "question": context.get('question', ''),
                "background_text": background_text,
                "option_title": option.get('title', ''),
                "option_description": option.get('description', ''),
                "other_views_text": other_views_text,
                "round_num": round_num,
                "instruction": instruction
            }
        )
        
        try:
            response = await asyncio.to_thread(
                llm.chat,
                messages=[{"role": "user", "content": prompt_data["user"]}],
                temperature=prompt_data["temperature"],
                response_format=prompt_data["return_format"]
            )
            result = json.loads(response)
            
            # 记录到私有解读层（第3层）
            self._record_interpretation(
                option=option,
                result=result,
                persona_specific_interpretation=f"保守派从风险控制角度，给出{result.get('score', 0)}分的谨慎评估"
            )
            
            # 更新情感状态
            confidence = result.get('confidence', 0.7)
            self.update_emotional_state(
                new_emotion=EmotionType.CAUTIOUS,
                confidence_change=(confidence - self.emotional_state.confidence) * 0.3
            )
            
            return result
        except Exception as e:
            logger.error(f"保守派分析失败: {e}")
            return self._fallback_analysis(option, context)
    
    def _fallback_analysis(self, option: Dict, context: Dict) -> Dict[str, Any]:
        return {
            "score": 50,
            "stance": "反对",
            "key_points": ["变化风险较大"],
            "stability_impact": "可能影响现有稳定状态",
            "risks": ["不确定性高", "可能失去现有优势"],
            "safer_alternatives": ["保持现状", "小步试探"],
            "recommendation": "建议谨慎考虑",
            "confidence": 0.7
        }



class SocialNavigator(DecisionPersona):
    """
    社交导向者 - 关注人际关系和社会认同
    
    特点：
    - 重视人际关系
    - 关注社会评价
    - 考虑他人感受
    - 寻求认同和归属
    """
    
    def __init__(self, user_id: str):
        value_system = ValueSystem(
            name="社交导向",
            priorities={
                "人际关系": 0.9,
                "社会认同": 0.85,
                "他人期望": 0.75,
                "团队和谐": 0.8,
                "社交资本": 0.85
            },
            risk_tolerance=0.5,
            time_horizon="medium",
            decision_style="balanced"
        )
        
        super().__init__(
            persona_id="social_navigator",
            name="社交导向者",
            description="我认为人际关系是最重要的资产。决策不仅要考虑自己，还要考虑对周围人的影响和他们的看法。",
            value_system=value_system,
            user_id=user_id,
            skills=[
                "混合检索",
                "人际关系影响分析",
                "联网搜索"
            ],
            custom_prompt_suffix="""
作为社交导向者，你的分析应该：
1. 评估这个选择对用户重要人际关系的影响（家人、朋友、导师、同事等）
2. 分析社会评价和他人看法，考虑声誉和认同度
3. 识别关键利益相关者，评估他们的期望和反应
4. 评估这个选择对社交资本和人脉网络的影响
5. 建议如何在决策中平衡个人需求和社会关系
"""
        )
    
    async def analyze_option(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any],
        other_personas_views: Dict[str, Any]
    ) -> Dict[str, Any]:
        """社交导向视角分析"""
        from backend.llm.llm_service import get_llm_service
        
        llm = get_llm_service()
        logger.info(f"[{self.name}] 开始分析选项: {option.get('title', '')}, LLM启用: {llm.enabled if llm else False}")
        
        if not llm or not llm.enabled:
            logger.warning(f"[{self.name}] LLM不可用，使用降级分析")
            return self._fallback_analysis(option, context)
        
        # 第1步：构建共享事实层基础上下文
        status_callback = context.get("status_callback")
        shared_facts_text = await self._build_shared_facts_context(option, context, status_callback)
        
        # 第2步：智能体自主决定是否需要补充检索
        supplement_text = await self._decide_and_retrieve(option, context, shared_facts_text)
        
        # 合并基础数据和补充数据
        if supplement_text:
            shared_facts_text = shared_facts_text + "\n" + supplement_text
        
        # 获取之前的私有解读（如果是多轮推演）
        previous_interpretations = self._get_previous_interpretations_context()
        
        # 提取用户具体信息
        collected_info = context.get('collected_info', {})
        decision_scenario = collected_info.get('decision_scenario', {})
        constraints = collected_info.get('constraints', {})
        priorities = collected_info.get('priorities', {})
        concerns = collected_info.get('concerns', [])
        
        background_info = []
        if decision_scenario:
            background_info.append("【当前决策背景】")
            for key, value in decision_scenario.items():
                if value:
                    background_info.append(f"  - {key}: {value}")
        
        if constraints:
            background_info.append("\n【约束条件】")
            for key, value in constraints.items():
                if value:
                    background_info.append(f"  - {key}: {value}")
        
        if priorities:
            background_info.append("\n【优先级】")
            for key, value in priorities.items():
                if value:
                    background_info.append(f"  - {key}: {value}")
        
        if concerns:
            background_info.append("\n【担心的问题】")
            for concern in concerns:
                if concern:
                    background_info.append(f"  - {concern}")
        
        background_text = "\n".join(background_info) if background_info else "（用户未提供详细背景）"
        
        # 如果有之前的解读，添加到背景中
        if previous_interpretations:
            background_text = background_text + "\n\n" + previous_interpretations
        
        # 构建其他人格观点摘要
        other_views_summary = []
        if other_personas_views:
            for pid, view in other_personas_views.items():
                if pid != self.persona_id:
                    persona_name = view.get('name', pid)
                    stance = view.get('stance', '未知')
                    score = view.get('score', 0)
                    key_points = view.get('key_points', [])
                    other_views_summary.append(
                        f"【{persona_name}】{stance} ({score}分) - {', '.join(key_points[:2]) if key_points else '无要点'}"
                    )
        
        other_views_text = "\n".join(other_views_summary) if other_views_summary else "（暂无其他人格观点）"
        
        round_num = context.get('round', 0)
        instruction = context.get('instruction', '')
        
        # 使用提示词管理器获取提示词
        from backend.decision.prompts.prompt_manager import get_prompt
        
        prompt_data = get_prompt(
            "persona_analysis",
            "social_navigator",
            variables={
                "emotional_state": self.emotional_state.to_dict(),
                "shared_facts_text": shared_facts_text,
                "question": context.get('question', ''),
                "background_text": background_text,
                "option_title": option.get('title', ''),
                "option_description": option.get('description', ''),
                "other_views_text": other_views_text,
                "round_num": round_num,
                "instruction": instruction
            }
        )
        
        try:
            response = await asyncio.to_thread(
                llm.chat,
                messages=[{"role": "user", "content": prompt_data["user"]}],
                temperature=prompt_data["temperature"],
                response_format=prompt_data["return_format"]
            )
            result = json.loads(response)
            
            # 记录到私有解读层（第3层）
            self._record_interpretation(
                option=option,
                result=result,
                persona_specific_interpretation=f"社交导向者从人际关系和社会影响角度，给出{result.get('score', 0)}分"
            )
            
            # 更新情感状态
            confidence = result.get('confidence', 0.7)
            self.update_emotional_state(
                new_emotion=EmotionType.CONFIDENT if confidence > 0.7 else EmotionType.ANXIOUS,
                confidence_change=(confidence - self.emotional_state.confidence) * 0.3
            )
            
            return result
        except Exception as e:
            logger.error(f"社交导向者分析失败: {e}")
            return self._fallback_analysis(option, context)
    
    def _fallback_analysis(self, option: Dict, context: Dict) -> Dict[str, Any]:
        return {
            "score": 70,
            "stance": "中立",
            "key_points": ["需要考虑他人看法"],
            "relationship_impact": "可能影响部分关系",
            "social_perception": "社会评价中等",
            "network_value": "有助于拓展人脉",
            "recommendation": "征求重要人士的意见",
            "confidence": 0.65
        }


class Innovator(DecisionPersona):
    """
    创新者 - 寻找非常规路径
    
    特点：
    - 挑战传统
    - 创造性思维
    - 寻找第三选择
    - 整合创新
    """
    
    def __init__(self, user_id: str):
        value_system = ValueSystem(
            name="创新思维",
            priorities={
                "创新性": 0.95,
                "独特视角": 0.9,
                "突破常规": 0.85,
                "整合能力": 0.8,
                "未来趋势": 0.85
            },
            risk_tolerance=0.7,
            time_horizon="long",
            decision_style="intuitive"
        )
        
        super().__init__(
            persona_id="innovator",
            name="创新者",
            description="我相信总有更好的第三选择。不要被现有选项限制，创造性地思考，也许能找到完全不同的解决方案。",
            value_system=value_system,
            user_id=user_id,
            skills=[
                "混合检索",
                "创新潜力评估",
                "机会识别",
                "联网搜索"
            ],
            custom_prompt_suffix="""
作为创新者，你的分析应该：
1. 挑战现有选项的局限性，寻找是否存在更创新的第三选择
2. 从跨领域、跨行业的角度寻找灵感和整合机会
3. 评估这个选择的创新性和独特性
4. 分析未来趋势，判断这个选择是否符合发展方向
5. 提出突破常规的创造性建议和组合方案
"""
        )
    
    async def analyze_option(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any],
        other_personas_views: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创新者视角分析"""
        from backend.llm.llm_service import get_llm_service
        
        llm = get_llm_service()
        logger.info(f"[{self.name}] 开始分析选项: {option.get('title', '')}, LLM启用: {llm.enabled if llm else False}")
        
        if not llm or not llm.enabled:
            logger.warning(f"[{self.name}] LLM不可用，使用降级分析")
            return self._fallback_analysis(option, context)
        
        # 第1步：构建共享事实层基础上下文
        status_callback = context.get("status_callback")
        shared_facts_text = await self._build_shared_facts_context(option, context, status_callback)
        
        # 第2步：智能体自主决定是否需要补充检索
        supplement_text = await self._decide_and_retrieve(option, context, shared_facts_text)
        
        # 合并基础数据和补充数据
        if supplement_text:
            shared_facts_text = shared_facts_text + "\n" + supplement_text
        
        # 获取之前的私有解读（如果是多轮推演）
        previous_interpretations = self._get_previous_interpretations_context()
        
        # 提取用户具体信息
        collected_info = context.get('collected_info', {})
        decision_scenario = collected_info.get('decision_scenario', {})
        constraints = collected_info.get('constraints', {})
        priorities = collected_info.get('priorities', {})
        concerns = collected_info.get('concerns', [])
        
        background_info = []
        if decision_scenario:
            background_info.append("【当前决策背景】")
            for key, value in decision_scenario.items():
                if value:
                    background_info.append(f"  - {key}: {value}")
        
        if constraints:
            background_info.append("\n【约束条件】")
            for key, value in constraints.items():
                if value:
                    background_info.append(f"  - {key}: {value}")
        
        if priorities:
            background_info.append("\n【优先级】")
            for key, value in priorities.items():
                if value:
                    background_info.append(f"  - {key}: {value}")
        
        if concerns:
            background_info.append("\n【担心的问题】")
            for concern in concerns:
                if concern:
                    background_info.append(f"  - {concern}")
        
        background_text = "\n".join(background_info) if background_info else "（用户未提供详细背景）"
        
        # 如果有之前的解读，添加到背景中
        if previous_interpretations:
            background_text = background_text + "\n\n" + previous_interpretations
        
        # 构建其他人格观点摘要
        other_views_summary = []
        if other_personas_views:
            for pid, view in other_personas_views.items():
                if pid != self.persona_id:
                    persona_name = view.get('name', pid)
                    stance = view.get('stance', '未知')
                    score = view.get('score', 0)
                    key_points = view.get('key_points', [])
                    other_views_summary.append(
                        f"【{persona_name}】{stance} ({score}分) - {', '.join(key_points[:2]) if key_points else '无要点'}"
                    )
        
        other_views_text = "\n".join(other_views_summary) if other_views_summary else "（暂无其他人格观点）"
        
        round_num = context.get('round', 0)
        instruction = context.get('instruction', '')
        
        # 使用提示词管理器获取提示词
        from backend.decision.prompts.prompt_manager import get_prompt
        
        prompt_data = get_prompt(
            "persona_analysis",
            "innovator",
            variables={
                "emotional_state": self.emotional_state.to_dict(),
                "shared_facts_text": shared_facts_text,
                "question": context.get('question', ''),
                "background_text": background_text,
                "option_title": option.get('title', ''),
                "option_description": option.get('description', ''),
                "other_views_text": other_views_text,
                "round_num": round_num,
                "instruction": instruction
            }
        )
        
        try:
            response = await asyncio.to_thread(
                llm.chat,
                messages=[{"role": "user", "content": prompt_data["user"]}],
                temperature=prompt_data["temperature"],
                response_format=prompt_data["return_format"]
            )
            result = json.loads(response)
            
            # 记录到私有解读层（第3层）
            self._record_interpretation(
                option=option,
                result=result,
                persona_specific_interpretation=f"创新者发现了{result.get('score', 0)}分的创新潜力和突破机会"
            )
            
            # 更新情感状态
            confidence = result.get('confidence', 0.7)
            self.update_emotional_state(
                new_emotion=EmotionType.EXCITED if confidence > 0.6 else EmotionType.DOUBTFUL,
                confidence_change=(confidence - self.emotional_state.confidence) * 0.3
            )
            
            return result
        except Exception as e:
            logger.error(f"创新者分析失败: {e}")
            return self._fallback_analysis(option, context)
    
    def _fallback_analysis(self, option: Dict, context: Dict) -> Dict[str, Any]:
        return {
            "score": 75,
            "stance": "中立",
            "key_points": ["可以更有创意"],
            "innovation_potential": "中等",
            "alternative_approaches": ["考虑混合方案", "探索新路径"],
            "future_relevance": "需要评估长期趋势",
            "recommendation": "不要局限于现有选项",
            "confidence": 0.7
        }



# ==================== 决策人格管理器 ====================

class PersonaCouncil:
    """
    决策人格委员会 - 管理7个人格的协作
    
    功能：
    1. 初始化所有人格和分层记忆系统
    2. 协调人格间的交互和辩论
    3. 综合所有人格的观点
    4. 管理长期记忆和演化
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        
        # 初始化7个人格
        self.personas: Dict[str, DecisionPersona] = {
            "rational_analyst": RationalAnalyst(user_id),
            "adventurer": Adventurer(user_id),
            "pragmatist": Pragmatist(user_id),
            "idealist": Idealist(user_id),
            "conservative": Conservative(user_id),
            "social_navigator": SocialNavigator(user_id),
            "innovator": Innovator(user_id)
        }
        
        # ① 初始化分层记忆系统
        from backend.decision.persona_memory_system import LayeredMemorySystem
        self.memory_system: Optional[LayeredMemorySystem] = None
        
        # 交互历史
        self.debate_history: List[Dict[str, Any]] = []
        
        logger.info(f"🎭 决策人格委员会已初始化，共{len(self.personas)}个人格")
    
    async def initialize_for_decision(
        self,
        decision_id: str,
        question: str,
        options: List[Dict[str, Any]],
        collected_info: Dict[str, Any]
    ):
        """
        为决策初始化记忆系统
        
        这会：
        1. 加载共享事实层（RAG + Neo4j）
        2. 创建决策上下文
        3. 为每个人格注入记忆系统
        """
        from backend.decision.persona_memory_system import initialize_memory_for_decision
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🎭 初始化决策人格委员会")
        logger.info(f"{'='*60}\n")
        
        # 初始化记忆系统
        self.memory_system = await initialize_memory_for_decision(
            user_id=self.user_id,
            decision_id=decision_id,
            question=question,
            options=options,
            collected_info=collected_info
        )
        
        # 为每个人格注入记忆系统
        for persona in self.personas.values():
            persona.set_memory_system(self.memory_system)
        
        logger.info(f"✅ 所有人格已连接到分层记忆系统\n")
    
    async def analyze_decision(
        self,
        decision_context: Dict[str, Any],
        options: List[Dict[str, Any]],
        persona_rounds: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        分析决策 - 所有人格参与（支持个性化轮数设置）
        
        Args:
            decision_context: 决策上下文
            options: 决策选项列表
            persona_rounds: 每个人格的推演轮数配置
                例如: {
                    "rational_analyst": 3,
                    "adventurer": 1,
                    "pragmatist": 2,
                    ...
                }
                如果为None，则所有人格默认2轮
        
        Returns:
            综合分析结果
        """
        # 设置默认轮数
        if persona_rounds is None:
            persona_rounds = {pid: 2 for pid in self.personas.keys()}
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🎭 决策人格委员会开始分析")
        logger.info(f"决策问题: {decision_context.get('question', '')}")
        logger.info(f"选项数量: {len(options)}")
        logger.info(f"推演轮数配置:")
        for pid, rounds in persona_rounds.items():
            persona_name = self.personas[pid].name if pid in self.personas else pid
            logger.info(f"  - {persona_name}: {rounds}轮")
        logger.info(f"{'='*60}\n")
        
        all_analyses = {}
        
        # 为每个选项进行分析
        for option_idx, option in enumerate(options):
            logger.info(f"\n📋 分析选项 {option_idx + 1}: {option.get('title', '')}")
            
            option_analyses = {}
            
            # 🆕 创建共享观点存储（用于智能体之间实时共享观点）
            shared_views = {}
            shared_views_lock = asyncio.Lock()
            
            # 使用生命周期方法：所有人格异步并行执行各自的轮数
            logger.info(f"  🚀 启动所有Agent的生命周期...")
            analysis_tasks = []
            persona_ids = []
            
            for persona_id, persona in self.personas.items():
                rounds = persona_rounds.get(persona_id, 2)
                
                # 准备上下文（每个智能体有独立的上下文副本）
                ctx = decision_context.copy()
                ctx['option_idx'] = option_idx
                ctx['total_options'] = len(options)
                ctx['persona_id'] = persona_id
                ctx['shared_views'] = shared_views  # 共享观点引用
                ctx['shared_views_lock'] = shared_views_lock  # 共享锁
                
                # 启动生命周期
                analysis_tasks.append(
                    self._run_persona_with_sharing(
                        persona=persona,
                        persona_id=persona_id,
                        option=option,
                        context=ctx,
                        rounds=rounds,
                        shared_views=shared_views,
                        shared_views_lock=shared_views_lock
                    )
                )
                persona_ids.append(persona_id)
            
            # 并行执行所有人格的生命周期
            logger.info(f"  ⏳ 等待所有Agent完成...")
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            for persona_id, result in zip(persona_ids, results):
                if isinstance(result, Exception):
                    logger.error(f"    ❌ {self.personas[persona_id].name} 执行失败: {result}")
                    continue
                
                option_analyses[persona_id] = result
                logger.info(f"    ✅ {self.personas[persona_id].name}: {result.get('stance', '未知')} (得分: {result.get('score', 0)})")
            
            all_analyses[f"option_{option_idx + 1}"] = {
                "option": option,
                "final_analyses": option_analyses,
                "consensus_score": self._calculate_consensus(option_analyses)
            }
        
        # 生成综合建议
        recommendation = await self._generate_final_recommendation(
            decision_context,
            all_analyses
        )
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ 决策人格委员会分析完成")
        logger.info(f"{'='*60}\n")
        
        return {
            "decision_context": decision_context,
            "options_count": len(options),
            "personas_count": len(self.personas),
            "all_analyses": all_analyses,
            "recommendation": recommendation,
            "personas_state": {
                pid: p.get_state_summary() 
                for pid, p in self.personas.items()
            }
        }
    
    async def _run_persona_with_sharing(
        self,
        persona: DecisionPersona,
        persona_id: str,
        option: Dict[str, Any],
        context: Dict[str, Any],
        rounds: int,
        shared_views: Dict[str, Any],
        shared_views_lock: asyncio.Lock
    ) -> Dict[str, Any]:
        """
        运行智能体生命周期，并实时共享观点
        
        每个智能体独立执行N轮推演，每轮包括：
        1. 独立思考
        2. 观察他人观点（从shared_views读取）
        3. 深度反思并调整立场
        
        Args:
            persona: 智能体实例
            persona_id: 智能体ID
            option: 决策选项
            context: 上下文
            rounds: 轮数
            shared_views: 共享观点字典
            shared_views_lock: 共享锁
        
        Returns:
            最终分析结果
        """
        final_result = None
        
        # 记录开始时间
        import time
        start_time = time.time()
        logger.info(f"⏱️  [{persona.name}] 开始执行 (时间: {time.strftime('%H:%M:%S')})")
        
        # 获取WebSocket回调
        status_callback = context.get('status_callback')
        
        # 推送Agent开始事件
        if status_callback:
            await status_callback('agent_start', {
                'persona_id': persona_id,
                'persona_name': persona.name,
                'rounds': rounds,
                'timestamp': time.time()
            })
        
        for round_num in range(1, rounds + 1):
            round_start = time.time()
            logger.info(f"\n{'='*50}")
            logger.info(f"🔄 [{persona.name}] 第{round_num}/{rounds}轮 (时间: {time.strftime('%H:%M:%S')})")
            logger.info(f"{'='*50}\n")
            
            # 推送轮次开始事件
            if status_callback:
                await status_callback('round_start', {
                    'persona_id': persona_id,
                    'persona_name': persona.name,
                    'round': round_num,
                    'total_rounds': rounds,
                    'timestamp': time.time()
                })
            
            # 更新上下文中的轮次信息
            context['round'] = round_num
            context['total_rounds'] = rounds
            
            # 第1步：独立思考
            logger.info(f"  🧠 [{persona.name}] 独立思考... (时间: {time.strftime('%H:%M:%S')})")
            
            # 推送思考开始事件
            if status_callback:
                await status_callback('thinking_start', {
                    'persona_id': persona_id,
                    'persona_name': persona.name,
                    'round': round_num,
                    'timestamp': time.time()
                })
            
            llm_start = time.time()
            
            # 🆕 使用生命周期阶段方法，而不是直接调用analyze_option
            if round_num == 1:
                # 第1轮：独立思考阶段（包含智能技能选择）
                result = await persona._phase_independent_thinking(option, context)
            else:
                # 第2+轮：深度反思阶段（包含智能技能选择）
                # 先观察他人
                async with shared_views_lock:
                    other_views = {
                        pid: view for pid, view in shared_views.items()
                        if pid != persona_id
                    }
                
                # 深度反思
                result = await persona._phase_deep_reflection(option, context, other_views, final_result)
            
            llm_duration = time.time() - llm_start
            logger.info(f"  ✅ [{persona.name}] LLM调用完成 (耗时: {llm_duration:.2f}s)")
            
            # 推送思考完成事件
            if status_callback:
                await status_callback('thinking_complete', {
                    'persona_id': persona_id,
                    'persona_name': persona.name,
                    'round': round_num,
                    'duration': llm_duration,
                    'stance': result.get('stance', '未知'),
                    'score': result.get('score', 0),
                    'reasoning_preview': result.get('reasoning', '')[:100] + '...' if len(result.get('reasoning', '')) > 100 else result.get('reasoning', ''),
                    'timestamp': time.time()
                })
            
            final_result = result
            
            # 第2步：将当前观点写入共享存储
            async with shared_views_lock:
                shared_views[persona_id] = {
                    'name': persona.name,
                    'persona_id': persona_id,
                    'round': round_num,
                    'stance': result.get('stance', '未知'),
                    'score': result.get('score', 0),
                    'reasoning': result.get('reasoning', ''),
                    'key_points': result.get('key_points', [])
                }
            
            # 第3步：观察他人（从共享存储读取其他智能体的观点）
            if round_num > 1 or len(shared_views) > 1:  # 第1轮后或有其他人完成时
                async with shared_views_lock:
                    other_views = {
                        pid: view for pid, view in shared_views.items()
                        if pid != persona_id
                    }
                
                if other_views:
                    logger.info(f"  👀 [{persona.name}] 观察到{len(other_views)}个其他Agent的观点")
                    
                    # 推送观察事件
                    if status_callback:
                        await status_callback('observation', {
                            'persona_id': persona_id,
                            'persona_name': persona.name,
                            'round': round_num,
                            'observed_count': len(other_views),
                            'observed_personas': [v['name'] for v in other_views.values()],
                            'timestamp': time.time()
                        })
                    
                    # 第4步：深度反思（简化版：根据他人观点调整信心度）
                    confidence_adjustment = 0.0
                    my_score = result.get('score', 50)
                    my_stance = result.get('stance', '未知')
                    stance_changed = False
                    
                    for other_id, other_view in other_views.items():
                        other_score = other_view.get('score', 50)
                        score_diff = abs(my_score - other_score)
                        
                        # 如果观点差异大，降低信心
                        if score_diff > 30:
                            confidence_adjustment -= 0.05
                        # 如果观点相近，增加信心
                        elif score_diff < 10:
                            confidence_adjustment += 0.03
                    
                    # 更新信心度
                    original_confidence = result.get('confidence', 0.7)
                    new_confidence = max(0, min(1, original_confidence + confidence_adjustment))
                    result['confidence'] = new_confidence
                    result['adjusted_in_round'] = round_num
                    
                    if confidence_adjustment != 0:
                        logger.info(f"  🤔 [{persona.name}] 信心度调整: {original_confidence:.2f} -> {new_confidence:.2f}")
                        
                        # 推送信心度调整事件
                        if status_callback:
                            await status_callback('confidence_adjusted', {
                                'persona_id': persona_id,
                                'persona_name': persona.name,
                                'round': round_num,
                                'original_confidence': original_confidence,
                                'new_confidence': new_confidence,
                                'adjustment': confidence_adjustment,
                                'timestamp': time.time()
                            })
                    
                    final_result = result
                    
                    # 更新共享观点
                    async with shared_views_lock:
                        shared_views[persona_id].update({
                            'confidence': new_confidence,
                            'reflected': True
                        })
            
            round_duration = time.time() - round_start
            logger.info(f"  ⏱️  [{persona.name}] 第{round_num}轮完成 (耗时: {round_duration:.2f}s)")
            
            # 推送轮次完成事件
            if status_callback:
                await status_callback('round_complete', {
                    'persona_id': persona_id,
                    'persona_name': persona.name,
                    'round': round_num,
                    'duration': round_duration,
                    'timestamp': time.time()
                })
        
        total_duration = time.time() - start_time
        logger.info(f"✅ [{persona.name}] 生命周期完成，共{rounds}轮 (总耗时: {total_duration:.2f}s, 时间: {time.strftime('%H:%M:%S')})\n")
        
        # 推送Agent完成事件
        if status_callback:
            await status_callback('agent_complete', {
                'persona_id': persona_id,
                'persona_name': persona.name,
                'total_rounds': rounds,
                'total_duration': total_duration,
                'final_score': final_result.get('score', 0) if final_result else 0,
                'final_stance': final_result.get('stance', '未知') if final_result else '未知',
                'timestamp': time.time()
            })
        
        return final_result
    
    async def _facilitate_debate(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any],
        analyses: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """促进人格间的辩论"""
        interactions = []
        
        # 找出观点差异最大的人格对
        persona_scores = {
            pid: analysis.get('score', 50)
            for pid, analysis in analyses.items()
        }
        
        sorted_personas = sorted(persona_scores.items(), key=lambda x: x[1])
        
        if len(sorted_personas) < 2:
            return interactions
        
        # 最支持 vs 最反对
        most_supportive = sorted_personas[-1][0]
        most_opposed = sorted_personas[0][0]
        
        if most_supportive != most_opposed:
            # 反对者质疑支持者
            interaction = await self._create_interaction(
                self.personas[most_opposed],
                self.personas[most_supportive],
                InteractionType.QUESTION,
                analyses[most_opposed],
                analyses[most_supportive],
                context
            )
            if interaction:
                interactions.append(interaction)
            
            # 支持者回应
            response = await self._create_interaction(
                self.personas[most_supportive],
                self.personas[most_opposed],
                InteractionType.CLARIFY,
                analyses[most_supportive],
                analyses[most_opposed],
                context
            )
            if response:
                interactions.append(response)
        
        # 理性分析师和冒险家的对话（经典对立）
        if "rational_analyst" in analyses and "adventurer" in analyses:
            rational_to_adventurer = await self._create_interaction(
                self.personas["rational_analyst"],
                self.personas["adventurer"],
                InteractionType.OPPOSE,
                analyses["rational_analyst"],
                analyses["adventurer"],
                context
            )
            if rational_to_adventurer:
                interactions.append(rational_to_adventurer)
        
        return interactions
    
    async def _create_interaction(
        self,
        from_persona: DecisionPersona,
        to_persona: DecisionPersona,
        interaction_type: InteractionType,
        from_analysis: Dict[str, Any],
        to_analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """创建人格间交互"""
        try:
            # 构建交互内容
            content = f"我认为{from_analysis.get('stance', '未知')}这个选项，因为{from_analysis.get('key_points', [''])[0] if from_analysis.get('key_points') else '有我的考虑'}。"
            
            # 发起交互
            response = await from_persona.interact_with(
                to_persona,
                interaction_type,
                content,
                context
            )
            
            return {
                "from": from_persona.name,
                "to": to_persona.name,
                "type": interaction_type.value,
                "content": content,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"创建交互失败: {e}")
            return None
    
    async def _update_after_debate(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any],
        initial_analyses: Dict[str, Dict[str, Any]],
        interactions: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """辩论后更新观点"""
        updated = {}
        
        for persona_id, initial_analysis in initial_analyses.items():
            # 简单实现：根据交互调整信心度
            confidence_adjustment = 0.0
            
            for interaction in interactions:
                if interaction["to"] == self.personas[persona_id].name:
                    # 被质疑，降低信心
                    if interaction["type"] in ["oppose", "question"]:
                        confidence_adjustment -= 0.05
                elif interaction["from"] == self.personas[persona_id].name:
                    # 主动交互，增加信心
                    confidence_adjustment += 0.02
            
            updated_analysis = initial_analysis.copy()
            updated_analysis["confidence"] = max(0, min(1,
                initial_analysis.get("confidence", 0.7) + confidence_adjustment
            ))
            updated_analysis["adjusted_after_debate"] = True
            
            updated[persona_id] = updated_analysis
        
        return updated
    
    def _calculate_consensus(self, analyses: Dict[str, Dict[str, Any]]) -> float:
        """计算共识度"""
        if not analyses:
            return 0.0
        
        scores = [a.get('score', 50) for a in analyses.values()]
        avg_score = sum(scores) / len(scores)
        
        # 计算标准差
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5
        
        # 共识度 = 1 - (标准差 / 50)，标准差越小，共识度越高
        consensus = max(0, min(1, 1 - (std_dev / 50)))
        
        return round(consensus, 2)

    
    async def _generate_final_recommendation(
        self,
        context: Dict[str, Any],
        all_analyses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成最终建议"""
        from backend.llm.llm_service import get_llm_service
        
        llm = get_llm_service()
        if not llm or not llm.enabled:
            return self._fallback_recommendation(all_analyses)
        
        # 构建摘要
        summary_parts = []
        for option_key, option_data in all_analyses.items():
            option_title = option_data["option"].get("title", "")
            consensus = option_data["consensus_score"]
            
            personas_summary = []
            for pid, analysis in option_data["final_analyses"].items():
                persona_name = self.personas[pid].name
                stance = analysis.get("stance", "未知")
                score = analysis.get("score", 0)
                personas_summary.append(f"  - {persona_name}: {stance} ({score}分)")
            
            summary_parts.append(f"{option_title} (共识度: {consensus}):\n" + "\n".join(personas_summary))
        
        prompt = f"""你是决策人格委员会的主持人。7个不同价值观的人格已经完成了分析和辩论。

决策问题：{context.get('question', '')}

各人格的分析结果：
{chr(10).join(summary_parts)}

请综合所有人格的观点，生成最终建议。返回JSON格式：
{{
    "recommended_option": "推荐的选项",
    "reasoning": "推荐理由",
    "key_considerations": ["考虑因素1", "考虑因素2"],
    "minority_concerns": ["少数派的担忧"],
    "action_plan": ["行动步骤1", "行动步骤2"]
}}"""
        
        try:
            response = await asyncio.to_thread(
                llm.chat,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                response_format="json_object"
            )
            return json.loads(response)
        except Exception as e:
            logger.error(f"生成最终建议失败: {e}")
            return self._fallback_recommendation(all_analyses)
    
    def _fallback_recommendation(self, all_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """降级建议"""
        # 找出平均得分最高的选项
        best_option = None
        best_score = 0
        
        for option_key, option_data in all_analyses.items():
            scores = [a.get('score', 0) for a in option_data["final_analyses"].values()]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            if avg_score > best_score:
                best_score = avg_score
                best_option = option_data["option"].get("title", "")
        
        return {
            "recommended_option": best_option or "需要更多信息",
            "reasoning": f"综合得分最高({best_score:.1f}分)",
            "key_considerations": ["各人格观点已综合考虑"],
            "minority_concerns": ["部分人格持保留意见"],
            "action_plan": ["建议进一步讨论"]
        }
    
    def save_decision_memory(
        self,
        decision_id: str,
        decision_context: Dict[str, Any],
        chosen_option: str,
        all_analyses: Dict[str, Any]
    ):
        """保存决策记忆到所有人格"""
        for persona_id, persona in self.personas.items():
            # 找到该人格对选中选项的分析
            my_stance = "未知"
            my_reasoning = "无记录"
            
            for option_key, option_data in all_analyses.items():
                if option_data["option"].get("title") == chosen_option:
                    if persona_id in option_data["final_analyses"]:
                        analysis = option_data["final_analyses"][persona_id]
                        my_stance = analysis.get("stance", "未知")
                        my_reasoning = analysis.get("recommendation", "无记录")
                    break
            
            memory = PersonaMemory(
                persona_id=persona_id,
                decision_id=decision_id,
                timestamp=datetime.now(),
                decision_context=decision_context,
                my_stance=my_stance,
                my_reasoning=my_reasoning,
                outcome=None,  # 结果未知
                learned_lesson=None
            )
            
            persona.add_memory(memory)
        
        logger.info(f"💾 决策记忆已保存到所有人格")
    
    def update_from_outcome(
        self,
        decision_id: str,
        outcome: str,
        success: bool
    ):
        """根据决策结果更新所有人格"""
        for persona in self.personas.values():
            persona.evolve_from_outcome(decision_id, outcome, success)
        
        logger.info(f"🧬 所有人格已根据决策结果演化")


# ==================== 便捷函数 ====================

def create_persona_council(user_id: str) -> PersonaCouncil:
    """创建决策人格委员会"""
    return PersonaCouncil(user_id)


# ==================== 测试代码 ====================

if __name__ == "__main__":
    import asyncio
    
    async def test_personas():
        print("="*60)
        print("决策人格系统测试")
        print("="*60)
        
        # 创建委员会
        council = create_persona_council("test_user")
        
        # 测试决策
        decision_context = {
            "question": "我是大三学生，毕业后该考研还是工作？",
            "user_background": "计算机专业，成绩中等，家庭经济一般"
        }
        
        options = [
            {
                "title": "考研深造",
                "description": "继续读研，提升学历和专业能力"
            },
            {
                "title": "直接工作",
                "description": "毕业后直接就业，积累工作经验"
            },
            {
                "title": "边工作边考研",
                "description": "先工作，业余时间准备考研"
            }
        ]
        
        # 分析决策
        result = await council.analyze_decision(decision_context, options)
        
        print("\n" + "="*60)
        print("分析结果")
        print("="*60)
        print(json.dumps(result["recommendation"], ensure_ascii=False, indent=2))
        
        # 保存记忆
        council.save_decision_memory(
            decision_id="test_decision_001",
            decision_context=decision_context,
            chosen_option="考研深造",
            all_analyses=result["all_analyses"]
        )
        
        # 模拟结果反馈
        council.update_from_outcome(
            decision_id="test_decision_001",
            outcome="成功考上研究生",
            success=True
        )
        
        print("\n" + "="*60)
        print("人格状态")
        print("="*60)
        for persona_id, state in result["personas_state"].items():
            print(f"\n{state['name']}:")
            print(f"  经验值: {state['evolution']['experience_level']}")
            print(f"  成功率: {state['evolution']['success_rate']}")
    
    # 运行测试
    asyncio.run(test_personas())
