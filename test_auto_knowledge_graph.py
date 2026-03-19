"""
测试自动化信息知识图谱生成
验证从数据采集到图谱构建的完整流程
"""
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
from datetime import datetime
from data_flow_orchestrator import DataFlowOrchestrator, PerceptionData
from multimodal.perception_layer import get_perception_layer
from agent.meta_agent import MetaAgent
from knowledge.neo4j_knowledge_graph import Neo4jKnowledgeGraph
from knowledge.information_knowledge_graph import InformationKnowledgeGraph
from learning.reinforcement_learner import ReinforcementLearner
from multimodal.enhanced_fusion import EnhancedMultimodalFusion
from learning.production_rag_system import ProductionRAGSystem


async def test_auto_knowledge_graph():
    """测试自动化知识图谱生成"""
    
    print("\n" + "="*70)
    print("  测试：自动化信息知识图谱生成")
    print("="*70 + "\n")
    
    user_id = "test_user_kg"
    
    # 1. 初始化系统组件
    print("📦 初始化系统组件...")
    
    try:
        perception_layer = get_perception_layer()
        print("  ✓ 感知层")
        
        meta_agent = MetaAgent()  # 不需要传入user_id
        print("  ✓ 元智能体")
        
        knowledge_graph = Neo4jKnowledgeGraph(user_id)
        print("  ✓ 传统知识图谱")
        
        info_kg = InformationKnowledgeGraph(user_id)
        print("  ✓ 信息知识图谱")
        
        learner = ReinforcementLearner(user_id, enable_rag=False)
        print("  ✓ 强化学习器")
        
        fusion = EnhancedMultimodalFusion()
        print("  ✓ 多模态融合")
        
        rag_system = ProductionRAGSystem(user_id, use_gpu=False)
        print("  ✓ RAG记忆系统")
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        print("提示: 请确保Neo4j已启动")
        return
    
    # 2. 创建数据流协调器
    print("\n🔧 创建数据流协调器...")
    orchestrator = DataFlowOrchestrator(
        perception_layer=perception_layer,
        meta_agent=meta_agent,
        knowledge_graph=knowledge_graph,
        reinforcement_learner=learner,
        multimodal_fusion=fusion,
        rag_system=rag_system,
        info_kg_system=info_kg  # 传入信息知识图谱
    )
    print("  ✓ 协调器已就绪\n")
    
    # 3. 清空测试用户的旧数据
    print("🧹 清空旧数据...")
    info_kg.clear_user_data()
    print("  ✓ 已清空\n")
    
    # 4. 测试场景1：对话数据
    print("\n" + "="*70)
    print("  场景1：对话数据 - '今天完成了数学作业，感觉很有成就感'")
    print("="*70 + "\n")
    
    perception_data_1 = PerceptionData(
        user_id=user_id,
        text="今天完成了数学作业，感觉很有成就感",
        timestamp=datetime.now()
    )
    
    result_1 = await orchestrator.process_perception_data(perception_data_1)
    print("\n✅ 场景1处理完成")
    
    # 立即查看图谱统计，不等待完整处理
    stats_1 = info_kg.get_statistics()
    print(f"\n📊 场景1后的图谱: {stats_1['information']['total']}个信息节点\n")
    
    # 5. 测试场景2：传感器数据
    print("\n" + "="*70)
    print("  场景2：传感器数据 - 跑步运动")
    print("="*70 + "\n")
    
    perception_data_2 = PerceptionData(
        user_id=user_id,
        text="刚跑完步，感觉很累但很爽",
        sensors={
            "steps": 8500,
            "heart_rate": 145,
            "accelerometer": {"x": 0.5, "y": 0.3, "z": 9.8},
            "activity": "running"
        },
        timestamp=datetime.now()
    )
    
    result_2 = await orchestrator.process_perception_data(perception_data_2)
    print("\n✅ 场景2处理完成\n")
    
    # 6. 测试场景3：混合数据
    print("\n" + "="*70)
    print("  场景3：混合数据 - 对话+传感器")
    print("="*70 + "\n")
    
    perception_data_3 = PerceptionData(
        user_id=user_id,
        text="在图书馆学习，准备考试",
        sensors={
            "steps": 1200,
            "heart_rate": 72,
            "light": 450,
            "activity": "sitting"
        },
        timestamp=datetime.now()
    )
    
    result_3 = await orchestrator.process_perception_data(perception_data_3)
    print("\n✅ 场景3处理完成\n")
    
    # 7. 查看最终图谱统计
    print("\n" + "="*70)
    print("  最终知识图谱统计")
    print("="*70 + "\n")
    
    stats = info_kg.get_statistics()
    
    print(f"📊 信息节点统计:")
    print(f"  总计: {stats['information']['total']} 个")
    print(f"  按类型:")
    for info_type, count in stats['information']['by_type'].items():
        print(f"    - {info_type}: {count} 个")
    print(f"  按领域:")
    for category, count in stats['information']['by_category'].items():
        print(f"    - {category}: {count} 个")
    
    print(f"\n📁 来源记录统计:")
    print(f"  总计: {stats['sources']['total']} 个")
    for source_type, count in stats['sources']['by_type'].items():
        print(f"    - {source_type}: {count} 个")
    
    print(f"\n🔗 关系统计:")
    print(f"  总计: {stats['relationships']['total']} 个")
    for rel_type, count in stats['relationships']['by_type'].items():
        print(f"    - {rel_type}: {count} 个")
    
    # 8. 测试信息检索
    print("\n" + "="*70)
    print("  测试信息检索")
    print("="*70 + "\n")
    
    # 搜索"学习"相关信息
    print("🔍 搜索关键词: '学习'")
    search_results = info_kg.search_information(
        keyword="学习",
        limit=5
    )
    print(f"  找到 {len(search_results)} 个相关信息:")
    for i, info in enumerate(search_results, 1):
        print(f"    {i}. [{info.get('type')}] {info.get('name')} - {info.get('category')}")
        print(f"       置信度: {info.get('confidence', 0):.2f}, 提及次数: {info.get('mention_count', 0)}")
    
    # 搜索"运动"相关信息
    print("\n🔍 搜索关键词: '运动'")
    search_results = info_kg.search_information(
        keyword="运动",
        limit=5
    )
    print(f"  找到 {len(search_results)} 个相关信息:")
    for i, info in enumerate(search_results, 1):
        print(f"    {i}. [{info.get('type')}] {info.get('name')} - {info.get('category')}")
        print(f"       置信度: {info.get('confidence', 0):.2f}, 提及次数: {info.get('mention_count', 0)}")
    
    # 9. 测试溯源功能
    if search_results:
        print("\n" + "="*70)
        print("  测试溯源功能")
        print("="*70 + "\n")
        
        first_info = search_results[0]
        info_name = first_info.get('name')
        print(f"🔍 查询信息 '{info_name}' 的来源:")
        
        sources = info_kg.get_information_sources(info_name)
        print(f"  找到 {len(sources)} 个来源:")
        for i, src in enumerate(sources, 1):
            source_data = src['source']
            print(f"    {i}. [{source_data.get('type')}] {source_data.get('source_id')}")
            print(f"       时间: {source_data.get('timestamp')}")
            print(f"       关系: {src['relation_type']}, 置信度: {src['confidence']:.2f}")
    
    # 10. 导出图谱
    print("\n" + "="*70)
    print("  导出知识图谱")
    print("="*70 + "\n")
    
    export_data = info_kg.export()
    print(f"📤 导出数据:")
    print(f"  信息节点: {len(export_data['information'])} 个")
    print(f"  来源记录: {len(export_data['sources'])} 个")
    print(f"  关系连接: {len(export_data['relationships'])} 个")
    
    # 显示部分信息节点
    if export_data['information']:
        print(f"\n  示例信息节点 (前3个):")
        for i, info in enumerate(export_data['information'][:3], 1):
            print(f"    {i}. {info.get('name')} ({info.get('type')})")
            print(f"       类别: {info.get('category')}, 置信度: {info.get('confidence', 0):.2f}")
    
    print("\n" + "="*70)
    print("  ✅ 测试完成！自动化信息知识图谱生成成功")
    print("="*70 + "\n")
    
    # 清理
    info_kg.close()
    knowledge_graph.close()


if __name__ == "__main__":
    asyncio.run(test_auto_knowledge_graph())
