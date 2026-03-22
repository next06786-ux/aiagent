"""
添加知识星图示例数据
创建丰富的节点和关系网络，展示星图可视化效果
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from datetime import datetime, timedelta
from knowledge.information_knowledge_graph import InformationKnowledgeGraph

# 丰富的知识节点数据
KNOWLEDGE_DATA = {
    # 人物节点
    "Person": [
        {"name": "张三", "category": "社交"},
        {"name": "李四", "category": "社交"},
        {"name": "王五", "category": "工作"},
        {"name": "小明", "category": "家庭"},
        {"name": "导师", "category": "学习"},
    ],
    
    # 概念节点
    "Concept": [
        {"name": "人工智能", "category": "学习"},
        {"name": "机器学习", "category": "学习"},
        {"name": "深度学习", "category": "学习"},
        {"name": "健康生活", "category": "健康"},
        {"name": "时间管理", "category": "效率"},
        {"name": "财务自由", "category": "财务"},
        {"name": "职业发展", "category": "工作"},
        {"name": "人际关系", "category": "社交"},
        {"name": "情绪管理", "category": "情感"},
        {"name": "创造力", "category": "学习"},
    ],
    
    # 事件节点
    "Event": [
        {"name": "晨跑", "category": "健康"},
        {"name": "读书", "category": "学习"},
        {"name": "冥想", "category": "情感"},
        {"name": "项目汇报", "category": "工作"},
        {"name": "团队聚餐", "category": "社交"},
        {"name": "技术分享", "category": "学习"},
        {"name": "健身", "category": "健康"},
        {"name": "写代码", "category": "工作"},
        {"name": "看电影", "category": "娱乐"},
        {"name": "旅行", "category": "娱乐"},
    ],
    
    # 地点节点
    "Location": [
        {"name": "公司", "category": "工作"},
        {"name": "健身房", "category": "健康"},
        {"name": "图书馆", "category": "学习"},
        {"name": "咖啡馆", "category": "社交"},
        {"name": "家", "category": "家庭"},
    ],
    
    # 实体节点
    "Entity": [
        {"name": "Python", "category": "学习"},
        {"name": "PyTorch", "category": "学习"},
        {"name": "MacBook", "category": "工具"},
        {"name": "Kindle", "category": "学习"},
        {"name": "投资组合", "category": "财务"},
    ],
    
    # 情感节点
    "Emotion": [
        {"name": "快乐", "category": "情感"},
        {"name": "焦虑", "category": "情感"},
        {"name": "平静", "category": "情感"},
        {"name": "成就感", "category": "情感"},
        {"name": "压力", "category": "情感"},
    ],
    
    # 健康节点
    "Health": [
        {"name": "睡眠质量", "category": "健康"},
        {"name": "心率", "category": "健康"},
        {"name": "步数", "category": "健康"},
        {"name": "体重", "category": "健康"},
    ],
    
    # 财务节点
    "Finance": [
        {"name": "月收入", "category": "财务"},
        {"name": "储蓄", "category": "财务"},
        {"name": "投资收益", "category": "财务"},
    ],
}

# 关系数据 - 创建丰富的连接网络
RELATIONSHIPS = [
    # 学习相关
    ("人工智能", "机器学习", "INCLUDES"),
    ("机器学习", "深度学习", "INCLUDES"),
    ("深度学习", "PyTorch", "USES"),
    ("Python", "PyTorch", "SUPPORTS"),
    ("读书", "人工智能", "ABOUT"),
    ("技术分享", "机器学习", "ABOUT"),
    ("导师", "人工智能", "TEACHES"),
    ("写代码", "Python", "USES"),
    
    # 健康相关
    ("晨跑", "健康生活", "CONTRIBUTES_TO"),
    ("健身", "健康生活", "CONTRIBUTES_TO"),
    ("冥想", "情绪管理", "HELPS"),
    ("睡眠质量", "健康生活", "AFFECTS"),
    ("晨跑", "步数", "INCREASES"),
    ("健身", "心率", "AFFECTS"),
    ("健身房", "健身", "LOCATION_OF"),
    
    # 工作相关
    ("项目汇报", "职业发展", "CONTRIBUTES_TO"),
    ("王五", "项目汇报", "PARTICIPATES"),
    ("公司", "项目汇报", "LOCATION_OF"),
    ("写代码", "职业发展", "CONTRIBUTES_TO"),
    ("MacBook", "写代码", "TOOL_FOR"),
    
    # 社交相关
    ("张三", "团队聚餐", "PARTICIPATES"),
    ("李四", "团队聚餐", "PARTICIPATES"),
    ("团队聚餐", "人际关系", "STRENGTHENS"),
    ("咖啡馆", "团队聚餐", "LOCATION_OF"),
    
    # 情感相关
    ("项目汇报", "成就感", "CAUSES"),
    ("压力", "焦虑", "CAUSES"),
    ("冥想", "平静", "CAUSES"),
    ("旅行", "快乐", "CAUSES"),
    ("时间管理", "压力", "REDUCES"),
    
    # 财务相关
    ("月收入", "储蓄", "ENABLES"),
    ("储蓄", "投资组合", "FUNDS"),
    ("投资组合", "投资收益", "GENERATES"),
    ("投资收益", "财务自由", "CONTRIBUTES_TO"),
    
    # 跨领域关联
    ("健康生活", "职业发展", "SUPPORTS"),
    ("情绪管理", "人际关系", "IMPROVES"),
    ("时间管理", "职业发展", "ENABLES"),
    ("创造力", "写代码", "ENHANCES"),
    ("读书", "创造力", "STIMULATES"),
    ("家", "小明", "LIVES_AT"),
    ("图书馆", "读书", "LOCATION_OF"),
    ("Kindle", "读书", "TOOL_FOR"),
]


def add_starmap_data():
    """添加星图示例数据"""
    
    print("\n" + "="*60)
    print("  🌟 添加知识星图示例数据")
    print("="*60 + "\n")
    
    user_id = "a113a299-ecff-4363-8d44-aff979dfc547"
    
    try:
        print("📡 连接Neo4j知识图谱...")
        kg = InformationKnowledgeGraph(user_id)
        print("  ✓ 连接成功\n")
        
        # 清空旧数据
        print("🧹 清空旧数据...")
        kg.clear_user_data()
        print("  ✓ 已清空\n")
        
        # 创建来源记录
        timestamp = int(datetime.now().timestamp() * 1000)
        source_id = f"{user_id}_{timestamp}_starmap_demo"
        kg.add_source(
            source_type="demo",
            source_id=source_id,
            timestamp=timestamp,
            metadata={"description": "知识星图示例数据"}
        )
        
        # 添加所有节点
        print("📥 添加知识节点...\n")
        total_nodes = 0
        
        for node_type, nodes in KNOWLEDGE_DATA.items():
            print(f"  [{node_type}]")
            for node in nodes:
                kg.add_information(
                    name=node["name"],
                    info_type=node_type,
                    category=node["category"],
                    confidence=0.9
                )
                kg.add_source_relationship(
                    info_name=node["name"],
                    source_id=source_id,
                    relation_type="MENTIONED_IN",
                    confidence=0.9
                )
                print(f"    ✓ {node['name']}")
                total_nodes += 1
            print()
        
        print(f"✅ 成功添加 {total_nodes} 个节点\n")
        
        # 添加关系
        print("🔗 添加知识关系...\n")
        total_relations = 0
        
        for source, target, rel_type in RELATIONSHIPS:
            success = kg.add_information_relationship(
                source_name=source,
                target_name=target,
                relation_type=rel_type,
                properties={"confidence": 0.85}
            )
            if success:
                print(f"  ✓ {source} --[{rel_type}]--> {target}")
                total_relations += 1
        
        print(f"\n✅ 成功添加 {total_relations} 条关系\n")
        
        # 显示统计
        print("="*60)
        print("  📊 知识图谱统计")
        print("="*60 + "\n")
        
        stats = kg.get_statistics()
        
        print(f"节点总数: {stats['information']['total']} 个")
        print(f"\n按类型分布:")
        for info_type, count in sorted(stats['information']['by_type'].items(), 
                                        key=lambda x: x[1], reverse=True):
            bar = "█" * count
            print(f"  {info_type:12} {bar} {count}")
        
        print(f"\n按领域分布:")
        for category, count in sorted(stats['information']['by_category'].items(), 
                                       key=lambda x: x[1], reverse=True):
            bar = "▓" * count
            print(f"  {category:8} {bar} {count}")
        
        print(f"\n关系总数: {stats['relationships']['total']} 条")
        
        print("\n" + "="*60)
        print("  ✅ 知识星图数据准备完成！")
        print("  现在可以在前端查看星图效果")
        print("="*60 + "\n")
        
        kg.close()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        print("\n提示: 请确保Neo4j已启动")


if __name__ == "__main__":
    add_starmap_data()
