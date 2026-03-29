"""
平行人生 · 决策游戏 API v2
事件链结构：玩家扮演主角，连续做 4-5 个决策，属性值实时变化，走向不同结局
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

router = APIRouter(prefix="/api/game/parallel-life", tags=["平行人生游戏"])

# ── 属性变化类型 ─────────────────────────────────────────────────────────────
# emotion: 情绪值 (-100 ~ 100, 初始 50)
# finance: 财务值 (-100 ~ 100, 初始 50)
# social:  社交值 (-100 ~ 100, 初始 50)

CHAPTERS = [
    {
        "id": "ch_career_start",
        "title": "职场元年",
        "subtitle": "你刚刚毕业，站在人生的第一个岔路口",
        "theme": "#1a1a3e",
        "accent": "#7C3AED",
        "cover_emoji": "🏢",
        "intro": "大学毕业，你拿到了两个 offer。\n一个是大厂，稳定但压力大；\n一个是创业公司，自由但充满未知。\n\n接下来的每一个选择，都将改变你的人生轨迹。",
        "nodes": [
            {
                "id": "n1",
                "type": "choice",
                "text": "毕业第一天，你面临第一个选择：",
                "options": [
                    {
                        "id": "A",
                        "text": "加入大厂，稳定月薪 18k",
                        "sub": "五险一金，晋升通道清晰，但加班是常态",
                        "delta": {"emotion": -5, "finance": 20, "social": 5},
                        "next": "n2a"
                    },
                    {
                        "id": "B",
                        "text": "加入创业公司，月薪 12k + 期权",
                        "sub": "方向很新，团队年轻，但融资只到 B 轮",
                        "delta": {"emotion": 10, "finance": -5, "social": 15},
                        "next": "n2b"
                    }
                ]
            },
            {
                "id": "n2a",
                "type": "choice",
                "text": "入职三个月，你发现大厂的工作节奏比想象中更快。\n\n周五晚上 10 点，leader 突然发来消息：\n"周末能来加个班吗，项目有点急。"",
                "options": [
                    {
                        "id": "A",
                        "text": "答应加班，展现积极态度",
                        "sub": "牺牲周末，但在 leader 面前留下好印象",
                        "delta": {"emotion": -15, "finance": 5, "social": -5},
                        "next": "n3a"
                    },
                    {
                        "id": "B",
                        "text": "委婉拒绝，说有事",
                        "sub": "保住了周末，但心里有点忐忑",
                        "delta": {"emotion": 10, "finance": 0, "social": 5},
                        "next": "n3b"
                    }
                ]
            },
            {
                "id": "n2b",
                "type": "choice",
                "text": "创业公司的节奏很快，你每天都在学新东西。\n\n但三个月后，公司融资遇到了麻烦，\nCEO 在全员会上说：\n"接下来两个月，大家工资打八折，共渡难关。"",
                "options": [
                    {
                        "id": "A",
                        "text": "接受降薪，相信公司能撑过去",
                        "sub": "留下来，但生活压力变大了",
                        "delta": {"emotion": -10, "finance": -15, "social": 10},
                        "next": "n3c"
                    },
                    {
                        "id": "B",
                        "text": "开始悄悄投简历，留条后路",
                        "sub": "理性应对，但有点愧疚",
                        "delta": {"emotion": 5, "finance": 5, "social": -10},
                        "next": "n3d"
                    }
                ]
            },
            {
                "id": "n3a",
                "type": "choice",
                "text": "你连续加了三个周末的班，项目顺利上线。\n\nleader 在组会上当众表扬了你，\n并暗示年底绩效会给你 A。\n\n但你的身体开始发出警告——\n最近总是失眠，周末也无法放松。",
                "options": [
                    {
                        "id": "A",
                        "text": "继续保持这个节奏，冲刺年底绩效",
                        "sub": "拼一把，争取晋升机会",
                        "delta": {"emotion": -20, "finance": 15, "social": -10},
                        "next": "n4"
                    },
                    {
                        "id": "B",
                        "text": "主动和 leader 谈，希望调整工作节奏",
                        "sub": "可能影响绩效，但身体更重要",
                        "delta": {"emotion": 15, "finance": -5, "social": 5},
                        "next": "n4"
                    }
                ]
            },
            {
                "id": "n3b",
                "type": "choice",
                "text": "你保住了周末，但发现组里其他人都去加班了。\n\n一个月后，绩效评定，你拿到了 B+，\n而那个周末加班的同事拿到了 A。\n\n你的朋友说：'要不要考虑换个部门？'",
                "options": [
                    {
                        "id": "A",
                        "text": "申请内部转岗，换个更适合自己的团队",
                        "sub": "需要重新适应，但可能找到更好的节奏",
                        "delta": {"emotion": 10, "finance": 0, "social": 15},
                        "next": "n4"
                    },
                    {
                        "id": "B",
                        "text": "留在原部门，调整心态继续做",
                        "sub": "稳定，但需要接受现实",
                        "delta": {"emotion": -5, "finance": 5, "social": 0},
                        "next": "n4"
                    }
                ]
            },
            {
                "id": "n3c",
                "type": "choice",
                "text": "你选择留下来，两个月后公司融资成功，\n工资恢复正常，CEO 还给每人发了一笔奖金。\n\n但你发现，自己的存款已经见底了，\n房租下个月就要到期。",
                "options": [
                    {
                        "id": "A",
                        "text": "找家人借钱，先渡过难关",
                        "sub": "解决了眼前问题，但有点不好意思",
                        "delta": {"emotion": -10, "finance": 15, "social": -5},
                        "next": "n4"
                    },
                    {
                        "id": "B",
                        "text": "找合租室友，降低生活成本",
                        "sub": "省钱，还认识了新朋友",
                        "delta": {"emotion": 5, "finance": 10, "social": 20},
                        "next": "n4"
                    }
                ]
            },
            {
                "id": "n3d",
                "type": "choice",
                "text": "你一边在公司上班，一边悄悄投简历。\n\n两周后，你收到了一家中型公司的 offer，\n月薪 15k，比现在高，但方向不如现在有趣。\n\n就在这时，你的 CEO 找你谈话，\n说公司想给你升职加薪。",
                "options": [
                    {
                        "id": "A",
                        "text": "接受新 offer，跳槽走人",
                        "sub": "薪资更高，但放弃了期权",
                        "delta": {"emotion": 5, "finance": 20, "social": -10},
                        "next": "n4"
                    },
                    {
                        "id": "B",
                        "text": "留下来，接受升职",
                        "sub": "赌一把，相信公司的未来",
                        "delta": {"emotion": 15, "finance": 5, "social": 10},
                        "next": "n4"
                    }
                ]
            },
            {
                "id": "n4",
                "type": "choice",
                "text": "工作一年了。\n\n你的大学同学约你周末聚会，\n说大家都很想你，但你手头有个项目还没做完。",
                "options": [
                    {
                        "id": "A",
                        "text": "去聚会，项目周一再说",
                        "sub": "久违的放松，和老朋友叙旧",
                        "delta": {"emotion": 20, "finance": -5, "social": 25},
                        "next": "ending"
                    },
                    {
                        "id": "B",
                        "text": "婉拒聚会，先把项目做完",
                        "sub": "对自己负责，但有点遗憾",
                        "delta": {"emotion": -10, "finance": 10, "social": -15},
                        "next": "ending"
                    }
                ]
            }
        ],
        "endings": [
            {
                "condition": "emotion_high",
                "threshold": {"emotion": 40},
                "title": "活得很通透",
                "text": "一年下来，你学会了在工作和生活之间找到平衡。\n薪资不是最高的，但你每天都能睡个好觉。\n朋友说你气色越来越好了。",
                "badge": "生活家"
            },
            {
                "condition": "finance_high",
                "threshold": {"finance": 40},
                "title": "职场新星",
                "text": "一年下来，你的账户余额比同龄人多了不少。\n代价是你的朋友圈越来越小，\n但你告诉自己，这只是暂时的。",
                "badge": "拼命三郎"
            },
            {
                "condition": "social_high",
                "threshold": {"social": 40},
                "title": "人脉达人",
                "text": "一年下来，你认识了很多有趣的人。\n你的人脉网络在悄悄扩张，\n机会也开始主动找上门来。",
                "badge": "社交达人"
            },
            {
                "condition": "balanced",
                "threshold": {},
                "title": "稳健前行",
                "text": "一年下来，你没有特别突出，\n但也没有什么遗憾。\n你在慢慢找到属于自己的节奏。",
                "badge": "均衡发展"
            }
        ]
    }
]


# ── 请求模型 ─────────────────────────────────────────────────────────────────

class ChoiceRequest(BaseModel):
    user_id: str
    chapter_id: str
    node_id: str
    option_id: str
    choice_time_ms: int
    current_stats: Dict[str, int]  # {"emotion": 50, "finance": 50, "social": 50}

class FinishRequest(BaseModel):
    user_id: str
    chapter_id: str
    final_stats: Dict[str, int]
    choices: List[Dict[str, Any]]  # [{node_id, option_id, choice_time_ms}, ...]

# ── 接口 ─────────────────────────────────────────────────────────────────────

@router.get("/chapters")
async def get_chapters():
    """获取所有关卡列表（不含节点详情）"""
    preview = []
    for ch in CHAPTERS:
        preview.append({
            "id": ch["id"],
            "title": ch["title"],
            "subtitle": ch["subtitle"],
            "theme": ch["theme"],
            "accent": ch["accent"],
            "cover_emoji": ch["cover_emoji"],
            "node_count": len([n for n in ch["nodes"] if n["type"] == "choice"])
        })
    return {"success": True, "data": preview}


@router.get("/chapter/{chapter_id}")
async def get_chapter(chapter_id: str):
    """获取关卡完整数据（含所有节点）"""
    ch = next((c for c in CHAPTERS if c["id"] == chapter_id), None)
    if not ch:
        return {"success": False, "message": "关卡不存在"}
    return {"success": True, "data": ch}


@router.post("/choice")
async def record_choice(req: ChoiceRequest):
    """记录单次选择，返回下一节点 ID 和属性变化"""
    ch = next((c for c in CHAPTERS if c["id"] == req.chapter_id), None)
    if not ch:
        return {"success": False, "message": "关卡不存在"}

    node = next((n for n in ch["nodes"] if n["id"] == req.node_id), None)
    if not node:
        return {"success": False, "message": "节点不存在"}

    option = next((o for o in node["options"] if o["id"] == req.option_id), None)
    if not option:
        return {"success": False, "message": "选项不存在"}

    # 计算新属性值
    new_stats = dict(req.current_stats)
    for k, v in option["delta"].items():
        new_stats[k] = max(-100, min(100, new_stats.get(k, 50) + v))

    return {
        "success": True,
        "data": {
            "next_node_id": option["next"],
            "delta": option["delta"],
            "new_stats": new_stats,
            "option_text": option["text"]
        }
    }


@router.post("/finish")
async def finish_chapter(req: FinishRequest):
    """完成关卡，返回结局和决策画像，同时保存训练数据"""
    ch = next((c for c in CHAPTERS if c["id"] == req.chapter_id), None)
    if not ch:
        return {"success": False, "message": "关卡不存在"}

    # 判断结局
    stats = req.final_stats
    ending = _pick_ending(ch["endings"], stats)

    # 保存训练数据
    _save_training_data(req, ch, ending)

    # 生成决策画像
    profile = _build_profile(req.choices, stats)

    return {
        "success": True,
        "data": {
            "ending": ending,
            "final_stats": stats,
            "profile": profile
        }
    }


def _pick_ending(endings: List[Dict], stats: Dict[str, int]) -> Dict:
    """根据最终属性值选择结局"""
    # 找最高属性
    best_key = max(stats, key=lambda k: stats[k])
    best_val = stats[best_key]

    for e in endings:
        if e["condition"] == "emotion_high" and best_key == "emotion" and best_val >= e["threshold"].get("emotion", 40):
            return e
        if e["condition"] == "finance_high" and best_key == "finance" and best_val >= e["threshold"].get("finance", 40):
            return e
        if e["condition"] == "social_high" and best_key == "social" and best_val >= e["threshold"].get("social", 40):
            return e

    return next(e for e in endings if e["condition"] == "balanced")


def _build_profile(choices: List[Dict], stats: Dict[str, int]) -> Dict:
    """从选择行为中提炼决策画像"""
    if not choices:
        return {}

    avg_time = sum(c.get("choice_time_ms", 5000) for c in choices) / len(choices)
    fast_choices = sum(1 for c in choices if c.get("choice_time_ms", 5000) < 4000)
    risk_choices = sum(1 for c in choices if c.get("option_id") == "B")

    return {
        "decision_speed": "fast" if avg_time < 5000 else "slow",
        "risk_tendency": "risk_seeking" if risk_choices > len(choices) / 2 else "risk_averse",
        "emotion_priority": stats.get("emotion", 50),
        "finance_priority": stats.get("finance", 50),
        "social_priority": stats.get("social", 50),
        "fast_choice_ratio": round(fast_choices / len(choices), 2)
    }


def _save_training_data(req: FinishRequest, ch: Dict, ending: Dict):
    """将游戏选择转换为 LoRA 训练对话存入数据库"""
    try:
        from backend.database.connection import db_connection
        from backend.database.models import ConversationHistory

        db = db_connection.get_session()
        now = datetime.utcnow()

        # 构造一条高质量的决策对话训练样本
        choices_desc = []
        for c in req.choices:
            node = next((n for n in ch["nodes"] if n["id"] == c.get("node_id")), None)
            if node:
                opt = next((o for o in node["options"] if o["id"] == c.get("option_id")), None)
                if opt:
                    choices_desc.append(f"面对"{node['text'][:30]}..."，选择了"{opt['text']}"")

        user_msg = f"我玩了一个叫"{ch['title']}"的人生模拟游戏。" + "；".join(choices_desc[:3]) + "。"
        assistant_msg = (
            f"从你的选择来看，{ending['text'][:60]}。"
            f"你的决策风格偏向{'冒险探索' if req.final_stats.get('social', 50) > 50 else '稳健保守'}，"
            f"在情绪、财务、社交三个维度上，你最看重的是"
            f"{'情绪健康' if req.final_stats.get('emotion', 50) >= max(req.final_stats.values()) else '财务安全' if req.final_stats.get('finance', 50) >= max(req.final_stats.values()) else '社交关系'}。"
        )

        db.add(ConversationHistory(
            user_id=req.user_id, role="user", content=user_msg,
            timestamp=now, session_id=f"game_{req.chapter_id}"
        ))
        db.add(ConversationHistory(
            user_id=req.user_id, role="assistant", content=assistant_msg,
            timestamp=now, session_id=f"game_{req.chapter_id}"
        ))
        db.commit()
        db.close()
    except Exception as e:
        print(f"[游戏] 保存训练数据失败: {e}")


# 保留旧接口兼容性
@router.get("/scenarios")
async def get_scenarios_compat():
    return await get_chapters()
