"""
测试前端知识图谱显示问题
验证API返回的数据格式是否正确
"""
import requests
import json

def test_kg_export_api():
    """测试知识图谱导出API"""
    print("=" * 70)
    print("测试：知识图谱导出API")
    print("=" * 70)
    
    url = "http://localhost:8000/api/v4/knowledge-graph/default_user/export"
    print(f"\n请求URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ API响应成功")
            print(f"success: {data.get('success')}")
            
            if data.get('success') and data.get('data'):
                graph_data = data['data']
                
                # 检查数据结构
                info_nodes = graph_data.get('information', [])
                source_nodes = graph_data.get('sources', [])
                relationships = graph_data.get('relationships', [])
                
                print(f"\n📊 数据统计:")
                print(f"  - information节点: {len(info_nodes)} 个")
                print(f"  - sources节点: {len(source_nodes)} 个")
                print(f"  - relationships关系: {len(relationships)} 个")
                
                # 检查节点格式
                if info_nodes:
                    print(f"\n📝 第一个information节点:")
                    first_node = info_nodes[0]
                    print(f"  - id: {first_node.get('id')}")
                    print(f"  - name: {first_node.get('name')}")
                    print(f"  - type: {first_node.get('type')}")
                    print(f"  - category: {first_node.get('category')}")
                    
                    # 检查前端需要的字段
                    required_fields = ['id', 'name', 'type']
                    missing_fields = [f for f in required_fields if f not in first_node]
                    
                    if missing_fields:
                        print(f"\n⚠️  缺少必需字段: {missing_fields}")
                    else:
                        print(f"\n✅ 节点格式正确")
                
                # 检查关系格式
                if relationships:
                    print(f"\n🔗 第一个关系:")
                    first_rel = relationships[0]
                    print(f"  - source: {first_rel.get('source')}")
                    print(f"  - target: {first_rel.get('target')}")
                    print(f"  - type: {first_rel.get('type')}")
                    
                    # 检查前端需要的字段
                    required_fields = ['source', 'target', 'type']
                    missing_fields = [f for f in required_fields if f not in first_rel]
                    
                    if missing_fields:
                        print(f"\n⚠️  缺少必需字段: {missing_fields}")
                    else:
                        print(f"\n✅ 关系格式正确")
                
                # 完整数据输出（用于调试）
                print(f"\n📄 完整响应数据（前500字符）:")
                print(json.dumps(data, ensure_ascii=False, indent=2)[:500])
                
            else:
                print(f"\n❌ API返回失败或数据为空")
                print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
        else:
            print(f"\n❌ HTTP错误: {response.status_code}")
            print(f"响应: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 无法连接到后端服务")
        print(f"提示: 请确保后端已启动 (python backend/start_server.py)")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_kg_export_api()
