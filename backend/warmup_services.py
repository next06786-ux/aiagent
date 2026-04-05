"""
服务预热脚本
在后端启动后自动执行，预先初始化连接和缓存
"""
import asyncio
import os
import sys


async def warmup_redis():
    """预热Redis连接"""
    try:
        import redis
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
            max_connections=50
        )
        redis_client.ping()
        print("✓ Redis连接池已预热")
        return True
    except Exception as e:
        print(f"✗ Redis预热失败: {e}")
        return False


async def warmup_llm():
    """预热LLM服务"""
    try:
        from backend.llm.llm_service import get_llm_service
        llm = get_llm_service()
        if llm and llm.enabled:
            # 发送一个简单的测试请求
            llm.chat([{"role": "user", "content": "测试"}], temperature=0.1)
            print("✓ LLM服务已预热")
            return True
        else:
            print("⚠ LLM服务未启用")
            return False
    except Exception as e:
        print(f"✗ LLM预热失败: {e}")
        return False


async def warmup_neo4j():
    """预热Neo4j连接"""
    try:
        from backend.knowledge.information_knowledge_graph import InformationKnowledgeGraph
        # 创建一个测试连接
        kg = InformationKnowledgeGraph("warmup_test")
        kg.close()
        print("✓ Neo4j连接已预热")
        return True
    except Exception as e:
        print(f"✗ Neo4j预热失败: {e}")
        return False


async def warmup_node_classifier():
    """预热节点分类器（加载缓存）"""
    try:
        from backend.decision.future_os_service import _load_cache
        cache = _load_cache()
        print(f"✓ 节点分类缓存已加载: {len(cache)} 条")
        return True
    except Exception as e:
        print(f"✗ 节点分类器预热失败: {e}")
        return False


async def warmup_all():
    """执行所有预热任务"""
    print("\n" + "="*60)
    print("开始服务预热...")
    print("="*60)
    
    tasks = [
        ("Redis连接池", warmup_redis()),
        ("Neo4j连接", warmup_neo4j()),
        ("节点分类器", warmup_node_classifier()),
        ("LLM服务", warmup_llm()),
    ]
    
    results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
    
    success_count = sum(1 for r in results if r is True)
    
    print("="*60)
    print(f"预热完成: {success_count}/{len(tasks)} 个服务就绪")
    print("="*60 + "\n")
    
    return success_count == len(tasks)


def run_warmup():
    """同步运行预热"""
    try:
        asyncio.run(warmup_all())
    except Exception as e:
        print(f"预热过程出错: {e}")


if __name__ == "__main__":
    run_warmup()
