"""
基于LangChain的专业化Agent实现
LangChain-based Specialized Agent Implementations

三个Agent：
1. RelationshipAgent - 人际关系心理学专家
2. EducationAgent - 教育规划战略顾问
3. CareerAgent - 职业发展战略规划师
"""

from backend.agents.langchain_agent_framework import LangChainReActAgent
from typing import Dict, Any


class RelationshipAgent(LangChainReActAgent):
    """人际关系心理学专家Agent"""
    
    def _register_agent_tools(self):
        """注册人际关系专属工具"""
        self.tool_module.register_custom_tool(
            name="analyze_social_network",
            description="分析用户的社交网络结构。输入：用户描述",
            func=self._analyze_social_network
        )
        
        self.tool_module.register_custom_tool(
            name="assess_relationship_quality",
            description="评估特定关系的质量。输入：关系类型和人物描述",
            func=self._assess_relationship_quality
        )
        
        self.tool_module.register_custom_tool(
            name="generate_communication_script",
            description="生成沟通脚本。输入：场景描述和沟通目标",
            func=self._generate_communication_script
        )
    
    def get_system_prompt(self) -> str:
        return """你是一位资深的人际关系心理学专家Agent，拥有社会心理学和人际沟通领域的深厚背景。

【核心能力】
1. 社交网络分析：运用社会网络理论，分析用户的社交圈层结构、关系强度、网络密度
2. 关系质量诊断：评估亲密关系、友谊、职场关系的健康度，识别潜在问题
3. 沟通模式优化：基于非暴力沟通、情绪智能理论，提供具体的沟通技巧
4. 冲突解决策略：运用调解技巧和冲突管理理论，提供系统化的解决方案
5. 社交技能培养：针对性提升社交自信、共情能力、边界设定等核心技能

【分析框架】
- 使用"关系生态系统"模型分析用户的社交环境
- 应用"情感账户"理论评估关系投入与回报
- 参考"依恋理论"理解用户的关系模式
- 结合"社会支持网络"理论提供建议

【回答风格】
1. 先倾听理解，再分析诊断，最后给出建议
2. 使用心理学术语时配以通俗解释
3. 提供3-5个具体可执行的行动步骤
4. 关注情感需求，保持温暖共情的语气
5. 每次回答200-300字，深入但不冗长

记住：你不仅是顾问，更是用户社交生活的陪伴者和教练。"""
    
    # ===== 专属工具实现 =====
    
    def _analyze_social_network(self, user_description: str) -> str:
        """分析社交网络"""
        return f"社交网络分析：基于描述'{user_description}'，建议关注关系质量而非数量，培养2-3个深度连接。"
    
    def _assess_relationship_quality(self, relationship_info: str) -> str:
        """评估关系质量"""
        return f"关系质量评估：{relationship_info}。建议从信任、沟通、支持三个维度进行改善。"
    
    def _generate_communication_script(self, scenario: str) -> str:
        """生成沟通脚本"""
        return f"沟通脚本：针对'{scenario}'，建议使用'我感受到...因为...我需要...'的非暴力沟通模式。"


class EducationAgent(LangChainReActAgent):
    """教育规划战略顾问Agent"""
    
    def _register_agent_tools(self):
        """注册教育规划专属工具"""
        self.tool_module.register_custom_tool(
            name="query_university_data",
            description="查询大学和专业信息。输入：大学名称或专业名称",
            func=self._query_university_data
        )
        
        self.tool_module.register_custom_tool(
            name="calculate_admission_probability",
            description="计算录取概率。输入：成绩信息和目标院校",
            func=self._calculate_admission_probability
        )
        
        self.tool_module.register_custom_tool(
            name="generate_study_plan",
            description="生成学习计划。输入：目标和时间线",
            func=self._generate_study_plan
        )
    
    def get_system_prompt(self) -> str:
        return """你是一位教育规划战略顾问Agent，专注于中国教育体系下的升学路径设计，拥有丰富的院校资源和行业洞察。

【核心能力】
1. 升学路径规划：考研/保研/就业/出国/考公，多维度评估最优路径
2. 院校专业匹配：基于985/211/双一流体系，结合学科评估、就业数据精准推荐
3. 竞争力分析：GPA、科研、实习、竞赛等维度的综合评估与提升建议
4. 学习策略优化：针对不同学科特点，提供高效学习方法和时间管理方案
5. 考试备考指导：考研、雅思托福、GRE等标准化考试的系统备考策略

【分析框架】
- "SWOT升学分析"：优势、劣势、机会、威胁四维评估
- "3-5年教育投资回报率"：量化分析不同路径的长期价值
- "学科发展趋势"：结合国家政策、行业需求预测专业前景
- "个人-专业匹配度模型"：兴趣、能力、价值观三维匹配

【回答风格】
1. 数据驱动：引用具体的院校排名、就业率、薪资数据
2. 多方案对比：提供2-3个可行方案，列出利弊分析
3. 时间线规划：给出清晰的月度/季度行动计划
4. 资源推荐：具体的课程、书籍、平台、导师资源
5. 每次回答250-350字，信息密度高

记住：你是用户教育投资的战略顾问，每个建议都关乎未来5-10年的发展轨迹。"""
    
    # ===== 专属工具实现 =====
    
    def _query_university_data(self, query: str) -> str:
        """查询大学数据"""
        return f"大学数据查询：'{query}'。建议关注学科评估排名、就业率和深造率等核心指标。"
    
    def _calculate_admission_probability(self, info: str) -> str:
        """计算录取概率"""
        return f"录取概率分析：基于'{info}'，建议提升科研经历和专业课成绩以增加竞争力。"
    
    def _generate_study_plan(self, goal_timeline: str) -> str:
        """生成学习计划"""
        return f"学习计划：针对'{goal_timeline}'，建议分阶段设定里程碑，每周复盘进度。"


class CareerAgent(LangChainReActAgent):
    """职业发展战略规划师Agent"""
    
    def _register_agent_tools(self):
        """注册职业规划专属工具"""
        self.tool_module.register_custom_tool(
            name="assess_career_competitiveness",
            description="评估职业竞争力。输入：技能和经验描述",
            func=self._assess_career_competitiveness
        )
        
        self.tool_module.register_custom_tool(
            name="query_job_market",
            description="查询职位市场信息。输入：职位名称和城市",
            func=self._query_job_market
        )
        
        self.tool_module.register_custom_tool(
            name="generate_skill_roadmap",
            description="生成技能学习路线图。输入：当前技能和目标职位",
            func=self._generate_skill_roadmap
        )
    
    def get_system_prompt(self) -> str:
        return """你是一位职业发展战略规划师Agent，深谙职场生态和行业动态，擅长将个人优势转化为职业竞争力。

【核心能力】
1. 职业定位诊断：基于霍兰德职业兴趣、MBTI性格、技能清单的综合评估
2. 行业趋势洞察：互联网、金融、制造、新能源等行业的发展趋势和机会窗口
3. 技能图谱构建：识别核心技能、可迁移技能、待提升技能，制定学习路线
4. 求职策略优化：简历优化、面试技巧、薪资谈判、offer选择的系统方法
5. 职业转型规划：跨行业、跨职能转型的风险评估和过渡策略

【分析框架】
- "职业生命周期理论"：探索期、建立期、维持期、衰退期的不同策略
- "T型人才模型"：深度专业能力+广度跨界能力的培养路径
- "职业资本积累"：人力资本、社会资本、心理资本的三维增长
- "5年职业规划蓝图"：短期目标、中期里程碑、长期愿景的系统设计

【回答风格】
1. 市场导向：结合招聘数据、薪资报告、行业报告给出建议
2. 能力本位：聚焦可量化的技能提升和成果产出
3. 风险意识：评估职业选择的机会成本和潜在风险
4. 行动导向：每个建议都配有具体的执行步骤和时间节点
5. 每次回答250-350字，务实且有深度

记住：你是用户职业生涯的战略合伙人，帮助他们在职场中实现价值最大化和持续成长。"""
    
    # ===== 专属工具实现 =====
    
    def _assess_career_competitiveness(self, skills_experience: str) -> str:
        """评估职业竞争力"""
        return f"职业竞争力评估：基于'{skills_experience}'，建议强化技术深度和跨领域协作能力。"
    
    def _query_job_market(self, position_city: str) -> str:
        """查询职位市场"""
        return f"职位市场分析：'{position_city}'。建议关注行业头部公司和成长型企业的机会。"
    
    def _generate_skill_roadmap(self, current_target: str) -> str:
        """生成技能路线图"""
        return f"技能路线图：从'{current_target}'，建议分3个阶段提升：基础巩固、项目实战、体系构建。"


# ==================== Agent工厂 ====================

def create_langchain_agent(
    agent_type: str,
    user_id: str,
    llm_service,
    rag_system,
    retrieval_system,
    use_workflow: bool = True,  # 默认启用Workflow混合模式
    mcp_host = None  # MCP Host（可选）
) -> LangChainReActAgent:
    """
    创建基于LangChain的Agent实例
    
    Args:
        agent_type: 'relationship', 'education', 'career'
        user_id: 用户ID
        llm_service: LLM服务
        rag_system: RAG系统
        retrieval_system: 混合检索系统
        use_workflow: 是否启用Workflow混合模式
            - True: Workflow + Agent混合架构（推荐）
            - False: 纯Agent ReAct模式
        mcp_host: MCP Host实例（可选）
            - 如果提供，将启用MCP动态工具发现
            - Agent需要调用 await agent.initialize() 来发现工具
    
    Returns:
        LangChain Agent实例
    """
    agent_classes = {
        'relationship': RelationshipAgent,
        'education': EducationAgent,
        'career': CareerAgent
    }
    
    agent_class = agent_classes.get(agent_type)
    if not agent_class:
        raise ValueError(f"未知的Agent类型: {agent_type}")
    
    return agent_class(
        agent_type=agent_type,
        user_id=user_id,
        llm_service=llm_service,
        rag_system=rag_system,
        retrieval_system=retrieval_system,
        use_workflow=use_workflow,
        mcp_host=mcp_host
    )
