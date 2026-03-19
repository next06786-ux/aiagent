"""
多模态感知层 - 第一层
整合所有感知模块，提供统一的多模态理解
"""
from typing import Dict, Any, Optional
from datetime import datetime
from backend.multimodal.text_processor import get_text_processor
from backend.multimodal.sensor_processor import get_sensor_processor
from backend.vision.image_processor import ImageProcessor
from backend.multimodal.enhanced_fusion import EnhancedMultimodalFusion


class PerceptionLayer:
    """
    多模态感知层
    
    职责：
    1. 接收原始的多模态数据（图像、文本、传感器）
    2. 使用专门的处理器处理每种模态
    3. 融合所有模态，生成统一的语义表示
    4. 输出给第2层（混合推理层）
    """
    
    def __init__(self):
        # 初始化各个处理器
        self.image_processor = ImageProcessor()
        self.text_processor = get_text_processor()
        self.sensor_processor = get_sensor_processor()
        self.fusion_engine = EnhancedMultimodalFusion()
        
        print("✓ 多模态感知层已初始化")
    
    def perceive(
        self,
        user_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        感知多模态数据
        
        Args:
            user_id: 用户ID
            data: 多模态数据
                {
                    "text": "用户输入的文字",
                    "image": "base64图像数据",
                    "sensor": {"steps": 1000, "accelerometer": {...}},
                    "context": {"timestamp": 123456, "location": "home"}
                }
        
        Returns:
            统一的多模态表示
        """
        try:
            print(f"\n[感知层] 开始处理用户 {user_id} 的数据...")
            
            perception_result = {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'modalities_processed': [],
                'perception_quality': 0.0
            }
            
            # 1. 处理文本模态
            if 'text' in data and data['text']:
                print("[感知层] 处理文本...")
                text_result = self.text_processor.process_text(
                    text=data['text'],
                    context=data.get('context')
                )
                perception_result['text_perception'] = text_result
                perception_result['modalities_processed'].append('text')
                print(f"  ✓ 文本处理完成: {text_result.get('intent', {}).get('type')}")
            
            # 2. 处理图像模态
            if 'image' in data and data['image']:
                print("[感知层] 处理图像...")
                image_result = self.image_processor.process_image(
                    image_data=data['image'],
                    metadata=data.get('context')
                )
                perception_result['image_perception'] = image_result
                perception_result['modalities_processed'].append('image')
                print(f"  ✓ 图像处理完成: {image_result.get('description', '')[:50]}...")
            
            # 3. 处理传感器模态
            if 'sensor' in data and data['sensor']:
                print("[感知层] 处理传感器数据...")
                sensor_result = self.sensor_processor.process_sensor_data(
                    sensor_data=data['sensor'],
                    context=data.get('context')
                )
                perception_result['sensor_perception'] = sensor_result
                perception_result['modalities_processed'].append('sensor')
                print(f"  ✓ 传感器处理完成: {sensor_result.get('activity_state', {}).get('primary_activity')}")
            
            # 4. 多模态融合
            print("[感知层] 融合多模态数据...")
            fused_representation = self._fuse_perceptions(perception_result, data)
            perception_result['fused_representation'] = fused_representation
            
            # 5. 计算感知质量
            perception_result['perception_quality'] = self._calculate_quality(perception_result)
            
            print(f"[感知层] 处理完成! 质量分数: {perception_result['perception_quality']:.2f}")
            print(f"[感知层] 处理的模态: {', '.join(perception_result['modalities_processed'])}\n")
            
            return perception_result
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'user_id': user_id,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _fuse_perceptions(
        self,
        perception_result: Dict[str, Any],
        raw_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """融合各个模态的感知结果"""
        fused = {
            'scene_understanding': {},
            'user_state': {},
            'context': {},
            'confidence': 0.0
        }
        
        # 从图像理解场景
        if 'image_perception' in perception_result:
            img = perception_result['image_perception']
            if img.get('success'):
                fused['scene_understanding'] = {
                    'scene_type': img.get('scene', {}).get('type', 'unknown'),
                    'objects': img.get('objects', []),
                    'description': img.get('description', ''),
                    'environment': img.get('scene', {}).get('indoor_outdoor', 'unknown')
                }
        
        # 从文本理解意图和情感
        if 'text_perception' in perception_result:
            txt = perception_result['text_perception']
            if txt.get('success'):
                fused['user_state']['intent'] = txt.get('intent', {})
                fused['user_state']['sentiment'] = txt.get('sentiment', {})
                fused['user_state']['expressed_concerns'] = txt.get('keywords', [])
        
        # 从传感器理解活动状态
        if 'sensor_perception' in perception_result:
            sensor = perception_result['sensor_perception']
            if sensor.get('success'):
                fused['user_state']['activity'] = sensor.get('activity_state', {})
                fused['user_state']['health_indicators'] = sensor.get('health_indicators', {})
        
        # 整合上下文
        if 'context' in raw_data:
            ctx = raw_data['context']
            fused['context'] = {
                'timestamp': ctx.get('timestamp'),
                'location': ctx.get('location'),
                'time_of_day': self._infer_time_of_day(ctx.get('timestamp'))
            }
        
        # 计算整体置信度
        confidences = []
        if 'image_perception' in perception_result:
            confidences.append(perception_result['image_perception'].get('scene', {}).get('confidence', 0.5))
        if 'text_perception' in perception_result:
            confidences.append(perception_result['text_perception'].get('sentiment', {}).get('confidence', 0.5))
        if 'sensor_perception' in perception_result:
            confidences.append(perception_result['sensor_perception'].get('activity_state', {}).get('confidence', 0.5))
        
        fused['confidence'] = sum(confidences) / len(confidences) if confidences else 0.5
        
        return fused
    
    def _calculate_quality(self, perception_result: Dict[str, Any]) -> float:
        """
        计算感知质量分数（0-1）
        
        考虑因素：
        1. 数据完整性 - 每种模态的字段是否完整
        2. 置信度 - 各处理器返回的confidence分数
        3. 数据质量 - 文本长度、传感器数值合理性等
        4. 模态一致性 - 不同模态的结果是否相互印证
        """
        quality_scores = []
        
        # 1. 文本模态质量（权重0.3）
        if 'text_perception' in perception_result:
            text_quality = self._evaluate_text_quality(perception_result['text_perception'])
            quality_scores.append(('text', text_quality, 0.3))
        
        # 2. 图像模态质量（权重0.4）
        if 'image_perception' in perception_result:
            image_quality = self._evaluate_image_quality(perception_result['image_perception'])
            quality_scores.append(('image', image_quality, 0.4))
        
        # 3. 传感器模态质量（权重0.3）
        if 'sensor_perception' in perception_result:
            sensor_quality = self._evaluate_sensor_quality(perception_result['sensor_perception'])
            quality_scores.append(('sensor', sensor_quality, 0.3))
        
        if not quality_scores:
            return 0.0
        
        # 计算加权平均
        total_weight = sum(weight for _, _, weight in quality_scores)
        weighted_sum = sum(quality * weight for _, quality, weight in quality_scores)
        base_quality = weighted_sum / total_weight
        
        # 4. 模态一致性加成（最多+10%）
        consistency_bonus = self._evaluate_consistency(perception_result) * 0.1
        
        final_quality = min(base_quality + consistency_bonus, 1.0)
        
        return final_quality
    
    def _evaluate_text_quality(self, text_result: Dict[str, Any]) -> float:
        """评估文本感知质量"""
        if not text_result.get('success'):
            return 0.0
        
        quality = 0.0
        
        # 基础成功分（30%）
        quality += 0.3
        
        # 情感分析置信度（30%）
        sentiment_conf = text_result.get('sentiment', {}).get('confidence', 0.5)
        quality += sentiment_conf * 0.3
        
        # 意图识别置信度（20%）
        intent_conf = text_result.get('intent', {}).get('confidence', 0.5)
        quality += intent_conf * 0.2
        
        # 文本长度合理性（10%）
        text_length = text_result.get('length', 0)
        if text_length >= 5:  # 至少5个字符
            length_score = min(text_length / 50, 1.0)  # 50字符为满分
            quality += length_score * 0.1
        
        # 关键词提取质量（10%）
        keywords = text_result.get('keywords', [])
        if len(keywords) > 0:
            keyword_score = min(len(keywords) / 5, 1.0)  # 5个关键词为满分
            quality += keyword_score * 0.1
        
        return min(quality, 1.0)
    
    def _evaluate_image_quality(self, image_result: Dict[str, Any]) -> float:
        """评估图像感知质量"""
        if not image_result.get('success'):
            return 0.0
        
        quality = 0.0
        
        # 基础成功分（20%）
        quality += 0.2
        
        # 场景识别置信度（40%）
        scene_conf = image_result.get('scene', {}).get('confidence', 0.5)
        quality += scene_conf * 0.4
        
        # 描述完整性（20%）
        description = image_result.get('description', '')
        if description:
            desc_score = min(len(description) / 100, 1.0)  # 100字符为满分
            quality += desc_score * 0.2
        
        # 对象检测数量（10%）
        objects = image_result.get('objects', [])
        if len(objects) > 0:
            obj_score = min(len(objects) / 5, 1.0)  # 5个对象为满分
            quality += obj_score * 0.1
        
        # 健康评估完整性（10%）
        health_assessment = image_result.get('health_assessment', {})
        if health_assessment:
            quality += 0.1
        
        return min(quality, 1.0)
    
    def _evaluate_sensor_quality(self, sensor_result: Dict[str, Any]) -> float:
        """评估传感器感知质量"""
        if not sensor_result.get('success'):
            return 0.0
        
        quality = 0.0
        
        # 基础成功分（20%）
        quality += 0.2
        
        # 活动状态置信度（30%）
        activity_conf = sensor_result.get('activity_state', {}).get('confidence', 0.5)
        quality += activity_conf * 0.3
        
        # 数据完整性（30%）
        completeness = 0.0
        if 'steps_analysis' in sensor_result:
            completeness += 0.33
        if 'motion_analysis' in sensor_result:
            completeness += 0.33
        if 'light_analysis' in sensor_result:
            completeness += 0.34
        quality += completeness * 0.3
        
        # 数据合理性（20%）
        reasonableness = 0.0
        
        # 检查步数合理性
        steps_analysis = sensor_result.get('steps_analysis', {})
        steps = steps_analysis.get('steps', 0)
        if 0 <= steps <= 50000:  # 合理范围
            reasonableness += 0.5
        
        # 检查加速度合理性
        motion_analysis = sensor_result.get('motion_analysis', {})
        magnitude = motion_analysis.get('magnitude', 0)
        if 0 <= magnitude <= 20:  # 合理范围
            reasonableness += 0.5
        
        quality += reasonableness * 0.2
        
        return min(quality, 1.0)
    
    def _evaluate_consistency(self, perception_result: Dict[str, Any]) -> float:
        """
        评估模态一致性
        检查不同模态的结果是否相互印证
        """
        consistency_score = 0.0
        checks = 0
        
        # 检查1：文本情感 vs 图像场景
        if 'text_perception' in perception_result and 'image_perception' in perception_result:
            text_sentiment = perception_result['text_perception'].get('sentiment', {}).get('label', '')
            scene_type = perception_result['image_perception'].get('scene', {}).get('type', '')
            
            # 积极情感 + 户外/运动场景 = 一致
            if text_sentiment == 'positive' and scene_type in ['outdoor', 'sports', 'nature']:
                consistency_score += 0.3
            # 消极情感 + 室内/工作场景 = 可能一致
            elif text_sentiment == 'negative' and scene_type in ['indoor', 'office']:
                consistency_score += 0.2
            
            checks += 1
        
        # 检查2：传感器活动 vs 文本内容
        if 'text_perception' in perception_result and 'sensor_perception' in perception_result:
            health_category = perception_result['text_perception'].get('health_category', {}).get('primary', '')
            activity = perception_result['sensor_perception'].get('activity_state', {}).get('primary_activity', '')
            
            # 文本提到运动 + 传感器检测到运动 = 一致
            if health_category == 'exercise' and activity in ['walking', 'exercising']:
                consistency_score += 0.4
            # 文本提到休息 + 传感器检测到静止 = 一致
            elif health_category == 'sleep' and activity == 'sedentary':
                consistency_score += 0.4
            
            checks += 1
        
        # 检查3：图像环境 vs 传感器光线
        if 'image_perception' in perception_result and 'sensor_perception' in perception_result:
            scene = perception_result['image_perception'].get('scene', {})
            indoor_outdoor = scene.get('indoor_outdoor', '')
            
            light_analysis = perception_result['sensor_perception'].get('light_analysis', {})
            light_env = light_analysis.get('environment', '')
            
            # 图像显示户外 + 光线传感器显示明亮 = 一致
            if indoor_outdoor == 'outdoor' and 'outdoor' in light_env:
                consistency_score += 0.3
            # 图像显示室内 + 光线传感器显示室内 = 一致
            elif indoor_outdoor == 'indoor' and 'indoor' in light_env:
                consistency_score += 0.3
            
            checks += 1
        
        return consistency_score / checks if checks > 0 else 0.0
    
    def _infer_time_of_day(self, timestamp: Optional[int]) -> str:
        """推断时间段"""
        if not timestamp:
            return 'unknown'
        
        try:
            dt = datetime.fromtimestamp(timestamp / 1000)
            hour = dt.hour
            
            if 6 <= hour < 9:
                return 'morning'
            elif 9 <= hour < 12:
                return 'forenoon'
            elif 12 <= hour < 14:
                return 'noon'
            elif 14 <= hour < 18:
                return 'afternoon'
            elif 18 <= hour < 22:
                return 'evening'
            else:
                return 'night'
        except:
            return 'unknown'


# 全局实例
_perception_layer = None

def get_perception_layer() -> PerceptionLayer:
    """获取全局感知层实例"""
    global _perception_layer
    if _perception_layer is None:
        _perception_layer = PerceptionLayer()
    return _perception_layer
