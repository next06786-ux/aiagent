"""
初始化测试数据
为系统各层预填充数据，验证5层架构和知识图谱自动化构建
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from datetime import datetime, timedelta
from data_flow_orchestrator import DataFlowOrchestrator, PerceptionData
from multimodal.perception_layer import get_perception_layer
from agent.meta_agent import MetaAgent
from knowledge.neo4j_knowledge_graph import Neo4jKnowledgeGraph
from knowledge.information_knowledge_graph import InformationKnowledgeGraph
from learning.reinforcement_learner import ReinforcementLearner
from multimodal.enhanced_fusion import EnhancedMultimodalFusion
from learning.production_rag_system import ProductionRAGSystem


# 测试数据集 - 模拟一周的用户活动
TEST_DATA = [
    # 第1天 - 周一工作日
    {
        "text": "早上7点起床，准备去公司上班",
        "sensors": {"steps": 1200, "heart_rate": 72, "activity": "walking"},
        "time_offset": -6  # 6天前
    },
    {
        "text": "上午完成了项目报告，感觉很有成就感",
        "sensors": {"steps": 3500, "heart_rate": 75, "activity": "sitting"},
        "time_offset": -6
    },
    {
        "text": "中午和同事一起吃饭，聊了新项目的想法",
        "sensors": {"steps": 5200, "heart_rate": 78, "activity": "walking"},
        "time_offset": -6
    },
    {
        "text": "下午开会讨论产品设计，有点累",
        "sensors": {"steps": 5800, "heart_rate": 82, "activity": "sitting"},
        "time_offset": -6
    },
    {
        "text": "晚上去健身房跑步，跑了5公里",
        "sensors": {"steps": 12000, "heart_rate": 145, "activity": "running"},
        "time_offset": -6
    },
    
    # 第2天 - 周二
    {
        "text": "今天学习了Python新特性，做了笔记",
        "sensors": {"steps": 2100, "heart_rate": 70, "activity": "sitting"},
        "time_offset": -5
    },
    {
        "text": "下午参加技术分享会，学到很多东西",
        "sensors": {"steps": 4500, "heart_rate": 75, "activity": "sitting"},
        "time_offset": -5
    },
    {
        "text": "晚上在图书馆看书，准备考试",
        "sensors": {"steps": 6200, "heart_rate": 68, "activity": "sitting"},
        "time_offset": -5
    },
    
    # 第3天 - 周三
    {
        "text": "早上做了瑜伽，感觉身心放松",
        "sensors": {"steps": 800, "heart_rate": 65, "activity": "exercising"},
        "time_offset": -4
    },
    {
        "text": "上午处理邮件和文档，工作效率很高",
        "sensors": {"steps": 3200, "heart_rate": 72, "activity": "sitting"},
        "time_offset": -4
    },
    {
        "text": "中午在公司附近的咖啡馆工作",
        "sensors": {"steps": 4800, "heart_rate": 70, "activity": "sitting"},
        "time_offset": -4
    },
    {
        "text": "下午完成了代码审查，发现了几个bug",
        "sensors": {"steps": 5100, "heart_rate": 78, "activity": "sitting"},
        "time_offset": -4
    },
    
    # 第4天 - 周四
    {
        "text": "今天压力有点大，项目deadline快到了",
        "sensors": {"steps": 2800, "heart_rate": 88, "activity": "sitting"},
        "time_offset": -3
    },
    {
        "text": "加班到晚上9点，终于完成了核心功能",
        "sensors": {"steps": 4200, "heart_rate": 85, "activity": "sitting"},
        "time_offset": -3
    },
    {
        "text": "回家路上买了宵夜，花了50元",
        "sensors": {"steps": 6500, "heart_rate": 75, "activity": "walking"},
        "time_offset": -3
    },
    
    # 第5天 - 周五
    {
        "text": "项目成功上线，团队一起庆祝",
        "sensors": {"steps": 5800, "heart_rate": 80, "activity": "walking"},
        "time_offset": -2
    },
    {
        "text": "下午和朋友约了看电影，很开心",
        "sensors": {"steps": 8200, "heart_rate": 72, "activity": "walking"},
        "time_offset": -2
    },
    {
        "text": "晚上聚餐，消费了200元",
        "sensors": {"steps": 9500, "heart_rate": 75, "activity": "sitting"},
        "time_offset": -2
    },
    
    # 第6天 - 周六
    {
        "text": "周末睡到自然醒，感觉很舒服",
        "sensors": {"steps": 500, "heart_rate": 62, "activity": "sitting"},
        "time_offset": -1
    },
    {
        "text": "上午去公园跑步，天气很好",
        "sensors": {"steps": 8500, "heart_rate": 135, "activity": "running"},
        "time_offset": -1
    },
    {
        "text": "下午在家学习新技术，看了几个教程",
        "sensors": {"steps": 9200, "heart_rate": 68, "activity": "sitting"},
        "time_offset": -1
    },
    {
        "text": "晚上做饭，尝试了新菜谱",
        "sensors": {"steps": 10500, "heart_rate": 70, "activity": "walking"},
        "time_offset": -1
    },
    
    # 第7天 - 周日（今天）
    {
        "text": "早上整理房间，打扫卫生",
        "sensors": {"steps": 2200, "heart_rate": 75, "activity": "walking"},
        "time_offset": 0
    },
    {
        "text": "上午复习数学，完成了作业",
        "sensors": {"steps": 2800, "heart_rate": 70, "activity": "sitting"},
        "time_offset": 0
    },
    {
        "text": "下午和家人视频通话，聊了很久",
        "sensors": {"steps": 3100, "heart_rate": 68, "activity": "sitting"},
        "time_offset": 0
    },
]


async def init_test_data():
    """初始化测试数据"""
    
    print("\n" + "="*70)
    print("  初始化测试数据 - 为系统各层预填充数据")
    print("="*70 + "\n")
    
    user_id = "demo_user"
    
    # 1. 初始化系统组件
    print("📦 初始化系统组件...")
    
    try:
        perception_layer = get_perception_layer()
        meta_agent = MetaAgent()
        knowledge_graph = Neo4jKnowledgeGraph(user_id)
        info_kg = InformationKnowledgeGraph(user_id)
        learner = ReinforcementLearner(user_id, enable_rag=False)
        fusion = EnhancedMultimodalFusion()
        rag_system = ProductionRAGSystem(user_id, use_gpu=False)
        
        print("  ✓ 所有组件已初始化\n")
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        print("提示: 请确保Neo4j已启动")
        return
    
    # 2. 创建数据流协调器
    print("🔧 创建数据流协调器...")
    orchestrator = DataFlowOrchestrator(
        perception_layer=perception_layer,
        meta_agent=meta_agent,
        knowledge_graph=knowledge_graph,
        reinforcement_learner=learner,
        multimodal_fusion=fusion,
        rag_system=rag_system,
        info_kg_system=info_kg
    )
    print("  ✓ 协调器已就绪\n")
    
    # 3. 清空旧数据
    print("🧹 清空旧数据...")
    info_kg.clear_user_data()
    knowledge_graph.clear_user_data()
    print("  ✓ 已清空\n")
    
    # 4. 批量导入测试数据
    print("📥 开始导入测试数据...")
    print(f"   共 {len(TEST_DATA)} 条记录\n")
    
    base_time = datetime.now()
    
    for i, data in enumerate(TEST_DATA, 1):
        # 计算时间戳
        timestamp = base_time + timedelta(days=data['time_offset'])
        
        # 创建感知数据
        perception_data = PerceptionData(
            user_id=user_id,
            text=data['text'],
            sensors=data.get('sensors'),
            timestamp=timestamp
        )
        
        print(f"[{i}/{len(TEST_DATA)}] 处理: {data['text'][:30]}...")
        
        # 处理数据（会自动构建知识图谱）
        try:
            result = await orchestrator.process_perception_data(perception_data)
            print(f"      ✓ 完成\n")
        except Exception as e:
            print(f"      ⚠️ 处理失败: {e}\n")
            continue
    
    # 5. 显示最终统计
    print("\n" + "="*70)
    print("  数据导入完成 - 系统统计")
    print("="*70 + "\n")
    
    # 信息知识图谱统计
    info_stats = info_kg.get_statistics()
    print("📊 信息知识图谱:")
    print(f"   信息节点: {info_stats['information']['total']} 个")
    print(f"     - 实体: {info_stats['information']['by_type'].get('entity', 0)} 个")
    print(f"     - 事件: {info_stats['information']['by_type'].get('event', 0)} 个")
    print(f"     - 概念: {info_stats['information']['by_type'].get('concept', 0)} 个")
    print(f"   来源记录: {info_stats['sources']['total']} 个")
    print(f"   关系连接: {info_stats['relationships']['total']} 个")
    
    print(f"\n   按生活领域分布:")
    for category, count in sorted(info_stats['information']['by_category'].items(), 
                                   key=lambda x: x[1], reverse=True):
        print(f"     - {category}: {count} 个")
    
    # 传统知识图谱统计
    kg_stats = knowledge_graph.get_statistics()
    print(f"\n📊 传统知识图谱:")
    print(f"   实体节点: {kg_stats['entities']['total']} 个")
    print(f"   关系连接: {kg_stats['relations']['total']} 个")
    
    # RAG记忆统计
    print(f"\n📊 RAG记忆系统:")
    print(f"   已存储 {len(TEST_DATA)} 条记忆")
    
    # 强化学习统计
    learner_stats = learner.get_statistics()
    print(f"\n📊 强化学习系统:")
    print(f"   训练轮次: {learner_stats['total_episodes']}")
    print(f"   平均奖励: {learner_stats['average_reward']:.2f}")
    
    print("\n" + "="*70)
    print("  ✅ 测试数据初始化完成！")
    print("  现在可以通过API或前端测试系统各层功能")
    print("="*70 + "\n")
    
    # 6. 展示一些示例查询
    print("🔍 示例查询:\n")
    
    # 搜索"学习"相关信息
    print("1. 搜索关键词: '学习'")
    results = info_kg.search_information(keyword="学习", limit=3)
    for r in results:
        print(f"   - [{r['type']}] {r['name']} ({r['category']})")
    
    # 搜索"运动"相关信息
    print("\n2. 搜索关键词: '运动'")
    results = info_kg.search_information(keyword="运动", limit=3)
    for r in results:
        print(f"   - [{r['type']}] {r['name']} ({r['category']})")
    
    # 搜索"工作"相关信息
    print("\n3. 搜索关键词: '工作'")
    results = info_kg.search_information(keyword="工作", limit=3)
    for r in results:
        print(f"   - [{r['type']}] {r['name']} ({r['category']})")
    
    print("\n")
    
    # 清理
    info_kg.close()
    knowledge_graph.close()


if __name__ == "__main__":
    asyncio.run(init_test_data())
