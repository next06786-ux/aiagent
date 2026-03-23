"""
测试启动管理器
验证系统初始化是否正常
"""
import asyncio
import sys
import os

# 添加后端目录到路径
sys.path.insert(0, os.path.dirname(__file__))

async def test_startup():
    """测试启动流程"""
    print("\n" + "="*70)
    print("  测试启动管理器")
    print("="*70 + "\n")
    
    try:
        from startup_manager import StartupManager
        
        # 执行启动
        await StartupManager.startup()
        
        # 检查系统状态
        print("\n" + "="*70)
        print("  检查系统状态")
        print("="*70 + "\n")
        
        status = StartupManager.get_init_status()
        
        for service, is_ready in status.items():
            icon = "✅" if is_ready else "❌"
            print(f"  {icon} {service}: {'就绪' if is_ready else '未就绪'}")
        
        # 测试获取系统实例
        print("\n" + "="*70)
        print("  测试获取系统实例")
        print("="*70 + "\n")
        
        llm = StartupManager.get_system('llm_service')
        print(f"  LLM 服务: {llm}")
        
        kg = StartupManager.get_user_system('default_user', 'info_kg')
        print(f"  知识图谱: {kg}")
        
        rag = StartupManager.get_user_system('default_user', 'rag')
        print(f"  RAG 系统: {rag}")
        
        print("\n" + "="*70)
        print("  ✅ 测试完成")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_startup())
    sys.exit(0 if success else 1)










