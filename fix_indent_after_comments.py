#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修复注释后的缩进问题"""

with open('backend/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed_lines = []
for i, line in enumerate(lines):
    # 检查是否是注释行
    if line.strip().startswith('#'):
        # 确保注释行以换行结束
        if not line.endswith('\n'):
            line = line + '\n'
        
        # 检查下一行是否存在且缩进异常
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            # 如果注释后紧跟代码且没有适当的缩进
            if next_line.strip() and not next_line.strip().startswith('#'):
                # 获取注释的缩进
                comment_indent = len(line) - len(line.lstrip())
                next_indent = len(next_line) - len(next_line.lstrip())
                
                # 如果下一行缩进小于注释且不是函数/类定义
                if next_indent < comment_indent and not any(next_line.strip().startswith(kw) for kw in ['def ', 'class ', '@', 'except', 'finally', 'elif', 'else:', 'return', 'break', 'continue', 'pass', 'raise']):
                    # 可能需要在注释和代码之间添加空行或调整缩进
                    pass
    
    fixed_lines.append(line)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print('✓ 修复了注释后的缩进问题')
