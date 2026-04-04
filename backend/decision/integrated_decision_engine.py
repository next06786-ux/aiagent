"""
整合决策引擎
将三维垂直决策引擎整合到现有的决策推演系统中
"""
from typing import Dict, List, Any, Optional
from enum import Enum
import re

from backend.vertical.career.career_decision_engine import CareerDecisionEngine
from backend.vertical.relationship.relationship_decision_engine import RelationshipDecisionEngine
from backend.vertical.education.education_decision_engine import EducationDecisionEngine


class DecisionType(Enum):
    """决策类型"""
    CAREER = "career"  # 职业决策
    RELATIONSHIP = "relationship"  # 关系决策
    EDUCATION = "education"  # 升学决策
    GENERAL = "general"  # 通用决策（原有算法）


class IntegratedDecisionEngine:
    """
    整合决策引擎
    
    根据决策类型调用不同的引擎：
    - 职业决策：使用职业决策引擎（真实岗位数据）
    - 关系决策：使用关系决策引擎（关系网络分析）
    - 升学决策：使用升学决策引擎（学校数据分析）
    - 通用决策：使用原有的LoRA推演算法
    """
    
    def __init__(self):
        self.career_engine = CareerDecisionEngine()
        self.relationship_engine = RelationshipDecisionEngine()
        self.education_engine = EducationDecisionEngine()
    
    def identify_decision_type(self, question: str) -> DecisionType:
        """
        自动识别决策类型
        
        Args:
            question: 用户问题
        
        Returns:
            决策类型
        """
        question_lower = question.lower()
        
        # 职业相关关键词
        career_keywords = [
            "工作", "职业", "跳槽", "转行", "面试", "offer", "公司", "岗位", 
            "薪资", "创业", "辞职", "升职", "加薪", "项目", "团队"
        ]
        career_score = sum(1 for keyword in career_keywords if keyword in question_lower)
        
        # 关系相关关键词
        relationship_keywords = [
            "关系", "家人", "父母", "伴侣", "朋友", "同事", "沟通", "冲突", 
            "结婚", "分手", "吵架", "矛盾", "理解", "支持", "反对"
        ]
        relationship_score = sum(1 for keyword in relationship_keywords if keyword in question_lower)
        
        # 升学相关关键词
        education_keywords = [
            "学校", "大学", "考研", "留学", "专业", "录取", "考试", 
            "升学", "读书", "学习", "深造", "研究生", "博士"
        ]
        education_score = sum(1 for keyword in education_keywords if keyword in question_lower)
        
        # 选择得分最高的类型
        scores = {
            DecisionType.CAREER: career_score,
            DecisionType.RELATIONSHIP: relationship_score,
            DecisionType.EDUCATION: education_score
        }
        
        max_score = max(scores.values())
        if max_score == 0:
            return DecisionType.GENERAL
        
        for decision_type, score in scores.items():
            if score == max_score:
                return decision_type
        
        return DecisionType.GENERAL
    
    def get_decision_type_info(self, decision_type: DecisionType) -> Dict[str, Any]:
        """
        获取决策类型的详细信息
        
        Args:
            decision_type: 决策类型
        
        Returns:
            决策类型信息
        """
        info_map = {
            DecisionType.CAREER: {
                "type": "career",
                "name": "职业决策",
                "description": "基于真实岗位数据和市场信息的职业选择决策",
                "features": [
                    "岗位匹配分析",
                    "薪资预期分析",
                    "学习路径规划",
                    "转型风险评估"
                ],
                "data_sources": [
                    "招聘网站API",
                    "行业报告",
                    "薪资数据",
                    "技能树"
                ],
                "suitable_for": [
                    "跳槽决策",
                    "转行规划",
                    "职业发展",
                    "技能提升"
                ]
            },
            DecisionType.RELATIONSHIP: {
                "type": "relationship",
                "name": "关系决策",
                "description": "基于关系网络和沟通策略的人际关系决策",
                "features": [
                    "关系网络建模",
                    "冲突分析",
                    "沟通策略建议",
                    "关系影响评估"
                ],
                "data_sources": [
                    "用户输入的关系信息",
                    "沟通历史",
                    "关系动态"
                ],
                "suitable_for": [
                    "家庭关系",
                    "伴侣关系",
                    "职场关系",
                    "朋友关系"
                ]
            },
            DecisionType.EDUCATION: {
                "type": "education",
                "name": "升学决策",
                "description": "基于学校数据和录取信息的升学规划决策",
                "features": [
                    "学校匹配分析",
                    "录取概率评估",
                    "成本收益分析",
                    "备考规划"
                ],
                "data_sources": [
                    "学校数据库",
                    "录取分数线",
                    "就业数据",
                    "学费信息"
                ],
                "suitable_for": [
                    "高考志愿",
                    "考研选择",
                    "留学规划",
                    "专业选择"
                ]
            },
            DecisionType.GENERAL: {
                "type": "general",
                "name": "通用决策",
                "description": "基于AI推演的通用决策分析（原有算法）",
                "features": [
                    "多分支推演",
                    "个性化模拟",
                    "风险评估",
                    "决策图谱"
                ],
                "data_sources": [
                    "用户画像",
                    "历史数据",
                    "AI推演",
                    "知识图谱"
                ],
                "suitable_for": [
                    "复杂决策",
                    "长期规划",
                    "不确定性决策",
                    "其他类型决策"
                ]
            }
        }
        
        return info_map.get(decision_type, info_map[DecisionType.GENERAL])
    
    def generate_information_checklist(
        self,
        decision_type: DecisionType,
        question: str,
        options: List[str]
    ) -> List[Dict[str, Any]]:
        """
        根据决策类型生成信息收集清单
        
        Args:
            decision_type: 决策类型
            question: 决策问题
            options: 选项列表
        
        Returns:
            信息收集清单
        """
        if decision_type == DecisionType.CAREER:
            return [
                {
                    "category": "岗位信息",
                    "items": [
                        {"key": "job_title", "label": "目标岗位名称", "type": "text", "required": True},
                        {"key": "company", "label": "目标公司", "type": "text", "required": True},
                        {"key": "salary_range", "label": "薪资范围（万/年）", "type": "range", "required": True},
                        {"key": "required_skills", "label": "所需技能", "type": "tags", "required": True},
                        {"key": "experience_required", "label": "要求工作年限", "type": "number", "required": True}
                    ]
                },
                {
                    "category": "当前状况",
                    "items": [
                        {"key": "current_position", "label": "当前职位", "type": "text", "required": False},
                        {"key": "current_salary", "label": "当前薪资（万/年）", "type": "number", "required": True},
                        {"key": "years_experience", "label": "工作年限", "type": "number", "required": True},
                        {"key": "current_skills", "label": "当前技能", "type": "tags", "required": True}
                    ]
                },
                {
                    "category": "个人偏好",
                    "items": [
                        {"key": "target_industry", "label": "目标行业", "type": "text", "required": False},
                        {"key": "location_preference", "label": "地域偏好", "type": "text", "required": False},
                        {"key": "financial_pressure", "label": "财务压力（0-1）", "type": "slider", "required": False},
                        {"key": "growth_priority", "label": "成长优先级（0-1）", "type": "slider", "required": False}
                    ]
                }
            ]
        
        elif decision_type == DecisionType.RELATIONSHIP:
            return [
                {
                    "category": "关键人物",
                    "items": [
                        {"key": "key_people", "label": "涉及的关键人物", "type": "list", "required": True},
                        {"key": "relationship_types", "label": "关系类型", "type": "tags", "required": True},
                        {"key": "support_levels", "label": "支持程度（-1到1）", "type": "list", "required": True}
                    ]
                },
                {
                    "category": "冲突分析",
                    "items": [
                        {"key": "current_conflicts", "label": "当前冲突点", "type": "textarea", "required": True},
                        {"key": "key_concerns", "label": "各方关键顾虑", "type": "list", "required": True},
                        {"key": "communication_history", "label": "沟通历史", "type": "textarea", "required": False}
                    ]
                },
                {
                    "category": "目标期望",
                    "items": [
                        {"key": "relationship_goals", "label": "关系目标", "type": "textarea", "required": True},
                        {"key": "acceptable_outcomes", "label": "可接受的结果", "type": "textarea", "required": False}
                    ]
                }
            ]
        
        elif decision_type == DecisionType.EDUCATION:
            return [
                {
                    "category": "学校信息",
                    "items": [
                        {"key": "school_name", "label": "目标学校", "type": "text", "required": True},
                        {"key": "major", "label": "目标专业", "type": "text", "required": True},
                        {"key": "admission_score", "label": "录取分数线", "type": "number", "required": True},
                        {"key": "tuition", "label": "学费（万/年）", "type": "number", "required": True},
                        {"key": "program_duration", "label": "学制（年）", "type": "number", "required": True}
                    ]
                },
                {
                    "category": "当前状况",
                    "items": [
                        {"key": "current_score", "label": "当前成绩/分数", "type": "number", "required": True},
                        {"key": "study_time_available", "label": "可用备考时间（月）", "type": "number", "required": True},
                        {"key": "budget_limit", "label": "预算上限（万）", "type": "number", "required": False}
                    ]
                },
                {
                    "category": "目标规划",
                    "items": [
                        {"key": "career_goal", "label": "职业目标", "type": "text", "required": False},
                        {"key": "location_preference", "label": "地域偏好", "type": "text", "required": False},
                        {"key": "family_support", "label": "家庭支持程度（0-1）", "type": "slider", "required": False}
                    ]
                }
            ]
        
        else:  # GENERAL
            return [
                {
                    "category": "决策上下文",
                    "items": [
                        {"key": "decision_context", "label": "决策背景", "type": "textarea", "required": True},
                        {"key": "user_constraints", "label": "现实约束", "type": "textarea", "required": True},
                        {"key": "priorities", "label": "优先级", "type": "textarea", "required": True}
                    ]
                },
                {
                    "category": "关键信息",
                    "items": [
                        {"key": "concerns", "label": "主要顾虑", "type": "textarea", "required": True},
                        {"key": "options_mentioned", "label": "考虑的选项", "type": "list", "required": True}
                    ]
                }
            ]
    
    def validate_collected_info(
        self,
        decision_type: DecisionType,
        collected_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        验证收集的信息是否完整
        
        Args:
            decision_type: 决策类型
            collected_info: 收集的信息
        
        Returns:
            验证结果
        """
        checklist = self.generate_information_checklist(decision_type, "", [])
        
        missing_required = []
        collected_count = 0
        total_required = 0
        
        for category in checklist:
            for item in category["items"]:
                if item["required"]:
                    total_required += 1
                    if item["key"] not in collected_info or not collected_info[item["key"]]:
                        missing_required.append(item["label"])
                    else:
                        collected_count += 1
        
        completion_rate = collected_count / total_required if total_required > 0 else 1.0
        
        return {
            "is_complete": len(missing_required) == 0,
            "completion_rate": round(completion_rate, 2),
            "missing_required": missing_required,
            "collected_count": collected_count,
            "total_required": total_required
        }
    
    def prepare_engine_context(
        self,
        decision_type: DecisionType,
        collected_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        将收集的信息转换为引擎所需的上下文格式
        
        Args:
            decision_type: 决策类型
            collected_info: 收集的信息
        
        Returns:
            引擎上下文
        """
        if decision_type == DecisionType.CAREER:
            from backend.vertical.career.career_decision_engine import CareerDecisionContext, JobPosition
            
            context = CareerDecisionContext(
                current_position=collected_info.get("current_position"),
                current_salary=float(collected_info.get("current_salary", 0)),
                years_experience=int(collected_info.get("years_experience", 0)),
                current_skills=collected_info.get("current_skills", []),
                target_industry=collected_info.get("target_industry"),
                location_preference=collected_info.get("location_preference"),
                financial_pressure=float(collected_info.get("financial_pressure", 0.5)),
                growth_priority=float(collected_info.get("growth_priority", 0.5))
            )
            
            # 构建岗位信息
            salary_range = collected_info.get("salary_range", [20, 30])
            if isinstance(salary_range, str):
                # 解析 "20-30" 格式
                parts = salary_range.split("-")
                salary_range = [float(parts[0]), float(parts[1])] if len(parts) == 2 else [20, 30]
            
            job = JobPosition(
                title=collected_info.get("job_title", ""),
                company=collected_info.get("company", ""),
                salary_range=tuple(salary_range),
                required_skills=collected_info.get("required_skills", []),
                experience_required=int(collected_info.get("experience_required", 0)),
                industry=collected_info.get("target_industry", ""),
                location=collected_info.get("location_preference", "")
            )
            
            return {"context": context, "job": job}
        
        elif decision_type == DecisionType.RELATIONSHIP:
            from backend.vertical.relationship.relationship_decision_engine import (
                RelationshipDecisionContext, Person, RelationshipType
            )
            
            # 构建人物列表
            key_people = []
            people_data = collected_info.get("key_people", [])
            
            for person_data in people_data:
                if isinstance(person_data, dict):
                    rel_type_str = person_data.get("relationship_type", "friend")
                    rel_type = RelationshipType[rel_type_str.upper()] if hasattr(RelationshipType, rel_type_str.upper()) else RelationshipType.FRIEND
                    
                    person = Person(
                        name=person_data.get("name", ""),
                        relationship_type=rel_type,
                        influence_weight=float(person_data.get("influence_weight", 0.5)),
                        emotional_closeness=float(person_data.get("emotional_closeness", 0.5)),
                        support_level=float(person_data.get("support_level", 0)),
                        key_concerns=person_data.get("key_concerns", [])
                    )
                    key_people.append(person)
            
            context = RelationshipDecisionContext(
                decision_topic=collected_info.get("decision_topic", ""),
                key_people=key_people,
                current_conflicts=collected_info.get("current_conflicts", []),
                relationship_goals=collected_info.get("relationship_goals", []),
                communication_history=collected_info.get("communication_history", {})
            )
            
            return {"context": context}
        
        elif decision_type == DecisionType.EDUCATION:
            from backend.vertical.education.education_decision_engine import (
                EducationDecisionContext, School
            )
            
            context = EducationDecisionContext(
                current_score=int(collected_info.get("current_score", 0)),
                target_major=collected_info.get("major"),
                location_preference=collected_info.get("location_preference"),
                budget_limit=float(collected_info.get("budget_limit", 0)),
                career_goal=collected_info.get("career_goal"),
                study_time_available=int(collected_info.get("study_time_available", 0)),
                family_support=float(collected_info.get("family_support", 0.5))
            )
            
            school = School(
                name=collected_info.get("school_name", ""),
                ranking=int(collected_info.get("ranking", 100)),
                location=collected_info.get("location_preference", ""),
                major=collected_info.get("major", ""),
                tuition=float(collected_info.get("tuition", 0)),
                admission_score=int(collected_info.get("admission_score", 0)),
                admission_rate=float(collected_info.get("admission_rate", 0.3)),
                employment_rate=float(collected_info.get("employment_rate", 0.85)),
                average_salary=float(collected_info.get("average_salary", 15)),
                program_duration=int(collected_info.get("program_duration", 4))
            )
            
            return {"context": context, "school": school}
        
        else:  # GENERAL
            return {"collected_info": collected_info}


# 全局实例
integrated_engine = IntegratedDecisionEngine()
