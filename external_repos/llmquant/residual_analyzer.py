"""
残差分析模块 - 简洁版本
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import json
import torch

# 全局存储
residual_data = {}

def save_residual(layer_idx, name, R, H, svd_enable):
    """保存残差数据"""
    key = f"layer_{layer_idx}_{name}"
    if key not in residual_data:
        residual_data[key] = {}
    mode = "svd" if svd_enable else "baseline"
    residual_data[key][mode] = {
        "R": R.cpu().clone(),
        "H": H.cpu().clone(),
    }

def analyze_distribution(R):
    """分析分布统计"""
    R_flat = R.flatten().cpu().numpy()
    return {
        "mean": float(np.mean(R_flat)),
        "std": float(np.std(R_flat)),
        "var": float(np.var(R_flat)),
        "min": float(np.min(R_flat)),
        "max": float(np.max(R_flat)),
        "p25": float(np.percentile(R_flat, 25)),
        "p50": float(np.percentile(R_flat, 50)),
        "p75": float(np.percentile(R_flat, 75)),
        "p95": float(np.percentile(R_flat, 95)),
        "p99": float(np.percentile(R_flat, 99)),
    }

def compute_mask_ratios(R, H, salient_metric):
    """计算mask比例"""
    try:
        from utils.structure import structural_guassian_distribution
        mask1, mask2, mask3 = structural_guassian_distribution(R, H, salient_metric, 50)
        total = mask1.numel()
        return {
            "mask1": float(mask1.sum().item() / total),
            "mask2": float(mask2.sum().item() / total),
            "mask3": float(mask3.sum().item() / total),
        }
    except:
        return {"mask1": 0, "mask2": 0, "mask3": 0}

def plot_3d_comparison(R_baseline, R_svd, layer_idx, name, save_dir):
    """3D对比图"""
    fig = plt.figure(figsize=(16, 6))
    for idx, (R, title) in enumerate([(R_baseline, "Baseline R (=W)"), 
                                       (R_svd, "SVD R (=W-L_quantized)")], 1):
        ax = fig.add_subplot(1, 2, idx, projection='3d')
        R_np = np.abs(R.cpu().numpy())
        rows, cols = R_np.shape
        step = max(1, min(rows//200, cols//200))
        R_sampled = R_np[::step, ::step]
        r, c = R_sampled.shape
        x, y = np.arange(c) * step, np.arange(r) * step
        X, Y = np.meshgrid(x, y)
        ax.plot_surface(X, Y, R_sampled, cmap='hot', alpha=0.8, linewidth=0)
        ax.set_xlabel('Column')
        ax.set_ylabel('Row')
        ax.set_zlabel('|Value|')
        ax.set_title(title)
    plt.suptitle(f"Layer {layer_idx} - {name}", fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, f"layer_{layer_idx}_{name}_3d.png"), 
                dpi=150, bbox_inches='tight')
    plt.close()

def plot_histogram_comparison(R_baseline, R_svd, layer_idx, name, save_dir):
    """直方图对比"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    for ax, R, title in [(ax1, R_baseline, "Baseline R (=W)"),
                          (ax2, R_svd, "SVD R (=W-L_quantized)")]:
        R_flat = R.flatten().cpu().numpy()
        ax.hist(R_flat, bins=100, alpha=0.7, 
                color='blue' if 'Baseline' in title else 'red', edgecolor='black')
        ax.set_xlabel('Value')
        ax.set_ylabel('Frequency')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
    plt.suptitle(f"Layer {layer_idx} - {name}", fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, f"layer_{layer_idx}_{name}_hist.png"), 
                dpi=150, bbox_inches='tight')
    plt.close()

def analyze_all(save_dir, salient_metric, target_layers=[1, 14, 31]):
    """分析所有收集的数据"""
    print("\n=== Analyzing Residuals ===")
    all_stats = {}
    
    for key in sorted(residual_data.keys()):
        if "baseline" not in residual_data[key] or "svd" not in residual_data[key]:
            continue
        
        layer_idx, name = key.replace("layer_", "").split("_", 1)
        layer_idx = int(layer_idx)
        
        if layer_idx not in target_layers:
            continue
        
        R_baseline = residual_data[key]["baseline"]["R"]
        R_svd = residual_data[key]["svd"]["R"]
        H = residual_data[key]["baseline"]["H"]
        
        stats_baseline = analyze_distribution(R_baseline)
        stats_svd = analyze_distribution(R_svd)
        mask_baseline = compute_mask_ratios(R_baseline, H, salient_metric)
        mask_svd = compute_mask_ratios(R_svd, H, salient_metric)
        
        all_stats[key] = {
            "baseline": {"stats": stats_baseline, "mask": mask_baseline},
            "svd": {"stats": stats_svd, "mask": mask_svd},
        }
        
        print(f"  Plotting {key}...")
        plot_3d_comparison(R_baseline, R_svd, layer_idx, name, save_dir)
        plot_histogram_comparison(R_baseline, R_svd, layer_idx, name, save_dir)
    
    with open(os.path.join(save_dir, "statistics.json"), 'w') as f:
        json.dump(all_stats, f, indent=2)
    
    print("\n=== Summary ===")
    for key in sorted(all_stats.keys()):
        b = all_stats[key]["baseline"]
        s = all_stats[key]["svd"]
        print(f"\n{key}:")
        print(f"  Baseline: mean={b['stats']['mean']:.6f}, std={b['stats']['std']:.6f}, "
              f"mask1={b['mask']['mask1']:.3f}, mask2={b['mask']['mask2']:.3f}, "
              f"mask3={b['mask']['mask3']:.3f}")
        print(f"  SVD:      mean={s['stats']['mean']:.6f}, std={s['stats']['std']:.6f}, "
              f"mask1={s['mask']['mask1']:.3f}, mask2={s['mask']['mask2']:.3f}, "
              f"mask3={s['mask']['mask3']:.3f}")
    
    print(f"\nResults saved to: {save_dir}")

def clear_data():
    """清空数据"""
    global residual_data
    residual_data = {}

