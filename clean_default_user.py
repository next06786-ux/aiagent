"""
清理 default_user 的测试数据
"""
import os
import shutil
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

def clean_neo4j_data():
    """清理Neo4j中的default_user数据"""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "lifeswarm123")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            # 删除default_user的所有节点和关系
            result = session.run("""
                MATCH (n {user_id: 'default_user'})
                DETACH DELETE n
                RETURN count(n) as deleted_count
            """)
            
            record = result.single()
            deleted_count = record['deleted_count'] if record else 0
            print(f"✅ 已从Neo4j删除 {deleted_count} 个default_user节点")
        
        driver.close()
        
    except Exception as e:
        print(f"❌ Neo4j清理失败: {e}")

def clean_rag_data():
    """清理RAG数据文件"""
    rag_dir = "backend/data/production_rag"
    
    if not os.path.exists(rag_dir):
        print(f"⚠️ RAG目录不存在: {rag_dir}")
        return
    
    files_to_delete = [
        "default_user_faiss.index",
        "default_user_metadata.json"
    ]
    
    deleted_count = 0
    for filename in files_to_delete:
        filepath = os.path.join(rag_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"✅ 已删除: {filepath}")
            deleted_count += 1
    
    print(f"✅ 已删除 {deleted_count} 个RAG文件")

def clean_simulation_data():
    """清理模拟数据文件"""
    sim_dir = "backend/data/simulations"
    
    if not os.path.exists(sim_dir):
        print(f"⚠️ 模拟目录不存在: {sim_dir}")
        return
    
    deleted_count = 0
    for filename in os.listdir(sim_dir):
        if "default_user" in filename:
            filepath = os.path.join(sim_dir, filename)
            os.remove(filepath)
            print(f"✅ 已删除: {filepath}")
            deleted_count += 1
    
    print(f"✅ 已删除 {deleted_count} 个模拟文件")

def main():
    print("=" * 60)
    print("开始清理 default_user 测试数据")
    print("=" * 60)
    
    # 1. 清理Neo4j数据
    print("\n[1/3] 清理Neo4j知识图谱数据...")
    clean_neo4j_data()
    
    # 2. 清理RAG数据
    print("\n[2/3] 清理RAG向量数据...")
    clean_rag_data()
    
    # 3. 清理模拟数据
    print("\n[3/3] 清理模拟数据...")
    clean_simulation_data()
    
    print("\n" + "=" * 60)
    print("✅ 清理完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
