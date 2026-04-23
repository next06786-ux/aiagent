"""
决策人格技能系统

每个智能体拥有一组可执行的技能，包括：
- 数据检索技能
- 分析技能
- 推理技能
等

作者: AI System
版本: 1.0
日期: 2026-04-19
"""
import logging
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class Skill(ABC):
    """技能基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Any:
        """执行技能"""
        pass


class HybridRetrievalSkill(Skill):
    """混合检索技能 - 从知识图谱和RAG检索数据"""
    
    def __init__(self, persona):
        super().__init__(
            name="混合检索",
            description="从知识图谱和向量数据库检索相关信息"
        )
        self.persona = persona
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行混合检索
        
        Args:
            context: {
                "query": "检索查询",
                "max_results": 10,
                "domains": ["education", "career", "relationship"]
            }
        
        Returns:
            {
                "success": bool,
                "results": List[Dict],
                "count": int
            }
        """
        query = context.get("query", "")
        max_results = context.get("max_results", 10)
        
        if not query:
            return {"success": False, "results": [], "count": 0, "error": "查询为空"}
        
        try:
            logger.info(f"[{self.persona.name}] 执行混合检索技能: {query}")
            results = await self.persona.supplement_shared_facts(query, max_results)
            
            return {
                "success": True,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            logger.error(f"[{self.persona.name}] 混合检索技能执行失败: {e}")
            return {
                "success": False,
                "results": [],
                "count": 0,
                "error": str(e)
            }


class DataAnalysisSkill(Skill):
    """数据分析技能 - 分析结构化数据"""
    
    def __init__(self, persona):
        super().__init__(
            name="数据分析",
            description="分析和解读结构化数据，提取关键指标"
        )
        self.persona = persona
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行数据分析
        
        Args:
            context: {
                "option": 选项信息,
                "collected_info": 收集的用户信息,
                "shared_facts": 共享事实数据
            }
        
        Returns:
            {
                "success": bool,
                "insights": List[str],   # 数据洞察
                "key_metrics": Dict,     # 关键指标
                "data_quality": str,     # 数据质量评估
                "thinking_process": str  # 思考过程
            }
        """
        from backend.llm.llm_service import get_llm_service
        
        option = context.get("option", {})
        collected_info = context.get("collected_info", {})
        shared_facts = context.get("shared_facts", None)
        
        logger.info(f"[{self.persona.name}] 执行数据分析技能")
        
        llm = get_llm_service()
        if not llm or not llm.enabled:
            return {
                "success": False,
                "error": "LLM不可用",
                "thinking_process": "LLM不可用，无法执行分析"
            }
        
        # 使用LLM分析数据
        import asyncio
        import json
        
        # 构建简化的数据摘要（不直接序列化SharedFactsLayer）
        data_summary = "用户数据摘要："
        if shared_facts and hasattr(shared_facts, 'relationships'):
            data_summary += f"\n- 人际关系: {len(shared_facts.relationships) if shared_facts.relationships else 0}个"
        if shared_facts and hasattr(shared_facts, 'education_history'):
            data_summary += f"\n- 教育背景: {len(shared_facts.education_history) if shared_facts.education_history else 0}条"
        if shared_facts and hasattr(shared_facts, 'career_history'):
            data_summary += f"\n- 职业经历: {len(shared_facts.career_history) if shared_facts.career_history else 0}条"
        
        prompt = f"""你是一个数据分析专家，请分析以下信息：

选项：{option.get('title', '')} - {option.get('description', '')}

用户背景：
{json.dumps(collected_info, ensure_ascii=False, indent=2)[:500]}

{data_summary}

请提供：
1. 3-5个关键数据洞察
2. 数据质量评估（高/中/低）
3. 关键指标识别
4. 你的思考过程（如何分析这些数据的）

返回JSON格式：
{{
    "insights": ["洞察1", "洞察2", "洞察3"],
    "data_quality": "高/中/低",
    "key_metrics": {{"指标名": "指标值"}},
    "thinking_process": "我的思考过程是..."
}}"""
        
        try:
            response = await asyncio.to_thread(
                llm.chat,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format="json_object"
            )
            result = json.loads(response)
            
            return {
                "success": True,
                "insights": result.get("insights", []),
                "key_metrics": result.get("key_metrics", {}),
                "data_quality": result.get("data_quality", "中"),
                "thinking_process": result.get("thinking_process", "未提供思考过程")
            }
        except Exception as e:
            logger.error(f"[{self.persona.name}] 数据分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "thinking_process": f"执行失败: {str(e)}"
            }


class RiskAssessmentSkill(Skill):
    """风险评估技能"""
    
    def __init__(self, persona):
        super().__init__(
            name="风险评估",
            description="识别和评估潜在风险"
        )
        self.persona = persona
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行风险评估
        
        Args:
            context: {
                "option": 选项信息,
                "collected_info": 收集的用户信息
            }
        
        Returns:
            {
                "success": bool,
                "risk_level": str,         # 风险等级
                "risk_factors": List[str], # 风险因素
                "mitigation": List[str],   # 缓解措施
                "thinking_process": str    # 思考过程
            }
        """
        from backend.llm.llm_service import get_llm_service
        
        option = context.get("option", {})
        collected_info = context.get("collected_info", {})
        
        logger.info(f"[{self.persona.name}] 执行风险评估技能")
        
        llm = get_llm_service()
        if not llm or not llm.enabled:
            # 基于persona的风险容忍度给出基础评估
            risk_tolerance = self.persona.value_system.risk_tolerance
            return {
                "success": True,
                "risk_level": "低" if risk_tolerance > 0.7 else "高" if risk_tolerance < 0.3 else "中",
                "risk_factors": ["需要LLM进行详细分析"],
                "mitigation": ["建议启用LLM获取详细建议"],
                "risk_tolerance": risk_tolerance,
                "thinking_process": f"基于风险容忍度{risk_tolerance}进行基础评估"
            }
        
        import asyncio
        import json
        
        prompt = f"""你是一个风险评估专家，请评估以下选项的风险：

选项：{option.get('title', '')} - {option.get('description', '')}

用户背景：
{json.dumps(collected_info, ensure_ascii=False, indent=2)[:500]}

评估者风险容忍度：{self.persona.value_system.risk_tolerance}

请提供：
1. 风险等级（低/中/高）
2. 3-5个主要风险因素
3. 3-5个风险缓解措施
4. 你的思考过程（如何评估这些风险的）

返回JSON格式：
{{
    "risk_level": "低/中/高",
    "risk_factors": ["风险1", "风险2"],
    "mitigation": ["措施1", "措施2"],
    "thinking_process": "我的思考过程是..."
}}"""
        
        try:
            response = await asyncio.to_thread(
                llm.chat,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format="json_object"
            )
            result = json.loads(response)
            
            return {
                "success": True,
                "risk_level": result.get("risk_level", "中"),
                "risk_factors": result.get("risk_factors", []),
                "mitigation": result.get("mitigation", []),
                "thinking_process": result.get("thinking_process", "未提供思考过程")
            }
        except Exception as e:
            logger.error(f"[{self.persona.name}] 风险评估失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "thinking_process": f"执行失败: {str(e)}"
            }


class OpportunityIdentificationSkill(Skill):
    """机会识别技能"""
    
    def __init__(self, persona):
        super().__init__(
            name="机会识别",
            description="发现和评估潜在机会"
        )
        self.persona = persona
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行机会识别
        
        Returns:
            {
                "success": bool,
                "opportunities": List[str],  # 识别的机会
                "potential_score": float,    # 潜力评分
                "thinking_process": str      # 思考过程
            }
        """
        from backend.llm.llm_service import get_llm_service
        
        option = context.get("option", {})
        collected_info = context.get("collected_info", {})
        
        logger.info(f"[{self.persona.name}] 执行机会识别技能")
        
        llm = get_llm_service()
        if not llm or not llm.enabled:
            return {
                "success": True,
                "opportunities": ["需要LLM进行详细分析"],
                "potential_score": 0.7,
                "thinking_process": "LLM不可用，使用默认分析"
            }
        
        import asyncio
        import json
        
        prompt = f"""你是一个机会识别专家，请识别以下选项中的潜在机会：

选项：{option.get('title', '')} - {option.get('description', '')}

用户背景：
{json.dumps(collected_info, ensure_ascii=False, indent=2)[:500]}

请提供：
1. 3-5个潜在机会
2. 整体潜力评分（0-1）
3. 你的思考过程（如何识别这些机会的）

返回JSON格式：
{{
    "opportunities": ["机会1", "机会2"],
    "potential_score": 0.8,
    "thinking_process": "我的思考过程是..."
}}"""
        
        try:
            response = await asyncio.to_thread(
                llm.chat,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                response_format="json_object"
            )
            result = json.loads(response)
            
            return {
                "success": True,
                "opportunities": result.get("opportunities", []),
                "potential_score": result.get("potential_score", 0.7),
                "thinking_process": result.get("thinking_process", "未提供思考过程")
            }
        except Exception as e:
            logger.error(f"[{self.persona.name}] 机会识别失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "thinking_process": f"执行失败: {str(e)}"
            }


class FeasibilityEvaluationSkill(Skill):
    """可行性评估技能"""
    
    def __init__(self, persona):
        super().__init__(
            name="可行性评估",
            description="评估方案的实际可行性"
        )
        self.persona = persona
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行可行性评估
        
        Returns:
            {
                "success": bool,
                "feasibility_score": float,  # 可行性评分
                "barriers": List[str],        # 障碍因素
                "enablers": List[str],        # 促进因素
                "thinking_process": str       # 思考过程
            }
        """
        from backend.llm.llm_service import get_llm_service
        
        option = context.get("option", {})
        collected_info = context.get("collected_info", {})
        
        logger.info(f"[{self.persona.name}] 执行可行性评估技能")
        
        llm = get_llm_service()
        if not llm or not llm.enabled:
            return {
                "success": True,
                "feasibility_score": 0.75,
                "barriers": ["需要LLM进行详细分析"],
                "enablers": ["需要LLM进行详细分析"],
                "thinking_process": "LLM不可用，使用默认评估"
            }
        
        import asyncio
        import json
        
        prompt = f"""你是一个可行性评估专家，请评估以下选项的可行性：

选项：{option.get('title', '')} - {option.get('description', '')}

用户背景：
{json.dumps(collected_info, ensure_ascii=False, indent=2)[:500]}

请提供：
1. 可行性评分（0-1）
2. 3-5个主要障碍
3. 3-5个促进因素
4. 你的思考过程（如何评估可行性的）

返回JSON格式：
{{
    "feasibility_score": 0.8,
    "barriers": ["障碍1", "障碍2"],
    "enablers": ["促进因素1", "促进因素2"],
    "thinking_process": "我的思考过程是..."
}}"""
        
        try:
            response = await asyncio.to_thread(
                llm.chat,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format="json_object"
            )
            result = json.loads(response)
            
            return {
                "success": True,
                "feasibility_score": result.get("feasibility_score", 0.75),
                "barriers": result.get("barriers", []),
                "enablers": result.get("enablers", []),
                "thinking_process": result.get("thinking_process", "未提供思考过程")
            }
        except Exception as e:
            logger.error(f"[{self.persona.name}] 可行性评估失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "thinking_process": f"执行失败: {str(e)}"
            }


class ValueAlignmentSkill(Skill):
    """价值观对齐分析技能"""
    
    def __init__(self, persona):
        super().__init__(
            name="价值观对齐分析",
            description="分析选项与核心价值观的契合度"
        )
        self.persona = persona
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行价值观对齐分析
        
        Returns:
            {
                "success": bool,
                "alignment_score": float,     # 对齐度评分
                "aligned_values": List[str],  # 契合的价值观
                "conflicts": List[str]        # 冲突的价值观
            }
        """
        from backend.llm.llm_service import get_llm_service
        
        option = context.get("option", {})
        collected_info = context.get("collected_info", {})
        
        logger.info(f"[{self.persona.name}] 执行价值观对齐分析技能")
        
        llm = get_llm_service()
        if not llm or not llm.enabled:
            return {
                "success": True,
                "alignment_score": 0.85,
                "aligned_values": ["需要LLM进行详细分析"],
                "conflicts": [],
                "thinking_process": "LLM不可用，使用默认评估"
            }
        
        import asyncio
        import json
        
        # 获取用户的价值观优先级
        priorities = collected_info.get('priorities', {})
        
        prompt = f"""你是一个价值观分析专家，请分析选项与用户价值观的契合度：

选项：{option.get('title', '')} - {option.get('description', '')}

用户价值观优先级：
{json.dumps(priorities, ensure_ascii=False, indent=2)}

用户背景：
{json.dumps(collected_info, ensure_ascii=False, indent=2)[:500]}

请提供：
1. 价值观对齐度评分（0-1）
2. 契合的价值观（3-5个）
3. 可能冲突的价值观
4. 你的思考过程（如何分析价值观对齐的）

返回JSON格式：
{{
    "alignment_score": 0.85,
    "aligned_values": ["价值观1", "价值观2"],
    "conflicts": ["冲突1"],
    "thinking_process": "我的思考过程是..."
}}"""
        
        try:
            response = await asyncio.to_thread(
                llm.chat,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format="json_object"
            )
            result = json.loads(response)
            
            return {
                "success": True,
                "alignment_score": result.get("alignment_score", 0.85),
                "aligned_values": result.get("aligned_values", []),
                "conflicts": result.get("conflicts", []),
                "thinking_process": result.get("thinking_process", "未提供思考过程")
            }
        except Exception as e:
            logger.error(f"[{self.persona.name}] 价值观对齐分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "thinking_process": f"执行失败: {str(e)}"
            }


class RelationshipImpactSkill(Skill):
    """人际关系影响分析技能"""
    
    def __init__(self, persona):
        super().__init__(
            name="人际关系影响分析",
            description="评估决策对人际关系的影响"
        )
        self.persona = persona
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行人际关系影响分析
        
        Returns:
            {
                "success": bool,
                "relationship_impact": str,      # 影响评估
                "affected_relationships": List,  # 受影响的关系
                "social_capital_change": str     # 社交资本变化
            }
        """
        from backend.llm.llm_service import get_llm_service
        
        option = context.get("option", {})
        collected_info = context.get("collected_info", {})
        shared_facts = context.get("shared_facts", {})
        
        logger.info(f"[{self.persona.name}] 执行人际关系影响分析技能")
        
        llm = get_llm_service()
        if not llm or not llm.enabled:
            return {
                "success": True,
                "relationship_impact": "中性",
                "affected_relationships": ["需要LLM进行详细分析"],
                "social_capital_change": "持平",
                "thinking_process": "LLM不可用，使用默认评估"
            }
        
        import asyncio
        import json
        
        # 提取人际关系数据
        relationships = []
        if shared_facts:
            # SharedFactsLayer对象，需要访问其属性
            if hasattr(shared_facts, 'relationships'):
                relationships = shared_facts.relationships[:5] if shared_facts.relationships else []
        
        prompt = f"""你是一个人际关系分析专家，请评估选项对人际关系的影响：

选项：{option.get('title', '')} - {option.get('description', '')}

用户人际关系：
{len(relationships)}个关系

用户背景：
{json.dumps(collected_info, ensure_ascii=False, indent=2)[:500]}

请提供：
1. 整体影响评估（积极/中性/消极）
2. 受影响的关系类型
3. 社交资本变化（增加/持平/减少）
4. 你的思考过程（如何分析人际关系影响的）

返回JSON格式：
{{
    "relationship_impact": "积极/中性/消极",
    "affected_relationships": ["家人", "朋友"],
    "social_capital_change": "增加/持平/减少",
    "thinking_process": "我的思考过程是..."
}}"""
        
        try:
            response = await asyncio.to_thread(
                llm.chat,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format="json_object"
            )
            result = json.loads(response)
            
            return {
                "success": True,
                "relationship_impact": result.get("relationship_impact", "中性"),
                "affected_relationships": result.get("affected_relationships", []),
                "social_capital_change": result.get("social_capital_change", "持平"),
                "thinking_process": result.get("thinking_process", "未提供思考过程")
            }
        except Exception as e:
            logger.error(f"[{self.persona.name}] 人际关系影响分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "thinking_process": f"执行失败: {str(e)}"
            }


class InnovationPotentialSkill(Skill):
    """创新潜力评估技能"""
    
    def __init__(self, persona):
        super().__init__(
            name="创新潜力评估",
            description="评估方案的创新性和突破潜力"
        )
        self.persona = persona
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行创新潜力评估
        
        Returns:
            {
                "success": bool,
                "innovation_score": float,        # 创新性评分
                "breakthrough_potential": str,    # 突破潜力
                "alternative_approaches": List    # 替代方案
            }
        """
        from backend.llm.llm_service import get_llm_service
        
        option = context.get("option", {})
        collected_info = context.get("collected_info", {})
        
        logger.info(f"[{self.persona.name}] 执行创新潜力评估技能")
        
        llm = get_llm_service()
        if not llm or not llm.enabled:
            return {
                "success": True,
                "innovation_score": 0.8,
                "breakthrough_potential": "中等",
                "alternative_approaches": ["需要LLM进行详细分析"],
                "thinking_process": "LLM不可用，使用默认评估"
            }
        
        import asyncio
        import json
        
        prompt = f"""你是一个创新评估专家，请评估选项的创新潜力：

选项：{option.get('title', '')} - {option.get('description', '')}

用户背景：
{json.dumps(collected_info, ensure_ascii=False, indent=2)[:500]}

请提供：
1. 创新性评分（0-1）
2. 突破潜力（低/中/高）
3. 3-5个创新性的替代方案
4. 你的思考过程（如何评估创新潜力的）

返回JSON格式：
{{
    "innovation_score": 0.8,
    "breakthrough_potential": "高",
    "alternative_approaches": ["方案1", "方案2"],
    "thinking_process": "我的思考过程是..."
}}"""
        
        try:
            response = await asyncio.to_thread(
                llm.chat,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                response_format="json_object"
            )
            result = json.loads(response)
            
            return {
                "success": True,
                "innovation_score": result.get("innovation_score", 0.8),
                "breakthrough_potential": result.get("breakthrough_potential", "中"),
                "alternative_approaches": result.get("alternative_approaches", []),
                "thinking_process": result.get("thinking_process", "未提供思考过程")
            }
        except Exception as e:
            logger.error(f"[{self.persona.name}] 创新潜力评估失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "thinking_process": f"执行失败: {str(e)}"
            }


class WebSearchSkill(Skill):
    """联网搜索技能 - 使用Qwen内置联网搜索功能"""
    
    def __init__(self, persona):
        super().__init__(
            name="联网搜索",
            description="从互联网搜索最新信息、数据和趋势（使用Qwen内置搜索）"
        )
        self.persona = persona
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行联网搜索（使用Qwen内置搜索功能）
        
        Args:
            context: {
                "query": "搜索查询"（可选，如果没有则智能生成）,
                "option": {},  # 决策选项
                "collected_info": {}  # 收集的信息
            }
        
        Returns:
            {
                "success": bool,
                "search_content": str,  # 搜索到的内容
                "analysis": str,  # 分析结果
                "key_insights": List[str],  # 关键洞察
                "thinking_process": str
            }
        """
        import asyncio
        import json
        from backend.llm.llm_service import get_llm_service
        
        query = context.get("query", "")
        option = context.get("option", {})
        collected_info = context.get("collected_info", {})
        
        # 🆕 智能生成搜索query（而不是硬编码）
        if not query:
            llm = get_llm_service()
            if llm and llm.enabled:
                # 使用LLM生成精准的搜索关键词
                query_gen_prompt = f"""作为{self.persona.name}，我需要从互联网搜索信息来帮助决策。

决策选项：{option.get('title', '')}
选项描述：{option.get('description', '')}

用户背景：
{json.dumps(collected_info, ensure_ascii=False, indent=2)[:300]}

请生成1-3个精准的搜索关键词或短语，用于搜索最相关的信息。

要求：
1. 关键词要简洁、精准
2. 聚焦于最关键的信息点
3. 避免冗长的描述

返回JSON格式：
{{
    "search_queries": ["关键词1", "关键词2"],
    "reason": "为什么选择这些关键词"
}}"""
                
                try:
                    response = await asyncio.to_thread(
                        llm.chat,
                        messages=[{"role": "user", "content": query_gen_prompt}],
                        temperature=0.7,
                        response_format="json_object"
                    )
                    query_result = json.loads(response)
                    search_queries = query_result.get("search_queries", [])
                    
                    if search_queries:
                        # 使用第一个关键词作为主要搜索query
                        query = search_queries[0]
                        logger.info(f"[{self.persona.name}] 智能生成搜索query: {query}")
                    else:
                        # 降级：使用选项标题
                        query = option.get('title', '')
                except Exception as e:
                    logger.warning(f"[{self.persona.name}] 生成搜索query失败: {e}")
                    query = option.get('title', '')
            else:
                # LLM不可用，使用选项标题
                query = option.get('title', '')
        
        if not query.strip():
            return {
                "success": False,
                "search_content": "",
                "analysis": "搜索查询为空",
                "key_insights": [],
                "error": "查询为空"
            }
        
        logger.info(f"[{self.persona.name}] 执行联网搜索技能: {query}")
        
        llm = get_llm_service()
        if not llm or not llm.enabled:
            return {
                "success": False,
                "search_content": "",
                "analysis": "LLM服务不可用",
                "key_insights": [],
                "error": "LLM服务不可用"
            }
        
        try:
            # 构建搜索提示词
            search_prompt = f"""作为{self.persona.name}，我需要从互联网搜索最新信息来帮助决策。

决策选项：
- 标题：{option.get('title', '')}
- 描述：{option.get('description', '')}

用户背景：
{json.dumps(collected_info, ensure_ascii=False, indent=2)[:500]}

搜索查询：{query}

请帮我：
1. 搜索相关的最新信息、数据和趋势
2. 分析这些信息对决策的影响
3. 提供关键洞察和建议
4. 说明你的思考过程

返回JSON格式：
{{
    "search_content": "搜索到的主要内容摘要",
    "analysis": "基于搜索结果的分析",
    "key_insights": ["洞察1", "洞察2", "洞察3"],
    "recommendations": ["建议1", "建议2"],
    "thinking_process": "我的思考过程..."
}}"""
            
            # 使用Qwen的联网搜索功能
            if llm.provider.value == "qwen":
                # 🌐 直接调用Qwen API，启用真实联网搜索
                try:
                    logger.info(f"[{self.persona.name}] 🌐 启用Qwen联网搜索: {query}")
                    search_start = __import__('time').time()
                    
                    # 简化提示词，让Qwen自由发挥联网搜索能力
                    simple_prompt = f"""请帮我搜索关于"{query}"的最新信息。

决策背景：{option.get('title', '')}

请提供：
1. 搜索到的关键信息
2. 对决策的影响分析
3. 具体建议

请用自然语言回答，不需要JSON格式。"""
                    
                    # 🔥 使用asyncio.to_thread让同步调用变成异步，避免阻塞
                    response = await asyncio.to_thread(
                        llm.client.chat.completions.create,
                        model=llm.model,
                        messages=[{"role": "user", "content": simple_prompt}],
                        temperature=0.7,
                        extra_body={"enable_search": True},  # ✅ 启用真实联网搜索
                        timeout=60
                    )
                    
                    search_duration = __import__('time').time() - search_start
                    content = response.choices[0].message.content
                    
                    logger.info(f"[{self.persona.name}] ✅ 联网搜索完成，耗时{search_duration:.2f}秒，获得{len(content)}字符的内容")
                    
                    # 使用LLM提取结构化信息
                    extract_prompt = f"""请从以下搜索结果中提取关键信息：

搜索结果：
{content}

请提取并返回JSON格式：
{{
    "search_content": "搜索内容摘要（100字以内）",
    "analysis": "对决策的影响分析",
    "key_insights": ["洞察1", "洞察2", "洞察3"],
    "recommendations": ["建议1", "建议2"],
    "thinking_process": "分析思路"
}}"""
                    
                    extract_response = await asyncio.to_thread(
                        llm.chat,
                        messages=[{"role": "user", "content": extract_prompt}],
                        temperature=0.5,
                        response_format="json_object"
                    )
                    
                    result = json.loads(extract_response)
                    result["success"] = True
                    result["raw_search_content"] = content  # 保留原始搜索内容
                    result["search_enabled"] = True  # 标记使用了真实联网搜索
                    
                    return result
                
                except Exception as e:
                    logger.error(f"[{self.persona.name}] Qwen联网搜索失败: {e}")
                    # 降级到普通模式（不联网）
                    logger.warning(f"[{self.persona.name}] 降级到知识库模式")
                    response = await asyncio.to_thread(
                        llm.chat,
                        messages=[{"role": "user", "content": search_prompt}],
                        temperature=0.7,
                        response_format="json_object"
                    )
                    result = json.loads(response)
                    result["success"] = True
                    result["search_enabled"] = False
                    result["note"] = "使用知识库回答（联网搜索失败）"
                    return result
            else:
                # 非Qwen模型，使用普通对话（不联网）
                logger.info(f"[{self.persona.name}] 使用{llm.provider.value}模型（不支持联网搜索）")
                response = await asyncio.to_thread(
                    llm.chat,
                    messages=[{"role": "user", "content": search_prompt}],
                    temperature=0.7,
                    response_format="json_object"
                )
                result = json.loads(response)
                result["success"] = True
                result["search_enabled"] = False
                result["note"] = "基于模型知识回答（不支持联网搜索）"
                return result
            
        except Exception as e:
            logger.error(f"[{self.persona.name}] 联网搜索技能执行失败: {e}")
            return {
                "success": False,
                "search_content": "",
                "analysis": f"搜索失败: {str(e)}",
                "key_insights": [],
                "error": str(e),
                "thinking_process": f"执行失败: {str(e)}"
            }


class SkillRegistry:
    """技能注册表 - 管理所有可用技能"""
    
    # 技能名称到技能类的映射
    SKILL_CLASSES = {
        "混合检索": HybridRetrievalSkill,
        "数据分析": DataAnalysisSkill,
        "风险评估": RiskAssessmentSkill,
        "机会识别": OpportunityIdentificationSkill,
        "可行性评估": FeasibilityEvaluationSkill,
        "价值观对齐分析": ValueAlignmentSkill,
        "人际关系影响分析": RelationshipImpactSkill,
        "创新潜力评估": InnovationPotentialSkill,
        "联网搜索": WebSearchSkill,
    }
    
    @classmethod
    def create_skill(cls, skill_name: str, persona) -> Optional[Skill]:
        """根据技能名称创建技能实例"""
        skill_class = cls.SKILL_CLASSES.get(skill_name)
        if skill_class:
            return skill_class(persona)
        else:
            logger.warning(f"未知技能: {skill_name}")
            return None


class SkillExecutor:
    """技能执行器 - 负责执行智能体的技能"""
    
    def __init__(self, persona):
        self.persona = persona
        self.skills: Dict[str, Skill] = {}
        self._initialize_skills()
    
    def _initialize_skills(self):
        """初始化智能体的所有技能"""
        if not hasattr(self.persona, 'skill_names'):
            return
        
        for skill_name in self.persona.skill_names:
            skill = SkillRegistry.create_skill(skill_name, self.persona)
            if skill:
                self.skills[skill_name] = skill
                logger.info(f"[{self.persona.name}] 加载技能: {skill_name}")
    
    async def execute_skill(self, skill_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行指定技能
        
        Args:
            skill_name: 技能名称
            context: 执行上下文
        
        Returns:
            技能执行结果
        """
        skill = self.skills.get(skill_name)
        if not skill:
            return {
                "success": False,
                "error": f"技能不存在: {skill_name}"
            }
        
        try:
            result = await skill.execute(context)
            logger.info(f"[{self.persona.name}] 技能执行成功: {skill_name}")
            return result
        except Exception as e:
            logger.error(f"[{self.persona.name}] 技能执行失败: {skill_name} - {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_skills(self) -> List[Dict[str, str]]:
        """列出所有可用技能"""
        return [
            {
                "name": skill.name,
                "description": skill.description
            }
            for skill in self.skills.values()
        ]
    
    def has_skill(self, skill_name: str) -> bool:
        """检查是否拥有某个技能"""
        return skill_name in self.skills
