"""
统一决策流程管理器
管理三维垂直决策的完整流程
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import uuid

from backend.vertical.career.career_decision_engine import CareerDecisionEngine, CareerDecisionContext, JobPosition
from backend.vertical.relationship.relationship_decision_engine import RelationshipDecisionEngine, RelationshipDecisionContext, Person
from backend.vertical.education.education_decision_engine import EducationDecisionEngine, EducationDecisionContext, School


class DecisionDomain(Enum):
    """决策领域"""
    CAREER = "career"  # 职业
    RELATIONSHIP = "relationship"  # 人际关系
    EDUCATION = "education"  # 升学


class DecisionStage(Enum):
    """决策阶段"""
    MODELING = "modeling"  # 决策建模
    COLLECTING = "collecting"  # 信息收集
    ANALYZING = "analyzing"  # 方案分析
    EXECUTING = "executing"  # 决策执行
    COMPLETED = "completed"  # 已完成


@dataclass
class DecisionSession:
    """决策会话"""
    session_id: str
    user_id: str
    domain: DecisionDomain
    stage: DecisionStage
    question: str
    created_at: datetime
    updated_at: datetime
    
    # 决策建模阶段数据
    options: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    goals: Dict[str, Any] = field(default_factory=dict)
    
    # 信息收集阶段数据
    information_checklist: List[Dict[str, Any]] = field(default_factory=list)
    collected_information: Dict[str, Any] = field(default_factory=dict)
    
    # 方案分析阶段数据
    analysis_results: List[Dict[str, Any]] = field(default_factory=list)
    comparison_matrix: Dict[str, Any] = field(default_factory=dict)
    
    # 执行阶段数据
    action_plan: List[Dict[str, Any]] = field(default_factory=list)
    progress_tracking: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "domain": self.domain.value,
            "stage": self.stage.value,
            "question": self.question,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "options": self.options,
            "assumptions": self.assumptions,
            "constraints": self.constraints,
            "goals": self.goals,
            "information_checklist": self.information_checklist,
            "collected_information": self.collected_information,
            "analysis_results": self.analysis_results,
            "comparison_matrix": self.comparison_matrix,
            "action_plan": self.action_plan,
            "progress_tracking": self.progress_tracking
        }


class UnifiedDecisionWorkflow:
    """
    统一决策流程管理器
    
    管理三个垂直维度的决策流程：
    1. 职业选择决策
    2. 人际关系决策
    3. 升学规划决策
    """
    
    def __init__(self):
        self.career_engine = CareerDecisionEngine()
        self.relationship_engine = RelationshipDecisionEngine()
        self.education_engine = EducationDecisionEngine()
        
        # 会话存储（实际应该用数据库）
        self.sessions: Dict[str, DecisionSession] = {}
    
    def identify_decision_domain(self, question: str) -> DecisionDomain:
        """
        识别决策领域
        
        Args:
            question: 用户问题
        
        Returns:
            决策领域
        """
        question_lower = question.lower()
        
        # 职业相关关键词
        career_keywords = ["工作", "职业", "跳槽", "转行", "面试", "offer", "公司", "岗位", "薪资", "创业"]
        if any(keyword in question_lower for keyword in career_keywords):
            return DecisionDomain.CAREER
        
        # 关系相关关键词
        relationship_keywords = ["关系", "家人", "父母", "伴侣", "朋友", "同事", "沟通", "冲突", "结婚", "分手"]
        if any(keyword in question_lower for keyword in relationship_keywords):
            return DecisionDomain.RELATIONSHIP
        
        # 升学相关关键词
        education_keywords = ["学校", "大学", "考研", "留学", "专业", "录取", "考试", "升学", "读书"]
        if any(keyword in question_lower for keyword in education_keywords):
            return DecisionDomain.EDUCATION
        
        # 默认返回职业
        return DecisionDomain.CAREER
    
    def create_session(
        self,
        user_id: str,
        question: str,
        domain: Optional[DecisionDomain] = None
    ) -> DecisionSession:
        """
        创建决策会话
        
        Args:
            user_id: 用户ID
            question: 决策问题
            domain: 决策领域（可选，自动识别）
        
        Returns:
            决策会话
        """
        if domain is None:
            domain = self.identify_decision_domain(question)
        
        session = DecisionSession(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            domain=domain,
            stage=DecisionStage.MODELING,
            question=question,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.sessions[session.session_id] = session
        return session
    
    def modeling_stage(
        self,
        session_id: str,
        options: List[str],
        assumptions: List[str],
        constraints: Dict[str, Any],
        goals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        决策建模阶段
        
        Args:
            session_id: 会话ID
            options: 选项列表
            assumptions: 假设列表
            constraints: 约束条件
            goals: 决策目标
        
        Returns:
            建模结果
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"会话不存在: {session_id}")
        
        session.options = options
        session.assumptions = assumptions
        session.constraints = constraints
        session.goals = goals
        session.stage = DecisionStage.COLLECTING
        session.updated_at = datetime.now()
        
        # 生成信息收集清单
        checklist = self._generate_information_checklist(session)
        session.information_checklist = checklist
        
        return {
            "session_id": session_id,
            "stage": "modeling_completed",
            "next_stage": "collecting",
            "options_count": len(options),
            "information_checklist": checklist,
            "message": f"决策建模完成，识别到{len(options)}个选项，需要收集{len(checklist)}项信息"
        }
    
    def _generate_information_checklist(self, session: DecisionSession) -> List[Dict[str, Any]]:
        """生成信息收集清单"""
        checklist = []
        
        if session.domain == DecisionDomain.CAREER:
            checklist = [
                {"item": "目标岗位的详细JD", "priority": "high", "collected": False},
                {"item": "目标公司的薪资范围", "priority": "high", "collected": False},
                {"item": "所需技能清单", "priority": "high", "collected": False},
                {"item": "行业发展趋势", "priority": "medium", "collected": False},
                {"item": "相似背景的转型案例", "priority": "medium", "collected": False},
                {"item": "学习资源和时间成本", "priority": "medium", "collected": False}
            ]
        elif session.domain == DecisionDomain.RELATIONSHIP:
            checklist = [
                {"item": "关键人物的态度和顾虑", "priority": "high", "collected": False},
                {"item": "当前关系状态评估", "priority": "high", "collected": False},
                {"item": "历史沟通记录", "priority": "medium", "collected": False},
                {"item": "各方的期待和底线", "priority": "high", "collected": False},
                {"item": "可能的冲突点", "priority": "medium", "collected": False}
            ]
        elif session.domain == DecisionDomain.EDUCATION:
            checklist = [
                {"item": "目标学校的录取分数线", "priority": "high", "collected": False},
                {"item": "专业课程设置和就业方向", "priority": "high", "collected": False},
                {"item": "学费和生活成本", "priority": "high", "collected": False},
                {"item": "历年录取数据", "priority": "medium", "collected": False},
                {"item": "毕业生就业情况", "priority": "medium", "collected": False},
                {"item": "备考资源和时间规划", "priority": "high", "collected": False}
            ]
        
        return checklist
    
    def collecting_stage(
        self,
        session_id: str,
        collected_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        信息收集阶段
        
        Args:
            session_id: 会话ID
            collected_info: 收集到的信息
        
        Returns:
            收集结果
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"会话不存在: {session_id}")
        
        session.collected_information.update(collected_info)
        session.updated_at = datetime.now()
        
        # 更新清单状态
        for item in session.information_checklist:
            if item["item"] in collected_info:
                item["collected"] = True
        
        # 检查是否收集完成
        high_priority_items = [item for item in session.information_checklist if item["priority"] == "high"]
        collected_high_priority = [item for item in high_priority_items if item["collected"]]
        
        completion_rate = len(collected_high_priority) / len(high_priority_items) if high_priority_items else 1.0
        
        if completion_rate >= 0.8:
            session.stage = DecisionStage.ANALYZING
            return {
                "session_id": session_id,
                "stage": "collecting_completed",
                "next_stage": "analyzing",
                "completion_rate": round(completion_rate, 2),
                "message": "关键信息收集完成，可以进入方案分析阶段"
            }
        else:
            return {
                "session_id": session_id,
                "stage": "collecting_in_progress",
                "completion_rate": round(completion_rate, 2),
                "missing_items": [item["item"] for item in high_priority_items if not item["collected"]],
                "message": f"信息收集进度{completion_rate*100:.0f}%，还需收集关键信息"
            }
    
    def analyzing_stage(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        方案分析阶段
        
        Args:
            session_id: 会话ID
        
        Returns:
            分析结果
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"会话不存在: {session_id}")
        
        # 根据领域调用相应的引擎
        if session.domain == DecisionDomain.CAREER:
            results = self._analyze_career_options(session)
        elif session.domain == DecisionDomain.RELATIONSHIP:
            results = self._analyze_relationship_options(session)
        elif session.domain == DecisionDomain.EDUCATION:
            results = self._analyze_education_options(session)
        else:
            raise ValueError(f"未知的决策领域: {session.domain}")
        
        session.analysis_results = results
        session.stage = DecisionStage.EXECUTING
        session.updated_at = datetime.now()
        
        return {
            "session_id": session_id,
            "stage": "analyzing_completed",
            "next_stage": "executing",
            "analysis_results": results,
            "message": "方案分析完成，可以制定执行计划"
        }
    
    def _analyze_career_options(self, session: DecisionSession) -> List[Dict[str, Any]]:
        """分析职业选项（集成决策逻辑画像）"""
        from backend.vertical.decision_logic_integration import get_decision_logic_profile
        
        # 获取决策逻辑画像
        decision_profile = get_decision_logic_profile(session.user_id)
        
        # 这里简化处理，实际应该从collected_information中提取数据
        results = []
        for option in session.options:
            result = {
                "option": option,
                "feasibility": 0.7,
                "benefit": 0.8,
                "risk": 0.4,
                "recommendation": "推荐"
            }
            
            # 如果有决策逻辑画像，调整评分
            if decision_profile:
                dimensions = decision_profile.get('dimensions', {})
                
                # 风险偏好影响风险评估
                if '风险偏好' in dimensions:
                    risk_tendency = dimensions['风险偏好'].get('value', 0)
                    # 风险偏好高的人，风险评分降低
                    result['risk'] = max(0.1, result['risk'] - risk_tendency * 0.2)
                
                # 主动性影响可行性评估
                if '主动性' in dimensions:
                    initiative = dimensions['主动性'].get('value', 0)
                    result['feasibility'] = min(1.0, result['feasibility'] + initiative * 0.15)
                
                result['decision_logic_applied'] = True
                result['decision_logic_confidence'] = decision_profile.get('confidence', 0)
            
            results.append(result)
        
        return results
    
    def _analyze_relationship_options(self, session: DecisionSession) -> List[Dict[str, Any]]:
        """分析关系选项（集成决策逻辑画像）"""
        from backend.vertical.decision_logic_integration import get_decision_logic_profile
        
        # 获取决策逻辑画像
        decision_profile = get_decision_logic_profile(session.user_id)
        
        results = []
        for option in session.options:
            result = {
                "option": option,
                "feasibility": 0.6,
                "benefit": 0.7,
                "risk": 0.5,
                "recommendation": "可行"
            }
            
            # 如果有决策逻辑画像，调整评分
            if decision_profile:
                dimensions = decision_profile.get('dimensions', {})
                
                # 权威态度影响关系决策
                if '权威态度' in dimensions:
                    authority = dimensions['权威态度'].get('value', 0)
                    # 权威态度高的人，更倾向于遵从规则
                    result['feasibility'] = min(1.0, result['feasibility'] + authority * 0.1)
                
                # 思维方式影响沟通策略
                if '思维方式' in dimensions:
                    thinking = dimensions['思维方式'].get('value', 0)
                    result['benefit'] = min(1.0, result['benefit'] + thinking * 0.12)
                
                result['decision_logic_applied'] = True
                result['decision_logic_confidence'] = decision_profile.get('confidence', 0)
            
            results.append(result)
        
        return results
    
    def _analyze_education_options(self, session: DecisionSession) -> List[Dict[str, Any]]:
        """分析升学选项（集成决策逻辑画像）"""
        from backend.vertical.decision_logic_integration import get_decision_logic_profile
        
        # 获取决策逻辑画像
        decision_profile = get_decision_logic_profile(session.user_id)
        
        results = []
        for option in session.options:
            result = {
                "option": option,
                "feasibility": 0.75,
                "benefit": 0.85,
                "risk": 0.3,
                "recommendation": "强烈推荐"
            }
            
            # 如果有决策逻辑画像，调整评分
            if decision_profile:
                dimensions = decision_profile.get('dimensions', {})
                
                # 创新倾向影响学校选择
                if '创新倾向' in dimensions:
                    innovation = dimensions['创新倾向'].get('value', 0)
                    # 创新倾向高的人，更看重学校的创新能力
                    result['benefit'] = min(1.0, result['benefit'] + innovation * 0.1)
                
                # 损失厌恶影响风险评估
                if '损失厌恶' in dimensions:
                    loss_aversion = dimensions['损失厌恶'].get('value', 0)
                    # 损失厌恶高的人，风险评分提高
                    result['risk'] = min(1.0, result['risk'] + loss_aversion * 0.15)
                
                # 思维方式影响学习路径规划
                if '思维方式' in dimensions:
                    thinking = dimensions['思维方式'].get('value', 0)
                    result['feasibility'] = min(1.0, result['feasibility'] + thinking * 0.1)
                
                result['decision_logic_applied'] = True
                result['decision_logic_confidence'] = decision_profile.get('confidence', 0)
            
            results.append(result)
        
        return results
    
    def executing_stage(
        self,
        session_id: str,
        selected_option: str,
        action_plan: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        决策执行阶段
        
        Args:
            session_id: 会话ID
            selected_option: 选择的选项
            action_plan: 行动计划
        
        Returns:
            执行计划
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"会话不存在: {session_id}")
        
        session.action_plan = action_plan
        session.updated_at = datetime.now()
        
        return {
            "session_id": session_id,
            "stage": "executing",
            "selected_option": selected_option,
            "action_plan": action_plan,
            "message": "执行计划已制定，开始追踪进度"
        }
    
    def track_progress(
        self,
        session_id: str,
        progress_update: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        追踪执行进度
        
        Args:
            session_id: 会话ID
            progress_update: 进度更新
        
        Returns:
            进度状态
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"会话不存在: {session_id}")
        
        progress_update["timestamp"] = datetime.now().isoformat()
        session.progress_tracking.append(progress_update)
        session.updated_at = datetime.now()
        
        return {
            "session_id": session_id,
            "progress_count": len(session.progress_tracking),
            "latest_update": progress_update,
            "message": "进度已更新"
        }
    
    def get_session(self, session_id: str) -> Optional[DecisionSession]:
        """获取会话"""
        return self.sessions.get(session_id)
    
    def list_user_sessions(self, user_id: str) -> List[DecisionSession]:
        """列出用户的所有会话"""
        return [
            session for session in self.sessions.values()
            if session.user_id == user_id
        ]


# 示例使用
if __name__ == "__main__":
    workflow = UnifiedDecisionWorkflow()
    
    # 创建职业决策会话
    session = workflow.create_session(
        user_id="user_123",
        question="我是否应该跳槽到字节跳动？"
    )
    
    print(f"创建会话: {session.session_id}")
    print(f"识别领域: {session.domain.value}")
    print(f"当前阶段: {session.stage.value}")
    
    # 决策建模
    modeling_result = workflow.modeling_stage(
        session_id=session.session_id,
        options=["跳槽到字节", "留在当前公司", "寻找其他机会"],
        assumptions=["字节的offer是真实的", "当前公司不会挽留", "市场环境稳定"],
        constraints={"时间": "3个月内决定", "薪资": "不低于当前30%"},
        goals={"短期": "薪资提升", "长期": "技术成长"}
    )
    
    print(f"\n建模结果: {modeling_result['message']}")
    print(f"信息清单: {len(modeling_result['information_checklist'])}项")
    
    # 信息收集
    collecting_result = workflow.collecting_stage(
        session_id=session.session_id,
        collected_info={
            "目标岗位的详细JD": "高级Python工程师，要求3年经验...",
            "目标公司的薪资范围": "30-40万",
            "所需技能清单": ["Python", "Django", "Redis", "Kafka"]
        }
    )
    
    print(f"\n收集结果: {collecting_result['message']}")
    print(f"完成度: {collecting_result['completion_rate']*100:.0f}%")
