"""
增强多模态融合系统
整合图像、传感器、文本数据，提供统一的多模态表示
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
from collections import defaultdict

# 导入各个处理器
from backend.vision.image_processor import ImageProcessor
from backend.multimodal.text_processor import get_text_processor
from backend.multimodal.sensor_processor import get_sensor_processor


@dataclass
class ModalityData:
    """单一模态数据"""
    modality_type: str  # text, image, sensor, audio
    raw_data: Any
    embedding: Optional[np.ndarray] = None
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FusedRepresentation:
    """融合后的多模态表示"""
    unified_embedding: np.ndarray
    modality_weights: Dict[str, float]
    confidence: float
    contributing_modalities: List[str]
    semantic_features: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class TextEncoder:
    """文本编码器"""
    
    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim
        self.vocab = {}
        self.vocab_size = 0
    
    def encode(self, text: str) -> np.ndarray:
        """编码文本为向量"""
        # 简化实现：使用词袋模型
        words = text.lower().split()
        
        # 构建词汇表
        for word in words:
            if word not in self.vocab:
                self.vocab[word] = self.vocab_size
                self.vocab_size += 1
        
        # 创建词频向量
        word_counts = defaultdict(int)
        for word in words:
            word_counts[self.vocab[word]] += 1
        
        # 转换为固定维度
        embedding = np.zeros(self.embedding_dim)
        for idx, count in word_counts.items():
            if idx < self.embedding_dim:
                embedding[idx] = count
        
        # 归一化
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding
    
    def extract_features(self, text: str) -> Dict[str, Any]:
        """提取文本特征"""
        words = text.lower().split()
        
        # 情感词典（简化版）
        positive_words = {'好', '棒', '开心', '满意', '喜欢', 'good', 'great', 'happy'}
        negative_words = {'差', '糟', '难过', '不满', '讨厌', 'bad', 'terrible', 'sad'}
        
        sentiment_score = 0
        for word in words:
            if word in positive_words:
                sentiment_score += 1
            elif word in negative_words:
                sentiment_score -= 1
        
        return {
            'word_count': len(words),
            'unique_words': len(set(words)),
            'sentiment_score': sentiment_score,
            'avg_word_length': np.mean([len(w) for w in words]) if words else 0
        }


class ImageEncoder:
    """图像编码器"""
    
    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim
    
    def encode(self, image_data: Any) -> np.ndarray:
        """编码图像为向量"""
        # 简化实现：如果是numpy数组，直接处理
        if isinstance(image_data, np.ndarray):
            # 展平并调整维度
            flat = image_data.flatten()
            if len(flat) > self.embedding_dim:
                # 降采样
                indices = np.linspace(0, len(flat)-1, self.embedding_dim, dtype=int)
                embedding = flat[indices]
            else:
                # 填充
                embedding = np.zeros(self.embedding_dim)
                embedding[:len(flat)] = flat
            
            # 归一化
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding
        
        # 如果是字典（包含特征）
        elif isinstance(image_data, dict):
            embedding = np.zeros(self.embedding_dim)
            
            # 提取数值特征
            idx = 0
            for key, value in image_data.items():
                if isinstance(value, (int, float)) and idx < self.embedding_dim:
                    embedding[idx] = value
                    idx += 1
            
            # 归一化
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding
        
        # 默认：随机向量
        return np.random.randn(self.embedding_dim) * 0.1
    
    def extract_features(self, image_data: Any) -> Dict[str, Any]:
        """提取图像特征"""
        if isinstance(image_data, dict):
            return {
                'has_face': image_data.get('has_face', False),
                'scene_type': image_data.get('scene', 'unknown'),
                'brightness': image_data.get('brightness', 0.5),
                'objects_count': len(image_data.get('objects', []))
            }
        
        return {
            'has_data': True,
            'data_type': str(type(image_data))
        }


class SensorEncoder:
    """传感器数据编码器"""
    
    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim
    
    def encode(self, sensor_data: Dict[str, Any]) -> np.ndarray:
        """编码传感器数据为向量"""
        embedding = np.zeros(self.embedding_dim)
        
        # 标准化的传感器字段
        sensor_fields = [
            'heart_rate', 'steps', 'sleep_hours', 'calories',
            'temperature', 'humidity', 'light_level',
            'accelerometer_x', 'accelerometer_y', 'accelerometer_z',
            'gyroscope_x', 'gyroscope_y', 'gyroscope_z'
        ]
        
        # 填充向量
        for idx, field in enumerate(sensor_fields):
            if idx >= self.embedding_dim:
                break
            if field in sensor_data:
                value = sensor_data[field]
                # 简单归一化
                if field == 'heart_rate':
                    embedding[idx] = value / 200.0
                elif field == 'steps':
                    embedding[idx] = min(value / 10000.0, 1.0)
                elif field == 'sleep_hours':
                    embedding[idx] = value / 12.0
                elif field == 'calories':
                    embedding[idx] = value / 3000.0
                else:
                    embedding[idx] = value
        
        return embedding
    
    def extract_features(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取传感器特征"""
        features = {
            'sensor_count': len(sensor_data),
            'has_health_data': any(k in sensor_data for k in ['heart_rate', 'steps', 'sleep_hours']),
            'has_motion_data': any(k in sensor_data for k in ['accelerometer_x', 'gyroscope_x']),
            'has_environment_data': any(k in sensor_data for k in ['temperature', 'humidity'])
        }
        
        # 计算活动水平
        if 'steps' in sensor_data:
            steps = sensor_data['steps']
            if steps > 10000:
                features['activity_level'] = 'high'
            elif steps > 5000:
                features['activity_level'] = 'medium'
            else:
                features['activity_level'] = 'low'
        
        return features


class AttentionFusion:
    """注意力机制融合"""
    
    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim
        # 简化的注意力权重
        self.attention_weights = np.random.randn(embedding_dim, embedding_dim) * 0.1
    
    def compute_attention(
        self,
        embeddings: List[np.ndarray],
        modality_types: List[str]
    ) -> np.ndarray:
        """计算注意力权重"""
        n_modalities = len(embeddings)
        
        if n_modalities == 0:
            return np.array([])
        
        if n_modalities == 1:
            return np.array([1.0])
        
        # 计算相似度矩阵
        similarity_matrix = np.zeros((n_modalities, n_modalities))
        for i in range(n_modalities):
            for j in range(n_modalities):
                if i != j:
                    # 余弦相似度
                    similarity = np.dot(embeddings[i], embeddings[j])
                    similarity_matrix[i, j] = similarity
        
        # 计算注意力分数
        attention_scores = np.sum(similarity_matrix, axis=1)
        
        # Softmax归一化
        exp_scores = np.exp(attention_scores - np.max(attention_scores))
        attention_weights = exp_scores / np.sum(exp_scores)
        
        return attention_weights
    
    def fuse(
        self,
        embeddings: List[np.ndarray],
        attention_weights: np.ndarray
    ) -> np.ndarray:
        """使用注意力权重融合嵌入"""
        if len(embeddings) == 0:
            return np.zeros(self.embedding_dim)
        
        # 加权求和
        fused = np.zeros(self.embedding_dim)
        for embedding, weight in zip(embeddings, attention_weights):
            fused += embedding * weight
        
        # 归一化
        norm = np.linalg.norm(fused)
        if norm > 0:
            fused = fused / norm
        
        return fused


class EnhancedMultimodalFusion:
    """增强多模态融合系统 - 支持实时融合"""
    
    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim
        
        # 编码器
        self.text_encoder = TextEncoder(embedding_dim)
        self.image_encoder = ImageEncoder(embedding_dim)
        self.sensor_encoder = SensorEncoder(embedding_dim)
        
        # 融合器
        self.attention_fusion = AttentionFusion(embedding_dim)
        
        # 统计
        self.fusion_history = []
        
        # 实时融合状态
        self.realtime_enabled = False
        self.last_fusion_time = None
        self.fusion_callbacks = []  # 回调函数列表
        
        # 数据缓冲区（用于实时融合）
        self.data_buffer = {
            'text': None,
            'image': None,
            'sensor': None,
            'timestamp': None
        }
    
    def enable_realtime_fusion(self, callback=None):
        """
        启用实时融合模式
        
        Args:
            callback: 融合完成后的回调函数
        """
        self.realtime_enabled = True
        if callback:
            self.fusion_callbacks.append(callback)
        print("✓ 实时融合模式已启用")
    
    def disable_realtime_fusion(self):
        """禁用实时融合模式"""
        self.realtime_enabled = False
        self.fusion_callbacks = []
        print("✓ 实时融合模式已禁用")
    
    def update_realtime_data(
        self,
        modality_type: str,
        data: Any,
        auto_fuse: bool = True
    ) -> Optional[FusedRepresentation]:
        """
        更新实时数据并触发融合
        
        Args:
            modality_type: 模态类型
            data: 数据
            auto_fuse: 是否自动触发融合
        
        Returns:
            如果触发融合，返回融合结果
        """
        if not self.realtime_enabled:
            return None
        
        # 更新缓冲区
        self.data_buffer[modality_type] = data
        self.data_buffer['timestamp'] = datetime.now()
        
        # 自动融合
        if auto_fuse:
            return self._trigger_realtime_fusion()
        
        return None
    
    def _trigger_realtime_fusion(self) -> Optional[FusedRepresentation]:
        """触发实时融合"""
        # 收集可用的模态数据
        modalities = []
        
        for modality_type in ['text', 'image', 'sensor']:
            if self.data_buffer[modality_type] is not None:
                modality_obj = self.process_modality(
                    modality_type,
                    self.data_buffer[modality_type]
                )
                modalities.append(modality_obj)
        
        if not modalities:
            return None
        
        # 执行融合
        fused = self.fuse(modalities, fusion_strategy='attention')
        self.last_fusion_time = datetime.now()
        
        # 调用回调函数
        for callback in self.fusion_callbacks:
            try:
                callback(fused)
            except Exception as e:
                print(f"回调函数执行失败: {e}")
        
        return fused
    
    def get_realtime_status(self) -> Dict[str, Any]:
        """获取实时融合状态"""
        return {
            'enabled': self.realtime_enabled,
            'last_fusion_time': self.last_fusion_time.isoformat() if self.last_fusion_time else None,
            'buffer_status': {
                modality: data is not None
                for modality, data in self.data_buffer.items()
                if modality != 'timestamp'
            },
            'callback_count': len(self.fusion_callbacks)
        }
    
    def process_modality(
        self,
        modality_type: str,
        data: Any,
        confidence: float = 1.0
    ) -> ModalityData:
        """处理单一模态数据"""
        # 选择编码器
        if modality_type == 'text':
            embedding = self.text_encoder.encode(str(data))
            metadata = self.text_encoder.extract_features(str(data))
        elif modality_type == 'image':
            embedding = self.image_encoder.encode(data)
            metadata = self.image_encoder.extract_features(data)
        elif modality_type == 'sensor':
            embedding = self.sensor_encoder.encode(data)
            metadata = self.sensor_encoder.extract_features(data)
        else:
            # 未知模态，使用默认编码
            embedding = np.random.randn(self.embedding_dim) * 0.1
            metadata = {'type': modality_type}
        
        return ModalityData(
            modality_type=modality_type,
            raw_data=data,
            embedding=embedding,
            confidence=confidence,
            metadata=metadata
        )
    
    def fuse(
        self,
        modalities: List[ModalityData],
        fusion_strategy: str = 'attention'
    ) -> FusedRepresentation:
        """融合多模态数据"""
        if not modalities:
            return FusedRepresentation(
                unified_embedding=np.zeros(self.embedding_dim),
                modality_weights={},
                confidence=0.0,
                contributing_modalities=[],
                semantic_features={}
            )
        
        # 提取嵌入和类型
        embeddings = [m.embedding for m in modalities]
        modality_types = [m.modality_type for m in modalities]
        confidences = [m.confidence for m in modalities]
        
        # 计算融合权重
        if fusion_strategy == 'attention':
            weights = self.attention_fusion.compute_attention(embeddings, modality_types)
        elif fusion_strategy == 'confidence':
            # 基于置信度的权重
            weights = np.array(confidences)
            weights = weights / np.sum(weights)
        else:  # 'average'
            weights = np.ones(len(embeddings)) / len(embeddings)
        
        # 融合嵌入
        unified_embedding = self.attention_fusion.fuse(embeddings, weights)
        
        # 合并语义特征
        semantic_features = {}
        for modality in modalities:
            for key, value in modality.metadata.items():
                semantic_features[f"{modality.modality_type}_{key}"] = value
        
        # 计算综合置信度
        overall_confidence = np.mean(confidences)
        
        # 创建融合表示
        fused = FusedRepresentation(
            unified_embedding=unified_embedding,
            modality_weights={
                modality_types[i]: float(weights[i])
                for i in range(len(modality_types))
            },
            confidence=overall_confidence,
            contributing_modalities=modality_types,
            semantic_features=semantic_features,
        )
        
        # 记录历史
        self.fusion_history.append({
            'timestamp': datetime.now(),
            'modalities': modality_types,
            'confidence': overall_confidence
        })
        
        return fused
    
    def fuse_modalities(
        self,
        modalities: List[Dict[str, Any]],
        fusion_strategy: str = 'attention'
    ) -> Dict[str, Any]:
        """
        融合多模态数据（字典格式）
        
        Args:
            modalities: 模态列表，每个元素包含 'type' 和 'data'
            fusion_strategy: 融合策略
        
        Returns:
            融合结果字典
        """
        # 转换为ModalityData对象
        modality_objects = []
        for mod in modalities:
            mod_type = mod.get('type', 'unknown')
            mod_data = mod.get('data')
            confidence = mod.get('confidence', 1.0)
            
            modality_obj = self.process_modality(mod_type, mod_data, confidence)
            modality_objects.append(modality_obj)
        
        # 融合
        fused = self.fuse(modality_objects, fusion_strategy)
        
        # 转换为字典格式
        return {
            'unified_embedding': fused.unified_embedding,
            'modality_weights': fused.modality_weights,
            'confidence': fused.confidence,
            'contributing_modalities': fused.contributing_modalities,
            'semantic_features': fused.semantic_features,
            'timestamp': fused.timestamp.isoformat()
        }
    
    def fuse_multimodal_input(
        self,
        text: Optional[str] = None,
        image: Optional[Any] = None,
        sensor: Optional[Dict[str, Any]] = None,
        fusion_strategy: str = 'attention'
    ) -> FusedRepresentation:
        """便捷方法：融合多模态输入"""
        modalities = []
        
        if text is not None:
            modalities.append(self.process_modality('text', text))
        
        if image is not None:
            modalities.append(self.process_modality('image', image))
        
        if sensor is not None:
            modalities.append(self.process_modality('sensor', sensor))
        
        return self.fuse(modalities, fusion_strategy)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取融合统计"""
        if not self.fusion_history:
            return {
                'total_fusions': 0,
                'average_confidence': 0.0,
                'modality_usage': {}
            }
        
        # 统计模态使用
        modality_counts = defaultdict(int)
        for record in self.fusion_history:
            for modality in record['modalities']:
                modality_counts[modality] += 1
        
        # 平均置信度
        avg_confidence = np.mean([r['confidence'] for r in self.fusion_history])
        
        return {
            'total_fusions': len(self.fusion_history),
            'average_confidence': float(avg_confidence),
            'modality_usage': dict(modality_counts),
            'recent_fusions': self.fusion_history[-10:]
        }


class MultimodalContextEnhancer:
    """多模态上下文增强器"""
    
    def __init__(self, fusion_system: Optional[EnhancedMultimodalFusion] = None):
        self.fusion_system = fusion_system or EnhancedMultimodalFusion()
        self.context_history = []
    
    def enhance_context(
        self,
        user_id: str,
        current_data: Dict[str, Any],
        fused_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用多模态信息增强上下文"""
        enhanced = {}
        
        # 提取时间上下文
        timestamp = current_data.get('timestamp', datetime.now().timestamp() * 1000)
        dt = datetime.fromtimestamp(timestamp / 1000)
        hour = dt.hour
        
        if 0 <= hour < 6:
            enhanced['time_context'] = 'late_night'
        elif 6 <= hour < 9:
            enhanced['time_context'] = 'morning'
        elif 9 <= hour < 12:
            enhanced['time_context'] = 'forenoon'
        elif 12 <= hour < 14:
            enhanced['time_context'] = 'noon'
        elif 14 <= hour < 18:
            enhanced['time_context'] = 'afternoon'
        elif 18 <= hour < 22:
            enhanced['time_context'] = 'evening'
        else:
            enhanced['time_context'] = 'night'
        
        # 提取活动水平
        sensor_data = current_data.get('sensor', {})
        if 'steps' in sensor_data:
            steps = sensor_data['steps']
            if steps > 10000:
                enhanced['activity_level'] = 0.8
            elif steps > 5000:
                enhanced['activity_level'] = 0.5
            else:
                enhanced['activity_level'] = 0.2
        else:
            enhanced['activity_level'] = 0.5
        
        # 添加多模态特征
        enhanced['multimodal'] = {
            'confidence': fused_features.get('confidence', 0),
            'modalities': fused_features.get('contributing_modalities', []),
            'weights': fused_features.get('modality_weights', {})
        }
        
        # 数据质量评估
        modality_count = len(fused_features.get('contributing_modalities', []))
        enhanced['data_quality'] = min(modality_count / 4.0, 1.0)
        
        return enhanced
    
    def create_rich_context(
        self,
        user_data: Dict[str, Any],
        text: Optional[str] = None,
        image: Optional[Any] = None,
        sensor: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建丰富的多模态上下文"""
        # 融合多模态数据
        fused = self.fusion_system.fuse_multimodal_input(text, image, sensor)
        
        # 基础上下文
        base_context = {
            'data_quality': 0.5,
            'urgency': 0.5,
            'complexity': 0.5,
            'domain': 'health'
        }
        
        # 增强上下文
        enhanced_context = self.enhance_context(base_context, fused)
        
        # 添加用户数据
        enhanced_context['user_data'] = user_data
        enhanced_context['fused_representation'] = fused
        
        return enhanced_context
