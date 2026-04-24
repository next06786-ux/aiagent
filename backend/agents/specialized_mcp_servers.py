"""
专业化MCP Servers - 为三个Agent提供独特的工具

每个Agent都有自己专属的MCP Server和工具集：
1. RelationshipMCPServer - 人际关系分析工具
2. EducationMCPServer - 教育规划工具
3. CareerMCPServer - 职业发展工具
"""

from backend.agents.mcp_integration import MCPServer, MCPTool
from typing import List, Dict, Any
import json
from datetime import datetime, timedelta



# ==================== 1. RelationshipMCPServer ====================

class RelationshipMCPServer(MCPServer):
    """
    人际关系分析MCP Server
    
    提供工具：
    1. analyze_communication_pattern - 分析沟通模式
    2. assess_relationship_health - 评估关系健康度
    3. generate_conflict_resolution - 生成冲突解决方案
    4. calculate_social_compatibility - 计算社交兼容性
    5. suggest_conversation_topics - 推荐对话话题
    """
    
    def __init__(self):
        super().__init__(
            server_id="relationship_tools",
            name="Relationship Analysis Server",
            description="提供人际关系分析和改善工具"
        )
    
    async def list_tools(self) -> List[MCPTool]:
        return [
            MCPTool(
                name="analyze_communication_pattern",
                description="分析两人之间的沟通模式，识别沟通障碍。输入：关系描述、最近互动情况",
                parameters={
                    "type": "object",
                    "properties": {
                        "relationship_type": {
                            "type": "string",
                            "description": "关系类型：朋友/同事/家人/恋人"
                        },
                        "recent_interactions": {
                            "type": "string",
                            "description": "最近的互动情况描述"
                        },
                        "issues": {
                            "type": "string",
                            "description": "遇到的问题"
                        }
                    },
                    "required": ["relationship_type", "recent_interactions"]
                },
                server_id=self.server_id,
                requires_approval=False
            ),
            MCPTool(
                name="assess_relationship_health",
                description="评估关系健康度（0-100分）。输入：关系描述、互动频率、满意度",
                parameters={
                    "type": "object",
                    "properties": {
                        "relationship_type": {"type": "string"},
                        "interaction_frequency": {
                            "type": "string",
                            "description": "互动频率：每天/每周/每月/很少"
                        },
                        "satisfaction_level": {
                            "type": "number",
                            "description": "满意度（1-10）"
                        },
                        "conflict_frequency": {
                            "type": "string",
                            "description": "冲突频率：经常/偶尔/很少/从不"
                        }
                    },
                    "required": ["relationship_type", "satisfaction_level"]
                },
                server_id=self.server_id,
                requires_approval=False
            ),
            MCPTool(
                name="generate_conflict_resolution",
                description="生成冲突解决方案。输入：冲突类型、双方立场",
                parameters={
                    "type": "object",
                    "properties": {
                        "conflict_type": {
                            "type": "string",
                            "description": "冲突类型：价值观/利益/误解/情感"
                        },
                        "your_position": {"type": "string", "description": "你的立场"},
                        "other_position": {"type": "string", "description": "对方立场"}
                    },
                    "required": ["conflict_type"]
                },
                server_id=self.server_id,
                requires_approval=False
            ),
            MCPTool(
                name="calculate_social_compatibility",
                description="计算社交兼容性得分。输入：性格特征、兴趣爱好、价值观",
                parameters={
                    "type": "object",
                    "properties": {
                        "your_traits": {"type": "string", "description": "你的性格特征"},
                        "other_traits": {"type": "string", "description": "对方性格特征"},
                        "shared_interests": {"type": "string", "description": "共同兴趣"}
                    },
                    "required": ["your_traits", "other_traits"]
                },
                server_id=self.server_id,
                requires_approval=False
            ),
            MCPTool(
                name="suggest_conversation_topics",
                description="推荐对话话题。输入：关系类型、对方兴趣、场景",
                parameters={
                    "type": "object",
                    "properties": {
                        "relationship_type": {"type": "string"},
                        "interests": {"type": "string", "description": "对方兴趣"},
                        "context": {"type": "string", "description": "对话场景"}
                    },
                    "required": ["relationship_type"]
                },
                server_id=self.server_id,
                requires_approval=False
            )
        ]

    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """执行人际关系分析工具"""
        
        if tool_name == "analyze_communication_pattern":
            relationship_type = parameters.get("relationship_type", "朋友")
            recent_interactions = parameters.get("recent_interactions", "")
            issues = parameters.get("issues", "")
            
            # 分析沟通模式
            patterns = {
                "朋友": ["倾听不足", "表达不清", "频率不够"],
                "同事": ["过于正式", "缺乏信任", "沟通效率低"],
                "家人": ["情绪化", "缺乏边界", "期望不一致"],
                "恋人": ["需求未表达", "情感忽视", "沟通时机不当"]
            }
            
            identified_patterns = patterns.get(relationship_type, ["需要更多信息"])
            
            return {
                "success": True,
                "relationship_type": relationship_type,
                "identified_patterns": identified_patterns,
                "recommendations": [
                    "使用'我感受到...'的表达方式",
                    "设定固定的沟通时间",
                    "练习积极倾听技巧"
                ],
                "communication_score": 65,
                "improvement_areas": ["情感表达", "倾听技巧", "冲突处理"]
            }
        
        elif tool_name == "assess_relationship_health":
            relationship_type = parameters.get("relationship_type", "朋友")
            satisfaction = parameters.get("satisfaction_level", 5)
            interaction_freq = parameters.get("interaction_frequency", "每周")
            conflict_freq = parameters.get("conflict_frequency", "偶尔")
            
            # 计算健康度得分
            base_score = satisfaction * 10
            
            freq_bonus = {
                "每天": 10, "每周": 5, "每月": 0, "很少": -10
            }.get(interaction_freq, 0)
            
            conflict_penalty = {
                "从不": 10, "很少": 5, "偶尔": 0, "经常": -15
            }.get(conflict_freq, 0)
            
            health_score = max(0, min(100, base_score + freq_bonus + conflict_penalty))
            
            # 评级
            if health_score >= 80:
                rating = "优秀"
                status = "关系非常健康"
            elif health_score >= 60:
                rating = "良好"
                status = "关系基本健康，有改善空间"
            elif health_score >= 40:
                rating = "一般"
                status = "关系需要关注和改善"
            else:
                rating = "较差"
                status = "关系存在严重问题"
            
            return {
                "success": True,
                "health_score": health_score,
                "rating": rating,
                "status": status,
                "strengths": ["互相尊重", "有共同话题"],
                "weaknesses": ["沟通频率不足", "情感表达欠缺"],
                "action_items": [
                    "增加互动频率",
                    "深入情感交流",
                    "共同参与活动"
                ]
            }
        
        elif tool_name == "generate_conflict_resolution":
            conflict_type = parameters.get("conflict_type", "误解")
            your_position = parameters.get("your_position", "")
            other_position = parameters.get("other_position", "")
            
            strategies = {
                "价值观": {
                    "approach": "尊重差异，寻找共同点",
                    "steps": [
                        "承认双方价值观的合理性",
                        "寻找核心共同价值",
                        "在行动层面寻求妥协"
                    ]
                },
                "利益": {
                    "approach": "双赢思维，创造性解决",
                    "steps": [
                        "明确双方真实需求",
                        "寻找利益交集",
                        "探索创新解决方案"
                    ]
                },
                "误解": {
                    "approach": "澄清事实，重建信任",
                    "steps": [
                        "坦诚沟通，澄清误解",
                        "表达真实意图",
                        "重建信任基础"
                    ]
                },
                "情感": {
                    "approach": "情感共鸣，修复关系",
                    "steps": [
                        "表达和倾听情感",
                        "承认对方感受",
                        "共同寻找解决方案"
                    ]
                }
            }
            
            strategy = strategies.get(conflict_type, strategies["误解"])
            
            return {
                "success": True,
                "conflict_type": conflict_type,
                "resolution_approach": strategy["approach"],
                "step_by_step_guide": strategy["steps"],
                "communication_script": f"我理解你的{conflict_type}，让我们一起找到解决方案...",
                "expected_outcome": "双方达成理解和共识",
                "follow_up_actions": ["定期检查", "持续沟通", "调整策略"]
            }
        
        elif tool_name == "calculate_social_compatibility":
            your_traits = parameters.get("your_traits", "")
            other_traits = parameters.get("other_traits", "")
            shared_interests = parameters.get("shared_interests", "")
            
            # 简化的兼容性计算
            compatibility_score = 70  # 基础分
            
            if shared_interests:
                compatibility_score += 15
            
            if "内向" in your_traits and "内向" in other_traits:
                compatibility_score += 10
            elif "外向" in your_traits and "外向" in other_traits:
                compatibility_score += 10
            
            return {
                "success": True,
                "compatibility_score": min(100, compatibility_score),
                "compatibility_level": "高" if compatibility_score >= 80 else "中" if compatibility_score >= 60 else "一般",
                "matching_traits": ["都重视沟通", "价值观相似"],
                "complementary_traits": ["一个外向一个内向，互补性强"],
                "potential_challenges": ["需要更多共同兴趣", "沟通方式需要磨合"],
                "relationship_advice": "你们有很好的兼容性基础，建议多培养共同兴趣"
            }
        
        elif tool_name == "suggest_conversation_topics":
            relationship_type = parameters.get("relationship_type", "朋友")
            interests = parameters.get("interests", "")
            context = parameters.get("context", "日常")
            
            topic_suggestions = {
                "朋友": [
                    "最近看的电影/剧集",
                    "共同的兴趣爱好",
                    "未来的计划和梦想",
                    "有趣的生活经历"
                ],
                "同事": [
                    "工作项目进展",
                    "行业趋势和见解",
                    "职业发展规划",
                    "工作之外的兴趣"
                ],
                "家人": [
                    "家庭近况和关心",
                    "童年回忆",
                    "未来家庭计划",
                    "健康和生活方式"
                ],
                "恋人": [
                    "彼此的感受和需求",
                    "共同的未来规划",
                    "浪漫的回忆",
                    "深层的价值观"
                ]
            }
            
            topics = topic_suggestions.get(relationship_type, topic_suggestions["朋友"])
            
            return {
                "success": True,
                "suggested_topics": topics,
                "conversation_starters": [
                    f"最近你对{interests}有什么新的想法吗？",
                    "我一直想和你聊聊...",
                    "你觉得...怎么样？"
                ],
                "tips": [
                    "保持开放和好奇的态度",
                    "多问开放式问题",
                    "分享自己的真实感受"
                ]
            }
        
        else:
            raise ValueError(f"未知工具: {tool_name}")
    
    async def list_resources(self):
        return []
    
    async def list_prompts(self):
        return []
    
    async def read_resource(self, uri: str):
        return None



# ==================== 2. EducationMCPServer ====================

class EducationMCPServer(MCPServer):
    """
    教育规划MCP Server
    
    提供工具：
    1. calculate_gpa_requirements - 计算目标院校GPA要求
    2. analyze_major_prospects - 分析专业前景
    3. generate_study_schedule - 生成学习计划
    4. assess_exam_readiness - 评估考试准备度
    5. recommend_universities - 推荐院校
    """
    
    def __init__(self):
        super().__init__(
            server_id="education_tools",
            name="Education Planning Server",
            description="提供教育规划和升学指导工具"
        )
    
    async def list_tools(self) -> List[MCPTool]:
        return [
            MCPTool(
                name="calculate_gpa_requirements",
                description="计算目标院校的GPA要求和录取概率。输入：目标院校、专业、当前GPA",
                parameters={
                    "type": "object",
                    "properties": {
                        "target_university": {"type": "string", "description": "目标院校"},
                        "major": {"type": "string", "description": "目标专业"},
                        "current_gpa": {"type": "number", "description": "当前GPA（0-4.0）"},
                        "additional_scores": {"type": "string", "description": "其他成绩（如托福、GRE）"}
                    },
                    "required": ["target_university", "current_gpa"]
                },
                server_id=self.server_id,
                requires_approval=False
            ),
            MCPTool(
                name="analyze_major_prospects",
                description="分析专业就业前景和发展趋势。输入：专业名称、关注维度",
                parameters={
                    "type": "object",
                    "properties": {
                        "major_name": {"type": "string", "description": "专业名称"},
                        "focus_areas": {
                            "type": "string",
                            "description": "关注维度：就业率/薪资/发展前景/学习难度"
                        }
                    },
                    "required": ["major_name"]
                },
                server_id=self.server_id,
                requires_approval=False
            ),
            MCPTool(
                name="generate_study_schedule",
                description="生成个性化学习计划。输入：目标、时间范围、当前水平",
                parameters={
                    "type": "object",
                    "properties": {
                        "goal": {"type": "string", "description": "学习目标"},
                        "timeframe": {"type": "string", "description": "时间范围（如3个月、半年）"},
                        "current_level": {"type": "string", "description": "当前水平"},
                        "daily_hours": {"type": "number", "description": "每天可用学习时间"}
                    },
                    "required": ["goal", "timeframe"]
                },
                server_id=self.server_id,
                requires_approval=False
            ),
            MCPTool(
                name="assess_exam_readiness",
                description="评估考试准备度。输入：考试类型、准备时间、模拟成绩",
                parameters={
                    "type": "object",
                    "properties": {
                        "exam_type": {"type": "string", "description": "考试类型：考研/托福/GRE/雅思"},
                        "preparation_days": {"type": "number", "description": "已准备天数"},
                        "mock_score": {"type": "number", "description": "模拟考试分数"},
                        "target_score": {"type": "number", "description": "目标分数"}
                    },
                    "required": ["exam_type", "preparation_days"]
                },
                server_id=self.server_id,
                requires_approval=False
            ),
            MCPTool(
                name="recommend_universities",
                description="推荐适合的院校。输入：GPA、专业方向、地区偏好",
                parameters={
                    "type": "object",
                    "properties": {
                        "gpa": {"type": "number"},
                        "major_direction": {"type": "string"},
                        "region_preference": {"type": "string", "description": "地区偏好"},
                        "budget": {"type": "string", "description": "预算范围"}
                    },
                    "required": ["gpa", "major_direction"]
                },
                server_id=self.server_id,
                requires_approval=False
            )
        ]

    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """执行教育规划工具"""
        
        if tool_name == "calculate_gpa_requirements":
            target_university = parameters.get("target_university", "")
            major = parameters.get("major", "计算机科学")
            current_gpa = parameters.get("current_gpa", 3.0)
            
            # 模拟不同院校的GPA要求
            university_requirements = {
                "清华大学": {"min_gpa": 3.7, "competitive_gpa": 3.9},
                "北京大学": {"min_gpa": 3.7, "competitive_gpa": 3.9},
                "复旦大学": {"min_gpa": 3.5, "competitive_gpa": 3.8},
                "上海交通大学": {"min_gpa": 3.5, "competitive_gpa": 3.8},
                "浙江大学": {"min_gpa": 3.4, "competitive_gpa": 3.7}
            }
            
            requirements = university_requirements.get(
                target_university,
                {"min_gpa": 3.0, "competitive_gpa": 3.5}
            )
            
            # 计算录取概率
            if current_gpa >= requirements["competitive_gpa"]:
                probability = "高（80-90%）"
                status = "优秀"
            elif current_gpa >= requirements["min_gpa"]:
                probability = "中等（50-70%）"
                status = "达标"
            else:
                probability = "较低（20-40%）"
                status = "需要提升"
            
            gap = max(0, requirements["competitive_gpa"] - current_gpa)
            
            return {
                "success": True,
                "target_university": target_university,
                "major": major,
                "current_gpa": current_gpa,
                "min_gpa_required": requirements["min_gpa"],
                "competitive_gpa": requirements["competitive_gpa"],
                "admission_probability": probability,
                "status": status,
                "gpa_gap": round(gap, 2),
                "recommendations": [
                    f"需要提升GPA {gap:.2f}分以达到竞争力水平" if gap > 0 else "GPA已达标，保持优势",
                    "增加科研项目经历",
                    "准备高质量推荐信",
                    "提升标准化考试成绩"
                ]
            }
        
        elif tool_name == "analyze_major_prospects":
            major_name = parameters.get("major_name", "")
            focus_areas = parameters.get("focus_areas", "就业率")
            
            # 专业数据库（示例）
            major_data = {
                "计算机科学": {
                    "employment_rate": 95,
                    "average_salary": "15-25万",
                    "growth_trend": "持续增长",
                    "difficulty": "中等偏高",
                    "hot_directions": ["人工智能", "大数据", "云计算"]
                },
                "金融学": {
                    "employment_rate": 88,
                    "average_salary": "12-20万",
                    "growth_trend": "稳定",
                    "difficulty": "中等",
                    "hot_directions": ["金融科技", "量化投资", "风险管理"]
                },
                "电子工程": {
                    "employment_rate": 92,
                    "average_salary": "12-18万",
                    "growth_trend": "稳定增长",
                    "difficulty": "高",
                    "hot_directions": ["芯片设计", "物联网", "5G通信"]
                }
            }
            
            data = major_data.get(major_name, {
                "employment_rate": 85,
                "average_salary": "8-15万",
                "growth_trend": "稳定",
                "difficulty": "中等",
                "hot_directions": ["待补充"]
            })
            
            return {
                "success": True,
                "major_name": major_name,
                "employment_rate": f"{data['employment_rate']}%",
                "average_salary": data["average_salary"],
                "growth_trend": data["growth_trend"],
                "learning_difficulty": data["difficulty"],
                "hot_directions": data["hot_directions"],
                "market_demand": "高" if data["employment_rate"] > 90 else "中等",
                "career_paths": [
                    "互联网公司技术岗",
                    "科研院所研究员",
                    "创业公司核心成员"
                ],
                "skill_requirements": [
                    "扎实的专业基础",
                    "实践项目经验",
                    "持续学习能力"
                ]
            }
        
        elif tool_name == "generate_study_schedule":
            goal = parameters.get("goal", "")
            timeframe = parameters.get("timeframe", "3个月")
            current_level = parameters.get("current_level", "初级")
            daily_hours = parameters.get("daily_hours", 4)
            
            # 生成学习计划
            phases = {
                "3个月": [
                    {"phase": "第1月", "focus": "基础知识", "hours_per_week": daily_hours * 7},
                    {"phase": "第2月", "focus": "深入学习", "hours_per_week": daily_hours * 7},
                    {"phase": "第3月", "focus": "实战练习", "hours_per_week": daily_hours * 7}
                ],
                "半年": [
                    {"phase": "第1-2月", "focus": "基础夯实", "hours_per_week": daily_hours * 7},
                    {"phase": "第3-4月", "focus": "进阶提升", "hours_per_week": daily_hours * 7},
                    {"phase": "第5-6月", "focus": "综合应用", "hours_per_week": daily_hours * 7}
                ]
            }
            
            schedule = phases.get(timeframe, phases["3个月"])
            
            return {
                "success": True,
                "goal": goal,
                "timeframe": timeframe,
                "total_hours": daily_hours * 7 * 12,  # 假设3个月
                "study_phases": schedule,
                "daily_schedule": {
                    "morning": "理论学习（2小时）",
                    "afternoon": "实践练习（1.5小时）",
                    "evening": "复习总结（0.5小时）"
                },
                "weekly_milestones": [
                    "完成基础章节学习",
                    "完成3个练习项目",
                    "通过阶段测试"
                ],
                "resources": [
                    "推荐教材：《XXX》",
                    "在线课程：Coursera/edX",
                    "练习平台：LeetCode/Kaggle"
                ]
            }
        
        elif tool_name == "assess_exam_readiness":
            exam_type = parameters.get("exam_type", "考研")
            preparation_days = parameters.get("preparation_days", 90)
            mock_score = parameters.get("mock_score", 0)
            target_score = parameters.get("target_score", 0)
            
            # 评估准备度
            if mock_score and target_score:
                score_gap = target_score - mock_score
                progress = (mock_score / target_score) * 100 if target_score > 0 else 0
            else:
                score_gap = 0
                progress = 50
            
            # 根据准备时间评估
            if preparation_days >= 180:
                time_status = "充足"
                readiness = "良好"
            elif preparation_days >= 90:
                time_status = "适中"
                readiness = "一般"
            else:
                time_status = "紧张"
                readiness = "需要加强"
            
            return {
                "success": True,
                "exam_type": exam_type,
                "preparation_days": preparation_days,
                "time_status": time_status,
                "current_progress": f"{progress:.1f}%",
                "readiness_level": readiness,
                "score_gap": score_gap if score_gap > 0 else 0,
                "strengths": ["基础扎实", "学习态度认真"],
                "weaknesses": ["做题速度慢", "知识点遗漏"],
                "improvement_plan": [
                    "每天刷题50道，提升速度",
                    "系统复习薄弱章节",
                    "每周模拟考试1次",
                    "调整作息，保证状态"
                ],
                "estimated_score": mock_score + (score_gap * 0.7) if mock_score else 0
            }
        
        elif tool_name == "recommend_universities":
            gpa = parameters.get("gpa", 3.0)
            major_direction = parameters.get("major_direction", "")
            region_preference = parameters.get("region_preference", "不限")
            budget = parameters.get("budget", "中等")
            
            # 根据GPA推荐院校
            if gpa >= 3.7:
                tier = "顶尖院校"
                universities = [
                    {"name": "清华大学", "match": 85, "reason": "GPA优秀，专业匹配"},
                    {"name": "北京大学", "match": 85, "reason": "综合实力强"},
                    {"name": "复旦大学", "match": 80, "reason": "地理位置好"}
                ]
            elif gpa >= 3.3:
                tier = "重点院校"
                universities = [
                    {"name": "浙江大学", "match": 80, "reason": "专业实力强"},
                    {"name": "上海交通大学", "match": 78, "reason": "就业前景好"},
                    {"name": "南京大学", "match": 75, "reason": "学术氛围好"}
                ]
            else:
                tier = "普通院校"
                universities = [
                    {"name": "华东师范大学", "match": 70, "reason": "录取概率高"},
                    {"name": "苏州大学", "match": 68, "reason": "性价比高"},
                    {"name": "南京师范大学", "match": 65, "reason": "专业不错"}
                ]
            
            return {
                "success": True,
                "gpa": gpa,
                "tier": tier,
                "recommended_universities": universities,
                "application_strategy": {
                    "reach_schools": 2,
                    "target_schools": 3,
                    "safety_schools": 2
                },
                "tips": [
                    "申请2所冲刺院校",
                    "申请3所目标院校",
                    "申请2所保底院校",
                    "准备充分的申请材料"
                ]
            }
        
        else:
            raise ValueError(f"未知工具: {tool_name}")
    
    async def list_resources(self):
        return []
    
    async def list_prompts(self):
        return []
    
    async def read_resource(self, uri: str):
        return None



# ==================== 职业发展 MCP Server ====================

class CareerMCPServer(MCPServer):
    """
    职业发展专业工具 MCP Server
    
    提供工具：
    1. assess_career_competitiveness - 评估职业竞争力
    2. query_job_market - 查询职位市场信息
    3. generate_skill_roadmap - 生成技能学习路线图
    4. analyze_career_transition - 分析职业转型可行性
    5. optimize_resume - 简历优化建议
    """
    
    def __init__(self):
        super().__init__(
            server_id="career_tools",
            name="Career Development Server",
            description="提供职业发展规划、市场分析、技能提升等专业工具"
        )
    
    async def list_tools(self) -> List[MCPTool]:
        return [
            MCPTool(
                name="assess_career_competitiveness",
                description="评估用户的职业竞争力，分析技能优势和待提升领域。输入：技能清单、工作经验、教育背景",
                parameters={
                    "type": "object",
                    "properties": {
                        "skills": {
                            "type": "string",
                            "description": "技能清单（如：Python, 项目管理, 数据分析）"
                        },
                        "experience": {
                            "type": "string",
                            "description": "工作经验描述"
                        },
                        "education": {
                            "type": "string",
                            "description": "教育背景"
                        },
                        "target_position": {
                            "type": "string",
                            "description": "目标职位（可选）"
                        }
                    },
                    "required": ["skills", "experience"]
                },
                server_id=self.server_id,
                requires_approval=False
            ),
            MCPTool(
                name="query_job_market",
                description="查询职位市场信息，包括薪资范围、需求趋势、热门公司。输入：职位名称、城市",
                parameters={
                    "type": "object",
                    "properties": {
                        "position": {
                            "type": "string",
                            "description": "职位名称（如：产品经理、Java开发）"
                        },
                        "city": {
                            "type": "string",
                            "description": "城市（如：北京、上海、深圳）"
                        },
                        "experience_level": {
                            "type": "string",
                            "description": "经验水平（应届/1-3年/3-5年/5年以上）",
                            "default": "不限"
                        }
                    },
                    "required": ["position", "city"]
                },
                server_id=self.server_id,
                requires_approval=False
            ),
            MCPTool(
                name="generate_skill_roadmap",
                description="生成技能学习路线图，从当前技能到目标职位的提升路径。输入：当前技能、目标职位",
                parameters={
                    "type": "object",
                    "properties": {
                        "current_skills": {
                            "type": "string",
                            "description": "当前技能水平"
                        },
                        "target_position": {
                            "type": "string",
                            "description": "目标职位"
                        },
                        "timeline": {
                            "type": "string",
                            "description": "学习时间线（如：3个月、6个月、1年）",
                            "default": "6个月"
                        }
                    },
                    "required": ["current_skills", "target_position"]
                },
                server_id=self.server_id,
                requires_approval=False
            ),
            MCPTool(
                name="analyze_career_transition",
                description="分析职业转型的可行性和风险，提供过渡策略。输入：当前职业、目标职业",
                parameters={
                    "type": "object",
                    "properties": {
                        "current_career": {
                            "type": "string",
                            "description": "当前职业/行业"
                        },
                        "target_career": {
                            "type": "string",
                            "description": "目标职业/行业"
                        },
                        "reason": {
                            "type": "string",
                            "description": "转型原因（可选）"
                        }
                    },
                    "required": ["current_career", "target_career"]
                },
                server_id=self.server_id,
                requires_approval=False
            ),
            MCPTool(
                name="optimize_resume",
                description="提供简历优化建议，针对目标职位优化内容和结构。输入：简历内容、目标职位",
                parameters={
                    "type": "object",
                    "properties": {
                        "resume_content": {
                            "type": "string",
                            "description": "简历主要内容（工作经历、项目经验）"
                        },
                        "target_position": {
                            "type": "string",
                            "description": "目标职位"
                        }
                    },
                    "required": ["resume_content", "target_position"]
                },
                server_id=self.server_id,
                requires_approval=False
            )
        ]
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """执行职业发展工具"""
        
        if tool_name == "assess_career_competitiveness":
            skills = parameters.get("skills", "")
            experience = parameters.get("experience", "")
            education = parameters.get("education", "")
            target = parameters.get("target_position", "")
            
            # 模拟竞争力评估
            return {
                "overall_score": 75,
                "strengths": [
                    "技术深度：具备扎实的专业技能",
                    "项目经验：有实际项目落地经验",
                    "学习能力：教育背景良好"
                ],
                "weaknesses": [
                    "跨领域能力：建议拓展相关领域知识",
                    "软技能：可加强沟通和团队协作能力"
                ],
                "improvement_suggestions": [
                    "深化核心技术栈，成为领域专家",
                    "参与开源项目，提升影响力",
                    "培养跨职能协作经验",
                    "建立个人技术品牌（博客/演讲）"
                ],
                "market_position": "中等偏上，具备较强竞争力"
            }
        
        elif tool_name == "query_job_market":
            position = parameters.get("position", "")
            city = parameters.get("city", "")
            level = parameters.get("experience_level", "不限")
            
            # 模拟市场数据
            return {
                "position": position,
                "city": city,
                "salary_range": {
                    "min": 15000,
                    "max": 35000,
                    "median": 25000,
                    "currency": "CNY/月"
                },
                "demand_trend": "需求旺盛，同比增长15%",
                "hot_companies": [
                    "字节跳动",
                    "阿里巴巴",
                    "腾讯",
                    "美团",
                    "快手"
                ],
                "required_skills": [
                    "专业技能（必备）",
                    "项目经验（2年以上）",
                    "团队协作能力",
                    "学习能力"
                ],
                "career_prospects": "发展前景良好，晋升路径清晰",
                "tips": [
                    f"{city}地区{position}岗位竞争激烈",
                    "建议突出项目成果和数据指标",
                    "关注行业头部公司和成长型企业"
                ]
            }
        
        elif tool_name == "generate_skill_roadmap":
            current = parameters.get("current_skills", "")
            target = parameters.get("target_position", "")
            timeline = parameters.get("timeline", "6个月")
            
            # 模拟技能路线图
            return {
                "timeline": timeline,
                "phases": [
                    {
                        "phase": "第1阶段：基础巩固（1-2个月）",
                        "goals": [
                            "补齐核心技能短板",
                            "建立系统化知识体系"
                        ],
                        "actions": [
                            "完成相关技术课程学习",
                            "阅读经典技术书籍",
                            "练习基础算法和数据结构"
                        ]
                    },
                    {
                        "phase": "第2阶段：项目实战（2-3个月）",
                        "goals": [
                            "积累实际项目经验",
                            "形成可展示的作品集"
                        ],
                        "actions": [
                            "参与开源项目贡献",
                            "开发个人项目",
                            "模拟真实业务场景"
                        ]
                    },
                    {
                        "phase": "第3阶段：体系构建（1-2个月）",
                        "goals": [
                            "建立完整技能体系",
                            "准备求职材料"
                        ],
                        "actions": [
                            "总结项目经验和技术博客",
                            "优化简历和作品集",
                            "准备面试和技术分享"
                        ]
                    }
                ],
                "resources": [
                    "在线课程：Coursera, Udemy",
                    "技术社区：GitHub, Stack Overflow",
                    "学习平台：LeetCode, 掘金"
                ],
                "milestones": [
                    "2个月：完成核心技能学习",
                    "4个月：完成2-3个项目",
                    "6个月：达到目标职位要求"
                ]
            }
        
        elif tool_name == "analyze_career_transition":
            current = parameters.get("current_career", "")
            target = parameters.get("target_career", "")
            reason = parameters.get("reason", "")
            
            # 模拟转型分析
            return {
                "feasibility": "中等可行",
                "difficulty_level": "中等",
                "transferable_skills": [
                    "项目管理经验",
                    "沟通协调能力",
                    "行业理解"
                ],
                "skill_gaps": [
                    "目标领域专业技能",
                    "相关工具和技术栈",
                    "行业特定知识"
                ],
                "transition_strategy": {
                    "phase1": "技能准备（3-6个月）：学习目标领域核心技能",
                    "phase2": "经验积累（6-12个月）：通过项目/实习积累经验",
                    "phase3": "正式转型（12个月后）：寻找目标职位机会"
                },
                "risks": [
                    "薪资可能短期下降",
                    "需要重新建立职业网络",
                    "学习曲线较陡峭"
                ],
                "opportunities": [
                    "进入新兴高增长领域",
                    "拓展职业发展空间",
                    "实现个人兴趣和价值"
                ],
                "recommendations": [
                    "先通过副业或兼职测试适配度",
                    "建立目标领域的人脉网络",
                    "保持财务缓冲应对过渡期",
                    "制定详细的学习和转型计划"
                ]
            }
        
        elif tool_name == "optimize_resume":
            content = parameters.get("resume_content", "")
            target = parameters.get("target_position", "")
            
            # 模拟简历优化建议
            return {
                "overall_assessment": "简历内容较完整，但需要针对目标职位优化",
                "structure_suggestions": [
                    "突出与目标职位最相关的经验",
                    "使用STAR法则描述项目成果",
                    "量化工作成果（数据、指标）"
                ],
                "content_optimization": {
                    "strengths_to_highlight": [
                        "相关项目经验",
                        "技术栈匹配度",
                        "团队协作成果"
                    ],
                    "areas_to_improve": [
                        "增加具体的业务影响数据",
                        "补充技术深度的体现",
                        "添加行业认可的成就"
                    ]
                },
                "keyword_suggestions": [
                    f"{target}相关的核心技能关键词",
                    "行业热门技术栈",
                    "项目管理方法论"
                ],
                "formatting_tips": [
                    "保持简洁，控制在2页以内",
                    "使用清晰的层次结构",
                    "突出重点信息（加粗、列表）",
                    "确保无错别字和格式问题"
                ],
                "action_items": [
                    "重写工作经历，突出量化成果",
                    "调整技能部分，匹配JD要求",
                    "添加项目亮点和技术难点",
                    "请行业人士review并提供反馈"
                ]
            }
        
        else:
            raise ValueError(f"未知工具: {tool_name}")
    
    async def list_resources(self):
        return []
    
    async def list_prompts(self):
        return []
    
    async def read_resource(self, uri: str):
        return None


# ==================== 通用工具：联网搜索 MCP Server（阿里云OpenSearch）====================

class WebSearchMCPServer(MCPServer):
    """
    联网搜索 MCP Server（使用阿里云OpenSearch AI搜索）
    
    提供工具：
    1. web_search - 智能联网搜索
    """
    
    def __init__(self, api_key: str = None, host: str = None, workspace: str = None, service_id: str = None):
        super().__init__(
            server_id="web_search_tools",
            name="Web Search Server",
            description="提供阿里云OpenSearch AI联网搜索能力"
        )
        import os
        self.api_key = api_key or os.getenv("QWEN_SEARCH_API_KEY", "")
        self.host = host or os.getenv("QWEN_SEARCH_HOST", "")
        self.workspace = workspace or os.getenv("QWEN_SEARCH_WORKSPACE", "default")
        self.service_id = service_id or os.getenv("QWEN_SEARCH_SERVICE_ID", "ops-web-search-001")
    
    async def list_tools(self) -> List[MCPTool]:
        return [
            MCPTool(
                name="web_search",
                description="智能联网搜索最新信息。阿里云AI搜索会自动优化搜索词并返回高质量结果。适用于：查询最新资讯、行业动态、技术趋势、市场数据等。",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索问题或关键词"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "返回结果数量（1-10）",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                },
                server_id=self.server_id,
                requires_approval=False
            )
        ]
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """执行搜索工具"""
        import httpx
        
        if not self.api_key or not self.host:
            return {
                "success": False,
                "error": "未配置OpenSearch API Key或Host"
            }
        
        query = parameters.get("query", "")
        if not query:
            return {"success": False, "error": "搜索关键词不能为空"}
        
        # 构建请求URL
        url = f"{self.host}/v3/openapi/workspaces/{self.workspace}/web-search/{self.service_id}"
        
        # 构建请求体
        body = {
            "query": query,
            "query_rewrite": True,  # 启用LLM优化搜索词
            "top_k": min(parameters.get("top_k", 5), 10),
            "content_type": "snippet"  # 返回摘要
        }
        
        # 请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 发起请求
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(url, json=body, headers=headers)
                response.raise_for_status()
                data = response.json()
            
            # 检查响应
            if not data.get("success", True):
                return {
                    "success": False,
                    "error": data.get("message", "搜索失败")
                }
            
            # 提取搜索结果
            results = []
            result_data = data.get("result", {})
            search_results = result_data.get("search_result", [])  # 注意：是 search_result 不是 search_results
            
            for item in search_results:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),  # 注意：是 link 不是 url
                    "snippet": item.get("content", "")[:500],
                    "source": item.get("link", "").split("/")[2] if item.get("link") else "",
                    "publish_time": ""
                })
            
            # 生成摘要
            summary = self._generate_summary(results)
            
            return {
                "success": True,
                "query": query,
                "rewritten_query": result_data.get("rewritten_query", query),
                "total_results": len(results),
                "results": results,
                "summary": summary
            }
        
        except httpx.TimeoutException:
            return {"success": False, "error": "搜索超时，请稍后重试"}
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg = error_data.get("message", error_msg)
            except:
                pass
            return {"success": False, "error": error_msg}
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"搜索详细错误:\n{error_detail}")
            return {"success": False, "error": f"搜索出错: {str(e)}"}
    
    def _generate_summary(self, results: List[Dict]) -> str:
        """生成搜索结果摘要"""
        if not results:
            return "未找到相关结果"
        
        summary_parts = []
        for i, result in enumerate(results[:3], 1):
            title = result.get("title", "")
            snippet = result.get("snippet", "")[:150]
            summary_parts.append(f"{i}. {title}\n   {snippet}...")
        
        return "\n\n".join(summary_parts)
    
    async def list_resources(self):
        return []
    
    async def list_prompts(self):
        return []
    
    async def read_resource(self, uri: str):
        return None
