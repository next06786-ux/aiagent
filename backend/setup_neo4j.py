"""
Neo4j 数据库初始化脚本
创建索引和约束，优化查询性能
"""
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()


def setup_neo4j():
    """初始化 Neo4j 数据库"""
    
    # 读取配置
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "lifeswarm123")
    
    print("="*60)
    print("Neo4j 数据库初始化")
    print("="*60)
    print(f"URI: {uri}")
    print(f"User: {user}")
    
    try:
        # 连接数据库
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        print("✅ 连接成功\n")
        
        with driver.session() as session:
            # 创建索引和约束
            constraints = [
                # 用户ID + 名称唯一约束
                "CREATE CONSTRAINT user_entity_unique IF NOT EXISTS FOR (e:Entity) REQUIRE (e.user_id, e.name) IS UNIQUE",
                "CREATE CONSTRAINT user_person_unique IF NOT EXISTS FOR (p:Person) REQUIRE (p.user_id, p.name) IS UNIQUE",
                "CREATE CONSTRAINT user_event_unique IF NOT EXISTS FOR (e:Event) REQUIRE (e.user_id, e.name) IS UNIQUE",
                "CREATE CONSTRAINT user_location_unique IF NOT EXISTS FOR (l:Location) REQUIRE (l.user_id, l.name) IS UNIQUE",
                "CREATE CONSTRAINT user_object_unique IF NOT EXISTS FOR (o:Object) REQUIRE (o.user_id, o.name) IS UNIQUE",
                "CREATE CONSTRAINT user_photo_unique IF NOT EXISTS FOR (p:Photo) REQUIRE (p.user_id, p.name) IS UNIQUE",
            ]
            
            indexes = [
                # 用户ID索引 - Neo4j 2026 语法
                "CREATE INDEX user_id_index IF NOT EXISTS FOR (n:Entity) ON (n.user_id)",
                "CREATE INDEX user_id_person_index IF NOT EXISTS FOR (n:Person) ON (n.user_id)",
                "CREATE INDEX user_id_event_index IF NOT EXISTS FOR (n:Event) ON (n.user_id)",
                "CREATE INDEX user_id_location_index IF NOT EXISTS FOR (n:Location) ON (n.user_id)",
                "CREATE INDEX user_id_object_index IF NOT EXISTS FOR (n:Object) ON (n.user_id)",
                "CREATE INDEX user_id_photo_index IF NOT EXISTS FOR (n:Photo) ON (n.user_id)",
                # 时间戳索引
                "CREATE INDEX timestamp_entity_index IF NOT EXISTS FOR (n:Entity) ON (n.timestamp)",
                "CREATE INDEX timestamp_event_index IF NOT EXISTS FOR (n:Event) ON (n.timestamp)",
                "CREATE INDEX timestamp_photo_index IF NOT EXISTS FOR (n:Photo) ON (n.timestamp)",
            ]
            
            print("创建约束...")
            for constraint in constraints:
                try:
                    session.run(constraint)
                    print(f"  ✅ {constraint.split('FOR')[1].split('REQUIRE')[0].strip()}")
                except Exception as e:
                    print(f"  ⚠️  约束已存在或创建失败: {e}")
            
            print("\n创建索引...")
            for index in indexes:
                try:
                    session.run(index)
                    print(f"  ✅ {index.split('FOR')[1].split('ON')[0].strip()}")
                except Exception as e:
                    print(f"  ⚠️  索引已存在或创建失败: {e}")
            
            # 验证 - 使用 SHOW 命令（Neo4j 2026）
            print("\n验证数据库...")
            try:
                result = session.run("SHOW INDEXES")
                index_count = len(list(result))
                print(f"  索引数量: {index_count}")
            except Exception as e:
                print(f"  ⚠️  无法查询索引: {e}")
            
            try:
                result = session.run("SHOW CONSTRAINTS")
                constraint_count = len(list(result))
                print(f"  约束数量: {constraint_count}")
            except Exception as e:
                print(f"  ⚠️  无法查询约束: {e}")
            
            # 测试写入
            print("\n测试写入...")
            session.run("""
                MERGE (u:User {user_id: 'test_user', name: 'Test User'})
                SET u.created_at = datetime()
                RETURN u
            """)
            print("  ✅ 测试节点创建成功")
            
            # 清理测试数据
            session.run("MATCH (u:User {user_id: 'test_user'}) DELETE u")
            print("  ✅ 测试数据清理完成")
        
        driver.close()
        
        print("\n" + "="*60)
        print("✅ Neo4j 初始化完成")
        print("="*60)
        print("\n可以开始使用 Neo4j 知识图谱了！")
        print("浏览器访问: http://localhost:7474")
        print(f"用户名: {user}")
        print(f"密码: {password}")
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        print("\n请检查:")
        print("1. Neo4j 是否已启动")
        print("2. 连接配置是否正确 (.env 文件)")
        print("3. 用户名密码是否正确")
        print("\n参考安装指南: backend/INSTALL_NEO4J.md")
        return False
    
    return True


if __name__ == "__main__":
    setup_neo4j()
