"""
视觉主导的多模态融合算法
Vision-Dominant Multimodal Fusion
"""
import torch
import torch.nn as nn
from typing import Dict, Tuple, Optional
import numpy as np


class CrossModalAttention(nn.Module):
    """跨模态注意力机制"""
    
    def __init__(self, dim: int = 512, num_heads: int = 8):
        super().__init__()
        self.num_heads = num_heads
        self.attention = nn.MultiheadAttention(dim, num_heads, batch_first=True)
        self.norm = nn.LayerNorm(dim)
        
    def forward(self, query, key, value, weights=None):
        """
        Args:
            query: 查询特征 (batch, seq_len, dim)
            key: 键特征 (batch, seq_len, dim)
            value: 值特征 (batch, seq_len, dim)
            weights: 模态权重 (可选)
        """
        attn_output, attn_weights = self.attention(query, key, value)
        
        if weights is not None:
            attn_output = attn_output * weights.unsqueeze(-1)
        
        output = self.norm(query + attn_output)
        return output, attn_weights


class VisionDominantFusion(nn.Module):
    """视觉主导的多模态融合模型"""
    
    def __init__(
        self,
        vision_dim: int = 768,
        text_dim: int = 768,
        context_dim: int = 128,
        fusion_dim: int = 512,
        num_heads: int = 8
    ):
        super().__init__()
        
        # 特征投影层
        self.vision_proj = nn.Linear(vision_dim, fusion_dim)
        self.text_proj = nn.Linear(text_dim, fusion_dim)
        self.context_proj = nn.Linear(context_dim, fusion_dim)
        
        # 跨模态注意力
        self.cross_attention = CrossModalAttention(fusion_dim, num_heads)
        
        # 权重预测网络
        self.weight_predictor = nn.Sequential(
            nn.Linear(fusion_dim * 3, 256),
            nn.ReLU(),
            nn.Linear(256, 3),
            nn.Softmax(dim=-1)
        )
        
        # 融合层
        self.fusion_layer = nn.Sequential(
            nn.Linear(fusion_dim, fusion_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(fusion_dim, fusion_dim)
        )
        
    def compute_adaptive_weights(
        self,
        vision_feat: torch.Tensor,
        text_feat: torch.Tensor,
        context_feat: torch.Tensor
    ) -> torch.Tensor:
        """
        动态计算各模态权重
        视觉主导: alpha ∈ [0.6, 0.8]
        """
        # 拼接特征
        concat_feat = torch.cat([
            vision_feat.mean(dim=1),
            text_feat.mean(dim=1),
            context_feat.mean(dim=1)
        ], dim=-1)
        
        # 预测权重
        weights = self.weight_predictor(concat_feat)
        
        # 确保视觉权重主导
        weights[:, 0] = 0.6 + 0.2 * weights[:, 0]  # alpha ∈ [0.6, 0.8]
        weights[:, 1] = 0.1 + 0.1 * weights[:, 1]  # beta ∈ [0.1, 0.2]
        weights[:, 2] = 0.1 + 0.1 * weights[:, 2]  # gamma ∈ [0.1, 0.2]
        
        # 归一化
        weights = weights / weights.sum(dim=-1, keepdim=True)
        
        return weights
    
    def forward(
        self,
        vision_feat: torch.Tensor,
        text_feat: torch.Tensor,
        context_feat: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        前向传播
        
        Args:
            vision_feat: 视觉特征 (batch, seq_len, vision_dim)
            text_feat: 文本特征 (batch, seq_len, text_dim)
            context_feat: 上下文特征 (batch, context_dim)
        
        Returns:
            fused_feat: 融合特征 (batch, fusion_dim)
            weights: 模态权重 (batch, 3)
        """
        # 特征投影
        v_proj = self.vision_proj(vision_feat)
        t_proj = self.text_proj(text_feat)
        c_proj = self.context_proj(context_feat.unsqueeze(1))
        
        # 计算自适应权重
        weights = self.compute_adaptive_weights(v_proj, t_proj, c_proj)
        
        # 跨模态注意力融合
        # 以视觉为query
        fused_vt, _ = self.cross_attention(v_proj, t_proj, t_proj)
        fused_vc, _ = self.cross_attention(v_proj, c_proj, c_proj)
        
        # 加权融合
        fused = (
            weights[:, 0:1, None] * fused_vt +
            weights[:, 1:2, None] * t_proj +
            weights[:, 2:3, None] * fused_vc
        )
        
        # 池化
        fused = fused.mean(dim=1)
        
        # 最终融合层
        output = self.fusion_layer(fused)
        
        return output, weights


class HierarchicalTagGenerator(nn.Module):
    """层次化标签生成器"""
    
    def __init__(
        self,
        input_dim: int = 512,
        num_scenes: int = 20,
        num_objects: int = 100,
        num_actions: int = 50,
        num_intents: int = 30
    ):
        super().__init__()
        
        # L1: 场景分类
        self.scene_classifier = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, num_scenes)
        )
        
        # L2: 物体识别
        self.object_detector = nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(512, num_objects)
        )
        
        # L3: 行为理解
        self.action_recognizer = nn.Sequential(
            nn.Linear(input_dim + num_scenes, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, num_actions)
        )
        
        # L4: 意图推断
        self.intent_predictor = nn.Sequential(
            nn.Linear(input_dim + num_scenes + num_actions, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, num_intents)
        )
    
    def forward(self, fused_feat: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        生成层次化标签
        
        Args:
            fused_feat: 融合特征 (batch, input_dim)
        
        Returns:
            tags: 各层级标签预测
        """
        # L1: 场景
        scene_logits = self.scene_classifier(fused_feat)
        scene_probs = torch.softmax(scene_logits, dim=-1)
        
        # L2: 物体
        object_logits = self.object_detector(fused_feat)
        object_probs = torch.sigmoid(object_logits)  # 多标签
        
        # L3: 行为 (条件于场景)
        action_input = torch.cat([fused_feat, scene_probs], dim=-1)
        action_logits = self.action_recognizer(action_input)
        action_probs = torch.softmax(action_logits, dim=-1)
        
        # L4: 意图 (条件于场景和行为)
        intent_input = torch.cat([fused_feat, scene_probs, action_probs], dim=-1)
        intent_logits = self.intent_predictor(intent_input)
        intent_probs = torch.softmax(intent_logits, dim=-1)
        
        return {
            'scene': {'logits': scene_logits, 'probs': scene_probs},
            'objects': {'logits': object_logits, 'probs': object_probs},
            'actions': {'logits': action_logits, 'probs': action_probs},
            'intents': {'logits': intent_logits, 'probs': intent_probs}
        }


class MultimodalTaggingModel(nn.Module):
    """完整的多模态标签生成模型"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        
        config = config or {}
        
        # 融合模块
        self.fusion = VisionDominantFusion(
            vision_dim=config.get('vision_dim', 768),
            text_dim=config.get('text_dim', 768),
            context_dim=config.get('context_dim', 128),
            fusion_dim=config.get('fusion_dim', 512)
        )
        
        # 标签生成模块
        self.tag_generator = HierarchicalTagGenerator(
            input_dim=config.get('fusion_dim', 512),
            num_scenes=config.get('num_scenes', 20),
            num_objects=config.get('num_objects', 100),
            num_actions=config.get('num_actions', 50),
            num_intents=config.get('num_intents', 30)
        )
    
    def forward(
        self,
        vision_feat: torch.Tensor,
        text_feat: torch.Tensor,
        context_feat: torch.Tensor
    ) -> Tuple[Dict[str, torch.Tensor], torch.Tensor]:
        """
        完整前向传播
        
        Returns:
            tags: 层次化标签
            weights: 模态权重
        """
        # 多模态融合
        fused_feat, weights = self.fusion(vision_feat, text_feat, context_feat)
        
        # 生成标签
        tags = self.tag_generator(fused_feat)
        
        return tags, weights


# 标签类别定义
SCENE_CATEGORIES = [
    '厨房', '卧室', '客厅', '浴室', '书房',
    '办公室', '街道', '公园', '商场', '餐厅',
    '健身房', '医院', '学校', '车内', '户外',
    '地铁', '机场', '酒店', '咖啡厅', '其他'
]

OBJECT_CATEGORIES = [
    # 食物
    '水果', '蔬菜', '肉类', '主食', '饮料', '零食',
    # 家具
    '桌子', '椅子', '沙发', '床', '柜子',
    # 电器
    '电视', '冰箱', '洗衣机', '空调', '电脑', '手机',
    # 工具
    '笔', '书', '文件', '钥匙', '钱包',
    # 其他
    '衣服', '鞋子', '包', '植物', '宠物'
    # ... 扩展到100类
]

ACTION_CATEGORIES = [
    '烹饪', '进餐', '睡觉', '阅读', '工作',
    '运动', '看电视', '玩手机', '打扫', '洗漱',
    '穿衣', '出门', '回家', '购物', '社交',
    '学习', '娱乐', '休息', '通勤', '其他'
    # ... 扩展到50类
]

INTENT_CATEGORIES = [
    '准备早餐', '准备午餐', '准备晚餐', '睡前准备',
    '出门准备', '工作准备', '运动准备', '学习准备',
    '娱乐放松', '健康管理', '家务整理', '社交活动',
    '购物计划', '出行计划', '休息放松', '其他'
    # ... 扩展到30类
]
