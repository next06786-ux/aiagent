"""
涌现检测与智能洞察模块

数据流程：
1. 用户发消息时 → realtime_analyzer 实时分析并存储洞察数据到数据库
2. 用户打开智能洞察页面时 → smart_insight_engine 读取数据进行涌现发现分析

提供：
- 实时对话分析（文本、图像、语音）
- 涌现现象检测（模式、非线性、协同、反馈循环、阈值、分岔）
- 智能洞察生成（级联效应、协同增益、临界点预警、反馈环路）
"""

from .emergence_detector import (
    EmergenceDetector,
    EmergenceEvent,
    EmergenceType,
    get_emergence_detector
)

from .conversation_analyzer import (
    ConversationAnalyzer,
    ConversationInsight,
    DataType
)

from .smart_insight_engine import (
    SmartInsightEngine,
    SmartInsight,
    InsightLevel,
    InsightCategory,
    get_smart_insight_engine
)

from .realtime_analyzer import (
    RealtimeInsightStorage,
    get_realtime_analyzer,
    analyze_message_realtime
)

__all__ = [
    # 涌现检测
    "EmergenceDetector",
    "EmergenceEvent", 
    "EmergenceType",
    "get_emergence_detector",
    
    # 对话分析
    "ConversationAnalyzer",
    "ConversationInsight",
    "DataType",
    
    # 智能洞察
    "SmartInsightEngine",
    "SmartInsight",
    "InsightLevel",
    "InsightCategory",
    "get_smart_insight_engine",
    
    # 实时分析
    "RealtimeInsightStorage",
    "get_realtime_analyzer",
    "analyze_message_realtime",
]
