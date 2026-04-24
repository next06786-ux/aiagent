"""
LifeSwarm 后端服务 - FastAPI 应用主入口
"""
import os
import sys
import time
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import asyncio
import threading

# 加载环境变量（从项目根目录）
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_env_file = os.path.join(_project_root, '.env')
load_dotenv(_env_file)

# 配置日志级别（减少冗余输出）
import logging
logging.basicConfig(level=logging.WARNING)  # 只显示WARNING及以上级别
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("fastapi").setLevel(logging.WARNING)

# 但允许决策相关的日志显示
logging.getLogger("backend.decision").setLevel(logging.INFO)

# 过滤恶意扫描的404日志
class ScanFilter(logging.Filter):
    """过滤常见的恶意扫描路径"""
    SCAN_PATTERNS = [
        'db.zip', 'database.php', 'credentials', 'api.log', 'env.sql',
        'backup.log', 'database.bak', 'admin.key', 'debug.conf', 'keys',
        'application.ts', 'database.py', 'info.php', 'index.tar', 'index.gz',
        'database.cfg', 'credentials.bak', 'index.yaml', 'help/info'
    ]
    
    def filter(self, record):
        # 检查日志消息是否包含扫描路径
        message = record.getMessage()
        if '404 Not Found' in message:
            return not any(pattern in message for pattern in self.SCAN_PATTERNS)
        return True

# 应用过滤器到uvicorn的access日志
logging.getLogger("uvicorn.access").addFilter(ScanFilter())

# 设置 HuggingFace 离线模式(避免网络问题)
os.environ['HF_HUB_OFFLINE'] = '1'

# 创建FastAPI应用
app = FastAPI(
    title="LifeSwarm API",
    description="智能生活助手系统 - 多模态数据采集,AI分析,知识图谱",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 初始化系统====================

# 延迟初始化所有系统(避免启动阻塞)个llm_service = None
hybrid_systems = {}
fusion_system = None
rag_systems = {}
learners = {}
report_generator = None
analysis_engine = None
enhanced_kg_systems = {}
optimized_learners = {}
optimized_detectors = {}

# 初始化数据库管理器(轻量级)
from backend.database.db_manager import db_manager

# 全局知识图谱系统字典
info_kg_systems = {}

# 轻量训练任务状态（已禁用）
# lora_training_tasks: Dict[str, Dict[str, Any]] = {}

def get_or_init_llm_service():
    """获取 LLM 服务"""
    from backend.startup_manager import get_llm_service
    return get_llm_service()

def get_or_init_fusion_system():
    """获取多模态融合系统（已禁用）"""
    return None

# 导入必要的类型(但不初始化)
from backend.learning.production_rag_system import ProductionRAGSystem, MemoryType
from backend.learning.reinforcement_learner import ReinforcementLearner
from backend.knowledge.information_knowledge_graph import InformationKnowledgeGraph
# OptimizedEmergenceDetector 已删除（prediction模块已移除）

def get_or_init_perception_layer():
    """获取感知层（已禁用）"""
    return None

def get_or_init_emergence_detector():
    """获取涌现检测系统（已禁用）"""
    return None

def get_or_init_report_generator():
    """获取报告生成器"""
    from backend.startup_manager import StartupManager
    return StartupManager.get_system('report_generator')

def get_or_init_analysis_engine():
    """获取分析引擎"""
    from backend.startup_manager import StartupManager
    return StartupManager.get_system('analysis_engine')


# ==================== 系统启动管理 ====================

from backend.startup_manager import StartupManager

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化所有系统"""
    import time
    overall_start = time.time()
    
    # StartupManager启动
    manager_start = time.time()
    await StartupManager.startup()
    print(f"??  StartupManager耗时: {time.time() - manager_start:.2f}秒\n")
    
    # 启动岗位数据调度器 - 已禁用（使用预缓存数据）
    # scheduler_start = time.time()
    # try:
    #     from backend.vertical.career.job_scheduler import start_job_scheduler
    #     start_job_scheduler()
    #     print("? 岗位数据调度器已启动")
    # except Exception as e:
    #     print(f"?? 岗位数据调度器启动失败: {e}")
    # print(f"??  岗位调度器耗时: {time.time() - scheduler_start:.2f}秒\n")
    print("??  岗位数据调度器已禁用，使用预缓存数据\n")
    
    # 本地 GPU 模型相关：仅在 ENABLE_LOCAL_MODEL=true 时加载
    import os
    enable_local = os.environ.get("ENABLE_LOCAL_MODEL", "false").lower() == "true"
    
    # 本地模型功能已禁用（LoRA模块已删除）
    if enable_local:
        print("⚠️  本地模型功能已禁用（LoRA模块已删除）")
    
    # 知识图谱按需加载（用户登录后异步加载）
    print("??  知识图谱将在用户登录后按需加载\n")

    # 预初始化 LLM 服务（避免首次请求时初始化延迟）
    llm_start = time.time()
    try:
        from backend.llm.llm_service import get_llm_service
        print("预初始化 LLM 服务...")
        llm = get_llm_service()
        if llm and llm.enabled:
            print(f"LLM 服务已就绪: {llm.provider.value}")
    except Exception as e:
        print(f"⚠️  LLM 服务初始化失败: {e}")
    print(f"⏱️  LLM服务耗时: {time.time() - llm_start:.2f}秒\n")
    
    # 启动消息处理器（后台异步处理）
    processor_start = time.time()
    try:
        from backend.conversation.message_processor import get_message_processor
        print("启动消息处理器...")
        processor = get_message_processor()
        print("✅ 消息处理器已启动（后台异步处理）")
    except Exception as e:
        print(f"⚠️  消息处理器启动失败: {e}")
    print(f"⏱️  消息处理器耗时: {time.time() - processor_start:.2f}秒\n")
    
    # 预初始化数据库连接
    db_start = time.time()
    try:
        from backend.database.connection import db_connection
        print("✅ 数据库连接预初始化完成")
    except Exception as e:
        print(f"?? 数据库连接预初始化失败: {e}")
    print(f"??  数据库连接耗时: {time.time() - db_start:.2f}秒\n")
    
    # 预热AI核心决策系统
    decision_start = time.time()
    try:
        print("?? 预热 AI 核心决策系统...")
        
        # 1. 预热决策信息收集器
        from backend.decision.decision_info_collector import DecisionInfoCollector
        info_collector = DecisionInfoCollector()
        print("  ✓ 决策信息收集器已就绪")
        
        # 2. 预热教育决策引擎（唯一保留的决策引擎）
        from backend.vertical.education.education_decision_engine import EducationDecisionEngine
        
        education_engine = EducationDecisionEngine()
        print("  ✓ 教育决策引擎已就绪")
        
        print("✓ AI 核心决策系统预热完成")
    except Exception as e:
        print(f"?? AI 核心决策系统预热失败: {e}")
    print(f"??  决策系统预热耗时: {time.time() - decision_start:.2f}秒\n")
    
    # 启动后台LLM分类任务
    bg_start = time.time()
    try:
        from backend.vertical.background_classifier import start_background_classification
        print("?? 启动后台LLM分类任务...")
        start_background_classification()
        print("? 后台LLM分类任务已启动（将在后台异步执行）")
    except Exception as e:
        print(f"?? 后台LLM分类任务启动失败: {e}")
    print(f"??  后台分类任务启动耗时: {time.time() - bg_start:.2f}秒\n")

    
    # 启动智能日程自动生成器
    schedule_start = time.time()
    try:
        from backend.schedule.schedule_auto_generator import start_auto_generator
        print("?? 启动智能日程自动生成器...")
        start_auto_generator()
        print("? 智能日程自动生成器已启动")
    except Exception as e:
        print(f"?? 智能日程自动生成器启动失败: {e}")
    print(f"??  日程自动生成器耗时: {time.time() - schedule_start:.2f}秒\n")
    
    # 【新增】检测活跃登录会话并自动加载用户系统
    login_check_start = time.time()
    try:
        from backend.auth.startup_login_checker import startup_check_and_load
        print("?? 检测活跃登录会话...")
        await startup_check_and_load()
        print("? 活跃会话检测完成")
    except Exception as e:
        print(f"?? 活跃会话检测失败: {e}")
    print(f"??  登录状态检测耗时: {time.time() - login_check_start:.2f}秒\n")
    
    print(f"?? 总启动耗时: {time.time() - overall_start:.2f}秒\n")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    import os
    
    # 停止消息处理器
    try:
        from backend.conversation.message_processor import stop_message_processor
        stop_message_processor()
        print("✅ 消息处理器已停止")
    except Exception as e:
        print(f"⚠️  消息处理器停止失败: {e}")
    
    # 停止智能日程自动生成器
    try:
        from backend.schedule.schedule_auto_generator import stop_auto_generator
        stop_auto_generator()
        print("✅ 智能日程自动生成器已停止")
    except Exception as e:
        print(f"⚠️  智能日程自动生成器停止失败: {e}")
    
    # LoRA调度器已删除
    print("⚠️  LoRA调度器已删除")


# ==================== 工具函数 ====================

def get_or_create_user_system(user_id: str):
    """获取或创建用户的系统实例"""
    from backend.startup_manager import StartupManager, _systems
    
    # 每个用户使用自己的RAG系统
    # 如果用户的RAG系统不存在，则创建
    if user_id not in _systems.get('rag_systems', {}):
        try:
            import os
            os.environ['HF_HUB_OFFLINE'] = '1'
            from backend.learning.production_rag_system import ProductionRAGSystem
            if 'rag_systems' not in _systems:
                _systems['rag_systems'] = {}
            # 使用CPU模式，GPU模式在4GB显存下不稳定
            _systems['rag_systems'][user_id] = ProductionRAGSystem(user_id, use_gpu=False)
            print(f"✓ 用户 {user_id} 的 RAG 系统已创建（生产级）")
        except (ImportError, RuntimeError) as e:
            from backend.learning.unified_rag_system import UnifiedRAGSystem
            if 'rag_systems' not in _systems:
                _systems['rag_systems'] = {}
            _systems['rag_systems'][user_id] = UnifiedRAGSystem(user_id)
            print(f"✓ 用户 {user_id} 的 RAG 系统已创建（轻量模式）")
    
    return {
        'hybrid': None,  # 按需初始化
        'rag': _systems.get('rag_systems', {}).get(user_id),
        'learner': StartupManager.get_user_system(user_id, 'learner'),
        'kg': StartupManager.get_user_system(user_id, 'kg'),
        'info_kg': StartupManager.get_user_system(user_id, 'info_kg')
    }


async def load_user_systems_async(user_id: str):
    """异步加载用户的星图系统"""
    import asyncio
    print(f"开始异步加载用户 {user_id} 的星图系统...")
    
    try:
        # 检查是否已加载
        global info_kg_systems
        
        if user_id not in info_kg_systems:
            # 加载信息知识图谱
            from backend.knowledge.information_knowledge_graph import InformationKnowledgeGraph
            info_kg_systems[user_id] = InformationKnowledgeGraph(user_id)
            print(f"✓ 用户 {user_id} 的信息知识图谱加载完成")
        
        # 加载 RAG 系统
        from backend.startup_manager import _systems, _init_status
        if user_id not in _systems.get('rag_systems', {}):
            try:
                import os
                os.environ['HF_HUB_OFFLINE'] = '1'
                from backend.learning.production_rag_system import ProductionRAGSystem
                # 使用CPU模式，GPU模式在4GB显存下不稳定
                _systems['rag_systems'][user_id] = ProductionRAGSystem(user_id, use_gpu=False)
                print(f"✓ 用户 {user_id} 的 RAG 系统加载完成（生产级）")
            except (ImportError, RuntimeError) as e:
                from backend.learning.unified_rag_system import UnifiedRAGSystem
                _systems['rag_systems'][user_id] = UnifiedRAGSystem(user_id)
                print(f"✓ 用户 {user_id} 的 RAG 系统加载完成（轻量模式）")
        
        # 更新初始化状态
        _init_status['knowledge_graph'] = True
        _init_status['rag_system'] = True
        
        print(f"✓ 用户 {user_id} 的所有系统加载完成")
        
    except Exception as e:
        print(f"✗ 用户 {user_id} 系统加载失败: {e}")
        import traceback
        traceback.print_exc()


# ==================== 健康检查====================

@app.get("/health")
async def health_check():
    """主后端健康检查"""
    from backend.startup_manager import get_init_status, _systems

    status = get_init_status()
    
    # 检查实际加载的用户系统（而不仅仅是初始化状态）
    kg_loaded = len(info_kg_systems) > 0
    rag_loaded = len(_systems.get('rag_systems', {})) > 0
    
    lora_dir = os.environ.get("LORA_MODELS_DIR", "./models/lora")
    lora_dir_exists = os.path.exists(lora_dir)
    lora_user_count = 0
    if lora_dir_exists:
        lora_user_count = len([
            d for d in os.listdir(lora_dir)
            if os.path.isdir(os.path.join(lora_dir, d))
        ])

    overall_status = "healthy" if status['llm_service'] else "degraded"

    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "deployment_mode": "transformers_native",
        "model": "Qwen/Qwen3.5-9B",
        "services": {
            "fastapi": "✅ 就绪",
            "llm": "✅ 就绪" if status['llm_service'] else "⚠️  未就绪",
            "knowledge_graph": "✅ 就绪" if kg_loaded else "⚠️  未就绪",
            "rag": "✅ 就绪" if rag_loaded else "⚠️  未就绪",
            "database": "✅ 就绪",
        },
        "user_systems": {
            "knowledge_graph_users": len(info_kg_systems),
            "rag_users": len(_systems.get('rag_systems', {}))
        }
    }


# ==================== 数据采集API ====================

@app.post("/api/v4/multimodal/data")
async def upload_multimodal_data(request_data: Dict[str, Any]):
    """
    上传多模态数据
    
    请求体:
    {
        "user_id": "user_001",
        "timestamp": 1234567890,
        "sensor": {...},
        "health": {...},
        "context": {...},
        "image": {...},
        "text": "用户输入",
        "metadata": {...}
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        timestamp = request_data.get("timestamp", int(datetime.now().timestamp() * 1000))
        
        # 获取用户系统
        systems = get_or_create_user_system(user_id)
        
        # 【已禁用】数据流协调器功能已移除
        
        # 1. 多模态融合(保留原有逻辑        modalities = []
        
        if "sensor" in request_data and request_data["sensor"]:
            modalities.append({
                "type": "sensor",
                "data": request_data["sensor"],
                "confidence": 0.9
            })
        
        if "health" in request_data and request_data["health"]:
            modalities.append({
                "type": "sensor",
                "data": request_data["health"],
                "confidence": 0.85
            })
        
        if "context" in request_data and request_data["context"]:
            modalities.append({
                "type": "sensor",
                "data": request_data["context"],
                "confidence": 0.8
            })
        
        if "text" in request_data and request_data["text"]:
            modalities.append({
                "type": "text",
                "data": request_data["text"],
                "confidence": 0.95
            })
        
        # 融合多模态数据
        fused_result = get_or_init_fusion_system().fuse_modalities(modalities)
        
        # 2. 感知层处理
        perception_result = get_or_init_perception_layer().perceive(
            user_id=user_id,
            data=request_data
        )
        
        # 3. 保存到数据库
        try:
            db_manager.save_health_record(
                user_id=user_id,
                data={
                    "sleep_hours": request_data.get("health", {}).get("sleepHours", 0),
                    "sleep_quality": request_data.get("health", {}).get("sleepQuality", 0),
                    "steps": request_data.get("sensor", {}).get("steps", 0),
                    "heart_rate": request_data.get("sensor", {}).get("heartRate", 0),
                    "exercise_minutes": request_data.get("health", {}).get("exerciseMinutes", 0),
                    "stress_level": request_data.get("health", {}).get("stressLevel", 0),
                    "health_score": 75.0
                }
            )
        except Exception as e:
            print(f"?? 数据库保存失 {e}")
        
        # 4. 添加到RAG记忆
        try:
            # 【改进】根据数据类型分别存            
            # 如果有图片,存储图片记忆
            if "image" in request_data and request_data["image"]:
                image_description = perception_result.get("image_analysis", {}).get("description", "用户上传了一张图")
                
                systems['rag'].add_memory(
                    memory_type=MemoryType.PHOTO,
                    content=f"图片记忆: {image_description}",
                    metadata={
                        "timestamp": timestamp,
                        "image_data": request_data["image"][:100] if isinstance(request_data["image"], str) else "binary",
                        "scene": perception_result.get("image_analysis", {}).get("scene", {}),
                        "objects": perception_result.get("image_analysis", {}).get("objects", [])
                    },
                    importance=0.8
                )
                print(f"[自动记忆] 图片已存入RAG: {image_description[:50]}...")
            
            # 如果有文本,存储对话记忆
            if "text" in request_data and request_data["text"]:
                systems['rag'].add_memory(
                    memory_type=MemoryType.CONVERSATION,
                    content=f"用户输入: {request_data['text']}",
                    metadata={
                        "timestamp": timestamp,
                        "context": request_data.get("context", {})
                    },
                    importance=0.7
                )
                print(f"[自动记忆] 文本已存入RAG: {request_data['text'][:50]}...")
            
            # 存储传感器数            if "sensor" in request_data and request_data["sensor"]:
                sensor_summary = f"传感器数 步数{request_data['sensor'].get('steps', 0)}, 心率{request_data['sensor'].get('heartRate', 0)}"
                
                systems['rag'].add_memory(
                    memory_type=MemoryType.SENSOR_DATA,
                    content=sensor_summary,
                    metadata={
                        "timestamp": timestamp,
                        "sensor_data": request_data["sensor"]
                    },
                    importance=0.5
                )
                print(f"[自动记忆] 传感器数据已存入RAG")
                
        except Exception as e:
            print(f"?? RAG保存失败: {e}")
        
        return {
            "code": 200,
            "message": "Data received successfully",
            "data": {
                "recordId": f"rec_{timestamp}",
                "timestamp": timestamp,
                "modalities_processed": [m["type"] for m in modalities],
                "fusion_confidence": fused_result.get("confidence", 0),
                "perception_quality": perception_result.get("perception_quality", 0)
            }
        }
    
    except Exception as e:
        print(f"数据上传失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== 分析API ====================

@app.get("/api/v4/analysis/{user_id}")
async def get_analysis(user_id: str):
    """获取用户分析结果"""
    try:
        systems = get_or_create_user_system(user_id)
        
        # 获取最近的健康记录
        health_records = db_manager.get_health_records(user_id, limit=7)
        
        if not health_records:
            return {
                "code": 404,
                "message": "No data found",
                "data": None
            }
        
        # 计算统计
        avg_sleep = sum(r.sleep_hours for r in health_records) / len(health_records) if health_records else 0
        avg_exercise = sum(r.exercise_minutes for r in health_records) / len(health_records) if health_records else 0
        avg_stress = sum(r.stress_level for r in health_records) / len(health_records) if health_records else 0
        
        return {
            "code": 200,
            "message": "Analysis retrieved successfully",
            "data": {
                "user_id": user_id,
                "period": "7_days",
                "health_metrics": {
                    "average_sleep": round(avg_sleep, 1),
                    "average_exercise": round(avg_exercise, 1),
                    "average_stress": round(avg_stress, 1),
                    "health_score": 75.0
                },
                "trends": {
                    "sleep_trend": "stable",
                    "exercise_trend": "improving",
                    "stress_trend": "stable"
                },
                "timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        print(f"分析失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== 6大领域综合分析API ====================

@app.get("/api/v4/life-analysis/{user_id}")
async def get_life_analysis(user_id: str):
    """
    获取综合生活分析
    
    分析6大领域:健康,时间,情绪,社交,财务,学习
    返回综合生活质量分数和关键洞察
    """
    try:
        # 获取用户的历史数据
        health_records = db_manager.get_health_records(user_id, limit=30)
        
        if not health_records:
            return {
                "code": 404,
                "message": "No data found",
                "data": None
            }
        
        # 转换为字典列        history = []
        for record in health_records:
            history.append({
                "timestamp": record.timestamp,
                "sleep_hours": getattr(record, 'sleep_hours', 7),
                "sleep_quality": getattr(record, 'sleep_quality', 7),
                "exercise_minutes": getattr(record, 'exercise_minutes', 30),
                "stress_level": getattr(record, 'stress_level', 5),
                "health_score": getattr(record, 'health_score', 75),
                "heart_rate": getattr(record, 'heart_rate', 70),
                "steps": getattr(record, 'steps', 5000),
                "mood": getattr(record, 'mood', 7),
                "work_hours": getattr(record, 'work_hours', 8),
                "focus_time": getattr(record, 'focus_time', 6),
                "task_completion_rate": getattr(record, 'task_completion_rate', 0.7),
                "interruptions": getattr(record, 'interruptions', 3),
                "time_pressure": getattr(record, 'time_pressure', 0.3),
                "social_hours": getattr(record, 'social_hours', 2),
                "social_interactions": getattr(record, 'social_interactions', 5),
                "loneliness": getattr(record, 'loneliness', 3),
                "social_satisfaction": getattr(record, 'social_satisfaction', 7),
                "income": getattr(record, 'income', 0),
                "spending": getattr(record, 'spending', 0),
                "savings": getattr(record, 'savings', 0),
                "debt": getattr(record, 'debt', 0),
                "learning_hours": getattr(record, 'learning_hours', 1),
                "learning_quality": getattr(record, 'learning_quality', 7),
                "test_score": getattr(record, 'test_score', 75),
                "goal_progress": getattr(record, 'goal_progress', 0.5)
            })
        
        # 获取当前用户数据
        user_data = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # 进行综合分析
        analysis = analysis_engine.analyze(user_id, user_data, history)
        
        # 获取领域总结
        domain_summary = analysis_engine.get_domain_summary(analysis)
        
        return {
            "code": 200,
            "message": "Life analysis completed",
            "data": {
                "user_id": user_id,
                "timestamp": analysis.timestamp,
                "overall_score": analysis.overall_score,
                "domains": domain_summary,
                "key_insights": analysis.key_insights,
                "priority_actions": analysis.priority_actions,
                "detailed_analysis": {
                    "health": analysis.health,
                    "time": analysis.time,
                    "emotion": analysis.emotion,
                    "social": analysis.social,
                    "finance": analysis.finance,
                    "learning": analysis.learning
                }
            }
        }
    
    except Exception as e:
        print(f"综合分析失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/v4/domain-analysis/{user_id}/{domain}")
async def get_domain_analysis(user_id: str, domain: str):
    """
    获取特定领域的详细分析
    
    domain: health, time, emotion, social, finance, learning
    """
    try:
        # 获取用户的历史数据
        health_records = db_manager.get_health_records(user_id, limit=30)
        
        if not health_records:
            return {
                "code": 404,
                "message": "No data found",
                "data": None
            }
        
        # 转换为字典列        history = []
        for record in health_records:
            history.append({
                "timestamp": record.timestamp,
                "sleep_hours": getattr(record, 'sleep_hours', 7),
                "sleep_quality": getattr(record, 'sleep_quality', 7),
                "exercise_minutes": getattr(record, 'exercise_minutes', 30),
                "stress_level": getattr(record, 'stress_level', 5),
                "health_score": getattr(record, 'health_score', 75),
                "heart_rate": getattr(record, 'heart_rate', 70),
                "steps": getattr(record, 'steps', 5000),
                "mood": getattr(record, 'mood', 7),
                "work_hours": getattr(record, 'work_hours', 8),
                "focus_time": getattr(record, 'focus_time', 6),
                "task_completion_rate": getattr(record, 'task_completion_rate', 0.7),
                "interruptions": getattr(record, 'interruptions', 3),
                "time_pressure": getattr(record, 'time_pressure', 0.3),
                "social_hours": getattr(record, 'social_hours', 2),
                "social_interactions": getattr(record, 'social_interactions', 5),
                "loneliness": getattr(record, 'loneliness', 3),
                "social_satisfaction": getattr(record, 'social_satisfaction', 7),
                "income": getattr(record, 'income', 0),
                "spending": getattr(record, 'spending', 0),
                "savings": getattr(record, 'savings', 0),
                "debt": getattr(record, 'debt', 0),
                "learning_hours": getattr(record, 'learning_hours', 1),
                "learning_quality": getattr(record, 'learning_quality', 7),
                "test_score": getattr(record, 'test_score', 75),
                "goal_progress": getattr(record, 'goal_progress', 0.5)
            })
        
        # 获取当前用户数据
        user_data = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # 进行综合分析
        analysis = analysis_engine.analyze(user_id, user_data, history)
        
        # 返回特定领域的分析
        domain_map = {
            "health": analysis.health,
            "time": analysis.time,
            "emotion": analysis.emotion,
            "social": analysis.social,
            "finance": analysis.finance,
            "learning": analysis.learning
        }
        
        if domain not in domain_map:
            return {
                "code": 400,
                "message": f"Invalid domain: {domain}. Valid domains: health, time, emotion, social, finance, learning",
                "data": None
            }
        
        return {
            "code": 200,
            "message": f"{domain} analysis completed",
            "data": {
                "user_id": user_id,
                "domain": domain,
                "timestamp": analysis.timestamp,
                "analysis": domain_map[domain]
            }
        }
    
    except Exception as e:
        print(f"领域分析失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== 用户认证API ====================

@app.post("/api/auth/register")
async def register(request_data: Dict[str, Any]):
    """
    用户注册
    
    请求个
    {
        "username": "user001",
        "email": "user@example.com",
        "password": "password123",
        "nickname": "昵称"
    }
    
    返回:
    {
        "code": 200,
        "message": "注册成功",
        "data": {
            "user_id": "xxx",
            "username": "user001",
            "email": "user@example.com",
            "nickname": "昵称",
            "token": "xxx"
        }
    }
    """
    try:
        from backend.auth.auth_service import get_auth_service
        
        username = request_data.get("username", "").strip()
        email = request_data.get("email", "").strip()
        password = request_data.get("password", "")
        nickname = request_data.get("nickname", "").strip()
        
        # 验证必填字段
        if not username or not email or not password:
            return {
                "code": 400,
                "message": "用户名,邮箱和密码不能为空",
                "data": None
            }
        
        # 验证用户名格式(3-20个字符,字母数字下划线)
        import re
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            return {
                "code": 400,
                "message": "用户名格式不正确个-20个字符,仅支持字母,数字,下划线",
                "data": None
            }
        
        # 验证邮箱格式
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return {
                "code": 400,
                "message": "邮箱格式不正",
                "data": None
            }
        
        # 验证密码长度
        if len(password) < 6:
            return {
                "code": 400,
                "message": "密码长度不能少于6",
                "data": None
            }
        
        auth_service = get_auth_service()
        result = auth_service.register(username, email, password, nickname)
        
        if result['success']:
            return {
                "code": 200,
                "message": result['message'],
                "data": result['data']
            }
        else:
            return {
                "code": 400,
                "message": result['message'],
                "data": None
            }
            
    except Exception as e:
        print(f"注册失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"注册失败: {str(e)}",
            "data": None
        }


@app.post("/api/auth/login")
async def login(request_data: Dict[str, Any]):
    """
    用户登录
    
    请求个
    {
        "username": "user001",  // 或邮        "password": "password123"
    }
    
    返回:
    {
        "code": 200,
        "message": "登录成功",
        "data": {
            "user_id": "xxx",
            "username": "user001",
            "email": "user@example.com",
            "nickname": "昵称",
            "avatar_url": "...",
            "token": "xxx"
        }
    }
    """
    try:
        from backend.auth.auth_service import get_auth_service
        
        username_or_email = request_data.get("username", "").strip()
        password = request_data.get("password", "")
        
        if not username_or_email or not password:
            return {
                "code": 400,
                "message": "用户名和密码不能为空",
                "data": None
            }
        
        auth_service = get_auth_service()
        result = auth_service.login(username_or_email, password)
        
        if result['success']:
            # 登录成功后，只为非管理员用户异步加载星图系统
            user_id = result['data']['user_id']
            is_admin = result['data'].get('is_admin', False)
            
            if not is_admin:
                asyncio.create_task(load_user_systems_async(user_id))
            else:
                print(f"👑 管理员 {user_id} 登录，跳过星图系统加载")
            
            return {
                "code": 200,
                "message": result['message'],
                "data": result['data']
            }
        else:
            return {
                "code": 401,
                "message": result['message'],
                "data": None
            }
            
    except Exception as e:
        print(f"登录失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"登录失败: {str(e)}",
            "data": None
        }


@app.post("/api/auth/logout")
async def logout(request_data: Dict[str, Any]):
    """
    用户登出
    
    请求个
    {
        "token": "xxx"
    }
    
    返回:
    {
        "code": 200,
        "message": "登出成功",
        "data": null
    }
    """
    try:
        from backend.auth.auth_service import get_auth_service
        
        token = request_data.get("token", "")
        
        if not token:
            return {
                "code": 400,
                "message": "Token不能为空",
                "data": None
            }
        
        auth_service = get_auth_service()
        result = auth_service.logout(token)
        
        return {
            "code": 200,
            "message": result['message'],
            "data": None
        }
        
    except Exception as e:
        print(f"登出失败: {e}")
        return {
            "code": 500,
            "message": f"登出失败: {str(e)}",
            "data": None
        }


@app.get("/api/auth/system-status/{user_id}")
async def get_user_system_status(user_id: str):
    """
    获取用户系统加载状态（RAG、知识图谱等）
    
    返回:
    {
        "code": 200,
        "message": "Success",
        "data": {
            "user_id": "xxx",
            "is_loaded": true,
            "systems": {
                "rag": true,
                "kg": true,
                "info_kg": true
            },
            "timestamp": "2024-01-01T00:00:00"
        }
    }
    """
    try:
        from backend.auth.login_state_manager import get_login_state_manager
        
        manager = get_login_state_manager()
        is_loaded = manager.is_user_loaded(user_id)
        status = manager.get_user_status(user_id)
        
        return {
            "code": 200,
            "message": "Success",
            "data": {
                "user_id": user_id,
                "is_loaded": is_loaded,
                "systems": status if status else {
                    "rag": False,
                    "kg": False,
                    "info_kg": False
                },
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        print(f"获取系统状态失败: {e}")
        return {
            "code": 500,
            "message": f"获取系统状态失败: {str(e)}",
            "data": None
        }


@app.post("/api/auth/load-systems")
async def manually_load_user_systems(request_data: Dict[str, Any]):
    """
    手动触发加载用户系统（用于重新加载或首次加载）
    
    请求体:
    {
        "user_id": "xxx"
    }
    
    返回:
    {
        "code": 200,
        "message": "系统加载完成",
        "data": {
            "user_id": "xxx",
            "systems": {
                "rag": true,
                "kg": true,
                "info_kg": true
            }
        }
    }
    """
    try:
        from backend.auth.login_state_manager import get_login_state_manager
        
        user_id = request_data.get("user_id", "")
        
        if not user_id:
            return {
                "code": 400,
                "message": "用户ID不能为空",
                "data": None
            }
        
        manager = get_login_state_manager()
        status = await manager.check_and_load_user_systems(user_id)
        
        return {
            "code": 200,
            "message": "系统加载完成",
            "data": {
                "user_id": user_id,
                "systems": status
            }
        }
        
    except Exception as e:
        print(f"加载用户系统失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"加载用户系统失败: {str(e)}",
            "data": None
        }


@app.get("/api/auth/user/{user_id}")
async def get_user_info(user_id: str):
    """
    获取用户信息
    
    返回:
    {
        "code": 200,
        "message": "Success",
        "data": {
            "user_id": "xxx",
            "username": "user001",
            "email": "user@example.com",
            "nickname": "昵称",
            "avatar_url": "...",
            ...
        }
    }
    """
    try:
        from backend.auth.auth_service import get_auth_service
        
        auth_service = get_auth_service()
        user_info = auth_service.get_user_info(user_id)
        
        if user_info:
            return {
                "code": 200,
                "message": "Success",
                "data": user_info
            }
        else:
            return {
                "code": 404,
                "message": "用户不存",
                "data": None
            }
            
    except Exception as e:
        print(f"获取用户信息失败: {e}")
        return {
            "code": 500,
            "message": f"获取用户信息失败: {str(e)}",
            "data": None
        }


@app.put("/api/auth/user/{user_id}")
async def update_user_info(user_id: str, request_data: Dict[str, Any]):
    """
    更新用户信息
    
    请求体:
    {
        "nickname": "新昵称",
        "avatar_url": "...",
        "phone": "13800138000"
    }
    
    返回:
    {
        "code": 200,
        "message": "更新成功",
        "data": {...}
    }
    """
    try:
        from backend.auth.auth_service import get_auth_service
        
        auth_service = get_auth_service()
        result = auth_service.update_user_info(user_id, **request_data)
        
        if result['success']:
            return {
                "code": 200,
                "message": result['message'],
                "data": result.get('data')
            }
        else:
            return {
                "code": 400,
                "message": result['message'],
                "data": None
            }
            
    except Exception as e:
        print(f"更新用户信息失败: {e}")
        return {
            "code": 500,
            "message": f"更新用户信息失败: {str(e)}",
            "data": None
        }


@app.post("/api/auth/change-password")
async def change_password(request_data: Dict[str, Any]):
    """
    修改密码
    
    请求个
    {
        "user_id": "xxx",
        "old_password": "old123",
        "new_password": "new123"
    }
    
    返回:
    {
        "code": 200,
        "message": "密码修改成功",
        "data": null
    }
    """
    try:
        from backend.auth.auth_service import get_auth_service
        
        user_id = request_data.get("user_id", "")
        old_password = request_data.get("old_password", "")
        new_password = request_data.get("new_password", "")
        
        if not user_id or not old_password or not new_password:
            return {
                "code": 400,
                "message": "参数不完",
                "data": None
            }
        
        if len(new_password) < 6:
            return {
                "code": 400,
                "message": "新密码长度不能少",
                "data": None
            }
        
        auth_service = get_auth_service()
        result = auth_service.change_password(user_id, old_password, new_password)
        
        if result['success']:
            return {
                "code": 200,
                "message": result['message'],
                "data": None
            }
        else:
            return {
                "code": 400,
                "message": result['message'],
                "data": None
            }
            
    except Exception as e:
        print(f"修改密码失败: {e}")
        return {
            "code": 500,
            "message": f"修改密码失败: {str(e)}",
            "data": None
        }


@app.post("/api/auth/verify-token")
async def verify_token(request_data: Dict[str, Any]):
    """
    验证Token
    
    请求个
    {
        "token": "xxx"
    }
    
    返回:
    {
        "code": 200,
        "message": "Token有效",
        "data": {
            "user_id": "xxx",
            "valid": true
        }
    }
    """
    try:
        from backend.auth.auth_service import get_auth_service
        
        token = request_data.get("token", "")
        
        if not token:
            return {
                "code": 400,
                "message": "Token不能为空",
                "data": None
            }
        
        auth_service = get_auth_service()
        user_id = auth_service.verify_token(token)
        
        if user_id:
            return {
                "code": 200,
                "message": "Token有效",
                "data": {
                    "user_id": user_id,
                    "valid": True
                }
            }
        else:
            return {
                "code": 401,
                "message": "Token无效或已过期",
                "data": {
                    "valid": False
                }
            }
            
    except Exception as e:
        print(f"验证Token失败: {e}")
        return {
            "code": 500,
            "message": f"验证Token失败: {str(e)}",
            "data": None
        }


# ==================== 图片上传与分析 ====================

@app.post("/api/chat/upload-image")
async def upload_and_analyze_image(file: UploadFile = File(...), user_id: str = "default_user"):
    """上传图片并用通义千问视觉模型分析"""
    try:
        import base64
        contents = await file.read()
        b64_image = base64.b64encode(contents).decode('utf-8')
        mime_type = file.content_type or 'image/jpeg'
        
        # 用通义千问视觉模型分析图片
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            return {"code": 500, "message": "视觉模型未配置", "data": {"description": "图片已接收但无法分析"}}
        
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
        
        response = client.chat.completions.create(
            model="qwen-vl-plus",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64_image}"}},
                    {"type": "text", "text": "请用中文简洁描述这张图片的内容，包括场景、人物、物体等关键信息。不要使用emoji。"}
                ]
            }],
            max_tokens=300
        )
        
        description = response.choices[0].message.content.strip()
        print(f"图片分析结果: {description[:100]}")
        
        return {
            "code": 200,
            "message": "Success",
            "data": {"description": description, "filename": file.filename}
        }
    except Exception as e:
        print(f"图片分析失败: {e}")
        return {"code": 500, "message": str(e), "data": {"description": "图片分析失败"}}


@app.post("/api/chat/speech-to-text")
async def speech_to_text(file: UploadFile = File(...)):
    """语音转文字 - 使用通义千问语音模型"""
    try:
        contents = await file.read()
        
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            return {"code": 500, "message": "语音识别未配置", "data": {"text": ""}}
        
        import dashscope
        from dashscope.audio.asr import Recognition
        dashscope.api_key = api_key
        
        # 根据文件类型确定格式
        filename = file.filename or "audio.m4a"
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'm4a'
        fmt_map = {'m4a': 'mp4', 'mp4': 'mp4', 'wav': 'wav', 'mp3': 'mp3', 'aac': 'aac', 'ogg': 'ogg'}
        audio_format = fmt_map.get(ext, 'mp4')
        
        # 保存临时文件
        import tempfile
        suffix = f'.{ext}'
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        try:
            import threading
            import time
            import subprocess
            from dashscope.audio.asr import Recognition, RecognitionCallback

            # m4a/mp4 需要先转成 PCM wav，Recognition 流式接口只支持 PCM
            wav_path = tmp_path.replace(f'.{ext}', '.wav')
            try:
                subprocess.run(
                    ['ffmpeg', '-y', '-i', tmp_path, '-ar', '16000', '-ac', '1',
                     '-f', 'wav', wav_path],
                    capture_output=True, timeout=30
                )
                read_path = wav_path
                read_format = 'wav'
            except Exception:
                # ffmpeg 不可用，直接用原文件
                read_path = tmp_path
                read_format = audio_format

            result_holder: dict = {"text": "", "current": "", "done": False}

            class _Callback(RecognitionCallback):
                def on_open(self) -> None:
                    pass
                def on_close(self) -> None:
                    # 把最后一句也加进去
                    if result_holder["current"]:
                        result_holder["text"] += result_holder["current"]
                    result_holder["done"] = True
                def on_error(self, result) -> None:
                    print(f"语音识别回调错误: {result}")
                    result_holder["done"] = True
                def on_event(self, result) -> None:
                    sentence = result.get_sentence()
                    if sentence and isinstance(sentence, dict):
                        t = sentence.get("text", "")
                        if t:
                            # 覆盖当前句子（不累加，避免重复）
                            result_holder["current"] = t
                            # 如果是句子结束，追加到最终结果并清空当前句
                            if sentence.get("sentence_end", False):
                                result_holder["text"] += t
                                result_holder["current"] = ""

            rec = Recognition(
                model='paraformer-realtime-v2',
                callback=_Callback(),
                format=read_format,
                sample_rate=16000,
                language_hints=['zh', 'en']
            )
            rec.start()
            _start_time = time.time()
            with open(read_path, 'rb') as f:
                while True:
                    chunk = f.read(3200)
                    if not chunk:
                        break
                    rec.send_audio_frame(chunk)
            rec.stop()

            for _ in range(150):
                if result_holder["done"]:
                    break
                time.sleep(0.1)

            text = result_holder["text"]
            elapsed = time.time() - _start_time
            print(f"[语音识别] 识别结果: '{text}', done={result_holder['done']}, 耗时: {elapsed:.1f}s")

            # 清理 wav 临时文件
            try:
                if wav_path != tmp_path:
                    os.unlink(wav_path)
            except Exception:
                pass
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        
        return {"code": 200, "data": {"text": text}}
    except ImportError:
        return {"code": 200, "data": {"text": "(语音识别需要安装: pip install dashscope)"}}
    except Exception as e:
        print(f"语音识别失败: {e}")
        import traceback
        traceback.print_exc()
        return {"code": 500, "message": str(e), "data": {"text": ""}}


# ==================== WebSocket Agent对话API ====================

from backend.websocket_manager import ws_manager, MessageType

@app.websocket("/ws/agent-chat")
async def websocket_agent_chat(websocket: WebSocket):
    """
    WebSocket Agent对话接口 - 支持多轮对话
    
    消息格式:
    客户端发送: {
        "token": "xxx",  # 仅第一次消息需要
        "agent_type": "relationship|education|career",  # 仅第一次消息需要
        "message": "你好",
        "conversation_id": "xxx" (可选)
    }
    
    服务端返回:
    - {"type": "connected", "session_id": "xxx"}
    - {"type": "retrieval_start", ...}
    - {"type": "retrieval_complete", ...}
    - {"type": "tool_start", "tool_name": "xxx", "server_name": "xxx"}
    - {"type": "tool_complete", "tool_name": "xxx", "result": "xxx"}
    - {"type": "tool_failed", "tool_name": "xxx", "error": "xxx"}
    - {"type": "response", "content": "xxx", "tool_calls": [...]}
    - {"type": "error", "error": "xxx"}
    """
    import uuid
    session_id = f"agent_session_{uuid.uuid4().hex[:16]}"
    user_id = None
    agent = None  # 复用同一个Agent实例
    agent_type = None
    sync_callback_wrapper = None
    
    try:
        # 接受连接
        await websocket.accept()
        print(f"✅ [WebSocket Agent] 连接已建立: {session_id}")
        
        # 发送连接成功消息
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id
        })
        
        # ===== 主循环：持续接收消息 =====
        while True:
            try:
                # 接收客户端消息
                message_data = await websocket.receive_text()
                request_data = json.loads(message_data)
                
                # 第一次消息：验证token并创建Agent
                if user_id is None:
                    from backend.auth.auth_service import get_auth_service
                    auth_service = get_auth_service()
                    token = request_data.get("token", "")
                    user_id = auth_service.verify_token(token)
                    
                    if not user_id:
                        await websocket.send_json({
                            "type": "error",
                            "error": "Token无效或已过期"
                        })
                        break
                    
                    # 注册WebSocket连接
                    await ws_manager.connect(websocket, user_id, session_id)
                    
                    # 获取Agent类型
                    agent_type = request_data.get("agent_type", "relationship")
                    
                    print(f"🤖 [WebSocket Agent] 初始化: user_id={user_id}, agent_type={agent_type}")
                    
                    # 创建Agent（只创建一次，后续复用）
                    from backend.agents.langchain_specialized_agents import create_langchain_agent
                    from backend.learning.rag_manager import RAGManager
                    from backend.learning.unified_hybrid_retrieval import UnifiedHybridRetrieval
                    from backend.agents.mcp_integration import MCPHost
                    from backend.agents.specialized_mcp_servers import (
                        WebSearchMCPServer,
                        RelationshipMCPServer,
                        EducationMCPServer
                    )
                    import os
                    
                    # 获取系统实例
                    llm_service = get_or_init_llm_service()
                    if not llm_service or not llm_service.enabled:
                        await websocket.send_json({
                            "type": "error",
                            "error": "LLM服务不可用"
                        })
                        break
                    
                    rag_system = RAGManager.get_system(user_id)
                    retrieval_system = UnifiedHybridRetrieval(user_id)
                    
                    # 创建MCP Host
                    mcp_host = MCPHost(user_id=user_id)
                    
                    # 注册工具
                    search_api_key = os.getenv("QWEN_SEARCH_API_KEY")
                    search_host = os.getenv("QWEN_SEARCH_HOST")
                    
                    mcp_host.register_server(WebSearchMCPServer(
                        api_key=search_api_key,
                        host=search_host,
                        workspace=os.getenv("QWEN_SEARCH_WORKSPACE", "default"),
                        service_id=os.getenv("QWEN_SEARCH_SERVICE_ID", "ops-web-search-001")
                    ))
                    
                    if agent_type == 'relationship':
                        mcp_host.register_server(RelationshipMCPServer())
                    elif agent_type == 'education':
                        mcp_host.register_server(EducationMCPServer())
                    
                    # 创建WebSocket回调
                    loop = asyncio.get_event_loop()
                    
                    def sync_callback_wrapper(event_type: str, data: dict):
                        """同步包装器"""
                        async def send_callback():
                            if event_type == "tool_call":
                                status = data.get("status")
                                tool_name = data.get("tool_name")
                                
                                if status == "running":
                                    await ws_manager.send_message(user_id, session_id, {
                                        "type": "tool_start",
                                        "tool_name": tool_name,
                                        "server_name": "Unknown",
                                        "timestamp": datetime.now().isoformat()
                                    })
                                elif status == "completed":
                                    await ws_manager.send_message(user_id, session_id, {
                                        "type": "tool_complete",
                                        "tool_name": tool_name,
                                        "server_name": "Unknown",
                                        "result": data.get("output", "")[:100],
                                        "timestamp": datetime.now().isoformat()
                                    })
                                elif status == "error":
                                    await ws_manager.send_message(user_id, session_id, {
                                        "type": "tool_failed",
                                        "tool_name": tool_name,
                                        "server_name": "Unknown",
                                        "error": data.get("error", ""),
                                        "timestamp": datetime.now().isoformat()
                                    })
                            
                            elif event_type == "memory_retrieval":
                                retrieval_type = data.get("type")
                                
                                if retrieval_type == "retrieval_start":
                                    await ws_manager.send_message(user_id, session_id, {
                                        "type": "retrieval_start",
                                        "query": data.get("query"),
                                        "reason": data.get("reason"),
                                        "agent_type": data.get("agent_type"),
                                        "timestamp": data.get("timestamp")
                                    })
                                elif retrieval_type == "retrieval_complete":
                                    await ws_manager.send_message(user_id, session_id, {
                                        "type": "retrieval_complete",
                                        "query": data.get("query"),
                                        "reason": data.get("reason"),
                                        "results_count": data.get("results_count"),
                                        "sources": data.get("sources", []),
                                        "timestamp": data.get("timestamp")
                                    })
                        
                        try:
                            future = asyncio.run_coroutine_threadsafe(send_callback(), loop)
                            return future.result(timeout=0.5)
                        except Exception as e:
                            print(f"⚠️  回调执行失败: {event_type} - {e}")
                    
                    # 创建Agent
                    agent = create_langchain_agent(
                        agent_type=agent_type,
                        user_id=user_id,
                        llm_service=llm_service,
                        rag_system=rag_system,
                        retrieval_system=retrieval_system,
                        use_workflow=True,
                        mcp_host=mcp_host,
                        websocket_callback=sync_callback_wrapper
                    )
                    
                    await agent.initialize()
                    print(f"✅ [WebSocket Agent] Agent创建完成，等待消息...")
                
                # 获取消息内容
                message = request_data.get("message", "")
                if not message:
                    await websocket.send_json({
                        "type": "error",
                        "error": "消息不能为空"
                    })
                    continue  # 继续等待下一条消息
                
                print(f"📨 [WebSocket Agent] 收到消息: {message[:50]}...")
                
                # 处理消息
                import concurrent.futures
                loop = asyncio.get_event_loop()
                
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = await loop.run_in_executor(
                        pool,
                        agent.process,
                        message
                    )
                
                # 发送响应
                await ws_manager.send_message(user_id, session_id, {
                    "type": "response",
                    "content": result['response'],
                    "metadata": {
                        "mode": result.get('mode'),
                        "agent_used": result.get('agent_used'),
                        "tool_calls": result.get('tool_calls', []),
                        "retrieval_stats": result.get('retrieval_stats', {})
                    },
                    "timestamp": datetime.now().isoformat()
                })
                
                print(f"✅ [WebSocket Agent] 消息处理完成，等待下一条消息...")
                
            except WebSocketDisconnect:
                print(f"✓ [WebSocket Agent] 客户端主动断开连接")
                break
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "error": "消息格式错误"
                })
                continue
            except Exception as e:
                print(f"❌ [WebSocket Agent] 处理消息失败: {e}")
                import traceback
                traceback.print_exc()
                await websocket.send_json({
                    "type": "error",
                    "error": str(e)
                })
                continue  # 继续等待下一条消息
    
    except WebSocketDisconnect:
        print(f"✓ [WebSocket Agent] 连接已断开: {session_id}")
    except Exception as e:
        print(f"❌ [WebSocket Agent] 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if user_id:
            ws_manager.disconnect(user_id, session_id)
        print(f"🔌 [WebSocket Agent] 连接清理完成: {session_id}")


# ==================== WebSocket 流式聊天API ====================

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket 流式聊天接口 - HarmonyOS 真正的实时流式方案
    使用 WebSocket 替代 SSE,实现真正的实时双向通信
    
    消息格式:
    客户端发送: {"user_id": "xxx", "message": "你好"}
    服务端返回: {"type": "start", "session_id": "xxx"}
                {"type": "progress", "content": "..."}
                {"type": "thinking_chunk", "content": "..."}
                {"type": "answer_chunk", "content": "..."}
                {"type": "done"}
    """
    await websocket.accept()
    print(f"?? WebSocket 连接已建立")
    
    try:
        while True:
            # 接收客户端消息
            message_data = await websocket.receive_text()
            print(f"?? 收到 WebSocket 消息: {message_data[:100]}...")
            
            try:
                request_data = json.loads(message_data)
                user_id = request_data.get("user_id", "default_user")
                message = request_data.get("message", "")
                user_context = request_data.get("context", {})
                session_id = request_data.get("session_id")  # 前端可以传入session_id
                
                if not message:
                    await websocket.send_json({"type": "error", "content": "消息不能为空"})
                    continue
                
                # 生成或使用现有会话ID
                import uuid
                if not session_id:
                    session_id = f"session_{uuid.uuid4().hex[:16]}"
                
                # 保存用户消息到数据库
                from backend.conversation.conversation_storage import ConversationStorage
                save_result = ConversationStorage.save_message(
                    user_id=user_id,
                    session_id=session_id,
                    role="user",
                    content=message
                )
                print(f"?? [保存] 用户消息已保存: user_id={user_id}, session_id={session_id}, 结果={save_result}")
                
                # 对话数据会自动存储到Neo4j和RAG（由message_processor处理）
                
                # 同时保存到内存（用于当前会话）
                global chat_history_storage
                if user_id not in chat_history_storage:
                    chat_history_storage[user_id] = {}
                if session_id not in chat_history_storage[user_id]:
                    chat_history_storage[user_id][session_id] = []
                
                user_message_data = {
                    "role": "user",
                    "content": message,
                    "timestamp": datetime.now().isoformat()
                }
                chat_history_storage[user_id][session_id].append(user_message_data)
                
                # 发送开始信息
                await websocket.send_json({"type": "start", "session_id": session_id})
                
                # 获取用户系统
                systems = get_or_create_user_system(user_id)
                
                # 使用LLM服务处理
                llm_service = get_or_init_llm_service()
                
                # 发送进度：分析中
                await websocket.send_json({"type": "progress", "content": "正在分析你的问题..."})
                await asyncio.sleep(0.3)
                
                # 【特殊处理】检测是否是"用户选择不跳转"的请求
                skip_navigation = False
                original_question = message
                print(f"[调试] 收到消息: {message[:100]}...")
                
                if message.startswith("[用户选择不跳转]"):
                    skip_navigation = True
                    # 提取原始问题
                    if "请直接回答以下问题，不要建议跳转：" in message:
                        original_question = message.split("请直接回答以下问题，不要建议跳转：", 1)[1].strip()
                    elif "请继续回答之前的问题：" in message:
                        original_question = message.split("请继续回答之前的问题：", 1)[1].strip()
                    print(f"[智能路由] ? 检测到用户选择不跳转，跳过导航建议，原问题: {original_question}")
                else:
                    print(f"[智能路由] ? 消息不是【用户选择不跳转】格式，skip_navigation={skip_navigation}")
                
                # 【智能路由】检测用户意图，提供导航建议（除非用户选择不跳转）
                navigation_data = None
                has_navigation = False
                schedule_task_triggered = False  # 标记是否触发了日程生成
                
                if not skip_navigation:
                    try:
                        from backend.ai_core.intent_router import intent_router
                        intent_result = intent_router.analyze_intent(message)
                        
                        if intent_result["has_navigation_intent"]:
                            primary_route = intent_result.get("primary_route")
                            
                            # 【特殊处理】智能日程 - 使用LLM判断是否是明确的生成请求
                            if primary_route and primary_route.get("module") == "smart_schedule":
                                # 使用LLM判断是否是明确的生成日程请求
                                try:
                                    llm_service = get_or_init_llm_service()
                                    if llm_service and llm_service.enabled:
                                        check_prompt = f"""判断用户消息是否是明确要求生成/创建日程的请求。

用户消息："{message}"

判断标准：
- 明确要求：包含"生成"、"创建"、"安排"、"规划"等动作词 + "日程"
- 不明确：只是询问、查看、了解日程功能

只返回JSON格式：
{{"is_explicit_request": true/false, "confidence": 0.0-1.0, "reason": "简短理由"}}

只返回JSON，不要其他内容。"""
                                    
                                        response = llm_service.chat(
                                            [{"role": "user", "content": check_prompt}],
                                            temperature=0.1,
                                            response_format="json_object"
                                        )
                                        
                                        # 解析LLM响应
                                        response = response.strip()
                                        start = response.find('{')
                                        end = response.rfind('}') + 1
                                        if start >= 0 and end > start:
                                            response = response[start:end]
                                        
                                        check_result = json.loads(response)
                                        is_explicit = check_result.get("is_explicit_request", False)
                                        llm_confidence = check_result.get("confidence", 0)
                                        
                                        print(f"[智能日程检查] LLM判断: explicit={is_explicit}, confidence={llm_confidence}, reason={check_result.get('reason')}")
                                        
                                        # 只有在LLM明确判断为生成请求且置信度高时才触发
                                        if is_explicit and llm_confidence > 0.8:
                                            # 异步触发日程生成任务
                                            from backend.schedule.schedule_task_manager import task_manager, TaskType
                                            
                                            task_id = task_manager.create_task(
                                                user_id=user_id,
                                                task_type=TaskType.SCHEDULE_GENERATION,
                                                params={
                                                    "description": message,
                                                    "tasks": [],
                                                    "date": None
                                                }
                                            )
                                            
                                            # 后台异步执行（不阻塞当前对话）
                                            asyncio.create_task(
                                                task_manager.execute_schedule_generation(
                                                    task_id,
                                                    user_id,
                                                    {
                                                        "description": message,
                                                        "tasks": [],
                                                        "date": None
                                                    }
                                                )
                                            )
                                            
                                            schedule_task_triggered = True
                                            
                                            # 发送任务创建通知
                                            await websocket.send_json({
                                                "type": "system",
                                                "content": f"? 已开始为你生成智能日程（任务ID: {task_id[:8]}...）\n正在后台分析你的时间模式和任务需求，稍后可在智能日程页面查看结果。"
                                            })
                                            await asyncio.sleep(0.5)
                                            
                                            print(f"[智能日程] 已触发异步任务: {task_id}")
                                        else:
                                            print(f"[智能日程] 不触发任务 - 不是明确的生成请求")
                                            
                                except Exception as e:
                                    print(f"[智能日程] LLM检查失败: {e}")
                                    import traceback
                                    traceback.print_exc()
                            
                            # 生成导航提示（带"不跳转"选项）
                            nav_prompt = intent_router.generate_navigation_prompt(intent_result)
                            if nav_prompt:
                                has_navigation = True
                                # 添加"不跳转"选项提示
                                nav_prompt += "\n\n?? 如果不需要跳转，我也可以继续为你解答相关问题。"
                                
                                navigation_data = {
                                    "type": "navigation",
                                    "content": nav_prompt,
                                    "routes": intent_result["suggested_routes"],
                                    "primary_route": intent_result["primary_route"],
                                    "allow_continue": True  # 允许用户选择不跳转
                                }
                                # 发送导航建议
                                await websocket.send_json(navigation_data)
                                await asyncio.sleep(0.5)
                                print(f"[智能路由] 已发送导航建议: {intent_result['primary_route']['name']}")
                    except Exception as e:
                        print(f"[智能路由] 意图识别失败: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"[智能路由] 跳过导航建议（用户选择不跳转）")
                
                # 【关键逻辑】只在以下情况生成回答：
                # 1. 用户明确选择"不跳转"（skip_navigation=True）
                # 2. 没有导航建议（has_navigation=False）
                # 如果有导航建议且用户还没选择，则等待用户操作
                should_generate_answer = skip_navigation or not has_navigation
                
                if not should_generate_answer:
                    print(f"[回答生成] 已发送导航建议，等待用户选择...")
                    # 发送完成信号，让前端知道导航建议已发送完毕
                    await websocket.send_json({"type": "done"})
                    print(f"? [WebSocket] 会话 {session_id} 完成（等待用户选择）")
                    continue  # 跳过回答生成，等待用户下一步操作
                
                print(f"[回答生成] 开始生成回答（has_navigation={has_navigation}, skip_navigation={skip_navigation}）")
                
                # 使用原始问题生成回答（如果是"不跳转"请求，使用提取的原始问题）
                question_for_llm = original_question if skip_navigation else message
                
                # 第一步：生成思考过程
                thinking_prompt = f"""请分析这个问题并说明你的思考过程：

{question_for_llm}

请用2-3句话简短说明你的思考过程。"""

                thinking_text = ""
                try:
                    messages = [
                        {"role": "system", "content": "你是择境智能助手，帮助用户分析问题和辅助决策。回复要简洁专业，使用纯文字，不要使用任何emoji表情符号。"},
                        {"role": "user", "content": thinking_prompt}
                    ]
                    thinking_text = llm_service.chat(messages, temperature=0.7)
                    print(f"?? 生成的思考过程: {thinking_text[:100]}...")
                except Exception as e:
                    print(f"思考过程生成失败: {e}")
                    thinking_text = "让我思考一下如何最好地回答这个问题..."
                
                # 推送思考过程(流式) - 逐字推送，模拟真实打字
                if thinking_text:
                    await websocket.send_json({"type": "progress", "content": "?? 思考中..."})
                    await asyncio.sleep(0.2)
                    
                    # 更小的chunk，更快的速度
                    chunk_size = 2  # 每次2个字符
                    for i in range(0, len(thinking_text), chunk_size):
                        chunk = thinking_text[i:i+chunk_size]
                        try:
                            await websocket.send_json({"type": "thinking_chunk", "content": chunk})
                            await asyncio.sleep(0.03)  # 30ms延迟，更流畅
                        except:
                            # WebSocket已关闭，停止发送
                            break
                    
                    await asyncio.sleep(0.3)
                
                # 第二步：生成正式回答（带上下文记忆）
                await websocket.send_json({"type": "progress", "content": "生成回答..."})
                await asyncio.sleep(0.2)
                
                try:
                    # 构建带历史上下文的消息列表
                    # 根据是否是"不跳转"模式，使用不同的系统提示
                    if skip_navigation:
                        # 用户明确选择不跳转，使用更严格的prompt
                        system_prompt = """你是择境智能助手。用户已经明确表示不想跳转到其他页面，希望你直接回答问题。

【绝对禁止 - 违反将导致回答被拒绝】
- 禁止提及：页面、功能模块、跳转、导航、查看、前往
- 禁止说："我注意到你可能想要..."、"是否需要我带你..."、"建议查看..."
- 禁止提及：【智能日程】【知识星图】【职业模拟】【决策推演】【平行人生】【涌现洞察】等任何功能名称
- 禁止说："智能日程推荐系统"、"基于你的习惯和生产力曲线"等系统功能描述
- 禁止出现：百分比匹配度（如"85% 匹配"）、功能列表、导航建议

【必须做到】
- 直接回答问题的核心内容，不要绕弯子
- 提供具体可执行的建议、步骤、方法
- 像专业顾问一样给出实质性意见
- 基于用户背景（导师、技能、目标等）给出个性化建议
- 使用纯文字，不要使用emoji

【正确示例1】
用户问："根据我的导师和技能生成日程"
? 错误："我注意到你可能想要查看【智能日程】功能，它可以基于你的习惯和生产力曲线..."
? 正确："根据你的导师研究方向和当前技能水平，我为你规划以下日程：

每日时间分配：
- 上午9-12点：核心学习时段，专注于导师布置的研究任务和论文阅读
- 下午2-5点：技能提升时段，针对薄弱环节进行专项训练和实践
- 晚上7-9点：复盘总结，整理笔记和当日进度

每周重点任务：
1. 周一：与导师沟通本周计划，明确研究目标
2. 周三：中期进度检查，调整学习节奏
3. 周五：周总结和下周规划，记录收获

技能提升建议：
根据你的技能树，建议优先提升编程能力和数据分析技能，每天投入2小时进行刻意练习。"

【正确示例2】
用户问："我的职业发展路径"
? 错误："建议查看【职业模拟】功能，可以帮你..."
? 正确："基于你的背景，职业发展可以考虑以下路径：

技术专家路线：深耕技术领域，成为行业专家。适合喜欢钻研技术的人。
管理路线：从技术转向团队管理，需要培养沟通和领导能力。
创业路线：利用技术优势创业，风险高但潜力大。

建议先评估自己的兴趣和优势，再选择合适的路径。"

现在请直接回答用户的问题，提供实质性的分析和建议。记住：绝对不要提及任何功能、页面或跳转！"""

                    elif has_navigation:
                        # 有导航但用户还没选择，稍微温和一点
                        system_prompt = """你是择境智能助手，帮助用户分析问题和辅助决策。

【重要指令】请直接回答问题的实质内容，不要建议跳转。

回复要求：
- 直接回答用户问题的实质内容
- 提供具体的分析、建议和指导
- 不要提及"跳转"、"导航"、"查看XX页面"
- 使用纯文字，不要使用emoji表情符号"""
                    else:
                        system_prompt = "你是择境智能助手，帮助用户分析问题和辅助决策。回复要简洁专业，使用纯文字，不要使用任何emoji表情符号。"
                    
                    messages = [
                        {"role": "system", "content": system_prompt},
                    ]
                    
                    # 如果是skip_navigation模式，添加多个示例对话来强化行为
                    if skip_navigation:
                        messages.extend([
                            {"role": "user", "content": "根据我的导师和技能生成日程"},
                            {"role": "assistant", "content": "根据你的导师研究方向和当前技能水平，我为你规划以下日程安排：\n\n**每日时间分配：**\n- 上午9-12点：核心学习时段，专注研究任务\n- 下午2-5点：技能提升，针对薄弱环节训练\n- 晚上7-9点：复盘总结，整理笔记\n\n**每周重点：**\n1. 周一：与导师沟通计划\n2. 周三：中期进度检查\n3. 周五：周总结和规划\n\n建议根据导师的具体要求和你的技能短板，调整时间分配比例。"},
                            {"role": "user", "content": "我的职业发展路径"},
                            {"role": "assistant", "content": "基于你的背景，职业发展可以考虑以下路径：\n\n**技术专家路线：**\n- 深耕技术领域，成为行业专家\n- 适合喜欢钻研技术的人\n\n**管理路线：**\n- 从技术转向团队管理\n- 需要培养沟通和领导能力\n\n**创业路线：**\n- 利用技术优势创业\n- 风险高但潜力大\n\n建议先评估自己的兴趣和优势，再选择合适的路径。"}
                        ])
                        print(f"[LLM] 添加了多个few-shot示例来强化不跳转行为")
                    
                    # 【长期记忆】从RAG系统检索相关历史记忆（跨会话）
                    relevant_memories = []
                    try:
                        if systems.get('rag'):
                            from backend.learning.production_rag_system import MemoryType
                            # 检索相关的对话记忆（使用原始问题）
                            relevant_memories = systems['rag'].retrieve_memories(
                                query=question_for_llm,
                                memory_types=[MemoryType.CONVERSATION],
                                top_k=3  # 最多3条相关记忆
                            )
                        if relevant_memories:
                            print(f"?? [长期记忆] 检索到 {len(relevant_memories)} 条相关记忆")
                            # 将记忆作为系统上下文加入
                            memory_context = "\n".join([
                                f"[历史记忆 {i+1}] {mem['content'][:200]}"
                                for i, mem in enumerate(relevant_memories)
                            ])
                            messages.append({
                                "role": "system",
                                "content": f"以下是用户的相关历史记忆，可以帮助你更好地理解用户：\n{memory_context}"
                            })
                    except Exception as mem_err:
                        print(f"?? RAG记忆检索失败: {mem_err}")
                    
                    # 【短期记忆】加载当前会话的历史消息作为上下文（最近10轮）
                    try:
                        from backend.database.models import ConversationHistory, Database
                        from backend.database.config import DatabaseConfig
                        db = Database(DatabaseConfig.get_database_url())
                        db_session = db.get_session()
                        
                        print(f"?? [查询] 查询历史: user_id={user_id}, session_id={session_id}")
                        
                        history_rows = db_session.query(ConversationHistory).filter(
                            ConversationHistory.user_id == user_id,
                            ConversationHistory.session_id == session_id
                        ).order_by(ConversationHistory.timestamp.desc()).limit(20).all()
                        
                        print(f"?? [查询] 找到 {len(history_rows)} 条历史记录")
                        
                        db_session.close()
                        
                        # 倒序取出后反转为正序
                        history_count = 0
                        for row in reversed(history_rows):
                            if row.role in ('user', 'assistant') and row.content:
                                # 跳过当前这条用户消息（已经在最后加了）和错误回复
                                if row.content == message:
                                    print(f"  ??  跳过当前消息: {row.content[:50]}")
                                    continue
                                if '无法回答' in (row.content or ''):
                                    print(f"  ??  跳过错误回复: {row.content[:50]}")
                                    continue
                                
                                # 【关键】如果是skip_navigation模式，过滤掉包含导航提示的消息
                                if skip_navigation and row.role == 'assistant':
                                    # 检查是否包含导航相关的关键词（扩展列表）
                                    navigation_keywords = [
                                        '我注意到你可能想要查看',
                                        '是否需要我带你跳转',
                                        '【智能日程】',
                                        '【知识星图】',
                                        '【职业模拟】',
                                        '【决策推演】',
                                        '【平行人生】',
                                        '【涌现洞察】',
                                        '其他相关功能：',
                                        '建议查看：',
                                        '你可以查看',
                                        '跳转到',
                                        '导航到',
                                        '前往',
                                        '查看页面',
                                        '功能模块',
                                        '相关页面'
                                    ]
                                    if any(keyword in (row.content or '') for keyword in navigation_keywords):
                                        print(f"  ??  [不跳转模式] 跳过导航提示: {row.content[:50]}")
                                        continue
                                
                                messages.append({"role": row.role, "content": row.content})
                                history_count += 1
                                print(f"  ? 加载历史 [{row.role}]: {row.content[:50]}...")
                        
                        print(f"?? [短期记忆] 成功加载了 {history_count} 条会话历史")
                    except Exception as hist_err:
                        print(f"?? 加载历史上下文失败: {hist_err}")
                        import traceback
                        traceback.print_exc()
                    
                    # 当前用户消息（使用原始问题）
                    messages.append({"role": "user", "content": question_for_llm})
                    
                    print(f"?? 发送 {len(messages)} 条消息给LLM（含长期记忆+短期记忆）")
                    if skip_navigation:
                        print(f"   [不跳转模式] 使用原始问题: {question_for_llm[:100]}...")
                        print(f"   [不跳转模式] system_prompt 前100字符: {system_prompt[:100]}...")
                    final_response = llm_service.chat(messages, temperature=0.7)
                    
                    print(f"[调试] LLM 返回内容前200字符: {final_response[:200]}...")
                    
                    # 【后处理】如果是skip_navigation模式，检查并清理可能的导航提示
                    if skip_navigation:
                        navigation_patterns = [
                            '我注意到你可能想要查看',
                            '是否需要我带你跳转',
                            '【智能日程】',
                            '【知识星图】',
                            '【职业模拟】',
                            '【决策推演】',
                            '【平行人生】',
                            '【涌现洞察】',
                            '建议查看：',
                            '你可以查看',
                            '跳转到',
                            '导航到',
                            '智能日程推荐系统',
                            '基于你的习惯和生产力曲线',
                            '其他相关功能：',
                            '其他相关功能',
                            '是否需要我带你',
                            '带你跳转',
                            '% 匹配',
                            '匹配\n',
                            '智能日程\n',
                        ]
                        
                        # 检查是否包含导航提示
                        has_navigation_content = any(pattern in final_response for pattern in navigation_patterns)
                        
                        if has_navigation_content:
                            print(f"?? [不跳转模式] 检测到回答中仍包含导航提示，尝试重新生成...")
                            
                            # 添加更强的约束，重新生成
                            messages.append({
                                "role": "assistant",
                                "content": final_response
                            })
                            messages.append({
                                "role": "user",
                                "content": "请直接回答问题，不要提及任何页面、功能、跳转、导航。只给出实质性的建议和内容。"
                            })
                            
                            try:
                                # 最多重新生成3次
                                for retry_count in range(3):
                                    raw_response = llm_service.chat(messages, temperature=0.3)
                                    
                                    # 检查清理后的结果
                                    cleaned_response = raw_response
                                    for pattern in navigation_patterns:
                                        cleaned_response = cleaned_response.replace(pattern, '')
                                    
                                    # 如果清理后和原始响应有明显差异，说明清理生效了
                                    if len(cleaned_response) < len(raw_response) * 0.8:
                                        print(f"?? [不跳转模式] 第{retry_count + 1}次重新生成后清理了导航内容")
                                        # 不要用被清理的版本，而是尝试继续修复
                                        messages.append({"role": "assistant", "content": raw_response})
                                        messages.append({
                                            "role": "user",
                                            "content": "你的回答中仍然包含了跳转/导航相关的内容。请完全忽略之前的回答，重新回答：直接告诉我具体的学习日程安排是什么？"
                                        })
                                        continue
                                    else:
                                        # 清理后内容变化不大，使用清理后的版本
                                        final_response = cleaned_response
                                        print(f"? [不跳转模式] 重新生成成功")
                                        break
                                else:
                                    # 3次都失败，使用清理后的版本
                                    final_response = cleaned_response
                                    print(f"?? [不跳转模式] 3次重新生成后仍有问题，使用清理版本")
                            except Exception as retry_err:
                                print(f"?? [不跳转模式] 重新生成失败: {retry_err}")
                                # 如果重新生成失败，至少清理掉明显的导航提示
                                for pattern in navigation_patterns:
                                    final_response = final_response.replace(pattern, '')
                    
                    print(f"回答: {final_response[:100]}...")
                except Exception as e:
                    print(f"LLM调用失败: {e}")
                    final_response = f"抱歉，我现在无法回答。错误：{str(e)}"
                
                # 推送回复内容(流式) - 逐字推送，模拟真实打字
                if final_response:
                    print(f"?? [WebSocket] 推送回复内容，长度: {len(final_response)}")
                    
                    # 更小的chunk，更快的速度
                    chunk_size = 3  # 每次3个字符
                    for i in range(0, len(final_response), chunk_size):
                        chunk = final_response[i:i+chunk_size]
                        await websocket.send_json({"type": "answer_chunk", "content": chunk})
                        await asyncio.sleep(0.025)  # 25ms延迟，更流畅
                    
                    # 推送完成信息
                    await websocket.send_json({"type": "done"})
                    print(f"? [WebSocket] 会话 {session_id} 完成（生成了回答）")
                    
                    # 保存AI回复到数据库
                    from backend.conversation.conversation_storage import ConversationStorage
                    save_result = ConversationStorage.save_message(
                        user_id=user_id,
                        session_id=session_id,
                        role="assistant",
                        content=final_response,
                        thinking=thinking_text
                    )
                    print(f"?? [保存] AI回复已保存: session_id={session_id}, 结果={save_result}")
                    
                    # 同时保存到RAG系统（用于LoRA训练）
                    try:
                        if systems.get('rag'):
                            from backend.learning.production_rag_system import MemoryType
                            conversation_content = f"用户: {message}\nAI: {final_response}"
                            systems['rag'].add_memory(
                                memory_type=MemoryType.CONVERSATION,
                                content=conversation_content,
                                metadata={
                                    "session_id": session_id,
                                    "thinking": thinking_text
                                }
                            )
                            print(f"? 对话已保存到RAG系统")
                        else:
                            print(f"?? RAG系统未初始化，跳过保存")
                    except Exception as e:
                        print(f"?? 保存到RAG系统失败: {e}")
                    
                    # 同时保存到内存（用于当前会话）
                    ai_message_data = {
                        "role": "assistant",
                        "content": final_response,
                        "thinking": thinking_text,
                        "timestamp": datetime.now().isoformat()
                    }
                    chat_history_storage[user_id][session_id].append(ai_message_data)
                    print(f"?? 已保存对话到数据库和内存，会话 {session_id}，共 {len(chat_history_storage[user_id][session_id])} 条消息")
                    
                    # 添加到RAG记忆
                    try:
                        if systems.get('rag'):
                            systems['rag'].add_memory(
                                memory_type=MemoryType.CONVERSATION,
                                content=message,
                                metadata={"user_id": user_id, "response": final_response},
                                importance=0.7
                            )
                    except Exception as e:
                        print(f"?? 对话记忆保存失败: {e}")
                
                # 【新】使用消息处理器异步提取信息到知识图谱和RAG
                try:
                    from backend.conversation.message_processor import get_message_processor
                    
                    processor = get_message_processor()
                    
                    # 异步提交到后台处理（不阻塞响应）
                    asyncio.create_task(processor.submit_message(
                        user_id=user_id,
                        message=message,
                        session_id=session_id,
                        metadata={
                            "timestamp": datetime.now().isoformat(),
                            "ai_response": final_response[:200]  # 包含AI回复的前200字符作为上下文
                        }
                    ))
                    
                    print(f"✅ [知识提取] 消息已提交到后台处理队列")
                    
                except Exception as e:
                    print(f"⚠️ [知识提取] 提交消息失败: {e}")
                
                # 清除人物关系图谱缓存，让前端获取最新数据
                try:
                    import redis
                    redis_client = redis.Redis(
                        host=os.getenv("REDIS_HOST", "localhost"),
                        port=int(os.getenv("REDIS_PORT", 6379)),
                        db=int(os.getenv("REDIS_DB", 0)),
                        decode_responses=True
                    )
                    # 清除该用户的知识图谱缓存
                    patterns = [
                        f"kg_export:{user_id}*",
                        f"kg_data:{user_id}*",
                        f"people_graph:{user_id}*",
                        f"llm_classify:*"  # 清除分类缓存，让新节点重新分类
                    ]
                    
                    total_deleted = 0
                    for pattern in patterns:
                        keys = redis_client.keys(pattern)
                        if keys:
                            redis_client.delete(*keys)
                            total_deleted += len(keys)
                    
                    if total_deleted > 0:
                        print(f"✅ 已清除 {total_deleted} 个缓存项")
                except Exception as cache_err:
                    print(f"⚠️ 清除缓存失败: {cache_err}")
                
            except json.JSONDecodeError:
                try:
                    await websocket.send_json({"type": "error", "content": "无效的JSON格式"})
                except:
                    pass  # WebSocket已关闭，忽略
            except Exception as e:
                print(f"[WebSocket] 处理失败: {e}")
                import traceback
                traceback.print_exc()
                try:
                    await websocket.send_json({"type": "error", "content": str(e)})
                except:
                    pass  # WebSocket已关闭，忽略
                
    except WebSocketDisconnect:
        print("✓ WebSocket 连接已断开")
    except Exception as e:
        print(f"[WebSocket] 错误: {e}")
        import traceback
        traceback.print_exc()


# ==================== 会话管理API ====================

# 全局对话历史存储 {user_id: {session_id: [messages]}}
chat_history_storage = {}

@app.get("/api/chat/sessions/{user_id}")
async def get_user_sessions(user_id: str):
    """获取用户的所有会话列表 - 从数据库读取"""
    try:
        from backend.database.models import ConversationHistory, Database
        from backend.database.config import DatabaseConfig
        from sqlalchemy import func, distinct
        
        db = Database(DatabaseConfig.get_database_url())
        session = db.get_session()
        
        # 查询该用户所有不同的session_id及其消息统计
        results = session.query(
            ConversationHistory.session_id,
            func.count(ConversationHistory.id).label('msg_count'),
            func.min(ConversationHistory.timestamp).label('created_at'),
            func.max(ConversationHistory.timestamp).label('updated_at')
        ).filter(
            ConversationHistory.user_id == user_id,
            ConversationHistory.session_id != None
        ).group_by(
            ConversationHistory.session_id
        ).order_by(
            func.max(ConversationHistory.timestamp).desc()
        ).all()
        
        sessions = []
        for row in results:
            # 获取第一条用户消息作为标题
            first_msg = session.query(ConversationHistory.content).filter(
                ConversationHistory.user_id == user_id,
                ConversationHistory.session_id == row.session_id,
                ConversationHistory.role == 'user'
            ).order_by(ConversationHistory.timestamp.asc()).first()
            
            title = (first_msg.content[:30] + "...") if first_msg and first_msg.content else "新对话"
            
            sessions.append({
                "session_id": row.session_id,
                "title": title,
                "message_count": row.msg_count,
                "created_at": row.created_at.isoformat() if row.created_at else "",
                "last_time": row.updated_at.isoformat() if row.updated_at else "",
                "preview": first_msg.content[:50] if first_msg and first_msg.content else ""
            })
        
        session.close()
        
        return {
            "code": 200,
            "message": "Success",
            "data": {"sessions": sessions}
        }
    
    except Exception as e:
        print(f"获取会话列表失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/chat/session/{user_id}/{session_id}")
async def get_session_history(user_id: str, session_id: str):
    """
    获取指定会话的历史消息
    
    返回格式:
    {
        "code": 200,
        "data": {
            "session_id": "xxx",
            "messages": [
                {
                    "role": "user",
                    "content": "你好",
                    "timestamp": "2024-01-01T10:00:00"
                },
                {
                    "role": "assistant",
                    "content": "你好！有什么可以帮助你的吗？",
                    "thinking": "用户打招呼，我应该友好回应",
                    "timestamp": "2024-01-01T10:00:01"
                }
            ]
        }
    }
    """
    try:
        from backend.database.models import ConversationHistory, Database
        from backend.database.config import DatabaseConfig
        
        db = Database(DatabaseConfig.get_database_url())
        session = db.get_session()
        
        rows = session.query(ConversationHistory).filter(
            ConversationHistory.user_id == user_id,
            ConversationHistory.session_id == session_id
        ).order_by(ConversationHistory.timestamp.asc()).all()
        
        session.close()
        
        if not rows:
            # 也检查内存
            if user_id in chat_history_storage and session_id in chat_history_storage[user_id]:
                messages = chat_history_storage[user_id][session_id]
            else:
                return {"code": 404, "message": "Session not found", "data": None}
        else:
            messages = [
                {
                    "id": str(r.id),
                    "role": r.role,
                    "content": r.content or "",
                    "thinking": r.thinking,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else ""
                }
                for r in rows
            ]
        
        return {
            "code": 200,
            "message": "Success",
            "data": {
                "session_id": session_id,
                "messages": messages
            }
        }
    
    except Exception as e:
        print(f"获取会话历史失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.post("/api/chat/session/new/{user_id}")
async def create_new_session(user_id: str):
    """
    创建新会话
    
    返回格式:
    {
        "code": 200,
        "data": {
            "session_id": "session_xxx"
        }
    }
    """
    try:
        import uuid
        session_id = f"session_{uuid.uuid4().hex[:16]}"
        
        # 初始化用户存储
        if user_id not in chat_history_storage:
            chat_history_storage[user_id] = {}
        
        # 创建新会话
        chat_history_storage[user_id][session_id] = []
        
        return {
            "code": 200,
            "message": "Session created",
            "data": {"session_id": session_id}
        }
    
    except Exception as e:
        print(f"创建会话失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== V4 对话API（前端新版本使用）====================

@app.get("/api/v4/conversations/{user_id}/list")
async def get_conversations_v4(user_id: str):
    """
    V4: 获取用户的所有对话列表（从数据库读取）
    
    返回格式:
    {
        "success": true,
        "data": [
            {
                "id": "session_xxx",
                "title": "关于健康的对话",
                "preview": "最近我感觉...",
                "message_count": 10,
                "last_message_time": "2024-01-01T11:00:00"
            }
        ]
    }
    """
    try:
        from backend.conversation.conversation_storage import ConversationStorage
        
        conversations = ConversationStorage.get_user_sessions(user_id)
        
        return {
            "success": True,
            "data": conversations  # 改为 data 字段，与前端接口一致
        }
    
    except Exception as e:
        print(f"获取对话列表失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "conversations": []
        }


@app.get("/api/v4/conversations/{user_id}/{session_id}/messages")
async def get_conversation_messages_v4(user_id: str, session_id: str):
    """
    V4: 获取指定对话的消息列表（从数据库读取）
    
    返回格式:
    {
        "success": true,
        "data": [
            {
                "id": "123",
                "role": "user",
                "content": "你好",
                "timestamp": "2024-01-01T10:00:00"
            },
            {
                "id": "124",
                "role": "assistant",
                "content": "你好！",
                "thinking": "用户打招呼",
                "timestamp": "2024-01-01T10:00:01"
            }
        ]
    }
    """
    try:
        from backend.conversation.conversation_storage import ConversationStorage
        
        messages = ConversationStorage.get_session_messages(user_id, session_id)
        
        return {
            "success": True,
            "data": messages  # 改为 data 字段，与前端接口一致
        }
    
    except Exception as e:
        print(f"获取对话消息失败: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "messages": []
        }


@app.post("/api/v4/conversations/{user_id}/create")
async def create_conversation_v4(user_id: str):
    """
    V4: 创建新对话
    
    返回格式:
    {
        "success": true,
        "data": {
            "conversation_id": "session_xxx"
        }
    }
    """
    try:
        import uuid
        session_id = f"session_{uuid.uuid4().hex[:16]}"
        
        # 初始化用户存储
        if user_id not in chat_history_storage:
            chat_history_storage[user_id] = {}
        
        # 创建新会话
        chat_history_storage[user_id][session_id] = []
        
        print(f"? 创建新对话: {session_id} for user {user_id}")
        
        return {
            "success": True,
            "data": {
                "conversation_id": session_id
            }
        }
    
    except Exception as e:
        print(f"创建对话失败: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "conversation_id": None
        }


# ==================== 反馈API ====================

@app.post("/api/hybrid/feedback")
async def submit_feedback(request_data: Dict[str, Any]):
    """
    提交用户反馈 - 使用真实的强化学习训    
    请求个
    {
        "user_id": "user_001",
        "rating": 5,
        "helpful": true,
        "action_taken": true,
        "action": "exercise",
        "state": {"health_score": 75, "mood": 7, "stress_level": 5},
        "strategy": "hybrid",
        "comments": "非常有帮助!"
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        rating = request_data.get("rating", 3)
        helpful = request_data.get("helpful", False)
        action_taken = request_data.get("action_taken", False)
        action = request_data.get("action", "unknown")
        state = request_data.get("state", {})
        strategy = request_data.get("strategy", "hybrid")
        
        # 使用真实的强化学习训练器
        from backend.learning.rl_trainer import get_rl_trainer, FeedbackType
        rl_trainer = get_rl_trainer(user_id)
        
        # 确定反馈类型
        if action_taken:
            feedback_type = FeedbackType.ADOPTED
        elif helpful:
            feedback_type = FeedbackType.HELPFUL
        elif rating >= 4:
            feedback_type = FeedbackType.HELPFUL
        elif rating >= 3:
            feedback_type = FeedbackType.NEUTRAL
        elif rating >= 2:
            feedback_type = FeedbackType.UNHELPFUL
        else:
            feedback_type = FeedbackType.HARMFUL
        
        # 记录交互并训        training_result = rl_trainer.record_interaction(state, action, feedback_type, strategy)
        
        # 获取训练统计
        stats = rl_trainer.get_training_statistics()
        
        # 评估策略性能
        strategy_performance = rl_trainer.evaluate_strategy_performance()
        
        # 评估推荐性能
        recommendation_performance = rl_trainer.evaluate_recommendation_performance()
        
        return {
            "code": 200,
            "message": "Feedback recorded and model trained",
            "data": {
                "training_result": training_result,
                "evolution_metrics": {
                    "total_samples": stats['total_episodes'],
                    "confidence_score": stats['average_reward'],
                    "best_strategy": stats['best_strategy'],
                    "best_recommendation": stats['best_recommendation']
                },
                "strategy_performance": strategy_performance,
                "recommendation_performance": recommendation_performance
            }
        }
    
    except Exception as e:
        print(f"反馈提交失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== 进化指标API ====================

@app.get("/api/chat/sessions/{user_id}")
async def get_user_sessions(user_id: str):
    """
    获取用户的所有会话列    
    返回:
    {
        "code": 200,
        "message": "Success",
        "data": {
            "sessions": [
                {
                    "session_id": "xxx",
                    "title": "对话标题",
                    "start_time": "2024-01-01T00:00:00",
                    "last_time": "2024-01-01T01:00:00",
                    "message_count": 10,
                    "is_current": true
                }
            ]
        }
    }
    """
    try:
        from llm.enhanced_conversation_manager import get_conversation_manager
        
        manager = get_conversation_manager(user_id)
        sessions = manager.get_all_sessions()
        
        return {
            "code": 200,
            "message": "Success",
            "data": {
                "sessions": sessions
            }
        }
    except Exception as e:
        print(f"获取会话列表失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/chat/session/{user_id}/{session_id}")
async def get_session_history(user_id: str, session_id: str):
    """
    获取指定会话的历史记忆    
    返回:
    {
        "code": 200,
        "message": "Success",
        "data": {
            "session_id": "xxx",
            "history": [
                {
                    "role": "user",
                    "content": "消息内容",
                    "timestamp": "2024-01-01T00:00:00"
                }
            ]
        }
    }
    """
    try:
        from llm.enhanced_conversation_manager import get_conversation_manager
        
        manager = get_conversation_manager(user_id, session_id=session_id)
        history = manager.get_conversation_history()
        
        return {
            "code": 200,
            "message": "Success",
            "data": {
                "session_id": session_id,
                "history": history
            }
        }
    except Exception as e:
        print(f"获取会话历史失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.delete("/api/chat/session/{user_id}/{session_id}")
async def delete_session(user_id: str, session_id: str):
    """
    删除指定会话
    
    返回:
    {
        "code": 200,
        "message": "Session deleted",
        "data": null
    }
    """
    try:
        from llm.enhanced_conversation_manager import get_conversation_manager
        
        manager = get_conversation_manager(user_id)
        manager.delete_session(session_id)
        
        return {
            "code": 200,
            "message": "Session deleted",
            "data": None
        }
    except Exception as e:
        print(f"删除会话失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.post("/api/chat/session/new/{user_id}")
async def create_new_session(user_id: str):
    """
    创建新会    
    返回:
    {
        "code": 200,
        "message": "New session created",
        "data": {
            "session_id": "xxx"
        }
    }
    """
    try:
        from llm.enhanced_conversation_manager import get_conversation_manager, clear_conversation_manager_cache
        
        # 清除缓存,强制创建新会话
        clear_conversation_manager_cache(user_id)
        
        manager = get_conversation_manager(user_id)
        
        return {
            "code": 200,
            "message": "New session created",
            "data": {
                "session_id": manager.session_id
            }
        }
    except Exception as e:
        print(f"创建新会话失 {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== 进化指标API ====================

@app.get("/api/hybrid/strategy/{user_id}")
async def get_hybrid_strategy(user_id: str):
    """获取混合智能策略"""
    try:
        hybrid_system = get_or_create_hybrid_system(user_id)
        
        # 获取当前策略
        strategy = {
            "user_id": user_id,
            "current_strategy": "balanced",
            "ai_weight": 0.6,
            "human_weight": 0.4,
            "confidence": 0.75,
            "recommendations": [
                "继续当前策略",
                "增加AI辅助比重"
            ]
        }
        
        return {
            "code": 200,
            "message": "Success",
            "data": strategy
        }
    except Exception as e:
        print(f"获取策略失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.get("/api/hybrid/evolution/{user_id}")
async def get_evolution_metrics(user_id: str):
    """获取进化指标"""
    try:
        systems = get_or_create_user_system(user_id)
        
        stats = systems['learner'].get_statistics()
        
        return {
            "code": 200,
            "data": {
                "totalSamples": stats['total_episodes'],
                "confidenceScore": stats['average_reward'],
                "accuracy": 0.75,
                "domainMetrics": {
                    "health": {"accuracy": 0.8, "samples": 100},
                    "time": {"accuracy": 0.75, "samples": 80},
                    "emotion": {"accuracy": 0.7, "samples": 60}
                },
                "recommendedStrategy": "hybrid",
                "lastUpdated": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        print(f"获取进化指标失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== AI对话API - SSE流式输出 ====================

# ==================== AI对话API - SSE流式输出 ====================

from backend.conversation.conversational_ai import ConversationalAI

# 全局对话系统实例
conversational_ai_system = None

def get_conversational_ai():
    """获取对话系统"""
    global conversational_ai_system
    if conversational_ai_system is None:
        from backend.startup_manager import StartupManager
        # 获取必要的系统组件
        meta_agent = StartupManager.get_system('meta_agent')
        kg = StartupManager.get_system('knowledge_graph')
        evolving_system = StartupManager.get_system('evolving_system')
        multimodal_fusion = StartupManager.get_system('multimodal_fusion')
        
        conversational_ai_system = ConversationalAI(
            meta_agent=meta_agent,
            knowledge_graph=kg,
            evolving_system=evolving_system,
            multimodal_fusion=multimodal_fusion
        )
    return conversational_ai_system


# ==================== LoRA 个性化训练 API ====================\n# 已删除：LoRA模块已移除\n\n# ==================== 流式聊天 API ====================

from backend.conversation.simple_streaming import router as streaming_router
app.include_router(streaming_router)

print("流式聊天 API 已加载")
print("   - POST /api/chat/stream - 流式聊天")
print("   - POST /api/chat/chat - 完整聊天")
print("   - GET /api/chat/health - 健康检查")


# ==================== 记忆查询 API ====================

@app.get("/api/memory/stats/{user_id}")
async def get_memory_stats(user_id: str):
    """获取用户的记忆统计信息"""
    try:
        from llm.enhanced_memory_retriever import get_enhanced_memory_retriever
        
        retriever = get_enhanced_memory_retriever(user_id)
        stats = retriever.get_memory_statistics()
        
        return {
            "code": 200,
            "message": "Success",
            "data": stats
        }
    except Exception as e:
        print(f"获取记忆统计失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/memory/list/{user_id}")
async def list_memories(user_id: str, memory_type: Optional[str] = None, limit: int = 10):
    """列出用户的记忆"""
    try:
        from llm.enhanced_memory_retriever import get_enhanced_memory_retriever, MemoryType
        
        retriever = get_enhanced_memory_retriever(user_id)
        
        if memory_type:
            # 按类型检查            mem_type = MemoryType(memory_type)
            memories = retriever.retrieve_by_type(mem_type, top_k=limit)
            
            return {
                "code": 200,
                "message": "Success",
                "data": {
                    "memories": [
                        {
                            "id": m.memory_id,
                            "type": m.memory_type.value,
                            "content": m.content,
                            "importance": m.importance,
                            "timestamp": m.timestamp.isoformat(),
                            "access_count": m.access_count
                        }
                        for m in memories
                    ]
                }
            }
        else:
            # 返回所有记忆            all_memories = sorted(retriever.memories, key=lambda x: x.timestamp, reverse=True)[:limit]
            
            return {
                "code": 200,
                "message": "Success",
                "data": {
                    "memories": [
                        {
                            "id": m.memory_id,
                            "type": m.memory_type.value,
                            "content": m.content,
                            "importance": m.importance,
                            "timestamp": m.timestamp.isoformat(),
                            "access_count": m.access_count
                        }
                        for m in all_memories
                    ]
                }
            }
    except Exception as e:
        print(f"列出记忆失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.get("/api/lora/models")
async def list_lora_models():
    """列出所有用户的 LoRA 模型"""
    try:
        import os
        models_dir = "./models/lora"
        
        if not os.path.exists(models_dir):
            return {
                "code": 200,
                "message": "Success",
                "data": {"models": []}
            }
        
        models = []
        for user_id in os.listdir(models_dir):
            user_dir = os.path.join(models_dir, user_id)
            if os.path.isdir(user_dir):
                # 查找最新版本
                versions = [d for d in os.listdir(user_dir) 
                           if d.startswith('v') and os.path.isdir(os.path.join(user_dir, d))]
                if versions:
                    latest_version = sorted(versions, key=lambda x: int(x[1:]))[-1]
                    final_path = os.path.join(user_dir, latest_version, "final")
                    
                    # 检查final 目录是否存在
                    if os.path.exists(final_path):
                        models.append({
                            "user_id": user_id,
                            "version": latest_version,
                            "path": final_path
                        })
        
        return {
            "code": 200,
            "message": "Success",
            "data": {
                "models": models,
                "total": len(models)
            }
        }
    except Exception as e:
        print(f"列出 LoRA 模型失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== 心理测评系统 API ====================

# 全局心理测评系统
personality_test = None

def get_personality_test():
    """获取心理测评系统(单例)"""
    global personality_test
    if personality_test is None:
        from personality.personality_test import PersonalityTest
        personality_test = PersonalityTest()
    return personality_test

@app.get("/api/personality/questions")
async def get_personality_questions():
    """获取心理测评题目"""
    try:
        test = get_personality_test()
        questions_data = test.get_questions()
        
        return {
            "code": 200,
            "message": "Success",
            "data": questions_data
        }
    except Exception as e:
        print(f"获取测评题目失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.post("/api/personality/submit")
async def submit_personality_test(request_data: Dict[str, Any]):
    """
    提交心理测评答案
    
    请求个
    {
        "user_id": "user_001",
        "answers": {
            "1": 3,
            "2": 4,
            ...
        }
    }
    """
    try:
        user_id = request_data.get("user_id")
        answers = request_data.get("answers", {})
        
        if not user_id:
            return {
                "code": 400,
                "message": "user_id 不能为空",
                "data": None
            }
        
        if not answers:
            return {
                "code": 400,
                "message": "answers 不能为空",
                "data": None
            }
        
        # 转换答案格式(字符串key转整数)
        answers_int = {int(k): int(v) for k, v in answers.items()}
        
        # 计算性格画像
        test = get_personality_test()
        profile = test.calculate_profile(user_id, answers_int)
        
        # 保存画像
        test.save_profile(profile)
        
        # 返回结果
        return {
            "code": 200,
            "message": "测评完成",
            "data": {
                "profile": profile.to_dict(),
                "summary": profile.get_summary()
            }
        }
    except Exception as e:
        print(f"提交测评失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.get("/api/personality/profile/{user_id}")
async def get_personality_profile(user_id: str):
    """获取用户的性格画像"""
    try:
        test = get_personality_test()
        profile = test.load_profile(user_id)
        
        if profile is None:
            return {
                "code": 404,
                "message": "未找到该用户的性格画像,请先完成测",
                "data": None
            }
        
        return {
            "code": 200,
            "message": "Success",
            "data": {
                "profile": profile.to_dict(),
                "summary": profile.get_summary()
            }
        }
    except Exception as e:
        print(f"获取性格画像失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== 决策模拟系统 API ====================

# 注册教育升学决策 API（信息收集 + 决策模拟）- 旧版本
# from backend.decision.education_decision_api_new import router as education_decision_router
# app.include_router(education_decision_router)

# 注册决策人格API（7个决策人格系统）- 新版本
from backend.decision.persona_decision_api import router as persona_decision_router
from backend.decision.persona_decision_api import compat_router as persona_compat_router
app.include_router(persona_decision_router)
app.include_router(persona_compat_router)  # 向后兼容路由

# 注册 Future OS API（知识星图系统：人物关系 / 职业发展 / 教育升学）
from backend.decision.future_os_api import router as future_os_router
app.include_router(future_os_router)

# 注册 AI 核心智能路由 API（意图识别 + 功能导航）
from backend.ai_core.ai_core_api import router as ai_core_router
app.include_router(ai_core_router)
print("AI 核心智能路由 API 已加载")

# 注册好友管理 API
from backend.social.friend_api import router as friend_router
app.include_router(friend_router)
print("好友管理 API 已加载")

# 注册树洞 API
from backend.social.tree_hole_api import router as tree_hole_router
app.include_router(tree_hole_router)
print("树洞 API 已加载")

# 在 app 级别注册决策推演 WebSocket（与 /ws/chat 同级，确保反向代理兼容）
# 注意：新的决策人格系统使用 /api/decision/persona/ws/simulate-option
# 这个端点保留用于向后兼容，但重定向到新系统
@app.websocket("/ws/decision-simulate")
async def decision_simulate_ws(websocket: WebSocket):
    """决策推演 WebSocket - 向后兼容端点，重定向到新的决策人格系统"""
    await websocket.accept()
    try:
        await websocket.send_json({
            "type": "redirect",
            "message": "请使用新的决策人格系统端点: /api/decision/persona/ws/simulate-option",
            "new_endpoint": "/api/decision/persona/ws/simulate-option"
        })
        await websocket.close()
    except Exception as e:
        print(f"[WS] WebSocket 处理异常: {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.close(code=1011, reason=f"服务器错误: {str(e)[:100]}")
        except:
            pass

print("增强决策 API 已加载（含 app 级 WebSocket）")
print("Future OS API 已加载")
print("   - GET /api/v5/future-os/knowledge/{user_id}")
print("   - POST /api/v5/future-os/context")
print("   - POST /api/v5/future-os/route")
print("   - POST /api/v5/future-os/simulate")
print("   - GET /api/v5/future-os/history/{user_id}")
print("   - GET /api/v5/future-os/simulations/{simulation_id}")
print("   - POST /api/v5/future-os/parallel-life/branch")
print("   - POST /api/v5/future-os/parallel-life/complete")

# ==================== 实时智慧洞察Agent API ====================

# 注册实时智慧洞察Agent API（人际关系 + 教育升学 + 职业规划）
from backend.insights.realtime_insight_api import router as realtime_insight_router
app.include_router(realtime_insight_router, prefix="/api/insights/realtime", tags=["realtime-insights"])

print("✅ 实时智慧洞察Agent API 已加载")
print("   - POST /api/insights/realtime/relationship/insight - 人际关系洞察")
print("   - POST /api/insights/realtime/education/insight - 教育升学洞察")
print("   - POST /api/insights/realtime/career/insight - 职业规划洞察")
print("   - GET /api/insights/realtime/agents/status - Agent状态")

# ==================== LoRA状态API ====================

# 全局LoRA调度器
lora_scheduler = None

def get_lora_scheduler():
    """获取LoRA调度器实例（单例）"""
    global lora_scheduler
    if lora_scheduler is None:
        from backend.lora.lora_scheduler import get_scheduler
        lora_scheduler = get_scheduler()
    return lora_scheduler


@app.get("/api/lora/progress/{user_id}")
async def get_lora_training_progress(user_id: str):
    """获取LoRA训练实时进度"""
    try:
        from backend.lora.auto_lora_trainer import get_training_progress
        progress = get_training_progress(user_id)
        return {"code": 200, "data": progress}
    except Exception as e:
        return {"code": 200, "data": {"is_training": False, "progress": 0, "stage": "", "error": None}}


@app.get("/api/lora/status/{user_id}")
async def get_lora_status(user_id: str):
    """
    获取用户的LoRA模型状态
    
    参数:
    - user_id: 用户ID
    
    注意：此功能已被移除，只保留教育升学决策链路
    """
    return {
        "code": 404,
        "message": "LoRA决策分析功能已被移除",
        "data": None
    }


@app.post("/api/lora/train/{user_id}")
async def trigger_lora_training(user_id: str, priority: str = "normal"):
    """手动触发LoRA训练 - 直接在后台线程执行"""
    if not user_id or user_id == "default_user":
        return {
            "code": 403,
            "message": "默认用户不允许触发个性化 LoRA 训练，请先登录真实账号",
            "data": None
        }
    try:
        from backend.lora.auto_lora_trainer import get_training_progress
        
        # 检查是否已在训练
        progress = get_training_progress(user_id)
        if progress.get("is_training"):
            return {
                "code": 409,
                "message": "该用户的模型正在训练中，请等待完成",
                "data": progress
            }
        
        # 在后台线程直接执行训练
        import threading
        def run_training():
            try:
                from backend.lora.auto_lora_trainer import AutoLoRATrainer
                trainer = AutoLoRATrainer(user_id)
                trainer.training_config["train_interval_days"] = 0  # 跳过间隔检查
                trainer.auto_train_workflow()
            except Exception as e:
                from backend.lora.auto_lora_trainer import _training_progress
                _training_progress[user_id] = {
                    "is_training": False, "progress": 0, "stage": "训练失败", "error": str(e)
                }
                print(f"后台训练失败: {e}")
        
        thread = threading.Thread(target=run_training, daemon=True)
        thread.start()
        
        return {
            "code": 200,
            "message": "训练已启动",
            "data": {"user_id": user_id}
        }
    except Exception as e:
        print(f"触发训练失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.get("/api/lora/scheduler/status")
async def get_scheduler_status():
    """获取调度器状态"""
    try:
        scheduler = get_lora_scheduler()
        status = scheduler.get_status()
        
        return {
            "code": 200,
            "message": "Success",
            "data": status
        }
    except Exception as e:
        print(f"获取调度器状态失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.post("/api/lora/scheduler/start")
async def start_scheduler():
    """启动调度器"""
    try:
        scheduler = get_lora_scheduler()
        scheduler.start()
        
        return {
            "code": 200,
            "message": "调度器已启动",
            "data": None
        }
    except Exception as e:
        print(f"启动调度器失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.post("/api/lora/scheduler/stop")
async def stop_scheduler():
    """停止调度器"""
    try:
        scheduler = get_lora_scheduler()
        scheduler.stop()
        
        return {
            "code": 200,
            "message": "调度器已停止",
            "data": None
        }
    except Exception as e:
        print(f"停止调度器失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

# ==================== 系统管理API ====================

@app.get("/api/system/health")
async def system_health_check():
    """系统健康检查"""
    try:
        from backend.utils.health_checker import HealthChecker
        
        checker = HealthChecker()
        results = checker.check_all()
        
        return {
            "code": 200,
            "message": "Health check completed",
            "data": results
        }
    except Exception as e:
        print(f"健康检查失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.get("/api/system/performance")
async def get_performance_stats():
    """获取性能统计"""
    try:
        from backend.utils.performance_monitor import get_monitor
        
        monitor = get_monitor()
        stats = monitor.get_statistics()
        
        return {
            "code": 200,
            "message": "Success",
            "data": stats
        }
    except Exception as e:
        print(f"获取性能统计失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.post("/api/system/backup")
async def create_system_backup():
    """创建系统备份"""
    try:
        from backend.utils.backup_manager import BackupManager
        
        manager = BackupManager()
        backup_path = manager.auto_backup()
        
        return {
            "code": 200,
            "message": "备份创建成功",
            "data": {"backup_path": backup_path}
        }
    except Exception as e:
        print(f"创建备份失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.get("/api/system/backups")
async def list_system_backups():
    """列出所有备份"""
    try:
        from backend.utils.backup_manager import BackupManager
        
        manager = BackupManager()
        backups = manager.list_backups()
        
        return {
            "code": 200,
            "message": "Success",
            "data": {"backups": backups}
        }
    except Exception as e:
        print(f"列出备份失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

# ==================== 根路径====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "LifeSwarm API",
        "version": "1.0.0",
        "description": "智能生活助手系统",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    # 启动服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=6006,
        reload=True
    )




@app.post("/api/lora/train/{user_id}")
async def trigger_lora_training(user_id: str):
    """触发指定用户的 LoRA 训练"""
    try:
        from backend.lora.auto_lora_trainer import AutoLoRATrainer

        if user_id in lora_training_tasks and lora_training_tasks[user_id].get("status") == "running":
            return {
                "code": 200,
                "message": "训练任务已在进行中",
                "data": lora_training_tasks[user_id]
            }

        lora_training_tasks[user_id] = {
            "user_id": user_id,
            "status": "running",
            "started_at": datetime.now().isoformat()
        }

        def _run_training():
            try:
                trainer = AutoLoRATrainer(user_id=user_id)
                trainer.auto_train_workflow()
                lora_training_tasks[user_id] = {
                    "user_id": user_id,
                    "status": "completed",
                    "finished_at": datetime.now().isoformat()
                }
            except Exception as e:
                lora_training_tasks[user_id] = {
                    "user_id": user_id,
                    "status": "failed",
                    "error": str(e),
                    "finished_at": datetime.now().isoformat()
                }

        threading.Thread(target=_run_training, daemon=True).start()

        return {
            "code": 200,
            "message": "LoRA训练已触发",
            "data": lora_training_tasks[user_id]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/lora/train/status/{user_id}")
async def get_lora_training_status(user_id: str):
    return {
        "code": 200,
        "message": "success",
        "data": lora_training_tasks.get(user_id, {"user_id": user_id, "status": "idle"})
    }


# ==================== 模型压缩管理 API ====================

@app.get("/api/compression/status")
async def get_compression_status():
    """获取模型压缩模块状态"""
    try:
        from backend.model_compression.quantizer import ModelQuantizer
        quantizer = ModelQuantizer()
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "backends": {
                    "bitsandbytes": quantizer.bitsandbytes_available,
                    "llmquant": quantizer.llmquant_available,
                    "obr": quantizer.obr_available,
                },
                "residual_analyzer": _residual_analyzer_status(),
            }
        }
    except Exception as e:
        return {"code": 500, "message": str(e), "data": None}


@app.post("/api/compression/compress-base-model")
async def api_compress_base_model(request_data: Dict[str, Any]):
    """
    触发基座模型 OBR 压缩（后台执行）
    
    Body:
        model: 模型路径
        output: 输出目录
        w_bits: 权重量化位数 (默认 4)
        sparsity: 稀疏度 (默认 0.5)
    """
    try:
        model = request_data.get("model")
        if not model:
            return {"code": 400, "message": "缺少 model 参数", "data": None}
        
        output = request_data.get("output", "models/qwen-obr")
        w_bits = request_data.get("w_bits", 4)
        a_bits = request_data.get("a_bits", 16)
        k_bits = request_data.get("k_bits", 4)
        v_bits = request_data.get("v_bits", 4)
        sparsity = request_data.get("sparsity", 0.5)
        nsamples = request_data.get("nsamples", 128)
        
        # 后台执行压缩
        import threading
        
        compression_tasks = getattr(app.state, '_compression_tasks', {})
        task_id = f"obr_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        compression_tasks[task_id] = {"status": "running", "started_at": datetime.now().isoformat()}
        app.state._compression_tasks = compression_tasks
        
        def _run_compression():
            try:
                from backend.model_compression.obr_wrapper import OBRCompressor
                compressor = OBRCompressor(
                    model_name=model, output_dir=output,
                    w_bits=w_bits, a_bits=a_bits, k_bits=k_bits, v_bits=v_bits,
                    sparsity_ratio=sparsity, nsamples=nsamples,
                )
                result = compressor.compress()
                compression_tasks[task_id] = {
                    "status": result["status"],
                    "result": result,
                    "finished_at": datetime.now().isoformat()
                }
            except Exception as e:
                compression_tasks[task_id] = {
                    "status": "failed", "error": str(e),
                    "finished_at": datetime.now().isoformat()
                }
        
        threading.Thread(target=_run_compression, daemon=True).start()
        
        return {
            "code": 200,
            "message": "基座模型压缩已启动",
            "data": {"task_id": task_id, "status": "running"}
        }
    except Exception as e:
        return {"code": 500, "message": str(e), "data": None}


@app.get("/api/compression/task/{task_id}")
async def get_compression_task_status(task_id: str):
    """查询压缩任务状态"""
    compression_tasks = getattr(app.state, '_compression_tasks', {})
    task = compression_tasks.get(task_id)
    if not task:
        return {"code": 404, "message": "任务不存在", "data": None}
    return {"code": 200, "message": "success", "data": task}


@app.post("/api/compression/quality-report")
async def api_generate_quality_report(request_data: Dict[str, Any]):
    """
    生成压缩质量报告
    
    Body:
        model_name: 模型名称
        baseline: {ppl, latency_ms, vram_gb, tokens_per_sec}
        compressed: {ppl, latency_ms, vram_gb, tokens_per_sec, quantization_method}
    """
    try:
        from backend.model_compression.quality_monitor import CompressionQualityMonitor
        
        model_name = request_data.get("model_name", "unknown")
        monitor = CompressionQualityMonitor(model_name)
        
        baseline = request_data.get("baseline", {})
        compressed = request_data.get("compressed", {})
        
        if baseline:
            monitor.record_baseline(**baseline)
        if compressed:
            monitor.record_compressed(**compressed)
        
        report = monitor.generate_report()
        
        return {"code": 200, "message": "success", "data": report}
    except Exception as e:
        return {"code": 500, "message": str(e), "data": None}


def _residual_analyzer_status() -> Dict[str, Any]:
    """获取残差分析器状态"""
    try:
        from backend.model_compression.quality_monitor import _residual_analyzer
        return {"available": _residual_analyzer.get("available", False)}
    except Exception:
        return {"available": False}

from backend.parallel_life.parallel_life_api import router as parallel_life_router
app.include_router(parallel_life_router)
print('? 平行人生 - 塔罗牌决策游戏 API 已加载')
print('   - POST /api/v5/parallel-life/draw-card')
print('   - POST /api/v5/parallel-life/submit-choice')
print('   - GET /api/v5/parallel-life/decision-profile/{user_id}')
print('   - GET /api/v5/parallel-life/game-stats/{user_id}')

# 知识图谱感知RAG API
from backend.learning.kg_rag_api import router as kg_rag_router
app.include_router(kg_rag_router)
print('知识图谱感知RAG API 已加载')

# Agent 状态查询接口
@app.get("/api/agent/status/{user_id}")
async def get_agent_status(user_id: str):
    """获取用户的个性化决策 Agent 状态（四层架构快照）"""
    try:
        from backend.agent.personal_agent import get_personal_agent
        agent = get_personal_agent(user_id)
        state = agent.refresh_state()
        return {"code": 200, "data": state.to_dict()}
    except Exception as e:
        return {"code": 500, "message": str(e)}



# ==================== 智能日程推荐API ====================

# 注册日程推荐路由
from backend.schedule.schedule_api import router as schedule_router
app.include_router(schedule_router)

# 注册AI核心路由
from backend.ai_core.ai_core_api import router as ai_core_router
app.include_router(ai_core_router)

print("? 智能日程推荐API已注册")
print("? AI核心API已注册")

# 注册管理员路由
from backend.admin.admin_api import router as admin_router
app.include_router(admin_router)
print("✅ 管理员API已注册")
print("   - GET /api/admin/check-permission")
print("   - GET /api/admin/users")
print("   - GET /api/admin/users/{user_id}")
print("   - PUT /api/admin/users/{user_id}/status")
print("   - DELETE /api/admin/users/{user_id}")

# 注册 LLM 切换路由
from backend.llm.llm_switch_api import router as llm_switch_router
app.include_router(llm_switch_router)
print("✅ LLM切换API已注册")
print("   - GET /api/llm/status")
print("   - POST /api/llm/switch")
print("   - POST /api/llm/test")
print("   - GET /api/admin/stats")
print("   - GET /api/admin/activities")


# ==================== 决策历史 API ====================

from backend.decision.decision_history import DecisionHistoryManager
from backend.decision.report_generator import DecisionReportGenerator
import uuid

# 初始化决策历史管理器
decision_history_manager = None

def get_decision_history_manager():
    """获取决策历史管理器"""
    global decision_history_manager
    if decision_history_manager is None:
        try:
            db_config = {
                'host': os.getenv('MYSQL_HOST', 'localhost'),
                'port': int(os.getenv('MYSQL_PORT', 3306)),
                'user': os.getenv('MYSQL_USER', 'root'),
                'password': os.getenv('MYSQL_PASSWORD', ''),
                'database': os.getenv('MYSQL_DATABASE', 'lifeswarm')
            }
            decision_history_manager = DecisionHistoryManager(db_config)
        except Exception as e:
            logging.error(f"初始化决策历史管理器失败: {e}")
            # 返回一个禁用的管理器
            decision_history_manager = type('DisabledManager', (), {'enabled': False})()
    return decision_history_manager


@app.post("/api/decision/history/save")
async def save_decision_history(request_data: Dict[str, Any]):
    """
    保存决策历史
    
    Request:
    {
        "user_id": "xxx",
        "session_id": "xxx",
        "question": "xxx",
        "decision_type": "xxx",
        "options_data": {...}
    }
    """
    try:
        manager = get_decision_history_manager()
        if not getattr(manager, 'enabled', False):
            raise HTTPException(
                status_code=503, 
                detail="决策历史功能暂时不可用，请安装 mysql-connector-python"
            )
        
        user_id = request_data.get('user_id')
        session_id = request_data.get('session_id')
        question = request_data.get('question')
        decision_type = request_data.get('decision_type', 'general')
        options_data = request_data.get('options_data', {})
        
        if not all([user_id, session_id, question]):
            raise HTTPException(status_code=400, detail="缺少必要参数")
        
        # 生成历史记录 ID
        history_id = str(uuid.uuid4())
        
        # 保存到数据库
        success = manager.save_history(
            history_id=history_id,
            user_id=user_id,
            session_id=session_id,
            question=question,
            decision_type=decision_type,
            options_data=options_data
        )
        
        if success:
            return {
                "success": True,
                "history_id": history_id,
                "message": "决策历史已保存"
            }
        else:
            raise HTTPException(status_code=500, detail="保存失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"保存决策历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/decision/history/list")
async def get_decision_history_list(
    user_id: str,
    limit: int = 20,
    offset: int = 0
):
    """
    获取用户的决策历史列表
    
    Query Parameters:
    - user_id: 用户ID
    - limit: 返回数量限制（默认20）
    - offset: 偏移量（默认0）
    """
    try:
        manager = get_decision_history_manager()
        result = manager.get_history_list(user_id, limit, offset)
        return result
        
    except Exception as e:
        logging.error(f"获取决策历史列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/decision/history/detail/{history_id}")
async def get_decision_history_detail(history_id: str):
    """
    获取决策历史详情
    
    Path Parameters:
    - history_id: 历史记录ID
    """
    try:
        manager = get_decision_history_manager()
        history = manager.get_history_detail(history_id)
        
        if history:
            return {
                "success": True,
                "history": history
            }
        else:
            raise HTTPException(status_code=404, detail="历史记录不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"获取决策历史详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/decision/history/delete/{history_id}")
async def delete_decision_history(history_id: str, user_id: str):
    """
    删除决策历史
    
    Path Parameters:
    - history_id: 历史记录ID
    
    Query Parameters:
    - user_id: 用户ID（用于权限验证）
    """
    try:
        manager = get_decision_history_manager()
        success = manager.delete_history(history_id, user_id)
        
        if success:
            return {
                "success": True,
                "message": "历史记录已删除"
            }
        else:
            raise HTTPException(status_code=404, detail="历史记录不存在或无权限")
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"删除决策历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/decision/generate-report")
async def generate_decision_report(request_data: Dict[str, Any]):
    """
    生成决策选项报告
    
    Request:
    {
        "question": "xxx",
        "option_title": "xxx",
        "option_description": "xxx",
        "agents_data": [...],
        "total_score": 85.5
    }
    """
    try:
        question = request_data.get('question', '')
        option_title = request_data.get('option_title', '')
        option_description = request_data.get('option_description', '')
        agents_data = request_data.get('agents_data', [])
        total_score = request_data.get('total_score', 0)
        
        # 获取 LLM 服务
        llm_service = get_or_init_llm_service()
        
        # 创建报告生成器
        generator = DecisionReportGenerator(llm_service)
        
        # 生成报告
        result = await generator.generate_option_report(
            question=question,
            option_title=option_title,
            option_description=option_description,
            agents_data=agents_data,
            total_score=total_score
        )
        
        return result
        
    except Exception as e:
        logging.error(f"生成决策报告失败: {e}")
        # 返回基础报告
        return {
            "success": False,
            "report": {
                "summary": f"该选项获得综合评分 {request_data.get('total_score', 0):.1f} 分",
                "key_insights": ["报告生成失败，请查看详细数据"],
                "strengths": [],
                "risks": [],
                "recommendation": "建议查看各 Agent 的详细分析",
                "agents_summary": request_data.get('agents_data', []),
                "total_score": request_data.get('total_score', 0)
            }
        }


# ==================== Agent对话API ====================

@app.post("/api/agent-chat")
async def agent_chat(request_data: Dict[str, Any]):
    """
    Agent对话接口 - 使用四模块架构
    
    请求体：
    {
        "token": "xxx",
        "agent_type": "relationship" | "education" | "career",
        "message": "用户消息",
        "conversation_id": "xxx" (可选),
        "conversation_title": "xxx" (可选)
    }
    """
    try:
        # 验证token
        from backend.auth.auth_service import get_auth_service
        auth_service = get_auth_service()
        
        token = request_data.get('token')
        if not token:
            return {'success': False, 'message': '缺少token'}
        
        # 验证token并获取用户ID
        user_id = auth_service.verify_token(token)
        if not user_id:
            return {'success': False, 'message': 'Token无效或已过期'}
        
        # 获取请求参数
        agent_type = request_data.get('agent_type')
        user_message = request_data.get('message')
        
        if not agent_type or not user_message:
            return {'success': False, 'message': '缺少必要参数'}
        
        # 使用LangChain ReAct Agent系统（支持MCP）
        from backend.agents.langchain_specialized_agents import create_langchain_agent
        from backend.learning.rag_manager import RAGManager
        from backend.learning.unified_hybrid_retrieval import UnifiedHybridRetrieval
        
        print(f"\n[Agent对话] 用户: {user_id}, Agent类型: {agent_type}")
        print(f"[Agent对话] 使用LangChain ReAct框架 + Workflow混合模式")
        
        # 获取系统实例
        llm_service = get_or_init_llm_service()
        if not llm_service or not llm_service.enabled:
            return {'success': False, 'message': 'LLM服务不可用'}
        
        rag_system = RAGManager.get_system(user_id)
        retrieval_system = UnifiedHybridRetrieval(user_id)
        
        # 创建MCP Host并注册工具
        from backend.agents.mcp_integration import MCPHost
        from backend.agents.specialized_mcp_servers import (
            WebSearchMCPServer,
            RelationshipMCPServer,
            EducationMCPServer
        )
        
        mcp_host = MCPHost(user_id=user_id)
        
        # 注册联网搜索（所有Agent共享）- 显式传递环境变量
        import os
        search_api_key = os.getenv("QWEN_SEARCH_API_KEY")
        search_host = os.getenv("QWEN_SEARCH_HOST")
        print(f"[DEBUG] 搜索API配置: api_key={'已设置' if search_api_key else '未设置'}, host={'已设置' if search_host else '未设置'}")
        
        mcp_host.register_server(WebSearchMCPServer(
            api_key=search_api_key,
            host=search_host,
            workspace=os.getenv("QWEN_SEARCH_WORKSPACE", "default"),
            service_id=os.getenv("QWEN_SEARCH_SERVICE_ID", "ops-web-search-001")
        ))
        
        # 根据Agent类型注册专属工具
        if agent_type == 'relationship':
            mcp_host.register_server(RelationshipMCPServer())
        elif agent_type == 'education':
            mcp_host.register_server(EducationMCPServer())
        
        # 创建LangChain Agent
        agent = create_langchain_agent(
            agent_type=agent_type,
            user_id=user_id,
            llm_service=llm_service,
            rag_system=rag_system,
            retrieval_system=retrieval_system,
            use_workflow=True,  # 启用Workflow混合模式
            mcp_host=mcp_host  # 启用MCP工具
        )
        
        # 异步初始化Agent（发现MCP工具）
        await agent.initialize()
        
        # 处理消息（LangChain ReAct模式）
        result = agent.process(user_message)
        
        # 保存对话历史到数据库
        conversation_id = request_data.get('conversation_id')
        if not conversation_id:
            import uuid
            conversation_id = str(uuid.uuid4())
        
        conversation_title = request_data.get('conversation_title')
        if not conversation_title:
            conversation_title = user_message[:50] + ('...' if len(user_message) > 50 else '')
        
        try:
            from backend.database.db_manager import DatabaseManager
            from backend.database.models import ConversationHistory
            
            db_manager = DatabaseManager()
            session = db_manager.get_session()
            
            try:
                # 保存用户消息
                user_record = ConversationHistory(
                    user_id=user_id,
                    agent_type=agent_type,
                    conversation_id=conversation_id,
                    conversation_title=conversation_title,
                    role='user',
                    content=user_message,
                    context={'retrieval_stats': result['retrieval_stats']},
                    timestamp=datetime.now()
                )
                session.add(user_record)
                
                # 保存助手回复
                assistant_record = ConversationHistory(
                    user_id=user_id,
                    agent_type=agent_type,
                    conversation_id=conversation_id,
                    conversation_title=conversation_title,
                    role='assistant',
                    content=result['response'],
                    retrieval_stats=result['retrieval_stats'],
                    timestamp=datetime.now()
                )
                session.add(assistant_record)
                
                session.commit()
                print(f"✅ [Agent对话] 对话历史已保存: conversation_id={conversation_id}")
                
            finally:
                session.close()
                
        except Exception as e:
            print(f"⚠️ [Agent对话] 保存对话历史失败: {e}")
            # 不影响主流程
        
        return {
            'success': True,
            'response': result['response'],
            'retrieval_stats': result['retrieval_stats'],
            'conversation_id': conversation_id,
            'mode': result.get('mode', 'unknown'),  # workflow_only / workflow_agent_hybrid / pure_agent
            'agent_used': result.get('agent_used', False),  # 是否使用了Agent推理
            'execution_path': result.get('execution_path', []),  # Workflow执行路径
            'tasks_executed': len(result.get('tasks_executed', [])),
            'tools_used': result.get('tools_used', []),
            'tool_calls': result.get('tool_calls', [])  # MCP工具调用信息
        }
        
    except Exception as e:
        print(f"❌ Agent对话失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'message': f'对话失败: {str(e)}'
        }


# ==================== Agent对话历史API ====================

@app.get("/api/agent-conversations")
async def get_agent_conversations(
    token: str,
    agent_type: str = None
):
    """
    获取Agent对话历史列表
    
    参数：
    - token: 用户token
    - agent_type: Agent类型（可选，不传则返回所有Agent的对话）
    """
    try:
        from backend.auth.auth_service import get_auth_service
        from backend.database.db_manager import DatabaseManager
        from backend.database.models import ConversationHistory
        from sqlalchemy import func, desc
        
        auth_service = get_auth_service()
        
        # 验证token
        user_id = auth_service.verify_token(token)
        if not user_id:
            return {'success': False, 'message': 'Token无效或已过期'}
        
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        try:
            # 查询对话列表（按conversation_id分组）
            query = session.query(
                ConversationHistory.conversation_id,
                ConversationHistory.agent_type,
                ConversationHistory.conversation_title,
                func.min(ConversationHistory.timestamp).label('created_at'),
                func.max(ConversationHistory.timestamp).label('updated_at'),
                func.count(ConversationHistory.id).label('message_count')
            ).filter(
                ConversationHistory.user_id == user_id,
                ConversationHistory.conversation_id.isnot(None)
            )
            
            # 如果指定了agent_type，添加过滤
            if agent_type:
                query = query.filter(ConversationHistory.agent_type == agent_type)
            
            # 分组并排序
            conversations = query.group_by(
                ConversationHistory.conversation_id,
                ConversationHistory.agent_type,
                ConversationHistory.conversation_title
            ).order_by(desc('updated_at')).all()
            
            # 格式化结果
            result = []
            for conv in conversations:
                result.append({
                    'conversation_id': conv.conversation_id,
                    'agent_type': conv.agent_type,
                    'title': conv.conversation_title,
                    'created_at': conv.created_at.isoformat() if conv.created_at else None,
                    'updated_at': conv.updated_at.isoformat() if conv.updated_at else None,
                    'message_count': conv.message_count
                })
            
            return {
                'success': True,
                'conversations': result,
                'total': len(result)
            }
            
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ 获取对话历史列表失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'message': f'获取失败: {str(e)}'
        }


@app.get("/api/agent-conversation/{conversation_id}")
async def get_agent_conversation_detail(
    conversation_id: str,
    token: str
):
    """
    获取单个对话的详细消息
    
    参数：
    - conversation_id: 对话ID
    - token: 用户token
    """
    try:
        from backend.auth.auth_service import get_auth_service
        from backend.database.db_manager import DatabaseManager
        from backend.database.models import ConversationHistory
        
        auth_service = get_auth_service()
        
        # 验证token
        user_id = auth_service.verify_token(token)
        if not user_id:
            return {'success': False, 'message': 'Token无效或已过期'}
        
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        try:
            # 查询对话消息
            messages = session.query(ConversationHistory).filter(
                ConversationHistory.user_id == user_id,
                ConversationHistory.conversation_id == conversation_id
            ).order_by(ConversationHistory.timestamp).all()
            
            if not messages:
                return {
                    'success': False,
                    'message': '对话不存在'
                }
            
            # 格式化消息
            result = []
            for msg in messages:
                result.append({
                    'id': msg.id,
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat() if msg.timestamp else None,
                    'retrieval_stats': msg.retrieval_stats,
                    'thinking': msg.thinking
                })
            
            return {
                'success': True,
                'conversation_id': conversation_id,
                'agent_type': messages[0].agent_type,
                'title': messages[0].conversation_title,
                'messages': result
            }
            
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ 获取对话详情失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'message': f'获取失败: {str(e)}'
        }


@app.delete("/api/agent-conversation/{conversation_id}")
async def delete_agent_conversation(
    conversation_id: str,
    request_data: Dict[str, Any]
):
    """
    删除对话历史
    
    请求体：
    {
        "token": "xxx"
    }
    """
    try:
        from backend.auth.auth_service import get_auth_service
        from backend.database.db_manager import DatabaseManager
        from backend.database.models import ConversationHistory
        
        auth_service = get_auth_service()
        
        token = request_data.get('token')
        if not token:
            return {'success': False, 'message': '缺少token'}
        
        # 验证token
        user_id = auth_service.verify_token(token)
        if not user_id:
            return {'success': False, 'message': 'Token无效或已过期'}
        
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        try:
            # 删除对话
            deleted_count = session.query(ConversationHistory).filter(
                ConversationHistory.user_id == user_id,
                ConversationHistory.conversation_id == conversation_id
            ).delete()
            
            session.commit()
            
            return {
                'success': True,
                'message': f'已删除 {deleted_count} 条消息'
            }
            
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ 删除对话失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'message': f'删除失败: {str(e)}'
        }


# ==================== Agent资料导入API ====================

@app.post("/api/agent-import")
async def agent_import_text(request_data: Dict[str, Any]):
    """
    Agent文本资料导入
    
    请求体：
    {
        "token": "xxx",
        "agent_type": "relationship" | "education" | "career",
        "import_type": "text",
        "content": "要导入的文本内容"
    }
    """
    try:
        # 验证token
        from backend.auth.auth_service import get_auth_service
        auth_service = get_auth_service()
        
        token = request_data.get('token')
        if not token:
            return {'success': False, 'message': '缺少token'}
        
        # 验证token并获取用户ID
        user_id = auth_service.verify_token(token)
        if not user_id:
            return {'success': False, 'message': 'Token无效或已过期'}
        
        print(f"✅ [Agent导入] Token验证成功，用户ID: {user_id}")
        
        # 获取参数
        agent_type = request_data.get('agent_type')
        content = request_data.get('content', '').strip()
        
        if not agent_type or not content:
            return {'success': False, 'message': '缺少必要参数'}
        
        if agent_type not in ['relationship', 'education', 'career']:
            return {'success': False, 'message': '无效的Agent类型'}
        
        # 获取RAG系统
        from backend.learning.rag_manager import RAGManager
        from backend.learning.production_rag_system import MemoryType
        
        rag_system = RAGManager.get_system(user_id)
        
        # 根据Agent类型确定记忆类型和领域
        memory_type_map = {
            'relationship': MemoryType.KNOWLEDGE,
            'education': MemoryType.KNOWLEDGE,
            'career': MemoryType.KNOWLEDGE
        }
        
        domain_map = {
            'relationship': 'relationship',
            'education': 'education',
            'career': 'career'
        }
        
        memory_type = memory_type_map[agent_type]
        domain = domain_map[agent_type]
        
        # 分段处理文本（按行分割）
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        if not lines:
            return {'success': False, 'message': '内容为空'}
        
        # 批量导入
        imported_count = 0
        for line in lines:
            try:
                rag_system.add_memory(
                    memory_type=memory_type,
                    content=line,
                    metadata={
                        'source': 'agent_import',
                        'agent_type': agent_type,
                        'domain': domain,
                        'imported_at': datetime.now().isoformat()
                    },
                    importance=0.8  # 用户主动导入的内容重要性较高
                )
                imported_count += 1
            except Exception as e:
                print(f"⚠️ 导入单条记忆失败: {e}")
                continue
        
        print(f"✅ [Agent导入] 用户{user_id}向{agent_type} Agent导入了{imported_count}条记忆")
        
        return {
            'success': True,
            'message': f'成功导入{imported_count}条记忆',
            'count': imported_count
        }
        
    except Exception as e:
        print(f"❌ Agent资料导入失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'message': f'导入失败: {str(e)}'
        }


@app.post("/api/agent-import-file")
async def agent_import_file(
    file: UploadFile = File(...),
    agent_type: str = Form(None),
    token: str = Form(None)
):
    """
    Agent文件资料导入
    
    支持格式：.txt, .md, .pdf, .docx
    """
    try:
        # 验证token
        from backend.auth.auth_service import get_auth_service
        auth_service = get_auth_service()
        
        if not token:
            return {'success': False, 'message': '缺少token'}
        
        # 验证token并获取用户ID
        user_id = auth_service.verify_token(token)
        if not user_id:
            return {'success': False, 'message': 'Token无效或已过期'}
        
        print(f"✅ [Agent文件导入] Token验证成功，用户ID: {user_id}")
        
        # 验证参数
        if not agent_type or agent_type not in ['relationship', 'education', 'career']:
            return {'success': False, 'message': '无效的Agent类型'}
        
        # 检查文件类型
        filename = file.filename.lower()
        if not any(filename.endswith(ext) for ext in ['.txt', '.md', '.pdf', '.docx']):
            return {'success': False, 'message': '不支持的文件格式，仅支持 .txt, .md, .pdf, .docx'}
        
        # 读取文件内容
        content = await file.read()
        
        # 根据文件类型解析内容
        text_content = ""
        
        if filename.endswith('.txt') or filename.endswith('.md'):
            # 文本文件直接解码
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text_content = content.decode('gbk')
                except:
                    return {'success': False, 'message': '文件编码错误，请使用UTF-8或GBK编码'}
        
        elif filename.endswith('.pdf'):
            # PDF文件解析
            try:
                import PyPDF2
                import io
                
                pdf_file = io.BytesIO(content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                text_parts = []
                for page in pdf_reader.pages:
                    text_parts.append(page.extract_text())
                
                text_content = '\n'.join(text_parts)
            except ImportError:
                return {'success': False, 'message': 'PDF解析功能未安装，请联系管理员'}
            except Exception as e:
                return {'success': False, 'message': f'PDF解析失败: {str(e)}'}
        
        elif filename.endswith('.docx'):
            # DOCX文件解析
            try:
                import docx
                import io
                
                docx_file = io.BytesIO(content)
                doc = docx.Document(docx_file)
                
                text_parts = []
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        text_parts.append(paragraph.text)
                
                text_content = '\n'.join(text_parts)
            except ImportError:
                return {'success': False, 'message': 'DOCX解析功能未安装，请联系管理员'}
            except Exception as e:
                return {'success': False, 'message': f'DOCX解析失败: {str(e)}'}
        
        if not text_content.strip():
            return {'success': False, 'message': '文件内容为空'}
        
        # 获取RAG系统
        from backend.learning.rag_manager import RAGManager
        from backend.learning.production_rag_system import MemoryType
        
        rag_system = RAGManager.get_system(user_id)
        
        # 根据Agent类型确定记忆类型和领域
        memory_type_map = {
            'relationship': MemoryType.KNOWLEDGE,
            'education': MemoryType.KNOWLEDGE,
            'career': MemoryType.KNOWLEDGE
        }
        
        domain_map = {
            'relationship': 'relationship',
            'education': 'education',
            'career': 'career'
        }
        
        memory_type = memory_type_map[agent_type]
        domain = domain_map[agent_type]
        
        # 分段处理文本（按行分割，过滤空行）
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        
        if not lines:
            return {'success': False, 'message': '文件内容为空'}
        
        # 批量导入
        imported_count = 0
        for line in lines:
            # 跳过太短的行（少于5个字符）
            if len(line) < 5:
                continue
            
            try:
                rag_system.add_memory(
                    memory_type=memory_type,
                    content=line,
                    metadata={
                        'source': 'file_import',
                        'agent_type': agent_type,
                        'domain': domain,
                        'filename': file.filename,
                        'imported_at': datetime.now().isoformat()
                    },
                    importance=0.8
                )
                imported_count += 1
            except Exception as e:
                print(f"⚠️ 导入单条记忆失败: {e}")
                continue
        
        print(f"✅ [Agent文件导入] 用户{user_id}从文件{file.filename}向{agent_type} Agent导入了{imported_count}条记忆")
        
        return {
            'success': True,
            'message': f'成功从文件导入{imported_count}条记忆',
            'count': imported_count,
            'filename': file.filename
        }
        
    except Exception as e:
        print(f"❌ Agent文件导入失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'message': f'导入失败: {str(e)}'
        }
