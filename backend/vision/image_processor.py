"""
图像处理模块
Image Processor - 处理上传的图像
集成 Qwen-VL-Plus 多模态模型进行真实的图像理解
"""
import base64
import io
from datetime import datetime
from typing import Dict, List, Any, Optional
from PIL import Image
import numpy as np
from .qwen_vision_analyzer import get_vision_analyzer


class ImageProcessor:
    """
    图像处理器
    集成 Qwen-VL-Plus 多模态模型进行真实的图像理解
    """
    def __init__(self):
        self.max_size = (1024, 1024)  # 最大尺寸
        self.quality = 85  # JPEG 质量
        
        # 获取 Qwen 视觉分析器
        self.vision_analyzer = get_vision_analyzer()
        self.use_ai_vision = self.vision_analyzer.enabled
    
    def process_image(
        self,
        image_data: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        处理图像 - 使用 Qwen-VL-Plus 多模态模型进行深度理解
        
        Args:
            image_data: Base64 编码的图像数据（格式：data:image/jpeg;base64,xxx 或纯 base64）
            metadata: 元数据（时间、位置等）
        
        Returns:
            处理结果
        """
        try:
            # 解码图像
            image = self._decode_image(image_data)
            
            # 调整大小
            image = self._resize_image(image)
            
            # 提取基础特征
            features = self._extract_basic_features(image)
            
            # 生成缩略图
            thumbnail = self._generate_thumbnail(image)
            
            # 确保 image_data 是完整的 data URL 格式
            if not image_data.startswith('data:image'):
                # 如果只是 base64，添加前缀
                image_data = f"data:image/jpeg;base64,{image_data}"
            
            # 使用 Qwen-VL-Plus 多模态模型进行深度理解
            if self.use_ai_vision:
                print("[ImageProcessor] 使用 Qwen-VL-Plus 分析图像...")
                vision_result = self.vision_analyzer.analyze_image(
                    image_url=image_data,
                    context=metadata
                )
                
                scene = vision_result.get('scene', {})
                objects = vision_result.get('objects', [])
                people = vision_result.get('people', {})
                description = vision_result.get('description', '')
                health_context = vision_result.get('health_context', '')
                print(f"[ImageProcessor] 分析完成: {description[:50]}...")
            else:
                # 降级到基础规则
                print("[ImageProcessor] 使用基础规则分析图像...")
                scene = self._classify_scene(features, metadata)
                objects = []
                people = {'count': 0, 'activities': []}
                description = scene.get('description', '')
                health_context = ''
            
            return {
                'success': True,
                'image_id': self._generate_id(),
                'timestamp': metadata.get('timestamp', datetime.now().isoformat()) if metadata else datetime.now().isoformat(),
                'location': metadata.get('location') if metadata else None,
                'features': features,
                'scene': scene,
                'objects': objects,
                'people': people,
                'description': description,
                'health_context': health_context,
                'thumbnail': thumbnail,
                'size': image.size,
                'format': image.format,
                'analysis_method': 'qwen_vl_plus' if self.use_ai_vision else 'basic'
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_for_health(
        self,
        image_data: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        从健康角度分析图像
        """
        try:
            # 确保格式正确
            if not image_data.startswith('data:image'):
                image_data = f"data:image/jpeg;base64,{image_data}"
            
            if self.use_ai_vision:
                return self.vision_analyzer.analyze_for_health(
                    image_url=image_data,
                    context=metadata
                )
            else:
                return {
                    'activity_type': 'unknown',
                    'health_indicators': {},
                    'suggestions': [],
                    'risk_level': 'low',
                    'confidence': 0.0
                }
        except Exception as e:
            print(f"健康分析失败: {e}")
            return {
                'error': str(e),
                'activity_type': 'unknown'
            }
    
    def _decode_image(self, image_data: str) -> Image.Image:
        """解码 Base64 图像"""
        # 移除 data URL 前缀（如果有）
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # 解码
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # 转换为 RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        return image
    
    def _resize_image(self, image: Image.Image) -> Image.Image:
        """调整图像大小"""
        if image.size[0] > self.max_size[0] or image.size[1] > self.max_size[1]:
            image.thumbnail(self.max_size, Image.Resampling.LANCZOS)
        return image
    
    def _extract_basic_features(self, image: Image.Image) -> Dict:
        """提取基础特征（不使用深度学习）"""
        # 转换为 numpy 数组
        img_array = np.array(image)
        
        # 计算颜色统计
        mean_color = img_array.mean(axis=(0, 1)).tolist()
        std_color = img_array.std(axis=(0, 1)).tolist()
        
        # 计算亮度
        brightness = img_array.mean()
        
        # 计算对比度
        contrast = img_array.std()
        
        # 颜色分布
        hist_r = np.histogram(img_array[:,:,0], bins=8)[0].tolist()
        hist_g = np.histogram(img_array[:,:,1], bins=8)[0].tolist()
        hist_b = np.histogram(img_array[:,:,2], bins=8)[0].tolist()
        
        return {
            'mean_color': mean_color,
            'std_color': std_color,
            'brightness': float(brightness),
            'contrast': float(contrast),
            'color_histogram': {
                'r': hist_r,
                'g': hist_g,
                'b': hist_b
            }
        }
    
    def _classify_scene(self, features: Dict, metadata: Optional[Dict]) -> Dict:
        """
        场景分类（基于规则 - 降级方案）
        """
        brightness = features['brightness']
        mean_color = features['mean_color']
        
        # 基于亮度判断室内/室外
        if brightness > 150:
            indoor_outdoor = 'outdoor'
            confidence = 0.7
        elif brightness < 80:
            indoor_outdoor = 'indoor'
            confidence = 0.7
        else:
            indoor_outdoor = 'unknown'
            confidence = 0.5
        
        # 基于颜色判断场景类型
        r, g, b = mean_color
        
        if g > r and g > b:
            scene_type = 'nature'  # 绿色主导 -> 自然场景
        elif b > r and b > g:
            scene_type = 'sky'  # 蓝色主导 -> 天空/水
        elif r > g and r > b:
            scene_type = 'indoor'  # 红色主导 -> 室内
        else:
            scene_type = 'general'
        
        # 基于时间判断
        time_context = 'unknown'
        if metadata and 'timestamp' in metadata:
            try:
                dt = datetime.fromisoformat(metadata['timestamp'])
                hour = dt.hour
                
                if 6 <= hour < 9:
                    time_context = 'morning'
                elif 12 <= hour < 14:
                    time_context = 'lunch'
                elif 18 <= hour < 20:
                    time_context = 'dinner'
                elif 22 <= hour or hour < 6:
                    time_context = 'night'
                else:
                    time_context = 'day'
            except:
                pass
        
        return {
            'type': scene_type,
            'indoor_outdoor': indoor_outdoor,
            'time_of_day': time_context,
            'lighting': 'bright' if brightness > 150 else 'dim',
            'confidence': confidence,
            'description': self._generate_scene_description(
                indoor_outdoor, scene_type, time_context
            )
        }
    
    def _generate_scene_description(
        self,
        indoor_outdoor: str,
        scene_type: str,
        time_context: str
    ) -> str:
        """生成场景描述"""
        descriptions = {
            ('outdoor', 'nature', 'morning'): '早晨的户外自然场景',
            ('outdoor', 'nature', 'day'): '白天的户外自然场景',
            ('indoor', 'general', 'lunch'): '午餐时间的室内场景',
            ('indoor', 'general', 'dinner'): '晚餐时间的室内场景',
            ('indoor', 'general', 'night'): '夜晚的室内场景',
        }
        
        key = (indoor_outdoor, scene_type, time_context)
        return descriptions.get(key, f'{indoor_outdoor} {scene_type} 场景')
    
    def _generate_thumbnail(self, image: Image.Image) -> str:
        """生成缩略图（Base64）"""
        # 创建缩略图
        thumbnail = image.copy()
        thumbnail.thumbnail((200, 200), Image.Resampling.LANCZOS)
        
        # 转换为 Base64
        buffer = io.BytesIO()
        thumbnail.save(buffer, format='JPEG', quality=70)
        thumbnail_b64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/jpeg;base64,{thumbnail_b64}"
    
    def _generate_id(self) -> str:
        """生成图像 ID"""
        return f"img_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"


class ImageMemoryManager:
    """
    图像记忆管理器
    管理图像的存储和检索
    """
    def __init__(self, db_manager):
        self.db = db_manager
        self.processor = ImageProcessor()
    
    def add_image(
        self,
        user_id: str,
        image_data: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """添加图像"""
        # 处理图像
        result = self.processor.process_image(image_data, metadata)
        
        if not result['success']:
            return result
        
        # 分析活动
        health_analysis = self.processor.analyze_for_health(image_data, metadata)
        result['health_analysis'] = health_analysis
        
        # 保存到数据库
        # self.db.save_image_memory(user_id, result)
        
        return result
    
    def get_recent_images(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """获取最近的图像"""
        # return self.db.get_recent_images(user_id, limit)
        return []
    
    def search_images(
        self,
        user_id: str,
        query: Dict
    ) -> List[Dict]:
        """搜索图像"""
        # return self.db.search_images(user_id, query)
        return []
