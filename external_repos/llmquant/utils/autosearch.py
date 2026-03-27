from re import L
import numpy as np
from pyparsing import line
import torch
from binary import high_order_residual, quantize_to_3bit_perchannel
from utils.mask import generate_structural_mask
from loguru import logger

def error_computing(origin_matrix, quantized_matrix):
    mse = torch.mean((origin_matrix - quantized_matrix) ** 2)
    return mse

def calculate_percentage_and_variance_original(weights, abs_weights, bin_edges):
    percentages = []
    variances = []
    accum_percentages = [0]
    total_elements = abs_weights.numel()
    for i in range(len(bin_edges) - 1):
        bin_mask = (abs_weights >= bin_edges[i]) & (abs_weights < bin_edges[i + 1])
        bin_weights = weights[bin_mask]
        percentages.append(bin_weights.numel() / total_elements * 100)
        accum_percentages.append(accum_percentages[-1] + percentages[-1])
        variances.append(torch.var(bin_weights))
    return percentages, variances, accum_percentages

'''
Include main method to search the rate for 2-bit salient data columns and the optimal split for 1-bit data
'''

def structural_searching_for_mask3(origin_matrix, up_lim=30):
    minimal_value = float('inf')
    minimal_value_0 = float('inf')
    optimal_split_0 = 1

    true_counts = origin_matrix.abs().sum(dim=0)
    
    # 确保 up_lim 不超过矩阵的列数
    num_cols = true_counts.shape[0]
    actual_up_lim = min(up_lim, num_cols)

    error = []
    lines = []
    # search for the optimal split for the first group, high order=2,, structured search
    if actual_up_lim <= 1:
        # 如果列数太少，直接返回全False的mask（所有列都作为非显著列）
        mask3 = torch.full((origin_matrix.shape[0], origin_matrix.shape[1]), False).to(origin_matrix.device)
        return mask3
    
    _, top_braq_2_columns = torch.topk(true_counts, actual_up_lim)
    for i in range(1, actual_up_lim):
        
        mask3 = torch.full((origin_matrix.shape[0], origin_matrix.shape[1]), False).to(origin_matrix.device)
        mask3[:, top_braq_2_columns[:i]] = True
        group3 = high_order_residual(origin_matrix, mask3, order=2)

        group4 = high_order_residual(origin_matrix, ~mask3, order=2)
        quantize_error_0 = error_computing(origin_matrix, group4+group3)
        error.append(quantize_error_0.item())
        lines.append(i)
        if torch.isfinite(quantize_error_0) and (quantize_error_0 < minimal_value_0):
            minimal_value_0 = quantize_error_0
            optimal_split_0 = i

    # 确保 optimal_split_0 不超过列数
    optimal_split_0 = max(1, min(int(optimal_split_0), num_cols))
    _, top_braq_2_columns = torch.topk(true_counts, optimal_split_0)
    mask3 = torch.full((origin_matrix.shape[0], origin_matrix.shape[1]), False).to(origin_matrix.device)
    mask3[:, top_braq_2_columns] = True

    # 计算显著权重的数量
    # num_salient_cols = optimal_split_0
    # total_cols = origin_matrix.shape[1]
    # salient_ratio = num_salient_cols / total_cols * 100 if total_cols > 0 else 0
    # logger.info(f"  Mask3 (salient weights): {num_salient_cols}/{total_cols} columns ({salient_ratio:.2f}%)")

    return  mask3

def from_mask3_to_optimal_split(origin_matrix, mask3, up_lim=30):
    minimal_value = float('inf')
    optimal_split = None
    group3 = high_order_residual(origin_matrix, mask3, order=2)

    search_matrix = origin_matrix * (~mask3)

    flat_abs_tensor = torch.abs(search_matrix).view(-1)
    percentiles = torch.linspace(0.10, 0.90, 81).to(origin_matrix.device)
    percentile_values = torch.tensor(
        np.quantile(flat_abs_tensor.detach().cpu().numpy(), q=percentiles.cpu().numpy(), axis=None, keepdims=False)
    ).to(origin_matrix.device)

    # search for the optimal split for the second group, high order=1,, non-structured search
    for split_value in percentile_values:
        mask1, mask2 = generate_structural_mask(origin_matrix, mask3, split_value)
        group1 = high_order_residual(origin_matrix, mask1, order=1)
        group2 = high_order_residual(origin_matrix, mask2, order=1)

        quantize_error = error_computing(origin_matrix, group1+group2+group3)
        if quantize_error < minimal_value:
            minimal_value = quantize_error
            optimal_split = split_value
        tmp = torch.max(torch.abs(search_matrix)).item()
    
    return optimal_split

def structural_searching(origin_matrix, up_lim=30):
    minimal_value = float('inf')
    minimal_value_0 = float('inf')
    optimal_split_0 = 1

    true_counts = origin_matrix.abs().sum(dim=0)

    error = []
    lines = []
    # search for the optimal split for the first group, high order=2,, structured search
    _, top_braq_2_columns = torch.topk(true_counts, up_lim)
    for i in range(1, up_lim):
        mask3 = torch.full((origin_matrix.shape[0], origin_matrix.shape[1]), False).to(origin_matrix.device)
        mask3[:, top_braq_2_columns[:i]] = True
        group3 = high_order_residual(origin_matrix, mask3, order=2)

        group4 = high_order_residual(origin_matrix, ~mask3, order=2)
        quantize_error_0 = error_computing(origin_matrix, group4+group3)
        error.append(quantize_error_0.item())
        lines.append(i)
        if torch.isfinite(quantize_error_0) and (quantize_error_0 < minimal_value_0):
            minimal_value_0 = quantize_error_0
            optimal_split_0 = i

    _, top_braq_2_columns = torch.topk(true_counts, optimal_split_0)
    mask3 = torch.full((origin_matrix.shape[0], origin_matrix.shape[1]), False).to(origin_matrix.device)
    mask3[:, top_braq_2_columns] = True
    group3 = high_order_residual(origin_matrix, mask3, order=2)

    search_matrix = origin_matrix * (~mask3)

    flat_abs_tensor = torch.abs(search_matrix).view(-1)
    percentiles = torch.linspace(0.10, 0.90, 81).to(origin_matrix.device)
    percentile_values = torch.tensor(
        np.quantile(flat_abs_tensor.detach().cpu().numpy(), q=percentiles.cpu().numpy(), axis=None, keepdims=False)
    ).to(origin_matrix.device)

    # search for the optimal split for the second group, high order=1,, non-structured search
    for split_value in percentile_values:
        mask1, mask2 = generate_structural_mask(origin_matrix, mask3, split_value)
        group1 = high_order_residual(origin_matrix, mask1, order=1)
        group2 = high_order_residual(origin_matrix, mask2, order=1)

        quantize_error = error_computing(origin_matrix, group1+group2+group3)
        if quantize_error < minimal_value:
            minimal_value = quantize_error
            optimal_split = split_value
        tmp = torch.max(torch.abs(search_matrix)).item()
    
    return optimal_split, mask3

def find_optimal_split(group_max, origin_matrix, border):
    optimal_split = None
    minimal_value = float('inf')
    searching_steps = torch.arange(0.1,0.8,0.01)
    searching_steps = searching_steps * group_max

    group3 = high_order_residual(origin_matrix, torch.abs(origin_matrix) > border, order=2)
    for split_value in searching_steps:

        group1 = high_order_residual(origin_matrix, (torch.abs(origin_matrix) > split_value) & (torch.abs(origin_matrix) <= border), order=1)
        group2 = high_order_residual(origin_matrix, torch.abs(origin_matrix) <= split_value, order=1)

        quantize_error = error_computing(origin_matrix, group1+group2+group3)
        if quantize_error < minimal_value:
            minimal_value = quantize_error
            optimal_split = split_value

    return optimal_split, minimal_value

def structural_searching_for_salient_cols_R(wanda_scores, R_block, up_lim=50):
    """
    搜索R block的显著列（基于wanda分数，和structural_searching_for_mask3一样）
    wanda_scores: [block_size] 列级别的wanda分数
    R_block: [out_features, block_size]
    返回：mask3 (显著列mask，2D)
    """
    minimal_value = float('inf')
    optimal_split = 1
    num_cols = wanda_scores.shape[0]
    actual_up_lim = min(up_lim, num_cols)
    
    if actual_up_lim <= 1:
        return torch.full((R_block.shape[0], R_block.shape[1]), False).to(R_block.device)
    
    _, top_cols = torch.topk(wanda_scores, actual_up_lim, largest=True)
    
    for i in range(1, actual_up_lim):
        mask3 = torch.full((R_block.shape[0], R_block.shape[1]), False).to(R_block.device)
        mask3[:, top_cols[:i]] = True
        group3 = high_order_residual(R_block, mask3, order=2)
        group4 = high_order_residual(R_block, ~mask3, order=2)
        quantize_error = error_computing(R_block, group4 + group3)
        if torch.isfinite(quantize_error) and (quantize_error < minimal_value):
            minimal_value = quantize_error
            optimal_split = i
    
    optimal_split = max(1, min(int(optimal_split), int(actual_up_lim)))
    mask3 = torch.full((R_block.shape[0], R_block.shape[1]), False).to(R_block.device)
    mask3[:, top_cols[:optimal_split]] = True
    return mask3


def structural_searching_for_salient_cols_mixed_R(col_scores, R_block, up_lim=50):
    """
    在给定列分数的前提下，搜索显著列数量 k（1..up_lim），
    目标是最小化混合量化误差：
      - 非显著列：二值残差近似（order=2）
      - 显著列：per-channel 3bit

    Args:
        col_scores: [block_size] 列分数（可来自 wanda/hessian/magnitude）
        R_block: [out_features, block_size]
        up_lim: 显著列数搜索上限

    Returns:
        best_mask3: [out_features, block_size] 显著列 mask（二维）
        best_k: 最优显著列数量
        best_mse: 对应的最小 MSE
    """
    n_rows, n_cols = R_block.shape
    device = R_block.device
    actual_up_lim = min(up_lim, n_cols)

    # 默认回退：不选显著列，整块走 order=2
    best_mask3 = torch.zeros((n_rows, n_cols), dtype=torch.bool, device=device)
    mask_all = torch.ones_like(R_block, dtype=torch.bool)
    best_q = high_order_residual(R_block, mask_all, order=2)
    best_mse = float(error_computing(R_block, best_q).item())
    best_k = 0

    if actual_up_lim <= 0:
        return best_mask3, best_k, best_mse

    _, top_cols = torch.topk(col_scores, actual_up_lim, largest=True)

    for k in range(1, actual_up_lim + 1):
        mask3 = torch.zeros((n_rows, n_cols), dtype=torch.bool, device=device)
        mask3[:, top_cols[:k]] = True
        non_salient_mask = ~mask3

        q_non_salient = high_order_residual(R_block, non_salient_mask, order=2)

        q_salient = torch.zeros_like(R_block)
        salient_indices = torch.where(mask3[0])[0]
        if salient_indices.numel() > 0:
            q_salient_part, _, _ = quantize_to_3bit_perchannel(R_block[:, salient_indices])
            q_salient[:, salient_indices] = q_salient_part.float()

        q_candidate = q_non_salient + q_salient
        candidate_mse = float(error_computing(R_block, q_candidate).item())

        if candidate_mse < best_mse:
            best_mse = candidate_mse
            best_mask3 = mask3
            best_k = k

    return best_mask3, best_k, best_mse

def structural_searching_for_prune_cols_R(wanda_scores, R_block, mask3_salient, up_lim=50, enable_prune=True):
    """
    剪枝R block的最后5%列（按wanda分数排序，基于整个block的列数）
    wanda_scores: [block_size] 列级别的wanda分数
    R_block: [out_features, block_size]
    mask3_salient: [out_features, block_size] 显著列mask
    返回：mask_prune (剪枝列mask，2D)
    """
    if not enable_prune:
        return torch.full((R_block.shape[0], R_block.shape[1]), False).to(R_block.device)
    
    total_cols = R_block.shape[1]
    # 计算5%（基于整个block，至少1列）
    num_prune = max(0, int(total_cols * 0.00))
    
    mask_non_salient = ~mask3_salient
    non_salient_cols = mask_non_salient[0]  # [block_size]
    
    if not non_salient_cols.any():
        mask_prune = torch.full((R_block.shape[0], R_block.shape[1]), False).to(R_block.device)
        logger.info(f"  Prune columns: 0/{total_cols} (0.00%)")
        return mask_prune
    
    # 获取非显著列的wanda分数和索引
    non_salient_indices = torch.where(non_salient_cols)[0]
    num_non_salient = len(non_salient_indices)
    
    # 限制剪枝数量不超过非显著列数量
    num_prune = min(num_prune, num_non_salient)
    
    if num_prune == 0:
        mask_prune = torch.full((R_block.shape[0], R_block.shape[1]), False).to(R_block.device)
        logger.info(f"  Prune columns: 0/{total_cols} (0.00%)")
        return mask_prune
    
    # 选择wanda分数最低的num_prune列
    non_salient_wanda = wanda_scores[non_salient_indices]
    _, bottom_cols_local = torch.topk(non_salient_wanda, num_prune, largest=False)
    bottom_cols = non_salient_indices[bottom_cols_local]
    
    # 创建剪枝mask
    mask_prune = torch.full((R_block.shape[0], R_block.shape[1]), False).to(R_block.device)
    mask_prune[:, bottom_cols] = True
    
    # 显示实际百分比
    prune_ratio = num_prune / total_cols * 100
    logger.info(f"  Prune columns: {num_prune}/{total_cols} ({prune_ratio:.2f}%)")
    return mask_prune
