#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""全面修复main.py的所有编码和语法问题"""

import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed_lines = []
for i, line in enumerate(lines):
    # 修复所有"个"相关的问题
    line = line.replace('个)', ')')
    line = line.replace('个,', ',')
    line = line.replace('个.', '.')
    line = line.replace('个;', ';')
    line = line.replace('个:', ':')
    line = line.replace('个"', '"')
    line = line.replace('"个', '"')
    line = line.replace('个}', '}')
    line = line.replace('个]', ']')
    line = line.replace('个 ', ' ')
    
    # 修复注释中的问题
    if '#' in line:
        line = line.replace('# 发个', '# 发送')
        line = line.replace('消个', '消息')
        line = line.replace('信个', '信息')
        line = line.replace('.5秒', '0.5秒')
        line = line.replace(' 个', ' 条')
    
    # 修复字符串中的问题
    if 'print(' in line or 'f"' in line or "f'" in line:
        line = line.replace('发个', '发送')
        line = line.replace('失个', '失败')
    
    # 修复docstring
    if '"""' in line:
        line = line.replace('个"""', '"""')
        line = line.replace('"""个', '"""')
        line = line.replace('个""', '"""')
        line = line.replace('""个', '"""')
    
    fixed_lines.append(line)

# 写回文件
with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print('✓ 全面修复完成')
