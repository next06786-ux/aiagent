"""
信息提取器
从原始数据（照片、传感器、对话）中提取结构化信息
支持 LLM 智能提取 + 正则兜底
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import re
import json
import os


class InformationExtractor:
    """信息提取器"""
    
    def __init__(self):
        # 预定义的实体类型
        self.entity_types = {
            "person": ["人物", "朋友", "家人", "同事"],
            "location": ["地点", "位置", "场所"],
            "object": ["物体", "物品", "设备"],
            "organization": ["公司", "组织", "机构"]
        }
        
        # 预定义的事件类型
        self.event_types = {
            "activity": ["运动", "活动", "锻炼"],
            "meeting": ["会议", "聚会", "见面"],
            "work": ["工作", "任务", "项目"],
            "study": ["学习", "阅读", "研究"],
            "entertainment": ["娱乐", "游戏", "观影"]
        }
        
        # 生活领域映射
        self.domain_mapping = {
            "时间管理": ["工作", "任务", "日程", "计划"],
            "社交管理": ["朋友", "聚会", "社交", "交流"],
            "学习管理": ["学习", "阅读", "课程", "知识"],
            "情绪管理": ["心情", "情绪", "感受", "压力"],
            "财务管理": ["消费", "购物", "理财", "支出"],
            "健康管理": ["运动", "健康", "饮食", "睡眠"]
        }
    
    def extract_from_photo(self, photo_analysis: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """从照片分析结果中提取信息"""
        extracted = {
            "entities": [],
            "events": [],
            "concepts": []
        }
        
        # 从图像分析结果提取
        if "image_perception" in photo_analysis:
            img = photo_analysis["image_perception"]
            
            # 提取场景作为概念
            if img.get("scene"):
                scene = img["scene"]
                extracted["concepts"].append({
                    "name": scene.get("type", "未知场景"),
                    "type": "concept",
                    "category": self._infer_category(scene.get("type", "")),
                    "confidence": scene.get("confidence", 0.7),
                    "attributes": {
                        "scene_type": scene.get("type"),
                        "indoor_outdoor": scene.get("indoor_outdoor")
                    }
                })
            
            # 提取物体作为实体
            if img.get("objects"):
                for obj in img["objects"][:5]:  # 最多5个主要物体
                    extracted["entities"].append({
                        "name": obj,
                        "type": "entity",
                        "entity_type": "object",
                        "category": self._infer_category(obj),
                        "confidence": 0.8
                    })
            
            # 提取描述中的信息
            if img.get("description"):
                desc_info = self._extract_from_text(img["description"])
                extracted["entities"].extend(desc_info["entities"])
                extracted["events"].extend(desc_info["events"])
                extracted["concepts"].extend(desc_info["concepts"])
        
        # 从融合表示提取
        if "fused_representation" in photo_analysis:
            fused = photo_analysis["fused_representation"]
            
            # 提取用户状态作为概念
            if fused.get("user_state"):
                state = fused["user_state"]
                
                # 情感状态
                if state.get("sentiment"):
                    sentiment = state["sentiment"]
                    extracted["concepts"].append({
                        "name": f"{sentiment.get('type', '中性')}情绪",
                        "type": "concept",
                        "category": "情绪管理",
                        "confidence": sentiment.get("confidence", 0.7),
                        "attributes": {
                            "sentiment_type": sentiment.get("type"),
                            "score": sentiment.get("score")
                        }
                    })
                
                # 活动状态
                if state.get("activity"):
                    activity = state["activity"]
                    if activity.get("primary_activity"):
                        extracted["events"].append({
                            "name": activity["primary_activity"],
                            "type": "event",
                            "event_type": "activity",
                            "category": self._infer_category(activity["primary_activity"]),
                            "confidence": activity.get("confidence", 0.7)
                        })
        
        return extracted
    
    def extract_from_sensor(self, sensor_data: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """从传感器数据中提取信息"""
        extracted = {
            "entities": [],
            "events": [],
            "concepts": []
        }
        
        # 提取活动事件
        if "activity_state" in sensor_data:
            activity = sensor_data["activity_state"]
            if activity.get("primary_activity"):
                extracted["events"].append({
                    "name": activity["primary_activity"],
                    "type": "event",
                    "event_type": "activity",
                    "category": "健康管理",
                    "confidence": activity.get("confidence", 0.8),
                    "attributes": {
                        "intensity": activity.get("intensity"),
                        "duration": activity.get("duration")
                    }
                })
        
        # 提取健康指标作为概念
        if "health_indicators" in sensor_data:
            health = sensor_data["health_indicators"]
            
            if health.get("stress_level"):
                extracted["concepts"].append({
                    "name": f"{health['stress_level']}压力",
                    "type": "concept",
                    "category": "情绪管理",
                    "confidence": 0.7,
                    "attributes": {"stress_level": health["stress_level"]}
                })
        
        # 提取地点信息
        if "location" in sensor_data:
            location = sensor_data["location"]
            if isinstance(location, str) and location:
                extracted["entities"].append({
                    "name": location,
                    "type": "entity",
                    "entity_type": "location",
                    "category": self._infer_category(location),
                    "confidence": 0.9
                })
        
        return extracted
    
    def extract_from_conversation(self, conversation_text: str, metadata: Dict = None) -> Dict[str, List[Dict]]:
        """从对话文本中提取信息 - 提取所有类型的实体、事件、概念"""
        metadata = metadata or {}
        
        extracted = {
            "entities": [],
            "events": [],
            "concepts": [],
            "patterns": []
        }
        
        # 用 LLM 一次性提取所有信息
        llm_result = self._extract_all_information_llm(conversation_text)
        if llm_result:
            extracted["entities"].extend(llm_result.get("entities", []))
            extracted["events"].extend(llm_result.get("events", []))
            extracted["concepts"].extend(llm_result.get("concepts", []))
            extracted["patterns"].extend(llm_result.get("patterns", []))
        else:
            # LLM 失败时降级到正则提取（只提取人物）
            persons = self._extract_persons(conversation_text)
            extracted["entities"].extend(persons)
        
        return extracted
    
    def _extract_all_information_llm(self, text: str) -> Optional[Dict[str, List[Dict]]]:
        """用大模型一次性提取所有类型的信息（实体、事件、概念、模式）"""
        try:
            from openai import OpenAI
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                return None
            
            client = OpenAI(
                api_key=api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            
            prompt = f"""从以下对话中提取结构化信息，包括：实体、事件、概念、模式。

对话内容：
{text[:3000]}

请以JSON格式返回，包含以下字段：

{{
  "entities": [
    // 人物实体（Person）
    {{
      "name": "人物名（不能是代词）",
      "type": "Person",
      "category": "family/close_friends/colleagues/friends/weak_ties",
      "description": "一句话描述"
    }},
    // 职位实体（Job）
    {{
      "name": "职位名称",
      "type": "Job",
      "category": "position",
      "description": "职位描述",
      "attributes": {{"company": "公司名", "location": "地点", "salary": "薪资"}}
    }},
    // 学校实体（School）
    {{
      "name": "学校名称",
      "type": "School",
      "category": "university/college/high_school",
      "description": "学校描述",
      "attributes": {{"major": "专业", "level": "本科/硕士/博士", "location": "地点"}}
    }},
    // 组织/公司实体（Organization）
    {{
      "name": "组织名称",
      "type": "Organization",
      "category": "company/institution/ngo",
      "description": "组织描述",
      "attributes": {{"industry": "行业", "location": "地点"}}
    }},
    // 地点实体（Location）
    {{
      "name": "地点名称",
      "type": "Location",
      "category": "city/country/venue",
      "description": "地点描述"
    }}
  ],
  "events": [
    // 事件（Event）- 重要：任何活动、行为、发生的事情都是事件
    // 根据时态和性质分类：
    // - 已发生的活动 → type: Activity/Social/Study/Work（会转为EXPERIENCE记忆）
    // - 未来的安排 → type: Schedule（会转为SCHEDULE记忆）
    // - 已完成的任务 → type: TaskCompletion（会转为TASK_COMPLETION记忆）
    {{
      "name": "事件名称（如：散步、聚餐、面试、开会、学习）",
      "type": "Activity/Meeting/Interview/Party/Travel/Study/Work/Social/Schedule/TaskCompletion",
      "description": "事件描述",
      "participants": ["具体的人名，不要用'说话者'、'用户'、'我'等泛指词"],
      "location": "地点",
      "time": "时间（如：今天、昨天、明天14:00、下周一）",
      "duration": "持续时间（如果提到）",
      "status": "scheduled/completed/ongoing"
    }}
  ],
  "concepts": [
    // 技能（Skill）
    {{
      "name": "技能名称",
      "type": "Skill",
      "description": "技能描述",
      "level": "初级/中级/高级/专家"
    }},
    // 兴趣（Interest）
    {{
      "name": "兴趣名称",
      "type": "Interest",
      "description": "兴趣描述"
    }},
    // 目标（Goal）
    {{
      "name": "目标名称",
      "type": "Goal",
      "description": "目标描述"
    }},
    // 价值观（Value）
    {{
      "name": "价值观名称",
      "type": "Value",
      "description": "价值观描述"
    }}
  ],
  "patterns": [
    {{
      "name": "模式名称",
      "type": "Habit/Preference/DecisionPattern",
      "description": "模式描述",
      "frequency": "出现频率（数字）"
    }}
  ],
  "decisions": [
    // 决策（Decision）- 用户做出的选择或决定
    {{
      "name": "决策名称",
      "description": "决策内容",
      "options": ["选项1", "选项2"],
      "chosen": "选择的选项",
      "reasons": ["理由1", "理由2"]
    }}
  ]
}}

重要规则：
1. 【实体-人物】人物名不能是代词（"你"、"我"、"他"、"她"等），必须是具体的名字或称呼
2. 【事件-分类】根据时态和性质分类事件：
   - 已发生的活动（"去散步了"、"吃了饭"）→ type: Activity/Social/Study/Work，status: completed
   - 未来的安排（"明天面试"、"下周开会"）→ type: Schedule，status: scheduled
   - 已完成的任务（"完成了作业"、"做完了项目"）→ type: TaskCompletion，status: completed
3. 【事件-参与者】participants只包含具体的人名，不要包含"说话者"、"用户"、"我"等泛指词
4. 【事件-时间】如果提到时间词（今天、昨天、上周、明天、下周一、14:00等），要记录在time字段
5. 【决策】识别决策关键词：决定、选择、接受、拒绝、打算、计划等
6. 只提取对话中明确提到的信息，不要推测
7. 如果某个类别没有信息，返回空数组 []
8. 技能要具体（如"Python编程"而不是"编程"）
9. 模式要基于对话中的行为特征识别

示例1（已发生的活动）：
输入："我和小明今天去散步了"
输出：
{{
  "entities": [
    {{"name": "小明", "type": "Person", "category": "friends", "description": "一起散步的朋友"}}
  ],
  "events": [
    {{"name": "散步", "type": "Activity", "description": "和小明一起散步", "participants": ["小明"], "location": "", "time": "今天", "status": "completed"}}
  ],
  "concepts": [],
  "patterns": [],
  "decisions": []
}}

示例2（未来安排）：
输入："明天下午2点要去字节跳动面试Python工程师"
输出：
{{
  "entities": [
    {{"name": "字节跳动", "type": "Organization", "category": "company", "description": "面试公司"}},
    {{"name": "Python工程师", "type": "Job", "category": "position", "description": "面试职位"}}
  ],
  "events": [
    {{"name": "面试", "type": "Schedule", "description": "字节跳动Python工程师面试", "participants": ["说话者"], "location": "字节跳动", "time": "明天下午2点", "status": "scheduled"}}
  ],
  "concepts": [],
  "patterns": [],
  "decisions": []
}}

示例3（决策）：
输入："我决定接受阿里的offer，因为薪资更高而且团队氛围好"
输出：
{{
  "entities": [
    {{"name": "阿里", "type": "Organization", "category": "company", "description": "决定加入的公司"}}
  ],
  "events": [],
  "concepts": [],
  "patterns": [],
  "decisions": [
    {{"name": "接受阿里offer", "description": "决定接受阿里的工作邀请", "options": ["接受", "拒绝"], "chosen": "接受", "reasons": ["薪资更高", "团队氛围好"]}}
  ]
}}

示例4（任务完成）：
输入："我完成了Python项目的代码重构，性能提升了30%"
输出：
{{
  "entities": [],
  "events": [
    {{"name": "Python项目代码重构", "type": "TaskCompletion", "description": "完成代码重构，性能提升30%", "participants": ["说话者"], "location": "", "time": "", "status": "completed"}}
  ],
  "concepts": [
    {{"name": "Python", "type": "Skill", "description": "使用Python进行项目开发", "level": "中级"}}
  ],
  "patterns": [],
  "decisions": []
}}

只返回JSON，不要其他文字。"""

            response = client.chat.completions.create(
                model="qwen-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000
            )
            
            result_text = response.choices[0].message.content.strip()
            if result_text.startswith("```"):
                result_text = re.sub(r'^```\w*\n?', '', result_text)
                result_text = re.sub(r'\n?```$', '', result_text)
            
            data = json.loads(result_text)
            
            # 处理实体
            entities = []
            pronoun_blacklist = {
                '你', '我', '他', '她', '它', '对方', '那个人', '这个人', '某人', '别人',
                '自己', '人家', '大家', '我们', '他们', '她们', '你们', '咱们', '咱',
                '谁', '某某', '那位', '这位', '那人', '此人', '本人', '用户', 'AI', '助手'
            }
            
            # 别名映射表（标准化人物称呼）
            alias_map = {
                '父亲': '爸爸', '老爸': '爸爸', '爸': '爸爸', '爹': '爸爸',
                '母亲': '妈妈', '老妈': '妈妈', '妈': '妈妈', '娘': '妈妈',
                '老婆': '妻子', '媳妇': '妻子', '爱人': '妻子', '太太': '妻子',
                '老公': '丈夫', '先生': '丈夫',
                '闺女': '女儿', '女': '女儿',
                '儿': '儿子', '子': '儿子',
                '哥': '哥哥', '弟': '弟弟', '姐': '姐姐', '妹': '妹妹'
            }
            
            seen_names = set()  # 用于去重
            
            for entity in data.get("entities", []):
                name = entity.get('name', '').strip()
                entity_type = entity.get('type', 'Person')
                
                # 过滤代词
                if entity_type == 'Person' and (not name or name in pronoun_blacklist or len(name) < 2):
                    continue
                
                # 别名标准化（只对Person类型）
                if entity_type == 'Person' and name in alias_map:
                    original_name = name
                    name = alias_map[name]
                    print(f"  [别名合并] {original_name} → {name}")
                
                # 去重检查
                if name in seen_names:
                    print(f"  [去重] 跳过重复实体: {name}")
                    continue
                seen_names.add(name)
                
                entities.append({
                    "name": name,
                    "type": "entity",
                    "entity_type": entity_type,
                    "category": entity.get('category', 'unknown'),
                    "confidence": 0.9,
                    "attributes": {
                        "description": entity.get('description', ''),
                        "extracted_by": "llm",
                        **(entity.get('attributes', {}))
                    }
                })
            
            # 处理事件
            events = []
            for event in data.get("events", []):
                name = event.get('name', '').strip()
                # 放宽事件名称长度限制：至少2个字符即可（如"散步"、"聚餐"）
                if name and len(name) >= 2:
                    event_type = event.get('type', 'Activity')
                    status = event.get('status', 'completed')
                    
                    events.append({
                        "name": name,
                        "type": "event",
                        "event_type": event_type,
                        "category": event.get('category', 'general'),
                        "confidence": 0.85,
                        "attributes": {
                            "description": event.get('description', ''),
                            "participants": event.get('participants', []),
                            "location": event.get('location', ''),
                            "time": event.get('time', ''),
                            "duration": event.get('duration', ''),
                            "status": status,  # scheduled/completed/ongoing
                            "extracted_by": "llm"
                        }
                    })
            
            # 处理决策（新增）
            decisions = []
            for decision in data.get("decisions", []):
                name = decision.get('name', '').strip()
                if name and len(name) >= 2:
                    decisions.append({
                        "name": name,
                        "type": "decision",
                        "confidence": 0.9,
                        "attributes": {
                            "description": decision.get('description', ''),
                            "options": decision.get('options', []),
                            "chosen": decision.get('chosen', ''),
                            "reasons": decision.get('reasons', []),
                            "extracted_by": "llm"
                        }
                    })
            
            # 处理概念
            concepts = []
            for concept in data.get("concepts", []):
                name = concept.get('name', '').strip()
                if name and len(name) > 1:
                    concepts.append({
                        "name": name,
                        "type": "concept",
                        "concept_type": concept.get('type', 'Interest'),
                        "category": concept.get('category', 'general'),
                        "confidence": 0.85,
                        "attributes": {
                            "description": concept.get('description', ''),
                            "level": concept.get('level', ''),
                            "extracted_by": "llm"
                        }
                    })
            
            # 处理模式
            patterns = []
            for pattern in data.get("patterns", []):
                name = pattern.get('name', '').strip()
                if name and len(name) > 3:
                    patterns.append({
                        "name": name,
                        "type": "pattern",
                        "pattern_type": pattern.get('type', 'Habit'),
                        "confidence": 0.80,
                        "attributes": {
                            "description": pattern.get('description', ''),
                            "frequency": pattern.get('frequency', 1),
                            "extracted_by": "llm"
                        }
                    })
            
            if entities or events or concepts or patterns or decisions:
                print(f"  [LLM提取] 识别到:")
                print(f"    - 实体: {len(entities)} 个 (Person:{sum(1 for e in entities if e['entity_type']=='Person')}, Job:{sum(1 for e in entities if e['entity_type']=='Job')}, School:{sum(1 for e in entities if e['entity_type']=='School')}, Org:{sum(1 for e in entities if e['entity_type']=='Organization')}, Location:{sum(1 for e in entities if e['entity_type']=='Location')})")
                print(f"    - 事件: {len(events)} 个 (Activity:{sum(1 for e in events if e['event_type'] in ['Activity','Social','Study','Work'])}, Schedule:{sum(1 for e in events if e['event_type']=='Schedule')}, TaskCompletion:{sum(1 for e in events if e['event_type']=='TaskCompletion')})")
                print(f"    - 概念: {len(concepts)} 个 (Skill:{sum(1 for c in concepts if c['concept_type']=='Skill')}, Interest:{sum(1 for c in concepts if c['concept_type']=='Interest')}, Goal:{sum(1 for c in concepts if c['concept_type']=='Goal')}, Value:{sum(1 for c in concepts if c['concept_type']=='Value')})")
                print(f"    - 模式: {len(patterns)} 个")
                print(f"    - 决策: {len(decisions)} 个")
            
            return {
                "entities": entities,
                "events": events,
                "concepts": concepts,
                "patterns": patterns,
                "decisions": decisions  # 新增
            }
            
        except Exception as e:
            print(f"  [LLM提取] 全量提取失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_persons_and_stories_llm(self, text: str) -> Optional[Dict[str, List[Dict]]]:
        """用大模型同时提取人物和关联故事（已废弃，使用 _extract_all_information_llm）"""
        try:
            from openai import OpenAI
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                return None
            
            client = OpenAI(
                api_key=api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            
            prompt = f"""从以下对话中同时提取：1) 提到的人物  2) 与人物相关的故事/事件

重要规则：
1. 绝对不要把代词当作人物名字："你"、"我"、"他"、"她"、"对方"、"别人"、"自己"等不能作为人物名
2. 如果只用代词指代某人且无法确定具体是谁，跳过该人物
3. "父母"拆成"爸爸"和"妈妈"
4. 同一个人的不同称呼合并，用最具体的名字
5. 故事要关联到具体的人物，描述这个人在对话中提到的事情
6. 故事应该是有意义的信息，不是简单的"提到了某人"

对话内容：
{text[:2000]}

请以JSON格式返回：
{{
  "persons": [
    {{
      "name": "人物名（不能是代词）",
      "category": "family/close_friends/colleagues/friends/weak_ties",
      "description": "一句话描述",
      "stories": ["与此人相关的故事1", "与此人相关的故事2"]
    }}
  ]
}}

如果没有具体人物，返回 {{"persons": []}}
只返回JSON。"""

            response = client.chat.completions.create(
                model="qwen-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1500
            )
            
            result_text = response.choices[0].message.content.strip()
            if result_text.startswith("```"):
                result_text = re.sub(r'^```\w*\n?', '', result_text)
                result_text = re.sub(r'\n?```$', '', result_text)
            
            data = json.loads(result_text)
            persons_data = data.get("persons", [])
            
            if not isinstance(persons_data, list):
                return None
            
            pronoun_blacklist = {
                '你', '我', '他', '她', '它', '对方', '那个人', '这个人', '某人', '别人',
                '自己', '人家', '大家', '我们', '他们', '她们', '你们', '咱们', '咱',
                '谁', '某某', '那位', '这位', '那人', '此人', '本人', '用户', 'AI', '助手'
            }
            valid_categories = {'family', 'close_friends', 'colleagues', 'friends', 'weak_ties'}
            
            entities = []
            events = []
            seen = set()
            
            for p in persons_data:
                name = p.get('name', '').strip()
                if not name or name in pronoun_blacklist or len(name) < 2:
                    continue
                if name in seen:
                    continue
                seen.add(name)
                
                category = p.get('category', 'friends')
                if category not in valid_categories:
                    category = 'friends'
                
                stories = p.get('stories', [])
                
                entities.append({
                    "name": name,
                    "type": "entity",
                    "entity_type": "person",
                    "category": category,
                    "confidence": 0.9,
                    "attributes": {
                        "description": p.get('description', ''),
                        "extracted_by": "llm",
                        "stories": stories
                    }
                })
                
                # 把故事作为事件节点，关联到人物
                for story in stories:
                    if story and len(story) > 5:
                        events.append({
                            "name": story[:50],
                            "type": "event",
                            "category": category,
                            "confidence": 0.85,
                            "attributes": {
                                "related_person": name,
                                "full_story": story,
                                "extracted_by": "llm"
                            }
                        })
            
            if entities:
                print(f"  [LLM提取] 识别到 {len(entities)} 个人物, {len(events)} 个故事")
            
            return {"entities": entities, "events": events}
            
        except Exception as e:
            print(f"  [LLM提取] 人物+故事提取失败: {e}")
            return None
    
    def _extract_persons_llm(self, text: str) -> List[Dict]:
        """用大模型智能提取人物"""
        try:
            from openai import OpenAI
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                return []
            
            client = OpenAI(
                api_key=api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            
            prompt = f"""从以下对话中提取提到的所有人物。只提取人物，不要提取地点、事件等。

重要规则：
1. "父母"不是一个人，要拆成"爸爸"和"妈妈"两个人
2. 绝对不要把代词当作人物名字。以下词语绝对不能作为人物名字出现：
   "你"、"我"、"他"、"她"、"它"、"对方"、"那个人"、"这个人"、"某人"、"别人"、"自己"、"人家"、"大家"、"我们"、"他们"、"她们"、"你们"、"咱们"、"咱"
3. 如果对话中只用代词指代某人（如"她很好"），但上下文无法确定具体是谁，则跳过这个人，不要提取
4. 同一个人的不同称呼要合并（如"小雨"和"对方"是同一个人，只保留"小雨"）
5. "爸爸"和"父亲"是同一个人，只保留一个
6. 不要提取"我"、"用户"、"AI"、"助手"
7. 只提取有明确称呼或名字的人物

对话内容：
{text[:2000]}

请以JSON数组格式返回，每个人物包含：
- name: 人物称呼（用最具体的名字，如有真名用真名。绝对不能是代词）
- category: 关系类别，只能是以下之一：family（家人）、close_friends（好友）、colleagues（同事）、friends（朋友）、weak_ties（弱关系）
- description: 一句话描述这个人物在对话中的角色或提到的事情
- aliases: 这个人在对话中的其他称呼（数组，如 ["对方", "她"]）

如果对话中没有提到任何具体人物（只有代词），返回空数组 []
只返回JSON，不要其他文字。"""

            response = client.chat.completions.create(
                model="qwen-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000
            )
            
            result_text = response.choices[0].message.content.strip()
            # 清理可能的 markdown 包裹
            if result_text.startswith("```"):
                result_text = re.sub(r'^```\w*\n?', '', result_text)
                result_text = re.sub(r'\n?```$', '', result_text)
            
            persons_data = json.loads(result_text)
            
            if not isinstance(persons_data, list):
                return []
            
            persons = []
            seen = set()
            valid_categories = {'family', 'close_friends', 'colleagues', 'friends', 'weak_ties'}
            # 代词黑名单 - 绝对不能作为人物名字
            pronoun_blacklist = {
                '你', '我', '他', '她', '它', '对方', '那个人', '这个人', '某人', '别人',
                '自己', '人家', '大家', '我们', '他们', '她们', '你们', '咱们', '咱',
                '谁', '某某', '那位', '这位', '那人', '此人', '本人', '用户', 'AI', '助手',
                '对象', '那边', '这边', '人', '朋友们', '同学们', '家人们'
            }
            
            # 代词/泛称黑名单 — 不应作为独立人物
            PRONOUN_BLACKLIST = pronoun_blacklist  # 使用上面定义的完整黑名单
            
            # 别名合并映射
            ALIAS_MAP = {
                '父亲': '爸爸', '老爸': '爸爸', '爸': '爸爸',
                '母亲': '妈妈', '老妈': '妈妈', '妈': '妈妈',
                '老婆': '妻子', '媳妇': '妻子', '爱人': '妻子',
                '老公': '丈夫',
                '闺女': '女儿',
            }
            
            for p in persons_data:
                name = p.get('name', '').strip()
                if not name or name in PRONOUN_BLACKLIST:
                    continue
                # 别名标准化
                name = ALIAS_MAP.get(name, name)
                if name in seen:
                    continue
                seen.add(name)
                # 也把 aliases 里的名字加入 seen 防止重复
                aliases = p.get('aliases', [])
                for alias in aliases:
                    seen.add(alias.strip())
                category = p.get('category', 'friends')
                if category not in valid_categories:
                    category = 'friends'
                
                persons.append({
                    "name": name,
                    "type": "entity",
                    "entity_type": "person",
                    "category": category,
                    "confidence": 0.9,
                    "attributes": {
                        "description": p.get('description', ''),
                        "extracted_by": "llm"
                    }
                })
            
            if persons:
                print(f"  [LLM提取] 识别到 {len(persons)} 个人物: {[p['name'] for p in persons]}")
            return persons
            
        except Exception as e:
            print(f"  [LLM提取] 失败，降级到正则: {e}")
            return []
    
    def _extract_persons(self, text: str) -> List[Dict]:
        """从文本中提取人物"""
        persons = []
        seen_names = set()
        
        if not text:
            return persons

        # 代词黑名单
        pronoun_blacklist = {
            '你', '我', '他', '她', '它', '对方', '那个人', '这个人', '某人', '别人',
            '自己', '人家', '大家', '我们', '他们', '她们', '你们', '咱们', '咱',
            '谁', '某某', '那位', '这位', '那人', '此人', '本人', '用户', 'AI', '助手',
            '对象', '那边', '这边', '人', '朋友们', '同学们', '家人们'
        }

        # 预处理：把"父母"拆成"爸爸"和"妈妈"
        text_processed = text.replace('父母', '爸爸和妈妈').replace('爸妈', '爸爸和妈妈')
        
        # 1. 称谓模式匹配 - 提取带称谓的人物
        relation_patterns = {
            # 家人
            'family': [
                (r'(?:我|我的)(爸爸|爸|父亲|老爸)', 'family'),
                (r'(?:我|我的)(妈妈|妈|母亲|老妈)', 'family'),
                (r'(?:我|我的)(哥哥|哥|弟弟|弟|姐姐|姐|妹妹|妹)', 'family'),
                (r'(?:我|我的)(爷爷|奶奶|外公|外婆|姥姥|姥爷)', 'family'),
                (r'(?:我|我的)(老婆|老公|妻子|丈夫|媳妇|爱人)', 'family'),
                (r'(?:我|我的)(儿子|女儿|孩子|宝宝|闺女)', 'family'),
                (r'(?:我|我的)(叔叔|阿姨|舅舅|舅妈|姑姑|姑父|伯伯|婶婶)', 'family'),
            ],
            # 好友
            'close_friends': [
                (r'(?:我|我的)(?:好朋友|闺蜜|死党|铁哥们|发小|兄弟)(\S{2,4})', 'close_friends'),
                (r'(?:好朋友|闺蜜|死党|铁哥们|发小)(\S{2,4})', 'close_friends'),
            ],
            # 同事
            'colleagues': [
                (r'(?:我|我们)(?:同事|领导|老板|上司|经理|主管|组长|总监)(\S{2,4})', 'colleagues'),
                (r'(?:同事|领导|老板|上司|经理|主管|组长|总监)(\S{2,4})', 'colleagues'),
            ],
            # 朋友
            'friends': [
                (r'(?:我|我的)(?:朋友|同学|室友|舍友|同桌|学长|学姐|学弟|学妹)(\S{2,4})', 'friends'),
                (r'(?:朋友|同学|室友|舍友|同桌)(\S{2,4})', 'friends'),
            ],
        }
        
        for category, patterns in relation_patterns.items():
            for pattern, cat in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    name = match.strip()
                    if name and len(name) >= 1 and name not in seen_names:
                        # 称谓本身也可以作为名字（如"爸爸"）
                        seen_names.add(name)
                        persons.append({
                            "name": name,
                            "type": "entity",
                            "entity_type": "person",
                            "category": category,
                            "confidence": 0.85
                        })
        
        # 2. 直接姓名模式 - 中文姓名（姓+名，2-4字）
        # 常见姓氏
        common_surnames = '赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳酆鲍史唐费廉岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董梁杜阮蓝闵席季麻强贾路娄危江童颜郭梅盛林刁钟徐邱骆高夏蔡田樊胡凌霍虞万支柯昝管卢莫经房裘缪干解应宗丁宣贲邓郁单杭洪包诸左石崔吉钮龚程嵇邢滑裴陆荣翁荀羊於惠甄曲家封芮羿储靳汲邴糜松井段富巫乌焦巴弓牧隗山谷车侯宓蓬全郗班仰秋仲伊宫宁仇栾暴甘钭厉戎祖武符刘景詹束龙叶幸司韶郜黎蓟薄印宿白怀蒲邰从鄂索咸籍赖卓蔺屠蒙池乔阴鬱胥能苍双闻莘党翟谭贡劳逄姬申扶堵冉宰郦雍郤璩桑桂濮牛寿通边扈燕冀郏浦尚农温别庄晏柴瞿阎充慕连茹习宦艾鱼容向古易慎戈廖庾终暨居衡步都耿满弘匡国文寇广禄阙东欧殳沃利蔚越夔隆师巩厍聂晁勾敖融冷訾辛阚那简饶空曾母沙乜养鞠须丰巢关蒯相查后荆红游竺权逯盖益桓公'
        name_pattern = rf'([{common_surnames}]\S{{1,3}})(?:说|告诉|问|跟|和|与|给|找|约|见|叫|是|在)'
        matches = re.findall(name_pattern, text)
        for match in matches:
            name = match.strip()
            if name and 2 <= len(name) <= 4 and name not in seen_names:
                # 过滤掉明显不是人名的
                skip_words = {'我们', '他们', '她们', '你们', '大家', '自己', '别人', '对方', '这个', '那个', '什么', '怎么', '为什么', '可以', '不能', '应该', '已经'}
                if name not in skip_words and name not in pronoun_blacklist:
                    seen_names.add(name)
                    persons.append({
                        "name": name,
                        "type": "entity",
                        "entity_type": "person",
                        "category": "friends",
                        "confidence": 0.7
                    })
        
        # 3. "叫XX"模式
        called_pattern = r'(?:叫|名叫|叫做|名字是)(\S{2,4})'
        matches = re.findall(called_pattern, text)
        for match in matches:
            name = match.strip()
            if name and len(name) >= 2 and name not in seen_names and name not in pronoun_blacklist:
                seen_names.add(name)
                seen_names.add(name)
                persons.append({
                    "name": name,
                    "type": "entity",
                    "entity_type": "person",
                    "category": "friends",
                    "confidence": 0.75
                })
        
        return persons
    
    def _extract_from_text(self, text: str) -> Dict[str, List[Dict]]:
        """从文本中提取信息（简化版NLP）"""
        extracted = {
            "entities": [],
            "events": [],
            "concepts": []
        }
        
        if not text:
            return extracted
        
        text_lower = text.lower()
        
        # 提取地点（简单模式匹配）
        location_patterns = [
            r'在(.{2,10}?)[，。、]',
            r'去(.{2,10}?)[，。、]',
            r'到(.{2,10}?)[，。、]'
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) >= 2:
                    extracted["entities"].append({
                        "name": match,
                        "type": "entity",
                        "entity_type": "location",
                        "category": self._infer_category(match),
                        "confidence": 0.6
                    })
        
        # 提取活动事件
        for event_type, keywords in self.event_types.items():
            for keyword in keywords:
                if keyword in text_lower:
                    extracted["events"].append({
                        "name": keyword,
                        "type": "event",
                        "event_type": event_type,
                        "category": self._infer_category(keyword),
                        "confidence": 0.7
                    })
                    break
        
        # 【增强】提取更多事件关键词
        activity_keywords = {
            "完成": "work",
            "finish": "work",
            "做": "work",
            "学习": "study",
            "study": "study",
            "阅读": "study",
            "read": "study",
            "作业": "study",
            "homework": "study",
            "跑步": "activity",
            "run": "activity",
            "运动": "activity",
            "exercise": "activity",
            "工作": "work",
            "work": "work"
        }
        
        for keyword, event_type in activity_keywords.items():
            if keyword in text_lower:
                extracted["events"].append({
                    "name": keyword,
                    "type": "event",
                    "event_type": event_type,
                    "category": self._infer_category(keyword),
                    "confidence": 0.75
                })
        
        # 提取概念
        for domain, keywords in self.domain_mapping.items():
            for keyword in keywords:
                if keyword in text_lower:
                    extracted["concepts"].append({
                        "name": keyword,
                        "type": "concept",
                        "category": domain,
                        "confidence": 0.6
                    })
                    break
        
        # 【增强】提取情绪概念
        emotion_keywords = {
            "开心": "positive",
            "高兴": "positive",
            "快乐": "positive",
            "成就感": "positive",
            "满足": "positive",
            "happy": "positive",
            "累": "negative",
            "疲惫": "negative",
            "压力": "negative",
            "tired": "negative",
            "爽": "positive",
            "舒服": "positive"
        }
        
        for keyword, emotion_type in emotion_keywords.items():
            if keyword in text_lower:
                extracted["concepts"].append({
                    "name": f"{emotion_type}情绪",
                    "type": "concept",
                    "category": "情绪管理",
                    "confidence": 0.7,
                    "attributes": {
                        "emotion_keyword": keyword,
                        "emotion_type": emotion_type
                    }
                })
        
        return extracted
    
    def _infer_category(self, text: str) -> str:
        """推断信息所属的生活领域"""
        text_lower = text.lower()
        
        for domain, keywords in self.domain_mapping.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return domain
        
        # 默认分类
        if any(k in text_lower for k in ["运动", "健康", "锻炼", "跑步"]):
            return "健康管理"
        elif any(k in text_lower for k in ["工作", "会议", "任务"]):
            return "时间管理"
        elif any(k in text_lower for k in ["朋友", "聚会", "社交"]):
            return "社交管理"
        elif any(k in text_lower for k in ["学习", "阅读", "课程"]):
            return "学习管理"
        elif any(k in text_lower for k in ["心情", "情绪", "感受"]):
            return "情绪管理"
        elif any(k in text_lower for k in ["消费", "购物", "支出"]):
            return "财务管理"
        
        return "其他"
    
    def infer_relationships(
        self,
        entities: List[Dict],
        events: List[Dict],
        concepts: List[Dict],
        context: Dict = None
    ) -> List[Dict]:
        """推理信息之间的关系"""
        relationships = []
        context = context or {}
        
        # 事件-地点关系
        for event in events:
            for entity in entities:
                if entity.get("entity_type") == "location":
                    relationships.append({
                        "source": event["name"],
                        "target": entity["name"],
                        "type": "OCCURS_AT",
                        "confidence": min(event["confidence"], entity["confidence"])
                    })
        
        # 事件-物体关系
        for event in events:
            for entity in entities:
                if entity.get("entity_type") == "object":
                    # 如果物体和事件相关
                    if self._is_related(event["name"], entity["name"]):
                        relationships.append({
                            "source": event["name"],
                            "target": entity["name"],
                            "type": "REQUIRES",
                            "confidence": 0.6
                        })
        
        # 概念-事件关系
        for concept in concepts:
            for event in events:
                if concept["category"] == event.get("category"):
                    relationships.append({
                        "source": concept["name"],
                        "target": event["name"],
                        "type": "INCLUDES",
                        "confidence": 0.7
                    })
        
        # 时序关系（如果有时间信息）
        if context.get("timestamp"):
            # 可以根据时间推理BEFORE/AFTER关系
            pass
        
        return relationships
    
    def _is_related(self, event_name: str, entity_name: str) -> bool:
        """判断事件和实体是否相关"""
        # 简单的关联规则
        relations = {
            "跑步": ["跑鞋", "运动服", "手表"],
            "学习": ["书籍", "笔记本", "电脑"],
            "工作": ["电脑", "文件", "笔"],
            "做饭": ["锅", "食材", "厨具"]
        }
        
        for event_key, related_entities in relations.items():
            if event_key in event_name.lower():
                if any(e in entity_name.lower() for e in related_entities):
                    return True
        
        return False
    
    def merge_duplicate_information(self, info_list: List[Dict]) -> List[Dict]:
        """合并重复的信息，提高置信度"""
        merged = {}
        
        for info in info_list:
            key = (info["name"], info["type"])
            
            if key in merged:
                # 已存在，更新置信度（取最大值）
                merged[key]["confidence"] = max(
                    merged[key]["confidence"],
                    info["confidence"]
                )
                # 合并属性
                if "attributes" in info:
                    if "attributes" not in merged[key]:
                        merged[key]["attributes"] = {}
                    merged[key]["attributes"].update(info["attributes"])
            else:
                # 新信息
                merged[key] = info.copy()
        
        return list(merged.values())
