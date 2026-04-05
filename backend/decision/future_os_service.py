from __future__ import annotations

import json
import os
import re
import uuid
import time
from collections import defaultdict
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

from backend.database.config import DatabaseConfig
from backend.database.models import Database
from backend.knowledge.information_knowledge_graph import InformationKnowledgeGraph


# ==================== 三级缓存架构 ====================
# L1: 内存LRU缓存（最快，纳秒级）
# L2: Redis缓存（快，毫秒级）
# L3: 文件持久化（冷启动恢复）

class MemoryCache:
    """L1内存缓存 - 最快的缓存层"""
    def __init__(self, maxsize=100, ttl_seconds=300):
        self._cache = {}
        self._timestamps = {}
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存，检查TTL"""
        if key not in self._cache:
            self.misses += 1
            return None
        
        # 检查是否过期
        if time.time() - self._timestamps[key] > self.ttl_seconds:
            del self._cache[key]
            del self._timestamps[key]
            self.misses += 1
            return None
        
        self.hits += 1
        return self._cache[key]
    
    def set(self, key: str, value: Any):
        """设置缓存，LRU淘汰"""
        # 如果缓存满了，删除最老的
        if len(self._cache) >= self.maxsize:
            oldest_key = min(self._timestamps.keys(), key=lambda k: self._timestamps[k])
            del self._cache[oldest_key]
            del self._timestamps[oldest_key]
        
        self._cache[key] = value
        self._timestamps[key] = time.time()
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._timestamps.clear()
    
    def stats(self) -> Dict[str, Any]:
        """缓存统计"""
        hit_rate = self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0
        return {
            "size": len(self._cache),
            "maxsize": self.maxsize,
            "ttl_seconds": self.ttl_seconds,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2%}"
        }

# 全局L1缓存实例
_l1_cache = MemoryCache(maxsize=100, ttl_seconds=300)  # 5分钟TTL


# ── 全局连接池 ─────────────────────────────────────────
_redis_client = None
_neo4j_connections = {}

def _get_redis_client():
    """获取全局Redis客户端（连接池）"""
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            _redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=int(os.getenv("REDIS_DB", 0)),
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                max_connections=50  # 连接池
            )
            # 测试连接
            _redis_client.ping()
            print("[KG] Redis连接池已初始化")
        except Exception as e:
            print(f"[KG] Redis连接失败: {e}")
            _redis_client = None
    return _redis_client




# ── LLM 智能节点分流 ─────────────────────────────────────────
# 持久化缓存文件路径
_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".node_classify_cache.json")

def _load_cache() -> Dict[str, str]:
    try:
        if os.path.exists(_CACHE_FILE):
            with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_cache(cache: Dict[str, str]) -> None:
    try:
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[KG] 缓存保存失败: {e}")

# 启动时从文件加载缓存
_llm_classify_cache: Dict[str, str] = _load_cache()
print(f"[KG] 节点分类缓存已加载: {len(_llm_classify_cache)} 条")


def _llm_classify_nodes(nodes: List[Dict[str, Any]], async_mode: bool = True) -> Dict[str, str]:
    """
    用 LLM 批量判断节点属于哪个视图：person（人物）/ signal（信号）/ career（职业）
    
    智能增量分类：
    - 已缓存的节点：立即返回
    - 未缓存的节点：
      - async_mode=True: 不返回（后台异步LLM分类，完成后自动显示）
      - async_mode=False: 同步等待LLM分类（阻塞）
    
    Args:
        nodes: 节点列表
        async_mode: 是否异步模式（默认True，新节点后台分类）
    
    Returns:
        {node_id: "person" | "signal" | "career"}  # 只包含已缓存的节点
    """
    result: Dict[str, str] = {}
    uncached: List[Dict[str, Any]] = []

    # 1. 从L3文件缓存获取已分类的节点
    for node in nodes:
        key = f"{node.get('name','')}|{node.get('type','')}|{node.get('category','')}"
        if key in _llm_classify_cache:
            result[node["id"]] = _llm_classify_cache[key]
        else:
            uncached.append(node)

    # 2. 如果没有新节点，直接返回
    if not uncached:
        print(f"[KG] 所有 {len(nodes)} 个节点已缓存，无需分类")
        return result
    
    print(f"[KG] 发现 {len(uncached)} 个新节点需要分类（已缓存 {len(result)} 个）")
    
    # 3. 异步模式：只返回已缓存的，新节点后台LLM分类
    if async_mode:
        # 启动后台异步任务进行精确分类
        print(f"[KG] 后台异步分类已启动，新节点将在分类完成后显示")
        import asyncio
        asyncio.create_task(_classify_nodes_background(uncached))
        
        # 只返回已缓存的节点分类结果
        return result
    
    # 4. 同步模式：立即LLM分类（阻塞）
    return _classify_nodes_sync(uncached, result)


async def _classify_nodes_background(uncached: List[Dict[str, Any]]):
    """后台异步精确分类节点"""
    try:
        print(f"[KG] 后台任务开始：精确分类 {len(uncached)} 个节点")
        await asyncio.sleep(1)  # 延迟1秒，让主请求先返回
        
        # 调用同步分类逻辑
        _classify_nodes_sync(uncached, {})
        
        print(f"[KG] 后台分类完成：{len(uncached)} 个节点已更新缓存")
        print(f"[KG] 提示：刷新页面或重新打开视图即可看到新节点")
        
        # TODO: 通过WebSocket推送更新通知前端自动刷新
        # await notify_frontend_update(user_id, "knowledge_graph_updated")
        
    except Exception as e:
        print(f"[KG] 后台分类失败: {e}")
        import traceback
        traceback.print_exc()


def _classify_nodes_sync(uncached: List[Dict[str, Any]], result: Dict[str, str]) -> Dict[str, str]:
    """同步LLM分类节点（阻塞）"""
    if not uncached:
        return result

    try:
        from backend.llm.llm_service import get_llm_service
        llm = get_llm_service()
        if not llm or not llm.enabled:
            print(f"[KG] LLM未启用，新节点将标记为signal")
            for node in uncached:
                result[node["id"]] = "signal"
                key = f"{node.get('name','')}|{node.get('type','')}|{node.get('category','')}"
                _llm_classify_cache[key] = "signal"
            _save_cache(_llm_classify_cache)
            return result

        # 分批处理，每批 20 个，避免超时
        BATCH = 20
        total_batches = (len(uncached) + BATCH - 1) // BATCH
        
        for batch_start in range(0, len(uncached), BATCH):
            batch = uncached[batch_start: batch_start + BATCH]
            batch_num = batch_start // BATCH + 1
            
            items = "\n".join(
                f'{i+1}. 名称="{n.get("name","")}" 类型="{n.get("type","")}" 分类="{n.get("category","")}"'
                for i, n in enumerate(batch)
            )
            prompt = f"""判断每个节点属于哪个类别：
1. 人物(person)：真实具体的人（家人/朋友/同事/导师等）
2. 职业(career)：技能/岗位/项目/工作/公司等职业相关
3. 信号(signal)：概念/事件/习惯/目标/情绪等其他内容

{items}

只返回JSON，格式：{{"results":[{{"id":1,"label":"人物"}},{{"id":2,"label":"职业"}},{{"id":3,"label":"信号"}}]}}"""

            try:
                print(f"[KG] 批次 {batch_num}/{total_batches} 调用LLM...")
                start_time = time.time()
                
                response = llm.chat(
                    [{"role": "user", "content": prompt}],
                    temperature=0.0,
                    response_format="json_object",
                )
                
                elapsed = time.time() - start_time
                print(f"[KG] 批次 {batch_num}/{total_batches} 完成，耗时 {elapsed:.1f}秒")
                
            except Exception as e:
                print(f"[KG] 批次 {batch_num} LLM 调用失败: {e}，该批标记为 signal")
                for node in batch:
                    result[node["id"]] = "signal"
                    key = f"{node.get('name','')}|{node.get('type','')}|{node.get('category','')}"
                    _llm_classify_cache[key] = "signal"
                continue

            if not response or not response.strip():
                for node in batch:
                    result[node["id"]] = "signal"
                continue

            try:
                # 提取 JSON
                raw = response.strip()
                start = raw.find('{')
                end = raw.rfind('}') + 1
                if start >= 0 and end > start:
                    raw = raw[start:end]
                parsed = json.loads(raw)
                id_to_label = {item["id"]: item["label"] for item in parsed.get("results", [])}
            except Exception as e:
                print(f"[KG] JSON 解析失败: {e}，响应: {response[:100]}")
                for node in batch:
                    result[node["id"]] = "signal"
                continue

            # 映射标签到类别
            for i, node in enumerate(batch):
                label = id_to_label.get(i + 1, "信号")
                if label in ("人物", "person", "Person"):
                    role = "person"
                elif label in ("职业", "career", "Career"):
                    role = "career"
                else:
                    role = "signal"
                
                result[node["id"]] = role
                key = f"{node.get('name','')}|{node.get('type','')}|{node.get('category','')}"
                _llm_classify_cache[key] = role

            # 每批完成后持久化缓存
            _save_cache(_llm_classify_cache)

    except Exception as e:
        print(f"[KG] LLM 分流整体失败: {e}")
        import traceback
        traceback.print_exc()
        for node in uncached:
            if node["id"] not in result:
                result[node["id"]] = "signal"

    return result


DEFAULT_PROFILE = {
    "risk_tolerance": 0.48,
    "delay_discount": 0.52,
    "social_dependency": 0.50,
    "execution_stability": 0.46,
    "growth_bias": 0.54,
    "loss_aversion": 0.58,
    "ambiguity_tolerance": 0.44,
}

BRANCH_LIBRARY = [
    {
        "branch_strategy": "保守稳定线",
        "agent_id": "branch_stability",
        "description": "优先稳住现金流、节奏和可执行性，再寻找下一步窗口。",
        "deltas": [
            {"finance": 0.12, "stress": -0.03, "confidence": 0.02, "growth": 0.04},
            {"social": 0.05, "confidence": 0.05, "stress": -0.02},
            {"growth": 0.08, "finance": 0.05, "stress": -0.04},
            {"confidence": 0.07, "social": 0.03, "health": 0.04},
        ],
        "keywords": ["稳定", "工作", "保守", "安全", "收入", "稳妥"],
    },
    {
        "branch_strategy": "成长优先线",
        "agent_id": "branch_growth",
        "description": "接受短期波动，把主要资源投向长期能力和跃迁空间。",
        "deltas": [
            {"growth": 0.16, "finance": -0.08, "stress": 0.04, "confidence": 0.05},
            {"growth": 0.12, "social": 0.04, "confidence": 0.06},
            {"growth": 0.10, "finance": -0.03, "health": -0.02, "confidence": 0.07},
            {"growth": 0.09, "confidence": 0.09, "finance": 0.03},
        ],
        "keywords": ["成长", "学习", "深造", "能力", "转型", "突破"],
    },
    {
        "branch_strategy": "关系优先线",
        "agent_id": "branch_relationship",
        "description": "优先降低人与人之间的摩擦，把关系稳定度放在首位。",
        "deltas": [
            {"social": 0.14, "emotion": 0.08, "finance": -0.03},
            {"social": 0.11, "stress": -0.04, "confidence": 0.03},
            {"social": 0.10, "emotion": 0.06, "growth": 0.03},
            {"social": 0.08, "confidence": 0.05, "health": 0.02},
        ],
        "keywords": ["关系", "家人", "朋友", "伴侣", "社交", "沟通"],
    },
    {
        "branch_strategy": "探索试错线",
        "agent_id": "branch_explore",
        "description": "保留安全垫后小步试错，用实验换取更清晰的方向。",
        "deltas": [
            {"growth": 0.10, "ambiguity": 0.08, "stress": 0.03, "finance": -0.04},
            {"growth": 0.08, "confidence": 0.05, "social": 0.03},
            {"growth": 0.09, "finance": 0.02, "stress": -0.01},
            {"confidence": 0.07, "finance": 0.03, "emotion": 0.04},
        ],
        "keywords": ["尝试", "探索", "副业", "创业", "实验", "转行"],
    },
    {
        "branch_strategy": "恢复缓冲线",
        "agent_id": "branch_recovery",
        "description": "先修复压力、健康和执行力，再决定是否切换路径。",
        "deltas": [
            {"health": 0.12, "stress": -0.10, "emotion": 0.07},
            {"health": 0.08, "confidence": 0.03, "finance": 0.02},
            {"emotion": 0.06, "stress": -0.06, "social": 0.03},
            {"confidence": 0.06, "growth": 0.04, "health": 0.06},
        ],
        "keywords": ["休息", "恢复", "焦虑", "压力", "健康", "缓冲"],
    },
]


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def avg(values: List[float], fallback: float = 0.0) -> float:
    clean = [float(item) for item in values if isinstance(item, (int, float))]
    return sum(clean) / len(clean) if clean else fallback


class FutureOSService:
    def __init__(self) -> None:
        self._db = Database(DatabaseConfig.get_database_url())

    def _db_session(self):
        return self._db.get_session()

    def ensure_tables(self) -> None:
        session = self._db_session()
        try:
            session.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS future_os_profiles (
                        user_id VARCHAR(100) PRIMARY KEY,
                        profile_json LONGTEXT NOT NULL,
                        updated_at VARCHAR(50) NOT NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
            )
            session.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS future_os_parallel_runs (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        scenario_id VARCHAR(100) NOT NULL,
                        simulation_id VARCHAR(100),
                        branch_id VARCHAR(100),
                        user_id VARCHAR(100) NOT NULL,
                        payload_json LONGTEXT NOT NULL,
                        created_at VARCHAR(50) NOT NULL,
                        INDEX idx_future_os_parallel_runs_user (user_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
            )
            session.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS future_os_branch_scenarios (
                        scenario_id VARCHAR(100) PRIMARY KEY,
                        simulation_id VARCHAR(100),
                        branch_id VARCHAR(100),
                        user_id VARCHAR(100) NOT NULL,
                        payload_json LONGTEXT NOT NULL,
                        created_at VARCHAR(50) NOT NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
            )
            session.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS decision_records (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        simulation_id VARCHAR(100) UNIQUE NOT NULL,
                        user_id VARCHAR(100) NOT NULL,
                        question TEXT,
                        options_count INT DEFAULT 0,
                        recommendation TEXT,
                        timeline_data LONGTEXT,
                        created_at VARCHAR(50),
                        INDEX idx_decision_records_user (user_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
            )
            session.commit()
        finally:
            session.close()

    def _load_graph_export(self, user_id: str) -> Dict[str, Any]:
        """加载知识图谱导出数据，带Redis缓存"""
        cache_key = f"kg_export:{user_id}"
        
        # 1. 尝试从Redis缓存读取（使用全局连接池）
        try:
            redis_client = _get_redis_client()
            if redis_client:
                cached = redis_client.get(cache_key)
                if cached:
                    print(f"[Cache Hit] 从Redis加载知识图谱: {user_id}")
                    return json.loads(cached)
        except Exception as e:
            print(f"[Cache Miss] Redis读取失败: {e}")
        
        # 2. 缓存未命中，从Neo4j加载
        try:
            info_kg = InformationKnowledgeGraph(user_id)
            try:
                export_data = info_kg.export()
                
                # 3. 写入Redis缓存，TTL 5分钟（使用全局连接池）
                try:
                    redis_client = _get_redis_client()
                    if redis_client:
                        redis_client.setex(
                            cache_key,
                            300,  # 5分钟过期
                            json.dumps(export_data, ensure_ascii=False)
                        )
                        print(f"[Cache Write] 知识图谱已缓存: {user_id}")
                except Exception as e:
                    print(f"[Cache Write Failed] {e}")
                
                return export_data
            finally:
                info_kg.close()
        except Exception as e:
            print(f"[Load Failed] 知识图谱加载失败: {e}")
            return {"information": [], "sources": [], "relationships": []}

    def _node_importance(
        self,
        node: Dict[str, Any],
        degree: int,
        question: str,
        view_mode: str,
    ) -> float:
        tokens = [token for token in re.split(r"[\s,，。；、/]+", question) if token]
        name = str(node.get("name", ""))
        confidence = float(node.get("confidence", 0.65) or 0.65)
        mention_count = float(node.get("mention_count", 1) or 1)
        match_bonus = 0.0
        for token in tokens:
            if token in name:
                match_bonus += 0.12
        category_bonus = 0.0
        return round(
            clamp(0.28 + confidence * 0.24 + min(0.18, degree * 0.03) + min(0.18, mention_count * 0.03) + match_bonus + category_bonus),
            3,
        )

    def _safe_profile_snapshot(self, user_id: str) -> Dict[str, float]:
        try:
            return self._derive_profile_from_history(user_id)
        except Exception:
            return dict(DEFAULT_PROFILE)

    def _guess_focus_domain(self, question: str) -> str:
        text = question or ""
        if re.search(r"(工作|职业|公司|面试|跳槽|创业|项目|offer|团队)", text, re.IGNORECASE):
            return "career"
        if re.search(r"(感情|关系|结婚|对象|伴侣|家庭|朋友)", text, re.IGNORECASE):
            return "relationship"
        if re.search(r"(钱|收入|投资|财务|副业|买房|存款)", text, re.IGNORECASE):
            return "finance"
        if re.search(r"(健康|身体|作息|运动|焦虑|情绪)", text, re.IGNORECASE):
            return "health"
        if re.search(r"(学习|学校|考试|读研|出国|课程)", text, re.IGNORECASE):
            return "learning"
        return "general"
    
    def _build_career_graph_view(
        self,
        user_id: str,
        question: str = ""
    ) -> Dict[str, Any]:
        """
        构建职业知识图谱视图
        
        整合真实岗位数据，展示技能-岗位-公司的3D关系
        """
        try:
            from backend.vertical.career.career_knowledge_graph import career_kg, UserSkillProfile
            
            # 从用户画像中获取技能信息
            profile = self._safe_profile_snapshot(user_id)
            
            # 尝试从知识图谱中提取用户的技能信息
            export = self._load_graph_export(user_id)
            info_nodes = list(export.get("information") or [])
            
            # 提取技能节点
            user_skills = {}
            current_position = None
            years_experience = 0
            
            for node in info_nodes:
                node_type = node.get("type", "")
                node_name = node.get("name", "")
                
                # 识别技能节点
                if node_type in ["skill", "技能", "能力"]:
                    # 默认掌握度0.7，可以后续让用户标注
                    user_skills[node_name] = 0.7
                
                # 识别职位信息
                if node_type in ["position", "职位", "工作"]:
                    current_position = node_name
            
            # 如果没有技能信息，使用默认技能
            if not user_skills:
                user_skills = {
                    "Python": 0.6,
                    "JavaScript": 0.5,
                    "MySQL": 0.6,
                    "Git": 0.7
                }
            
            # 从问题中推断求职方向
            target_direction = "Python工程师"  # 默认方向
            if question:
                # 提取关键词
                if "Python" in question or "python" in question.lower():
                    target_direction = "Python工程师"
                elif "Java" in question or "java" in question.lower():
                    target_direction = "Java工程师"
                elif "前端" in question:
                    target_direction = "前端工程师"
                elif "后端" in question:
                    target_direction = "后端工程师"
            
            # 分类技能：已掌握、部分掌握、缺失
            mastered_skills = [skill for skill, level in user_skills.items() if level >= 0.7]
            partial_skills = [skill for skill, level in user_skills.items() if 0.3 <= level < 0.7]
            missing_skills = []  # 缺失技能由图谱构建器自动推断
            
            # 构建用户技能画像（使用正确的参数）
            user_profile = UserSkillProfile(
                mastered_skills=mastered_skills,
                partial_skills=partial_skills,
                missing_skills=missing_skills,
                target_direction=target_direction
            )
            
            # 构建职业知识图谱（只传user_profile参数）
            graph_data = career_kg.build_career_graph(user_profile=user_profile)
            
            # 转换为知识星图的格式
            return {
                "view_mode": "career",
                "title": "职业决策视图（真实岗位数据）",
                "nodes": graph_data["nodes"],
                "links": graph_data["edges"],
                "summary": {
                    "user_id": user_id,
                    "view_mode": "career",
                    "node_count": len(graph_data["nodes"]),
                    "link_count": len(graph_data["edges"]),
                    "top_nodes": [],
                    "metadata": graph_data["metadata"]
                }
            }
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[职业图谱] 构建失败: {e}，返回空图谱")
            
            # 返回空图谱
            return {
                "view_mode": "career",
                "title": "职业决策视图",
                "nodes": [],
                "links": [],
                "summary": {
                    "user_id": user_id,
                    "view_mode": "career",
                    "node_count": 0,
                    "link_count": 0,
                    "error": str(e)
                }
            }

    def _build_education_graph_view(
        self,
        user_id: str,
        question: str = ""
    ) -> Dict[str, Any]:
        """
        构建教育升学知识图谱视图

        整合学业数据、目标学校、申请规划，展示升学决策图谱
        """
        try:
            from backend.vertical.education.education_knowledge_graph import (
                education_kg, EducationUserProfile
            )

            # 从用户画像中获取学业信息
            profile = self._safe_profile_snapshot(user_id)

            # 尝试从知识图谱中提取学业信息
            export = self._load_graph_export(user_id)
            info_nodes = list(export.get("information") or [])

            # 提取学业节点
            gpa = profile.get("gpa", 3.5)
            ranking = profile.get("ranking_percent", 0.2)
            research = profile.get("research", 0.5)

            for node in info_nodes:
                node_type = node.get("type", "")
                node_name = node.get("name", "")
                if node_type in ["gpa", "GPA", "score", "成绩"]:
                    try:
                        gpa = float(node.get("score", gpa))
                    except:
                        pass
                if node_type in ["research", "科研", "publication"]:
                    research = max(research, 0.6)

            # 从问题中推断关键词
            target_major = ""
            location = ""
            keywords = ["人工智能", "计算机", "金融", "经济", "工程", "医学", "理科", "文科"]
            for kw in keywords:
                if kw in question:
                    target_major = kw
                    break

            # 构建学生学业档案
            user_profile = EducationUserProfile(
                student_id=user_id,
                gpa=gpa,
                gpa_max=4.0,
                ranking_percent=ranking,
                sat_act=profile.get("sat", 0),
                gre_gmat=profile.get("gre", 0),
                toefl_ielts=profile.get("toefl", 0),
                research_experience=research,
                publications=profile.get("publications", 0),
                target_major=target_major,
                target_level=profile.get("target_level", "master")
            )

            # 构建教育知识图谱
            graph_data = education_kg.build_education_graph(
                user_profile=user_profile,
                search_keyword=target_major,
                location=location
            )

            # 转换为知识星图的格式
            return {
                "view_mode": "signals",
                "title": "教育升学决策视图",
                "nodes": graph_data["nodes"],
                "links": graph_data["edges"],
                "summary": {
                    "user_id": user_id,
                    "view_mode": "signals",
                    "node_count": len(graph_data["nodes"]),
                    "link_count": len(graph_data["edges"]),
                    "top_nodes": [],
                    "metadata": graph_data["metadata"]
                }
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[教育图谱] 构建失败: {e}，返回空图谱")

            return {
                "view_mode": "signals",
                "title": "教育升学决策视图",
                "nodes": [],
                "links": [],
                "summary": {
                    "user_id": user_id,
                    "view_mode": "signals",
                    "node_count": 0,
                    "link_count": 0,
                    "error": str(e)
                }
            }

    def _build_bootstrap_graph(
        self,
        user_id: str,
        view_key: str,
        question: str,
    ) -> Dict[str, Any]:
        profile = self._safe_profile_snapshot(user_id)
        focus_domain = self._guess_focus_domain(question)
        focus_name_map = {
            "career": "职业跃迁焦点",
            "relationship": "关系稳定焦点",
            "finance": "财务安全焦点",
            "health": "身心状态焦点",
            "learning": "学习成长焦点",
            "general": "当前决策焦点",
        }
        focus_name = (question or "").strip()[:18] or focus_name_map.get(focus_domain, "当前决策焦点")

        if view_key == "people":
            collaboration_name = "同事/合作方" if focus_domain in {"career", "finance"} else "关键关系人"
            node_defs: List[Dict[str, Any]] = [
                {
                    "id": "bootstrap_self",
                    "name": "我",
                    "type": "person",
                    "category": "self",
                    "view_role": "person",
                    "weight": 0.98,
                    "influence_score": 0.99,
                    "insight_tags": ["引导图谱", "AI核心"],
                },
                {
                    "id": "bootstrap_family",
                    "name": "家人",
                    "type": "person",
                    "category": "family",
                    "view_role": "person",
                    "weight": round(clamp(0.56 + profile["social_dependency"] * 0.28), 3),
                    "influence_score": round(clamp(0.60 + profile["social_dependency"] * 0.24), 3),
                    "insight_tags": ["支持系统"],
                },
                {
                    "id": "bootstrap_partner",
                    "name": "伴侣/亲密关系",
                    "type": "person",
                    "category": "partner",
                    "view_role": "person",
                    "weight": round(clamp(0.48 + profile["social_dependency"] * 0.24), 3),
                    "influence_score": round(clamp(0.50 + profile["social_dependency"] * 0.22), 3),
                    "insight_tags": ["情绪联动"],
                },
                {
                    "id": "bootstrap_mentor",
                    "name": "导师/前辈",
                    "type": "person",
                    "category": "mentor",
                    "view_role": "person",
                    "weight": round(clamp(0.44 + profile["growth_bias"] * 0.30), 3),
                    "influence_score": round(clamp(0.46 + profile["growth_bias"] * 0.28), 3),
                    "insight_tags": ["成长牵引"],
                },
                {
                    "id": "bootstrap_friends",
                    "name": "朋友/同伴",
                    "type": "person",
                    "category": "friends",
                    "view_role": "person",
                    "weight": round(clamp(0.42 + profile["social_dependency"] * 0.26), 3),
                    "influence_score": round(clamp(0.44 + profile["social_dependency"] * 0.22), 3),
                    "insight_tags": ["同温层"],
                },
                {
                    "id": "bootstrap_collab",
                    "name": collaboration_name,
                    "type": "person",
                    "category": "team",
                    "view_role": "person",
                    "weight": round(clamp(0.40 + profile["execution_stability"] * 0.20 + profile["growth_bias"] * 0.12), 3),
                    "influence_score": round(clamp(0.44 + profile["execution_stability"] * 0.20 + profile["growth_bias"] * 0.12), 3),
                    "insight_tags": ["现实推进"],
                },
            ]
            links = [
                {"source": "bootstrap_self", "target": "bootstrap_family", "type": "SUPPORTS", "strength": 0.78, "description": "基础支持"},
                {"source": "bootstrap_self", "target": "bootstrap_partner", "type": "AFFECTS", "strength": 0.72, "description": "情绪联动"},
                {"source": "bootstrap_self", "target": "bootstrap_mentor", "type": "GUIDES", "strength": 0.75, "description": "经验引导"},
                {"source": "bootstrap_self", "target": "bootstrap_friends", "type": "FEEDBACK", "strength": 0.68, "description": "同伴反馈"},
                {"source": "bootstrap_self", "target": "bootstrap_collab", "type": "COORDINATES", "strength": 0.70, "description": "现实推进"},
                {"source": "bootstrap_family", "target": "bootstrap_partner", "type": "INTERACTS", "strength": 0.56, "description": "关系耦合"},
                {"source": "bootstrap_mentor", "target": "bootstrap_collab", "type": "ENABLES", "strength": 0.59, "description": "机会转化"},
            ]
            title = "人物关系视图（引导星图）"
        else:
            node_defs = [
                {
                    "id": "bootstrap_focus",
                    "name": focus_name,
                    "type": "event",
                    "category": "focus",
                    "view_role": "signal",
                    "weight": 0.92,
                    "influence_score": 0.95,
                    "insight_tags": ["问题锚点"],
                },
                {
                    "id": "bootstrap_growth",
                    "name": "成长潜力",
                    "type": "concept",
                    "category": "growth",
                    "view_role": "signal",
                    "weight": round(clamp(0.42 + profile["growth_bias"] * 0.36), 3),
                    "influence_score": round(clamp(0.46 + profile["growth_bias"] * 0.32), 3),
                    "insight_tags": ["长期收益"],
                },
                {
                    "id": "bootstrap_execution",
                    "name": "执行稳定性",
                    "type": "resource",
                    "category": "execution",
                    "view_role": "signal",
                    "weight": round(clamp(0.42 + profile["execution_stability"] * 0.34), 3),
                    "influence_score": round(clamp(0.44 + profile["execution_stability"] * 0.32), 3),
                    "insight_tags": ["可落地性"],
                },
                {
                    "id": "bootstrap_finance",
                    "name": "现金压力",
                    "type": "finance",
                    "category": "finance",
                    "view_role": "signal",
                    "weight": round(clamp(0.38 + (1 - profile["risk_tolerance"]) * 0.34), 3),
                    "influence_score": round(clamp(0.42 + profile["loss_aversion"] * 0.28), 3),
                    "insight_tags": ["现实成本"],
                },
                {
                    "id": "bootstrap_health",
                    "name": "身心状态",
                    "type": "health",
                    "category": "health",
                    "view_role": "signal",
                    "weight": round(clamp(0.40 + (1 - profile["execution_stability"]) * 0.14 + profile["ambiguity_tolerance"] * 0.18), 3),
                    "influence_score": round(clamp(0.42 + (1 - profile["execution_stability"]) * 0.16), 3),
                    "insight_tags": ["恢复能力"],
                },
                {
                    "id": "bootstrap_relationship",
                    "name": "关系牵引",
                    "type": "emotion",
                    "category": "relationship",
                    "view_role": "signal",
                    "weight": round(clamp(0.40 + profile["social_dependency"] * 0.32), 3),
                    "influence_score": round(clamp(0.42 + profile["social_dependency"] * 0.30), 3),
                    "insight_tags": ["人物影响"],
                },
                {
                    "id": "bootstrap_risk",
                    "name": "风险敞口",
                    "type": "risk",
                    "category": "risk",
                    "view_role": "signal",
                    "weight": round(clamp(0.36 + profile["loss_aversion"] * 0.32), 3),
                    "influence_score": round(clamp(0.40 + profile["loss_aversion"] * 0.28), 3),
                    "insight_tags": ["需要校准"],
                },
            ]
            links = [
                {"source": "bootstrap_focus", "target": "bootstrap_growth", "type": "DRIVES", "strength": 0.72, "description": "决策对长期成长的拉动"},
                {"source": "bootstrap_focus", "target": "bootstrap_execution", "type": "DEPENDS_ON", "strength": 0.74, "description": "落地需要执行稳定"},
                {"source": "bootstrap_focus", "target": "bootstrap_finance", "type": "COSTS", "strength": 0.66, "description": "短期成本约束"},
                {"source": "bootstrap_focus", "target": "bootstrap_health", "type": "AFFECTS", "strength": 0.61, "description": "身心承压反馈"},
                {"source": "bootstrap_focus", "target": "bootstrap_relationship", "type": "INFLUENCED_BY", "strength": 0.68, "description": "关系网络影响选择"},
                {"source": "bootstrap_focus", "target": "bootstrap_risk", "type": "EXPOSES", "strength": 0.70, "description": "潜在风险暴露"},
                {"source": "bootstrap_execution", "target": "bootstrap_growth", "type": "ENABLES", "strength": 0.64, "description": "持续执行放大成长"},
                {"source": "bootstrap_finance", "target": "bootstrap_risk", "type": "AMPLIFIES", "strength": 0.58, "description": "现金压力抬高风险"},
                {"source": "bootstrap_relationship", "target": "bootstrap_health", "type": "AFFECTS", "strength": 0.55, "description": "关系变化影响状态"},
            ]
            title = "信号节点视图（引导星图）"

        degree_map: Dict[str, int] = defaultdict(int)
        for link in links:
            degree_map[str(link["source"])] += 1
            degree_map[str(link["target"])] += 1

        nodes: List[Dict[str, Any]] = []
        for node in node_defs:
            nodes.append(
                {
                    **node,
                    "connections": degree_map.get(str(node["id"]), 0),
                }
            )

        top_names = sorted(
            [(str(node["name"]), float(node["influence_score"])) for node in nodes],
            key=lambda item: item[1],
            reverse=True,
        )
        return {
            "view_mode": view_key,
            "title": title,
            "nodes": nodes,
            "links": links,
            "summary": {
                "user_id": user_id,
                "view_mode": view_key,
                "node_count": len(nodes),
                "link_count": len(links),
                "top_nodes": [name for name, _ in top_names[:5]],
                "bootstrap": True,
            },
        }

    def get_graph_view(
        self,
        user_id: str,
        view_mode: str = "people",
        question: str = "",
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取知识图谱视图 - 三级缓存架构
        L1: 内存缓存（最快）→ L2: Redis缓存 → L3: 计算生成
        """
        import time
        func_start = time.time()
        
        # 生成缓存key（包含所有参数）
        cache_key = f"kg_view:{user_id}:{view_mode}:{question}:{session_id or 'all'}"
        print(f"[KG Service] 🔑 缓存Key: {cache_key}")
        
        # L1: 尝试从内存缓存读取（最快，纳秒级）
        l1_start = time.time()
        cached = _l1_cache.get(cache_key)
        l1_time = time.time() - l1_start
        
        if cached:
            total_time = time.time() - func_start
            print(f"[L1 Hit] ⚡ 从内存加载视图: {view_mode}, L1耗时={l1_time*1000:.2f}ms, 总耗时={total_time*1000:.2f}ms")
            return cached
        
        print(f"[L1 Miss] 内存缓存未命中, 检查耗时={l1_time*1000:.2f}ms")
        
        # L2: 尝试从Redis缓存读取（快，毫秒级）
        l2_start = time.time()
        try:
            redis_client = _get_redis_client()
            if redis_client:
                cached_str = redis_client.get(cache_key)
                l2_time = time.time() - l2_start
                
                if cached_str:
                    result = json.loads(cached_str)
                    total_time = time.time() - func_start
                    print(f"[L2 Hit] 🔥 从Redis加载视图: {view_mode}, L2耗时={l2_time*1000:.2f}ms, 总耗时={total_time*1000:.2f}ms")
                    # 回填到L1缓存
                    _l1_cache.set(cache_key, result)
                    return result
                else:
                    print(f"[L2 Miss] Redis缓存未命中, 检查耗时={l2_time*1000:.2f}ms")
        except Exception as e:
            l2_time = time.time() - l2_start
            print(f"[L2 Miss] Redis读取失败: {e}, 耗时={l2_time*1000:.2f}ms")
        
        # L3: 缓存未命中，计算视图数据
        print(f"[L3 Compute] 🔨 开始计算视图: {view_mode}")
        compute_start = time.time()
        
        # career 视图：职业知识图谱
        if view_mode == "career":
            result = self._build_career_graph_view(user_id, question)
        # signals 视图：教育升学知识图谱
        elif view_mode == "signals":
            result = self._build_education_graph_view(user_id, question)
        # people 视图：人物关系图谱
        else:
            view_key = "people"
            export = self._load_graph_export(user_id)
            info_nodes = list(export.get("information") or [])
            relationships = list(export.get("relationships") or [])

            if not info_nodes:
                result = self._build_bootstrap_graph(user_id, view_key, question)
            else:
                result = self._process_graph_view(
                    user_id, view_key, question, session_id,
                    info_nodes, relationships
                )
        
        elapsed = time.time() - compute_start
        total_time = time.time() - func_start
        print(f"[L3 Compute] ✅ 视图计算完成, 计算耗时={elapsed:.3f}s, 总耗时={total_time:.3f}s")
        
        # 写入L1内存缓存（最快）
        cache_write_start = time.time()
        _l1_cache.set(cache_key, result)
        
        # 写入L2 Redis缓存，TTL 30分钟
        try:
            redis_client = _get_redis_client()
            if redis_client:
                redis_client.setex(
                    cache_key,
                    1800,  # 30分钟过期
                    json.dumps(result, ensure_ascii=False)
                )
                cache_write_time = time.time() - cache_write_start
                print(f"[Cache Write] 💾 视图已缓存到L1+L2: {view_mode}, 写入耗时={cache_write_time*1000:.2f}ms")
        except Exception as e:
            cache_write_time = time.time() - cache_write_start
            print(f"[Cache Write Failed] ❌ 缓存写入失败: {e}, 耗时={cache_write_time*1000:.2f}ms")
        
        return result
    
    def _process_graph_view(
        self,
        user_id: str,
        view_key: str,
        question: str,
        session_id: Optional[str],
        info_nodes: List[Dict],
        relationships: List[Dict]
    ) -> Dict[str, Any]:
        """
        处理图谱视图数据（从get_graph_view中提取）
        优化：只在必要时才调用LLM分类
        """
        
        if session_id:
            allowed_ids = {
                node["id"]
                for node in info_nodes
                if node.get("session_id") == session_id
                or (node.get("metadata") or {}).get("session_id") == session_id
            }
            if allowed_ids:
                info_nodes = [node for node in info_nodes if node["id"] in allowed_ids]
                relationships = [rel for rel in relationships if rel.get("source") in allowed_ids and rel.get("target") in allowed_ids]

        # ── LLM智能分流（增量式，异步后台分类） ──────────────────────────────
        # 异步模式：有新节点时后台分类，不阻塞视图加载
        llm_labels = _llm_classify_nodes(info_nodes, async_mode=True)
        people_ids = {nid for nid, label in llm_labels.items() if label == "person"}
        career_ids = {nid for nid, label in llm_labels.items() if label == "career"}

        # 根据视图类型过滤节点
        if view_key == "people":
            filtered_nodes = [node for node in info_nodes if node["id"] in people_ids]
        elif view_key == "career":
            filtered_nodes = [node for node in info_nodes if node["id"] in career_ids]
        else:  # signals
            filtered_nodes = [node for node in info_nodes if node["id"] not in people_ids and node["id"] not in career_ids]
        
        if not filtered_nodes:
            filtered_nodes = info_nodes[:16]

        filtered_ids = {node["id"] for node in filtered_nodes}
        filtered_links = [rel for rel in relationships if rel.get("source") in filtered_ids and rel.get("target") in filtered_ids]

        # 若过滤后无连线，将主节点的同类型邻居也纳入展示
        if not filtered_links and relationships:
            neighbor_ids: set = set()
            all_node_ids = {n["id"] for n in info_nodes}
            for rel in relationships:
                src, tgt = rel.get("source"), rel.get("target")
                if src in filtered_ids and tgt in all_node_ids:
                    neighbor_ids.add(tgt)
                if tgt in filtered_ids and src in all_node_ids:
                    neighbor_ids.add(src)
            neighbor_ids -= filtered_ids
            
            # 只取同类型节点
            if view_key == "people":
                extra_nodes = [n for n in info_nodes if n["id"] in neighbor_ids and n["id"] in people_ids][:30]
            elif view_key == "career":
                extra_nodes = [n for n in info_nodes if n["id"] in neighbor_ids and n["id"] in career_ids][:30]
            else:  # signals
                extra_nodes = [n for n in info_nodes if n["id"] in neighbor_ids and n["id"] not in people_ids and n["id"] not in career_ids][:30]
            
            filtered_nodes = filtered_nodes + extra_nodes
            filtered_ids = {n["id"] for n in filtered_nodes}
            filtered_links = [rel for rel in relationships if rel.get("source") in filtered_ids and rel.get("target") in filtered_ids]

        degree_map: Dict[str, int] = defaultdict(int)
        for rel in filtered_links:
            degree_map[str(rel.get("source"))] += 1
            degree_map[str(rel.get("target"))] += 1

        nodes: List[Dict[str, Any]] = []
        top_names: List[Tuple[str, float]] = []
        for node in filtered_nodes:
            importance = self._node_importance(node, degree_map.get(node["id"], 0), question, view_key)
            influence = round(clamp(importance + min(0.12, degree_map.get(node["id"], 0) * 0.02)), 3)
            tags: List[str] = []
            if node["id"] in people_ids:
                tags.append(str(node.get("category") or "关系人物"))
            else:
                tags.append(str(node.get("type") or "signal"))
            if degree_map.get(node["id"], 0) >= 3:
                tags.append("高连接")
            # 标记 LLM 分流的节点
            if node["id"] in llm_labels:
                tags.append("AI分类")
            nodes.append(
                {
                    "id": node["id"],
                    "name": node.get("name", "未命名节点"),
                    "type": node.get("type", "Information"),
                    "category": node.get("category"),
                    "view_role": "person" if node["id"] in people_ids else "signal",
                    "weight": importance,
                    "influence_score": influence,
                    "connections": degree_map.get(node["id"], 0),
                    "insight_tags": tags,
                }
            )
            top_names.append((str(node.get("name", "")), influence))

        links = [
            {
                "source": rel.get("source"),
                "target": rel.get("target"),
                "type": rel.get("type", "RELATED"),
                "strength": round(clamp(float(rel.get("confidence", 0.55) or 0.55) + 0.04), 3),
                "description": rel.get("description"),
            }
            for rel in filtered_links
        ]
        top_names.sort(key=lambda item: item[1], reverse=True)

        # ── 人物视图：注入"我"节点作为中心 ──────────────────
        if view_key == "people":
            me_id = f"__me__{user_id}"
            # 为每个人物节点添加到"我"的连线（如果还没有）
            existing_link_pairs = {(l["source"], l["target"]) for l in links}
            for node_item in nodes:
                pair = (me_id, node_item["id"])
                pair_rev = (node_item["id"], me_id)
                if pair not in existing_link_pairs and pair_rev not in existing_link_pairs:
                    links.append({
                        "source": me_id,
                        "target": node_item["id"],
                        "type": "RELATES_TO",
                        "strength": round(node_item["influence_score"] * 0.6 + 0.2, 3),
                        "description": None,
                    })
            # "我"节点插到最前面，权重最高
            me_node = {
                "id": me_id,
                "name": "我",
                "type": "Self",
                "category": "self",
                "view_role": "person",
                "weight": 1.0,
                "influence_score": 1.0,
                "connections": len(nodes),
                "insight_tags": ["中心", "自我"],
                "is_self": True,
            }
            nodes.insert(0, me_node)

        return {
            "view_mode": view_key,
            "title": "人物关系视图" if view_key == "people" else "升学规划视图",
            "nodes": nodes,
            "links": links,
            "summary": {
                "user_id": user_id,
                "view_mode": view_key,
                "node_count": len(nodes),
                "link_count": len(links),
                "top_nodes": [name for name, _ in top_names[:5]],
            },
        }

    def _load_profile(self, user_id: str) -> Dict[str, float]:
        self.ensure_tables()
        session = self._db_session()
        try:
            row = session.execute(text("SELECT profile_json FROM future_os_profiles WHERE user_id = :uid"), {"uid": user_id}).fetchone()
            if not row or not row[0]:
                return dict(DEFAULT_PROFILE)
            parsed = json.loads(row[0])
            profile = dict(DEFAULT_PROFILE)
            for key in profile:
                if key in parsed:
                    profile[key] = clamp(float(parsed[key]))
            return profile
        except Exception:
            return dict(DEFAULT_PROFILE)
        finally:
            session.close()

    def _save_profile(self, user_id: str, profile: Dict[str, float]) -> None:
        self.ensure_tables()
        session = self._db_session()
        try:
            session.execute(
                text(
                    """
                    INSERT INTO future_os_profiles (user_id, profile_json, updated_at)
                    VALUES (:uid, :payload, :updated_at)
                    ON DUPLICATE KEY UPDATE profile_json = VALUES(profile_json), updated_at = VALUES(updated_at)
                    """
                ),
                {"uid": user_id, "payload": json.dumps(profile, ensure_ascii=False), "updated_at": datetime.now().isoformat()},
            )
            session.commit()
        finally:
            session.close()

    def _load_recent_parallel_runs(self, user_id: str) -> List[Dict[str, Any]]:
        self.ensure_tables()
        session = self._db_session()
        try:
            rows = session.execute(
                text(
                    """
                    SELECT payload_json
                    FROM future_os_parallel_runs
                    WHERE user_id = :uid
                    ORDER BY id DESC
                    LIMIT 12
                    """
                ),
                {"uid": user_id},
            ).fetchall()
            result = []
            for row in rows:
                try:
                    result.append(json.loads(row[0]))
                except Exception:
                    continue
            return result
        except Exception:
            return []
        finally:
            session.close()

    def _derive_profile_from_history(self, user_id: str) -> Dict[str, float]:
        profile = self._load_profile(user_id)
        runs = self._load_recent_parallel_runs(user_id)
        if not runs:
            return profile

        profile["risk_tolerance"] = clamp(avg([run.get("behavior_profile", {}).get("actual_risk_tolerance", profile["risk_tolerance"]) for run in runs], profile["risk_tolerance"]))
        profile["social_dependency"] = clamp(avg([run.get("behavior_profile", {}).get("actual_social_dependency", profile["social_dependency"]) for run in runs], profile["social_dependency"]))
        profile["execution_stability"] = clamp(avg([run.get("behavior_profile", {}).get("actual_execution_stability", profile["execution_stability"]) for run in runs], profile["execution_stability"]))
        profile["growth_bias"] = clamp(avg([run.get("behavior_profile", {}).get("actual_growth_bias", profile["growth_bias"]) for run in runs], profile["growth_bias"]))
        profile["loss_aversion"] = clamp(avg([run.get("behavior_profile", {}).get("actual_loss_aversion", profile["loss_aversion"]) for run in runs], profile["loss_aversion"]))
        profile["ambiguity_tolerance"] = clamp(avg([1.0 - run.get("behavior_profile", {}).get("actual_loss_aversion", 1.0 - profile["ambiguity_tolerance"]) for run in runs], profile["ambiguity_tolerance"]))
        return profile

    def build_context(self, user_id: str, question: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        people_view = self.get_graph_view(user_id, "people", question, session_id)
        signal_view = self.get_graph_view(user_id, "signals", question, session_id)
        profile = self._derive_profile_from_history(user_id)

        people_nodes = sorted(people_view["nodes"], key=lambda item: float(item.get("influence_score", 0.0)), reverse=True)
        signal_nodes = sorted(signal_view["nodes"], key=lambda item: float(item.get("weight", 0.0)), reverse=True)
        
        # 智能推荐视图：人物关系、升学规划、职业发展
        if re.search(r"(家人|朋友|伴侣|同事|导师|关系|谁)", question):
            recommended_view = "people"
        elif re.search(r"(学习|课程|专业|升学|考研|留学|学校)", question):
            recommended_view = "signals"
        elif re.search(r"(工作|职业|技能|岗位|公司|求职|面试)", question):
            recommended_view = "career"
        else:
            recommended_view = "people"

        return {
            "question": question,
            "recommended_view": recommended_view,
            "profile": profile,
            "top_people": people_nodes[:5],
            "top_signals": signal_nodes[:6],
            "brief": {
                "current_focus": "关系影响" if recommended_view == "people" else "状态与约束",
                "people_count": people_view["summary"]["node_count"],
                "signal_count": signal_view["summary"]["node_count"],
                "key_people": [item["name"] for item in people_nodes[:3]],
                "key_signals": [item["name"] for item in signal_nodes[:4]],
            },
        }

    def route_message(self, user_id: str, message: str) -> Dict[str, Any]:
        if re.search(r"(关系|家人|朋友|伴侣|同事|导师|谁影响我)", message):
            module = "knowledge_graph"
            target_view = "people"
            reason = "这条消息更像在询问关系影响，优先打开人物关系视图。"
        elif re.search(r"(如果|选择|该不该|要不要|决策|路径|推演)", message):
            module = "decision_graph"
            target_view = "signals"
            reason = "这条消息包含明显的分支选择语义，适合进入决策图谱舞台。"
        elif re.search(r"(模拟|体验|游戏|看看我会怎么选|情境)", message):
            module = "parallel_life"
            target_view = "signals"
            reason = "这条消息适合用情境化方式采集真实取舍，建议进入平行人生。"
        else:
            module = "chat"
            target_view = "signals"
            reason = "先在 AI 核心对话里补充信息，再决定是否进入图谱或游戏。"
        context = self.build_context(user_id, message)
        return {
            "recommended_module": module,
            "recommended_view": target_view,
            "reason": reason,
            "context_brief": context["brief"],
        }

    def _build_agent_votes(
        self,
        strategy: str,
        impact_vector: Dict[str, float],
        probability: float,
        execution_confidence: float,
    ) -> List[Dict[str, Any]]:
        growth_signal = float(impact_vector.get("growth", 0.0))
        finance_signal = float(impact_vector.get("finance", 0.0))
        stress_signal = float(impact_vector.get("stress", 0.0))
        social_signal = float(impact_vector.get("social", 0.0))

        growth_score = clamp(0.48 + growth_signal * 1.6 + execution_confidence * 0.14)
        stability_score = clamp(0.54 + finance_signal * 1.25 - max(0.0, stress_signal) * 0.9 + probability * 0.08)
        relation_score = clamp(0.5 + social_signal * 1.45 + (0.06 if "关系" in strategy else 0.0))

        def stance(score: float) -> str:
            if score >= 0.66:
                return "support"
            if score <= 0.42:
                return "challenge"
            return "watch"

        return [
            {
                "agent_id": "growth_agent",
                "agent_name": "成长代理",
                "stance": stance(growth_score),
                "score": round(growth_score, 3),
                "confidence": round(clamp(execution_confidence + 0.06), 3),
                "reason": "评估这一步是否真正扩大长期成长空间。",
                "focus": ["growth", "confidence"],
                "flags": ["upside"] if growth_signal > 0 else ["plateau"],
            },
            {
                "agent_id": "stability_agent",
                "agent_name": "稳定代理",
                "stance": stance(stability_score),
                "score": round(stability_score, 3),
                "confidence": round(clamp(probability + 0.05), 3),
                "reason": "检查现金流、压力和执行可持续性是否可控。",
                "focus": ["finance", "stress", "health"],
                "flags": ["risk"] if stress_signal > 0.08 else ["stable"],
            },
            {
                "agent_id": "relationship_agent",
                "agent_name": "关系代理",
                "stance": stance(relation_score),
                "score": round(relation_score, 3),
                "confidence": round(clamp((probability + execution_confidence) / 2), 3),
                "reason": "评估关键人物的支持、摩擦与协同空间。",
                "focus": ["social", "support"],
                "flags": ["people"] if social_signal >= 0 else ["friction"],
            },
        ]

    def _branch_fit_score(self, strategy: str, question: str, profile: Dict[str, float]) -> float:
        score = 0.45
        if "稳定" in strategy and profile["loss_aversion"] > 0.55:
            score += 0.14
        if "成长" in strategy and profile["growth_bias"] > 0.52:
            score += 0.16
        if "关系" in strategy and profile["social_dependency"] > 0.52:
            score += 0.16
        if "探索" in strategy and profile["ambiguity_tolerance"] > 0.5:
            score += 0.14
        if "恢复" in strategy and re.search(r"(累|焦虑|压力|休息|恢复|健康)", question):
            score += 0.18
        return round(score, 3)

    def _infer_branch_blueprints(self, question: str, options: List[str], profile: Dict[str, float]) -> List[Dict[str, Any]]:
        explicit = [item.strip() for item in options if item.strip()]
        branches: List[Dict[str, Any]] = []
        if explicit:
            for index, option in enumerate(explicit[:5]):
                matched = None
                for blueprint in BRANCH_LIBRARY:
                    if any(keyword in option for keyword in blueprint["keywords"]):
                        matched = blueprint
                        break
                matched = dict(matched or BRANCH_LIBRARY[index % len(BRANCH_LIBRARY)])
                matched["title"] = option
                matched["option_id"] = f"option_{index + 1}"
                branches.append(matched)
            return branches

        ranked = sorted(BRANCH_LIBRARY, key=lambda item: self._branch_fit_score(item["branch_strategy"], question, profile), reverse=True)
        for index, blueprint in enumerate(ranked[:4]):
            branch = dict(blueprint)
            branch["title"] = blueprint["branch_strategy"]
            branch["option_id"] = f"option_{index + 1}"
            branches.append(branch)
        return branches

    def _base_state_vector(self, profile: Dict[str, float], context: Dict[str, Any]) -> Dict[str, float]:
        signal_names = " ".join(item["name"] for item in context.get("top_signals", []))
        health_penalty = 0.08 if re.search(r"(睡眠|健康|疲惫|压力)", signal_names) else 0.0
        finance_penalty = 0.08 if re.search(r"(财务|房租|收入|开销)", signal_names) else 0.0
        return {
            "energy": clamp(0.60 - health_penalty + (profile["execution_stability"] - 0.5) * 0.16),
            "confidence": clamp(0.52 + (profile["growth_bias"] - 0.5) * 0.20),
            "finance": clamp(0.50 - finance_penalty + (profile["loss_aversion"] - 0.5) * 0.10),
            "social_stability": clamp(0.55 + (profile["social_dependency"] - 0.5) * 0.18),
            "health": clamp(0.58 - health_penalty),
            "growth": clamp(0.56 + (profile["growth_bias"] - 0.5) * 0.24),
            "stress": clamp(0.42 + (profile["loss_aversion"] - 0.5) * 0.22 + health_penalty),
        }

    def _pick_key_people(self, context: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
        return list(context.get("top_people", []))[:limit]

    def _apply_delta(
        self,
        state: Dict[str, float],
        delta: Dict[str, float],
        people: List[Dict[str, Any]],
        strategy: str,
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        relation_delta = 0.0
        if people:
            influence = avg([float(item.get("influence_score", 0.5)) for item in people], 0.5)
            if "关系" in strategy:
                relation_delta = influence * 0.05
            elif "稳定" in strategy:
                relation_delta = influence * 0.02
            elif "成长" in strategy:
                relation_delta = influence * 0.015

        next_state = dict(state)
        impact_vector: Dict[str, float] = {}
        mapping = {
            "finance": "finance",
            "growth": "growth",
            "emotion": "confidence",
            "social": "social_stability",
            "health": "health",
            "confidence": "confidence",
            "stress": "stress",
            "ambiguity": "energy",
        }
        for key, value in delta.items():
            target = mapping.get(key, key)
            if target not in next_state:
                continue
            adjusted = float(value)
            if target == "social_stability":
                adjusted += relation_delta
            next_state[target] = clamp(next_state[target] + adjusted)
            impact_vector[key if key != "ambiguity" else "growth"] = round(adjusted, 3)

        if next_state["stress"] > 0.7:
            next_state["energy"] = clamp(next_state["energy"] - 0.06)
            impact_vector["health"] = round(impact_vector.get("health", 0.0) - 0.04, 3)
        return next_state, impact_vector

    def _branch_event_text(self, strategy: str, month: int, lead_person: Optional[str]) -> str:
        if "稳定" in strategy:
            templates = [
                "先稳住现金流与作息，把问题拆成可执行小步。",
                f"和 {lead_person or '关键人物'} 对齐预期，降低路径摩擦。",
                "保留主线收益，同时给下一步保留试探空间。",
                "形成更稳的节奏，为下一阶段切换积累筹码。",
            ]
        elif "成长" in strategy:
            templates = [
                "把更多时间投入长期能力建设，接受短期波动。",
                f"向 {lead_person or '关键人物'} 寻求反馈与资源支持。",
                "承受阶段性压力，换取能力曲线抬升。",
                "能力开始反哺结果，路径逐渐进入正循环。",
            ]
        elif "关系" in strategy:
            templates = [
                "先把关系稳定与沟通成本放到台面上处理。",
                f"围绕 {lead_person or '关键人物'} 重新安排节奏和边界。",
                "把关键承诺与现实约束重新对齐。",
                "关系更稳，但部分成长或收益速度被主动放缓。",
            ]
        elif "探索" in strategy:
            templates = [
                "保留安全垫后小步试错，不一次性押满筹码。",
                f"拉上 {lead_person or '关键人物'} 一起验证假设与风险。",
                "用阶段性反馈筛掉不适合自己的方向。",
                "在试错中获得更清晰的长期路线。",
            ]
        else:
            templates = [
                "先降低压力和消耗，把状态恢复到可持续区间。",
                "缩小决策范围，只保留最关键的一两个目标。",
                f"借助 {lead_person or '关键人物'} 的支持修复执行力。",
                "恢复稳定后，再决定是否重新切换主线。",
            ]
        return templates[min(max(month - 1, 0), len(templates) - 1)]

    def _build_decision_graph_payload(self, branch_id: str, title: str, timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
        nodes = []
        edges = []
        dominant_axes: Dict[str, float] = defaultdict(float)
        high_risk_nodes = 0
        for item in timeline:
            node = dict(item)
            node["event_type"] = "branch_state"
            node["opportunity_tag"] = "high" if sum(v for v in node["impact_vector"].values() if v > 0) > 0.16 else "medium"
            node["visual_weight"] = round(clamp(abs(sum(node["impact_vector"].values())) * 1.6, 0.22, 1.0), 3)
            nodes.append(node)
            if node["risk_tag"] == "high":
                high_risk_nodes += 1
            for key, value in node["impact_vector"].items():
                dominant_axes[key] += abs(float(value))
            if node.get("parent_event_id"):
                edges.append(
                    {
                        "edge_id": f"{node['parent_event_id']}->{node['event_id']}",
                        "source": node["parent_event_id"],
                        "target": node["event_id"],
                        "relation": "next",
                        "strength": round(float(node["execution_confidence"]), 3),
                        "label": f"M{node['month']}",
                    }
                )
        return {
            "graph_id": f"{branch_id}_graph",
            "schema_version": 2,
            "layout_hint": "future-state-stage",
            "graph_summary": {
                "title": title,
                "node_count": len(nodes),
                "edge_count": len(edges),
                "high_risk_nodes": high_risk_nodes,
                "dominant_axes": [key for key, _ in sorted(dominant_axes.items(), key=lambda item: item[1], reverse=True)[:4]],
                "agent_stance_mix": {branch_id: len(nodes)},
                "review_mode": "branch_agents_v2",
            },
            "nodes": nodes,
            "edges": edges,
        }

    def _build_branch_option(
        self,
        question: str,
        branch: Dict[str, Any],
        context: Dict[str, Any],
        base_state: Dict[str, float],
    ) -> Dict[str, Any]:
        key_people = self._pick_key_people(context)
        key_people_names = [item["name"] for item in key_people]
        strategy = str(branch["branch_strategy"])
        current_state = dict(base_state)
        nodes: List[Dict[str, Any]] = []

        for index, delta in enumerate(branch["deltas"], start=1):
            lead_person = key_people_names[(index - 1) % len(key_people_names)] if key_people_names else None
            next_state, impact_vector = self._apply_delta(current_state, delta, key_people, strategy)
            probability = clamp(
                0.72
                - index * 0.06
                + (context["profile"]["execution_stability"] - 0.5) * 0.18
                + (0.04 if strategy.startswith("保守") else 0.0)
                - (0.03 if strategy.startswith("探索") else 0.0)
            )
            execution_confidence = clamp(
                0.55
                + (context["profile"]["execution_stability"] - 0.5) * 0.42
                + (0.06 if strategy.startswith("关系") and context["profile"]["social_dependency"] > 0.55 else 0.0)
                - (0.05 if next_state["stress"] > 0.68 else 0.0)
            )
            negative_sum = sum(abs(value) for value in impact_vector.values() if value < 0)
            collapse_risk = "high" if negative_sum >= 0.22 or next_state["stress"] >= 0.72 else "medium" if negative_sum >= 0.12 else "low"
            nodes.append(
                {
                    "branch_id": branch["agent_id"],
                    "branch_strategy": strategy,
                    "event_id": f"{branch['agent_id']}_m{index}",
                    "parent_event_id": nodes[-1]["event_id"] if nodes else None,
                    "node_level": index,
                    "month": index * 2,
                    "state_before": {key: round(value, 3) for key, value in current_state.items()},
                    "event": self._branch_event_text(strategy, index, lead_person),
                    "state_after": {key: round(value, 3) for key, value in next_state.items()},
                    "impact_vector": impact_vector,
                    "impact": impact_vector,
                    "probability": round(probability, 3),
                    "execution_confidence": round(execution_confidence, 3),
                    "collapse_risk": collapse_risk,
                    "risk_tag": collapse_risk,
                    "branch_group": branch["agent_id"],
                    "key_people": key_people_names[:2],
                    "evidence_sources": ["knowledge_graph", "parallel_life_profile", "conversation_memory"],
                    "agent_votes": self._build_agent_votes(
                        strategy=strategy,
                        impact_vector=impact_vector,
                        probability=probability,
                        execution_confidence=execution_confidence,
                    ),
                }
            )
            current_state = next_state

        final_state = nodes[-1]["state_after"] if nodes else base_state
        final_score = round(
            (
                final_state["confidence"] * 26
                + final_state["growth"] * 24
                + final_state["finance"] * 20
                + final_state["social_stability"] * 16
                + final_state["health"] * 14
                - final_state["stress"] * 18
            )
            * 100
            / 82,
            1,
        )
        final_score = max(25.0, min(92.0, final_score))
        risk_level = round(clamp(avg([0.78 if node["collapse_risk"] == "high" else 0.48 if node["collapse_risk"] == "medium" else 0.2 for node in nodes], 0.5)), 3)
        return {
            "option_id": branch["option_id"],
            "title": branch["title"],
            "description": branch["description"],
            "branch_strategy": strategy,
            "branch_agent_id": branch["agent_id"],
            "key_people": key_people_names,
            "timeline": nodes,
            "decision_graph": self._build_decision_graph_payload(branch["agent_id"], branch["title"], nodes),
            "final_score": final_score,
            "risk_level": risk_level,
            "execution_confidence": round(avg([node["execution_confidence"] for node in nodes], 0.55), 3),
            "dropout_risk_month": next((node["month"] for node in nodes if node["collapse_risk"] == "high"), None),
            "personal_note": f"{strategy} 更适合当前画像，关键影响人物：{' / '.join(key_people_names[:2]) if key_people_names else '暂无显著人物压力'}。",
        }

    def simulate_decision(
        self,
        user_id: str,
        question: str,
        options: Optional[List[str]] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.ensure_tables()
        context = self.build_context(user_id, question.strip(), session_id)
        branches = self._infer_branch_blueprints(question, options or [], context["profile"])
        base_state = self._base_state_vector(context["profile"], context)
        branch_options = [self._build_branch_option(question, branch, context, base_state) for branch in branches]
        recommendation = max(
            branch_options,
            key=lambda item: float(item["final_score"]) * 0.6 + float(item["execution_confidence"]) * 40 - float(item["risk_level"]) * 18,
        ) if branch_options else None
        payload = {
            "simulation_id": f"future_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "question": question.strip(),
            "options_count": len(branch_options),
            "recommendation": recommendation["title"] if recommendation else "",
            "schema_version": 5,
            "engine_mode": "future_os_branch_agents_v2",
            "context_snapshot": context,
            "options": branch_options,
            "created_at": datetime.now().isoformat(),
        }
        self._save_decision_record(payload)
        return payload

    def _save_decision_record(self, payload: Dict[str, Any]) -> None:
        self.ensure_tables()
        session = self._db_session()
        try:
            session.execute(
                text(
                    """
                    INSERT INTO decision_records
                        (simulation_id, user_id, question, options_count, recommendation, timeline_data, created_at)
                    VALUES
                        (:sid, :uid, :question, :options_count, :recommendation, :timeline_data, :created_at)
                    ON DUPLICATE KEY UPDATE
                        question = VALUES(question),
                        options_count = VALUES(options_count),
                        recommendation = VALUES(recommendation),
                        timeline_data = VALUES(timeline_data),
                        created_at = VALUES(created_at)
                    """
                ),
                {
                    "sid": payload["simulation_id"],
                    "uid": payload["user_id"],
                    "question": payload["question"],
                    "options_count": len(payload.get("options", [])),
                    "recommendation": payload.get("recommendation", ""),
                    "timeline_data": json.dumps(payload, ensure_ascii=False),
                    "created_at": payload.get("created_at", datetime.now().isoformat()),
                },
            )
            session.commit()
        finally:
            session.close()

    def load_simulation(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        self.ensure_tables()
        session = self._db_session()
        try:
            row = session.execute(text("SELECT timeline_data FROM decision_records WHERE simulation_id = :sid"), {"sid": simulation_id}).fetchone()
            if not row or not row[0]:
                return None
            payload = json.loads(row[0])
            return payload if isinstance(payload, dict) else None
        except Exception:
            return None
        finally:
            session.close()

    def list_simulations(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        self.ensure_tables()
        session = self._db_session()
        try:
            rows = session.execute(
                text(
                    """
                    SELECT simulation_id, question, options_count, recommendation, created_at
                    FROM decision_records
                    WHERE user_id = :uid
                    ORDER BY id DESC
                    LIMIT :limit_count
                    """
                ),
                {"uid": user_id, "limit_count": max(1, min(limit, 100))},
            ).fetchall()
            results: List[Dict[str, Any]] = []
            for row in rows:
                results.append(
                    {
                        "simulation_id": str(row[0] or ""),
                        "question": str(row[1] or ""),
                        "options_count": int(row[2] or 0),
                        "recommendation": str(row[3] or ""),
                        "created_at": str(row[4] or ""),
                    }
                )
            return results
        except Exception:
            return []
        finally:
            session.close()

    def create_parallel_life_branch(self, user_id: str, simulation_id: str, branch_id: str) -> Dict[str, Any]:
        self.ensure_tables()
        record = self.load_simulation(simulation_id)
        if not record:
            raise ValueError("未找到对应的决策推演记录")

        branch = None
        for option in record.get("options", []):
            if option.get("branch_agent_id") == branch_id or option.get("option_id") == branch_id:
                branch = option
                break
        if branch is None:
            raise ValueError("未找到对应的分支")

        timeline = list(branch.get("timeline") or [])
        scenario_id = f"pl_{uuid.uuid4().hex[:12]}"
        nodes: List[Dict[str, Any]] = []
        for index, item in enumerate(timeline[:3], start=1):
            key_people = item.get("key_people") or []
            person_hint = key_people[0] if key_people else "关键人物"
            nodes.append(
                {
                    "id": f"scene_{index}",
                    "type": "choice",
                    "text": item.get("event", ""),
                    "options": [
                        {
                            "id": f"A{index}",
                            "text": "继续沿着这条分支推进",
                            "sub": f"保持 {branch.get('branch_strategy', '当前策略')} 的节奏，并处理 {person_hint} 带来的影响",
                            "delta": {
                                "emotion": 8,
                                "finance": int(round(item.get("impact_vector", {}).get("finance", 0.0) * 100)),
                                "social": int(round(item.get("impact_vector", {}).get("social", 0.0) * 100)),
                                "health": int(round(item.get("impact_vector", {}).get("health", 0.0) * 100)),
                                "growth": int(round(item.get("impact_vector", {}).get("growth", 0.0) * 100)),
                                "confidence": int(round((item.get("execution_confidence", 0.5) - 0.5) * 100)),
                                "stress": int(round(item.get("impact_vector", {}).get("stress", 0.0) * 100)),
                            },
                            "next": f"scene_{index + 1}" if index < min(3, len(timeline)) else "reflection",
                        },
                        {
                            "id": f"B{index}",
                            "text": "谨慎推进，先降低损耗",
                            "sub": "保留这条路的方向，但控制资源消耗和压力上升",
                            "delta": {
                                "emotion": 4,
                                "finance": max(-4, int(round(item.get("impact_vector", {}).get("finance", 0.0) * 60))),
                                "social": max(-3, int(round(item.get("impact_vector", {}).get("social", 0.0) * 60))),
                                "health": 4,
                                "growth": max(2, int(round(item.get("impact_vector", {}).get("growth", 0.0) * 60))),
                                "confidence": 3,
                                "stress": -5,
                            },
                            "next": f"scene_{index + 1}" if index < min(3, len(timeline)) else "reflection",
                        },
                    ],
                    "next": f"scene_{index + 1}" if index < min(3, len(timeline)) else "reflection",
                }
            )

        nodes.append(
            {
                "id": "reflection",
                "type": "free_input",
                "text": "如果真走这条路，你最担心付出的代价是什么？又最想守住什么？",
                "options": [],
                "next": "ending_choice",
            }
        )
        nodes.append(
            {
                "id": "ending_choice",
                "type": "choice",
                "text": "走完这一轮体验后，你更想怎样定义这条路？",
                "options": [
                    {
                        "id": "A_end",
                        "text": "这是我愿意认真投入的一条路",
                        "sub": "说明这条分支和你的真实偏好较匹配",
                        "delta": {"emotion": 10, "finance": 5, "social": 6, "health": 2, "growth": 12, "confidence": 12, "stress": -3},
                        "next": "ending",
                    },
                    {
                        "id": "B_end",
                        "text": "这条路有吸引力，但我需要更多缓冲",
                        "sub": "说明你对方向有兴趣，但执行和资源仍是阻力",
                        "delta": {"emotion": 2, "finance": 2, "social": 2, "health": 3, "growth": 4, "confidence": 4, "stress": -1},
                        "next": "ending",
                    },
                ],
                "next": "ending",
            }
        )

        scenario = {
            "scenario_id": scenario_id,
            "simulation_id": simulation_id,
            "branch_id": branch.get("branch_agent_id") or branch.get("option_id"),
            "source_question": record.get("question", ""),
            "title": branch.get("title", "平行人生分支体验"),
            "subtitle": branch.get("branch_strategy", ""),
            "theme": "#0b1830",
            "accent": "#5aa9ff",
            "cover_emoji": "◎",
            "intro": f"这是一条来自决策图谱舞台的分支体验。你将沿着“{branch.get('title', '')}”走几步，系统会根据你的行为更新真实决策画像。",
            "nodes": nodes,
            "endings": [
                {"condition": "match_high", "title": "高匹配分支", "text": "你在这条路上的选择与行为表现说明，它很可能是真正适合你的方向。", "badge": "分支匹配高"},
                {"condition": "balanced", "title": "保留观察", "text": "你对这条路有兴趣，但现实约束和执行负担仍然需要进一步校准。", "badge": "继续观察"},
            ],
            "branch_context": branch,
        }

        session = self._db_session()
        try:
            session.execute(
                text(
                    """
                    INSERT INTO future_os_branch_scenarios
                        (scenario_id, simulation_id, branch_id, user_id, payload_json, created_at)
                    VALUES
                        (:scenario_id, :simulation_id, :branch_id, :user_id, :payload_json, :created_at)
                    ON DUPLICATE KEY UPDATE payload_json = VALUES(payload_json), created_at = VALUES(created_at)
                    """
                ),
                {
                    "scenario_id": scenario_id,
                    "simulation_id": simulation_id,
                    "branch_id": scenario["branch_id"],
                    "user_id": user_id,
                    "payload_json": json.dumps(scenario, ensure_ascii=False),
                    "created_at": datetime.now().isoformat(),
                },
            )
            session.commit()
        finally:
            session.close()
        return scenario

    def _load_branch_scenario(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        self.ensure_tables()
        session = self._db_session()
        try:
            row = session.execute(text("SELECT payload_json FROM future_os_branch_scenarios WHERE scenario_id = :sid"), {"sid": scenario_id}).fetchone()
            if not row or not row[0]:
                return None
            payload = json.loads(row[0])
            return payload if isinstance(payload, dict) else None
        except Exception:
            return None
        finally:
            session.close()

    def complete_parallel_life(
        self,
        user_id: str,
        scenario_id: str,
        simulation_id: str,
        branch_id: str,
        final_stats: Dict[str, float],
        choices: Optional[List[Dict[str, Any]]] = None,
        emotion_feedback: Optional[str] = None,
        free_text: str = "",
    ) -> Dict[str, Any]:
        self.ensure_tables()
        choices = choices or []
        profile = self._derive_profile_from_history(user_id)
        avg_latency_ms = avg([float(item.get("choice_time_ms", 6000)) for item in choices], 6000)
        reversal_count = sum(1 for item in choices if str(item.get("option_id", "")).startswith("B"))
        growth_signal = clamp((float(final_stats.get("growth", 50)) + 100) / 200)
        finance_signal = clamp((float(final_stats.get("finance", 50)) + 100) / 200)
        social_signal = clamp((float(final_stats.get("social", 50)) + 100) / 200)
        stress_signal = clamp((float(final_stats.get("stress", 30)) + 100) / 200)

        behavior_profile = {
            "actual_risk_tolerance": round(clamp(0.45 + (1 - stress_signal) * 0.18 + (0.08 if reversal_count <= 1 else -0.06)), 3),
            "actual_social_dependency": round(clamp(0.42 + social_signal * 0.32), 3),
            "actual_execution_stability": round(clamp(0.58 - min(0.18, avg_latency_ms / 30000) - reversal_count * 0.04), 3),
            "actual_growth_bias": round(clamp(0.40 + growth_signal * 0.34), 3),
            "actual_loss_aversion": round(clamp(0.52 + max(0.0, 0.65 - finance_signal) * 0.28), 3),
            "actual_recovery_after_setback": round(clamp(0.48 + (1 - stress_signal) * 0.24), 3),
        }

        updated_profile = {
            "risk_tolerance": round((profile["risk_tolerance"] * 0.7) + (behavior_profile["actual_risk_tolerance"] * 0.3), 3),
            "delay_discount": round(profile["delay_discount"], 3),
            "social_dependency": round((profile["social_dependency"] * 0.72) + (behavior_profile["actual_social_dependency"] * 0.28), 3),
            "execution_stability": round((profile["execution_stability"] * 0.68) + (behavior_profile["actual_execution_stability"] * 0.32), 3),
            "growth_bias": round((profile["growth_bias"] * 0.7) + (behavior_profile["actual_growth_bias"] * 0.3), 3),
            "loss_aversion": round((profile["loss_aversion"] * 0.74) + (behavior_profile["actual_loss_aversion"] * 0.26), 3),
            "ambiguity_tolerance": round((profile["ambiguity_tolerance"] * 0.75) + ((1 - behavior_profile["actual_loss_aversion"]) * 0.25), 3),
        }
        self._save_profile(user_id, updated_profile)

        scenario = self._load_branch_scenario(scenario_id) or {}
        branch_context = scenario.get("branch_context", {})
        summary = {
            "scenario_id": scenario_id,
            "simulation_id": simulation_id,
            "branch_id": branch_id,
            "user_id": user_id,
            "final_stats": final_stats,
            "choices": choices,
            "emotion_feedback": emotion_feedback or "",
            "free_text": free_text,
            "behavior_profile": behavior_profile,
            "updated_profile": updated_profile,
            "created_at": datetime.now().isoformat(),
        }

        session = self._db_session()
        try:
            session.execute(
                text(
                    """
                    INSERT INTO future_os_parallel_runs
                        (scenario_id, simulation_id, branch_id, user_id, payload_json, created_at)
                    VALUES
                        (:scenario_id, :simulation_id, :branch_id, :user_id, :payload_json, :created_at)
                    """
                ),
                {
                    "scenario_id": scenario_id,
                    "simulation_id": simulation_id,
                    "branch_id": branch_id,
                    "user_id": user_id,
                    "payload_json": json.dumps(summary, ensure_ascii=False),
                    "created_at": summary["created_at"],
                },
            )
            session.commit()
        finally:
            session.close()

        self._write_parallel_feedback_to_graph(user_id, branch_context, behavior_profile, emotion_feedback or "", free_text, scenario_id)
        next_hint = "这条路与你的真实行为较匹配，可以回到决策图谱舞台继续展开。" if behavior_profile["actual_execution_stability"] >= 0.52 else "这条路对你有吸引力，但执行阻力较大，建议回到图谱重新调低节奏。"
        return {"summary": summary, "behavior_profile": behavior_profile, "updated_profile": updated_profile, "next_hint": next_hint}

    def _write_parallel_feedback_to_graph(
        self,
        user_id: str,
        branch_context: Dict[str, Any],
        behavior_profile: Dict[str, float],
        emotion_feedback: str,
        free_text: str,
        scenario_id: str,
    ) -> None:
        try:
            info_kg = InformationKnowledgeGraph(user_id)
        except Exception:
            return
        try:
            branch_title = str(branch_context.get("title") or "分支体验")
            preference_node = f"偏好:{branch_title}"
            behavior_node = "模式:执行稳定性较高" if behavior_profile["actual_execution_stability"] >= 0.52 else "模式:执行阻力偏高"
            info_kg.add_information(preference_node, "concept", "preference", 0.82, {"scenario_id": scenario_id})
            info_kg.add_information(behavior_node, "pattern", "behavior", 0.78, {"scenario_id": scenario_id})
            source_id = f"parallel_{scenario_id}"
            info_kg.add_source("parallel_life", source_id, int(datetime.now().timestamp()), {"emotion_feedback": emotion_feedback, "free_text": free_text[:180]})
            info_kg.add_source_relationship(preference_node, source_id, "RECORDED_IN", 0.82)
            info_kg.add_source_relationship(behavior_node, source_id, "RECORDED_IN", 0.78)
            info_kg.add_information_relationship(preference_node, behavior_node, "INFLUENCES", {"weight": 0.72})
            for person_name in (branch_context.get("key_people") or [])[:2]:
                info_kg.add_information_relationship(str(person_name), preference_node, "INFLUENCES", {"weight": 0.66})
        except Exception:
            pass
        finally:
            try:
                info_kg.close()
            except Exception:
                pass
