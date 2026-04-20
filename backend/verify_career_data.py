"""
验证职业规划数据脚本
检查Neo4j中是否正确创建了：我→技能→岗位→公司的完整链路
"""
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

def verify_career_data(user_id="test_user_001"):
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "lifeswarm123")
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        with driver.session() as session:
            print("\n" + "="*60)
            print("职业规划数据验证")
            print("="*60)
            
            # 1. 检查技能节点
            print("\n1. 检查技能节点 (Concept, type='Skill')")
            result = session.run("""
                MATCH (u:User {user_id: $user_id})-[r:HAS_PROFILE]->(c:Concept)
                WHERE c.type = 'Skill'
                RETURN count(c) as skill_count
            """, user_id=user_id)
            skill_count = result.single()['skill_count']
            print(f"   ✓ 找到 {skill_count} 个技能节点")
            
            # 2. 检查岗位节点
            print("\n2. 检查岗位节点 (Entity, type='Job')")
            result = session.run("""
                MATCH (u:User {user_id: $user_id})-[r:INTERESTED_IN]->(e:Entity)
                WHERE e.type = 'Job'
                RETURN count(e) as job_count
            """, user_id=user_id)
            job_count = result.single()['job_count']
            print(f"   ✓ 找到 {job_count} 个岗位节点")
            
            # 3. 检查公司节点
            print("\n3. 检查公司节点 (Entity, type='Organization')")
            result = session.run("""
                MATCH (e:Entity {user_id: $user_id})
                WHERE e.type = 'Organization'
                RETURN count(e) as company_count
            """, user_id=user_id)
            company_count = result.single()['company_count']
            print(f"   ✓ 找到 {company_count} 个公司节点")
            
            # 4. 检查 Job → Skill (REQUIRES) 关系
            print("\n4. 检查 Job → Skill (REQUIRES) 关系")
            result = session.run("""
                MATCH (j:Entity {user_id: $user_id})-[r:REQUIRES]->(c:Concept)
                WHERE j.type = 'Job' AND c.type = 'Skill'
                RETURN count(r) as requires_count
            """, user_id=user_id)
            requires_count = result.single()['requires_count']
            print(f"   ✓ 找到 {requires_count} 个 REQUIRES 关系")
            
            # 5. 检查 Job → Company (PART_OF) 关系
            print("\n5. 检查 Job → Company (PART_OF) 关系")
            result = session.run("""
                MATCH (j:Entity {user_id: $user_id})-[r:PART_OF]->(c:Entity)
                WHERE j.type = 'Job' AND c.type = 'Organization'
                RETURN count(r) as part_of_count
            """, user_id=user_id)
            part_of_count = result.single()['part_of_count']
            print(f"   ✓ 找到 {part_of_count} 个 PART_OF 关系")
            
            # 6. 显示示例数据
            print("\n6. 示例数据（前3个岗位的完整链路）")
            result = session.run("""
                MATCH (u:User {user_id: $user_id})-[:INTERESTED_IN]->(j:Entity)
                WHERE j.type = 'Job'
                OPTIONAL MATCH (j)-[:REQUIRES]->(s:Concept)
                WHERE s.type = 'Skill'
                OPTIONAL MATCH (j)-[:PART_OF]->(c:Entity)
                WHERE c.type = 'Organization'
                RETURN j.name as job,
                       c.name as company,
                       collect(DISTINCT s.name) as skills
                LIMIT 3
            """, user_id=user_id)
            
            for i, record in enumerate(result, 1):
                print(f"\n   岗位 {i}: {record['job']}")
                print(f"   公司: {record['company'] or '未关联'}")
                print(f"   技能: {', '.join(record['skills'][:5]) if record['skills'] else '未关联'}")
            
            print("\n" + "="*60)
            print("验证完成！")
            print("="*60)
            
            # 总结
            print("\n总结:")
            print(f"  - 技能节点: {skill_count}")
            print(f"  - 岗位节点: {job_count}")
            print(f"  - 公司节点: {company_count}")
            print(f"  - Job→Skill关系: {requires_count}")
            print(f"  - Job→Company关系: {part_of_count}")
            
            if requires_count == 0:
                print("\n⚠ 警告: 没有找到 Job→Skill (REQUIRES) 关系！")
                print("   这意味着职业规划视图中不会显示技能层。")
            
            if part_of_count == 0:
                print("\n⚠ 警告: 没有找到 Job→Company (PART_OF) 关系！")
                print("   这意味着职业规划视图中不会显示公司层。")
            
    finally:
        driver.close()

if __name__ == "__main__":
    verify_career_data()
