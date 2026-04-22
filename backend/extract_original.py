#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从git历史提取原始decision_personas.py文件
"""
import subprocess
import sys

def extract_from_git():
    """从git提取文件"""
    try:
        # 从git历史提取文件内容
        result = subprocess.run(
            ['git', 'show', 'ecb5f01:backend/decision/decision_personas.py'],
            capture_output=True,
            text=False  # 使用bytes模式
        )
        
        if result.returncode != 0:
            print(f"Git命令失败: {result.stderr.decode('utf-8', errors='ignore')}")
            return False
        
        # 保存原始字节内容
        with open('backend/decision/decision_personas_original_reference.txt', 'wb') as f:
            f.write(result.stdout)
        
        print(f"✅ 已提取原文件，大小: {len(result.stdout)} 字节")
        print(f"   保存到: backend/decision/decision_personas_original_reference.txt")
        
        # 统计行数
        lines = result.stdout.decode('utf-8', errors='ignore').split('\n')
        print(f"   总行数: {len(lines)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 提取失败: {e}")
        return False

if __name__ == "__main__":
    if extract_from_git():
        print("\n下一步: 运行 rebuild_personas.py 来重建文件")
    else:
        sys.exit(1)
