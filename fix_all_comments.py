#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修复所有注释末尾缺字的问题"""

import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed_lines = []
for line in lines:
    # 如果是注释行且后面紧跟代码（缩进异常）
    if line.strip().startswith('#'):
        # 修复各种缺字情况
        line = re.sub(r'(#.+?)数\s*$', r'\1数据\n', line)
        line = re.sub(r'(#.+?)过\s*$', r'\1过程\n', line)
        line = re.sub(r'(#.+?)分\s*$', r'\1分析\n', line)
        line = re.sub(r'(#.+?)处\s*$', r'\1处理\n', line)
        line = re.sub(r'(#.+?)信\s*$', r'\1信息\n', line)
        line = re.sub(r'(#.+?)消\s*$', r'\1消息\n', line)
        line = re.sub(r'(#.+?)事\s*$', r'\1事件\n', line)
        line = re.sub(r'(#.+?)函\s*$', r'\1函数\n', line)
        line = re.sub(r'(#.+?)获\s*$', r'\1获取\n', line)
        line = re.sub(r'(#.+?)进\s*$', r'\1进度\n', line)
        line = re.sub(r'(#.+?)更\s*$', r'\1更新\n', line)
        
        # 确保注释后有换行
        if not line.endswith('\n'):
            line += '\n'
    
    # 修复print语句中的问题
    if 'print(' in line and '发送进' in line:
        line = line.replace('发送进', '发送进度:')
    
    fixed_lines.append(line)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print('✓ 修复了所有注释问题')
