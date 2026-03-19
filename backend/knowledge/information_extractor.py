"""
信息提取器
从原始数据（照片、传感器、对话）中提取结构化信息
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import re


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
        """从对话文本中提取信息"""
        metadata = metadata or {}
        
        extracted = {
            "entities": [],
            "events": [],
            "concepts": []
        }
        
        # 使用文本提取
        text_info = self._extract_from_text(conversation_text)
        extracted["entities"].extend(text_info["entities"])
        extracted["events"].extend(text_info["events"])
        extracted["concepts"].extend(text_info["concepts"])
        
        # 从元数据提取
        if metadata.get("intent"):
            intent = metadata["intent"]
            extracted["concepts"].append({
                "name": intent.get("type", "未知意图"),
                "type": "concept",
                "category": self._infer_category(intent.get("type", "")),
                "confidence": intent.get("confidence", 0.7)
            })
        
        return extracted
    
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
