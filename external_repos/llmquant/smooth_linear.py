"""
SmoothLinear: 支持正向 SmoothQuant 的自定义 Linear 层
在 forward 中自动对输入激活应用下缩放（X_new = X / scale）
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from loguru import logger


class SmoothLinear(nn.Module):
    """
    支持正向 SmoothQuant 的自定义 Linear 层
    在 forward 中对输入激活进行下缩放：X_new = X / scale
    权重已经在量化时被上缩放过了：W_new = W * scale
    """

    def __init__(self, in_features, out_features, bias=True, 
                 weight=None, smooth_scale=None, layer_name="unknown"):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.layer_name = layer_name
        
        if weight is not None:
            # 使用量化后的权重（已经平滑过了）
            weight_fp16 = weight.clone().half() if weight.dtype != torch.float16 else weight.clone()
            self.weight = nn.Parameter(weight_fp16, requires_grad=False)
            
            if bias is not None and isinstance(bias, torch.Tensor):
                bias_fp16 = bias.clone().half() if bias.dtype != torch.float16 else bias.clone()
                self.bias = nn.Parameter(bias_fp16, requires_grad=False)
            elif bias is True:
                self.bias = nn.Parameter(torch.zeros(out_features, dtype=torch.float16), requires_grad=False)
            else:
                self.register_parameter('bias', None)
            
            # 正向 SmoothQuant 参数
            if smooth_scale is not None:
                self.register_buffer('smooth_scale', smooth_scale.clone().half())
            else:
                self.register_buffer('smooth_scale', torch.ones(in_features, dtype=torch.float16))
        else:
            # 加载时创建空层（等待 load_state_dict）
            self.weight = nn.Parameter(torch.empty(out_features, in_features), requires_grad=False)
            if bias:
                self.bias = nn.Parameter(torch.empty(out_features), requires_grad=False)
            else:
                self.register_parameter('bias', None)
            
            if smooth_scale is not None:
                self.register_buffer('smooth_scale', smooth_scale.clone().half() if isinstance(smooth_scale, torch.Tensor) else torch.ones(in_features, dtype=torch.float16))
            else:
                self.register_buffer('smooth_scale', torch.ones(in_features, dtype=torch.float16))
    
    def forward(self, x):
        """
        前向传播：对输入激活应用下缩放，然后与权重计算
        Y = (X / scale) @ (W * scale) = X @ W（数学等价）
        
        权重已经在量化时被上缩放过了，所以这里只需要对输入激活下缩放
        """
        # 检查 smooth_scale 是否已初始化
        if self.smooth_scale.numel() == 1 and self.smooth_scale.item() == 1.0:
            # 未初始化或未使用 SmoothQuant，直接使用原始计算
            return F.linear(x, self.weight, self.bias)
        
        # 对输入激活应用下缩放：X_new = X / scale
        # x: [batch_size, seq_len, in_features] 或 [batch_size, in_features]
        # smooth_scale: [in_features]
        if x.dim() == 3:
            # [batch_size, seq_len, in_features]
            smooth_scale = self.smooth_scale.view(1, 1, -1).to(x.dtype)  # [1, 1, in_features]
        else:
            # [batch_size, in_features]
            smooth_scale = self.smooth_scale.view(1, -1).to(x.dtype)  # [1, in_features]
        
        x_smooth = x / smooth_scale
        
        # 使用已经上缩放过的权重计算（权重在量化时已经修改过了）
        return F.linear(x_smooth, self.weight, self.bias)
    
    def extra_repr(self):
        return f'in_features={self.in_features}, out_features={self.out_features}, smoothquant=True'

