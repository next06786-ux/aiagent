#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试职业知识图谱功能"""

from backend.vertical.career.career_knowledge_graph import career_kg, UserSkillProfile

# 创建测试用户技能档案
user_profile = UserSkillProfile(
    mastered_skills=["Python", "JavaScript", "Git", "MySQL"],
    partial_skills=["React", "Docker"],
    missing_skills=["Kubernetes", "AWS"],
    target_direction="Python工程师"
)

print("=" * 60)
print("测试职业知识图谱构建")
print("=" * 60)

# 测试构建知识图谱
print("\n1. 构建职业知识图谱...")
graph_data = career_kg.build_career_graph(user_profile)

print(f"✓ 图谱构建成功!")
print(f"  - 总节点数: {graph_data['metadata']['total_nodes']}")
print(f"  - 总连线数: {graph_data['metadata']['total_edges']}")
print(f"  - 技能节点: {len(graph_data['layers']['skills'])}")
print(f"  - 岗位节点: {len(graph_data['layers']['jobs'])}")
print(f"  - 公司节点: {len(graph_data['layers']['companies'])}")

# 测试学习路径计算
print("\n2. 计算学习路径...")
target_skill = "Kubernetes"
path = career_kg.calculate_learning_path(user_profile, target_skill)
print(f"✓ 学习路径: {' -> '.join(path)}")

# 测试可达岗位查询
print("\n3. 查询可达岗位...")
reachable = career_kg.find_reachable_jobs(user_profile, max_missing_skills=3)
print(f"✓ 找到 {len(reachable)} 个可达岗位")
if reachable:
    print(f"  最匹配岗位: {reachable[0]['job']['title']} (匹配度: {reachable[0]['match_rate']:.2%})")

print("\n" + "=" * 60)
print("所有测试通过!")
print("=" * 60)
