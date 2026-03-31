# -*- coding: utf-8 -*-
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
        "cover_emoji": "W",
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
                "text": "入职三个月，你发现大厂的工作节奏比想象中更快。\n\n周五晚上 10 点，leader 突然发来消息：\n'周末能来加个班吗，项目有点急。'",
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
                "text": "创业公司的节奏很快，你每天都在学新东西。\n\n但三个月后，公司融资遇到了麻烦，\nCEO 在全员会上说：\n'接下来两个月，大家工资打八折，共渡难关。'",
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
    },
    {
        "id": "ch_relationship",
        "title": "感情抉择",
        "subtitle": "爱情与现实之间，你会怎么选",
        "theme": "#1a0a1e",
        "accent": "#FF6B9D",
        "cover_emoji": "",
        "intro": "你和伴侣在一起两年了。\n最近你拿到了一个很好的工作机会，\n但在另一个城市。\n\n接下来的每一个选择，\n都会影响你们的关系走向。",
        "nodes": [
            {"id": "r1", "type": "choice", "text": "你拿到了梦想中的 offer，但公司在另一个城市。伴侣说不想异地。你怎么选？",
             "options": [
                {"id": "A", "text": "接受 offer，试试异地", "sub": "追求事业，但感情面临考验", "delta": {"emotion": -10, "finance": 20, "social": -15}, "next": "r2a"},
                {"id": "B", "text": "放弃 offer，留下来", "sub": "感情第一，但可能会遗憾", "delta": {"emotion": 5, "finance": -5, "social": 15}, "next": "r2b"}
            ]},
            {"id": "r2a", "type": "choice", "text": "异地第一个月，你们约定每天视频。但你加班越来越多，有两天没联系。伴侣发消息说：'你是不是不在乎我了？'",
             "options": [
                {"id": "A", "text": "立刻打电话解释，承诺调整时间", "sub": "牺牲一些工作时间维护感情", "delta": {"emotion": 10, "finance": -5, "social": 15}, "next": "r3"},
                {"id": "B", "text": "回消息说最近真的很忙，希望理解", "sub": "坦诚但可能让对方失望", "delta": {"emotion": -5, "finance": 5, "social": -10}, "next": "r3"}
            ]},
            {"id": "r2b", "type": "choice", "text": "你留下来了，在本地找了一份还行的工作。但偶尔会想起那个 offer。一天晚上伴侣问你：'你后悔吗？'",
             "options": [
                {"id": "A", "text": "说实话：有时候会想，但不后悔", "sub": "坦诚面对，但可能让对方有压力", "delta": {"emotion": 5, "finance": 0, "social": 5}, "next": "r3"},
                {"id": "B", "text": "说不后悔，你比什么都重要", "sub": "让对方安心，但压抑了自己", "delta": {"emotion": -10, "finance": 0, "social": 10}, "next": "r3"}
            ]},
            {"id": "r3", "type": "free_input", "text": "回想一下你自己的感情经历，你觉得在感情和事业之间，最难的是什么？", "options": [], "next": "r4"},
            {"id": "r4", "type": "choice", "text": "半年过去了。你的一个朋友说：'我觉得你最近状态不太好，是不是该好好想想自己到底要什么？'",
             "options": [
                {"id": "A", "text": "认真反思，和伴侣深谈一次", "sub": "直面问题，可能会有转机", "delta": {"emotion": 15, "finance": 0, "social": 10}, "next": "r5"},
                {"id": "B", "text": "觉得朋友多管闲事，继续现状", "sub": "回避问题，但内心不安", "delta": {"emotion": -15, "finance": 5, "social": -10}, "next": "r5"}
            ]},
            {"id": "r5", "type": "choice", "text": "一年了。你和伴侣坐下来，认真聊了一次未来。",
             "options": [
                {"id": "A", "text": "一起制定一个两年计划，互相妥协", "sub": "成熟的选择，但需要双方都付出", "delta": {"emotion": 20, "finance": 5, "social": 20}, "next": "ending"},
                {"id": "B", "text": "承认彼此想要的不一样，和平分开", "sub": "痛苦但诚实的选择", "delta": {"emotion": -10, "finance": 10, "social": -5}, "next": "ending"}
            ]}
        ],
        "endings": [
            {"condition": "emotion_high", "threshold": {"emotion": 40}, "title": "感情守护者", "text": "你选择了用心经营感情，虽然事业上有些妥协，但你拥有一段真实而深厚的关系。", "badge": "真心守护"},
            {"condition": "finance_high", "threshold": {"finance": 40}, "title": "独立前行", "text": "你选择了事业优先，虽然感情上有遗憾，但你对自己的未来更有掌控感。", "badge": "独立自主"},
            {"condition": "social_high", "threshold": {"social": 40}, "title": "关系达人", "text": "你善于维护各种关系，在感情和社交之间找到了平衡。", "badge": "情商高手"},
            {"condition": "balanced", "threshold": {}, "title": "在路上", "text": "感情的事没有标准答案，你在慢慢找到属于自己的方式。", "badge": "成长中"}
        ]
    },
    {
        "id": "ch_growth",
        "title": "自我突破",
        "subtitle": "舒适区之外，是恐惧还是自由",
        "theme": "#0a1a0e",
        "accent": "#34d399",
        "cover_emoji": "",
        "intro": "你在一个稳定但无聊的岗位上待了两年。\n最近你开始思考：\n这真的是我想要的生活吗？\n\n改变，还是继续？",
        "nodes": [
            {"id": "g1", "type": "choice", "text": "周末，你刷到一个线下课程，主题是你一直感兴趣但从没尝试过的领域。报名费 3000 元。",
             "options": [
                {"id": "A", "text": "报名，给自己一个机会", "sub": "花钱但可能打开新世界", "delta": {"emotion": 15, "finance": -15, "social": 5}, "next": "g2a"},
                {"id": "B", "text": "算了，看看网上免费的就行", "sub": "省钱但可能又拖延了", "delta": {"emotion": -5, "finance": 5, "social": 0}, "next": "g2b"}
            ]},
            {"id": "g2a", "type": "choice", "text": "课程第一天，你发现班上的人都比你有经验。老师布置了一个作业，你完全不会做。",
             "options": [
                {"id": "A", "text": "硬着头皮问旁边的同学", "sub": "有点丢脸，但可能交到朋友", "delta": {"emotion": -5, "finance": 0, "social": 20}, "next": "g3"},
                {"id": "B", "text": "自己回去查资料，熬夜搞定", "sub": "独立解决，但很累", "delta": {"emotion": -10, "finance": 0, "social": -5}, "next": "g3"}
            ]},
            {"id": "g2b", "type": "choice", "text": "你在网上找了一堆免费教程，看了两天就没动力了。一个月后，你又回到了刷手机的日常。一天你的同事说：'你最近好像不太开心。'",
             "options": [
                {"id": "A", "text": "承认自己有点迷茫，想做点改变", "sub": "坦诚面对，可能得到支持", "delta": {"emotion": 5, "finance": 0, "social": 10}, "next": "g3"},
                {"id": "B", "text": "说没事，就是最近有点累", "sub": "掩饰真实感受", "delta": {"emotion": -10, "finance": 0, "social": -5}, "next": "g3"}
            ]},
            {"id": "g3", "type": "free_input", "text": "你有没有过想做但一直没做的事？是什么阻止了你？", "options": [], "next": "g4"},
            {"id": "g4", "type": "choice", "text": "三个月后，你有了一个小小的副业想法。但要启动它，你需要每天下班后花 2 小时。",
             "options": [
                {"id": "A", "text": "开始做，哪怕每天只推进一点", "sub": "辛苦但有方向感", "delta": {"emotion": 10, "finance": -5, "social": -10}, "next": "g5"},
                {"id": "B", "text": "等周末再说，平时太累了", "sub": "合理但可能又拖了", "delta": {"emotion": -5, "finance": 5, "social": 5}, "next": "g5"}
            ]},
            {"id": "g5", "type": "choice", "text": "半年过去了。你的生活和半年前相比，有了一些变化。你的家人问你：'你最近在忙什么？'",
             "options": [
                {"id": "A", "text": "兴奋地分享你的新尝试", "sub": "可能得到支持，也可能被泼冷水", "delta": {"emotion": 10, "finance": 0, "social": 15}, "next": "g6"},
                {"id": "B", "text": "轻描淡写地说没什么", "sub": "保护自己，但也错过了支持", "delta": {"emotion": -5, "finance": 0, "social": -5}, "next": "g6"}
            ]},
            {"id": "g6", "type": "choice", "text": "一年了。回头看，你觉得这一年最大的收获是什么？",
             "options": [
                {"id": "A", "text": "我学会了行动比想象重要", "sub": "成长型思维", "delta": {"emotion": 20, "finance": 5, "social": 10}, "next": "ending"},
                {"id": "B", "text": "我更了解自己想要什么了", "sub": "自我认知提升", "delta": {"emotion": 15, "finance": 0, "social": 5}, "next": "ending"}
            ]}
        ],
        "endings": [
            {"condition": "emotion_high", "threshold": {"emotion": 40}, "title": "内心富足", "text": "你选择了面对自己的真实需求，虽然过程不容易，但你的内心比一年前强大了很多。", "badge": "勇敢者"},
            {"condition": "finance_high", "threshold": {"finance": 40}, "title": "务实主义", "text": "你在稳定和探索之间找到了平衡，没有冲动，但也没有停下脚步。", "badge": "稳中求进"},
            {"condition": "social_high", "threshold": {"social": 40}, "title": "连接者", "text": "你在探索的过程中认识了很多新朋友，你的世界变大了。", "badge": "破圈达人"},
            {"condition": "balanced", "threshold": {}, "title": "探索中", "text": "改变不是一蹴而就的，你已经迈出了第一步，这就够了。", "badge": "起步者"}
        ]
    },
    {
        "id": "ch_money_game",
        "title": "财富迷局",
        "subtitle": "当机会和风险同时敲门",
        "theme": "#1a2e1a",
        "accent": "#FF9500",
        "cover_emoji": "$",
        "tarot_suit": "金币",
        "intro": "你攒了一笔钱，朋友拉你一起投资。\n听起来很靠谱，但你也听说过太多翻车的故事。\n\n是稳稳存银行，还是搏一把？",
        "nodes": [
            {"id": "n1", "type": "choice", "text": "朋友说有个项目，投10万半年翻倍。你怎么看？",
             "options": [
                 {"id": "A", "text": "投5万试试水", "sub": "控制风险，先小额参与", "delta": {"emotion": 5, "finance": -15, "social": 10}, "next": "n2a"},
                 {"id": "B", "text": "全部存定期", "sub": "稳妥第一，不碰不熟的东西", "delta": {"emotion": -5, "finance": 10, "social": -5}, "next": "n2b"}
             ]},
            {"id": "n2a", "type": "choice", "text": "第二个月，项目说要追加投资才能拿到更高回报。",
             "options": [
                 {"id": "A", "text": "再投5万，相信朋友", "sub": "加大投入，搏更高收益", "delta": {"emotion": -10, "finance": -20, "social": 5}, "next": "n3"},
                 {"id": "B", "text": "不追加，观望", "sub": "见好就收，保持冷静", "delta": {"emotion": 5, "finance": 0, "social": -5}, "next": "n3"}
             ]},
            {"id": "n2b", "type": "choice", "text": "存了定期后，你发现物价涨了不少，存款利率跑不赢通胀。",
             "options": [
                 {"id": "A", "text": "学习理财知识", "sub": "花时间研究基金和股票", "delta": {"emotion": 5, "finance": 5, "social": 0}, "next": "n3"},
                 {"id": "B", "text": "无所谓，安全最重要", "sub": "继续存银行，心安理得", "delta": {"emotion": 0, "finance": -5, "social": 0}, "next": "n3"}
             ]},
            {"id": "n3", "type": "free_input", "text": "回顾这段理财经历，你最大的感悟是什么？", "options": [], "next": "ending"}
        ],
        "endings": [
            {"condition": "finance_high", "threshold": {"finance": 40}, "title": "理财达人", "text": "你在风险和收益之间找到了平衡，开始建立自己的投资体系。", "badge": "金融新星"},
            {"condition": "emotion_high", "threshold": {"emotion": 40}, "title": "心态稳健", "text": "不管赚没赚到钱，你的心态一直很稳，这比什么都重要。", "badge": "淡定哥"},
            {"condition": "balanced", "threshold": {}, "title": "交了学费", "text": "有些教训只有亲身经历才能学到，这笔学费不亏。", "badge": "成长中"}
        ]
    },
    {
        "id": "ch_family_pressure",
        "title": "家庭期望",
        "subtitle": "父母的期望和自己的梦想",
        "theme": "#2e1a1a",
        "accent": "#FF6B9D",
        "cover_emoji": "H",
        "tarot_suit": "圣杯",
        "intro": "过年回家，父母又开始催你了。\n考公、结婚、买房...他们的期望像山一样压过来。\n\n你想走自己的路，但又不想让他们失望。",
        "nodes": [
            {"id": "n1", "type": "choice", "text": "妈妈说：'你同学都考上公务员了，你也去考吧。'",
             "options": [
                 {"id": "A", "text": "答应试试", "sub": "先报名，考不考再说", "delta": {"emotion": -10, "finance": -5, "social": 10}, "next": "n2a"},
                 {"id": "B", "text": "坦白说不想考", "sub": "直接表达自己的想法", "delta": {"emotion": 10, "finance": 0, "social": -15}, "next": "n2b"}
             ]},
            {"id": "n2a", "type": "choice", "text": "你报了名，但复习的时候完全看不进去。",
             "options": [
                 {"id": "A", "text": "硬着头皮考", "sub": "既然答应了就做到", "delta": {"emotion": -15, "finance": -5, "social": 5}, "next": "n3"},
                 {"id": "B", "text": "跟父母摊牌", "sub": "说清楚自己真正想做什么", "delta": {"emotion": 15, "finance": 0, "social": -10}, "next": "n3"}
             ]},
            {"id": "n2b", "type": "choice", "text": "爸妈很失望，家里气氛变得很僵。",
             "options": [
                 {"id": "A", "text": "用行动证明自己", "sub": "在自己的领域做出成绩", "delta": {"emotion": 10, "finance": 10, "social": -5}, "next": "n3"},
                 {"id": "B", "text": "找个折中方案", "sub": "既不完全听从也不完全对抗", "delta": {"emotion": 5, "finance": 0, "social": 5}, "next": "n3"}
             ]},
            {"id": "n3", "type": "free_input", "text": "如果能对父母说一句真心话，你会说什么？", "options": [], "next": "ending"}
        ],
        "endings": [
            {"condition": "emotion_high", "threshold": {"emotion": 40}, "title": "忠于自我", "text": "你选择了自己的路，虽然不容易，但你活得更真实了。", "badge": "真我"},
            {"condition": "social_high", "threshold": {"social": 40}, "title": "家和万事兴", "text": "你找到了和家人沟通的方式，理解是双向的。", "badge": "调和者"},
            {"condition": "balanced", "threshold": {}, "title": "在路上", "text": "家庭和自我之间的平衡，是一辈子的课题。", "badge": "成长中"}
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


@router.get("/random")
async def get_random_chapter():
    """随机返回一个关卡的完整数据"""
    import random
    ch = random.choice(CHAPTERS)
    return {"success": True, "data": ch}


@router.get("/generate")
async def generate_random_chapter():
    """调用大模型 API 随机生成全新关卡 — 3-4选项、6+节点、7维属性"""
    import random
    try:
        from openai import OpenAI
        import os, re
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            ch = random.choice(CHAPTERS)
            return {"success": True, "data": ch, "generated": False}

        themes = [
            "一段意外的旅行改变了你的人生轨迹",
            "你收到了一封来自陌生人的信，里面有一个改变命运的机会",
            "你的好朋友突然找你借一大笔钱",
            "公司裁员名单上出现了你的名字",
            "你在路上捡到了一个装满现金的钱包",
            "前任突然联系你说想复合",
            "室友做了一件让你很不舒服的事",
            "你发现了一个可以赚快钱但有风险的副业",
            "父母突然告诉你家里出了大事需要你回去",
            "你暗恋的人突然向你表白了",
            "你的创业项目终于拿到了第一笔投资",
            "毕业后你面临留在大城市还是回老家的选择",
            "你最好的朋友要移民了，问你要不要一起",
            "你被公司派到一个完全陌生的城市工作半年",
            "你发现自己的工作正在被AI取代",
            "一个很久没联系的老同学突然约你合伙创业",
        ]
        theme = random.choice(themes)
        accents = ["#7C3AED", "#FF6B9D", "#0A59F7", "#FF9500", "#00C853", "#E91E63", "#009688"]
        accent = random.choice(accents)

        client = OpenAI(api_key=api_key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
        prompt = f"""你是一个互动叙事游戏设计师。请根据以下主题生成一个丰富的决策游戏关卡。

主题：{theme}

严格要求：
1. 生成 6 个决策节点，形成深度分支树：n1 -> n2a/n2b/n2c -> n3a/n3b -> n4a/n4b -> n5 -> n6(free_input)
2. n1 必须有 3 个选项（A/B/C），分别通向 n2a/n2b/n2c
3. n2a/n2b/n2c 各有 2-3 个选项，通向 n3a 或 n3b
4. n3a/n3b 各有 2 个选项，通向 n4a 或 n4b
5. n4a/n4b 各有 2 个选项，通向 n5
6. n5 有 2 个选项，通向 n6
7. n6 是 free_input 节点，让玩家写感悟，next 为 "ending"
8. 每个选项的 delta 必须包含 7 个维度：emotion/finance/social/health/growth/confidence/stress，值范围 -25 到 25
9. 生成 4 个不同的结局
10. 所有文本要生动、接地气、有强烈代入感，像在讲一个真实的故事

返回 JSON：
{{
  "title": "4-6字标题",
  "subtitle": "10-15字副标题",
  "intro": "50-100字介绍，用\\n换行",
  "nodes": [
    {{"id": "n1", "type": "choice", "text": "生动的场景描述（30-50字）",
      "options": [
        {{"id": "A", "text": "选项（10-20字）", "sub": "补充说明", "delta": {{"emotion": 5, "finance": -10, "social": 5, "health": 0, "growth": 10, "confidence": 5, "stress": -5}}, "next": "n2a"}},
        {{"id": "B", "text": "选项", "sub": "说明", "delta": {{"emotion": -5, "finance": 10, "social": -5, "health": 0, "growth": -5, "confidence": -5, "stress": 10}}, "next": "n2b"}},
        {{"id": "C", "text": "选项", "sub": "说明", "delta": {{"emotion": 0, "finance": 0, "social": 10, "health": 5, "growth": 5, "confidence": 0, "stress": -10}}, "next": "n2c"}}
      ]}},
    ... 其余节点按上述结构生成 ...
    {{"id": "n6", "type": "free_input", "text": "深度反思问题", "options": [], "next": "ending"}}
  ],
  "endings": [
    {{"condition": "growth_high", "threshold": {{"growth": 30}}, "title": "结局标题", "text": "结局描述（30-50字）", "badge": "徽章名"}},
    {{"condition": "confidence_high", "threshold": {{"confidence": 30}}, "title": "标题", "text": "描述", "badge": "徽章"}},
    {{"condition": "emotion_high", "threshold": {{"emotion": 30}}, "title": "标题", "text": "描述", "badge": "徽章"}},
    {{"condition": "balanced", "threshold": {{}}, "title": "默认结局", "text": "描述", "badge": "徽章"}}
  ]
}}

只返回 JSON。"""

        response = client.chat.completions.create(
            model="qwen-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.95,
            max_tokens=3000
        )
        result_text = response.choices[0].message.content.strip()
        if result_text.startswith("```"):
            result_text = re.sub(r'^```\w*\n?', '', result_text)
            result_text = re.sub(r'\n?```$', '', result_text)

        chapter_data = json.loads(result_text)
        chapter_data["id"] = f"ch_gen_{random.randint(10000, 99999)}"
        chapter_data["theme"] = "#1a1a2e"
        chapter_data["accent"] = accent
        chapter_data["cover_emoji"] = random.choice(["?", "!", "*", "$", "#", "@", "&", "~"])
        if "intro" not in chapter_data:
            chapter_data["intro"] = chapter_data.get("subtitle", "")

        return {"success": True, "data": chapter_data, "generated": True}

    except Exception as e:
        print(f"[平行人生] AI生成关卡失败: {e}")
        import traceback
        traceback.print_exc()
        import random as rnd
        ch = rnd.choice(CHAPTERS)
        return {"success": True, "data": ch, "generated": False}


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


class FreeInputRequest(BaseModel):
    user_id: str
    chapter_id: str
    node_id: str
    user_text: str
    current_stats: Dict[str, int]


@router.post("/free-input")
async def record_free_input(req: FreeInputRequest):
    """记录自由文本输入，保存为高质量训练数据"""
    ch = next((c for c in CHAPTERS if c["id"] == req.chapter_id), None)
    if not ch:
        return {"success": False, "message": "关卡不存在"}

    node = next((n for n in ch["nodes"] if n["id"] == req.node_id), None)
    if not node or node.get("type") != "free_input":
        return {"success": False, "message": "节点不存在或类型不匹配"}

    # 保存为训练数据（自由表达是最高质量的个人偏好数据）
    try:
        from backend.database.connection import db_connection
        from backend.database.models import ConversationHistory

        db = db_connection.get_session()
        now = datetime.utcnow()
        db.add(ConversationHistory(
            user_id=req.user_id, role="user",
            content=f"[游戏自由表达] 问题：{node['text']} 回答：{req.user_text}",
            timestamp=now, session_id=f"game_{req.chapter_id}"
        ))
        db.add(ConversationHistory(
            user_id=req.user_id, role="assistant",
            content=f"感谢你的分享，这让我更了解你的想法和价值观。",
            timestamp=now, session_id=f"game_{req.chapter_id}"
        ))
        db.commit()
        db.close()
    except Exception as e:
        print(f"[游戏] 保存自由输入失败: {e}")

    return {
        "success": True,
        "data": {
            "next_node_id": node.get("next", "ending"),
            "delta": {"emotion": 0, "finance": 0, "social": 0},
            "new_stats": dict(req.current_stats)
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
                    choices_desc.append(f"面对[{node['text'][:30]}...]，选择了[{opt['text']}]")

        user_msg = f"我玩了一个叫[{ch['title']}]的人生模拟游戏。" + "；".join(choices_desc[:3]) + "。"
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
