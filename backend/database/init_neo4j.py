"""
Neo4j数据库初始化脚本
重新规划数据库结构，清除旧数据
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()


class Neo4jInitializer:
    """Neo4j数据库初始化器"""
    
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "lifeswarm123")
        
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        print(f"✅ 连接到Neo4j: {uri}")
    
    def close(self):
        if self.driver:
            self.driver.close()
    
    def clear_all_data(self):
        """清除所有数据（谨慎操作！）"""
        print("\n⚠️  警告：即将删除所有Neo4j数据！")
        confirm = input("请输入 'YES' 确认删除: ")
        
        if confirm != "YES":
            print("❌ 取消操作")
            return False
        
        with self.driver.session() as session:
            # 删除所有节点和关系
            print("🗑️  删除所有节点和关系...")
            session.run("MATCH (n) DETACH DELETE n")
            
            # 删除所有约束
            print("🗑️  删除所有约束...")
            constraints = session.run("SHOW CONSTRAINTS").data()
            for constraint in constraints:
                constraint_name = constraint.get('name')
                if constraint_name:
                    try:
                        session.run(f"DROP CONSTRAINT {constraint_name}")
                    except Exception as e:
                        print(f"   跳过约束 {constraint_name}: {e}")
            
            # 删除所有索引
            print("🗑️  删除所有索引...")
            indexes = session.run("SHOW INDEXES").data()
            for index in indexes:
                index_name = index.get('name')
                if index_name and not index_name.startswith('constraint_'):
                    try:
                        session.run(f"DROP INDEX {index_name}")
                    except Exception as e:
                        print(f"   跳过索引 {index_name}: {e}")
        
        print("✅ 所有数据已清除")
        return True
    
    def create_constraints(self):
        """创建约束"""
        print("\n📋 创建约束...")
        
        constraints = [
            # User节点
            "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
            
            # Information节点
            "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (ev:Event) REQUIRE ev.id IS UNIQUE",
            "CREATE CONSTRAINT concept_id_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT pattern_id_unique IF NOT EXISTS FOR (p:Pattern) REQUIRE p.id IS UNIQUE",
            
            # Source节点
            "CREATE CONSTRAINT source_id_unique IF NOT EXISTS FOR (s:Source) REQUIRE s.source_id IS UNIQUE",
            
            # Career节点
            "CREATE CONSTRAINT job_id_unique IF NOT EXISTS FOR (j:Job) REQUIRE j.job_id IS UNIQUE",
            "CREATE CONSTRAINT company_id_unique IF NOT EXISTS FOR (co:Company) REQUIRE co.company_id IS UNIQUE",
            
            # Education节点
            "CREATE CONSTRAINT school_id_unique IF NOT EXISTS FOR (sc:School) REQUIRE sc.school_id IS UNIQUE",
            "CREATE CONSTRAINT major_id_unique IF NOT EXISTS FOR (m:Major) REQUIRE m.major_id IS UNIQUE",
            "CREATE CONSTRAINT professor_id_unique IF NOT EXISTS FOR (pr:Professor) REQUIRE pr.professor_id IS UNIQUE",
        ]
        
        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    print(f"   ✓ {constraint.split('FOR')[1].split('REQUIRE')[0].strip()}")
                except Exception as e:
                    print(f"   ✗ 失败: {e}")
        
        print("✅ 约束创建完成")
    
    def create_indexes(self):
        """创建索引"""
        print("\n📋 创建索引...")
        
        indexes = [
            # User索引
            "CREATE INDEX user_name_index IF NOT EXISTS FOR (u:User) ON (u.name)",
            
            # Entity索引
            "CREATE INDEX entity_user_id_index IF NOT EXISTS FOR (e:Entity) ON (e.user_id)",
            "CREATE INDEX entity_category_index IF NOT EXISTS FOR (e:Entity) ON (e.category)",
            "CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            
            # Event索引
            "CREATE INDEX event_user_id_index IF NOT EXISTS FOR (ev:Event) ON (ev.user_id)",
            "CREATE INDEX event_category_index IF NOT EXISTS FOR (ev:Event) ON (ev.category)",
            
            # Concept索引
            "CREATE INDEX concept_user_id_index IF NOT EXISTS FOR (c:Concept) ON (c.user_id)",
            "CREATE INDEX concept_category_index IF NOT EXISTS FOR (c:Concept) ON (c.category)",
            
            # Pattern索引
            "CREATE INDEX pattern_user_id_index IF NOT EXISTS FOR (p:Pattern) ON (p.user_id)",
            
            # Source索引
            "CREATE INDEX source_user_id_index IF NOT EXISTS FOR (s:Source) ON (s.user_id)",
            "CREATE INDEX source_type_index IF NOT EXISTS FOR (s:Source) ON (s.type)",
            
            # Job索引
            "CREATE INDEX job_position_name_index IF NOT EXISTS FOR (j:Job) ON (j.position_name)",
            "CREATE INDEX job_city_index IF NOT EXISTS FOR (j:Job) ON (j.city)",
            "CREATE INDEX job_company_name_index IF NOT EXISTS FOR (j:Job) ON (j.company_name)",
            "CREATE INDEX job_category_index IF NOT EXISTS FOR (j:Job) ON (j.category)",
            
            # Company索引
            "CREATE INDEX company_name_index IF NOT EXISTS FOR (co:Company) ON (co.name)",
            
            # School索引
            "CREATE INDEX school_name_index IF NOT EXISTS FOR (sc:School) ON (sc.name)",
            "CREATE INDEX school_location_index IF NOT EXISTS FOR (sc:School) ON (sc.location)",
            "CREATE INDEX school_tier_index IF NOT EXISTS FOR (sc:School) ON (sc.tier)",
            "CREATE INDEX school_category_index IF NOT EXISTS FOR (sc:School) ON (sc.classification_category)",
            
            # Major索引
            "CREATE INDEX major_name_index IF NOT EXISTS FOR (m:Major) ON (m.name)",
            
            # Professor索引
            "CREATE INDEX professor_name_index IF NOT EXISTS FOR (pr:Professor) ON (pr.name)",
        ]
        
        with self.driver.session() as session:
            for index in indexes:
                try:
                    session.run(index)
                    print(f"   ✓ {index.split('FOR')[1].split('ON')[0].strip()}")
                except Exception as e:
                    print(f"   ✗ 失败: {e}")
        
        print("✅ 索引创建完成")
    
    def create_sample_data(self):
        """创建示例数据 - 完整的用户知识图谱"""
        print("\n📋 创建示例数据...")
        
        with self.driver.session() as session:
            # 1. 创建示例用户
            session.run("""
                CREATE (u:User {
                    user_id: "user_demo",
                    name: "张三",
                    age: 25,
                    gender: "男",
                    location: "北京",
                    education_level: "本科",
                    major: "计算机科学",
                    work_years: 3,
                    current_position: "Python工程师",
                    skills: ["Python", "Django", "PostgreSQL"],
                    interests: ["编程", "阅读", "旅行"],
                    created_at: datetime(),
                    updated_at: datetime()
                })
            """)
            print("   ✓ 创建示例用户")
            
            # 2. 创建Source节点（对话来源）
            session.run("""
                CREATE (s1:Source {
                    source_id: "conv_001",
                    user_id: "user_demo",
                    type: "Conversation",
                    content: "我大学同学李四现在在阿里工作，做算法工程师，年薪50万",
                    timestamp: datetime('2026-04-15T10:30:00'),
                    metadata: '{"session_id": "session_123", "turn": 5}',
                    created_at: datetime()
                }),
                (s2:Source {
                    source_id: "conv_002",
                    user_id: "user_demo",
                    type: "Conversation",
                    content: "我在考虑申请清华大学的计算机系研究生",
                    timestamp: datetime('2026-04-16T14:20:00'),
                    metadata: '{"session_id": "session_124", "turn": 3}',
                    created_at: datetime()
                }),
                (s3:Source {
                    source_id: "conv_003",
                    user_id: "user_demo",
                    type: "Conversation",
                    content: "字节跳动在招Python后端工程师，要求熟悉Django和微服务",
                    timestamp: datetime('2026-04-17T09:15:00'),
                    metadata: '{"session_id": "session_125", "turn": 2}',
                    created_at: datetime()
                })
            """)
            print("   ✓ 创建示例来源节点")
            
            # 3. 创建Entity节点（人物）
            session.run("""
                CREATE (e1:Entity {
                    id: "entity_person_001",
                    user_id: "user_demo",
                    name: "李四",
                    type: "Person",
                    category: "friends",
                    description: "大学同学，现在在阿里工作",
                    attributes: '{"role": "同学", "company": "阿里巴巴", "position": "算法工程师", "salary": "50万"}',
                    confidence: 0.95,
                    weight: 0.8,
                    influence_score: 0.7,
                    created_at: datetime(),
                    updated_at: datetime(),
                    mention_count: 1
                })
            """)
            print("   ✓ 创建人物实体节点")
            
            # 4. 创建Entity节点（职位）
            session.run("""
                CREATE (e2:Entity {
                    id: "entity_job_001",
                    user_id: "user_demo",
                    name: "Python后端工程师",
                    type: "Job",
                    category: "position",
                    description: "字节跳动招聘的后端岗位",
                    attributes: '{"company": "字节跳动", "salary": "30k-50k", "location": "北京", "requirements": ["Python", "Django", "微服务"], "experience": "3-5年"}',
                    confidence: 0.92,
                    weight: 0.75,
                    created_at: datetime(),
                    updated_at: datetime(),
                    mention_count: 1
                })
            """)
            print("   ✓ 创建职位实体节点")
            
            # 5. 创建Entity节点（学校）
            session.run("""
                CREATE (e3:Entity {
                    id: "entity_school_001",
                    user_id: "user_demo",
                    name: "清华大学",
                    type: "School",
                    category: "university",
                    description: "计算机系研究生项目",
                    attributes: '{"major": "计算机科学", "level": "master", "location": "北京", "tier": "985", "ranking": 1}',
                    confidence: 0.98,
                    weight: 0.9,
                    created_at: datetime(),
                    updated_at: datetime(),
                    mention_count: 1
                })
            """)
            print("   ✓ 创建学校实体节点")
            
            # 6. 创建Concept节点（技能）
            session.run("""
                CREATE (c1:Concept {
                    id: "concept_skill_001",
                    user_id: "user_demo",
                    name: "Python编程",
                    type: "Skill",
                    category: "programming",
                    description: "熟练使用Python进行后端开发",
                    level: "高级",
                    confidence: 0.98,
                    weight: 0.95,
                    created_at: datetime(),
                    updated_at: datetime(),
                    mention_count: 3
                }),
                (c2:Concept {
                    id: "concept_skill_002",
                    user_id: "user_demo",
                    name: "Django框架",
                    type: "Skill",
                    category: "framework",
                    description: "使用Django开发Web应用",
                    level: "中级",
                    confidence: 0.90,
                    weight: 0.80,
                    created_at: datetime(),
                    updated_at: datetime(),
                    mention_count: 2
                })
            """)
            print("   ✓ 创建技能概念节点")
            
            # 7. 创建Event节点（面试）
            session.run("""
                CREATE (ev1:Event {
                    id: "event_001",
                    user_id: "user_demo",
                    name: "字节跳动面试",
                    type: "Interview",
                    category: "career",
                    description: "后端工程师岗位二面",
                    start_time: datetime('2026-04-20T14:00:00'),
                    location: "北京字节跳动总部",
                    participants: ["面试官王五", "我"],
                    confidence: 0.92,
                    created_at: datetime(),
                    updated_at: datetime()
                })
            """)
            print("   ✓ 创建事件节点")
            
            # 8. 创建Pattern节点（偏好模式）
            session.run("""
                CREATE (p1:Pattern {
                    id: "pattern_001",
                    user_id: "user_demo",
                    name: "偏好大厂工作",
                    type: "Preference",
                    category: "career",
                    description: "用户在职业选择中倾向于选择大型互联网公司",
                    frequency: 3,
                    confidence: 0.88,
                    identified_at: datetime(),
                    evidence: ["conv_001", "conv_003"],
                    created_at: datetime()
                })
            """)
            print("   ✓ 创建模式节点")
            
            # 9. 创建关系：信息溯源
            session.run("""
                MATCH (e1:Entity {id: "entity_person_001"}), (s1:Source {source_id: "conv_001"})
                CREATE (e1)-[:EXTRACTED_FROM {
                    extraction_method: "LLM",
                    confidence: 0.95,
                    created_at: datetime()
                }]->(s1)
            """)
            session.run("""
                MATCH (e2:Entity {id: "entity_job_001"}), (s3:Source {source_id: "conv_003"})
                CREATE (e2)-[:EXTRACTED_FROM {
                    extraction_method: "LLM",
                    confidence: 0.92,
                    created_at: datetime()
                }]->(s3)
            """)
            session.run("""
                MATCH (e3:Entity {id: "entity_school_001"}), (s2:Source {source_id: "conv_002"})
                CREATE (e3)-[:EXTRACTED_FROM {
                    extraction_method: "LLM",
                    confidence: 0.98,
                    created_at: datetime()
                }]->(s2)
            """)
            print("   ✓ 创建信息溯源关系")
            
            # 10. 创建关系：用户关系
            session.run("""
                MATCH (u:User {user_id: "user_demo"}), (e1:Entity {id: "entity_person_001"})
                CREATE (u)-[:KNOWS {
                    relationship_type: "friend",
                    closeness: 0.8,
                    since: datetime('2020-09-01'),
                    created_at: datetime()
                }]->(e1)
            """)
            session.run("""
                MATCH (u:User {user_id: "user_demo"}), (e2:Entity {id: "entity_job_001"})
                CREATE (u)-[:INTERESTED_IN {
                    interest_level: 0.9,
                    timestamp: datetime(),
                    created_at: datetime()
                }]->(e2)
            """)
            session.run("""
                MATCH (u:User {user_id: "user_demo"}), (e3:Entity {id: "entity_school_001"})
                CREATE (u)-[:INTERESTED_IN {
                    interest_level: 0.85,
                    timestamp: datetime(),
                    created_at: datetime()
                }]->(e3)
            """)
            session.run("""
                MATCH (u:User {user_id: "user_demo"}), (c1:Concept {id: "concept_skill_001"})
                CREATE (u)-[:HAS_PROFILE {
                    since: datetime('2021-01-01'),
                    confidence: 0.98,
                    created_at: datetime()
                }]->(c1)
            """)
            session.run("""
                MATCH (u:User {user_id: "user_demo"}), (c2:Concept {id: "concept_skill_002"})
                CREATE (u)-[:HAS_PROFILE {
                    since: datetime('2022-06-01'),
                    confidence: 0.90,
                    created_at: datetime()
                }]->(c2)
            """)
            session.run("""
                MATCH (u:User {user_id: "user_demo"}), (p1:Pattern {id: "pattern_001"})
                CREATE (u)-[:EXHIBITS {
                    frequency: 3,
                    confidence: 0.88,
                    created_at: datetime()
                }]->(p1)
            """)
            print("   ✓ 创建用户关系")
            
            # 11. 创建关系：实体间关系
            session.run("""
                MATCH (e2:Entity {id: "entity_job_001"}), (c1:Concept {id: "concept_skill_001"})
                CREATE (e2)-[:REQUIRES {
                    importance: 0.9,
                    level: "高级",
                    created_at: datetime()
                }]->(c1)
            """)
            session.run("""
                MATCH (e2:Entity {id: "entity_job_001"}), (c2:Concept {id: "concept_skill_002"})
                CREATE (e2)-[:REQUIRES {
                    importance: 0.8,
                    level: "中级",
                    created_at: datetime()
                }]->(c2)
            """)
            print("   ✓ 创建实体间关系")
            
            # 12. 创建关系：来源归属
            session.run("""
                MATCH (s:Source {user_id: "user_demo"}), (u:User {user_id: "user_demo"})
                CREATE (s)-[:CREATED_BY {
                    timestamp: s.timestamp,
                    created_at: datetime()
                }]->(u)
            """)
            print("   ✓ 创建来源归属关系")
        
        print("✅ 示例数据创建完成")
    
    def verify_schema(self):
        """验证数据库架构"""
        print("\n📊 验证数据库架构...")
        
        with self.driver.session() as session:
            # 统计约束
            constraints = session.run("SHOW CONSTRAINTS").data()
            print(f"   ✓ 约束数量: {len(constraints)}")
            
            # 统计索引
            indexes = session.run("SHOW INDEXES").data()
            print(f"   ✓ 索引数量: {len(indexes)}")
            
            # 统计节点
            node_count = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
            print(f"   ✓ 节点数量: {node_count}")
            
            # 统计关系
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
            print(f"   ✓ 关系数量: {rel_count}")
            
            # 统计各类型节点
            node_types = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as type, count(n) as count
                ORDER BY count DESC
            """).data()
            
            if node_types:
                print("\n   节点类型分布:")
                for node_type in node_types:
                    print(f"      - {node_type['type']}: {node_type['count']}")
        
        print("\n✅ 数据库架构验证完成")
    
    def run_full_initialization(self):
        """运行完整初始化流程"""
        print("=" * 60)
        print("Neo4j 数据库初始化")
        print("=" * 60)
        
        try:
            # 1. 清除旧数据
            if not self.clear_all_data():
                return
            
            # 2. 创建约束
            self.create_constraints()
            
            # 3. 创建索引
            self.create_indexes()
            
            # 4. 创建示例数据
            create_sample = input("\n是否创建示例数据？(y/n): ")
            if create_sample.lower() == 'y':
                self.create_sample_data()
            
            # 5. 验证架构
            self.verify_schema()
            
            print("\n" + "=" * 60)
            print("✅ Neo4j 数据库初始化完成！")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ 初始化失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.close()


def main():
    """主函数"""
    initializer = Neo4jInitializer()
    initializer.run_full_initialization()


if __name__ == "__main__":
    main()
