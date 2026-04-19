"""
决策逻辑分析器
分析用户在塔罗牌游戏中的选择，提取决策模式
"""
from typing import Dict, Any, List
from datetime import datetime
from collections import defaultdict
import json


class DecisionLogicAnalyzer:
    """决策逻辑分析器"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        
        # 获取RAG系统和数据库
        from backend.startup_manager import StartupManager
        from backend.database.db_manager import db_manager
        
        # 尝试多种方式获取RAG系统
        self.rag_system = StartupManager.get_user_system(user_id, 'rag')
        if not self.rag_system:
            self.rag_system = StartupManager.get_user_system('default_user', 'rag')
        
        # 如果还是没有，尝试直接创建
        if not self.rag_system:
            try:
                from backend.learning.rag_manager import RAGManager
                self.rag_system = RAGManager.get_system(user_id, use_gpu=False)
                print(f"[决策逻辑] 为用户 {user_id} 创建新的RAG系统")
            except Exception as e:
                print(f"[决策逻辑] 创建RAG系统失败: {e}")
                self.rag_system = None
        
        self.db_manager = db_manager
    
    def record_choice(
        self,
        card: str,
        dimension: str,
        scenario: str,
        choice: str,
        tendency_value: float
    ):
        """
        记录用户的选择
        
        Args:
            card: 塔罗牌名称
            dimension: 决策维度
            scenario: 情景描述
            choice: 用户选择
            tendency_value: 倾向值（-1到1）
        """
        # 1. 存储到RAG系统
        self._store_to_rag(card, dimension, scenario, choice, tendency_value)
        
        # 2. 存储到数据库
        self._store_to_database(card, dimension, scenario, choice, tendency_value)
        
        print(f"[决策逻辑] 用户 {self.user_id} 的选择已记录: {dimension} = {tendency_value}")
    
    def _store_to_rag(
        self,
        card: str,
        dimension: str,
        scenario: str,
        choice: str,
        tendency_value: float
    ):
        """存储到RAG系统"""
        try:
            from backend.learning.production_rag_system import MemoryType
            
            if not self.rag_system:
                print("[决策逻辑] RAG系统未初始化")
                return
            
            # 生成倾向标签
            if tendency_value < -0.5:
                tendency_label = "强烈倾向左侧"
            elif tendency_value < -0.2:
                tendency_label = "倾向左侧"
            elif tendency_value < 0.2:
                tendency_label = "平衡"
            elif tendency_value < 0.5:
                tendency_label = "倾向右侧"
            else:
                tendency_label = "强烈倾向右侧"
            
            content = f"""在'{card}'塔罗牌场景中，用户在{dimension}维度上{tendency_label}（倾向值：{tendency_value}）

场景描述：{scenario}

用户选择：{choice}

这反映了用户在该决策维度上的价值观和偏好。"""
            
            self.rag_system.add_memory(
                memory_type=MemoryType.DECISION_LOGIC,  # 使用新的类型
                content=content,
                metadata={
                    'source': 'tarot_game',
                    'card': card,
                    'dimension': dimension,
                    'choice': choice,
                    'scenario': scenario[:200],  # 截断场景描述
                    'tendency_value': tendency_value,
                    'tendency_label': tendency_label,
                    'timestamp': datetime.now().isoformat()
                },
                importance=0.95  # 决策逻辑画像非常重要
            )
            
            print(f"[决策逻辑] 已存入RAG (DECISION_LOGIC类型)")
            
        except Exception as e:
            print(f"[决策逻辑] 存入RAG失败: {e}")
    
    def _store_to_database(
        self,
        card: str,
        dimension: str,
        scenario: str,
        choice: str,
        tendency_value: float
    ):
        """存储到数据库"""
        try:
            # TODO: 创建决策逻辑表
            # 暂时跳过数据库存储
            pass
        except Exception as e:
            print(f"[决策逻辑] 存入数据库失败: {e}")
    
    def get_decision_profile(self) -> Dict[str, Any]:
        """
        获取用户的决策画像
        
        Returns:
            {
                'dimensions': {维度: 倾向值},
                'patterns': 决策模式描述,
                'confidence': 置信度
            }
        """
        try:
            from backend.learning.production_rag_system import MemoryType
            
            if not self.rag_system:
                return self._get_default_profile()
            
            # 从RAG检索所有决策逻辑记录
            results = self.rag_system.search(
                query="用户决策逻辑和价值观",
                memory_types=[MemoryType.DECISION_LOGIC],  # 使用新类型
                top_k=100
            )
            
            # 按维度聚合
            dimension_values = defaultdict(list)
            
            for result in results:
                metadata = result.metadata if hasattr(result, 'metadata') else result.get('metadata', {})
                
                if metadata.get('source') == 'tarot_game':
                    dimension = metadata.get('dimension')
                    tendency = metadata.get('tendency_value')
                    
                    if dimension and tendency is not None:
                        dimension_values[dimension].append(tendency)
            
            # 计算每个维度的平均倾向
            profile = {}
            for dimension, values in dimension_values.items():
                if values:
                    avg_tendency = sum(values) / len(values)
                    profile[dimension] = {
                        'value': round(avg_tendency, 2),
                        'count': len(values),
                        'confidence': min(len(values) / 5.0, 1.0)  # 5次选择达到满置信度
                    }
            
            # 生成决策模式描述
            patterns = self._generate_pattern_description(profile)
            
            # 计算整体置信度
            total_choices = sum(len(values) for values in dimension_values.values())
            overall_confidence = min(total_choices / 20.0, 1.0)  # 20次选择达到满置信度
            
            return {
                'dimensions': profile,
                'patterns': patterns,
                'confidence': round(overall_confidence, 2),
                'total_choices': total_choices
            }
            
        except Exception as e:
            print(f"[决策逻辑] 获取决策画像失败: {e}")
            return self._get_default_profile()
    
    def _generate_pattern_description(self, profile: Dict[str, Any]) -> List[str]:
        """生成决策模式描述"""
        patterns = []
        
        for dimension, data in profile.items():
            value = data['value']
            confidence = data['confidence']
            
            if confidence < 0.4:
                continue  # 置信度太低，跳过
            
            # 根据倾向值生成描述
            if value < -0.5:
                patterns.append(f"{dimension}: 明显倾向于左侧选择")
            elif value > 0.5:
                patterns.append(f"{dimension}: 明显倾向于右侧选择")
            elif -0.3 < value < 0.3:
                patterns.append(f"{dimension}: 倾向平衡")
        
        return patterns
    
    def _get_default_profile(self) -> Dict[str, Any]:
        """默认决策画像（无数据时）"""
        return {
            'dimensions': {},
            'patterns': [],
            'confidence': 0.0,
            'total_choices': 0
        }
    
    def apply_to_decision_engine(self, decision_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        将决策逻辑应用到决策推演引擎
        
        Args:
            decision_context: 决策上下文
        
        Returns:
            增强后的决策上下文
        """
        profile = self.get_decision_profile()
        
        if profile['confidence'] < 0.3:
            print("[决策逻辑] 置信度不足，不应用决策画像")
            return decision_context
        
        # 将决策画像添加到上下文
        decision_context['user_decision_profile'] = profile
        decision_context['decision_logic_available'] = True
        
        print(f"[决策逻辑] 决策画像已应用，置信度: {profile['confidence']}")
        
        return decision_context
