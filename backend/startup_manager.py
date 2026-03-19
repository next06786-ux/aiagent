"""
系统启动管理器
集中管理所有系统的初始化逻辑
在后端启动时执行，而不是延迟初始化
"""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局系统实例
_systems = {
    'llm_service': None,
    'fusion_system': None,
    'perception_layer': None,
    'emergence_detector': None,
    'report_generator': None,
    'analysis_engine': None,
    'knowledge_graphs': {},
    'info_kg_systems': {},
    'hybrid_systems': {},
    'rag_systems': {},
    'learners': {},
    'optimized_learners': {},
    'optimized_detectors': {},
    'feedback_processors': {},
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
        print("\n" + "=" * 70)
        print(f"  {text}")
        print("=" * 70 + "\n")
    
    @staticmethod
    def print_step(step: int, total: int, text: str):
        """打印步骤"""
        print(f"  [{step}/{total}] ⏳ {text}...")
    
    @staticmethod
    def print_success(text: str):
        """打印成功"""
        print(f"  ✅ {text}")
    
    @staticmethod
    def print_warning(text: str):
        """打印警告"""
        print(f"  ⚠️  {text}")
    
    @staticmethod
    def print_error(text: str):
        """打印错误"""
        print(f"  ❌ {text}")
    
    @staticmethod
    async def init_llm_service():
        """初始化 LLM 服务"""
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
        """初始化多模态融合系统"""
        try:
            from backend.multimodal.enhanced_fusion import EnhancedMultimodalFusion
            _systems['fusion_system'] = EnhancedMultimodalFusion()
            StartupManager.print_success("多模态融合系统初始化完成")
            return True
        except Exception as e:
            StartupManager.print_warning(f"多模态融合系统初始化失败: {e}")
            return False
    
    @staticmethod
    async def init_perception_layer():
        """初始化感知层"""
        try:
            from backend.multimodal.perception_layer import get_perception_layer
            _systems['perception_layer'] = get_perception_layer()
            StartupManager.print_success("感知层初始化完成")
            return True
        except Exception as e:
            StartupManager.print_warning(f"感知层初始化失败: {e}")
            return False
    
    @staticmethod
    async def init_emergence_detector():
        """初始化涌现检测系统"""
        try:
            from backend.prediction.emergence_detector import get_emergence_detector
            _systems['emergence_detector'] = get_emergence_detector()
            _init_status['emergence_detector'] = True
            StartupManager.print_success("涌现检测系统初始化完成")
            return True
        except Exception as e:
            StartupManager.print_warning(f"涌现检测系统初始化失败: {e}")
            return False
    
    @staticmethod
    async def init_report_generator():
        """初始化报告生成器"""
        try:
            from backend.prediction.emergence_report_generator import get_report_generator
            _systems['report_generator'] = get_report_generator()
            StartupManager.print_success("报告生成器初始化完成")
            return True
        except Exception as e:
            StartupManager.print_warning(f"报告生成器初始化失败: {e}")
            return False
    
    @staticmethod
    async def init_analysis_engine():
        """初始化分析引擎"""
        try:
            from backend.analysis.unified_analyzer import get_analysis_engine
            _systems['analysis_engine'] = get_analysis_engine()
            StartupManager.print_success("分析引擎初始化完成")
            return True
        except Exception as e:
            StartupManager.print_warning(f"分析引擎初始化失败: {e}")
            return False
    
    @staticmethod
    async def init_default_user_systems():
        """初始化默认用户的系统"""
        default_user = "default_user"
        
        try:
            # 初始化信息知识图谱
            from backend.knowledge.information_knowledge_graph import InformationKnowledgeGraph
            _systems['info_kg_systems'][default_user] = InformationKnowledgeGraph(default_user)
            StartupManager.print_success(f"信息知识图谱初始化完成 ({default_user})")
            _init_status['knowledge_graph'] = True
        except Exception as e:
            StartupManager.print_warning(f"信息知识图谱初始化失败: {e}")
            _systems['info_kg_systems'][default_user] = None
        
        try:
            # 初始化 Neo4j 知识图谱
            from backend.knowledge.neo4j_knowledge_graph import Neo4jKnowledgeGraph
            _systems['knowledge_graphs'][default_user] = Neo4jKnowledgeGraph(default_user)
            StartupManager.print_success(f"Neo4j 知识图谱初始化完成 ({default_user})")
        except Exception as e:
            StartupManager.print_warning(f"Neo4j 知识图谱初始化失败: {e}")
            _systems['knowledge_graphs'][default_user] = None
        
        try:
            # 初始化 RAG 系统（设置离线模式避免网络问题）
            import os
            os.environ['HF_HUB_OFFLINE'] = '1'  # 启用离线模式
            
            from backend.learning.production_rag_system import ProductionRAGSystem
            _systems['rag_systems'][default_user] = ProductionRAGSystem(default_user, use_gpu=False)
            StartupManager.print_success(f"RAG 系统初始化完成 ({default_user})")
            _init_status['rag_system'] = True
        except Exception as e:
            StartupManager.print_warning(f"RAG 系统初始化失败: {e}")
            _systems['rag_systems'][default_user] = None
    
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
        print("  初始化关键系统...\n")
        results = await asyncio.gather(*[task[1]() for task in tasks])
        
        # 初始化默认用户系统
        print("\n  初始化默认用户系统...\n")
        await StartupManager.init_default_user_systems()
        
        # 计算耗时
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # 打印总结
        StartupManager.print_header("✨ 系统启动完成")
        print(f"  启动耗时: {elapsed:.2f} 秒")
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
        elif system_type == 'kg':
            return _systems['knowledge_graphs'].get(user_id)
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

def get_knowledge_graph(user_id: str = "default_user"):
    """获取知识图谱"""
    return _systems['knowledge_graphs'].get(user_id)

def get_info_kg(user_id: str = "default_user"):
    """获取信息知识图谱"""
    return _systems['info_kg_systems'].get(user_id)

def get_rag_system(user_id: str = "default_user"):
    """获取 RAG 系统"""
    return _systems['rag_systems'].get(user_id)

def get_init_status():
    """获取初始化状态"""
    return _init_status.copy()

