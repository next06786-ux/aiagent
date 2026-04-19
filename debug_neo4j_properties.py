"""
调试Neo4j properties返回的数据
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "lifeswarm123"

user_id = "2c2139f7-bab4-483d-9882-ae83ce8734cd"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

with driver.session() as session:
    # 使用和检索器相同的查询
    result = session.run("""
        MATCH (n:Entity)
        WHERE n.user_id = $user_id AND n.type = 'Person'
        RETURN elementId(n) as id, labels(n) as labels, properties(n) as props
        LIMIT 3
    """, user_id=user_id)
    
    print("=" * 60)
    print("Neo4j properties() 返回的数据:")
    print("=" * 60)
    
    for i, record in enumerate(result, 1):
        print(f"\n节点 {i}:")
        print(f"  ID: {record['id']}")
        print(f"  Labels: {record['labels']}")
        print(f"  Props: {dict(record['props'])}")
        
        # 解析props
        props = dict(record['props'])
        print(f"  解析后:")
        print(f"    type: {props.get('type')}")
        print(f"    name: {props.get('name')}")
        print(f"    category: {props.get('category')}")

driver.close()
