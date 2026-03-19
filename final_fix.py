#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""最终修复脚本 - 处理所有剩余问题"""

import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed_lines = []
for i, line in enumerate(lines, 1):
    original = line
    
    # 修复docstring
    if '"""' in line and line.count('"""') == 1:
        # 单个三引号，可能缺少闭合
        if line.strip().endswith('""'):
            line = line.rstrip() + '"\n'
    
    # 修复注释末尾缺字
    if line.strip().startswith('#'):
        line = re.sub(r'# (.+?)数\s*$', r'# \1数据', line)
        line = re.sub(r'# (.+?)过\s*$', r'# \1过程', line)
        line = re.sub(r'# (.+?)分\s*$', r'# \1分析', line)
        line = re.sub(r'# (.+?)处\s*$', r'# \1处理', line)
        line = re.sub(r'# (.+?)信\s*$', r'# \1信息', line)
        line = re.sub(r'# (.+?)消\s*$', r'# \1消息', line)
        line = re.sub(r'# (.+?)事\s*$', r'# \1事件', line)
        line = re.sub(r'# (.+?)函\s*$', r'# \1函数', line)
    
    # 修复print语句中的问题
    if 'print(' in line:
        line = re.sub(r'发\s+\{', r'发送: {', line)
        line = re.sub(r'发\s+"', r'发送: "', line)
        line = re.sub(r'发\s+f"', r'发送: f"', line)
    
    # 修复缩进问题 - 如果注释后面紧跟代码且缩进不对
    if i > 1 and lines[i-2].strip().startswith('#') and not line.strip().startswith('#'):
        # 检查是否缩进异常
        prev_indent = len(lines[i-2]) - len(lines[i-2].lstrip())
        curr_indent = len(line) - len(line.lstrip())
        if line.strip() and curr_indent < prev_indent and not line.strip().startswith(('def ', 'class ', '@', 'except', 'finally', 'elif', 'else')):
            # 可能需要调整缩进
            pass
    
    fixed_lines.append(line)

# 写回
with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print('✓ 最终修复完成')
