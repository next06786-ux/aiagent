"""
为用户 2c2139f7-bab4-483d-9882-ae83ce8734cd 批量写入知识图谱数据
运行: python backend/scripts/seed_knowledge_graph.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.knowledge.information_knowledge_graph import InformationKnowledgeGraph

USER_ID = "2c2139f7-bab4-483d-9882-ae83ce8734cd"

# ── 新增节点 ─────────────────────────────────────────────────
NODES = [
    # 人物
    ("李明", "entity", "社交", 0.82, {"role": "朋友", "closeness": 0.75}),
    ("王芳", "entity", "社交", 0.78, {"role": "同事", "closeness": 0.6}),
    ("陈教授", "entity", "学习", 0.85, {"role": "导师", "closeness": 0.7}),
    ("父亲", "entity", "家庭", 0.9, {"role": "家人", "closeness": 0.88}),
    ("母亲", "entity", "家庭", 0.9, {"role": "家人", "closeness": 0.9}),
    ("前同事赵磊", "entity", "工作", 0.65, {"role": "前同事", "closeness": 0.45}),
    ("创业伙伴", "entity", "工作", 0.8, {"role": "合伙人", "closeness": 0.72}),

    # 事件
    ("晋升评审", "event", "工作", 0.88, {"status": "进行中", "urgency": "高"}),
    ("年度体检", "event", "健康", 0.75, {"status": "待完成", "urgency": "中"}),
    ("家庭聚会", "event", "家庭", 0.7, {"status": "计划中", "urgency": "低"}),
    ("技术分享会", "event", "学习", 0.72, {"status": "计划中", "urgency": "中"}),
    ("投资复盘", "event", "财务", 0.8, {"status": "进行中", "urgency": "高"}),
    ("健身打卡", "event", "健康", 0.65, {"status": "持续中", "urgency": "低"}),
    ("读书计划", "event", "学习", 0.7, {"status": "进行中", "urgency": "低"}),

    # 概念/目标
    ("副业收入", "concept", "财务", 0.85, {"type": "目标", "priority": "高"}),
    ("技术博客", "concept", "学习", 0.75, {"type": "项目", "priority": "中"}),
    ("冥想习惯", "concept", "健康", 0.7, {"type": "习惯", "priority": "中"}),
    ("英语提升", "concept", "学习", 0.78, {"type": "目标", "priority": "高"}),
    ("代码质量", "concept", "工作", 0.82, {"type": "标准", "priority": "高"}),
    ("工作生活平衡", "concept", "情感", 0.88, {"type": "价值观", "priority": "高"}),
    ("被动收入", "concept", "财务", 0.8, {"type": "目标", "priority": "高"}),
    ("开源项目", "concept", "学习", 0.72, {"type": "项目", "priority": "中"}),
    ("情绪稳定", "concept", "情感", 0.85, {"type": "目标", "priority": "高"}),
    ("社交边界", "concept", "社交", 0.75, {"type": "价值观", "priority": "中"}),

    # 健康
    ("运动频率", "pattern", "健康", 0.7, {"frequency": "每周3次", "trend": "上升"}),
    ("饮食习惯", "pattern", "健康", 0.68, {"quality": "中等", "trend": "改善中"}),
    ("睡眠规律", "pattern", "健康", 0.72, {"avg_hours": 7.2, "trend": "稳定"}),
    ("压力水平", "pattern", "健康", 0.8, {"level": "中高", "trend": "波动"}),

    # 情绪
    ("焦虑", "entity", "情感", 0.75, {"trigger": "工作压力", "frequency": "偶发"}),
    ("期待", "entity", "情感", 0.7, {"trigger": "新项目", "frequency": "常见"}),
    ("满足感", "entity", "情感", 0.78, {"trigger": "完成目标", "frequency": "间歇"}),
    ("孤独感", "entity", "情感", 0.65, {"trigger": "社交减少", "frequency": "偶发"}),

    # 工作
    ("项目A", "event", "工作", 0.85, {"status": "进行中", "deadline": "Q2"}),
    ("技术债务", "concept", "工作", 0.78, {"severity": "中", "priority": "高"}),
    ("团队协作", "concept", "工作", 0.8, {"quality": "良好", "trend": "改善"}),
    ("绩效目标", "concept", "工作", 0.88, {"completion": 0.65, "deadline": "年底"}),

    # 财务
    ("股票投资", "entity", "财务", 0.75, {"risk": "中", "return": "待观察"}),
    ("应急基金", "concept", "财务", 0.82, {"months_covered": 3, "target": 6}),
    ("消费记录", "pattern", "财务", 0.65, {"trend": "稳定", "category": "日常"}),

    # 学习
    ("Python进阶", "concept", "学习", 0.8, {"progress": 0.6, "priority": "高"}),
    ("系统设计", "concept", "学习", 0.82, {"progress": 0.4, "priority": "高"}),
    ("产品思维", "concept", "学习", 0.75, {"progress": 0.3, "priority": "中"}),
]

# ── 关系 ─────────────────────────────────────────────────────
RELATIONS = [
    # 人物关系
    ("李明", "人际关系", "RELATED_TO", {"strength": 0.75}),
    ("王芳", "人际关系", "RELATED_TO", {"strength": 0.6}),
    ("陈教授", "导师", "MENTORS", {"strength": 0.85}),
    ("父亲", "家庭", "BELONGS_TO", {"strength": 0.9}),
    ("母亲", "家庭", "BELONGS_TO", {"strength": 0.9}),
    ("创业伙伴", "职业发展", "SUPPORTS", {"strength": 0.72}),

    # 事件关联
    ("晋升评审", "绩效目标", "REQUIRES", {"strength": 0.88}),
    ("晋升评审", "代码质量", "REQUIRES", {"strength": 0.8}),
    ("晋升评审", "团队协作", "REQUIRES", {"strength": 0.75}),
    ("投资复盘", "股票投资", "ANALYZES", {"strength": 0.8}),
    ("投资复盘", "被动收入", "CONTRIBUTES_TO", {"strength": 0.7}),
    ("健身打卡", "运动频率", "IMPROVES", {"strength": 0.75}),
    ("健身打卡", "压力水平", "REDUCES", {"strength": 0.65}),
    ("读书计划", "Python进阶", "ADVANCES", {"strength": 0.7}),
    ("读书计划", "系统设计", "ADVANCES", {"strength": 0.65}),

    # 概念关联
    ("副业收入", "被动收入", "LEADS_TO", {"strength": 0.8}),
    ("副业收入", "财务自由", "CONTRIBUTES_TO", {"strength": 0.75}),
    ("技术博客", "开源项目", "RELATED_TO", {"strength": 0.7}),
    ("技术博客", "英语提升", "REQUIRES", {"strength": 0.6}),
    ("冥想习惯", "情绪稳定", "IMPROVES", {"strength": 0.78}),
    ("冥想习惯", "压力水平", "REDUCES", {"strength": 0.72}),
    ("工作生活平衡", "压力水平", "REDUCES", {"strength": 0.8}),
    ("工作生活平衡", "满足感", "INCREASES", {"strength": 0.75}),
    ("社交边界", "孤独感", "CAUSES", {"strength": 0.55}),
    ("社交边界", "情绪稳定", "SUPPORTS", {"strength": 0.65}),

    # 情绪关联
    ("焦虑", "压力水平", "CAUSED_BY", {"strength": 0.82}),
    ("焦虑", "睡眠规律", "DISRUPTS", {"strength": 0.7}),
    ("期待", "项目A", "TRIGGERED_BY", {"strength": 0.72}),
    ("满足感", "绩效目标", "TRIGGERED_BY", {"strength": 0.75}),
    ("孤独感", "社交边界", "CAUSED_BY", {"strength": 0.6}),

    # 健康关联
    ("运动频率", "睡眠规律", "IMPROVES", {"strength": 0.7}),
    ("饮食习惯", "健康生活", "CONTRIBUTES_TO", {"strength": 0.72}),
    ("睡眠规律", "压力水平", "AFFECTS", {"strength": 0.75}),
    ("年度体检", "健康生活", "MONITORS", {"strength": 0.8}),

    # 工作关联
    ("项目A", "晋升评审", "IMPACTS", {"strength": 0.85}),
    ("项目A", "团队协作", "REQUIRES", {"strength": 0.78}),
    ("技术债务", "代码质量", "REDUCES", {"strength": 0.8}),
    ("技术债务", "项目A", "RISKS", {"strength": 0.7}),
    ("绩效目标", "职业发展", "DRIVES", {"strength": 0.88}),

    # 学习关联
    ("Python进阶", "系统设计", "COMPLEMENTS", {"strength": 0.75}),
    ("系统设计", "代码质量", "IMPROVES", {"strength": 0.8}),
    ("产品思维", "职业发展", "ENHANCES", {"strength": 0.7}),
    ("英语提升", "职业发展", "ENHANCES", {"strength": 0.72}),
    ("人工智能", "Python进阶", "REQUIRES", {"strength": 0.82}),
    ("机器学习", "Python进阶", "REQUIRES", {"strength": 0.8}),

    # 财务关联
    ("股票投资", "投资收益", "GENERATES", {"strength": 0.7}),
    ("应急基金", "财务自由", "SUPPORTS", {"strength": 0.75}),
    ("消费记录", "应急基金", "AFFECTS", {"strength": 0.65}),
]


def main():
    print(f"连接 Neo4j，用户: {USER_ID}")
    kg = InformationKnowledgeGraph(USER_ID)

    print(f"\n写入 {len(NODES)} 个节点...")
    ok = 0
    for name, ntype, category, confidence, attrs in NODES:
        try:
            kg.add_information(name, ntype, category, confidence, attrs)
            ok += 1
            print(f"  ✓ {name} ({ntype}/{category})")
        except Exception as e:
            print(f"  ✗ {name}: {e}")
    print(f"节点写入完成: {ok}/{len(NODES)}")

    print(f"\n写入 {len(RELATIONS)} 条关系...")
    ok = 0
    for src, tgt, rel_type, props in RELATIONS:
        try:
            result = kg.add_information_relationship(src, tgt, rel_type, props)
            if result:
                ok += 1
                print(f"  ✓ {src} -{rel_type}-> {tgt}")
            else:
                print(f"  ⚠ {src} -{rel_type}-> {tgt} (节点不存在，跳过)")
        except Exception as e:
            print(f"  ✗ {src} -> {tgt}: {e}")
    print(f"关系写入完成: {ok}/{len(RELATIONS)}")

    stats = kg.get_statistics()
    print(f"\n图谱统计:")
    print(f"  信息节点总数: {stats['information']['total']}")
    print(f"  关系总数: {stats['relationships']['total']}")
    kg.close()
    print("\n完成！")


if __name__ == "__main__":
    main()
