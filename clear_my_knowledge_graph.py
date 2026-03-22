"""
清除指定用户的知识图谱节点
"""
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('backend/.env')

# Neo4j 连接配置
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'your_password')

# 你的用户ID
USER_ID = 'a113a299-ecff-4363-8d44-aff979dfc547'

def clear_user_knowledge_graph(user_id: str):
    """清除指定用户的所有知识图谱节点和关系"""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            # 1. 统计节点数量
            result = session.run("""
                MATCH (n)
                WHERE n.user_id = $user_id
                RETURN count(n) as count
            """, user_id=user_id)
            count = result.single()['count']
            print(f"📊 找到 {count} 个节点属于用户 {user_id}")
            
            if count == 0:
                print("✅ 没有需要删除的节点")
                return
            
            # 2. 删除所有关系
            result = session.run("""
                MATCH (n)-[r]-()
                WHERE n.user_id = $user_id
                DELETE r
                RETURN count(r) as count
            """, user_id=user_id)
            rel_count = result.single()['count']
            print(f"🗑️  删除了 {rel_count} 条关系")
            
            # 3. 删除所有节点
            result = session.run("""
                MATCH (n)
                WHERE n.user_id = $user_id
                DELETE n
                RETURN count(n) as count
            """, user_id=user_id)
            node_count = result.single()['count']
            print(f"🗑️  删除了 {node_count} 个节点")
            
            print(f"✅ 成功清除用户 {user_id} 的知识图谱")
            
    except Exception as e:
        print(f"❌ 清除失败: {e}")
    finally:
        driver.close()

if __name__ == '__main__':
    print(f"🚀 开始清除用户 {USER_ID} 的知识图谱...")
    clear_user_knowledge_graph(USER_ID)
    print("✅ 完成！")
