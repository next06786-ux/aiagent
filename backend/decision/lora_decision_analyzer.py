"""
LoRA增强的决策分析器
使用用户专属的LoRA模型进行个性化决策分析
"""
import os
import sys
from typing import List, Dict, Any, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.lora.lora_model_manager import lora_manager


class LoRADecisionAnalyzer:
    """使用LoRA模型进行个性化决策分析"""
    
    def __init__(self):
        self.lora_manager = lora_manager
    
    def generate_timeline_with_lora(
        self,
        user_id: str,
        question: str,
        option: Dict[str, str],
        profile: Any,
        num_events: int = 3  # 减少到3
    ) -> List[Dict[str, Any]]:
        """
        使用LoRA模型生成完整的时间线
        
        Args:
            user_id: 用户ID
            question: 决策问题
            option: 选项信息
            profile: 用户性格画像
            num_events: 生成事件数量
        
        Returns:
            时间线事件列表
        """
        if not self.lora_manager.has_lora_model(user_id):
            return []
        
        try:
            # 构造时间线生成prompt
            prompt = self._build_timeline_prompt(
                question=question,
                option=option,
                profile=profile,
                num_events=num_events
            )
            
            # 使用LoRA模型生成（减少token数量以节省内存）
            response = self.lora_manager.generate(
                user_id=user_id,
                prompt=prompt,
                max_new_tokens=400,  # 减少到400
                temperature=0.7
            )
            
            # 解析JSON响应
            timeline = self._parse_timeline_json(response)
            
            # 清理GPU缓存
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            return timeline
            
        except Exception as e:
            print(f"⚠️ LoRA时间线生成失败: {e}")
            return []
    
    def _build_timeline_prompt(
        self,
        question: str,
        option: Dict[str, str],
        profile: Any,
        num_events: int
    ) -> str:
        """构造时间线生成prompt（简化版，减少内存使用）"""
        prompt = f"<|im_start|>user\n"
        prompt += f"决策：{question}\n"
        prompt += f"选择：{option['title']}\n\n"
        
        if profile:
            prompt += f"性格：{profile.decision_style}，{profile.risk_preference}\n\n"
        
        prompt += f"请直接输出{num_events}个关键事件的JSON数组，不要有其他文字说明：\n"
        prompt += f'<|im_end|>\n<|im_start|>assistant\n'
        prompt += f'{{"timeline": ['
        
        return prompt
    
    def _parse_timeline_json(self, response: str) -> List[Dict[str, Any]]:
        """解析时间线JSON响应（支持多种格式）"""
        import json
        import re
        
        timeline = []
        
        try:
            print(f"📝 LoRA原始响应长度: {len(response)} 字符")
            print(f"📝 LoRA原始响应前300字符: {response[:300]}")
            
            # 移除markdown代码块标记
            response = re.sub(r'```json\s*', '', response)
            response = re.sub(r'```\s*', '', response)
            
            # 尝试多种解析方式
            
            # 方式1: 标准格式 {"timeline": [...]}
            match1 = re.search(r'\{"timeline":\s*\[(.*?)\]\s*\}', response, re.DOTALL)
            if match1:
                try:
                    json_str = match1.group(0)
                    data = json.loads(json_str)
                    if 'timeline' in data:
                        timeline = self._extract_events(data['timeline'])
                        if timeline:
                            print(f"✓ 方式1成功: {len(timeline)} 个事件")
                            return timeline
                except:
                    pass
            
            # 方式2: 直接数组 [...]
            match2 = re.search(r'\[\s*\{.*?\}\s*\]', response, re.DOTALL)
            if match2:
                try:
                    json_str = match2.group(0)
                    data = json.loads(json_str)
                    timeline = self._extract_events(data)
                    if timeline:
                        print(f"✓ 方式2成功: {len(timeline)} 个事件")
                        return timeline
                except:
                    pass
            
            # 方式3: 嵌套格式 [{"timeline": [...]}]
            match3 = re.search(r'\[\s*\{\s*"timeline":\s*\[(.*?)\]\s*\}\s*\]', response, re.DOTALL)
            if match3:
                try:
                    inner_array = '[' + match3.group(1) + ']'
                    data = json.loads(inner_array)
                    timeline = self._extract_events(data)
                    if timeline:
                        print(f"✓ 方式3成功: {len(timeline)} 个事件")
                        return timeline
                except:
                    pass
            
            print(f"⚠️ 所有解析方式都失败")
            
        except Exception as e:
            print(f"⚠️ 解析时间线JSON失败: {e}")
        
        return timeline
    
    def _extract_events(self, data) -> List[Dict[str, Any]]:
        """从数据中提取事件"""
        events = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    if 'month' in item and 'event' in item:
                        events.append({
                            'month': int(item['month']),
                            'event': str(item['event']),
                            'impact': item.get('impact', {}),
                            'probability': float(item.get('probability', 0.8))
                        })
        events.sort(key=lambda x: x['month'])
        return events
    
    def enhance_timeline_events(
        self,
        user_id: str,
        option_title: str,
        option_description: str,
        base_events: List[Dict],
        profile: Any,
        use_lora: bool = True
    ) -> List[Dict]:
        """
        使用LoRA模型增强时间线事件描述
        
        Args:
            user_id: 用户ID
            option_title: 选项标题
            option_description: 选项描述
            base_events: 基础事件列表
            profile: 用户性格画像
            use_lora: 是否使用LoRA模型
        
        Returns:
            增强后的事件列表
        """
        if not use_lora or not self.lora_manager.has_lora_model(user_id):
            # 如果不使用LoRA或用户没有LoRA模型，返回原始事件
            return base_events
        
        try:
            enhanced_events = []
            
            for event in base_events:
                # 构造个性化分析prompt
                prompt = self._build_event_analysis_prompt(
                    option_title=option_title,
                    option_description=option_description,
                    event=event,
                    profile=profile
                )
                
                # 使用LoRA模型生成个性化分析
                analysis = self.lora_manager.generate(
                    user_id=user_id,
                    prompt=prompt,
                    max_new_tokens=150,
                    temperature=0.7
                )
                
                # 增强事件描述
                enhanced_event = event.copy()
                enhanced_event['event'] = self._extract_event_description(analysis, event['event'])
                
                enhanced_events.append(enhanced_event)
            
            return enhanced_events
            
        except Exception as e:
            print(f"⚠️ LoRA增强失败，使用基础事件: {e}")
            return base_events
    
    def generate_personalized_recommendation(
        self,
        user_id: str,
        question: str,
        options: List[Dict],
        profile: Any,
        use_lora: bool = True
    ) -> str:
        """
        使用LoRA模型生成个性化推荐
        
        必须使用LoRA模型，如果用户没有LoRA模型会抛出异常
        """
        if not use_lora:
            raise ValueError("推荐生成必须启用LoRA模型 (use_lora=True)")
        
        if not self.lora_manager.has_lora_model(user_id):
            raise ValueError(f"用户 {user_id} 还没有训练LoRA模型，无法生成个性化推荐")
        
        # 构造推荐prompt
        prompt = self._build_recommendation_prompt(
            question=question,
            options=options,
            profile=profile
        )
        
        # 使用LoRA模型生成
        recommendation = self.lora_manager.generate(
            user_id=user_id,
            prompt=prompt,
            max_new_tokens=300,
            temperature=0.7
        )
        
        return self._clean_recommendation(recommendation)
    
    def analyze_decision_with_lora(
        self,
        user_id: str,
        question: str,
        option: Dict[str, str],
        profile: Any
    ) -> Dict[str, Any]:
        """
        使用LoRA模型深度分析单个决策选项
        
        Args:
            user_id: 用户ID
            question: 决策问题
            option: 单个选项
            profile: 用户性格画像
        
        Returns:
            分析结果（包含优势、劣势、建议等）
        """
        if not self.lora_manager.has_lora_model(user_id):
            return {
                "advantages": [],
                "disadvantages": [],
                "suggestions": [],
                "personal_fit": 0.5
            }
        
        try:
            # 构造分析prompt
            prompt = self._build_analysis_prompt(
                question=question,
                option=option,
                profile=profile
            )
            
            # 使用LoRA模型生成分析
            analysis = self.lora_manager.generate(
                user_id=user_id,
                prompt=prompt,
                max_new_tokens=400,
                temperature=0.7
            )
            
            # 解析分析结果
            return self._parse_analysis(analysis)
            
        except Exception as e:
            print(f"⚠️ LoRA分析失败: {e}")
            return {
                "advantages": [],
                "disadvantages": [],
                "suggestions": [],
                "personal_fit": 0.5
            }
    
    def _build_event_analysis_prompt(
        self,
        option_title: str,
        option_description: str,
        event: Dict,
        profile: Any
    ) -> str:
        """构造事件分析prompt"""
        prompt = f"<|im_start|>user\n"
        prompt += f"我正在考虑「{option_title}」这个选择。\n"
        prompt += f"在第{event['month']}个月，可能会发生：{event['event']}\n"
        prompt += f"请根据我的性格特点，用一句话描述这个事件对我的具体影响。\n"
        prompt += f"<|im_end|>\n<|im_start|>assistant\n"
        
        return prompt
    
    def _build_recommendation_prompt(
        self,
        question: str,
        options: List[Dict],
        profile: Any
    ) -> str:
        """构造推荐prompt"""
        prompt = f"<|im_start|>user\n"
        prompt += f"我面临一个重要决策：{question}\n\n"
        prompt += f"我分析了以下几个选项：\n"
        
        for opt in options:
            prompt += f"\n{opt['title']}：\n"
            prompt += f"- 综合得分：{opt['final_score']:.1f}/100\n"
            prompt += f"- 风险等级：{opt['risk_level']:.2f}\n"
        
        if profile:
            prompt += f"\n我的性格特点：\n"
            prompt += f"- 决策风格：{profile.decision_style}\n"
            prompt += f"- 风险偏好：{profile.risk_preference}\n"
            prompt += f"- 生活优先级：{profile.life_priority}\n"
        
        prompt += f"\n请给我一个个性化的建议，告诉我应该选择哪个选项，以及为什么。\n"
        prompt += f"<|im_end|>\n<|im_start|>assistant\n"
        
        return prompt
    
    def _build_analysis_prompt(
        self,
        question: str,
        option: Dict[str, str],
        profile: Any
    ) -> str:
        """构造深度分析prompt"""
        prompt = f"<|im_start|>user\n"
        prompt += f"我在考虑：{question}\n"
        prompt += f"其中一个选项是「{option['title']}」：{option.get('description', '')}\n\n"
        
        if profile:
            prompt += f"考虑到我的性格特点（{profile.decision_style}、{profile.risk_preference}），\n"
        
        prompt += f"请分析这个选项的：\n"
        prompt += f"1. 优势（3点）\n"
        prompt += f"2. 劣势（3点）\n"
        prompt += f"3. 给我的建议（2点）\n"
        prompt += f"<|im_end|>\n<|im_start|>assistant\n"
        
        return prompt
    
    def _extract_event_description(self, analysis: str, fallback: str) -> str:
        """从LoRA生成的分析中提取事件描述"""
        # 清理生成的文本
        analysis = analysis.strip()
        
        # 如果生成的文本太短或太长，使用原始描述
        if len(analysis) < 10 or len(analysis) > 200:
            return fallback
        
        # 取第一句话
        sentences = analysis.split('。')
        if sentences:
            return sentences[0] + '。'
        
        return fallback
    
    def _clean_recommendation(self, recommendation: str) -> str:
        """清理推荐文本"""
        # 移除多余的空白
        recommendation = recommendation.strip()
        
        # 移除可能的重复内容
        lines = recommendation.split('\n')
        unique_lines = []
        seen = set()
        
        for line in lines:
            line = line.strip()
            if line and line not in seen:
                unique_lines.append(line)
                seen.add(line)
        
        return '\n'.join(unique_lines)
    
    def _parse_analysis(self, analysis: str) -> Dict[str, Any]:
        """解析LoRA生成的分析结果"""
        result = {
            "advantages": [],
            "disadvantages": [],
            "suggestions": [],
            "personal_fit": 0.7  # 默认适配度
        }
        
        # 简单的文本解析
        lines = analysis.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if '优势' in line or 'advantage' in line.lower():
                current_section = 'advantages'
            elif '劣势' in line or 'disadvantage' in line.lower():
                current_section = 'disadvantages'
            elif '建议' in line or 'suggestion' in line.lower():
                current_section = 'suggestions'
            elif current_section and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                # 提取列表项
                item = line.lstrip('-•0123456789. ').strip()
                if item:
                    result[current_section].append(item)
        
        return result
    
    def get_lora_status(self, user_id: str) -> Dict[str, Any]:
        """获取用户的LoRA模型状态"""
        try:
            info = self.lora_manager.get_model_info(user_id)
            
            return {
                "has_lora": info.get('has_lora', False),
                "model_version": info.get('model_version', 0),
                "is_loaded": info.get('is_loaded', False),
                "last_train_time": info.get('last_train_time'),
                "training_data_size": info.get('current_data_size', 0)
            }
        except Exception as e:
            print(f"⚠️ 获取LoRA状态失败: {e}")
            # 返回默认状态
            return {
                "has_lora": False,
                "model_version": 0,
                "is_loaded": False,
                "last_train_time": None,
                "training_data_size": 0,
                "error": str(e)
            }


# 测试代码
if __name__ == "__main__":
    analyzer = LoRADecisionAnalyzer()
    
    # 测试用户
    user_id = "test_user_001"
    
    # 检查LoRA状态
    status = analyzer.get_lora_status(user_id)
    print("="*60)
    print("LoRA模型状态")
    print("="*60)
    print(f"有LoRA模型: {status['has_lora']}")
    print(f"模型版本: v{status['model_version']}")
    print(f"训练数据量: {status['training_data_size']}")
    print()
    
    if status['has_lora']:
        # 测试推荐生成
        print("="*60)
        print("测试个性化推荐生成")
        print("="*60)
        
        options = [
            {"title": "考研", "final_score": 75.5, "risk_level": 0.35},
            {"title": "工作", "final_score": 82.3, "risk_level": 0.15},
            {"title": "创业", "final_score": 65.0, "risk_level": 0.65}
        ]
        
        # 模拟性格画像
        class MockProfile:
            decision_style = "rational"
            risk_preference = "risk_neutral"
            life_priority = "career_first"
        
        recommendation = analyzer.generate_personalized_recommendation(
            user_id=user_id,
            question="毕业后应该选择什么？",
            options=options,
            profile=MockProfile(),
            use_lora=True
        )
        
        print(f"\n个性化推荐:\n{recommendation}")
    else:
        print("⚠️ 用户还没有训练LoRA模型")
        print("💡 提示: 运行 test_lora_training.py 来训练模型")
