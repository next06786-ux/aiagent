"""
AI核心智能路由服务 - LLM驱动
使用大模型理解用户意图并提供功能跳转建议

优势：
- 🧠 智能理解复杂语义和隐含意图
- 🎯 准确识别用户真实需求
- 🔄 自适应学习用户表达习惯
"""
from typing import Dict, List, Optional, Any
import json


class IntentRouter:
    """LLM驱动的智能意图路由器"""
    
    def __init__(self):
        # 定义功能模块（供LLM参考）
        self.available_modules = {
            "knowledge_graph": {
                "name": "知识星图",
                "path": "/knowledge-graph",
                "description": "查看你的知识图谱，包括人际关系网络、教育升学规划、职业发展路径",
                "view_modes": {
                    "people": "人际关系视图 - 查看你的社交网络、家人朋友、同事导师等关系",
                    "education": "教育升学视图 - 查看学业成绩、目标学校、申请规划",
                    "career": "职业发展视图 - 查看技能树、岗位匹配、职业路径"
                },
                "use_cases": [
                    "想了解人际关系",
                    "查看社交网络",
                    "升学规划",
                    "职业发展分析",
                    "技能评估"
                ]
            },
            "decision": {
                "name": "决策推演",
                "path": "/decision",
                "description": "帮你分析重要决策，推演不同选择的结果和影响",
                "use_cases": [
                    "面临选择困难",
                    "需要决策建议",
                    "分析利弊",
                    "评估风险"
                ]
            },
            "parallel_life": {
                "name": "平行人生",
                "path": "/parallel-life",
                "description": "模拟不同选择下的人生轨迹，看看另一种可能",
                "use_cases": [
                    "想知道如果...会怎样",
                    "模拟未来",
                    "探索不同人生路径"
                ]
            },
            "emergence": {
                "name": "涌现洞察",
                "path": "/emergence-dashboard",
                "description": "查看你的整体状态、行为模式、趋势分析和深度洞察",
                "use_cases": [
                    "了解整体状态",
                    "查看数据分析",
                    "发现行为模式",
                    "获取洞察建议"
                ]
            },
            "data_collection": {
                "name": "数据采集",
                "path": "/data-collection",
                "description": "记录和采集你的日常数据、生活轨迹",
                "use_cases": [
                    "记录数据",
                    "添加信息",
                    "上传内容"
                ]
            },
            "career_simulation": {
                "name": "职业模拟",
                "path": "/career-simulation",
                "description": "模拟和评估职业发展路径，规划职业生涯",
                "use_cases": [
                    "职业规划",
                    "职业评估",
                    "职业选择"
                ]
            },
            "smart_schedule": {
                "name": "智能日程",
                "path": "/smart-schedule",
                "description": "智能日程推荐系统，基于你的习惯和生产力曲线推荐最佳时间安排",
                "use_cases": [
                    "安排日程",
                    "时间管理",
                    "任务规划",
                    "查看日程",
                    "什么时候做某事",
                    "时间安排",
                    "日程优化",
                    "生产力分析"
                ]
            }
        }
    
    def _build_llm_prompt(self, user_message: str) -> str:
        """构建LLM提示词"""
        modules_desc = []
        for module_id, info in self.available_modules.items():
            desc = f"**{info['name']}** ({module_id})\n"
            desc += f"  路径: {info['path']}\n"
            desc += f"  功能: {info['description']}\n"
            
            if "view_modes" in info:
                desc += f"  视图模式:\n"
                for mode, mode_desc in info["view_modes"].items():
                    desc += f"    - {mode}: {mode_desc}\n"
            
            desc += f"  适用场景: {', '.join(info['use_cases'])}\n"
            modules_desc.append(desc)
        
        prompt = f"""你是一个智能路由助手，负责分析用户消息并判断是否需要导航到特定功能模块。

可用的功能模块：
{chr(10).join(modules_desc)}

用户消息："{user_message}"

请分析用户的意图，判断是否需要导航到某个功能模块。

输出JSON格式（必须是有效的JSON）：
{{
  "has_navigation_intent": true/false,
  "suggested_routes": [
    {{
      "module": "模块ID",
      "confidence": 0.0-1.0,
      "reason": "推荐理由",
      "view_mode": "视图模式（仅knowledge_graph需要，可选people/signals/career）"
    }}
  ],
  "analysis": "简短的意图分析"
}}

规则：
1. 如果用户明确想查看某个功能，has_navigation_intent=true
2. 如果只是普通聊天/提问，has_navigation_intent=false
3. confidence表示推荐的置信度（0-1）
4. 最多推荐3个模块，按置信度排序
5. 对于知识星图，根据用户提到的内容判断view_mode：
   - 提到人际/关系/朋友/家人 → people
   - 提到升学/学校/申请/GPA → signals
   - 提到职业/工作/技能/求职 → career
6. 必须返回有效的JSON，不要有其他文字

只返回JSON，不要有任何其他内容。"""
        
        return prompt
    
    def analyze_intent(self, user_message: str) -> Dict[str, Any]:
        """
        使用LLM分析用户意图
        
        返回：
        {
            "has_navigation_intent": bool,
            "suggested_routes": [...],
            "primary_route": dict,
            "analysis": str
        }
        """
        try:
            from backend.llm.llm_service import get_llm_service
            
            llm = get_llm_service()
            if not llm or not llm.enabled:
                print("[IntentRouter] LLM不可用，返回空结果")
                return self._empty_result()
            
            # 构建提示词
            prompt = self._build_llm_prompt(user_message)
            
            # 调用LLM
            response = llm.chat(
                [{"role": "user", "content": prompt}],
                temperature=0.1,  # 低温度，更确定性
                response_format="json_object"
            )
            
            # 解析响应
            try:
                # 提取JSON（有时LLM会在JSON前后加文字）
                response = response.strip()
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    response = response[start:end]
                
                result = json.loads(response)
                
                # 补充模块信息
                for route in result.get("suggested_routes", []):
                    module_id = route.get("module")
                    if module_id in self.available_modules:
                        module_info = self.available_modules[module_id]
                        route["name"] = module_info["name"]
                        route["path"] = module_info["path"]
                        route["description"] = module_info["description"]
                
                # 设置主要推荐
                suggested_routes = result.get("suggested_routes", [])
                result["primary_route"] = suggested_routes[0] if suggested_routes else None
                
                return result
                
            except json.JSONDecodeError as e:
                print(f"[IntentRouter] JSON解析失败: {e}")
                print(f"[IntentRouter] 原始响应: {response[:200]}")
                return self._empty_result()
        
        except Exception as e:
            print(f"[IntentRouter] LLM调用失败: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_result()
    
    def _empty_result(self) -> Dict[str, Any]:
        """返回空结果"""
        return {
            "has_navigation_intent": False,
            "suggested_routes": [],
            "primary_route": None,
            "analysis": "无法分析意图"
        }
    
    def generate_navigation_prompt(self, intent_result: Dict[str, Any]) -> Optional[str]:
        """
        生成导航提示文本（纯文字，无emoji）
        
        返回格式化的提示文本，供AI回复使用
        """
        if not intent_result["has_navigation_intent"]:
            return None
        
        primary = intent_result["primary_route"]
        if not primary:
            return None
        
        # 生成主要推荐（纯文字）
        prompt = f"我注意到你可能想要查看【{primary['name']}】\n\n"
        prompt += f"{primary['description']}\n\n"
        
        if primary.get("view_mode"):
            view_mode_names = {
                "people": "人际关系视图",
                "education": "教育升学视图",
                "career": "职业发展视图"
            }
            prompt += f"建议查看：{view_mode_names.get(primary['view_mode'], primary['view_mode'])}\n\n"
        
        # 如果有其他建议
        other_routes = intent_result["suggested_routes"][1:]
        if other_routes:
            prompt += "其他相关功能：\n"
            for route in other_routes:
                prompt += f"- {route['name']}: {route['description']}\n"
        
        prompt += "\n是否需要我带你跳转过去？"
        
        return prompt


# 全局实例
intent_router = IntentRouter()
