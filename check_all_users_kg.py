from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'your_password')

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

with driver.session() as session:
    # 查询所有不同的 user_id 及其节点数
    result = session.run("""
        MATCH (n)
        WHERE n.user_id IS NOT NULL AND NOT n:Source
        RETURN n.user_id as user_id, count(n) as node_count
        ORDER BY node_count DESC
    """)
    
    print("=" * 60)
    print("  所有用户的知识图谱数据")
    print("=" * 60)
    
    for r in result:
        user_id = r['user_id']
        count = r['node_count']
        print(f"\n用户: {user_id}")
        print(f"节点数: {count}")
        
        # 显示该用户的前3个节点
        nodes = session.run("""
            MATCH (n {user_id: $user_id})
            WHERE NOT n:Source
            RETURN n.name as name, n.category as category
            LIMIT 3
        """, user_id=user_id)
        print("示例节点:")
        for n in nodes:
            print(f"  - {n['name']} ({n['category']})")

driver.close()
