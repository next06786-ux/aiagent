"""统计Neo4j节点数量"""
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "lifeswarm123")

driver = GraphDatabase.driver(uri, auth=(user, password))
USER_ID = "2c2139f7-bab4-483d-9882-ae83ce8734cd"

with driver.session() as session:
    # 总节点统计
    result = session.run("""
        MATCH (n {user_id: $user_id})
        RETURN labels(n)[0] as type, count(n) as count
        ORDER BY count DESC
    """, user_id=USER_ID).data()
    
    print("=" * 60)
    print("Neo4j 数据统计")
    print("=" * 60)
    print("\n节点统计:")
    total = 0
    for row in result:
        print(f"  {row['type']}: {row['count']}")
        total += row['count']
    print(f"\n总计: {total} 个节点")
    
    # Entity分类统计
    entity_stats = session.run("""
        MATCH (e:Entity {user_id: $user_id})
        RETURN e.category as category, count(e) as count
        ORDER BY count DESC
    """, user_id=USER_ID).data()
    
    print("\nEntity节点分类:")
    for row in entity_stats:
        print(f"  {row['category']}: {row['count']}")
    
    # Concept分类统计
    concept_stats = session.run("""
        MATCH (c:Concept {user_id: $user_id})
        RETURN c.type as type, count(c) as count
        ORDER BY count DESC
    """, user_id=USER_ID).data()
    
    print("\nConcept节点分类:")
    for row in concept_stats:
        print(f"  {row['type']}: {row['count']}")
    
    # 关系统计
    rel_stats = session.run("""
        MATCH (u:User {user_id: $user_id})-[r]->(n)
        RETURN type(r) as rel_type, count(r) as count
        ORDER BY count DESC
    """, user_id=USER_ID).data()
    
    print("\n用户关系统计:")
    for row in rel_stats:
        print(f"  {row['rel_type']}: {row['count']}")
    
    print("\n" + "=" * 60)

driver.close()
