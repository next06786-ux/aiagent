"""调试学校节点数据"""
import os
import sys
from dotenv import load_dotenv

# 设置UTF-8编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

USER_ID = "2c2139f7-bab4-483d-9882-ae83ce8734cd"

# 使用InformationKnowledgeGraph导出数据
from backend.knowledge.information_knowledge_graph import InformationKnowledgeGraph

info_kg = InformationKnowledgeGraph(USER_ID)
export = info_kg.export()
info_nodes = export.get('information', [])

print("=" * 60)
print("调试学校节点数据")
print("=" * 60)

# 统计节点类型
entity_count = 0
school_count = 0

for node in info_nodes:
    node_label = node.get("type", "")  # 节点标签
    node_category = node.get("category", "")
    
    if node_label == "Entity":
        entity_count += 1
        if node_category == "university":
            school_count += 1
            if school_count <= 5:
                print(f"\n学校节点 #{school_count}:")
                print(f"  name: {node.get('name')}")
                print(f"  category: '{node_category}'")
                print(f"  id: {node.get('id')}")

print("\n" + "=" * 60)
print(f"Entity节点总数: {entity_count}")
print(f"学校节点数: {school_count}")
print("=" * 60)

info_kg.close()
