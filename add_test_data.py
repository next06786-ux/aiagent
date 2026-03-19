"""
直接添加测试数据到知识图谱
不依赖复杂的系统初始化
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from datetime import datetime, timedelta
from knowledge.information_knowledge_graph import InformationKnowledgeGraph

# 测试数据
TEST_SCENARIOS = [
    {
        "day": "周一",
        "activities": [
            {"info": "完成", "type": "event", "category": "时间管理"},
            {"info": "项目报告", "type": "entity", "category": "时间管理"},
            {"info": "工作", "type": "concept", "category": "时间管理"},
            {"info": "成就感", "type": "concept", "category": "情绪管理"},
        ]
    },
    {
        "day": "周二", 
        "activities": [
            {"info": "学习", "type": "event", "category": "学习管理"},
            {"info": "Python", "type": "entity", "category": "学习管理"},
            {"info": "技术分享会", "type": "event", "category": "学习管理"},
        ]
    },
    {
        "day": "周三",
        "activities": [
            {"info": "瑜伽", "type": "event", "category": "健康管理"},
            {"info": "放松", "type": "concept", "category": "情绪管理"},
            {"info": "咖啡馆", "type": "entity", "category": "社交管理"},
        ]
    },
    {
        "day": "周四",
        "activities": [
            {"info": "压力", "type": "concept", "category": "情绪管理"},
            {"info": "加班", "type": "event", "category": "时间管理"},
            {"info": "deadline", "type": "concept", "category": "时间管理"},
        ]
    },
    {
        "day": "周五",
        "activities": [
            {"info": "项目上线", "type": "event", "category": "时间管理"},
            {"info": "庆祝", "type": "event", "category": "社交管理"},
            {"info": "看电影", "type": "event", "category": "社交管理"},
            {"info": "聚餐", "type": "event", "category": "社交管理"},
            {"info": "消费200元", "type": "entity", "category": "财务管理"},
        ]
    },
    {
        "day": "周六",
        "activities": [
            {"info": "跑步", "type": "event", "category": "健康管理"},
            {"info": "公园", "type": "entity", "category": "健康管理"},
            {"info": "学习新技术", "type": "event", "category": "学习管理"},
            {"info": "做饭", "type": "event", "category": "健康管理"},
        ]
    },
    {
        "day": "周日",
        "activities": [
            {"info": "打扫卫生", "type": "event", "category": "时间管理"},
            {"info": "数学作业", "type": "entity", "category": "学习管理"},
            {"info": "家人", "type": "entity", "category": "社交管理"},
            {"info": "视频通话", "type": "event", "category": "社交管理"},
        ]
    },
]


def add_test_data():
    """添加测试数据"""
    
    print("\n" + "="*60)
    print("  添加测试数据到信息知识图谱")
    print("="*60 + "\n")
    
    user_id = "default_user"  # 改为前端使用的用户ID
    
    try:
        # 连接知识图谱
        print("📡 连接Neo4j知识图谱...")
        kg = InformationKnowledgeGraph(user_id)
        print("  ✓ 连接成功\n")
        
        # 清空旧数据
        print("🧹 清空旧数据...")
        kg.clear_user_data()
        print("  ✓ 已清空\n")
        
        # 添加数据
        print("📥 添加测试数据...\n")
        
        base_time = datetime.now()
        total_added = 0
        
        for i, scenario in enumerate(TEST_SCENARIOS):
            day = scenario["day"]
            timestamp = int((base_time - timedelta(days=len(TEST_SCENARIOS)-i-1)).timestamp() * 1000)
            
            print(f"[{day}]")
            
            # 创建来源记录
            source_id = f"{user_id}_{timestamp}_{day}"
            kg.add_source(
                source_type="conversation",
                source_id=source_id,
                timestamp=timestamp,
                metadata={"day": day}
            )
            
            # 添加信息节点
            for activity in scenario["activities"]:
                info_name = activity["info"]
                info_type = activity["type"]
                category = activity["category"]
                
                # 添加信息节点
                kg.add_information(
                    name=info_name,
                    info_type=info_type,
                    category=category,
                    confidence=0.85
                )
                
                # 添加溯源关系
                kg.add_source_relationship(
                    info_name=info_name,
                    source_id=source_id,
                    relation_type="MENTIONED_IN",
                    confidence=0.85
                )
                
                print(f"  ✓ {info_name} ({info_type} - {category})")
                total_added += 1
            
            print()
        
        print(f"✅ 成功添加 {total_added} 个信息节点\n")
        
        # 添加一些关系
        print("🔗 添加信息关系...\n")
        
        relationships = [
            ("学习", "Python", "INCLUDES"),
            ("工作", "项目报告", "REQUIRES"),
            ("跑步", "公园", "OCCURS_AT"),
            ("聚餐", "消费200元", "CAUSES"),
            ("加班", "压力", "CAUSES"),
            ("瑜伽", "放松", "CAUSES"),
        ]
        
        for source, target, rel_type in relationships:
            success = kg.add_information_relationship(
                source_name=source,
                target_name=target,
                relation_type=rel_type,
                properties={"confidence": 0.8}
            )
            if success:
                print(f"  ✓ {source} --[{rel_type}]--> {target}")
        
        print()
        
        # 显示统计
        print("="*60)
        print("  知识图谱统计")
        print("="*60 + "\n")
        
        stats = kg.get_statistics()
        
        print(f"📊 信息节点: {stats['information']['total']} 个")
        print(f"   按类型:")
        for info_type, count in stats['information']['by_type'].items():
            print(f"     - {info_type}: {count} 个")
        
        print(f"\n   按生活领域:")
        for category, count in sorted(stats['information']['by_category'].items(), 
                                       key=lambda x: x[1], reverse=True):
            print(f"     - {category}: {count} 个")
        
        print(f"\n📁 来源记录: {stats['sources']['total']} 个")
        print(f"🔗 关系连接: {stats['relationships']['total']} 个")
        
        # 示例查询
        print("\n" + "="*60)
        print("  示例查询")
        print("="*60 + "\n")
        
        queries = ["学习", "运动", "工作", "社交"]
        
        for keyword in queries:
            results = kg.search_information(keyword=keyword, limit=3)
            if results:
                print(f"🔍 '{keyword}' 相关信息:")
                for r in results:
                    print(f"   - [{r['type']}] {r['name']} ({r['category']})")
                print()
        
        print("="*60)
        print("  ✅ 测试数据添加完成！")
        print("  现在可以启动后端服务测试系统功能")
        print("="*60 + "\n")
        
        kg.close()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        print("\n提示: 请确保Neo4j已启动")


if __name__ == "__main__":
    add_test_data()
