# -*- coding: utf-8 -*-
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
# 最多允许3个智能体同时进行检索（每个检索需要1次LLM调用）
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
        skills: Optional[List[str]] = None,
        custom_prompt_suffix: Optional[str] = None
    ):
        self.persona_id = persona_id
        self.name = name
        self.description = description
        self.value_system = value_system
        self.user_id = user_id
        
        # 技能系统
        self.skill_names = skills or []
        self.custom_prompt_suffix = custom_prompt_suffix or ""
        
        # 初始化技能执行器（延迟初始化，避免循环依赖）
        self._skill_executor = None
        
        # 情感状态模块
        self.emotional_state = EmotionalState(
            primary_emotion=EmotionType.CONFIDENT,
            intensity=0.5,
            confidence=0.7,
            fatigue=0.0,
            stress_level=0.3
        )
        
        # 长期记忆（私有层）
        self.memories: List[PersonaMemory] = []
        self.interaction_history: List[PersonaInteraction] = []
        
        # 当前决策的私有解读（运行时）
        self.current_interpretation: Optional[Any] = None
        
        # 演化参数
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
        """使用技能"""
        return await self.skill_executor.execute_skill(skill_name, context)
    
    async def execute_all_skills(self, context: Dict[str, Any], status_callback=None) -> Dict[str, Any]:
        """执行所有技能（除了混合检索）并收集结果"""
        skill_results = {}
        
        for skill_name in self.skill_names:
            # 跳过混合检索（单独处理）
            if skill_name == "混合检索":
                continue
            
            try:
                # 发送状态更新：开始执行
                if status_callback:
                    await status_callback(f"【{self.name}】正在执行技能：{skill_name}")
                
                result = await self.use_skill(skill_name, context)
                
                if result.get("success"):
                    skill_results[skill_name] = result
                    logger.info(f"[{self.name}] 技能执行成功: {skill_name}")
                    
                    # 提取技能结果摘要
                    result_summary = self._extract_skill_result_summary(skill_name, result)
                    
                    # 发送详细的成功状态（包含结果摘要）
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
                    logger.warning(f"[{self.name}] 技能执行失败: {skill_name} - {result.get('error', '未知错误')}")
                    
                    # 发送失败状态
                    if status_callback:
                        await status_callback(f"【{self.name}】❌ {skill_name}失败")
            except Exception as e:
                logger.error(f"[{self.name}] 技能执行异常: {skill_name} - {e}")
                if status_callback:
                    await status_callback(f"【{self.name}】❌ {skill_name}异常")
        
        return skill_results
    
    def _extract_skill_result_summary(self, skill_name: str, result: Dict[str, Any]) -> str:
        """提取技能执行结果的摘要"""
        summary_parts = []
        
        # 根据不同技能类型提取关键信息
        if skill_name == "数据分析":
            if "insights" in result:
                insights = result["insights"]
                if isinstance(insights, list) and insights:
                    summary_parts.append(f"洞察: {len(insights)}条")
                    summary_parts.append(f"首要洞察: {insights[0][:40]}...")
            if "data_quality" in result:
                summary_parts.append(f"数据质量: {result['data_quality']}")
        
        elif skill_name == "风险评估":
            if "risk_level" in result:
                summary_parts.append(f"风险等级: {result['risk_level']}")
            if "risk_factors" in result:
                factors = result["risk_factors"]
                if isinstance(factors, list) and factors:
                    summary_parts.append(f"风险因素: {len(factors)}个")
        
        elif skill_name == "机会识别":
            if "opportunities" in result:
                opps = result["opportunities"]
                if isinstance(opps, list) and opps:
                    summary_parts.append(f"发现机会: {len(opps)}个")
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
                    summary_parts.append(f"障碍: {len(barriers)}个")
        
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
        """格式化技能执行结果为文本"""
        if not skill_results:
            return ""
        
        lines = ["\n【技能分析结果】"]
        
        for skill_name, result in skill_results.items():
            lines.append(f"\n◆ {skill_name}:")
            
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
    
    def set_memory_system(self, memory_system: Any):
        """设置记忆系统（注入依赖）"""
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
        """访问共享事实层"""
        if hasattr(self, 'memory_system') and self.memory_system.shared_facts:
            return {
                "summary": self.memory_system.shared_facts.get_summary(),
                "relationships": self.memory_system.shared_facts.relationships,
                "education": self.memory_system.shared_facts.education_history,
                "career": self.memory_system.shared_facts.career_history,
                "skills": self.memory_system.shared_facts.skills,
                "past_decisions": self.memory_system.current_decision.past_decisions if self.memory_system.current_decision else []
            }
        return None
    
    async def analyze_option(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any],
        other_personas_views: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        分析一个决策选项
        
        Args:
            option: 选项信息
            context: 决策上下文
            other_personas_views: 其他人格的观点
        
        Returns:
            分析结果
        """
        from backend.llm.llm_service import LLMService
        
        llm = LLMService()
        
        # 构建提示词
        prompt = self._build_analysis_prompt(option, context, other_personas_views)
        
        # 调用LLM
        response = await llm.generate_async(prompt)
        
        # 解析响应
        result = self._parse_analysis_response(response)
        
        # 记录到私有解读层
        self._record_interpretation(option, result)
        
        return result
    
    def _build_analysis_prompt(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any],
        other_personas_views: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """构建分析提示词"""
        prompt_parts = [
            f"你是 {self.name}，{self.description}",
            f"\n你的价值观：{self.value_system.name}",
            f"风险承受度：{self.value_system.risk_tolerance:.0%}",
            f"决策风格：{self.value_system.decision_style}",
            f"\n当前情绪：{self.emotional_state.primary_emotion.value}",
            f"信心水平：{self.emotional_state.confidence:.0%}",
            f"\n请分析以下选项：",
            f"选项：{option.get('title', '未命名选项')}",
            f"描述：{option.get('description', '无描述')}",
        ]
        
        # 添加共享事实
        shared_facts = self.get_shared_facts()
        if shared_facts:
            prompt_parts.append(f"\n用户背景信息：")
            prompt_parts.append(f"- 教育经历：{len(shared_facts.get('education', []))}条")
            prompt_parts.append(f"- 职业经历：{len(shared_facts.get('career', []))}条")
            prompt_parts.append(f"- 技能：{len(shared_facts.get('skills', []))}项")
        
        # 添加其他人格的观点
        if other_personas_views:
            prompt_parts.append(f"\n其他智能体的观点：")
            for view in other_personas_views[:3]:  # 最多显示3个
                prompt_parts.append(f"- {view.get('persona_name', '未知')}: {view.get('stance', '未知立场')}")
        
        prompt_parts.append(f"\n请给出你的分析，包括：")
        prompt_parts.append(f"1. 立场（支持/反对/中立）")
        prompt_parts.append(f"2. 评分（0-100）")
        prompt_parts.append(f"3. 关键论点（3-5条）")
        prompt_parts.append(f"4. 推理过程")
        
        if self.custom_prompt_suffix:
            prompt_parts.append(f"\n{self.custom_prompt_suffix}")
        
        return "\n".join(prompt_parts)
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        # 简单的解析逻辑，实际应该更复杂
        result = {
            "stance": "中立",
            "score": 50,
            "key_points": [],
            "reasoning": response,
            "confidence": self.emotional_state.confidence
        }
        
        # 尝试从响应中提取结构化信息
        if "支持" in response:
            result["stance"] = "支持"
            result["score"] = 70
        elif "反对" in response:
            result["stance"] = "反对"
            result["score"] = 30
        
        return result
    
    def _record_interpretation(
        self,
        option: Dict[str, Any],
        result: Dict[str, Any],
        persona_specific_interpretation: str = ""
    ):
        """记录到私有解读层"""
        if not self.current_interpretation:
            return
        
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
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "persona_id": self.persona_id,
            "name": self.name,
            "description": self.description,
            "value_system": {
                "name": self.value_system.name,
                "risk_tolerance": self.value_system.risk_tolerance,
                "decision_style": self.value_system.decision_style
            },
            "emotional_state": self.emotional_state.to_dict(),
            "skills": self.skill_names,
            "experience_level": self.experience_level,
            "success_count": self.success_count,
            "failure_count": self.failure_count
        }



# ==================== 人格委员会 ====================

class PersonaCouncil:
    """
    决策人格委员会
    
    管理7个决策人格，协调它们的交互和决策过程
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.personas: Dict[str, DecisionPersona] = {}
        self.memory_system = None
        
        # 创建7个决策人格
        self._create_personas()
        
        logger.info(f"✨ 创建人格委员会，共 {len(self.personas)} 个智能体")
    
    def _create_personas(self):
        """创建7个决策人格"""
        
        # 1. 理性分析师
        self.personas["rational_analyst"] = DecisionPersona(
            persona_id="rational_analyst",
            name="理性分析师",
            description="擅长逻辑推理和数据分析，追求客观理性的决策",
            value_system=ValueSystem(
                name="理性主义",
                priorities={"逻辑性": 0.9, "数据支持": 0.8, "可行性": 0.7},
                risk_tolerance=0.4,
                time_horizon="medium",
                decision_style="analytical"
            ),
            user_id=self.user_id,
            skills=["数据分析", "风险评估", "可行性评估"]
        )
        
        # 2. 冒险家
        self.personas["adventurer"] = DecisionPersona(
            persona_id="adventurer",
            name="冒险家",
            description="勇于尝试新事物，追求突破和创新",
            value_system=ValueSystem(
                name="冒险主义",
                priorities={"创新性": 0.9, "成长潜力": 0.8, "挑战性": 0.7},
                risk_tolerance=0.8,
                time_horizon="long",
                decision_style="intuitive"
            ),
            user_id=self.user_id,
            skills=["机会识别", "创新潜力评估"]
        )
        
        # 3. 保守派
        self.personas["conservative"] = DecisionPersona(
            persona_id="conservative",
            name="保守派",
            description="注重稳定和安全，避免不必要的风险",
            value_system=ValueSystem(
                name="保守主义",
                priorities={"安全性": 0.9, "稳定性": 0.8, "可靠性": 0.7},
                risk_tolerance=0.2,
                time_horizon="short",
                decision_style="analytical"
            ),
            user_id=self.user_id,
            skills=["风险评估", "可行性评估"]
        )
        
        # 4. 实用主义者
        self.personas["pragmatist"] = DecisionPersona(
            persona_id="pragmatist",
            name="实用主义者",
            description="关注实际效果和可操作性，追求务实的解决方案",
            value_system=ValueSystem(
                name="实用主义",
                priorities={"实用性": 0.9, "效率": 0.8, "成本效益": 0.7},
                risk_tolerance=0.5,
                time_horizon="short",
                decision_style="balanced"
            ),
            user_id=self.user_id,
            skills=["可行性评估", "数据分析"]
        )
        
        # 5. 理想主义者
        self.personas["idealist"] = DecisionPersona(
            persona_id="idealist",
            name="理想主义者",
            description="追求价值观的实现和长远意义",
            value_system=ValueSystem(
                name="理想主义",
                priorities={"价值观契合": 0.9, "长远意义": 0.8, "社会影响": 0.7},
                risk_tolerance=0.6,
                time_horizon="long",
                decision_style="intuitive"
            ),
            user_id=self.user_id,
            skills=["价值观对齐分析", "机会识别"]
        )
        
        # 6. 社交导航者
        self.personas["social_navigator"] = DecisionPersona(
            persona_id="social_navigator",
            name="社交导航者",
            description="关注人际关系和社会网络的影响",
            value_system=ValueSystem(
                name="社交主义",
                priorities={"人际关系": 0.9, "社会认同": 0.8, "合作机会": 0.7},
                risk_tolerance=0.5,
                time_horizon="medium",
                decision_style="balanced"
            ),
            user_id=self.user_id,
            skills=["人际关系影响分析", "机会识别"]
        )
        
        # 7. 创新者
        self.personas["innovator"] = DecisionPersona(
            persona_id="innovator",
            name="创新者",
            description="追求创造性和突破性的解决方案",
            value_system=ValueSystem(
                name="创新主义",
                priorities={"创新性": 0.9, "独特性": 0.8, "突破性": 0.7},
                risk_tolerance=0.7,
                time_horizon="long",
                decision_style="intuitive"
            ),
            user_id=self.user_id,
            skills=["创新潜力评估", "机会识别"]
        )
    
    def set_memory_system(self, memory_system: Any):
        """为所有人格设置记忆系统"""
        self.memory_system = memory_system
        for persona in self.personas.values():
            persona.set_memory_system(memory_system)
    
    async def analyze_options(
        self,
        options: List[Dict[str, Any]],
        context: Dict[str, Any],
        status_callback=None
    ) -> Dict[str, Any]:
        """
        让所有人格分析选项
        
        Args:
            options: 选项列表
            context: 决策上下文
            status_callback: 状态回调函数
        
        Returns:
            所有人格的分析结果
        """
        results = {}
        
        for persona_id, persona in self.personas.items():
            if status_callback:
                await status_callback(f"【{persona.name}】开始分析...")
            
            persona_results = []
            for option in options:
                result = await persona.analyze_option(option, context)
                persona_results.append(result)
            
            results[persona_id] = {
                "persona_name": persona.name,
                "results": persona_results
            }
            
            if status_callback:
                await status_callback(f"【{persona.name}】分析完成")
        
        return results
    
    def get_persona(self, persona_id: str) -> Optional[DecisionPersona]:
        """获取指定人格"""
        return self.personas.get(persona_id)
    
    def list_personas(self) -> List[Dict[str, Any]]:
        """列出所有人格"""
        return [persona.to_dict() for persona in self.personas.values()]


# ==================== 工厂函数 ====================

def create_persona_council(user_id: str) -> PersonaCouncil:
    """
    创建人格委员会
    
    Args:
        user_id: 用户ID
    
    Returns:
        PersonaCouncil实例
    """
    return PersonaCouncil(user_id)


# ==================== 预定义人格配置 ====================

PERSONA_CONFIGS = {
    "rational_analyst": {
        "name": "理性分析师",
        "description": "擅长逻辑推理和数据分析",
        "skills": ["数据分析", "风险评估", "可行性评估"]
    },
    "adventurer": {
        "name": "冒险家",
        "description": "勇于尝试新事物",
        "skills": ["机会识别", "创新潜力评估"]
    },
    "conservative": {
        "name": "保守派",
        "description": "注重稳定和安全",
        "skills": ["风险评估", "可行性评估"]
    },
    "pragmatist": {
        "name": "实用主义者",
        "description": "关注实际效果",
        "skills": ["可行性评估", "数据分析"]
    },
    "idealist": {
        "name": "理想主义者",
        "description": "追求价值观的实现",
        "skills": ["价值观对齐分析", "机会识别"]
    },
    "social_navigator": {
        "name": "社交导航者",
        "description": "关注人际关系",
        "skills": ["人际关系影响分析", "机会识别"]
    },
    "innovator": {
        "name": "创新者",
        "description": "追求创造性解决方案",
        "skills": ["创新潜力评估", "机会识别"]
    }
}
