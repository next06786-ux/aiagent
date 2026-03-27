
import numpy as np
import torch
from tqdm import tqdm
import pickle
import os
import argparse


def exchange(i, j, tensor):
    """交换矩阵的第i行和第j行，第i列和第j列"""
    indices_row = torch.arange(tensor.size(0))
    indices_row[i], indices_row[j] = indices_row[j].item(), indices_row[i].item()
    tensor = tensor[indices_row]

    indices_col = torch.arange(tensor.size(1))
    indices_col[i], indices_col[j] = indices_col[j].item(), indices_col[i].item()
    tensor = tensor[:, indices_col]
    return tensor


def generate_rot_for_size(n, device='cuda'):

    R = torch.eye(n).to(device)

    for i in range(n-1):
        rot_i = torch.eye(n).to(device)
        cos = 1 / np.sqrt(i+2)
        sin = np.sqrt(i+1) / np.sqrt(i+2)
        rot_i[i, i] = rot_i[i + 1, i + 1] = cos
        rot_i[i, i + 1] = -sin
        rot_i[i + 1, i] = sin
        R = torch.matmul(rot_i, R)

    R = exchange(0, n-1, R).cpu()
    return R


def generate_rot_pkl(output_path='Rot.pkl', sizes=None, device='cuda', force=False):
    """
    生成Rot.pkl文件
    
    参数:
        output_path: 输出文件路径
        sizes: 要生成的尺寸列表，None表示生成全部（2^1 到 2^12）
        device: 设备
        force: 是否强制重新生成（即使已存在）
    """
    # 默认生成所有尺寸：2^1 到 2^12
    if sizes is None:
        sizes = [int(2**i) for i in range(1, 13)]
    
    # 加载已存在的字典（如果存在且不强制）
    if os.path.exists(output_path) and not force:
        try:
            with open(output_path, 'rb') as f:
                dic = pickle.load(f)
            print(f"Loaded existing Rot.pkl from {output_path}")
        except:
            dic = {}
            print(f"Failed to load existing Rot.pkl, creating new one")
    else:
        dic = {}
        if os.path.exists(output_path) and force:
            print(f"Force regenerating Rot.pkl at {output_path}")
    
    # 生成每个尺寸的旋转矩阵
    for n in sizes:
        if n in dic and not force:
            print(f"  Size {n}: already exists, skipping...")
            continue
        
        print(f"  Generating rotation matrix for size {n}...")
        R = generate_rot_for_size(n, device)
        dic[n] = R
        print(f"  ✓ Size {n} completed")
    
    # 保存
    output_dir = os.path.dirname(output_path) if os.path.dirname(output_path) else '.'
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'wb') as f:
        pickle.dump(dic, f)
    
    print(f"\n✓ Rot.pkl saved to {output_path}")
    print(f"  Contains sizes: {sorted(dic.keys())}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Precompute rotation matrices for DuQuant')
    parser.add_argument(
        '--sizes',
        type=int,
        nargs='+',
        default=None,
        help='Sizes to generate (default: all sizes from 2^1 to 2^12)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='Rot.pkl',
        help='Output file path (default: Rot.pkl in current directory)'
    )
    parser.add_argument(
        '--device',
        type=str,
        default='cuda',
        help='Device to use (default: cuda)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force regenerate even if file exists'
    )
    
    args = parser.parse_args()
    
    # 如果output是相对路径，相对于脚本所在目录
    if not os.path.isabs(args.output):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        args.output = os.path.join(script_dir, args.output)
    
    print(f"Generating rotation matrices...")
    print(f"  Output: {args.output}")
    print(f"  Device: {args.device}")
    print(f"  Sizes: {args.sizes if args.sizes else 'all (2^1 to 2^12)'}")
    print()
    
    generate_rot_pkl(
        output_path=args.output,
        sizes=args.sizes,
        device=args.device,
        force=args.force
    )