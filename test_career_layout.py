#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试职业图谱布局 - 检查三层结构"""

from backend.vertical.career.career_knowledge_graph import career_kg, UserSkillProfile
import math

# 创建测试用户技能档案
user_profile = UserSkillProfile(
    mastered_skills=["Python", "JavaScript", "Git", "MySQL"],
    partial_skills=["React", "Docker"],
    missing_skills=["Kubernetes", "AWS"],
    target_direction="Python工程师"
)

print("=" * 70)
print("职业图谱三层结构验证")
print("=" * 70)

# 构建图谱
graph_data = career_kg.build_career_graph(user_profile)

# 分析每层的半径分布
layers = {
    "center": [],
    "skill": [],
    "job": [],
    "company": []
}

for node in graph_data["nodes"]:
    pos = node["position"]
    radius = math.sqrt(pos["x"]**2 + pos["y"]**2 + pos["z"]**2)
    node_type = node["type"]
    layers[node_type].append({
        "id": node["id"],
        "label": node["label"],
        "radius": radius,
        "layer": node["layer"]
    })

# 打印每层统计
print("\n【中心节点】")
for n in layers["center"]:
    print(f"  {n['label']}: 半径={n['radius']:.2f}")

print("\n【第一圈 - 技能层】预期半径: 15-20")
skill_radii = [n["radius"] for n in layers["skill"]]
if skill_radii:
    print(f"  节点数: {len(skill_radii)}")
    print(f"  半径范围: {min(skill_radii):.2f} ~ {max(skill_radii):.2f}")
    print(f"  平均半径: {sum(skill_radii)/len(skill_radii):.2f}")
    print(f"  技能列表: {', '.join([n['label'] for n in layers['skill'][:5]])}...")

print("\n【第二圈 - 岗位层】预期半径: 35-40")
job_radii = [n["radius"] for n in layers["job"]]
if job_radii:
    print(f"  节点数: {len(job_radii)}")
    print(f"  半径范围: {min(job_radii):.2f} ~ {max(job_radii):.2f}")
    print(f"  平均半径: {sum(job_radii)/len(job_radii):.2f}")
    print(f"  岗位列表: {', '.join([n['label'] for n in layers['job'][:5]])}...")

print("\n【第三圈 - 公司层】预期半径: 55-60")
company_radii = [n["radius"] for n in layers["company"]]
if company_radii:
    print(f"  节点数: {len(company_radii)}")
    print(f"  半径范围: {min(company_radii):.2f} ~ {max(company_radii):.2f}")
    print(f"  平均半径: {sum(company_radii)/len(company_radii):.2f}")
    print(f"  公司列表: {', '.join([n['label'] for n in layers['company'][:5]])}...")

# 检查层次分离度
print("\n【层次分离度检查】")
if skill_radii and job_radii:
    gap1 = min(job_radii) - max(skill_radii)
    print(f"  技能层 → 岗位层 间隙: {gap1:.2f} (应该 > 10)")
    
if job_radii and company_radii:
    gap2 = min(company_radii) - max(job_radii)
    print(f"  岗位层 → 公司层 间隙: {gap2:.2f} (应该 > 10)")

print("\n" + "=" * 70)
if skill_radii and job_radii and company_radii:
    if (min(job_radii) - max(skill_radii) > 10 and 
        min(company_radii) - max(job_radii) > 10):
        print("✓ 三层结构清晰，层次分明！")
    else:
        print("⚠ 层次间隙不足，可能视觉混乱")
else:
    print("⚠ 某些层缺少节点")
print("=" * 70)
