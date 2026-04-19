"""
系统启动管理器
集中管理所有系统的初始化逻辑
在后端启动时执行，而不是延迟初始化

环境变量开关：
  ENABLE_LOCAL_MODEL=false  → 跳过本地 GPU/LoRA 相关加载（默认 false，适合 2GB 服务器）
  ENABLE_LOCAL_MODEL=true   → 加载本地 Qwen 基座 + LoRA（需要 GPU 服务器）
  VERBOSE_STARTUP=true      → 显示详细启动日志（默认 false）
"""
import asyncio
import os
from typing import Dict, Any, Optional
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.WARNING)  # 默认只显示警告和错误
logger = logging.getLogger(__name__)

# 是否启用本地 GPU 模型（默认关闭，适合轻量服务器）
ENABLE_LOCAL_MODEL = os.environ.get("ENABLE_LOCAL_MODEL", "false").lower() == "true"

# 是否显示详细启动日志（默认关闭）
VERBOSE_STARTUP = os.environ.get("VERBOSE_STARTUP", "false").lower() == "true"

# 全局系统实例
_systems = {
    'llm_service': None,
    'fusion_system': None,
    'perception_layer': None,
    'emergence_detector': None,
    'report_generator': None,
    'analysis_engine': None,
    'info_kg_systems': {},
    'hybrid_systems': {},
    'rag_systems': {},
    'learners': {},
    'optimized_learners': {},
    'optimized_detectors': {},
}

# 初始化状态
_init_status = {
    'llm_service': False,
    'fusion_system': False,
    'perception_layer': False,
    'emergence_detector': False,
    'knowledge_graph': False,
    'rag_system': False,
}


class StartupManager:
    """系统启动管理器"""
    
    @staticmethod
    def print_header(text: str):
        """打印标题"""
        if VERBOSE_STARTUP:
            print("\n" + "=" * 70)
            print(f"  {text}")
            print("=" * 70 + "\n")
    
    @staticmethod
    def print_step(step: int, total: int, text: str):
        """打印步骤"""
        if VERBOSE_STARTUP:
            print(f"  [{step}/{total}] ⏳ {text}...")
    
    @staticmethod
    def print_success(text: str):
        """打印成功"""
        if VERBOSE_STARTUP:
            print(f"  ✅ {text}")
    
    @staticmethod
    def print_warning(text: str):
        """打印警告"""
        if VERBOSE_STARTUP:
            print(f"  ⚠️  {text}")
    
    @staticmethod
    def print_error(text: str):
        """打印错误"""
        print(f"  ❌ {text}")  # 错误始终显示
    
    @staticmethod
    async def init_llm_service():
        """初始化 LLM 服务（API 模式始终可用，本地模型需 ENABLE_LOCAL_MODEL=true）"""
        try:
            from backend.llm.llm_service import get_llm_service
            _systems['llm_service'] = get_llm_service()
            _init_status['llm_service'] = True
            StartupManager.print_success("LLM 服务初始化完成")
            return True
        except Exception as e:
            StartupManager.print_warning(f"LLM 服务初始化失败: {e}")
            return False
    
    @staticmethod
    async def init_fusion_system():
        """初始化多模态融合系统（已禁用，模块不存在）"""
        StartupManager.print_warning("多模态融合系统模块不存在，跳过初始化")
        return False
    
    @staticmethod
    async def init_perception_layer():
        """初始化感知层（已禁用，模块不存在）"""
        StartupManager.print_warning("感知层模块不存在，跳过初始化")
        return False
    
    @staticmethod
    async def init_emergence_detector():
        """初始化涌现检测系统（已禁用，模块已删除）"""
        StartupManager.print_warning("涌现检测系统模块已删除，跳过初始化")
        return False
    
    @staticmethod
    async def init_report_generator():
        """初始化报告生成器（已禁用，模块已删除）"""
        StartupManager.print_warning("报告生成器模块已删除，跳过初始化")
        return False
    
    @staticmethod
    async def init_analysis_engine():
        """初始化分析引擎（已禁用，模块不存在）"""
        StartupManager.print_warning("分析引擎模块不存在，跳过初始化")
        return False
    
    @staticmethod
    async def init_default_user_systems():
        """初始化默认用户的系统（已禁用，改为按需加载）"""
        # 知识图谱和RAG系统将在用户登录后按需加载
        StartupManager.print_success("用户系统将在登录后按需加载")
        _init_status['knowledge_graph'] = False  # 标记为未初始化
        _init_status['rag_system'] = False
    @staticmethod
    async def warmup_services():
        """预热服务（连接池、缓存等）- 非阻塞，失败不影响启动"""
        print("\n  预热服务...\n")
        
        # 使用超时保护，避免预热阻塞启动
        async def warmup_with_timeout():
            # 1. 预热Redis连接池（非阻塞）
            try:
                from backend.decision.future_os_service import _get_redis_client
                redis_client = _get_redis_client()
                if redis_client:
                    # 使用短超时，避免阻塞
                    redis_client.ping()
                    StartupManager.print_success("Redis连接池已预热")
            except Exception as e:
                # Redis预热失败不影响启动
                StartupManager.print_warning(f"Redis预热跳过: {e}")
            
            # 2. 预热节点分类缓存（非阻塞）
            try:
                from backend.decision.future_os_service import _load_cache
                cache = _load_cache()
                StartupManager.print_success(f"节点分类缓存已加载: {len(cache)} 条")
            except Exception as e:
                # 缓存加载失败不影响启动
                StartupManager.print_warning(f"节点分类缓存跳过: {e}")
            
            # 3. LLM服务预热已移到main.py的startup_event中异步执行
            # 这里不再预热，避免重复
            try:
                if _systems['llm_service'] and _systems['llm_service'].enabled:
                    StartupManager.print_success("LLM服务已就绪（将在后台预热）")
            except Exception as e:
                StartupManager.print_warning(f"LLM服务检查失败: {e}")
        
        try:
            # 5秒超时保护
            await asyncio.wait_for(warmup_with_timeout(), timeout=5.0)
        except asyncio.TimeoutError:
            StartupManager.print_warning("预热超时，跳过剩余预热任务")
        except Exception as e:
            StartupManager.print_warning(f"预热过程出错: {e}")
    
    @staticmethod
    async def startup():
        """执行完整的启动流程"""
        StartupManager.print_header("🚀 LifeSwarm 系统启动")
        
        start_time = datetime.now()
        
        # 定义初始化任务
        tasks = [
            ("LLM 服务", StartupManager.init_llm_service),
            ("多模态融合系统", StartupManager.init_fusion_system),
            ("感知层", StartupManager.init_perception_layer),
            ("涌现检测系统", StartupManager.init_emergence_detector),
            ("报告生成器", StartupManager.init_report_generator),
            ("分析引擎", StartupManager.init_analysis_engine),
        ]
        
        total = len(tasks)
        
        # 并行初始化关键系统
        step_start = datetime.now()
        print("  初始化关键系统...\n")
        results = await asyncio.gather(*[task[1]() for task in tasks])
        step_elapsed = (datetime.now() - step_start).total_seconds()
        print(f"\n  ⏱️  关键系统初始化耗时: {step_elapsed:.2f}秒\n")
        
        # 初始化默认用户系统
        step_start = datetime.now()
        print("  初始化默认用户系统...\n")
        await StartupManager.init_default_user_systems()
        step_elapsed = (datetime.now() - step_start).total_seconds()
        print(f"\n  ⏱️  用户系统初始化耗时: {step_elapsed:.2f}秒\n")
        
        # 预热服务
        step_start = datetime.now()
        await StartupManager.warmup_services()
        step_elapsed = (datetime.now() - step_start).total_seconds()
        print(f"\n  ⏱️  服务预热耗时: {step_elapsed:.2f}秒\n")
        
        # 计算耗时
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # 打印总结
        StartupManager.print_header("✨ 系统启动完成")
        print(f"  总启动耗时: {elapsed:.2f} 秒")
        print(f"  LLM 服务: {'✅ 就绪' if _init_status['llm_service'] else '⚠️  未就绪'}")
        print(f"  知识图谱: {'✅ 就绪' if _init_status['knowledge_graph'] else '⚠️  未就绪'}")
        print(f"  RAG 系统: {'✅ 就绪' if _init_status['rag_system'] else '⚠️  未就绪'}")
        print(f"  涌现检测: {'✅ 就绪' if _init_status['emergence_detector'] else '⚠️  未就绪'}")
        print("\n  系统已就绪，可以接收请求\n")
    
    @staticmethod
    def get_system(name: str) -> Optional[Any]:
        """获取系统实例"""
        return _systems.get(name)
    
    @staticmethod
    def get_user_system(user_id: str, system_type: str) -> Optional[Any]:
        """获取用户系统实例"""
        if system_type == 'info_kg':
            return _systems['info_kg_systems'].get(user_id)
        elif system_type == 'rag':
            return _systems['rag_systems'].get(user_id)
        elif system_type == 'learner':
            return _systems['learners'].get(user_id)
        return None
    
    @staticmethod
    def get_init_status() -> Dict[str, bool]:
        """获取初始化状态"""
        return _init_status.copy()


# 便捷函数
def get_llm_service():
    """获取 LLM 服务"""
    return _systems['llm_service']

def get_fusion_system():
    """获取多模态融合系统"""
    return _systems['fusion_system']

def get_perception_layer():
    """获取感知层"""
    return _systems['perception_layer']

def get_emergence_detector():
    """获取涌现检测系统"""
    return _systems['emergence_detector']

def get_info_kg(user_id: str = "default_user"):
    """获取信息知识图谱"""
    return _systems['info_kg_systems'].get(user_id)

def get_rag_system(user_id: str = "default_user"):
    """获取 RAG 系统"""
    return _systems['rag_systems'].get(user_id)

def get_init_status():
    """获取初始化状态"""
    return _init_status.copy()


async def _test_llm_async():
    """异步测试LLM（预热）"""
    try:
        await asyncio.sleep(1)  # 等待1秒后再测试
        if _systems['llm_service']:
            _systems['llm_service'].chat(
                [{"role": "user", "content": "测试"}],
                temperature=0.1
            )
            logger.info("LLM服务预热完成")
    except Exception as e:
        logger.warning(f"LLM预热测试失败: {e}")
