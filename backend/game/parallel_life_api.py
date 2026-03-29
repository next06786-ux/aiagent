"""
平行人生游戏 API
收集用户决策偏好数据，用于 LoRA 训练和 profile 更新
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

router = APIRouter(prefix="/api/game/parallel-life", tags=["平行人生游戏"])

# ── 场景库 ──────────────────────────────────────────────────────────────────

SCENARIOS = [
    {
        "id": "career_fork_001",
        "type": "risk_career",
        "title": "职业岔路口",
        "theme_color": "#6B48FF",
        "bg_gradient": ["#1a1a2e", "#16213e"],
        "scene_text": "毕业季，你同时拿到了两个 offer。\n\n时间不多，明天就要给答复。",
        "options": [
            {
                "id": "A",
                "label": "大厂稳定岗",
                "detail": "月薪 18k，五险一金，加班不多，晋升通道清晰",
                "color": "#0A59F7",
                "icon": "shield"
            },
            {
                "id": "B",
                "label": "早期创业公司",
                "detail": "月薪 12k，期权诱人，方向很新，但融资只到 B 轮",
                "color": "#FF9500",
                "icon": "rocket"
            }
        ],
        "outcomes": {
            "A": [
                {"month": 3,  "text": "顺利通过试用期，工作节奏稳定，开始还房贷"},
                {"month": 6,  "text": "负责了一个小模块，得到 leader 认可，加薪 8%"},
                {"month": 12, "text": "年终绩效 B+，公司传出裁员消息，你的部门暂时安全"}
            ],
            "B": [
                {"month": 3,  "text": "产品上线，用户反馈不错，但融资进展比预期慢"},
                {"month": 6,  "text": "公司开始控制成本，你主动承担了更多职责"},
                {"month": 12, "text": "C 轮融资成功，期权价值翻了 3 倍，但竞争对手也来了"}
            ]
        },
        "followups": [
            {
                "id": "regret_if_fired",
                "text": "如果 A 公司一年后裁员了，你会后悔选 A 吗？",
                "type": "slider",
                "left_label": "完全不后悔",
                "right_label": "非常后悔"
            },
            {
                "id": "risk_tolerance",
                "text": "如果 B 公司的期权最终一文不值，你能接受吗？",
                "type": "slider",
                "left_label": "完全接受",
                "right_label": "难以接受"
            }
        ]
    },
    {
        "id": "life_vs_career_002",
        "type": "priority_life",
        "title": "爱情与事业",
        "theme_color": "#FF6B9D",
        "bg_gradient": ["#1a0a1e", "#2d1b33"],
        "scene_text": "你拿到了梦想中的工作机会。\n\n但公司在另一个城市，而你的伴侣不想异地。",
        "options": [
            {
                "id": "A",
                "label": "接受 offer，异地试试",
                "detail": "先去，两人约定一年后再做决定",
                "color": "#6B48FF",
                "icon": "plane"
            },
            {
                "id": "B",
                "label": "放弃 offer，留下来",
                "detail": "在本地继续找，感情第一",
                "color": "#00C853",
                "icon": "heart"
            }
        ],
        "outcomes": {
            "A": [
                {"month": 3,  "text": "工作很充实，但每周视频通话开始变少"},
                {"month": 6,  "text": "两人因为一件小事大吵，异地的裂缝开始显现"},
                {"month": 12, "text": "你升职了，但感情走到了十字路口，需要做一个更大的决定"}
            ],
            "B": [
                {"month": 3,  "text": "感情稳定，但你偶尔会想起那个 offer"},
                {"month": 6,  "text": "在本地找到了一份还不错的工作，薪资低一些"},
                {"month": 12, "text": "生活平稳，但那个梦想的机会偶尔还是会出现在脑海里"}
            ]
        },
        "followups": [
            {
                "id": "priority_weight",
                "text": "在你心里，事业和感情，哪个更重要？",
                "type": "slider",
                "left_label": "感情第一",
                "right_label": "事业第一"
            }
        ]
    },
    {
        "id": "invest_003",
        "type": "risk_finance",
        "title": "这笔钱怎么用",
        "theme_color": "#00C853",
        "bg_gradient": ["#0a1a0e", "#0d2b14"],
        "scene_text": "你手里有 5 万块存款。\n\n朋友找你入股他的小生意，说半年能回本。",
        "options": [
            {
                "id": "A",
                "label": "存银行，稳稳的",
                "detail": "年化 2.5%，安全，随时可取",
                "color": "#0A59F7",
                "icon": "bank"
            },
            {
                "id": "B",
                "label": "投朋友的项目",
                "detail": "预期回报 30%，但朋友没有创业经验",
                "color": "#FF9500",
                "icon": "invest"
            }
        ],
        "outcomes": {
            "A": [
                {"month": 3,  "text": "存款安全，朋友的生意开张了，看起来还不错"},
                {"month": 6,  "text": "利息到账 625 元，朋友说项目遇到了一些麻烦"},
                {"month": 12, "text": "本金完好，朋友的项目关闭了，他损失了不少"}
            ],
            "B": [
                {"month": 3,  "text": "项目开张，你参与了一些决策，很有参与感"},
                {"month": 6,  "text": "遇到了资金周转问题，朋友向你借了更多"},
                {"month": 12, "text": "项目最终亏损，你拿回了 3 万，损失了 2 万，友情也有些裂痕"}
            ]
        },
        "followups": [
            {
                "id": "loss_tolerance",
                "text": "如果投资亏了 40%，你的第一反应是？",
                "type": "slider",
                "left_label": "认了，继续",
                "right_label": "后悔不已"
            }
        ]
    }
]

# ── 数据模型 ─────────────────────────────────────────────────────────────────

class GameResultRequest(BaseModel):
    user_id: str
    scenario_id: str
    scenario_type: str
    initial_choice: str
    choice_time_ms: int
    regret_triggered: bool
    final_choice: str
    followup_answers: Dict[str, float]

# ── 接口 ─────────────────────────────────────────────────────────────────────

@router.get("/scenarios")
async def get_scenarios():
    """获取所有场景（不含结局，防止剧透）"""
    preview = []
    for s in SCENARIOS:
        preview.append({
            "id": s["id"],
            "type": s["type"],
            "title": s["title"],
            "theme_color": s["theme_color"],
            "bg_gradient": s["bg_gradient"],
            "scene_text": s["scene_text"],
            "options": s["options"],
            "followups": s["followups"]
        })
    return {"success": True, "data": preview}


@router.get("/scenario/{scenario_id}/outcomes")
async def get_outcomes(scenario_id: str, chosen: str):
    """选择后获取两条路的结局"""
    scenario = next((s for s in SCENARIOS if s["id"] == scenario_id), None)
    if not scenario:
        return {"success": False, "message": "场景不存在"}
    return {
        "success": True,
        "data": {
            "chosen": chosen,
            "outcomes": scenario["outcomes"]
        }
    }


@router.post("/result")
async def save_game_result(req: GameResultRequest):
    """
    保存游戏结果，同时：
    1. 更新用户 PersonalityProfile
    2. 生成 LoRA 训练对话对存入数据库
    """
    try:
        _update_profile(req)
        _save_training_data(req)
        return {"success": True, "message": "数据已保存"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def _update_profile(req: GameResultRequest):
    """根据游戏结果更新用户画像"""
    try:
        from backend.personality.personality_test import PersonalityTest
        pt = PersonalityTest()
        profile = pt.load_profile(req.user_id)
        if profile is None:
            return

        # 根据场景类型和选择更新对应维度
        if req.scenario_type == "risk_career":
            # B = 激进，A = 保守
            is_risk_seeking = req.final_choice == "B"
            regret = req.followup_answers.get("regret_if_fired", 0.5)
            # 后悔倾向高 → 更保守
            if is_risk_seeking and regret < 0.4:
                profile.risk_preference = "risk_seeking"
            elif not is_risk_seeking and regret > 0.6:
                profile.risk_preference = "risk_averse"
            # 犹豫时间 > 10s → 慢决策
            if req.choice_time_ms > 10000:
                profile.decision_speed = min(profile.decision_speed + 0.3, 4.0)

        elif req.scenario_type == "priority_life":
            priority = req.followup_answers.get("priority_weight", 0.5)
            if priority < 0.35:
                profile.life_priority = "relationship_first"
            elif priority > 0.65:
                profile.life_priority = "career_first"

        elif req.scenario_type == "risk_finance":
            loss_tolerance = req.followup_answers.get("loss_tolerance", 0.5)
            if loss_tolerance < 0.35:
                profile.risk_preference = "risk_seeking"
            elif loss_tolerance > 0.65:
                profile.risk_preference = "risk_averse"

        pt.save_profile(profile)
    except Exception as e:
        print(f"[游戏] 更新 profile 失败: {e}")


def _save_training_data(req: GameResultRequest):
    """将游戏对话转换为 LoRA 训练格式存入数据库"""
    try:
        scenario = next((s for s in SCENARIOS if s["id"] == req.scenario_id), None)
        if not scenario:
            return

        chosen_opt = next((o for o in scenario["options"] if o["id"] == req.final_choice), None)
        other_opt  = next((o for o in scenario["options"] if o["id"] != req.final_choice), None)
        if not chosen_opt or not other_opt:
            return

        # 构造一条高质量的决策对话训练样本
        user_msg = (
            f"我面临一个选择：{chosen_opt['label']} 还是 {other_opt['label']}。"
            f"{chosen_opt['label']}的情况是：{chosen_opt['detail']}。"
            f"{other_opt['label']}的情况是：{other_opt['detail']}。"
            f"我倾向于选{chosen_opt['label']}，你觉得呢？"
        )

        regret = req.followup_answers.get("regret_if_fired", req.followup_answers.get("loss_tolerance", 0.5))
        risk_desc = "你愿意承担一定风险换取更大可能性" if req.final_choice == "B" else "你更看重稳定性和可预期的结果"
        regret_desc = "即使结果不理想，你也能接受自己的选择" if regret < 0.5 else "你对决策结果比较在意，后悔倾向较高"

        assistant_msg = (
            f"从你的选择来看，{risk_desc}。"
            f"{chosen_opt['label']}确实{chosen_opt['detail']}，"
            f"这与你当前的优先级比较匹配。"
            f"需要注意的是，{other_opt['label']}也有其价值，"
            f"但你选择了更符合自己判断的方向。{regret_desc}。"
        )

        from backend.database.connection import db_connection
        from backend.database.models import ConversationHistory
        db = db_connection.get_session()
        now = datetime.utcnow()

        db.add(ConversationHistory(
            user_id=req.user_id,
            role="user",
            content=user_msg,
            timestamp=now,
            session_id=f"game_{req.scenario_id}"
        ))
        db.add(ConversationHistory(
            user_id=req.user_id,
            role="assistant",
            content=assistant_msg,
            timestamp=now,
            session_id=f"game_{req.scenario_id}"
        ))
        db.commit()
        db.close()
        print(f"[游戏] 用户 {req.user_id} 训练数据已保存")
    except Exception as e:
        print(f"[游戏] 保存训练数据失败: {e}")
