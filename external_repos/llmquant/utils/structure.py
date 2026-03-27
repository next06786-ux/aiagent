import torch
from utils.autosearch import structural_searching,structural_searching_for_mask3,from_mask3_to_optimal_split
from utils.mask import generate_structural_mask

'''
Used to generate masks for minor structural 2-bit salient data and split major 1-bit normal data according to different metric.
'''
# def structural_guassian_distribution(tmp, H=None, metric="magnitude", up_lim=30):
#     if metric == "hessian":
#         target_weights = tmp ** 2 / (torch.diag(H).reshape((1, -1))) ** 2
#     elif metric == "magnitude":
#         target_weights = tmp
#     else:
#         raise NotImplementedError

#     optimal_split, mask3 = structural_searching(target_weights, up_lim)
#     mask1, mask2 = generate_structural_mask(target_weights, mask3, optimal_split)

#     # print(mask1.sum() / mask1.numel(), mask2.sum() / mask2.numel(), mask3.sum() / mask3.numel())
#     return mask1, mask2, mask3


def structural_guassian_distribution(tmp, H=None, metric="magnitude", up_lim=30, act_norm=None):
    """
    生成结构性mask，支持多种显著性指标。
    
    参数:
        tmp: [out_features, in_features] 权重矩阵
        H: [in_features, in_features] Hessian矩阵（用于hessian metric）
        metric: "magnitude", "hessian", 或 "wanda"
        up_lim: 显著列的上限数量
        act_norm: [in_features] 激活范数（用于wanda metric）
    
    返回:
        mask1, mask2, mask3: 三个mask，分别对应非显著、显著、最显著部分
    """
    if metric == "wanda":
        # Wanda分数 = |tmp| * act_norm
        # act_norm: [in_features]
        if act_norm is None:
            raise ValueError("act_norm must be provided when metric='wanda'")
        act_norm_reshaped = act_norm.reshape(1, -1)  # [1, in_features]
        # tmp: [out_features, in_features]
        # target_weights: [out_features, in_features]
        target_weights = tmp.abs() * act_norm_reshaped
    elif metric == "hessian":
        if H is None:
            raise ValueError("H must be provided when metric='hessian'")
        target_weights = tmp ** 2 / (torch.diag(H).reshape((1, -1))) ** 2
    elif metric == "magnitude":
        target_weights = tmp
    else:
        raise NotImplementedError(f"metric '{metric}' not supported. Use 'magnitude', 'hessian', or 'wanda'.")

    mask3 = structural_searching_for_mask3(target_weights, up_lim)
    optimal_split = from_mask3_to_optimal_split(tmp, mask3, up_lim)
    mask1, mask2 = generate_structural_mask(tmp, mask3, optimal_split)

    # print(mask1.sum() / mask1.numel(), mask2.sum() / mask2.numel(), mask3.sum() / mask3.numel())
    return mask1, mask2, mask3
