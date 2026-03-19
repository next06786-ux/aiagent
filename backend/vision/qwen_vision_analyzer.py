"""
Qwen 视觉分析器
使用 Qwen-VL-Plus 的多模态能力分析图像（通过 OpenAI 兼容接口）
"""
import os
from typing import Dict, Any, Optional
from openai import OpenAI
import json
import re


class QwenVisionAnalyzer:
    """
    使用 Qwen-VL-Plus 多模态模型分析图像
    通过 OpenAI 兼容接口调用
    """
    
    def __init__(self):
        self.api_key = os.getenv('DASHSCOPE_API_KEY')
        if self.api_key:
            # 使用 OpenAI 兼容接口
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            self.enabled = True
            print("✓ Qwen-VL-Plus 多模态分析已启用")
        else:
            self.client = None
            self.enabled = False
            print("⚠ 未配置 DASHSCOPE_API_KEY")
    
    def analyze_image(
        self,
        image_url: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        分析图像内容
        
        Args:
            image_url: 图像 URL 或 base64 数据（格式：data:image/jpeg;base64,xxx）
            context: 额外上下文（时间、位置等）
        
        Returns:
            分析结果
        """
        if not self.enabled:
            return self._fallback_result()
        
        try:
            # 构建提示词
            prompt = self._build_prompt(context)
            
            # 构建消息（OpenAI 格式）
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url  # 支持 base64 格式
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
            
            # 调用 Qwen-VL-Plus（通过 OpenAI 兼容接口）
            response = self.client.chat.completions.create(
                model="qwen-vl-plus",  # 使用多模态模型
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
            
            # 提取响应
            result_text = response.choices[0].message.content
            return self._parse_response(result_text)
                
        except Exception as e:
            print(f"图像分析出错: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_result()
    
    def _build_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """构建分析提示词"""
        prompt = """请详细分析这张图片，并以JSON格式返回以下信息：

{
  "scene": {
    "type": "场景类型（如：厨房、办公室、户外、餐厅等）",
    "indoor_outdoor": "indoor 或 outdoor",
    "lighting": "光线情况（明亮/昏暗/自然光等）",
    "time_of_day": "推测的时间段（早晨/中午/傍晚/夜晚）"
  },
  "objects": [
    {"name": "物体名称", "confidence": 0.9},
    {"name": "物体名称", "confidence": 0.85}
  ],
  "people": {
    "count": 人数,
    "activities": ["活动描述1", "活动描述2"]
  },
  "mood": "整体氛围（轻松/忙碌/安静等）",
  "description": "用一句话描述这张图片的主要内容",
  "health_context": "从健康角度的观察（如：在运动、在用餐、在工作等）"
}

请只返回JSON，不要其他文字。"""
        
        # 添加时间上下文
        if context and 'timestamp' in context:
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(context['timestamp'])
                prompt += f"\n\n参考信息：当前时间是 {dt.strftime('%Y-%m-%d %H:%M:%S')}"
            except:
                pass
        
        # 添加位置上下文
        if context and 'location' in context:
            prompt += f"\n位置信息：{context['location']}"
        
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """解析 Qwen 的响应"""
        try:
            # 提取 JSON 部分
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                # 标准化格式
                return {
                    'success': True,
                    'scene': result.get('scene', {}),
                    'objects': result.get('objects', []),
                    'people': result.get('people', {}),
                    'mood': result.get('mood', 'unknown'),
                    'description': result.get('description', ''),
                    'health_context': result.get('health_context', ''),
                    'raw_response': response_text,
                    'confidence': 0.85
                }
            else:
                # 如果没有 JSON，返回原始文本
                return {
                    'success': True,
                    'description': response_text[:200],
                    'raw_response': response_text,
                    'confidence': 0.5
                }
        except Exception as e:
            print(f"解析响应失败: {e}")
            return {
                'success': False,
                'description': response_text[:200] if response_text else '',
                'error': str(e)
            }
    
    def _fallback_result(self) -> Dict[str, Any]:
        """降级结果（当 API 不可用时）"""
        return {
            'success': False,
            'scene': {
                'type': 'unknown',
                'indoor_outdoor': 'unknown'
            },
            'objects': [],
            'people': {'count': 0, 'activities': []},
            'description': '图像分析服务暂时不可用',
            'confidence': 0.0
        }
    
    def analyze_for_health(
        self,
        image_url: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        从健康角度分析图像
        
        专注于：饮食、运动、睡眠、情绪等健康相关内容
        """
        if not self.enabled:
            return self._fallback_result()
        
        try:
            prompt = """请从健康管理的角度分析这张图片，以JSON格式返回：

{
  "activity_type": "活动类型（运动/用餐/工作/休息/社交等）",
  "health_indicators": {
    "food": "如果是饮食相关，描述食物类型和健康程度",
    "exercise": "如果是运动相关，描述运动类型和强度",
    "posture": "如果能看到人，描述姿势是否健康",
    "environment": "环境对健康的影响（光线、空气等）"
  },
  "suggestions": ["健康建议1", "健康建议2"],
  "risk_level": "风险等级（low/medium/high）",
  "confidence": 0.0-1.0
}

只返回JSON，不要其他内容。"""
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
            
            response = self.client.chat.completions.create(
                model="qwen-vl-plus",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            result_text = response.choices[0].message.content
            
            # 解析 JSON
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {'description': result_text}
                
        except Exception as e:
            print(f"健康分析出错: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_result()


# 全局实例
_analyzer = None

def get_vision_analyzer() -> QwenVisionAnalyzer:
    """获取全局视觉分析器实例"""
    global _analyzer
    if _analyzer is None:
        _analyzer = QwenVisionAnalyzer()
    return _analyzer
