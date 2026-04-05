"""
教育知识图谱构建器 - 用于生成3D可视化的升学规划知识图谱

三层同心圆结构：
1. 学业层 - 当前GPA、排名、标化成绩
2. 目标学校层 - 冲刺/匹配/保底学校
3. 规划行动层 - 备考任务、申请策略

对接：
- 录取概率分析
- 教育ROI计算
- 申请策略优化
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import math
import random


@dataclass
class EducationUserProfile:
    """学生学业档案"""
    student_id: str
    gpa: float                        # 当前GPA (0-4.0)
    gpa_max: float = 4.0             # GPA满分
    ranking_percent: float = 0.2      # 年级排名百分比
    sat_act: float = 0.0            # SAT/ACT成绩
    gre_gmat: float = 0.0           # GRE/GMAT成绩
    toefl_ielts: float = 0.0        # 语言成绩
    research_experience: float = 0.5  # 科研经历
    publications: int = 0            # 发表论文数
    target_major: str = ""           # 目标专业
    target_level: str = "master"      # 目标学历：bachelor/master/phd


class EducationKnowledgeGraph:
    """教育升学知识图谱构建器"""

    def __init__(self):
        self.school_database = self._init_school_database()
        self.major_database = self._init_major_database()

    def _init_school_database(self) -> Dict[str, Dict]:
        """初始化学校数据库"""
        return {
            "清华大学": {
                "tier": "top", "tier_name": "顶尖",
                "tuition": 50000, "living": 20000,
                "avg_gpa": 3.85, "acceptance": 0.01,
                "avg_salary": 280000, "employment": 0.98,
                "location": "北京", "category": "理工"
            },
            "北京大学": {
                "tier": "top", "tier_name": "顶尖",
                "tuition": 50000, "living": 20000,
                "avg_gpa": 3.85, "acceptance": 0.01,
                "avg_salary": 270000, "employment": 0.98,
                "location": "北京", "category": "综合"
            },
            "MIT": {
                "tier": "top", "tier_name": "顶尖",
                "tuition": 58000, "living": 25000,
                "avg_gpa": 3.9, "acceptance": 0.04,
                "avg_salary": 380000, "employment": 0.96,
                "location": "Massachusetts", "category": "理工"
            },
            "Stanford": {
                "tier": "top", "tier_name": "顶尖",
                "tuition": 60000, "living": 26000,
                "avg_gpa": 3.88, "acceptance": 0.04,
                "avg_salary": 360000, "employment": 0.95,
                "location": "California", "category": "综合"
            },
            "复旦大学": {
                "tier": "elite", "tier_name": "精英",
                "tuition": 45000, "living": 18000,
                "avg_gpa": 3.6, "acceptance": 0.05,
                "avg_salary": 220000, "employment": 0.95,
                "location": "上海", "category": "综合"
            },
            "上海交通大学": {
                "tier": "elite", "tier_name": "精英",
                "tuition": 45000, "living": 18000,
                "avg_gpa": 3.55, "acceptance": 0.06,
                "avg_salary": 230000, "employment": 0.95,
                "location": "上海", "category": "理工"
            },
            "浙江大学": {
                "tier": "elite", "tier_name": "精英",
                "tuition": 42000, "living": 18000,
                "avg_gpa": 3.5, "acceptance": 0.07,
                "avg_salary": 210000, "employment": 0.95,
                "location": "杭州", "category": "综合"
            },
            "CMU": {
                "tier": "elite", "tier_name": "精英",
                "tuition": 60000, "living": 24000,
                "avg_gpa": 3.8, "acceptance": 0.07,
                "avg_salary": 350000, "employment": 0.97,
                "location": "Pennsylvania", "category": "理工"
            },
            "Berkeley": {
                "tier": "elite", "tier_name": "精英",
                "tuition": 58000, "living": 25000,
                "avg_gpa": 3.75, "acceptance": 0.08,
                "avg_salary": 330000, "employment": 0.96,
                "location": "California", "category": "综合"
            },
            "南京大学": {
                "tier": "good", "tier_name": "良好",
                "tuition": 40000, "living": 15000,
                "avg_gpa": 3.3, "acceptance": 0.15,
                "avg_salary": 180000, "employment": 0.92,
                "location": "南京", "category": "综合"
            },
            "武汉大学": {
                "tier": "good", "tier_name": "良好",
                "tuition": 38000, "living": 15000,
                "avg_gpa": 3.3, "acceptance": 0.15,
                "avg_salary": 175000, "employment": 0.92,
                "location": "武汉", "category": "综合"
            },
        }

    def _init_major_database(self) -> Dict[str, Dict]:
        """初始化专业数据库"""
        return {
            "计算机科学": {"category": "cs", "difficulty": 0.75, "demand": 0.95, "salary": 0.95, "growth": 0.90, "competition": 0.90},
            "人工智能": {"category": "cs", "difficulty": 0.85, "demand": 0.98, "salary": 0.98, "growth": 0.95, "competition": 0.95},
            "数据科学": {"category": "cs", "difficulty": 0.70, "demand": 0.92, "salary": 0.90, "growth": 0.88, "competition": 0.88},
            "金融工程": {"category": "business", "difficulty": 0.65, "demand": 0.80, "salary": 0.90, "growth": 0.60, "competition": 0.85},
            "经济学": {"category": "social", "difficulty": 0.60, "demand": 0.75, "salary": 0.80, "growth": 0.65, "competition": 0.75},
            "电子工程": {"category": "engineering", "difficulty": 0.72, "demand": 0.85, "salary": 0.88, "growth": 0.78, "competition": 0.82},
            "机械工程": {"category": "engineering", "difficulty": 0.70, "demand": 0.80, "salary": 0.82, "growth": 0.70, "competition": 0.75},
            "生物医学": {"category": "science", "difficulty": 0.80, "demand": 0.70, "salary": 0.75, "growth": 0.75, "competition": 0.80},
        }

    def build_education_graph(
        self,
        user_profile: EducationUserProfile,
        search_keyword: str = "",
        location: str = ""
    ) -> Dict[str, Any]:
        """
        构建教育升学知识图谱 - 清晰的三层同心圆结构
        """
        nodes = []
        edges = []

        center_id = "edu_center_" + user_profile.student_id
        nodes.append({
            "id": center_id, "label": "我", "type": "center", "layer": 0,
            "position": {"x": 0, "y": 0, "z": 0},
            "size": 18, "color": "#4A90E2",
            "metadata": {
                "gpa": user_profile.gpa,
                "gpa_ratio": user_profile.gpa / user_profile.gpa_max,
                "ranking": user_profile.ranking_percent,
                "sat": user_profile.sat_act,
                "research": user_profile.research_experience
            }
        })

        academic_nodes, academic_edges = self._build_academic_layer(user_profile, center_id)
        nodes.extend(academic_nodes)
        edges.extend(academic_edges)

        school_nodes, school_edges = self._build_school_layer(
            user_profile, center_id, search_keyword, location
        )
        nodes.extend(school_nodes)
        edges.extend(school_edges)

        action_nodes, action_edges = self._build_action_layer(
            user_profile, school_nodes, center_id
        )
        nodes.extend(action_nodes)
        edges.extend(action_edges)

        tier_counts = {"top": 0, "elite": 0, "good": 0}
        for s in school_nodes:
            tier = s.get("metadata", {}).get("tier", "")
            if tier in tier_counts:
                tier_counts[tier] += 1

        return {
            "nodes": nodes,
            "edges": edges,
            "layers": {
                "academic": [n["id"] for n in academic_nodes],
                "schools": [n["id"] for n in school_nodes],
                "actions": [n["id"] for n in action_nodes],
            },
            "metadata": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "user_direction": user_profile.target_major,
                "data_sources": {"education_kg": len(school_nodes)},
                "tier_distribution": tier_counts,
                "layer_info": {
                    "layer1": {"name": "学业层", "radius": 18, "count": len(academic_nodes)},
                    "layer2": {"name": "目标学校层", "radius": 38, "count": len(school_nodes)},
                    "layer3": {"name": "规划行动层", "radius": 58, "count": len(action_nodes)}
                }
            }
        }

    def _build_academic_layer(
        self,
        user_profile: EducationUserProfile,
        center_id: str
    ) -> tuple:
        nodes, edges = [], []

        gpa_ratio = user_profile.gpa / user_profile.gpa_max
        gpa_color = "#4CAF50" if gpa_ratio >= 0.85 else ("#FFC107" if gpa_ratio >= 0.70 else "#F44336")
        nodes.append({
            "id": "node_gpa",
            "label": "GPA %.1f/%.1f" % (user_profile.gpa, user_profile.gpa_max),
            "type": "academic", "layer": 1,
            "position": self._polar_pos(18, 0),
            "size": 10 + gpa_ratio * 8,
            "color": gpa_color,
            "metadata": {
                "value": user_profile.gpa,
                "max": user_profile.gpa_max,
                "ratio": round(gpa_ratio, 3),
                "ranking_percent": user_profile.ranking_percent
            }
        })
        edges.append({
            "source": center_id, "target": "node_gpa",
            "type": "academic_performance",
            "weight": gpa_ratio, "width": 1 + gpa_ratio * 3,
            "color": gpa_color
        })

        if user_profile.sat_act > 0:
            sat_ratio = min(1.0, user_profile.sat_act / 1600)
            sat_color = "#4CAF50" if sat_ratio >= 0.90 else ("#FFC107" if sat_ratio >= 0.75 else "#F44336")
            nodes.append({
                "id": "node_sat",
                "label": "SAT %d" % int(user_profile.sat_act),
                "type": "academic", "layer": 1,
                "position": self._polar_pos(18, math.pi * 2 / 3),
                "size": 10 + sat_ratio * 8,
                "color": sat_color,
                "metadata": {"value": user_profile.sat_act, "max": 1600, "ratio": round(sat_ratio, 3)}
            })
            edges.append({
                "source": center_id, "target": "node_sat",
                "type": "academic_performance",
                "weight": sat_ratio, "width": 1 + sat_ratio * 3,
                "color": sat_color
            })

        if user_profile.research_experience > 0.3:
            label = ("科研 x %d" % user_profile.publications) if user_profile.publications > 0 else "科研经历"
            nodes.append({
                "id": "node_research",
                "label": label,
                "type": "academic", "layer": 1,
                "position": self._polar_pos(18, math.pi * 4 / 3),
                "size": 8 + user_profile.research_experience * 8,
                "color": "#9575FF",
                "metadata": {
                    "experience_level": user_profile.research_experience,
                    "publications": user_profile.publications
                }
            })
            edges.append({
                "source": center_id, "target": "node_research",
                "type": "research_background",
                "weight": user_profile.research_experience,
                "width": 2,
                "color": "#9575FF"
            })

        if user_profile.ranking_percent < 0.3:
            ranking_label = "前%d%%" % int(user_profile.ranking_percent * 100)
            ranking_ratio = 1.0 - user_profile.ranking_percent
            nodes.append({
                "id": "node_ranking",
                "label": ranking_label,
                "type": "academic", "layer": 1,
                "position": self._polar_pos(18, math.pi * 5 / 3),
                "size": 8 + ranking_ratio * 8,
                "color": "#4FACFE",
                "metadata": {"ranking_percent": user_profile.ranking_percent}
            })
            edges.append({
                "source": center_id, "target": "node_ranking",
                "type": "academic_performance",
                "weight": ranking_ratio, "width": 1 + ranking_ratio * 3,
                "color": "#4FACFE"
            })

        return nodes, edges

    def _build_school_layer(
        self,
        user_profile: EducationUserProfile,
        center_id: str,
        search_keyword: str,
        location: str
    ) -> tuple:
        nodes, edges = [], []

        reach_schools = []
        match_schools = []
        safety_schools = []

        for school_name, school_info in self.school_database.items():
            if search_keyword and (search_keyword not in school_name and
               search_keyword not in school_info.get("category", "")):
                continue
            if location and location not in school_info.get("location", ""):
                continue

            gpa_ratio = user_profile.gpa / user_profile.gpa_max
            gpa_match = gpa_ratio / max(school_info["avg_gpa"] / 4.0, 0.01)
            prob = min(0.95, max(0.01, gpa_match * school_info["acceptance"] * 1.5))

            school_data = {"name": school_name, "info": school_info, "probability": prob}

            if prob >= 0.5:
                safety_schools.append(school_data)
            elif prob >= 0.2:
                match_schools.append(school_data)
            else:
                reach_schools.append(school_data)

        if not (reach_schools or match_schools or safety_schools):
            reach_schools = [{"name": "清华", "info": self.school_database.get("清华大学", {}), "probability": 0.05}]
            match_schools = [{"name": "复旦", "info": self.school_database.get("复旦大学", {}), "probability": 0.30}]
            safety_schools = [{"name": "南大", "info": self.school_database.get("南京大学", {}), "probability": 0.60}]

        def add_school_group(schools, color, base_angle, angle_range, tier, tier_name):
            n = len(schools)
            if n == 0:
                return
            tier_color = {"top": "#FF6B6B", "elite": "#4FACFE", "good": "#43E97B"}.get(tier, color)
            for i, s in enumerate(schools):
                angle = base_angle + (i / max(n - 1, 1)) * angle_range
                prob = s["probability"]
                size = 6 + prob * 12
                node_id = "school_" + s["name"]
                nodes.append({
                    "id": node_id,
                    "label": s["name"],
                    "type": "school", "layer": 2,
                    "position": self._polar_pos(38, angle),
                    "size": size,
                    "color": tier_color,
                    "metadata": {
                        "tier": tier,
                        "tier_name": tier_name,
                        "probability": round(prob, 3),
                        "tuition": s["info"].get("tuition", 0),
                        "avg_salary": s["info"].get("avg_salary", 0),
                        "acceptance": s["info"].get("acceptance", 0),
                        "location": s["info"].get("location", ""),
                        "category": s["info"].get("category", "")
                    }
                })
                edges.append({
                    "source": center_id, "target": node_id,
                    "type": "target_school",
                    "weight": prob,
                    "width": 1 + prob * 4,
                    "color": tier_color
                })

        add_school_group(reach_schools, "#FF6B6B", 0, math.pi * 2 / 3, "top", "冲刺")
        add_school_group(match_schools, "#4FACFE", math.pi * 2 / 3, math.pi * 2 / 3, "elite", "匹配")
        add_school_group(safety_schools, "#43E97B", math.pi * 4 / 3, math.pi * 2 / 3, "good", "保底")

        # 竞争关系
        start_idx = len(nodes) - len(reach_schools) - len(match_schools) - len(safety_schools)
        all_school_nodes = nodes[start_idx:]
        for i, s1 in enumerate(all_school_nodes):
            for s2 in all_school_nodes[i + 1:]:
                edges.append({
                    "source": s1["id"], "target": s2["id"],
                    "type": "competition",
                    "weight": 0.3, "width": 1,
                    "color": "#6B48FF", "dashed": True
                })

        return nodes, edges

    def _build_action_layer(
        self,
        user_profile: EducationUserProfile,
        school_nodes: List[Dict],
        center_id: str
    ) -> tuple:
        nodes, edges = [], []

        actions = [
            {"id": "action_gre_prep", "label": "GRE备考", "color": "#FF8C42", "action_type": "exam_prep", "priority": 0.9},
            {"id": "action_research", "label": "科研提升", "color": "#9575FF", "action_type": "research", "priority": 0.7},
            {"id": "action_recommendation", "label": "推荐信", "color": "#4FACFE", "action_type": "application", "priority": 0.8},
            {"id": "action_personal_statement", "label": "个人陈述", "color": "#43E97B", "action_type": "application", "priority": 0.85},
            {"id": "action_interview", "label": "面试准备", "color": "#F093FB", "action_type": "interview", "priority": 0.6},
            {"id": "action_scholarship", "label": "奖学金申请", "color": "#FFD93D", "action_type": "financial", "priority": 0.75},
        ]

        priority_boost = 0.2 if user_profile.research_experience > 0.5 else 0

        for i, action in enumerate(actions):
            priority = min(1.0, action["priority"] + priority_boost * random.random())
            nodes.append({
                "id": action["id"],
                "label": action["label"],
                "type": "action", "layer": 3,
                "position": self._polar_pos(58, (float(i) / len(actions)) * math.pi * 2),
                "size": 6 + priority * 8,
                "color": action["color"],
                "metadata": {
                    "action_type": action["action_type"],
                    "priority": round(priority, 3),
                    "urgency": "high" if priority > 0.8 else ("medium" if priority > 0.6 else "low")
                }
            })
            edges.append({
                "source": center_id, "target": action["id"],
                "type": "action_plan",
                "weight": priority,
                "width": 1 + priority * 2,
                "color": action["color"]
            })

        # 行动连接到学校
        for school_node in school_nodes:
            tier = school_node.get("metadata", {}).get("tier", "")
            prob = school_node.get("metadata", {}).get("probability", 0.5)
            if tier == "top" or prob < 0.2:
                for action in actions[:4]:
                    edges.append({
                        "source": school_node["id"], "target": action["id"],
                        "type": "action_requirement",
                        "weight": 0.4, "width": 1,
                        "color": "#FFC107", "dashed": True
                    })

        return nodes, edges

    def _polar_pos(self, radius: float, angle: float) -> Dict[str, float]:
        x = radius * math.cos(angle)
        y = radius * math.cos(angle) * 0.3
        z = radius * math.sin(angle)
        return {"x": round(x, 2), "y": round(y, 2), "z": round(z, 2)}


# 全局实例
education_kg = EducationKnowledgeGraph()
