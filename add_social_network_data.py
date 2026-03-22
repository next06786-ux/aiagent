"""
添加人际关系网络数据
以"我"为中心，构建社交关系图谱
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from datetime import datetime
from knowledge.information_knowledge_graph import InformationKnowledgeGraph
import random

# 人际关系数据
SOCIAL_NETWORK = {
    # 核心：我自己
    "me": {
        "name": "我",
        "type": "Person",
        "category": "自己",
        "importance": 10
    },
    
    # 家人（最亲密）
    "family": [
        {"name": "爸爸", "relation": "FATHER", "intimacy": 10},
        {"name": "妈妈", "relation": "MOTHER", "intimacy": 10},
        {"name": "妻子", "relation": "SPOUSE", "intimacy": 10},
        {"name": "儿子", "relation": "CHILD", "intimacy": 10},
        {"name": "爷爷", "relation": "GRANDFATHER", "intimacy": 8},
        {"name": "奶奶", "relation": "GRANDMOTHER", "intimacy": 8},
        {"name": "外公", "relation": "GRANDFATHER", "intimacy": 7},
        {"name": "外婆", "relation": "GRANDMOTHER", "intimacy": 7},
        {"name": "哥哥", "relation": "SIBLING", "intimacy": 8},
        {"name": "姐姐", "relation": "SIBLING", "intimacy": 8},
        {"name": "叔叔", "relation": "UNCLE", "intimacy": 5},
        {"name": "阿姨", "relation": "AUNT", "intimacy": 5},
        {"name": "表哥", "relation": "COUSIN", "intimacy": 4},
        {"name": "表妹", "relation": "COUSIN", "intimacy": 4},
    ],
    
    # 好友（亲密）
    "close_friends": [
        {"name": "小明", "relation": "BEST_FRIEND", "intimacy": 9, "context": "发小"},
        {"name": "小红", "relation": "BEST_FRIEND", "intimacy": 9, "context": "闺蜜"},
        {"name": "阿强", "relation": "CLOSE_FRIEND", "intimacy": 8, "context": "大学室友"},
        {"name": "小李", "relation": "CLOSE_FRIEND", "intimacy": 8, "context": "高中同学"},
        {"name": "老王", "relation": "CLOSE_FRIEND", "intimacy": 7, "context": "球友"},
    ],
    
    # 同事
    "colleagues": [
        {"name": "张总", "relation": "BOSS", "intimacy": 5, "context": "直属领导"},
        {"name": "李经理", "relation": "MANAGER", "intimacy": 4, "context": "部门经理"},
        {"name": "王工", "relation": "COLLEAGUE", "intimacy": 6, "context": "同组同事"},
        {"name": "赵姐", "relation": "COLLEAGUE", "intimacy": 5, "context": "同组同事"},
        {"name": "刘哥", "relation": "COLLEAGUE", "intimacy": 5, "context": "隔壁组"},
        {"name": "陈工", "relation": "COLLEAGUE", "intimacy": 4, "context": "技术大牛"},
        {"name": "小周", "relation": "COLLEAGUE", "intimacy": 6, "context": "新来的"},
        {"name": "孙总", "relation": "EXECUTIVE", "intimacy": 2, "context": "公司高管"},
    ],
    
    # 普通朋友
    "friends": [
        {"name": "健身教练", "relation": "ACQUAINTANCE", "intimacy": 3, "context": "健身房"},
        {"name": "邻居大叔", "relation": "NEIGHBOR", "intimacy": 3, "context": "楼上"},
        {"name": "快递小哥", "relation": "SERVICE", "intimacy": 2, "context": "常送件"},
        {"name": "理发师Tony", "relation": "SERVICE", "intimacy": 3, "context": "理发店"},
        {"name": "咖啡店老板", "relation": "ACQUAINTANCE", "intimacy": 3, "context": "常去"},
        {"name": "前同事小张", "relation": "EX_COLLEAGUE", "intimacy": 4, "context": "上家公司"},
        {"name": "大学老师", "relation": "MENTOR", "intimacy": 5, "context": "导师"},
        {"name": "驾校教练", "relation": "TEACHER", "intimacy": 2, "context": "学车"},
    ],
    
    # 网友/弱关系
    "weak_ties": [
        {"name": "技术群友A", "relation": "ONLINE_FRIEND", "intimacy": 2, "context": "技术交流群"},
        {"name": "技术群友B", "relation": "ONLINE_FRIEND", "intimacy": 2, "context": "技术交流群"},
        {"name": "游戏好友", "relation": "ONLINE_FRIEND", "intimacy": 3, "context": "王者荣耀"},
        {"name": "微博网友", "relation": "FOLLOWER", "intimacy": 1, "context": "互关"},
        {"name": "知乎大V", "relation": "FOLLOWING", "intimacy": 1, "context": "关注"},
    ],
}

# 人与人之间的关系（除了与"我"的关系外）
INTER_PERSON_RELATIONS = [
    # 家人之间
    ("爸爸", "妈妈", "SPOUSE", 10),
    ("爸爸", "爷爷", "CHILD", 9),
    ("爸爸", "奶奶", "CHILD", 9),
    ("妈妈", "外公", "CHILD", 9),
    ("妈妈", "外婆", "CHILD", 9),
    ("哥哥", "爸爸", "CHILD", 9),
    ("哥哥", "妈妈", "CHILD", 9),
    ("姐姐", "爸爸", "CHILD", 9),
    ("姐姐", "妈妈", "CHILD", 9),
    ("叔叔", "爷爷", "CHILD", 8),
    ("表哥", "叔叔", "CHILD", 7),
    
    # 同事之间
    ("张总", "李经理", "MANAGES", 5),
    ("李经理", "王工", "MANAGES", 4),
    ("李经理", "赵姐", "MANAGES", 4),
    ("王工", "赵姐", "COLLEAGUE", 6),
    ("王工", "小周", "MENTOR", 5),
    ("刘哥", "陈工", "COLLEAGUE", 4),
    ("孙总", "张总", "MANAGES", 3),
    
    # 朋友之间
    ("小明", "阿强", "FRIEND", 5),
    ("小李", "小红", "FRIEND", 4),
    ("老王", "健身教练", "KNOWS", 3),
    
    # 弱关系
    ("技术群友A", "技术群友B", "ONLINE_FRIEND", 3),
]


def add_social_network():
    print("\n" + "="*60)
    print("  👥 添加人际关系网络数据")
    print("="*60 + "\n")
    
    user_id = "a113a299-ecff-4363-8d44-aff979dfc547"
    
    try:
        print("📡 连接Neo4j...")
        kg = InformationKnowledgeGraph(user_id)
        print("  ✓ 连接成功\n")
        
        print("🧹 清空旧数据...")
        kg.clear_user_data()
        print("  ✓ 已清空\n")
        
        # 创建来源
        timestamp = int(datetime.now().timestamp() * 1000)
        source_id = f"{user_id}_{timestamp}_social_network"
        kg.add_source(
            source_type="social",
            source_id=source_id,
            timestamp=timestamp,
            metadata={"description": "人际关系网络"}
        )
        
        # 添加"我"
        me = SOCIAL_NETWORK["me"]
        kg.add_information(
            name=me["name"],
            info_type=me["type"],
            category=me["category"],
            confidence=1.0,
            attributes={"importance": me["importance"]}
        )
        print(f"  ✓ 添加核心节点: {me['name']}")
        
        # 添加所有人物节点
        all_people = []
        total_relations = 0
        
        for group_name, people in SOCIAL_NETWORK.items():
            if group_name == "me":
                continue
                
            print(f"\n  [{group_name}]")
            for person in people:
                # 添加人物节点
                kg.add_information(
                    name=person["name"],
                    info_type="Person",
                    category=group_name,
                    confidence=0.9,
                    attributes={
                        "intimacy": person["intimacy"],
                        "context": person.get("context", "")
                    }
                )
                kg.add_source_relationship(
                    info_name=person["name"],
                    source_id=source_id,
                    relation_type="MENTIONED_IN",
                    confidence=0.9
                )
                
                # 添加与"我"的关系
                kg.add_information_relationship(
                    source_name="我",
                    target_name=person["name"],
                    relation_type=person["relation"],
                    properties={
                        "intimacy": person["intimacy"],
                        "context": person.get("context", "")
                    }
                )
                
                print(f"    ✓ {person['name']} ({person['relation']}, 亲密度:{person['intimacy']})")
                all_people.append(person["name"])
                total_relations += 1
        
        # 添加人与人之间的关系
        print(f"\n  [人际互联]")
        for p1, p2, rel, intimacy in INTER_PERSON_RELATIONS:
            success = kg.add_information_relationship(
                source_name=p1,
                target_name=p2,
                relation_type=rel,
                properties={"intimacy": intimacy}
            )
            if success:
                print(f"    ✓ {p1} --[{rel}]--> {p2}")
                total_relations += 1
        
        # 统计
        stats = kg.get_statistics()
        print("\n" + "="*60)
        print("  📊 人际关系网络统计")
        print("="*60)
        print(f"  人物节点: {stats['information']['total']}")
        print(f"  关系连接: {total_relations}")
        print("\n  按圈层分布:")
        for category, count in stats['information']['by_category'].items():
            print(f"    {category}: {count} 人")
        print("="*60 + "\n")
        
        kg.close()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    add_social_network()
