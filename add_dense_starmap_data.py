"""
添加密集的知识星图数据
创建大量节点和连线，形成星云效果
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from datetime import datetime
from knowledge.information_knowledge_graph import InformationKnowledgeGraph
import random

# 生成大量节点
def generate_nodes():
    nodes = []
    
    # 核心概念群（中心）
    core_concepts = [
        "人工智能", "机器学习", "深度学习", "神经网络", "自然语言处理",
        "计算机视觉", "强化学习", "数据科学", "算法", "模型训练"
    ]
    for name in core_concepts:
        nodes.append({"name": name, "type": "Concept", "category": "技术", "cluster": 0})
    
    # 人物群
    people = [
        "张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十",
        "郑一", "王二", "导师", "同事A", "同事B", "朋友C", "家人D"
    ]
    for name in people:
        nodes.append({"name": name, "type": "Person", "category": "社交", "cluster": 1})
    
    # 事件群
    events = [
        "晨跑", "读书", "冥想", "项目汇报", "团队聚餐", "技术分享", "健身",
        "写代码", "看电影", "旅行", "学习Python", "参加会议", "代码评审",
        "产品发布", "年度总结", "团建活动", "培训课程", "面试", "答辩"
    ]
    for name in events:
        nodes.append({"name": name, "type": "Event", "category": "活动", "cluster": 2})
    
    # 地点群
    locations = [
        "公司", "健身房", "图书馆", "咖啡馆", "家", "公园", "商场",
        "餐厅", "电影院", "学校", "医院", "银行", "机场"
    ]
    for name in locations:
        nodes.append({"name": name, "type": "Location", "category": "地点", "cluster": 3})
    
    # 技术实体群
    tech_entities = [
        "Python", "PyTorch", "TensorFlow", "JavaScript", "React", "Vue",
        "Docker", "Kubernetes", "AWS", "Linux", "Git", "VSCode",
        "MacBook", "iPhone", "iPad", "服务器", "数据库", "API"
    ]
    for name in tech_entities:
        nodes.append({"name": name, "type": "Entity", "category": "技术", "cluster": 0})
    
    # 情感群
    emotions = [
        "快乐", "焦虑", "平静", "成就感", "压力", "兴奋", "满足",
        "期待", "紧张", "放松", "自信", "困惑"
    ]
    for name in emotions:
        nodes.append({"name": name, "type": "Emotion", "category": "情感", "cluster": 4})
    
    # 健康群
    health = [
        "睡眠质量", "心率", "步数", "体重", "血压", "运动量",
        "饮食", "水分摄入", "久坐时间", "屏幕时间"
    ]
    for name in health:
        nodes.append({"name": name, "type": "Health", "category": "健康", "cluster": 5})
    
    # 财务群
    finance = [
        "月收入", "储蓄", "投资收益", "房贷", "消费", "理财",
        "股票", "基金", "保险", "税务"
    ]
    for name in finance:
        nodes.append({"name": name, "type": "Finance", "category": "财务", "cluster": 6})
    
    # 学习群
    learning = [
        "英语学习", "数学", "物理", "编程", "设计", "写作",
        "演讲", "管理", "沟通", "领导力", "创新思维"
    ]
    for name in learning:
        nodes.append({"name": name, "type": "Learning", "category": "学习", "cluster": 7})
    
    return nodes


def generate_relationships(nodes):
    """生成大量关系，形成密集网络"""
    relationships = []
    node_names = [n["name"] for n in nodes]
    
    # 同类型节点之间的关系（形成聚类）
    for i, n1 in enumerate(nodes):
        for j, n2 in enumerate(nodes):
            if i >= j:
                continue
            
            # 同一cluster的节点有更高概率连接
            if n1["cluster"] == n2["cluster"]:
                if random.random() < 0.4:  # 40%概率
                    relationships.append((n1["name"], n2["name"], "RELATED_TO"))
            else:
                # 不同cluster之间也有少量连接
                if random.random() < 0.05:  # 5%概率
                    relationships.append((n1["name"], n2["name"], "CONNECTED_TO"))
    
    # 添加一些特定的语义关系
    semantic_relations = [
        ("人工智能", "机器学习", "INCLUDES"),
        ("机器学习", "深度学习", "INCLUDES"),
        ("深度学习", "神经网络", "USES"),
        ("Python", "PyTorch", "SUPPORTS"),
        ("Python", "TensorFlow", "SUPPORTS"),
        ("晨跑", "健康", "CONTRIBUTES_TO"),
        ("读书", "学习", "IS_PART_OF"),
        ("压力", "焦虑", "CAUSES"),
        ("冥想", "平静", "CAUSES"),
        ("月收入", "储蓄", "ENABLES"),
    ]
    
    for s, t, r in semantic_relations:
        if s in node_names and t in node_names:
            relationships.append((s, t, r))
    
    return relationships


def add_dense_data():
    print("\n" + "="*60)
    print("  🌌 添加密集知识星图数据")
    print("="*60 + "\n")
    
    user_id = "default_user"
    
    try:
        print("📡 连接Neo4j...")
        kg = InformationKnowledgeGraph(user_id)
        print("  ✓ 连接成功\n")
        
        print("🧹 清空旧数据...")
        kg.clear_user_data()
        print("  ✓ 已清空\n")
        
        # 创建来源
        timestamp = int(datetime.now().timestamp() * 1000)
        source_id = f"{user_id}_{timestamp}_dense_starmap"
        kg.add_source(
            source_type="demo",
            source_id=source_id,
            timestamp=timestamp,
            metadata={"description": "密集知识星图"}
        )
        
        # 生成节点
        nodes = generate_nodes()
        print(f"📥 添加 {len(nodes)} 个节点...")
        
        for node in nodes:
            kg.add_information(
                name=node["name"],
                info_type=node["type"],
                category=node["category"],
                confidence=0.9
            )
            kg.add_source_relationship(
                info_name=node["name"],
                source_id=source_id,
                relation_type="MENTIONED_IN",
                confidence=0.9
            )
        print("  ✓ 节点添加完成\n")
        
        # 生成关系
        relationships = generate_relationships(nodes)
        print(f"🔗 添加 {len(relationships)} 条关系...")
        
        added = 0
        for source, target, rel_type in relationships:
            success = kg.add_information_relationship(
                source_name=source,
                target_name=target,
                relation_type=rel_type,
                properties={"confidence": 0.8}
            )
            if success:
                added += 1
        
        print(f"  ✓ 成功添加 {added} 条关系\n")
        
        # 统计
        stats = kg.get_statistics()
        print("="*60)
        print("  📊 统计")
        print("="*60)
        print(f"  节点: {stats['information']['total']}")
        print(f"  关系: {stats['relationships']['total']}")
        print("="*60 + "\n")
        
        kg.close()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    add_dense_data()
