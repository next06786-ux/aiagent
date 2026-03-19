"""
文本处理模块
处理用户输入的文本，提取意图、情感、关键信息
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import re


class TextProcessor:
    """
    文本处理器
    提取文本中的意图、情感、关键词等信息
    """
    
    def __init__(self):
        # 情感词典
        self.positive_words = {
            '好', '棒', '开心', '高兴', '满意', '喜欢', '爱', '舒服', '轻松',
            'good', 'great', 'happy', 'love', 'nice', 'excellent'
        }
        self.negative_words = {
            '差', '糟', '难过', '不满', '讨厌', '累', '疲劳', '压力', '焦虑',
            'bad', 'terrible', 'sad', 'tired', 'stress', 'anxious'
        }
        
        # 健康相关关键词
        self.health_keywords = {
            'food': ['吃', '早餐', '午餐', '晚餐', '食物', '饮食', 'eat', 'food', 'meal'],
            'exercise': ['运动', '跑步', '健身', '锻炼', 'exercise', 'run', 'gym', 'workout'],
            'sleep': ['睡觉', '睡眠', '休息', 'sleep', 'rest', 'tired'],
            'work': ['工作', '加班', '会议', '项目', 'work', 'meeting', 'project'],
            'mood': ['心情', '情绪', '感觉', 'mood', 'feel', 'emotion']
        }
    
    def process_text(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        处理文本
        
        Args:
            text: 用户输入的文本
            context: 上下文信息（时间、位置等）
        
        Returns:
            处理结果
        """
        if not text or not text.strip():
            return {
                'success': False,
                'error': 'Empty text'
            }
        
        try:
            # 基础信息
            result = {
                'success': True,
                'original_text': text,
                'processed_text': text.strip(),
                'length': len(text),
                'timestamp': datetime.now().isoformat()
            }
            
            # 情感分析
            result['sentiment'] = self._analyze_sentiment(text)
            
            # 意图识别
            result['intent'] = self._detect_intent(text)
            
            # 关键词提取
            result['keywords'] = self._extract_keywords(text)
            
            # 健康相关分类
            result['health_category'] = self._classify_health_category(text)
            
            # 提取数值信息
            result['numbers'] = self._extract_numbers(text)
            
            # 上下文增强
            if context:
                result['context_enhanced'] = self._enhance_with_context(text, context)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'original_text': text
            }
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """情感分析"""
        text_lower = text.lower()
        words = set(re.findall(r'\w+', text_lower))
        
        positive_count = len(words & self.positive_words)
        negative_count = len(words & self.negative_words)
        
        # 计算情感分数 (-1 到 1)
        total = positive_count + negative_count
        if total == 0:
            score = 0.0
            label = 'neutral'
        else:
            score = (positive_count - negative_count) / total
            if score > 0.3:
                label = 'positive'
            elif score < -0.3:
                label = 'negative'
            else:
                label = 'neutral'
        
        return {
            'score': score,
            'label': label,
            'positive_words': positive_count,
            'negative_words': negative_count,
            'confidence': min(abs(score) + 0.3, 1.0)
        }
    
    def _detect_intent(self, text: str) -> Dict[str, Any]:
        """意图识别"""
        text_lower = text.lower()
        
        # 问题意图
        if any(q in text_lower for q in ['?', '？', '吗', '呢', 'how', 'what', 'why']):
            intent_type = 'question'
            confidence = 0.8
        
        # 陈述意图
        elif any(s in text_lower for s in ['我', '今天', '刚', 'i ', 'just', 'today']):
            intent_type = 'statement'
            confidence = 0.7
        
        # 请求意图
        elif any(r in text_lower for r in ['帮', '建议', '推荐', 'help', 'suggest', 'recommend']):
            intent_type = 'request'
            confidence = 0.8
        
        else:
            intent_type = 'unknown'
            confidence = 0.3
        
        return {
            'type': intent_type,
            'confidence': confidence
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取（基于词频和长度）
        words = re.findall(r'\w+', text.lower())
        
        # 过滤停用词
        stop_words = {'的', '了', '是', '在', '我', '你', '他', '她', '它', 
                     'the', 'a', 'an', 'is', 'are', 'was', 'were', 'i', 'you'}
        
        keywords = [w for w in words if w not in stop_words and len(w) > 1]
        
        # 去重并保持顺序
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        
        return unique_keywords[:10]  # 最多返回10个关键词
    
    def _classify_health_category(self, text: str) -> Dict[str, Any]:
        """健康相关分类"""
        text_lower = text.lower()
        categories = []
        
        for category, keywords in self.health_keywords.items():
            if any(kw in text_lower for kw in keywords):
                categories.append(category)
        
        if not categories:
            return {
                'primary': 'general',
                'all': [],
                'confidence': 0.3
            }
        
        return {
            'primary': categories[0],
            'all': categories,
            'confidence': 0.7
        }
    
    def _extract_numbers(self, text: str) -> List[Dict[str, Any]]:
        """提取数值信息"""
        # 匹配数字（整数和小数）
        number_pattern = r'\d+\.?\d*'
        numbers = re.findall(number_pattern, text)
        
        results = []
        for num in numbers:
            try:
                value = float(num)
                results.append({
                    'value': value,
                    'text': num,
                    'context': self._get_number_context(text, num)
                })
            except:
                pass
        
        return results
    
    def _get_number_context(self, text: str, number: str) -> str:
        """获取数字的上下文"""
        # 查找数字前后的词
        pattern = r'(\w+\s+)?' + re.escape(number) + r'(\s+\w+)?'
        match = re.search(pattern, text)
        
        if match:
            return match.group(0).strip()
        return number
    
    def _enhance_with_context(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用上下文增强文本理解"""
        enhanced = {}
        
        # 时间上下文
        if 'timestamp' in context:
            try:
                dt = datetime.fromtimestamp(context['timestamp'] / 1000)
                hour = dt.hour
                
                if 6 <= hour < 9:
                    enhanced['time_period'] = 'morning'
                elif 12 <= hour < 14:
                    enhanced['time_period'] = 'lunch'
                elif 18 <= hour < 22:
                    enhanced['time_period'] = 'evening'
                else:
                    enhanced['time_period'] = 'other'
            except:
                pass
        
        # 位置上下文
        if 'location' in context:
            enhanced['location'] = context['location']
        
        # 活动上下文
        if 'activity' in context:
            enhanced['activity'] = context['activity']
        
        return enhanced


# 全局实例
_processor = None

def get_text_processor() -> TextProcessor:
    """获取全局文本处理器实例"""
    global _processor
    if _processor is None:
        _processor = TextProcessor()
    return _processor
