#!/usr/bin/env python3
"""
测试知识图谱三个视图的连通性

验证：
1. people视图 - 人物关系图谱
2. signals视图 - 教育升学图谱
3. career视图 - 职业发展图谱
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.decision.future_os_service import FutureOSService


def test_people_view():
    """测试人物关系视图"""
    print("\n" + "="*60)
    print("测试 1: 人物关系视图 (people)")
    print("="*60)
    
    service = FutureOSService()
    try:
        result = service.get_graph_view(
            user_id="test_user_001",
            view_mode="people",
            question="我应该跳槽吗？"
        )
        
        print(f"✓ 视图模式: {result.get('view_mode')}")
        print(f"✓ 标题: {result.get('title')}")
        print(f"✓ 节点数: {len(result.get('nodes', []))}")
        print(f"✓ 连接数: {len(result.get('links', []))}")
        
        # 检查是否有"我"节点
        has_self = any(n.get('name') == '我' or n.get('is_self') for n in result.get('nodes', []))
        print(f"✓ 包含中心节点'我': {has_self}")
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_signals_view():
    """测试教育升学视图"""
    print("\n" + "="*60)
    print("测试 2: 教育升学视图 (signals)")
    print("="*60)
    
    service = FutureOSService()
    try:
        result = service.get_graph_view(
            user_id="test_user_001",
            view_mode="signals",
            question="我应该申请哪些学校？"
        )
        
        print(f"✓ 视图模式: {result.get('view_mode')}")
        print(f"✓ 标题: {result.get('title')}")
        print(f"✓ 节点数: {len(result.get('nodes', []))}")
        print(f"✓ 连接数: {len(result.get('links', []))}")
        
        # 检查是否有三层结构
        metadata = result.get('summary', {}).get('metadata', {})
        layer_info = metadata.get('layer_info', {})
        print(f"✓ 三层结构:")
        for layer_key, layer_data in layer_info.items():
            print(f"  - {layer_data.get('name')}: {layer_data.get('count')}个节点")
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_career_view():
    """测试职业发展视图"""
    print("\n" + "="*60)
    print("测试 3: 职业发展视图 (career)")
    print("="*60)
    
    service = FutureOSService()
    try:
        result = service.get_graph_view(
            user_id="test_user_001",
            view_mode="career",
            question="我想找Python工程师的工作"
        )
        
        print(f"✓ 视图模式: {result.get('view_mode')}")
        print(f"✓ 标题: {result.get('title')}")
        print(f"✓ 节点数: {len(result.get('nodes', []))}")
        print(f"✓ 连接数: {len(result.get('links', []))}")
        
        # 检查节点类型分布
        nodes = result.get('nodes', [])
        node_types = {}
        for node in nodes:
            node_type = node.get('type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        print(f"✓ 节点类型分布:")
        for node_type, count in node_types.items():
            print(f"  - {node_type}: {count}个")
        
        # 检查是否有真实岗位数据
        metadata = result.get('summary', {}).get('metadata', {})
        data_sources = metadata.get('data_sources', {})
        print(f"✓ 数据来源: {data_sources}")
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("知识图谱三视图连通性测试")
    print("="*60)
    
    results = []
    
    # 测试三个视图
    results.append(("people视图", test_people_view()))
    results.append(("signals视图", test_signals_view()))
    results.append(("career视图", test_career_view()))
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n🎉 所有测试通过！三个视图已成功连接到后端链条。")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查上述错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
