#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""自动修复所有注释末尾缺失的文字"""

import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复所有注释末尾的问题
# 匹配模式: # xxx数  或 # xxx过  等（注释末尾缺字）
patterns = [
    (r'# ([^#\n]*?)数\s*\n', r'# \1数据\n'),
    (r'# ([^#\n]*?)过\s*\n', r'# \1过程\n'),
    (r'# ([^#\n]*?)分\s*\n', r'# \1分析\n'),
    (r'# ([^#\n]*?)处\s*\n', r'# \1处理\n'),
    (r'# ([^#\n]*?)信\s*\n', r'# \1信息\n'),
    (r'# ([^#\n]*?)消\s*\n', r'# \1消息\n'),
]

for pattern, replacement in patterns:
    content = re.sub(pattern, replacement, content)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ 自动修复完成')
