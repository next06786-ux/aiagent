from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'your_password')

user_id = "2c2139f7-bab4-483d-9882-ae83ce8734cd"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

with driver.session() as session:
    result = session.run("""
        MATCH (n {user_id: $user_id})
        WHERE NOT n:Source
        RETURN count(n) as count
    """, user_id=user_id)
    count = result.single()['count']
    print(f"Neo4j 直接查询 - 用户 {user_id} 节点数: {count}")
    
    # 列出前10个节点
    result = session.run("""
        MATCH (n {user_id: $user_id})
        WHERE NOT n:Source
        RETURN n.name as name, labels(n)[0] as type, n.category as category
        LIMIT 10
    """, user_id=user_id)
    print("\n前10个节点:")
    for r in result:
        print(f"  - {r['name']} ({r['category'] or r['type']})")

driver.close()
